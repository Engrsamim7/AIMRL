"""Mechanism diagnostics: descriptive evidence, no new superiority assertions."""
import argparse
import base64
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from diagnose_gate_decisions import fingerprint, CAPS

TOL=1e-8

def read(run,name):
    p=run/(name+'.csv');return pd.read_csv(p if p.exists() else p.with_suffix('.csv.gz'))


def original_reference(parent,raw):
    source=read(parent,'mechanism_convoys')
    source=source[source.graph.lt(2)&source.episode.lt(2)].copy()
    actual=raw[raw.method.eq('COMBINED')]
    ref=source[source.method.eq('COMBINED')]
    key=['algo','seed','graph','case','episode','convoy']
    a,b=actual.set_index(key).sort_index(),ref.set_index(key).sort_index()
    assert len(a)==len(b)==2560 and a.index.equals(b.index)
    cols=[c for c in a.columns if c not in ['method']]
    for c in cols:assert np.allclose(a[c],b[c],equal_nan=True),c
    return source


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/gate-decision-diagnosis');ap.add_argument('--parent',default='simulator/out/matched-gate-study');ap.add_argument('--output',default='revision/gate-decision-diagnosis');args=ap.parse_args()
    run,parent,out=Path(args.run).resolve(),Path(args.parent).resolve(),Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((run/'pipeline.json').read_text());assert meta['status']=='completed' and meta['source_hash']==fingerprint()
    p,e,ep,raw,d=[read(run,n) for n in ['packets','effects','episodes','convoys','drift_labels']]
    assert len(ep)==1024 and len(raw)==5120
    assert (raw.delivered+raw.destroyed+raw.censored).eq(1).all()
    assert np.allclose(raw.elapsed,raw.travel+raw.service+raw.wait)
    source=original_reference(parent,raw)
    assert len(json.loads((run/'warmup_verification.json').read_text()))==16
    full=e[e.context.eq('full')].copy();prefix=e[e.context.eq('prefix')].copy()
    full['actual_delta_utility']=(2*full.accepted.astype(int)-1)*full.delta_utility
    full['actual_delta_delivery']=(2*full.accepted.astype(int)-1)*full.delta_delivery
    for r in e.itertuples():
        a,b=json.loads(r.accept_rows),json.loads(r.reject_rows)
        assert len(a)==len(b)==5
        assert all(x['delivered']+x['destroyed']+x['censored']==1 for x in a+b)
        assert a[r.convoy]['delivered']-b[r.convoy]['delivered']==r.delta_delivery
        assert sum(x['delivered'] for x in a)-sum(x['delivered'] for x in b)==r.delta_team_deliveries
    total=p.groupby('algo').agg(eligible=('id','size'),genuine=('genuine','sum'),raw_admit=('raw_accept','sum'),final_admit=('accepted','sum')).reset_index()
    counts=p.groupby(['algo','category']).size().rename('candidates').reset_index()
    selected=full.groupby(['algo','category']).size().rename('selected').reset_index()
    coverage=counts.merge(selected,on=['algo','category'],how='left').fillna({'selected':0});coverage['coverage_pct']=100*coverage.selected/coverage.candidates
    coverage.to_csv(out/'coverage.csv',index=False);total.to_csv(out/'candidate_totals.csv',index=False)
    record=[]
    for (algo,cat),z in full.groupby(['algo','category']):
        record.append(dict(algo=algo,category=cat,pairs=len(z),next_action_changes=int(z.changed_next_edge.sum()),path_changes=int(z.changed_receiver_path.sum()),
            actual_delivery_helps=int(z.actual_delta_delivery.gt(0).sum()),actual_delivery_harms=int(z.actual_delta_delivery.lt(0).sum()),
            actual_utility_helps=int(z.actual_delta_utility.gt(TOL).sum()),actual_utility_harms=int(z.actual_delta_utility.lt(-TOL).sum()),
            utility_unchanged=int(z.actual_delta_utility.abs().le(TOL).sum()),mean_actual_utility_gain=z.actual_delta_utility.mean(),
            mean_abs_prediction_error=np.abs(z.predicted_value-z.delta_utility).mean()))
    causal=pd.DataFrame(record);causal.to_csv(out/'causal_effects.csv',index=False)
    key=['algo','seed','graph','case','episode','convoy','t','id']
    paired=prefix.merge(full,on=key,suffixes=('_prefix','_full'),validate='one_to_one')
    masking=[]
    for (algo,cat),z in paired.groupby(['algo','category_prefix']):
        masking.append(dict(algo=algo,category=cat,pairs=len(z),
            prefix_delivery_only=int((z.delta_delivery_prefix.ne(0)&z.delta_delivery_full.eq(0)).sum()),
            full_delivery_only=int((z.delta_delivery_prefix.eq(0)&z.delta_delivery_full.ne(0)).sum()),
            prefix_utility_only=int((z.delta_utility_prefix.abs().gt(TOL)&z.delta_utility_full.abs().le(TOL)).sum()),
            full_utility_only=int((z.delta_utility_prefix.abs().le(TOL)&z.delta_utility_full.abs().gt(TOL)).sum()),
            mean_abs_prefix=np.abs(z.delta_utility_prefix).mean(),mean_abs_full=np.abs(z.delta_utility_full).mean()))
    masking=pd.DataFrame(masking);masking.to_csv(out/'credit_context.csv',index=False)
    drift=[]
    for (algo,seed,stage),z in d.groupby(['algo','seed','stage']):
        drift.append(dict(algo=algo,seed=seed,stage=stage,labels=len(z),mae=np.abs(z.predicted_value-z.utility_gain).mean(),zero_mae=np.abs(z.utility_gain).mean(),mse=np.square(z.predicted_value-z.utility_gain).mean(),nonzero_labels=int(z.utility_gain.abs().gt(TOL).sum()),positive_delivery_labels=int(z.delivery_gain.gt(0).sum()),predicted_negative_rate=float((z.predicted_value-.5*z.uncertainty<=-1.).mean())))
    drift=pd.DataFrame(drift);drift.to_csv(out/'drift_by_seed.csv',index=False)
    macro=drift.groupby(['algo','stage']).agg(seeds=('seed','size'),labels=('labels','sum'),mae=('mae','mean'),zero_mae=('zero_mae','mean'),nonzero_labels=('nonzero_labels','sum'),positive_delivery_labels=('positive_delivery_labels','sum')).reset_index();macro.to_csv(out/'prediction_transport.csv',index=False)
    a=drift.pivot(index=['algo','seed'],columns='stage',values='mae');a['adapted_minus_warmup_mae']=a.adapted-a.warmup;a.to_csv(out/'drift_difference.csv')
    # Same fixed actors for all three methods, including SAFE reference from parent.
    static=pd.concat([raw,source[source.method.eq('SAFE')]],ignore_index=True)
    static['utility']=40*static.delivered-40*static.destroyed-40*static.censored-static.elapsed
    summary=static.groupby(['algo','method']).agg(convoys=('convoy','size'),delivery_pct=('delivered',lambda x:100*x.mean()),utility=('utility','mean')).reset_index();summary.to_csv(out/'static_comparison.csv',index=False)
    opening=[]
    for algo,z in p.groupby('algo'):
        peer_clear=z.blocked_report.eq(False)&z.peer_blocked.gt(.5)
        opening.append(dict(algo=algo,eligible=len(z),genuine_clear=int((z.genuine&~z.blocked_report).sum()),genuine_clear_against_warning=int((z.genuine&peer_clear).sum()),correct_clear_against_warning=int((peer_clear&~z.truth_at_decision).sum()),clear_against_warning=int(peer_clear.sum()),false_warnings=int((z.blocked_report&~z.truth_at_decision).sum()),false_warnings_forced_accepted=int((z.blocked_report&~z.truth_at_decision&z.rule.eq('preserve_credible_warning')).sum())))
    opening=pd.DataFrame(opening);opening.to_csv(out/'clearance_opportunities.csv',index=False)
    images=[];plt.rcParams.update({'font.size':10,'figure.dpi':140})
    with PdfPages(out/'gate_decision_diagnosis.pdf') as pdf:
        def save(fig,name):
            fig.savefig(out/(name+'.png'),bbox_inches='tight');fig.savefig(out/(name+'.pdf'),bbox_inches='tight');pdf.savefig(fig,bbox_inches='tight');images.append(name);plt.close(fig)
        fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
        cats=list(CAPS)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=coverage[coverage.algo==algo].set_index('category').reindex(cats).fillna(0)
            ax.bar(range(4),z.candidates);ax.set_xticks(range(4),[x.replace('_','\n') for x in cats]);ax.set_title(algo.upper());ax.set_ylabel('Eligible packet candidates')
            for i,r in enumerate(z.itertuples()):ax.text(i,r.candidates,f'{int(r.candidates)}\n({int(r.selected)} replayed)',ha='center',va='bottom',fontsize=9)
        fig.suptitle('What does learned filtering actually change?\nChronological stratified diagnostic subset');fig.tight_layout();save(fig,'01_gate_decisions')
        fig,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=causal[causal.algo==algo].set_index('category').reindex(cats).fillna(0);x=np.arange(4)
            ax.bar(x-.2,z.actual_delivery_helps,.2,label='Actual choice helps delivery');ax.bar(x,z.actual_delivery_harms,.2,label='Actual choice harms delivery');ax.bar(x+.2,z.next_action_changes,.2,label='Next action changes')
            ax.set_xticks(range(4),[c.replace('_','\n') for c in cats]);ax.set_title(algo.upper());ax.set_ylabel('Selected full-inbox replay pairs')
        axes[0].legend(fontsize=8);fig.suptitle('Accept/reject intervention, with all remaining packets retained');fig.tight_layout();save(fig,'02_causal_effects')
        fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=macro[macro.algo==algo].set_index('stage').reindex(['warmup','adapted']);x=np.arange(2)
            ax.bar(x-.18,z.mae,.36,label='Original model');ax.bar(x+.18,z.zero_mae,.36,label='Always predict zero');ax.set_xticks(x,['Warmup actor','Adapted actor']);ax.set_title(algo.upper());ax.legend()
        axes[0].set_ylabel('Mean absolute error (macro across 8 seeds)');fig.suptitle('Fresh training-style labels: prediction transport, no refitting');fig.tight_layout();save(fig,'03_prediction_transport')
        fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=a.loc[algo];ax.bar(z.index,z.adapted_minus_warmup_mae);ax.axhline(0,color='black',lw=1);ax.set_title(algo.upper());ax.set_xlabel('Paired actor seed')
        axes[0].set_ylabel('Adapted minus warmup prediction MAE');fig.suptitle('Positive: higher error after adaptation; changed encounters remain a confound');fig.tight_layout();save(fig,'04_drift_variation')
        fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=summary[summary.algo==algo].set_index('method').reindex(['SAFE','COMBINED','KEEP-WARNING']);ax.bar(range(3),z.delivery_pct);ax.set_xticks(range(3),['SAFE','COMBINED','KEEP-WARNING']);ax.set_ylim(0,105);ax.set_title(algo.upper())
        axes[0].set_ylabel('Actual delivery (%)');fig.suptitle('Same COMBINED-trained actor, same subset tapes; descriptive, no retraining');fig.tight_layout();save(fig,'05_static_rule')
        fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=masking[masking.algo==algo].set_index('category').reindex(['disagreement','warning_override']).fillna(0);x=np.arange(2)
            ax.bar(x-.18,z.mean_abs_prefix,.36,label='Prefix only');ax.bar(x+.18,z.mean_abs_full,.36,label='Full current inbox');ax.set_xticks(x,['Disagreement','Warning override']);ax.set_title(algo.upper());ax.legend()
        axes[0].set_ylabel('Mean absolute marginal receiver utility');fig.suptitle('Same packet, different credit context; both retain future transmissions');fig.tight_layout();save(fig,'06_credit_context')
    body='# Decision-level gate diagnosis\n\nExploratory diagnosis following the null matched-training primary result. No fitted gate or final routing checkpoint was changed. All figures and tables are descriptive.\n\n'
    body+=f'Exactly reproduced **512 original COMBINED trajectories / 2,560 convoy records**. Audited **{len(p):,} eligible packet candidates** and completed **{len(full):,} full-inbox accept/reject replay pairs** plus **{len(prefix):,} prefix-context pairs**. All sixteen reconstructed warmup actors matched their recorded network hashes.\n\n'
    for title,table in [('Candidate coverage and selection',coverage),('Selected causal packet effects',causal),('Prediction transport: equal weight per actor seed',macro),('Same actor, simple static comparison',summary),('Actual clearance opportunities',opening),('Credit-context comparison',masking)]:body+='## '+title+'\n\n'+table.to_markdown(index=False)+'\n\n'
    body+='## How to interpret these diagnostics\n\n'
    body+='The admission comparison holds earlier packet interpretation fixed: a disagreement is the learned gate changing the safeguards-only decision on the same public prefix. Category selection is chronological and capped per episode; replay frequencies are not unbiased population effect estimates. Packet effects are conditional and cannot be summed into the total gate effect. Each full-inbox branch matching the original choice reproduces the complete factual convoy outcomes. All remaining current-inbox packets and future events are retained, except in the separately identified prefix check.\n\n'
    body+='Warmup/adapted prediction errors use new layouts and tapes, the same original estimator, and the original label-generation routine. The two actors can visit different states and create different packets, so error differences do not isolate staleness as a causal explanation of the null. Compare the model with the zero-value predictor as well as with its own earlier errors. A lower adapted error is evidence against a blanket staleness explanation.\n\n'
    body+='KEEP-WARNING has no learned value model: it blocks every peer clearance of a fresh peer warning, including corroborated clearances. Own observations and the common TTL still apply. All three static-comparison methods use the COMBINED-trained actor. This can favor its familiar gate and is not a comparison of separately optimized systems or fresh confirmation. Check actual genuine reopening opportunities before treating a conservative rule as generally preferable. Correct forged payloads are possible; true origin and current truth are evaluator-only annotations.\n\n'
    body+='Delivery is binary and checked against convoy records. Utility includes failure and elapsed-time penalties. An elapsed-time reduction can arise from early destruction and is not an efficiency benefit; inspect accept_rows/reject_rows for paired successful convoy costs. No bandwidth, universal-superiority, equivalence or noninferiority claim follows. Original historical results remain unchanged.\n\n'
    body+='## Reproduce\n\nSee [the diagnosis protocol](../gate-decision-diagnosis-protocol.md). After running the diagnostic runner from simulator/, run this report from the repository root:\n\n```bash\nMPLCONFIGDIR=/tmp/aimrl-mpl OPENBLAS_NUM_THREADS=1 .venv/bin/python simulator/report_gate_diagnosis.py --run simulator/out/gate-decision-diagnosis --parent simulator/out/matched-gate-study --output revision/gate-decision-diagnosis\n```\n'
    (out/'README.md').write_text(body)
    html='<!doctype html><html><meta charset="utf-8"><title>Gate decision diagnosis</title><style>body{font:16px system-ui;max-width:1200px;margin:2rem auto;padding:1rem}img{width:100%}</style><h1>Gate decision diagnosis</h1><p>Exploratory mechanism diagnosis. Read README.md for selection, data and limits.</p>'
    for name in images:html+=f'<h2>{name.replace("_"," ")}</h2><img src="data:image/png;base64,{base64.b64encode((out/(name+".png")).read_bytes()).decode()}" alt="{name}">'
    (out/'index.html').write_text(html+'</html>')
    check=dict(status='passed',source_hash=fingerprint(),original_episodes_reproduced=512,original_convoys_reproduced=2560,eligible_candidates=len(p),full_replay_pairs=len(full),prefix_replay_pairs=len(prefix),warmup_hashes_verified=16,drift_label_samples=len(d),figures=len(images),deployed_models_refitted=False,new_confirmatory_tests=0)
    (out/'verification.json').write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check),flush=True)

if __name__=='__main__':main()
