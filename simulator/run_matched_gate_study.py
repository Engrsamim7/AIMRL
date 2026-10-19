"""Prospective matched-training 2x2 gate experiment; existing studies stay intact."""
import argparse
import copy
import hashlib
import heapq
import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from ammarl2.learn import LearnedPolicy, OBSERVATION_VERSION
from ammarl2.metrics import episode_metrics
from ammarl2.sim import DEPART
from guarded_research_gate import GuardedResearchPolicy
from research_gate import ValueEnsemble, FEATURES, public_features
from research_cases import Case, fork_graph
from run_cover_traffic_stress import simulation
from run_research_study import utility
from run_reviewer_revision import write_json, source_hash

ROOT = Path(__file__).resolve().parent
METHODS = ['ALL', 'SAFE', 'VALUE', 'COMBINED']
SEEDS = list(range(8))
# All arms see exactly the same training distribution and environment tapes.
TRAIN_CASES = [Case(f'train-r{r}-d{d}', spoof=r, delay=d, loss=.1, impersonation=.9)
               for r, d in [(2., 1.), (6., 1.), (2., 4.), (6., 4.)]] + [
    Case('train-honest'), Case('train-late', spoof=6., lead=0., delay=8., impersonation=.9),
    Case('train-redundant', spoof=6., full_sensing=True, impersonation=.9),
    Case('train-no-hazards', spoof=6., no_hazards=True, impersonation=.9)]
TEST_CASES = [replace(c, name=c.name.replace('train-', 'seen-')) for c in TRAIN_CASES[:4]] + [
    Case('unseen-r4-d2-loss20', spoof=4., delay=2., loss=.2, impersonation=.9),
    Case('unseen-r8-d1-loss20', spoof=8., delay=1., loss=.2, impersonation=.9),
    replace(TRAIN_CASES[5], name='late-control'), replace(TRAIN_CASES[7], name='no-hazard-control')]
DESIGN = dict(
    status='specified_before_any_new_training_or_test', algorithms=['dqn', 'mappo'], seeds=SEEDS,
    methods=METHODS, warmup_episodes=300, adaptation_episodes_per_arm=300,
    auxiliary_label_episodes_per_seed=160, auxiliary_fit_episodes=128,
    auxiliary_model='five bootstrap ridge regressors, ridge 10, training-only normalization',
    settings=dict(strength=12., threshold=-1., beta=.5, warning_confidence=.4),
    settings_selection='fixed from earlier research before this experiment; validation is diagnostic, no model/setting selection',
    fairness='each final actor has 300 common warmup + 300 arm-specific episodes; identical initial state, optimizer/replay/RNG and adaptation tapes within paired seed; auxiliary data shared/available to all arms but used only by value arms; total gate fitting compute is NOT equal',
    guards='identical warning/clearance constraints in SAFE and COMBINED; value-off uses constant admission score; this SAFE is a factorial safeguard baseline, not the previous SAFE-ALL implementation',
    value_model='fitted to frozen warmup ALL actor; fixed throughout adaptation and tests; estimates can become stale as actor adapts',
    layouts=dict(train='55000..55059, 2/3 forks', auxiliary='56000..56039, 2/3 forks', validation='57000..57003, 2/3 forks', test='58000..58015, 3/4 forks; 4-fork size held out'),
    tapes=dict(warmup='60000000 + seed*10000 + episode', auxiliary='61000000 + seed*10000 + episode', adaptation='62000000 + seed*10000 + episode', validation='63000000 + graph*10000 + case*100 + episode', test='64000000 + graph*10000 + case*100 + episode', mechanism='65000000 + graph*10000 + case*100 + episode'),
    validation_episodes_per_graph_case=3, test_episodes_per_graph_case=10, test_layouts=16,
    train_cases=[asdict(c) for c in TRAIN_CASES], test_cases=[asdict(c) for c in TEST_CASES],
    primary='COMBINED minus SAFE, delivery averaged equally over 8 cases, separately DQN/MAPPO (2 contrasts)',
    secondary_confirmatory='COMBINED minus ALL/SAFE/VALUE, each of 8 cases and 2 algorithms (48 contrasts)',
    correction='50 new delivery contrasts plus 198 earlier exploratory comparisons = 248 two-sided Bonferroni simultaneous intervals; 200000 crossed paired bootstrap draws',
    primary_success='corrected lower delivery-difference bound > 0 for the named algorithm; no improvement is assumed',
    mechanism='descriptive fixed-COMBINED-actor SAFE/COMBINED swaps on 4 fresh 3/4-fork layouts and independent tapes; not additional trained seeds or confirmatory tests',
    endpoints='full delivery primary; follower delivery, defined utility, elapsed/nominal costs among common survivors, packet admission and training time descriptive',
    limits=['structured fork benchmark, not operational validation', '8 independent paired training seeds per algorithm, not convoy count as replication', 'receiver filtering does not save transmitted bandwidth', 'forgery targets/payload independent of live hazards; honest-only channel loss; forged receiver injection', 'no test-driven retuning or case omission', 'initial common ALL warmup, not from-scratch gate-specific training', 'no guarantee of superiority or convergence'])


def fingerprint():
    h = hashlib.sha256(source_hash().encode())
    for name in ['research_gate.py', 'research_cases.py', 'guarded_research_gate.py', 'run_research_study.py', 'run_guarded_research_study.py', 'run_cover_traffic_stress.py', 'run_matched_gate_study.py']:
        h.update(name.encode()); h.update((ROOT/name).read_bytes())
    return h.hexdigest()


class AdmitAll:
    def predict(self, x):
        return 1., 0.


def policy(method, actor=None, model=None):
    if method not in METHODS:
        raise ValueError(method)
    learned = method in ['VALUE', 'COMBINED']
    guarded = method in ['SAFE', 'COMBINED']
    if learned and model is None:
        raise ValueError('Learned arm requires training-only value model')
    return GuardedResearchPolicy(method, mode='value', actor=actor,
        value_model=model if learned else AdmitAll(), weights='threat', use_obs=True,
        response_strength=12., relevance_scope='reachable', value_threshold=-1.,
        uncertainty_weight=.5, warning_confidence=.4,
        warning_guard=guarded, clearance_guard=guarded)


def examples(g, hazards, case, p, seed):
    """Matched chronological-prefix interventions under independent cover traffic."""
    assert p.actor is None or not p.actor.train
    snapshots=[]
    def capture(sim, cv, t):
        if not cv.inbox or len(snapshots)>=4:
            return
        hook=sim.before_decision; sim.before_decision=None
        try:
            shadow=copy.deepcopy(sim)
        finally:
            sim.before_decision=hook
        heapq.heappush(shadow.ev, (t, -1, DEPART, cv.id))
        snapshots.append((shadow, cv.id, t, sorted(copy.deepcopy(cv.inbox), key=lambda m:(m['t_obs'],m['id']))))
    factual=simulation(g,hazards,case,p,seed); factual.before_decision=capture; factual.run()
    rows=[]
    for snapshot,cid,t,messages in snapshots:
        prefix=[]
        for packet in messages:
            x,eligible=public_features(snapshot,snapshot.cv[cid],t,prefix,packet)
            if eligible:
                a,b=copy.deepcopy(snapshot),copy.deepcopy(snapshot)
                a.cv[cid].inbox=copy.deepcopy(prefix); b.cv[cid].inbox=copy.deepcopy(prefix+[packet])
                ra,rb=a.run(),b.run(); common=min(a.t,b.t)
                assert [v for v in a.attack_log if v[0]<=common]==[v for v in b.attack_log if v[0]<=common]
                rows.append(dict(zip(FEATURES,x)) | dict(utility_gain=utility(rb['rows'][cid])-utility(ra['rows'][cid]), delivery_gain=rb['rows'][cid]['delivered']-ra['rows'][cid]['delivered'], genuine=packet['genuine'], convoy=cid, packet_id=packet['id']))
            prefix.append(packet)
    return rows


def frozen(actor):
    result=copy.deepcopy(actor)
    result.train=False; result.eps=0.; result.buf=[]; result.pend={}; result.traj={}; result.losses=[]
    return result


def weight_hash(actor):
    h=hashlib.sha256()
    for k,v in actor.net.state_dict().items():
        h.update(k.encode()); h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def checkpoint(actor, path):
    torch.save(dict(source_hash=fingerprint(), observation_version=OBSERVATION_VERSION,
        parameters=asdict(actor), state_dict=actor.net.state_dict(), updates=actor.nupd,
        weight_hash=weight_hash(actor), warmup_episodes=300, adaptation_episodes=300),path)


def load_actor(path):
    data=torch.load(path,map_location='cpu',weights_only=True)
    assert data['source_hash']==fingerprint() and data['observation_version']==OBSERVATION_VERSION
    params=data['parameters']; params.update(train=False,eps=0.)
    actor=LearnedPolicy(**params); actor.net.load_state_dict(data['state_dict'])
    assert weight_hash(actor)==data['weight_hash']
    return actor


def train_job(task):
    algo,seed,folder=task; torch.set_num_threads(1); out=Path(folder)
    start=time.perf_counter(); rows=[]
    actor=LearnedPolicy(algo,algo=algo,seed=seed,train=True,comm='all',use_obs=True,weights='threat',relevance_scope='reachable')
    for ep in range(300):
        case=TRAIN_CASES[ep%8]; g,h=fork_graph(55000+ep%60,2+(ep//8)%2)
        actor.eps=max(.03,.5*(1-ep/420.))
        result=simulation(g,h,case,policy('ALL',actor),60000000+seed*10000+ep).run(); actor.end_episode()
        rows.append(dict(algo=algo,seed=seed,method='WARMUP',episode=ep,updates=actor.nupd,**episode_metrics(result['rows'])))
    initial=weight_hash(actor); warm_updates=actor.nupd; probe=frozen(actor); causal=[]
    for ep in range(160):
        case=TRAIN_CASES[ep%8]; g,h=fork_graph(56000+ep%40,2+(ep//8)%2)
        causal.extend(dict(episode=ep,case=case.name,**r) for r in examples(g,h,case,policy('ALL',probe),61000000+seed*10000+ep))
    df=pd.DataFrame(causal); fit=df[df.episode<128]; hold=df[df.episode>=128]
    assert len(fit)>50 and len(hold)>10
    model=ValueEnsemble().fit(fit[FEATURES],fit.utility_gain,66000+seed)
    pred=np.array([model.predict(x)[0] for x in hold[FEATURES].to_numpy()])
    df.to_csv(out/'value_models'/f'{algo}_s{seed}_examples.csv.gz',index=False)
    write_json(out/'value_models'/f'{algo}_s{seed}.json',dict(source_hash=fingerprint(), warmup_weight_hash=initial, examples=len(df),fit_examples=len(fit),holdout_examples=len(hold),holdout_mae=float(np.abs(pred-hold.utility_gain).mean()),model=model.state()))
    manifest=[]
    for method in METHODS:
        a=copy.deepcopy(actor); assert weight_hash(a)==initial
        armstart=time.perf_counter()
        for ep in range(300):
            case=TRAIN_CASES[ep%8]; g,h=fork_graph(55000+ep%60,2+(ep//8)%2)
            a.eps=max(.03,.5*(1-(300+ep)/420.))
            result=simulation(g,h,case,policy(method,a,model),62000000+seed*10000+ep).run(); a.end_episode()
            rows.append(dict(algo=algo,seed=seed,method=method,episode=300+ep,updates=a.nupd,**episode_metrics(result['rows'])))
        assert a.nupd>warm_updates
        checkpoint(a,out/'models'/f'{algo}_s{seed}_{method}.pt')
        manifest.append(dict(algo=algo,seed=seed,method=method,warmup_weight_hash=initial,final_weight_hash=weight_hash(a),warmup_updates=warm_updates,adaptation_updates=a.nupd-warm_updates,arm_training_seconds=time.perf_counter()-armstart,actor_exposure_episodes=600))
    pd.DataFrame(rows).to_csv(out/'training'/f'{algo}_s{seed}.csv.gz',index=False)
    print(f'TRAINED {algo} seed={seed}; {len(df)} causal labels; {time.perf_counter()-start:.1f}s',flush=True)
    return manifest


def evaluate_job(task):
    algo,seed,gi,split,folder=task; torch.set_num_threads(1); out=Path(folder)
    model=ValueEnsemble.load(json.loads((out/'value_models'/f'{algo}_s{seed}.json').read_text())['model'])
    actors={m:load_actor(out/'models'/f'{algo}_s{seed}_{m}.pt') for m in METHODS}
    before={m:weight_hash(a) for m,a in actors.items()}
    cases=TRAIN_CASES if split=='validation' else TEST_CASES
    base={'validation':57000,'test':58000,'mechanism':59000}[split]
    g,h=fork_graph(base+gi,2+gi%2 if split=='validation' else 3+gi%2)
    namespace={'validation':63000000,'test':64000000,'mechanism':65000000}[split]
    n=3 if split=='validation' else 10; rows=[]; raw=[]
    methods=['SAFE','COMBINED'] if split=='mechanism' else METHODS
    for ci,case in enumerate(cases):
        for ep in range(n):
            schedule=None
            for method in methods:
                a=actors['COMBINED'] if split=='mechanism' else actors[method]
                sim=simulation(g,h,case,policy(method,a,model),namespace+gi*10000+ci*100+ep)
                current=[(c.id,c.target,c.depart_t) for c in sim.cv]
                if schedule is None: schedule=current
                assert schedule==current
                result=sim.run(); key=dict(split=split,graph=gi,stages=2+gi%2 if split=='validation' else 3+gi%2,algo=algo,seed=seed,case=case.name,episode=ep,method=method)
                rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats'],follower_delivery=episode_metrics([r for r in result['rows'] if r['convoy']>=2])['delivery_rate'],utility_mean=float(np.mean([utility(r) for r in result['rows']]))))
                raw.extend(dict(**key,**r) for r in result['rows'])
    assert all(weight_hash(a)==before[m] for m,a in actors.items())
    return rows,raw


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='out/matched-gate-study');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    out=Path(args.output).resolve(); out.mkdir(parents=True,exist_ok=False)
    for folder in ['models','value_models','training']:(out/folder).mkdir()
    initial=fingerprint(); start=time.perf_counter()
    write_json(out/'design.json',dict(**DESIGN,source_hash=initial))
    write_json(out/'pipeline.json',dict(status='training',source_hash=initial))
    specs=[(a,s,str(out)) for a in ['dqn','mappo'] for s in SEEDS]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        trained=[]
        for result in pool.map(train_job,specs): trained.extend(result)
        pd.DataFrame(trained).to_csv(out/'training_manifest.csv',index=False)
        validation=[]
        for rows,_ in pool.map(evaluate_job,[(a,s,g,'validation',str(out)) for a,s,_ in specs for g in range(4)]): validation.extend(rows)
        pd.DataFrame(validation).to_csv(out/'validation.csv.gz',index=False)
        assert fingerprint()==initial
        write_json(out/'locked_settings.json',dict(status='locked_before_test',source_hash=initial,settings=DESIGN['settings'],validation_used_for_selection=False,checkpoints={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'models').glob('*.pt'))}))
        write_json(out/'pipeline.json',dict(status='testing',source_hash=initial))
        for split,graphs in [('test',16),('mechanism',4)]:
            episodes=[]
            for i,(rows,raw) in enumerate(pool.map(evaluate_job,[(a,s,g,split,str(out)) for a,s,_ in specs for g in range(graphs)])):
                episodes.extend(rows)
                pd.DataFrame(raw).to_csv(out/(split+'_convoys.csv'),index=False,mode='w' if i==0 else 'a',header=i==0)
                if (i+1)%16==0: print(f'{split}: {i+1} actor-layout jobs, {len(episodes)} episodes',flush=True)
            pd.DataFrame(episodes).to_csv(out/(split+'_episodes.csv.gz'),index=False)
    assert fingerprint()==initial
    write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,seconds=time.perf_counter()-start,independent_training_seeds_per_algorithm=8,checkpoints=64,unique_warmup_episodes=4800,arm_adaptation_episodes=19200,auxiliary_factual_episodes=2560,validation_episodes=6144,test_episodes=81920,mechanism_episodes=10240))
    print('MATCHED STUDY COMPLETE',flush=True)

if __name__=='__main__':main()
