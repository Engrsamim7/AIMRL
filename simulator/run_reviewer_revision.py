"""Execute reviewer follow-up on the recovered original topology.

Default: 20 fresh all-communication models, 300 episodes each; frozen-weight
none/all/gate evaluation. This isolates filtering at inference, not the effect
of separately training each communication mode. All results come from Sim runs.
"""
import argparse,copy,hashlib,json,multiprocessing,platform,time
from pathlib import Path
from dataclasses import asdict,replace
from concurrent.futures import ProcessPoolExecutor,as_completed
from functools import partial
import numpy as np
import pandas as pd
import torch
from ammarl2.graph import make_graph
from ammarl2.sim import Cfg,MSG
from ammarl2.policies import Policy
from ammarl2.learn import LearnedPolicy,OBSERVATION_VERSION
from ammarl2.reviewer import original_graph,NETWORK,ReviewerSim,m4_sensing,cc2_graph,cc2_factory,ScoutFixturePolicy
from ammarl2.metrics import episode_metrics
from ammarl2.counterfactual import single_message_effects

ROOT=Path(__file__).resolve().parent

def source_hash():
    h=hashlib.sha256()
    for p in sorted(list((ROOT/'ammarl2').glob('*.py'))+[Path(__file__).resolve()]):
        h.update(p.name.encode());h.update(p.read_bytes())
    h.update(NETWORK.read_bytes())
    return h.hexdigest()

def write_json(path,obj):
    def clean(v):
        if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [clean(x) for x in v]
        if isinstance(v,np.generic):return clean(v.item())
        if isinstance(v,float) and not np.isfinite(v):return None
        return v
    Path(path).write_text(json.dumps(clean(obj),indent=2,allow_nan=False)+'\n')

def base_config():
    return Cfg(n_convoys=3,stagger=0,hub_cap=2,hub_service=1,tau_reveal=5,tau_msg=2,
               congestion_factor=.15,attack_rate=.5,attack_dur=(15,30),budget=5,p_kill=.7,
               horizon=300,allow_base_transit=True)

def scenario(name):
    c=base_config()
    mixed='mixed' in name
    if 'disrupted' in name or 'reactive' in name:
        c=replace(c,tau_msg=4,p_loss=.2,spoof_rate=2,conf_mu=.85,conf_sd=.1)
    if 'reactive' in name:c=replace(c,adv='reactive',spoof_mode='targeted')
    return c,mixed

SCENARIOS=['uniform-clean','uniform-disrupted','mixed-disrupted','mixed-reactive']

def train_job(job):
    algo,seed,episodes,folder=job;torch.set_num_threads(1)
    g=original_graph();p=LearnedPolicy(f'{algo}-all',algo=algo,comm='all',use_obs=True,weights='threat',train=True,seed=seed,relevance_scope='reachable')
    rows=[];start=time.perf_counter()
    for ep in range(episodes):
        c,mixed=scenario(SCENARIOS[ep%len(SCENARIOS)])
        p.eps=max(.03,.4*(1-ep/max(1,.7*episodes)))
        s=ReviewerSim(g,c,p,1100000+seed*10000+ep,m4_sensing(g,mixed))
        result=s.run();p.end_episode()
        rows.append(dict(algo=algo,training_seed=seed,episode=ep,scenario=SCENARIOS[ep%4],
                         optimizer_updates=p.nupd,last_loss=p.losses[-1] if p.losses else None,
                         decisions=len(result['decisions']),**episode_metrics(result['rows'])))
    assert p.nupd>0
    torch.save(dict(observation_version=OBSERVATION_VERSION,source_hash=source_hash(),parameters=asdict(p),
                    episodes=episodes,optimizer_updates=p.nupd,state_dict=p.net.state_dict(),
                    agent_state_dicts={i:n.state_dict() for i,n in p.agent_nets.items()} if algo=='ippo' else {}),Path(folder)/f'{algo}_s{seed}.pt')
    pd.DataFrame(rows).to_csv(Path(folder)/f'{algo}_s{seed}_training.csv',index=False)
    return dict(algo=algo,seed=seed,episodes=episodes,updates=p.nupd,seconds=time.perf_counter()-start)

def load(path):
    v=torch.load(path,map_location='cpu',weights_only=True)
    if v['source_hash']!=source_hash() or v['observation_version']!=OBSERVATION_VERSION:raise ValueError('Source/checkpoint mismatch')
    params=v['parameters'];params.update(train=False,eps=0)
    p=LearnedPolicy(**params);p.net.load_state_dict(v['state_dict'])
    if p.algo=='ippo':
        p.train=True
        for i,state in v['agent_state_dicts'].items():p.agent_network(i).load_state_dict(state)
        p.train=False
    return p

def heuristics(eta=1.,kappa=.6,strength=12.):
    settings=dict(weights='threat',use_obs=True,response_strength=strength)
    return [Policy('NC',comm='none',**settings),Policy('ALL',comm='all',**settings),
            Policy('GATE-route',comm='gate',relevance_scope='route',**settings),
            Policy('GATE-static',comm='gate',scaling='static',eta=.4,relevance_scope='reachable',**settings),
            Policy('GATE-reachable',comm='gate',eta=eta,kappa_min=kappa,relevance_scope='reachable',**settings)]

def validate_selection(out):
    g=original_graph();rows=[]
    for eta in [.4,1.,2.]:
        for kappa in [.4,.6,.8]:
            for name in SCENARIOS:
                c,mixed=scenario(name)
                for ep in range(10):
                    p=Policy('candidate',weights='threat',use_obs=True,comm='gate',eta=eta,kappa_min=kappa,relevance_scope='reachable')
                    r=ReviewerSim(g,c,p,2100000+ep,m4_sensing(g,mixed)).run()
                    rows.append(dict(eta=eta,kappa=kappa,scenario=name,episode=ep,delivery=episode_metrics(r['rows'])['delivery_rate'],genuine_processed=sum(m['genuine'] for m in r['message_audit']),genuine_accepted=r['stats']['true_accepted']))
    df=pd.DataFrame(rows);df.to_csv(out/'validation.csv',index=False)
    summary=df.groupby(['eta','kappa']).agg(delivery=('delivery','mean'),genuine_processed=('genuine_processed','sum'),genuine_accepted=('genuine_accepted','sum')).reset_index()
    summary['genuine_admission']=summary.genuine_accepted/summary.genuine_processed.clip(lower=1)
    summary.to_csv(out/'validation_summary.csv',index=False)
    summary=summary[summary.genuine_admission>=.05].sort_values(['delivery','eta','kappa'],ascending=[False,True,True])
    if summary.empty:raise RuntimeError('No validation gate admits at least 5% of processed genuine reports; expand the validation grid or inspect sensing without evaluating test results')
    best=summary.iloc[0];selected=dict(eta=float(best.eta),kappa=float(best.kappa),criterion='mean actual delivery subject to >=5% genuine admission in validation; ties smaller eta then kappa',minimum_genuine_admission=.05,actual_validation_admission=float(best.genuine_admission),validation_seeds=[2100000+i for i in range(10)])
    write_json(out/'gate_selection.json',selected);return selected

def summarize_episodes(df,out):
    keys=['scenario','method'];summary=df.groupby(keys).agg(delivery=('delivery_rate','mean'),episodes=('delivery_rate','size'),nominal_delivered=('nominal_delivered_mean','mean'),realized_delivered=('realized_delivered_mean','mean'),sent=('msg_sent','mean'),accepted=('accepted','mean')).reset_index()
    summary.to_csv(out/'summary.csv',index=False)
    rng=np.random.default_rng(20261012);contrast=[]
    for scenario_name in SCENARIOS:
        sub=df[df.scenario==scenario_name]
        for group in ['heuristic','dqn','ppo','ippo','mappo']:
            if group=='heuristic':a='GATE-reachable';b='ALL'
            else:a=group.upper()+'-gate';b=group.upper()+'-all'
            left=sub[sub.method==a].set_index(['training_seed','episode']).delivery_rate
            right=sub[sub.method==b].set_index(['training_seed','episode']).delivery_rate
            delta=left.subtract(right);assert not delta.isna().any()
            arr=delta.unstack().to_numpy()
            boot=np.array([arr[rng.integers(arr.shape[0],size=arr.shape[0])][:,rng.integers(arr.shape[1],size=arr.shape[1])].mean() for _ in range(3000)])
            lo,hi=np.quantile(boot,[.025,.975]);contrast.append(dict(scenario=scenario_name,group=group,difference_pp=100*arr.mean(),lower_pp=100*lo,upper_pp=100*hi,uncertainty='paired episode and training-seed bootstrap; fixed original topology'))
    pd.DataFrame(contrast).to_csv(out/'contrasts.csv',index=False)

def evaluate(out,selected,n_eval):
    g=original_graph();models=[load(p) for p in sorted((out/'models').glob('*.pt'))];rows=[];raw=[];audit=[]
    for name in SCENARIOS:
        c,mixed=scenario(name)
        for ep in range(n_eval):
            policies=[(p,-1) for p in heuristics(selected['eta'],selected['kappa'])]
            for model in models:
                for comm in ['none','all','gate']:
                    model.comm=comm;model.name=model.algo.upper()+'-'+comm;model.eta=selected['eta'];model.kappa_min=selected['kappa']
                    # A fresh copy shares fitted parameters but no transient evaluation state.
                    policies.append((copy.deepcopy(model),model.seed))
            schedule=None
            for policy,ts in policies:
                t=time.perf_counter();sim=ReviewerSim(g,c,policy,3100000+ep,m4_sensing(g,mixed));result=sim.run()
                key=dict(scenario=name,method=policy.name,training_seed=ts,episode=ep)
                actual=[(r['convoy'],r['target'],r['depart_t']) for r in result['rows']]
                if schedule is None:schedule=actual
                assert schedule==actual
                met=episode_metrics(result['rows']);rows.append(dict(**key,**met,**result['stats'],accepted=result['stats']['true_accepted']+result['stats']['spoof_accepted'],seconds=time.perf_counter()-t))
                raw.extend(dict(**key,**r) for r in result['rows'])
                audit.extend(dict(**key,**m) for m in result['message_audit'])
        pd.DataFrame(rows).to_csv(out/'episodes.csv',index=False)
        print('evaluated '+name,flush=True)
    pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False);pd.DataFrame(audit).to_csv(out/'messages.csv',index=False)
    summarize_episodes(pd.DataFrame(rows),out)

def ablation(out,n_eval):
    g=original_graph();rows=[]
    for name in ['mixed-disrupted','mixed-reactive']:
        c,mixed=scenario(name)
        for ep in range(n_eval):
            zero=[]
            for strength in [0.,8.,12.]:
                for mask in range(8):
                    p=Policy(f'FRC{mask:03b}',weights='threat',use_obs=True,comm='gate',response_strength=strength,relevance_scope='reachable',gate_fresh=bool(mask&4),gate_rel=bool(mask&2),gate_conf=bool(mask&1))
                    result=ReviewerSim(g,c,p,3100000+ep,m4_sensing(g,mixed)).run()
                    rows.append(dict(scenario=name,episode=ep,strength=strength,mask=f'{mask:03b}',**episode_metrics(result['rows'])))
                    if strength==0:zero.append([(r['delivered'],r['nominal'],r['blocked_enc']) for r in result['rows']])
            assert all(z==zero[0] for z in zero)
    pd.DataFrame(rows).to_csv(out/'ablation.csv',index=False)

def cc2(out,n_eval):
    rows=[];raw=[];replay=[]
    for delay in [1.,4.,8.]:
        for loss in [0.,.2]:
            for ep in range(n_eval):
                hot=4 if ep%2==0 else 5;g,mask,_=cc2_graph(hot)
                c=Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=delay,p_loss=loss,tau_reveal=0,p_kill=1)
                for comm in ['none','all','gate']:
                    p=ScoutFixturePolicy(comm,comm=comm,use_obs=True,relevance_scope='reachable')
                    result=cc2_factory(g,c,p,4100000+ep,hot=hot).run()
                    key=dict(delay=delay,loss=loss,episode=ep,mode=comm,hot=hot)
                    rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats']))
                    raw.extend(dict(**key,**r) for r in result['rows'])
    pd.DataFrame(rows).to_csv(out/'cc2_episodes.csv',index=False);pd.DataFrame(raw).to_csv(out/'cc2_convoys.csv',index=False)
    g,mask,_=cc2_graph(4);c=Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=1,tau_reveal=0,p_kill=1)
    for ep in range(10):
        for comm in ['all','gate']:
            p=ScoutFixturePolicy(comm,comm=comm,use_obs=True,relevance_scope='reachable')
            f,m,_=single_message_effects(g,c,p,4100000+ep,simulator_factory=partial(cc2_factory,hot=4))
            f['episode']=ep;f['mode']=comm;replay.append(f)
    pd.concat(replay,ignore_index=True).to_csv(out/'cc2_replay.csv',index=False)

def replay_m4(out):
    g=original_graph();c,mixed=scenario('mixed-disrupted');frames=[];meta=[]
    for ep in range(4):
        for p in heuristics()[-1:]+[heuristics()[1]]:
            factory=partial(ReviewerSim,sensing=m4_sensing(g,mixed))
            f,m,_=single_message_effects(g,c,p,5100000+ep,simulator_factory=factory)
            f['episode']=ep;f['method']=p.name;frames.append(f);meta.append(dict(episode=ep,method=p.name,**m))
    pd.concat(frames,ignore_index=True).to_csv(out/'m4_replay.csv',index=False);write_json(out/'m4_replay_manifest.json',meta)

def scaling(out):
    rows=[]
    for size,layers,width in [(39,6,6),(51,4,12),(203,10,20),(483,20,24)]:
        for ep in range(2):
            g=make_graph(6000+ep,layers=layers,width=width);c,mixed=scenario('mixed-disrupted')
            for p in heuristics():
                t=time.perf_counter();r=ReviewerSim(g,c,p,6000000+ep,m4_sensing(g,mixed)).run()
                rows.append(dict(nodes=size,episode=ep,method=p.name,seconds=time.perf_counter()-t,**episode_metrics(r['rows'])))
    pd.DataFrame(rows).to_csv(out/'scaling.csv',index=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='out/reviewer-revision-v2');ap.add_argument('--episodes',type=int,default=300);ap.add_argument('--seeds',type=int,default=5);ap.add_argument('--eval',type=int,default=50);ap.add_argument('--workers',type=int,default=4)
    args=ap.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False);(out/'models').mkdir()
    torch.set_num_threads(1);start=time.perf_counter();initial=source_hash()
    write_json(out/'pipeline.json',dict(status='running',arguments=vars(args),source_hash=initial))
    jobs=[(algo,seed,args.episodes,str(out/'models')) for algo in ['dqn','ppo','ippo','mappo'] for seed in range(args.seeds)]
    records=[]
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        for future in as_completed([pool.submit(train_job,j) for j in jobs]):
            record=future.result();records.append(record);print('trained '+json.dumps(record),flush=True)
    write_json(out/'training_manifest.json',records)
    selected=validate_selection(out);print('validation selected '+json.dumps(selected),flush=True)
    evaluate(out,selected,args.eval);ablation(out,args.eval);print('ablation completed',flush=True)
    cc2(out,args.eval);replay_m4(out);scaling(out)
    assert source_hash()==initial
    write_json(out/'pipeline.json',dict(status='completed',arguments=vars(args),source_hash=initial,observation_version=OBSERVATION_VERSION,
      graph=dict(nodes=19,edges=64,original_json_sha256=hashlib.sha256(NETWORK.read_bytes()).hexdigest()),
      training_episodes=sum(r['episodes'] for r in records),models=len(records),base_config=asdict(base_config()),
      evaluation_seed_start=3100000,validation_seed_start=2100000,training_seed_start=1100000,seconds=time.perf_counter()-start,
      checks=['new checkpoint source hashes','identical convoy schedule within contrasts','zero-strength outcome equality','complete exogenous attack replay','unknown edges excluded from actor live telemetry'],
      limitations=['Frozen-weight communication comparison; modes not separately retrained','One original topology; no geographic generalization claim','300 episodes do not prove convergence','CC2 is controlled binary hazard fixture, not original route-threat-only outcome','Larger-graph inference only; fixed population and attack budget','Synthetic confidence scores; no authentication claim','Validation gate activity constraint added after discovering inactive v1; v2 uses new schedules']))
    print('COMPLETE',flush=True)

if __name__=='__main__':main()
