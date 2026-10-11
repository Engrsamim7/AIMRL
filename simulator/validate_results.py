"""Audit completed reconstruction run artifacts without trusting exit codes alone."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from run_experiments import source_hash, write_json, standard_methods


def validate(root):
    report={'source_hash':source_hash(),'runs':{}}
    for path in sorted(root.iterdir()):
        if not path.is_dir() or not (path/'manifest.json').exists():
            continue
        m=json.loads((path/'manifest.json').read_text())
        assert m['status']=='completed',f'{path}: incomplete or failed run'
        assert m['source_hash']==source_hash(),f'{path}: different source version'
        args=m['arguments']; command=args['command']; row={'command':command,'seconds':m['elapsed_seconds']}
        if command=='train':
            curves=pd.read_csv(path/'training_curves.csv')
            expected=len(args['algos'])*len(args['comms'])*len(args['seeds'])*args['episodes']
            assert len(curves)==expected
            updates=curves.groupby(['algo','comm','seed']).optimizer_updates.max()
            assert updates.gt(0).all()
            assert curves.groupby(['algo','comm','seed']).last_loss.last().notna().all()
            assert np.isfinite(curves.last_loss.dropna()).all()
            assert len(list(path.glob('*.pt')))==len(updates)
            row.update(episodes=len(curves),checkpoints=len(updates),optimizer_updates_verified=True)
        elif command in ('evaluate','ablate'):
            raw=pd.read_csv(path/'convoys.csv')
            metrics=pd.read_csv(path/('episode_metrics.csv' if command=='evaluate' else 'ablation_metrics.csv'))
            assert set(metrics.graph_seed)==set(args['graphs'])
            expected_pairs={(gs,5*gs+ep) for gs in args['graphs'] for ep in range(args['eval_episodes'])}
            identity=['method','training_seed','nodes'] if command=='evaluate' else ['method','response_strength']
            if command=='evaluate':
                expected_policies={(p.name,None) for p in standard_methods().values()}
                if args['checkpoints']:
                    # Prefer the sibling copy when auditing an extracted portable bundle.
                    checkpoint_path=Path(args['checkpoints'])
                    portable=root/checkpoint_path.name
                    if portable.is_dir(): checkpoint_path=portable
                    records=json.loads((checkpoint_path/'checkpoints.json').read_text())
                    expected_policies.update((f"{r['algo']}-{r['comm']}",r['seed']) for r in records)
                for size,subset in metrics.groupby('nodes'):
                    actual={(r.method,None if pd.isna(r.training_seed) else int(r.training_seed))
                            for r in subset.itertuples()}
                    assert actual==expected_policies,f'{path}: missing or unexpected policy instances at {size} nodes'
                assert len(metrics)==len(expected_policies)*len(args['sizes'])*len(expected_pairs)
            for key,records in metrics.groupby(identity,dropna=False):
                assert set(zip(records.graph_seed,records.episode_seed))==expected_pairs
                assert len(records)==len(expected_pairs),f'{path}: missing or duplicated evaluations for {key}'
            if command=='ablate':
                assert len(metrics)==len(args['strengths'])*(2+2*len(args['etas'])*8)*len(expected_pairs)
            assert len(raw)==len(metrics)*args['convoys']
            keys=identity+['graph_seed','episode_seed']
            recalculated=raw.groupby(keys,dropna=False).agg(
                raw_delivery=('delivered','mean'),raw_destroyed=('destroyed','sum'),
                raw_censored=('censored','sum'),raw_blocked=('blocked_enc','sum')).reset_index()
            joined=metrics.merge(recalculated,on=keys,validate='one_to_one')
            assert len(joined)==len(metrics)
            assert np.allclose(joined.delivery_rate,joined.raw_delivery)
            assert np.allclose(joined.n_destroyed,joined.raw_destroyed)
            assert np.allclose(joined.n_censored,joined.raw_censored)
            assert np.allclose(joined.blocked_encounters_total,joined.raw_blocked)
            for column in ['blocked_enc','surprise_blocked_enc','hops']:
                assert raw[column].ge(0).all() and (raw[column]%1==0).all()
            assert raw.surprise_blocked_enc.le(raw.blocked_enc).all()
            assert (raw.delivered+raw.destroyed+raw.censored==1).all()
            delivered=raw[raw.delivered==1]
            assert (delivered.nominal>=delivered.nominal_optimal-1e-8).all()
            assert np.allclose(delivered.realized,delivered.travel+delivered.wait+delivered.service)
            b1=delivered[delivered.method=='B1']
            if len(b1): assert np.allclose(b1.nominal,b1.nominal_optimal)
            group=['graph_seed','episode_seed','convoy']+(['nodes'] if command=='evaluate' else [])
            for key, records in raw.groupby(group):
                assert records.target.nunique()==1 and records.depart_t.nunique()==1
            if command=='evaluate':
                assert set(raw.nodes)==set(args['sizes'])
                assert raw.groupby(['method','training_seed','nodes'],dropna=False).size().gt(0).all()
            elif 0 in args['strengths']:
                zero=raw[raw.response_strength==0]
                for key,records in zero.groupby(group):
                    for metric in ['nominal','delivered','blocked_enc','wait','realized']:
                        assert records[metric].nunique(dropna=False)==1
                row['zero_strength_outcomes_identical']=True
            row.update(episode_runs=len(metrics),convoy_records=len(raw),metric_invariants_verified=True)
            if command=='evaluate': row['node_sizes']=sorted(raw.nodes.unique().tolist())
        elif command=='fir':
            effects=pd.read_csv(path/'single_message_effects.csv')
            summaries=json.loads((path/'fir_summary.json').read_text())
            assert len(summaries)==len(args['graphs'])*args['eval_episodes']*len([c for c in args['comms'] if c!='none'])
            expected={(c,gs,5*gs+ep) for c in args['comms'] if c!='none'
                      for gs in args['graphs'] for ep in range(args['eval_episodes'])}
            assert {(s['method'],s['graph_seed'],s['episode_seed']) for s in summaries}==expected
            assert sum(s['selected_messages'] for s in summaries)==len(effects)
            full=args['max_messages'] is None
            if full: assert all(s['selected_messages']==s['processed_messages'] for s in summaries)
            assert not effects.duplicated(['method','graph_seed','episode_seed','message_id']).any()
            row.update(interventions=len(effects),all_processed_messages=full,
                       changed_receiver_paths=int(effects.changed_receiver_path.sum()))
        report['runs'][path.name]=row
    assert report['runs'],'No completed run manifests found'
    write_json(root/'validation.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_root',type=Path)
    validate(parser.parse_args().run_root)
