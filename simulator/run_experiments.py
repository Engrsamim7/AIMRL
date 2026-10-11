"""Versioned reconstruction experiments; old manuscript outputs are never reused.

Every command writes a new run directory with raw convoy records, explicit
metrics, source hashes, configuration, library versions and timing. Smoke runs
exercise code and must not be cited as scientific performance comparisons.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import resource
import sys
import time
import tracemalloc
import importlib.metadata
import numpy as np
import pandas as pd
import torch
from ammarl2.graph import make_graph
from ammarl2.sim import Sim, Cfg
from ammarl2.policies import Policy, standard_methods
from ammarl2.learn import LearnedPolicy, OBSERVATION_VERSION
from ammarl2.metrics import episode_metrics
from ammarl2.counterfactual import single_message_effects

ROOT = Path(__file__).resolve().parent
SIZES = {39:(6,6), 51:(4,12), 203:(10,20), 483:(20,24)}


def source_hash():
    digest=hashlib.sha256()
    for p in sorted(list((ROOT/'ammarl2').glob('*.py'))+[Path(__file__).resolve()]):
        digest.update(p.name.encode()); digest.update(p.read_bytes())
    return digest.hexdigest()


def write_json(path, value):
    def clean(x):
        if isinstance(x, dict): return {k:clean(v) for k,v in x.items()}
        if isinstance(x, (list,tuple)): return [clean(v) for v in x]
        if isinstance(x, np.generic): return clean(x.item())
        if isinstance(x, float) and not np.isfinite(x): return None
        return x
    path.write_text(json.dumps(clean(value),indent=2,allow_nan=False)+'\n')


def config(args):
    return Cfg(n_convoys=args.convoys,stagger=.5,hub_cap=1,hub_service=args.hub_service,
               tau_msg=args.delay,p_loss=args.loss,spoof_rate=args.spoof,
               adv=args.adversary,spoof_mode=args.spoof_mode,
               attack_rate=args.attack_rate,attack_dur=tuple(args.attack_duration),budget=args.budget,
               p_kill=args.p_kill,
               horizon=5000,react_delay=2,conf_mu=args.conf_mu,conf_sd=args.conf_sd)


def train(args, out):
    cfg=config(args); records=[]; curves=[]
    for algo in args.algos:
        for comm in args.comms:
            for seed in args.seeds:
                settings=dict(name=f'{algo}-{comm}',algo=algo,comm=comm,use_obs=True,
                              weights='threat',train=True,seed=seed)
                if args.smoke:
                    settings.update(dqn_warmup=32,dqn_batch_size=8,ppo_epochs=1)
                policy=LearnedPolicy(**settings)
                for ep in range(args.episodes):
                    gs=1+ep%40 # training graphs 1..40, never held-out 300+
                    policy.eps=max(.03,.4*(1-ep/max(1,.7*args.episodes)))
                    start=time.perf_counter()
                    sim=Sim(make_graph(gs,layers=6,width=6),cfg,policy,10000+seed*100000+ep)
                    result=sim.run(); policy.end_episode()
                    row=dict(algo=algo,comm=comm,seed=seed,episode=ep,graph_seed=gs,
                             seconds=time.perf_counter()-start,optimizer_updates=policy.nupd,
                             last_loss=policy.losses[-1] if policy.losses else None,
                             decisions=len(result['decisions']),**episode_metrics(result['rows']))
                    curves.append(row)
                    if (ep+1)%10==0 or ep+1==args.episodes:
                        print(f'{algo}/{comm}/seed={seed}: {ep+1}/{args.episodes} episodes; updates={policy.nupd}',flush=True)
                if policy.nupd==0:
                    raise RuntimeError(f'{algo}/{comm} had no optimizer updates; increase training budget')
                policy.train=False; policy.eps=0
                path=out/f'{algo}_{comm}_s{seed}.pt'
                torch.save(dict(observation_version=OBSERVATION_VERSION,
                                source_hash=source_hash(),parameters=asdict(policy),
                                sim_config=asdict(cfg),graph_kwargs=dict(layers=6,width=6),
                                trained_graph_seeds=list(range(1,41)),
                                episodes=args.episodes,smoke=args.smoke,
                                optimizer_updates=policy.nupd,
                                state_dict=policy.net.state_dict(),
                                agent_state_dicts={i:net.state_dict() for i,net in policy.agent_nets.items()}
                                if algo=='ippo' else {}),path)
                records.append(dict(path=str(path),algo=algo,comm=comm,seed=seed,
                                    updates=policy.nupd))
                pd.DataFrame(curves).to_csv(out/'training_curves.csv',index=False)
                write_json(out/'checkpoints.json',records)
                print(f'trained {algo}/{comm}/seed={seed}: {policy.nupd} updates',flush=True)
    pd.DataFrame(curves).to_csv(out/'training_curves.csv',index=False)
    write_json(out/'checkpoints.json',records)


def load_models(checkpoints, allow_smoke):
    policies=[]
    if checkpoints is None:
        return policies
    for path in sorted(Path(checkpoints).glob('*.pt')):
        saved=torch.load(path,map_location='cpu',weights_only=True)
        if not isinstance(saved,dict) or saved.get('observation_version')!=OBSERVATION_VERSION:
            raise ValueError(f'{path}: incompatible legacy checkpoint; retrain')
        if saved['source_hash']!=source_hash():
            raise ValueError(f'{path}: source changed since training; retrain with current source')
        if saved['smoke'] and not allow_smoke:
            raise ValueError('Smoke checkpoints require --smoke and cannot support final performance claims')
        params=saved['parameters']; params.update(train=False,eps=0.)
        policy=LearnedPolicy(**params); policy.net.load_state_dict(saved['state_dict'])
        if policy.algo=='ippo':
            policy.train=True
            for slot,weights in saved['agent_state_dicts'].items():
                policy.agent_network(slot).load_state_dict(weights)
            policy.train=False
        policies.append((policy,dict(checkpoint=str(path),training_seed=policy.seed)))
    if not policies:
        raise ValueError('No reconstructed checkpoints found')
    return policies


def evaluate(args,out):
    cfg=config(args); models=load_models(args.checkpoints,args.smoke)
    policies=[(p,dict(training_seed=None)) for p in standard_methods().values()]+models
    metrics=[]; raw=[]
    for size in args.sizes:
        layers,width=SIZES[size]
        gkw=dict(layers=layers,width=width)
        for gs in args.graphs:
            g=make_graph(gs,**gkw)
            for ep in range(args.eval_episodes):
                seed=5*gs+ep
                for policy,model_meta in policies:
                    if args.profile_memory: tracemalloc.start()
                    start=time.perf_counter()
                    sim=Sim(g,cfg,policy,seed); result=sim.run()
                    seconds=time.perf_counter()-start
                    peak=tracemalloc.get_traced_memory()[1] if args.profile_memory else None
                    if args.profile_memory: tracemalloc.stop()
                    identity=dict(method=policy.name,graph_seed=gs,episode_seed=seed,
                                  nodes=g.n,edges=g.m,**model_meta)
                    metrics.append(dict(**identity,seconds=seconds,python_peak_bytes=peak,
                                        process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                                        **episode_metrics(result['rows'])))
                    raw.extend(dict(**identity,**r) for r in result['rows'])
        pd.DataFrame(metrics).to_csv(out/'episode_metrics.csv',index=False)
        pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False)
        print(f'evaluated {size} nodes',flush=True)
    pd.DataFrame(metrics).to_csv(out/'episode_metrics.csv',index=False)
    pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False)
    # Paired CIs resample graph clusters after averaging episodes and training seeds.
    frame=pd.DataFrame(metrics); cis=[]
    for size in frame.nodes.unique():
        subset=frame[frame.nodes==size]
        baseline=subset[subset.method=='NC'].groupby('graph_seed').delivery_rate.mean()
        for method in subset.method.unique():
            values=subset[subset.method==method].groupby('graph_seed').delivery_rate.mean()
            delta=(values-baseline).dropna().to_numpy()
            if len(delta)<2: continue  # no meaningless CI from one graph
            samples=np.random.default_rng(0).choice(delta,size=(2000,len(delta))).mean(1)
            cis.append(dict(nodes=int(size),method=method,versus='NC',graphs=len(delta),
                            delivery_difference=float(delta.mean()),
                            lower=float(np.percentile(samples,2.5)),upper=float(np.percentile(samples,97.5))))
    write_json(out/'paired_graph_bootstrap.json',cis)


def ablate(args,out):
    cfg=config(args); rows=[]; raw=[]
    for strength in args.strengths:
        policies=[Policy('NC',weights='threat',use_obs=True,response_strength=strength),
                  Policy('ALL',weights='threat',use_obs=True,comm='all',response_strength=strength)]
        for rule in ('static','travel'):
            for eta in args.etas:
                for mask in range(8):
                    policies.append(Policy(f'{rule}-F{mask&1}-R{(mask>>1)&1}-C{(mask>>2)&1}-eta{eta}',
                                           weights='threat',use_obs=True,comm='gate',scaling=rule,
                                           eta=eta,gate_fresh=bool(mask&1),gate_rel=bool(mask&2),
                                           gate_conf=bool(mask&4),response_strength=strength))
        for gs in args.graphs:
            for ep in range(args.eval_episodes):
                g=make_graph(gs,layers=6,width=6); seed=5*gs+ep
                for p in policies:
                    result=Sim(g,cfg,p,seed).run()
                    identity=dict(method=p.name,response_strength=strength,graph_seed=gs,episode_seed=seed)
                    rows.append(dict(**identity,**episode_metrics(result['rows']),**result['stats']))
                    raw.extend(dict(**identity,**r) for r in result['rows'])
    pd.DataFrame(rows).to_csv(out/'ablation_metrics.csv',index=False)
    pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False)


def fir(args,out):
    cfg=config(args); rows=[]; summaries=[]
    for gs in args.graphs:
        for ep in range(args.eval_episodes):
            for comm in args.comms:
                if comm=='none': continue
                p=Policy(comm,comm=comm,use_obs=True,weights='threat')
                effects,meta,result=single_message_effects(make_graph(gs,layers=6,width=6),cfg,p,
                                                          5*gs+ep,args.max_messages)
                identity=dict(method=comm,graph_seed=gs,episode_seed=5*gs+ep)
                rows.extend(dict(**identity,**r) for r in effects.to_dict('records'))
                summaries.append(dict(**identity,**meta))
    pd.DataFrame(rows).to_csv(out/'single_message_effects.csv',index=False)
    write_json(out/'fir_summary.json',summaries)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['train','evaluate','ablate','fir'])
    parser.add_argument('--output',required=True,help='New directory; refusing overwrite')
    parser.add_argument('--smoke',action='store_true',help='Diagnostic run, not final scientific evidence')
    parser.add_argument('--threads',type=int,default=2)
    parser.add_argument('--convoys',type=int,default=30)
    parser.add_argument('--attack-rate',type=float,default=.6)
    parser.add_argument('--attack-duration',nargs=2,type=float,default=[20,40])
    parser.add_argument('--budget',type=int,default=8)
    parser.add_argument('--p-kill',type=float,default=.5)
    parser.add_argument('--hub-service',type=float,default=2)
    parser.add_argument('--conf-mu',type=float,default=1)
    parser.add_argument('--conf-sd',type=float,default=0)
    parser.add_argument('--profile-memory',action='store_true',help='Adds Python allocation instrumentation overhead')
    parser.add_argument('--delay',type=float,default=1)
    parser.add_argument('--loss',type=float,default=0)
    parser.add_argument('--spoof',type=float,default=0)
    parser.add_argument('--adversary',choices=['random','reactive'],default='random')
    parser.add_argument('--spoof-mode',choices=['exogenous','targeted'],default='exogenous')
    parser.add_argument('--algos',nargs='+',choices=['dqn','ppo','ippo','mappo'],default=['dqn','ppo','ippo','mappo'])
    parser.add_argument('--comms',nargs='+',choices=['none','all','gate'],default=['none','all','gate'])
    parser.add_argument('--seeds',nargs='+',type=int,default=[0,1,2])
    parser.add_argument('--episodes',type=int,default=300)
    parser.add_argument('--eval-episodes',type=int,default=5)
    parser.add_argument('--graphs',nargs='+',type=int,default=list(range(300,310)))
    parser.add_argument('--sizes',nargs='+',type=int,choices=list(SIZES),default=[39])
    parser.add_argument('--checkpoints')
    parser.add_argument('--strengths',nargs='+',type=float,default=[0,4,8,12,24])
    parser.add_argument('--etas',nargs='+',type=float,default=[.4,1,2])
    parser.add_argument('--max-messages',type=int,help='Limit FIR to an explicitly labeled diagnostic prefix')
    args=parser.parse_args()
    if args.threads<1 or args.episodes<1 or args.eval_episodes<1:
        parser.error('Thread and episode counts must be positive')
    if any(gs<300 for gs in args.graphs):
        parser.error('Evaluation graphs must be held-out (seed >=300)')
    out=Path(args.output).resolve(); out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(args.threads)
    manifest=dict(schema='reviewer-reconstruction-v2',observation_version=OBSERVATION_VERSION,
                  source_hash=source_hash(),argv=sys.argv,arguments=vars(args),
                  config=asdict(config(args)),python=platform.python_version(),
                  packages={n:importlib.metadata.version(n) for n in ['numpy','pandas','torch','scipy']},
                  purpose='smoke validation only' if args.smoke else 'experiment (convergence and protocol require review)',
                  status='running')
    write_json(out/'manifest.json',manifest)
    start=time.perf_counter()
    try:
        globals()[args.command](args,out)
    except Exception as exc:
        manifest.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        write_json(out/'manifest.json',manifest);raise
    manifest.update(status='completed',elapsed_seconds=time.perf_counter()-start)
    write_json(out/'manifest.json',manifest)


if __name__=='__main__':
    main()
