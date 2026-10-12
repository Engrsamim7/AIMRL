"""Validation-first, new-schedule adaptive gate experiment; preserve all outcomes."""
import argparse,copy,hashlib,json,itertools,time
from pathlib import Path
from dataclasses import asdict,replace
from functools import partial
import numpy as np
import pandas as pd
import torch
from adaptive_gate import AdaptiveGate
from ammarl2.policies import Policy
from ammarl2.graph import make_graph
from ammarl2.sim import Cfg,MSG
from ammarl2.reviewer import original_graph,ReviewerSim,m4_sensing,cc2_graph,cc2_factory,ScoutFixturePolicy,NETWORK
from ammarl2.metrics import episode_metrics
from ammarl2.counterfactual import single_message_effects
from run_reviewer_revision import load,source_hash as core_hash,write_json
from run_gate_fixtures import fixture_factory

ROOT=Path(__file__).resolve().parent
REGIMES=['reliable','delayed-spoof','heavy-spoof','reactive-spoof']

def fingerprint():
    h=hashlib.sha256(core_hash().encode())
    for name in ['adaptive_gate.py','run_adaptive_experiments.py']:
        h.update(name.encode());h.update((ROOT/name).read_bytes())
    return h.hexdigest()

def config(regime):
    c=Cfg(n_convoys=3,stagger=0,hub_cap=2,hub_service=1,tau_reveal=5,tau_msg=1,p_loss=0,spoof_rate=0,conf_mu=.85,conf_sd=.1,congestion_factor=.15,attack_rate=.5,attack_dur=(15,30),budget=5,p_kill=.7,horizon=300,allow_base_transit=True)
    if regime=='delayed-spoof':c=replace(c,tau_msg=4,p_loss=.2,spoof_rate=2)
    if regime=='heavy-spoof':c=replace(c,tau_msg=4,p_loss=.2,spoof_rate=8)
    if regime=='reactive-spoof':c=replace(c,tau_msg=4,p_loss=.2,spoof_rate=2,adv='reactive',spoof_mode='targeted')
    return c

class MixedSpoofSim(ReviewerSim):
    def do_spoof(self,t):
        first_seq=self.event_seq
        super().do_spoof(t)
        rng=np.random.default_rng(np.random.SeedSequence([self.seed,91873,self.spoof_seq]))
        for time_,seq,typ,payload in self.ev:
            if typ!=MSG or seq<first_seq:continue
            receiver,packet=payload
            clear=rng.random()<.6
            candidates=sorted(self.active) if clear else [e for e in range(self.g.m) if e not in self.active]
            if candidates:packet['e']=int(rng.choice(candidates))
            packet['blocked']=not clear
            packet['conf']=float(np.clip(rng.normal(.85,.1),.05,1.))
            impersonation=.25 if self.cfg.spoof_rate>=8 or self.cfg.adv=='reactive' else 0.
            packet['sender']=int(rng.integers(self.cfg.n_convoys)) if rng.random()<impersonation else -1

def graph_cases(validation=False,n=10):
    yield 0,'original-19',original_graph()
    start=18200 if validation else 19200
    count=1 if validation else n
    for size,layers,width in [(39,6,6),(51,4,12)]:
        for i in range(count):yield size*100+i,f'synthetic-{size}',make_graph(start+size+i,layers=layers,width=width)

def adaptive(name,params,**kwargs):
    return AdaptiveGate(name,weights='threat',use_obs=True,relevance_scope='reachable',**params,**kwargs)

def methods(params,ablate=False):
    common=dict(weights='threat',use_obs=True,response_strength=12.,relevance_scope='reachable')
    result=[Policy('NC',comm='none',**common),Policy('COMM-ALL',comm='all',**common),
            Policy('FRC',comm='gate',eta=1.,kappa_min=.6,**common),Policy('FRC-v2',comm='gate',eta=1.,kappa_min=.4,**common),
            adaptive('SOFT-NC',params,mode='none'),adaptive('SOFT-ALL',params,mode='all'),
            adaptive('SOFT-FRC',params,mode='frc'),adaptive('VALUE-GATE',params)]
    if ablate:
        result.append(adaptive('NO-CLEARANCE-GUARD',params,clearance_guard=False))
        result.append(adaptive('NO-FEEDBACK',params,adapt_reliability=False))
        altered=dict(params);altered['risk_aversion']=0.;result.append(adaptive('NO-RISK-AVERSION',altered))
        altered=dict(params);altered['age_scale']=1000000.;result.append(adaptive('NO-AGE-DISCOUNT',altered))
    return result

def tune(out):
    rows=[]
    for risk,age,value in itertools.product([0.,.25,.5],[2.,4.,8.],[.02,.1,.3]):
        params=dict(risk_aversion=risk,age_scale=age,min_value=value)
        for gid,family,g in graph_cases(True):
            for ri,regime in enumerate(REGIMES):
                c=config(regime)
                for ep in range(10):
                    p=adaptive('candidate',params);result=MixedSpoofSim(g,c,p,13000000+gid*1000+ri*100+ep,m4_sensing(g,True)).run()
                    met=episode_metrics(result['rows'])
                    rows.append(dict(**params,family=family,graph=gid,regime=regime,episode=ep,delivery=met['delivery_rate'],elapsed=met['realized_delivered_mean'],accepted=result['stats']['true_accepted']+result['stats']['spoof_accepted'],genuine_processed=sum(m['genuine'] for m in result['message_audit']),genuine_accepted=result['stats']['true_accepted']))
        print('validated '+json.dumps(params),flush=True)
    df=pd.DataFrame(rows);df.to_csv(out/'validation.csv',index=False)
    keys=['risk_aversion','age_scale','min_value'];rank=df.groupby(keys).agg(delivery=('delivery','mean'),elapsed=('elapsed','mean'),accepted=('accepted','mean'),genuine_processed=('genuine_processed','sum'),genuine_accepted=('genuine_accepted','sum')).reset_index()
    rank['genuine_admission']=rank.genuine_accepted/rank.genuine_processed.clip(lower=1);rank.to_csv(out/'validation_summary.csv',index=False)
    eligible=rank[rank.genuine_admission>=.05].sort_values(['delivery','elapsed','accepted']+keys,ascending=[False,True,True,True,True,True])
    if eligible.empty:raise RuntimeError('No active gate on validation; stop without inspecting test results')
    best=eligible.iloc[0];params={key:float(best[key]) for key in keys}
    write_json(out/'selected.json',dict(parameters=params,selection='highest mean delivery, then shorter delivered elapsed time, then fewer accepted packets; >=5% genuine admission; deterministic parameter tie order',validation_genuine_admission=float(best.genuine_admission),unknown_block_prior=.05,source_hash=fingerprint()))
    return params

def record(out,params,n_graphs,n_eval):
    rows=[];raw=[];audit=[];decisions=[]
    baseline_paths=sorted((ROOT/'out/reviewer-revision-v2/models').glob('*.pt'))
    if len(baseline_paths)!=20:raise RuntimeError('Require the 20 preserved baseline models; no silent omission')
    models=[load(p) for p in baseline_paths]
    (out/'baseline_models').mkdir()
    for p in baseline_paths:(out/'baseline_models'/p.name).write_bytes(p.read_bytes())
    for gid,family,g in graph_cases(False,n_graphs):
        for ri,regime in enumerate(REGIMES):
            c=config(regime)
            for ep in range(n_eval):
                policy_list=[(p,-1) for p in methods(params,ablate=True)]
                if gid==0:
                    for fitted in models:
                        for comm in ['all','gate']:
                            fitted.comm=comm;fitted.name=fitted.algo.upper()+('-ALL' if comm=='all' else '-FRC');fitted.eta=1.;fitted.kappa_min=.6
                            policy_list.append((copy.deepcopy(fitted),fitted.seed))
                schedules=None
                for p,seed in policy_list:
                    start=time.perf_counter();s=MixedSpoofSim(g,c,p,14000000+gid*1000+ri*100+ep,m4_sensing(g,True));result=s.run()
                    key=dict(family=family,graph=gid,regime=regime,episode=ep,method=p.name,training_seed=seed)
                    schedule=[(cv.id,cv.target,cv.depart_t) for cv in s.cv]
                    if schedules is None:schedules=schedule
                    assert schedules==schedule
                    rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats'],seconds=time.perf_counter()-start))
                    raw.extend(dict(**key,**r) for r in result['rows']);audit.extend(dict(**key,**m) for m in result['message_audit'])
                    if isinstance(p,AdaptiveGate):decisions.extend(dict(**key,**d) for d in result['decisions'])
        first=gid==0
        for name,records in [('convoys',raw),('messages',audit),('decisions',decisions)]:
            pd.DataFrame(records).to_csv(out/(name+'.csv'),index=False,mode='w' if first else 'a',header=first)
        raw.clear();audit.clear();decisions.clear()
        print('tested '+family+' graph='+str(gid),flush=True)
    pd.DataFrame(rows).to_csv(out/'episodes.csv',index=False)
    return rows

def controlled_factory(g,cfg,p,seed,hot=4,case='accurate'):
    if case!='impersonated-clear':return fixture_factory(g,cfg,p,seed,hot=hot,false_confidence=None if case=='accurate' else .2 if case=='low-clear' else .9)
    s=cc2_factory(g,cfg,p,seed,hot=hot);blocked=4 if hot==4 else 6
    for cv in [1,2]:
        s.stats['spoof_sent']+=1;s.push(3.,MSG,(cv,dict(id=f'impersonation:{seed}:{cv}',sender=0,e=blocked,t_obs=2.,blocked=False,conf=.9,genuine=False)))
    return s

def controlled(out,params):
    rows=[];raw=[];replays=[]
    for case in ['accurate','low-clear','high-clear','impersonated-clear']:
        for delay in [1.,4.]:
            for loss in [0.,.2]:
                for ep in range(50):
                    hot=4 if ep%2==0 else 5;g,_,_=cc2_graph(hot);c=Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=delay,p_loss=loss,tau_reveal=0,p_kill=1)
                    # False packets have the same configured delay as honest packets.
                    # At delay 4, adjust fixture injection to t=2+delay below.
                    policies=[ScoutFixturePolicy('NC',comm='none',use_obs=True,relevance_scope='reachable'),ScoutFixturePolicy('COMM-ALL',comm='all',use_obs=True,relevance_scope='reachable'),ScoutFixturePolicy('FRC',comm='gate',use_obs=True,relevance_scope='reachable')]+[adaptive(name,params,mode=mode,forced_scout_routes=True) for name,mode in [('SOFT-NC','none'),('SOFT-ALL','all'),('SOFT-FRC','frc'),('VALUE-GATE','value')]]
                    for p in policies:
                        sim=controlled_factory(g,c,p,15000000+ep,hot=hot,case=case)
                        # Existing fixture uses one-unit injection; re-time to configured delay.
                        sim.ev=[(2.+delay if typ==MSG and packet[1].get('genuine') is False else t,k,typ,packet) for t,k,typ,packet in sim.ev]
                        __import__('heapq').heapify(sim.ev)
                        result=sim.run();key=dict(case=case,delay=delay,loss=loss,episode=ep,method=p.name)
                        rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats']));raw.extend(dict(**key,**r) for r in result['rows'])
    pd.DataFrame(rows).to_csv(out/'controlled_episodes.csv',index=False);pd.DataFrame(raw).to_csv(out/'controlled_convoys.csv',index=False)
    c=Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=1,tau_reveal=0,p_kill=1);g,_,_=cc2_graph(4)
    for case in ['accurate','high-clear','impersonated-clear']:
        for ep in range(5):
            for p in [ScoutFixturePolicy('COMM-ALL',comm='all',use_obs=True,relevance_scope='reachable'),adaptive('SOFT-ALL',params,mode='all',forced_scout_routes=True),adaptive('VALUE-GATE',params,forced_scout_routes=True)]:
                frame,meta,_=single_message_effects(g,c,p,16000000+ep,simulator_factory=partial(controlled_factory,hot=4,case=case))
                frame['case']=case;frame['episode']=ep;frame['method']=p.name;replays.append(frame)
    pd.concat(replays,ignore_index=True).to_csv(out/'controlled_replay.csv',index=False)

def replay(out,params):
    g=original_graph();c=config('delayed-spoof');frames=[];meta=[]
    for ep in range(5):
        for p in [methods(params)[1],methods(params)[5],methods(params)[7]]:
            frame,m,_=single_message_effects(g,c,p,17000000+ep,simulator_factory=partial(MixedSpoofSim,sensing=m4_sensing(g,True)))
            frame['episode']=ep;frame['method']=p.name;frames.append(frame);meta.append(dict(episode=ep,method=p.name,**m))
    pd.concat(frames,ignore_index=True).to_csv(out/'replay.csv',index=False);write_json(out/'replay_manifest.json',meta)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='out/adaptive-gate-v2');ap.add_argument('--graphs',type=int,default=10);ap.add_argument('--episodes',type=int,default=30);a=ap.parse_args();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False);torch.set_num_threads(1);start=time.perf_counter();initial=fingerprint()
    write_json(out/'pipeline.json',dict(status='running',source_hash=initial,arguments=vars(a)))
    params=tune(out);rows=record(out,params,a.graphs,a.episodes);controlled(out,params);replay(out,params)
    assert fingerprint()==initial
    write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,core_source_hash=core_hash(),parameters=params,arguments=vars(a),evaluation_episodes=len(rows),seconds=time.perf_counter()-start,new_offline_training_episodes=0,reused_baseline_models=20,online_learning='per-convoy sender agreement from local observations; reset every episode',spoof_contract='60% false clear on adversary-known interdictions, 40% false block on other edges; 25% identity impersonation in heavy/reactive regimes',clearance_guard='two fresh claimed independent clear sources or direct local observation; preserved warning anchors expire at TTL',scope='original 19-node topology plus ten new graphs each at 39 and 51 nodes; declared mixed sensor coverage',limitations=['Approximate probabilities and sender agreement are not calibrated','No authenticated identity; multiple forged identities can invalidate clearance quorum','No learned deep gate; adaptive method is model-based routing and admission','Soft-fusion comparators isolate estimator changes from filtering','No general superiority or convergence assumed']))
    print('COMPLETE',flush=True)

if __name__=='__main__':main()
