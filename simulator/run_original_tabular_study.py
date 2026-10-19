"""Original source reproduction followed by tabular-only repaired comparisons."""
import argparse
import copy
import hashlib
import json
import random
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
from original_tabular import legacy,FixedGateAgent,canonical_rows,repaired_episode,q_state,source_hashes,SOURCE
from run_reviewer_revision import write_json
ROOT=Path(__file__).resolve().parent
SEEDS=[42,137,271,999,1337]
MODES=['NONE','ALL','FRC','TRAVEL']
WEIGHTS={'code':dict(peer_weight=8.,local_weight=2.,delta=.05),'manuscript':dict(peer_weight=12.,local_weight=8.,delta=.15)}
CASES=[dict(name='clean',rb=0,reveal=5.,delay=2.,loss=0.),dict(name='original-contested',rb=2,reveal=5.,delay=2.,loss=0.),dict(name='delayed',rb=2,reveal=5.,delay=6.,loss=0.),dict(name='heavy-blocking',rb=4,reveal=5.,delay=2.,loss=0.),dict(name='loss20',rb=2,reveal=5.,delay=2.,loss=.2),dict(name='slow-reveal',rb=2,reveal=12.,delay=2.,loss=0.)]
DESIGN=dict(status='specified_before_training_and_comparison',purpose='faithful original reproduction and minimal tabular repairs, NOT a neural or learned-gate study',
 original=dict(topology_seed=42,nodes=19,edges=64,seeds=SEEDS,training_episodes=300,learned_evaluation_episodes=20,classical_evaluation_episodes=1,methods=['B1','B2','B3','IQL','NC','AMMARL','AMMARL_NOGAT','MAPPO_LABEL'],M4=dict(n_ag=3,rb=2,reveal=5.,hub_capacity=5,radius=1,delay=2.),CC2='2 unique NC/AMMARL paths x5 seeds x200 episodes; preserve original label-alias mapping, do not pretend seven independent algorithms'),
 execution='AST select unmodified original function/class bodies, run exact training/evaluation helpers; read-only trace instrumentation verified against direct originals; do not run presentation generator or top-level campaigns',
 reproduction_limits='source-execution reproduction, not verification of published constants or a universal fixed-environment bitwise historical reproduction; original eval epsilon.05 and top-level protocol retained',
 repair='same hub-indexed independent Q-learning, alpha.15,gamma.93,epsilon decay.992 floor.05,post-episode updates; connect genuine hazard source, edge-identify buffer, clear/reset, reject future/expired/duplicate packets, own timestamp precedence, stable event ties, recheck blocked retry, avoid self-counting hub capacity and release terminal slots; train only physically realized transitions with terminal mask; separate nominal/legacy costs and failure/censoring',
 source_assumption='observed revealed block maps to hazard1; observed base threat>=.25 or changed block emits confidence1; report generation continues in NONE so message overhead and unrelated RNG consumption remain matched',
 unchanged_physics='original event-driven traversal/congestion, original persistent red blocks and traffic-reactive busiest-edge wave; no destruction probability added; threat-score proxy is NOT delivery or survival probability; same19-node graph',
 repaired_train=dict(seeds=SEEDS,episodes=300,arms=MODES,weights=WEIGHTS,sensing=['uniform','mixed'],models=80,regimes='original M4 training config rb0/1/2 thirds, reveal5,delay2,loss0; six regimes are held-out evaluation sensitivities'),
 sensing='uniform radius1 is closest to original; mixed is separately labeled scientific refinement: C0 radius2, followers radius1 and public inter-hub blind-edge mask; unknown prior.35 at age-inf, not a fabricated clear observation',
 scoring='code8/2 delta.05 versus manuscript12/8 delta.15 is an explicit scoring-specification factor; all modes within each specification have identical coefficients; this factor changes weights AND fork criterion, so do not attribute its total effect to weights alone',
 gates='FRC eta.4 TTL8 confidence.6 immediate fork relevance; TRAVEL min(TTL,eta*own visible outgoing travel estimate),sameconfidence/relevance; no value learning or neural features',
 validation='4 fresh graph seeds100010..100013 x6cases x3 environment episodes x5 actor seeds; choose TRAVEL eta.4/.8/1.6 by pooled delivery then nominal all cost, fixed candidate order; FRC retains manuscript eta.4; weights unchanged',
 test='original graph42 plus8 fresh graph seeds100100..100107;6cases x10 environment episodes;80 separately trained tabular configurations;43200 method episodes129600convoys; original graph primary, fresh graphs transfer; no assumed generalization',
 tapes=dict(training='300000000+seed_index*10000+episode',validation='310000000+graph_index*10000+case_index*100+episode',test='320000000+graph_index*10000+case_index*100+episode'),
 contrasts='FRC minus ALL/NONE and selected TRAVEL minus FRC;2scoring specifications x2sensing contracts x2metrics(delivery,route-prior score on all convoys) x2topology scopes=48 pooled contrasts; all conditions descriptive',
 uncertainty='200000 crossed paired training-seed/environment bootstrap draws; Bonferroni436 =388 earlier+48 new contrasts; original graph inference conditions on that graph; fresh graph scope resamples graphs',
 limits=['not an operational simulator','original threat is a route score, no attack-induced killing model','original attack targets can depend on traffic; paired seeds are total policy comparisons, not identical exogenous attack tapes','uniform sensing can make delayed peer information redundant','small fixed training budget does not establish convergence','historical presentation constants remain unverified','mixed sensing/travel age are refinements, not bug fixes'])


def fingerprint():
 h=hashlib.sha256(json.dumps(source_hashes(),sort_keys=True).encode())
 for name in ['original_tabular.py','run_original_tabular_study.py']:h.update((ROOT/name).read_bytes())
 return h.hexdigest()


def historical_job(task):
 method,seed,folder=task;l=legacy();out=Path(folder);episodes=[];raw=[];agents=[];native_results=[];old_compute=l.core.ContestedRoutingSim._compute_stats;old_travel=l.core.ContestedRoutingSim._traversal_time;old_depart=l.core.ContestedRoutingSim._try_depart
 def record_depart(env,cid,policy,q_tables=None):
  previous=getattr(env,'_audit_cid',None);env._audit_cid=cid
  try:return old_depart(env,cid,policy,q_tables)
  finally:env._audit_cid=previous
 def record_travel(env,u,v):
  d=old_travel(env,u,v)
  if getattr(env,'_audit_cid',None) is not None:
   if not hasattr(env,'_audit_committed'):env._audit_committed=[]
   env._audit_committed.append(dict(convoy=env._audit_cid,u=u,v=v,depart=env.sim_time,arrive=env.sim_time+d,cost=env.edge_state[(u,v)]['cost']))
  return d
 def record_stats(env,cvs):
  result=old_compute(env,cvs);native_results.append(result);i=len(episodes);train=method not in ['B1','B2','B3'] and i<300
  key=dict(version='original',method=method,seed=seed,split='train' if train else 'evaluation',episode=i if train else i-300 if method not in ['B1','B2','B3'] else i)
  episodes.append(dict(**key,**result,hazard_entries=sum(len(a.hazard_buf) for a in agents if hasattr(a,'hazard_buf')),hazard_uses=sum(getattr(a,'msgs_used',0) for a in agents)))
  raw.extend(dict(**key,**r) for r in canonical_rows(env,cvs));return result
 def wrapper(base):
  class Recorded(base):
   def __init__(self,*a,**kw):super().__init__(*a,**kw);agents.append(self)
  return Recorded
 original_types={k:l.gated[k] for k in ['GatedQAgent','NoGateQAgent','MAPPOAgent']};original_q=l.marl.QAgent
 try:
  l.core.ContestedRoutingSim._compute_stats=record_stats;l.core.ContestedRoutingSim._traversal_time=record_travel;l.core.ContestedRoutingSim._try_depart=record_depart
  for name,cls in original_types.items():l.gated[name]=wrapper(cls)
  l.marl.QAgent=wrapper(original_q)
  make=lambda:l.core.make_network(seed=42)
  if method in ['B1','B2','B3']:summary=l.gated['run_classical'](method,make,2,5.,5,1,seed)
  elif method in ['IQL','NC']:summary,_=l.gated['train_eval_iql'](method,make,3,2,5.,5,1,seed)
  elif method=='AMMARL':summary,_=l.gated['train_eval_gated']('AMMARL',make,3,2,5.,5,1,seed)
  elif method=='AMMARL_NOGAT':summary,_=l.gated['train_eval_nogate'](make,3,2,5.,5,1,seed)
  elif method=='MAPPO_LABEL':summary,_=l.gated['train_eval_mappo'](make,3,2,5.,5,1,seed)
  else:raise ValueError(method)
 finally:
  l.core.ContestedRoutingSim._compute_stats=old_compute;l.core.ContestedRoutingSim._traversal_time=old_travel;l.core.ContestedRoutingSim._try_depart=old_depart;l.marl.QAgent=original_q;l.gated.update(original_types)
 for row,native in zip(episodes,native_results):row.update(native)
 if agents:write_json(out/'original_models'/f'{method}_s{seed}.json',dict(source_hash=fingerprint(),agents=q_state(agents)))
 pd.DataFrame(episodes).to_csv(out/'original'/f'{method}_s{seed}_episodes.csv.gz',index=False);pd.DataFrame(raw).to_csv(out/'original'/f'{method}_s{seed}_convoys.csv.gz',index=False)
 print(f'ORIGINAL {method} seed={seed} complete',flush=True);return dict(method=method,seed=seed,**summary)


def cc2_job(task):
 seed,folder=task;l=legacy();rows=[];raw=[]
 for mode in ['NC','AMMARL']:
  for ep in range(200):
   stats,sim,cvs=l.cc['run_cc2_episode'](seed*100000+ep,mode);key=dict(seed=seed,episode=ep,mode=mode)
   rows.append(dict(**key,**stats));raw.extend(dict(**key,**r) for r in canonical_rows(sim,cvs))
 print(f'ORIGINAL CC2 seed={seed} complete',flush=True);return rows,raw


def closest_repair_job(task):
 seed,folder=task;out=Path(folder);g=legacy().core.make_network(seed=42);agents=[FixedGateAgent(i,g.graph['targets'][i],mode='FRC',**WEIGHTS['code']) for i in range(3)];rows=[];raw=[]
 for ep in range(320):
  train=ep<300
  if not train:
   for a in agents:a.epsilon=.05
  stats,rs,env=repaired_episode(agents,seed+ep,rb=0 if ep<100 else 1 if ep<200 else 2,train=train)
  key=dict(version='closest-repair',method='AMMARL',seed=seed,split='train' if train else 'evaluation',episode=ep if train else ep-300)
  rows.append(dict(**key,**stats));raw.extend(dict(**key,**r) for r in rs)
 write_json(out/'closest'/f's{seed}_model.json',dict(source_hash=fingerprint(),agents=q_state(agents),evaluation_epsilon=.05))
 pd.DataFrame(rows).to_csv(out/'closest'/f's{seed}_episodes.csv.gz',index=False);pd.DataFrame(raw).to_csv(out/'closest'/f's{seed}_convoys.csv.gz',index=False)
 print(f'CLOSEST REPAIR seed={seed}',flush=True)


def train_job(task):
 weight,sensing,mode,si,folder=task;seed=SEEDS[si];out=Path(folder);g=legacy().core.make_network(seed=42);agents=[FixedGateAgent(i,g.graph['targets'][i],mode=mode,**WEIGHTS[weight]) for i in range(3)];rows=[]
 for ep in range(300):
  case=dict(CASES[1]);case.pop('name');case['rb']=0 if ep<100 else 1 if ep<200 else 2
  stats,_,_=repaired_episode(agents,300000000+si*10000+ep,sensing=sensing,train=True,**case)
  rows.append(dict(weight=weight,sensing=sensing,mode=mode,seed=seed,episode=ep,**stats))
 for a in agents:a.epsilon=0.
 name=f'{weight}_{sensing}_{mode}_s{seed}';write_json(out/'models'/(name+'.json'),dict(source_hash=fingerprint(),weight=weight,sensing=sensing,mode=mode,seed=seed,eta=.4,agents=q_state(agents)))
 pd.DataFrame(rows).to_csv(out/'training'/(name+'.csv.gz'),index=False)
 print(f'REPAIRED TRAIN {name}',flush=True);return dict(weight=weight,sensing=sensing,mode=mode,seed=seed,episodes=300)


def load_agents(path):
 state=json.loads(Path(path).read_text());assert state['source_hash']==fingerprint()
 agents=[]
 for row in state['agents']:
  a=FixedGateAgent(row['id'],row['target'],mode=state['mode'],eta=state['eta'],**WEIGHTS[state['weight']]);a.Q.clear()
  for s,acts in row['Q'].items():a.Q[int(s)].update({int(v):q for v,q in acts.items()})
  a.epsilon=0.;agents.append(a)
 return agents


def evaluate_job(task):
 weight,sensing,si,gi,split,folder=task;out=Path(folder);seed=SEEDS[si];validation=split=='validation';network_seed=100010+gi if validation else 42 if gi==0 else 100099+gi
 modes=['TRAVEL'] if validation else MODES;settings=None if validation else json.loads((out/'locked_settings.json').read_text())['travel_eta'];rows=[];raw=[]
 for mode in modes:
  agents=load_agents(out/'models'/f'{weight}_{sensing}_{mode}_s{seed}.json');before=json.dumps(q_state(agents),sort_keys=True)
  for eta in ([.4,.8,1.6] if validation else [settings[weight][sensing] if mode=='TRAVEL' else .4]):
   for a in agents:a.eta=eta
   for ci,c in enumerate(CASES):
    case=dict(c);name=case.pop('name')
    for ep in range(3 if validation else 10):
     stats,rs,env=repaired_episode(agents,(310000000 if validation else 320000000)+gi*10000+ci*100+ep,network_seed=network_seed,sensing=sensing,**case)
     key=dict(version='repaired',split=split,weight=weight,sensing=sensing,mode=mode,seed=seed,graph=gi,network_seed=network_seed,case=name,episode=ep,eta=eta)
     rows.append(dict(**key,**stats,route_score_all=float(np.mean([r['route_prior_score'] for r in rs]))))
     if not validation:raw.extend(dict(**key,**r) for r in rs)
  assert before==json.dumps(q_state(agents),sort_keys=True)
 return rows,raw


def select_eta(df):
 settings={}
 for w in WEIGHTS:
  settings[w]={}
  for sensing in ['uniform','mixed']:
   z=df[(df.weight==w)&(df.sensing==sensing)].groupby('eta').agg(delivery=('delivery_rate','mean'),nominal=('nominal_all_mean','mean')).reset_index().sort_values(['delivery','nominal','eta'],ascending=[False,True,True]);settings[w][sensing]=float(z.iloc[0].eta)
 return settings


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='out/original-tabular-study');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
 for sub in ['original','original_models','closest','models','training']:(out/sub).mkdir()
 initial=fingerprint();start=time.perf_counter();write_json(out/'design.json',dict(**DESIGN,source_hash=initial,original_sha256=source_hashes()));write_json(out/'pipeline.json',dict(status='original_reproduction',source_hash=initial))
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  originals=list(pool.map(historical_job,[(m,s,str(out)) for m in DESIGN['original']['methods'] for s in SEEDS]));pd.DataFrame(originals).to_csv(out/'original_summary.csv',index=False)
  cc=[];raw=[]
  for r,b in pool.map(cc2_job,[(s,str(out)) for s in SEEDS]):cc.extend(r);raw.extend(b)
  pd.DataFrame(cc).to_csv(out/'cc2_original.csv.gz',index=False);pd.DataFrame(raw).to_csv(out/'cc2_original_convoys.csv.gz',index=False)
  list(pool.map(closest_repair_job,[(s,str(out)) for s in SEEDS]))
  write_json(out/'pipeline.json',dict(status='repaired_training',source_hash=initial));specs=[(w,s,m,i,str(out)) for w in WEIGHTS for s in ['uniform','mixed'] for m in MODES for i in range(5)]
  list(pool.map(train_job,specs));validation=[]
  write_json(out/'pipeline.json',dict(status='validation',source_hash=initial))
  for r,_ in pool.map(evaluate_job,[(w,s,i,g,'validation',str(out)) for w in WEIGHTS for s in ['uniform','mixed'] for i in range(5) for g in range(4)]):validation.extend(r)
  df=pd.DataFrame(validation);df.to_csv(out/'validation.csv.gz',index=False);settings=select_eta(df);assert fingerprint()==initial
  write_json(out/'locked_settings.json',dict(status='locked_before_test',source_hash=initial,travel_eta=settings,models={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'models').glob('*.json')}));write_json(out/'pipeline.json',dict(status='testing',source_hash=initial));episodes=[]
  import gzip
  with gzip.open(out/'test_convoys.csv.gz','wt') as dest:
   for i,(r,b) in enumerate(pool.map(evaluate_job,[(w,s,i,g,'test',str(out)) for w in WEIGHTS for s in ['uniform','mixed'] for i in range(5) for g in range(9)])):
    episodes.extend(r);pd.DataFrame(b).to_csv(dest,index=False,header=i==0)
    if (i+1)%20==0:print(f'TEST {i+1}/180 jobs',flush=True)
  pd.DataFrame(episodes).to_csv(out/'test_episodes.csv.gz',index=False)
 assert fingerprint()==initial
 write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,seconds=time.perf_counter()-start,original_training_episodes=7500,original_M4_evaluation_episodes=515,original_CC2_unique_episodes=2000,closest_repair_training_episodes=1500,closest_repair_evaluation_episodes=100,repaired_training_episodes=24000,validation_episodes=4320,test_episodes=43200,repaired_tabular_models=80))
 print('ORIGINAL TABULAR STUDY COMPLETE',flush=True)
if __name__=='__main__':main()
