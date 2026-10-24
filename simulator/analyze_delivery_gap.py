"""Read-only decomposition of the completed delivery study, not a new experiment.

Run from the repository root. The old test data are development evidence for
any subsequent redesign; this script does not select a replacement gate.
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', default='revision/delivery-learning-results')
    ap.add_argument('--run', default='simulator/out/delivery-learning-v3')
    ap.add_argument('--label-snapshot', default='revision/delivery-mathematical-inputs/training_label_snapshot.csv')
    ap.add_argument('--output', default='revision/delivery-mathematical-analysis')
    args = ap.parse_args()
    source, run, out = Path(args.results), Path(args.run), Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    effects = pd.read_csv(source / 'heldout_rejection_effects.csv')
    predictions = pd.read_csv(source / 'rejected_packet_predictions.csv')
    summary = pd.read_csv(source / 'summary.csv').set_index('method')
    labels = pd.read_csv(source / 'causal_label_summary.csv')
    keys = ['seed', 'graph', 'size', 'case', 'episode']
    assert not effects.duplicated(keys).any()
    paired = effects.merge(predictions, on=keys + ['effect'], validate='one_to_one')
    assert len(paired) == len(effects) == len(predictions)
    assert np.allclose(paired.difference_pp, -paired.realized_admit_minus_reject_pp)
    n = int(summary.loc['LEARN', 'episodes'])
    assert n == int(summary.loc['ALL', 'episodes'])
    n_convoys = 8
    # Effects use fleet fractions in multiples of one of eight convoy outcomes.
    convoy_changes = effects.difference_pp * n_convoys / 100
    assert np.allclose(convoy_changes, convoy_changes.round())
    positive = effects.difference_pp > 0
    negative = effects.difference_pp < 0
    gain = effects.loc[positive, 'difference_pp'].sum() / n
    loss = -effects.loc[negative, 'difference_pp'].sum() / n
    delta = summary.loc['LEARN', 'on_time_pct'] - summary.loc['ALL', 'on_time_pct']
    assert np.isclose(gain - loss, delta)
    q = len(effects) / n
    assert np.isclose(q * effects.difference_pp.mean(), delta)
    assert int(summary.loc['LEARN', 'rejections']) == len(effects)
    active = labels[~labels.control].copy()
    active.to_csv(out / 'training_signal_by_seed.csv', index=False)
    snapshot = Path(args.label_snapshot)
    scale_rows = []
    if snapshot.exists():
        training_labels = pd.read_csv(snapshot)
        for seed, block in training_labels[~training_labels.control].groupby('seed'):
            y = block.delta.to_numpy()
            variances = np.var(np.stack([y, y > 0, y < 0], axis=1), axis=0)
            reference = active[active.seed == seed].iloc[0]
            assert len(y) == reference.labels and (y < 0).sum() == reference.admit_harms and (y > 0).sum() == reference.admit_helps
            scale_rows.append(dict(seed=int(seed),fit_samples=len(y),
                fleet_value_variance=variances[0],admission_benefit_indicator_variance=variances[1],
                admission_harm_indicator_variance=variances[2],
                value_share_of_summed_target_variance_pct=100*variances[0]/variances.sum()))
        pd.DataFrame(scale_rows).to_csv(out / 'multioutput_target_scale.csv', index=False)
    by_seed = paired.groupby('seed').agg(
        rejections=('effect', 'size'),
        helpful=('difference_pp', lambda v: int((v > 0).sum())),
        harmful=('difference_pp', lambda v: int((v < 0).sum())),
        no_delivery_effect=('difference_pp', lambda v: int((v == 0).sum())),
        predicted_admission_effect_pp=('predicted_admit_minus_reject_pp', 'mean'),
        actual_admission_effect_pp=('realized_admit_minus_reject_pp', 'mean'),
        predicted_rejection_harm_frequency=('estimated_admission_benefit_frequency', 'mean'),
        actual_rejection_harm_frequency=('difference_pp', lambda v: float((v < 0).mean())),
    )
    by_seed.to_csv(out / 'selected_rejection_predictions_by_seed.csv')
    # Use complete saved validation rollouts if available. Average across the
    # eight actors before measuring spread across the 24 shared environments.
    validation_path = run / 'validation.csv.gz'
    validation = None
    if validation_path.exists():
        val = pd.read_csv(validation_path)
        baseline = val[val.setting == 0].set_index(['seed', 'graph', 'case', 'episode']).on_time
        rows = []
        for setting, block in val.groupby('setting'):
            d = 100 * (block.set_index(baseline.index.names).on_time - baseline)
            clusters = d.groupby(['graph', 'case', 'episode']).mean()
            rows.append(dict(setting=int(setting),mean_gain_pp=d.mean(),
                             shared_environment_clusters=len(clusters),
                             actor_rows=len(d),environment_cluster_sd_pp=clusters.std(ddof=1)))
        validation = pd.DataFrame(rows)
        validation.to_csv(out / 'validation_pairing_and_spread.csv', index=False)
    inputs = [source / name for name in ['heldout_rejection_effects.csv',
              'rejected_packet_predictions.csv', 'summary.csv', 'causal_label_summary.csv']]
    if validation_path.exists(): inputs.append(validation_path)
    if snapshot.exists(): inputs.append(snapshot)
    numbers = dict(
        scope='Retrospective diagnostic of existing v3 outcomes; not a new superiority test.',
        method_episodes=n, convoy_outcomes_per_method=n*n_convoys,
        rejected_packets=len(effects), rejection_episode_fraction=q,
        helpful_rejections=int(positive.sum()), harmful_rejections=int(negative.sum()),
        zero_delivery_effect_rejections=int((~positive & ~negative).sum()),
        on_time_convoys_recovered=int(round(convoy_changes[positive].sum())),
        on_time_convoys_lost=int(round(-convoy_changes[negative].sum())),
        net_on_time_convoy_change=int(round(convoy_changes.sum())),
        gross_delivery_gain_pp=gain, gross_delivery_loss_pp=loss, net_delivery_change_pp=delta,
        mean_gain_pp_per_rejected_episode=effects.difference_pp.mean(),
        mean_gain_pp_needed_for_1pp_overall_at_same_activity=1/q,
        mean_predicted_admission_effect_pp=predictions.predicted_admit_minus_reject_pp.mean(),
        mean_actual_admission_effect_pp=predictions.realized_admit_minus_reject_pp.mean(),
        mean_predicted_rejection_harm_frequency=predictions.estimated_admission_benefit_frequency.mean(),
        observed_rejection_harm_frequency=float(negative.mean()),
        harmful_admission_training_labels=int(active.admit_harms.sum()),
        useful_admission_training_labels=int(active.admit_helps.sum()),
        zero_effect_active_training_labels=int(active.no_delivery_effect.sum()),
        min_harmful_admission_labels_per_model=int(active.admit_harms.min()),
        max_harmful_admission_labels_per_model=int(active.admit_harms.max()),
        min_value_target_variance_share_pct=min((r['value_share_of_summed_target_variance_pct'] for r in scale_rows), default=None),
        max_value_target_variance_share_pct=max((r['value_share_of_summed_target_variance_pct'] for r in scale_rows), default=None),
        global_false_rejection_rate_identified=False,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    )
    (out / 'analysis.json').write_text(json.dumps(numbers, indent=2) + '\n')
    plt.rcParams.update({'font.size':10})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    bars = axes[0].bar(['Helpful\nrejections', 'Harmful\nrejections', 'Net\neffect'],
                       [gain, -loss, delta], color=['tab:blue','tab:orange','tab:gray'])
    axes[0].bar_label(bars, fmt='%+.3f', padding=4)
    axes[0].set_ylim(-.85, .75)
    axes[0].axhline(0, color='black', linewidth=.8)
    axes[0].set_ylabel('On-time delivery change (percentage points)')
    axes[0].set_title(f'Across all {n:,} paired LEARN/ALL episodes')
    bars = axes[1].bar(['Predicted rejection\nharm frequency', 'Observed rejection\nharm frequency'],
        [100*numbers['mean_predicted_rejection_harm_frequency'],100*numbers['observed_rejection_harm_frequency']],
        color=['tab:blue','tab:orange'])
    axes[1].bar_label(bars, fmt='%.2f%%', padding=4)
    axes[1].set_ylim(0,12)
    axes[1].set_ylabel('Frequency among selected rejections (%)')
    axes[1].set_title(f'Selected {len(effects):,} rejected packets only')
    fig.suptitle('Why the tested gate lost delivery: gains were outweighed by mistakes\nDescriptive decomposition; selected-case predictions are not global calibration',fontsize=12)
    fig.tight_layout()
    fig.savefig(out / 'delivery_gap_decomposition.png', dpi=160)
    fig.savefig(out / 'delivery_gap_decomposition.pdf')
    plt.close(fig)
    print(json.dumps(numbers), flush=True)


if __name__ == '__main__':
    main()
