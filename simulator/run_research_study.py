"""Fresh opportunity benchmark, causal value training, and locked paired tests."""
import argparse
import copy
import hashlib
import heapq
import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ammarl2.learn import LearnedPolicy, OBSERVATION_VERSION
from ammarl2.metrics import episode_metrics
from ammarl2.reviewer import original_graph
from ammarl2.sim import DEPART
from research_cases import CASES, factory, fork_graph
from research_gate import ResearchPolicy, ValueEnsemble, FEATURES, public_features
from run_reviewer_revision import source_hash as core_hash, write_json

ROOT=Path(__file__).resolve().parent
METHODS=['NC','ALL','FRC','SAFE-ALL','VALUE','VALUE-NO-UNCERTAINTY','VALUE-NO-FEEDBACK']
DESIGN=dict(
    purpose='Bounded communication value study; no universal-superiority target',
    actor_algorithms=['dqn','mappo'],actor_training_seeds=[0,1,2],actor_training_episodes=600,
    value_training_episodes_per_actor=100,training_batch_selection='first four nonempty routing inboxes per episode; all eligible packets in each, chronological prefixes',
    value_fit_episodes_per_actor=80,value_internal_holdout_episodes_per_actor=20,
    value_estimator='five bootstrap ridge regressors; fixed ridge 10; training-only feature normalization',
    utility='40 delivered -40 destroyed -40 censored - elapsed time, per receiver',
    penalty_candidates=[12.,40.,80.],threshold_candidates=[-1.,0.,1.],uncertainty_candidates=[0.,.5],
    frc_eta_candidates=[1.,2.,4.,8.],frc_confidence_candidates=[.4,.6,.8],
    penalty_selection='validation ALL delivery, then lower delivered time, then lower penalty',
    gate_selection='pooled validation VALUE delivery, then shorter delivered time, then fewer admitted packets; >=5% genuine admission',
    actor_training_environment_seeds='40000000 + seed*10000 + episode',
    value_training_environment_seeds='40100000 + actor_index*10000 + episode',
    validation_environment_seeds='41000000+case_index*100+episode; distinct actor-independent schedules',
    test_environment_seeds='43000000+graph_index*10000+case_index*100+episode',
    layout_train='44000..44059; stages 2 or 3',layout_validation='45000..45014; stages 2 or 3',
    layout_test='47000..47009; stages 2 or 3; plus original graph bridge',
    test_episodes_per_graph_case=20,bridge_episodes_per_case=10,
    primary_scope='constructed multi-fork graphs; clearly declared two scouts/three followers, shared target, radius 2/1, blind fork edges except redundant-sensing control',
    primary_comparisons='VALUE vs ALL, FRC, SAFE-ALL in each of nine cases and three actor families; 81 simultaneous tests; hierarchy/crossed bootstrap',
    bridge_scope='original topology with same declared scout lead/shared target and original 20% coverage gaps; descriptive transfer check',
    caveats=['No guaranteed superiority; all cases published','Two unauthenticated identities are not independent observers','Constructed cases are mechanism benchmarks, not military operational validation','No tuning on earlier audit or new test results'],
    cases=[asdict(c) for c in CASES])


def fingerprint():
    h=hashlib.sha256(core_hash().encode())
    for name in ['research_gate.py','research_cases.py','run_research_study.py']:
        h.update(name.encode());h.update((ROOT/name).read_bytes())
    return h.hexdigest()


def make_policy(mode, strength, actor=None, model=None, settings=None, frc=None):
    aliases={'NC':'none','ALL':'all','FRC':'frc','SAFE-ALL':'safe','VALUE':'value','VALUE-NO-UNCERTAINTY':'value','VALUE-NO-FEEDBACK':'value'}
    settings=dict(settings or {})
    if mode=='VALUE-NO-UNCERTAINTY':settings['uncertainty_weight']=0.
    return ResearchPolicy(mode,weights='threat',use_obs=True,response_strength=strength,
                          relevance_scope='reachable',mode=aliases[mode],actor=actor,value_model=model,
                          learn_agreement=mode!='VALUE-NO-FEEDBACK',**settings,**(frc or {}))


def choose_strength(out):
    rows=[]
    for strength in DESIGN['penalty_candidates']:
        for ci,case in enumerate(CASES):
            for ep in range(15):
                g,h=fork_graph(45000+ep,2+ep%2)
                sim=factory(g,h,case,make_policy('ALL',strength),41000000+ci*100+ep)
                result=sim.run();rows.append(dict(strength=strength,case=case.name,episode=ep,**episode_metrics(result['rows'])))
    df=pd.DataFrame(rows);df.to_csv(out/'penalty_validation.csv',index=False)
    rank=df.groupby('strength').agg(delivery=('delivery_rate','mean'),elapsed=('realized_delivered_mean','mean')).reset_index()
    rank=rank.sort_values(['delivery','elapsed','strength'],ascending=[False,True,True])
    rank.to_csv(out/'penalty_selection.csv',index=False)
    return float(rank.iloc[0].strength)


def train_actor(job):
    algo,seed,strength,out,source_hash=job;torch.set_num_threads(1)
    actor=LearnedPolicy(algo,algo=algo,seed=seed,train=True,comm='all',use_obs=True,weights='threat',relevance_scope='reachable')
    policy=make_policy('ALL',strength,actor=actor);rows=[];start=time.perf_counter()
    for ep in range(DESIGN['actor_training_episodes']):
        case=CASES[ep%len(CASES)];g,h=fork_graph(44000+ep%60,2+ep%2)
        actor.eps=max(.03,.5*(1-ep/420.))
        sim=factory(g,h,case,policy,40000000+seed*10000+ep)
        result=sim.run();actor.end_episode()
        rows.append(dict(algo=algo,seed=seed,episode=ep,case=case.name,updates=actor.nupd,last_loss=actor.losses[-1] if actor.losses else np.nan,**episode_metrics(result['rows'])))
        if (ep+1)%100==0:print(f'Training {algo} seed={seed}: {ep+1}/600 episodes, {actor.nupd} updates',flush=True)
    assert actor.nupd>0
    path=Path(out)/'models'/f'{algo}_s{seed}.pt'
    torch.save(dict(source_hash=source_hash,observation_version=OBSERVATION_VERSION,parameters=asdict(actor),state_dict=actor.net.state_dict(),episodes=DESIGN['actor_training_episodes'],updates=actor.nupd),path)
    pd.DataFrame(rows).to_csv(path.with_suffix('.training.csv'),index=False)
    return dict(algo=algo,seed=seed,updates=actor.nupd,seconds=time.perf_counter()-start)


def load_actor(path):
    state=torch.load(path,map_location='cpu',weights_only=True)
    assert state['source_hash']==fingerprint() and state['observation_version']==OBSERVATION_VERSION
    params=state['parameters'];params.update(train=False,eps=0.)
    actor=LearnedPolicy(**params);actor.net.load_state_dict(state['state_dict'])
    return actor


def utility(row):
    return 40*row['delivered']-40*row['destroyed']-40*row['censored']-row['elapsed']


def causal_examples(g, hazards, case, policy, seed):
    """Chronological-prefix effects, with remaining current-inbox packets removed.

    Labels compare inclusion vs omission of one packet conditional on earlier
    packets. Both futures retain future transmissions and exogenous events.
    No test label or privileged state appears in the predictor features.
    """
    assert policy.mode=='all' and (policy.actor is None or not policy.actor.train)
    snapshots=[]
    def capture(sim,cv,t):
        if not cv.inbox or len(snapshots)>=4:return
        hook=sim.before_decision;sim.before_decision=None
        try:shadow=copy.deepcopy(sim)
        finally:sim.before_decision=hook
        heapq.heappush(shadow.ev,(t,-1,DEPART,cv.id))
        snapshots.append((shadow,cv.id,t,sorted(copy.deepcopy(cv.inbox),key=lambda m:(m['t_obs'],m['id']))))
    factual=factory(g,hazards,case,policy,seed);factual.before_decision=capture;factual.run()
    rows=[]
    for snapshot,cid,t,messages in snapshots:
        prefix=[]
        for packet in messages:
            features,eligible=public_features(snapshot,snapshot.cv[cid],t,prefix,packet)
            if eligible:
                without=copy.deepcopy(snapshot);with_=copy.deepcopy(snapshot)
                without.cv[cid].inbox=copy.deepcopy(prefix)
                with_.cv[cid].inbox=copy.deepcopy(prefix+[packet])
                a,b=without.run(),with_.run()
                common=min(without.t,with_.t)
                assert [x for x in without.attack_log if x[0]<=common]==[x for x in with_.attack_log if x[0]<=common]
                rows.append(dict(**dict(zip(FEATURES,features)),utility_gain=utility(b['rows'][cid])-utility(a['rows'][cid]),delivery_gain=b['rows'][cid]['delivered']-a['rows'][cid]['delivered'],changed_path=without.cv[cid].path!=with_.cv[cid].path,genuine=packet['genuine'],convoy=cid,decision_t=t,packet_id=packet['id']))
            prefix.append(packet)
    return rows


def actor_specs(out):
    yield 'planner',-1,None
    for path in sorted((out/'models').glob('*.pt')):
        actor=load_actor(path);yield actor.algo,actor.seed,actor


def train_values(out,strength):
    models={}
    for ai,(algo,seed,actor) in enumerate(actor_specs(out)):
        rows=[]
        for ep in range(DESIGN['value_training_episodes_per_actor']):
            case=CASES[ep%len(CASES)];g,h=fork_graph(44000+ep%60,2+ep%2)
            effects=causal_examples(g,h,case,make_policy('ALL',strength,actor=actor),40100000+ai*10000+ep)
            rows.extend(dict(algo=algo,seed=seed,episode=ep,case=case.name,**r) for r in effects)
        df=pd.DataFrame(rows);assert len(df)>50
        df.to_csv(out/'value_models'/f'{algo}_s{seed}_examples.csv',index=False)
        fit=df[df.episode<80];holdout=df[df.episode>=80]
        assert len(fit)>40 and len(holdout)>10
        model=ValueEnsemble().fit(fit[FEATURES],fit.utility_gain,88000+ai)
        predictions=np.array([model.predict(x)[0] for x in holdout[FEATURES].to_numpy()])
        evaluation=dict(holdout_examples=len(holdout),mean_absolute_error=float(np.abs(predictions-holdout.utility_gain).mean()),mean_squared_error=float(np.square(predictions-holdout.utility_gain).mean()),positive_delivery_labels=int((holdout.delivery_gain>0).sum()))
        write_json(out/'value_models'/f'{algo}_s{seed}.json',dict(source_hash=fingerprint(),actor=algo,seed=seed,examples=len(df),fitted_examples=len(fit),internal_holdout=evaluation,model=model.state(),target='included minus omitted receiver utility, chronological-prefix full-episode intervention'))
        models[(algo,seed)]=model
        print(f'Value model {algo} {seed}: {len(df)} causal examples, {(df.delivery_gain>0).sum()} positive delivery labels',flush=True)
    return models


def select_gate(out,strength,models):
    rows=[]
    for threshold in DESIGN['threshold_candidates']:
        for beta in DESIGN['uncertainty_candidates']:
            settings=dict(value_threshold=threshold,uncertainty_weight=beta)
            for algo,seed,actor in actor_specs(out):
                for ci,case in enumerate(CASES):
                    for ep in range(10):
                        g,h=fork_graph(45000+ep,2+ep%2)
                        policy=make_policy('VALUE',strength,actor=actor,model=models[(algo,seed)],settings=settings)
                        result=factory(g,h,case,policy,41000000+ci*100+ep).run()
                        rows.append(dict(threshold=threshold,beta=beta,algo=algo,seed=seed,case=case.name,episode=ep,genuine_processed=sum(bool(m['genuine']) for m in result['message_audit']),**episode_metrics(result['rows']),**result['stats']))
            print(f'Validated VALUE threshold={threshold} beta={beta}',flush=True)
    df=pd.DataFrame(rows);df.to_csv(out/'gate_validation.csv',index=False)
    rank=df.groupby(['threshold','beta']).agg(delivery=('delivery_rate','mean'),elapsed=('realized_delivered_mean','mean'),accepted=('true_accepted','sum'),genuine_processed=('genuine_processed','sum'),spoof_accepted=('spoof_accepted','sum')).reset_index()
    rank['genuine_admission']=rank.accepted/rank.genuine_processed.clip(lower=1)
    rank['total_accepted']=rank.accepted+rank.spoof_accepted
    rank.to_csv(out/'gate_selection.csv',index=False)
    eligible=rank[rank.genuine_admission>=.05].sort_values(['delivery','elapsed','total_accepted','threshold','beta'],ascending=[False,True,True,True,True])
    if eligible.empty:raise RuntimeError('No active validated gate; do not unlock test')
    best=eligible.iloc[0]
    settings=dict(value_threshold=float(best.threshold),uncertainty_weight=float(best.beta))
    write_json(out/'locked_settings.json',dict(status='locked_before_test',source_hash=fingerprint(),strength=strength,gate=settings,validation_genuine_admission=float(best.genuine_admission),test_results_inspected=False))
    return settings


def select_frc(out,strength):
    rows=[]
    for eta in DESIGN['frc_eta_candidates']:
        for kappa in DESIGN['frc_confidence_candidates']:
            for algo,seed,actor in actor_specs(out):
                for ci,case in enumerate(CASES):
                    for ep in range(10):
                        g,h=fork_graph(45000+ep,2+ep%2)
                        policy=make_policy('FRC',strength,actor=actor,frc=dict(eta=eta,kappa_min=kappa))
                        result=factory(g,h,case,policy,41000000+ci*100+ep).run()
                        rows.append(dict(eta=eta,kappa=kappa,algo=algo,seed=seed,case=case.name,episode=ep,**episode_metrics(result['rows']),**result['stats']))
            print(f'Validated FRC eta={eta} confidence={kappa}',flush=True)
    df=pd.DataFrame(rows);df.to_csv(out/'frc_validation.csv',index=False)
    rank=df.groupby(['eta','kappa']).agg(delivery=('delivery_rate','mean'),elapsed=('realized_delivered_mean','mean'),accepted=('true_accepted','sum'),spoof_accepted=('spoof_accepted','sum')).reset_index()
    rank['total_accepted']=rank.accepted+rank.spoof_accepted
    rank=rank.sort_values(['delivery','elapsed','total_accepted','eta','kappa'],ascending=[False,True,True,True,True])
    rank.to_csv(out/'frc_selection.csv',index=False)
    best=rank.iloc[0]
    return dict(eta=float(best.eta),kappa_min=float(best.kappa))


def test_job(job):
    gi,family,algo,seed,strength,settings,frc,folder=job;torch.set_num_threads(1);out=Path(folder)
    if family=='original-topology':g,h=original_graph(),()
    else:g,h=fork_graph(47000+gi,2+gi%2)
    actor=None if algo=='planner' else load_actor(out/'models'/f'{algo}_s{seed}.pt')
    model=ValueEnsemble.load(json.loads((out/'value_models'/f'{algo}_s{seed}.json').read_text())['model'])
    rows=[];convoys=[];messages=[]
    before={k:v.clone() for k,v in actor.net.state_dict().items()} if actor is not None else None
    for ci,case in enumerate(CASES):
        for ep in range(DESIGN['bridge_episodes_per_case'] if family=='original-topology' else DESIGN['test_episodes_per_graph_case']):
            schedule=None
            for method in METHODS:
                policy=make_policy(method,strength,actor=actor,model=model,settings=settings if method.startswith('VALUE') else None,frc=frc if method=='FRC' else None)
                sim=factory(g,h,case,policy,43000000+gi*10000+ci*100+ep,bridge=family=='original-topology')
                current=[(cv.id,cv.target,cv.depart_t) for cv in sim.cv]
                if schedule is None:schedule=current
                assert current==schedule
                result=sim.run();key=dict(family=family,graph=gi,algo=algo,seed=seed,case=case.name,episode=ep,method=method)
                met=episode_metrics(result['rows']);followers=episode_metrics([r for r in result['rows'] if r['convoy']>=2])
                rows.append(dict(**key,**met,**result['stats'],follower_delivery=followers['delivery_rate'],decisions=len(result['decisions']),utility_mean=np.mean([utility(r) for r in result['rows']])))
                convoys.extend(dict(**key,**r) for r in result['rows'])
                messages.extend(dict(**key,**m) for m in result['message_audit'])
    if actor is not None:assert all(torch.equal(v,before[k]) for k,v in actor.net.state_dict().items())
    return rows,convoys,messages


def test(out,strength,models,settings,frc,workers):
    rows=[]
    specs=[(algo,seed) for algo,seed,_ in actor_specs(out)]
    jobs=[(gi,'constructed-forks' if gi<10 else 'original-topology',algo,seed,strength,settings,frc,str(out)) for gi in range(11) for algo,seed in specs]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i,(episodes,convoys,messages) in enumerate(pool.map(test_job,jobs)):
            rows.extend(episodes)
            for name,records in [('convoys',convoys),('messages',messages)]:
                frame=pd.DataFrame(records);path=out/(name+'.csv')
                frame.to_csv(path,index=False,mode='w' if i==0 else 'a',header=i==0)
            if (i+1)%7==0:print(f'Tested layout {i//7}: {len(rows)} episodes',flush=True)
    pd.DataFrame(rows).to_csv(out/'episodes.csv',index=False)
    return len(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='out/research-opportunity-study');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'models').mkdir();(out/'value_models').mkdir();torch.set_num_threads(1)
    initial=fingerprint();start=time.perf_counter()
    write_json(out/'design.json',dict(source_hash=initial,design=DESIGN,status='specified_before_training_and_test'))
    write_json(out/'pipeline.json',dict(status='running',source_hash=initial))
    strength=choose_strength(out);print(f'Validation selected hazard penalty {strength}',flush=True)
    jobs=[(algo,seed,strength,str(out),initial) for algo in DESIGN['actor_algorithms'] for seed in DESIGN['actor_training_seeds']]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        trained=[]
        for result in pool.map(train_actor,jobs):
            trained.append(result);print('Trained '+json.dumps(result),flush=True)
    write_json(out/'training_manifest.json',trained)
    models=train_values(out,strength);settings=select_gate(out,strength,models)
    frc=select_frc(out,strength)
    write_json(out/'locked_settings.json',dict(status='locked_before_test',source_hash=initial,strength=strength,gate=settings,frc=frc,test_results_inspected=False))
    assert fingerprint()==initial
    count=test(out,strength,models,settings,frc,a.workers)
    assert fingerprint()==initial
    write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,core_source_hash=core_hash(),settings=dict(strength=strength,**settings,frc=frc),offline_actor_training_episodes=6*600,value_training_episodes=7*100,evaluation_episodes=count,seconds=time.perf_counter()-start,new_test_schedules=True,original_code_unchanged=True))
    print('COMPLETE',flush=True)


if __name__=='__main__':main()
