"""Development-only actor-aware admission: opportunity, fit, select, audit.

No historical test layouts/tapes are read or reclassified as new confirmation.
"""
import argparse
import copy
import hashlib
import heapq
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import pandas as pd
import torch
from ammarl2.sim import DEPART
from ammarl2.metrics import episode_metrics
from actor_aware_gate import FEATURES, ACTION_INDEX, LeafForest, policy
from recovery_gate import FEATURES as BASE_FEATURES, TRAIN, graph, simulation
from run_recovery_gate_study import load_actor, encoded_rows, fingerprint as parent_hash
from run_matched_gate_study import weight_hash
from run_research_study import utility
from run_reviewer_revision import write_json
ROOT=Path(__file__).resolve().parent
SEEDS=list(range(8));MODELS=['TREE_BASE','ACTOR_AWARE'];METHODS=['ALL','SAFE','KEEP','AGE']+MODELS
SIZES=dict(fit=256,calibration=64,audit=64)
BASES=dict(fit=91000,calibration=92000,audit=93000)
TAPES=dict(fit=800000000,calibration=810000000,audit=820000000)
GRID=[dict(beta=b,margin=m,delivery_tolerance=d) for b in [0.,.5,1.] for m in [0.,.5,1.] for d in [0.,.01]]
DESIGN=dict(status='specified_before_development_data',purpose='algorithm development and go/no-go diagnosis, NOT a new confirmatory superiority study',
 parent='recovery-gate-study SAFE-trained frozen actors, DQN/MAPPO, all8 seeds; no new routing training seeds',
 data='fresh training-distribution layouts and tapes only; original recovery final test never loaded; fit/calibration/audit layouts disjoint; all8 conditions crossed on every graph',
 splits=SIZES,layouts=BASES,tapes=TAPES,
 label_sampling='uniform at most6 reachable full-inbox actor-action-changing candidates and2 other candidates per factual SAFE episode; public selection only; no unused-slot borrowing',
 causal='one packet accepted/rejected, full inbox/future SAFE preserved; factual branch and both probed next actions checked; fleet utility/delivery targets',
 oracle='best nonnegative single sampled flip from each factual episode; privileged hindsight opportunity reference, NOT an attainable policy, global bound, summed packet effects or independent confirmation',
 learner='ExtraTrees160 depth8 leaf8 bootstrap80percent max_features80percent; two outputs: fleet utility and delivery gain from flipping SAFE; fit relevant action-changing examples only; fixed defaults, per routing seed',
 ablation='TREE_BASE original30 features vs ACTOR_AWARE original30+23 public full-inbox actor probe features; both same data, trees, relevance restriction, override budget and selection grid',
 authority='SAFE fallback, publicly reachable edge, actual full-inbox reference actor action changes; at most ONE learned override over entire fleet episode; remaining admissions SAFE; heuristic tree dispersion, not calibrated risk',
 grid=GRID,selection='separately per algorithm/model pooled calibration utility, delivery>=SAFE-1pp; if no option eligible deploy SAFE; explicit abstention candidate; ties prefer abstention then first candidate',
 audit='freeze selected options and all model/checkpoint hashes; evaluate all six methods on8 fresh2/3-fork development graphs x8conditions x8seeds x2algorithms =6144 method episodes; no audit-driven model changes',
 uncertainty='exploratory crossed bootstrap intervals conditional on existing routing checkpoints; not independent fresh algorithm-training replication or confirmatory superiority',
 advance='development evidence only; report predictive error vszero and paired fleet outcomes; a new superiority claim needs separately specified matched retraining and untouched confirmation',
 limitations=['one-override budget can miss joint-message benefits','SAFE remainder is deliberate reference context','no delayed-effect zero assumption from no next-action change','tree dispersion not calibrated','16 existing actors reused, not16 new independent seeds','small synthetic graphs, not operational validation','all conditions and negative findings retained'])


def fingerprint():
 h=hashlib.sha256(parent_hash().encode())
 for name in ['actor_aware_gate.py','run_actor_aware_development.py']:h.update(name.encode());h.update((ROOT/name).read_bytes())
 h.update((ROOT.parent/'requirements-actor-aware.txt').read_bytes());return h.hexdigest()


def one_episode(g,h,case,actor,tape):
 p=policy('SAFE',actor,collect=True);snapshots={}
 def capture(s,cv,t):
  if not cv.inbox:return
  hook=s.before_decision;s.before_decision=None;logs=s.policy.candidates;s.policy.candidates=[];probes=s.policy.probe_records;s.policy.probe_records={}
  try:shadow=copy.deepcopy(s)
  finally:s.before_decision=hook;s.policy.candidates=logs;s.policy.probe_records=probes
  shadow.policy.collect=False;heapq.heappush(shadow.ev,(t,-1,DEPART,cv.id));snapshots[(cv.id,float(t))]=shadow
 s=simulation(g,h,case,p,tape);s.before_decision=capture;factual=s.run();rng=np.random.default_rng(np.random.SeedSequence([tape,582]));chosen=[]
 relevant=lambda r:r['reachable']>.5 and r['probe_action_change']>.5
 for rows,cap in [([r for r in p.candidates if relevant(r)],6),([r for r in p.candidates if not relevant(r)],2)]:
  if rows:chosen.extend(rows[i] for i in sorted(rng.choice(len(rows),min(cap,len(rows)),replace=False)))
 labels=[];baseu=float(np.mean([utility(r) for r in factual['rows']]));based=float(np.mean([r['delivered'] for r in factual['rows']]))
 for r in chosen:
  snapshot=snapshots[(r['convoy'],r['t'])];branches=[]
  for accept in [True,False]:
   b=copy.deepcopy(snapshot);b.policy.force={(r['convoy'],r['t'],r['id']):accept};b.policy.force_hits=0;first=len(b.decisions);result=b.run();assert b.policy.force_hits==1
   assert b.decisions[first]['edge']==r['probe_accept_edge' if accept else 'probe_reject_edge']
   if accept==r['accepted']:assert encoded_rows(result['rows'])==encoded_rows(factual['rows'])
   branches.append((b,result['rows']))
  (a,ra),(b,rb)=branches;common=min(a.t,b.t);assert a.recovery_schedule==b.recovery_schedule
  assert [x for x in a.attack_log if x[0]<=common]==[x for x in b.attack_log if x[0]<=common]
  flip=rb if r['accepted'] else ra
  labels.append(dict(**r,flip_utility=float(np.mean([utility(x) for x in flip]))-baseu,flip_delivery=float(np.mean([x['delivered'] for x in flip]))-based,flip_receiver_utility=utility(flip[r['convoy']])-utility(factual['rows'][r['convoy']]),baseline_utility=baseu,baseline_delivery=based,accept_rows=encoded_rows(ra),reject_rows=encoded_rows(rb)))
 best=max([r['flip_utility'] for r in labels]+[0.]);bestrows=next((r for r in labels if r['flip_utility']==best),None) if best>0 else None
 return labels,dict(**episode_metrics(factual['rows']),utility_mean=baseu,eligible=len(p.candidates),action_candidates=sum(relevant(r) for r in p.candidates),sampled=len(labels),oracle_sampled_gain=best,oracle_delivery_gain=bestrows['flip_delivery'] if bestrows else 0.,oracle_packet_id=bestrows['id'] if bestrows else None),factual['rows']


def collect_job(task):
 algo,seed,parent,folder=task;torch.set_num_threads(1);out=Path(folder);a=load_actor(Path(parent)/'models'/f'{algo}_s{seed}_SAFE.pt');before=weight_hash(a);start=time.perf_counter();labels=[];episodes=[];raw=[]
 for split,n in SIZES.items():
  for ep in range(n):
   gi=ep//8;g,h=graph(BASES[split]+gi,2+gi%2);case=TRAIN[ep%8];key=dict(algo=algo,seed=seed,split=split,graph=gi,case=case.name,episode=ep)
   ls,summary,rs=one_episode(g,h,case,a,TAPES[split]+gi*10000+(ep%8)*100)
   labels.extend(dict(**key,**r) for r in ls);episodes.append(dict(**key,**summary));raw.extend(dict(**key,**r) for r in rs)
  print(f'COLLECTED {algo} seed={seed} {split}; cumulative labels={len(labels)}',flush=True)
 assert weight_hash(a)==before
 pd.DataFrame(labels).to_csv(out/'labels'/f'{algo}_s{seed}.csv.gz',index=False);pd.DataFrame(episodes).to_csv(out/'factual'/f'{algo}_s{seed}.csv.gz',index=False);pd.DataFrame(raw).to_csv(out/'factual'/f'{algo}_s{seed}_convoys.csv.gz',index=False)
 data=pd.DataFrame(labels);fit=data[(data.split=='fit') & data.reachable.gt(.5) & data.probe_action_change.gt(.5)];diagnostics=[]
 if len(fit)<24:raise RuntimeError(f'Insufficient actor-relevant fit labels: {algo} {seed} {len(fit)}; preserve data and report rather than silently change design')
 for method,features in [('TREE_BASE',BASE_FEATURES),('ACTOR_AWARE',FEATURES)]:
  m=LeafForest().fit(fit[features],fit[['flip_utility','flip_delivery']],95000+seed);m.save(out/'models'/f'{algo}_s{seed}_{method}.npz')
  diagnostics.append(dict(algo=algo,seed=seed,method=method,fit_examples=len(fit),routing_weight_hash=before))
 print(f'FIT {algo} seed={seed}; relevant labels={len(fit)}; {time.perf_counter()-start:.1f}s',flush=True);return diagnostics


def evaluate_job(task):
 algo,seed,split,parent,folder=task;torch.set_num_threads(1);out=Path(folder);a=load_actor(Path(parent)/'models'/f'{algo}_s{seed}_SAFE.pt');before=weight_hash(a)
 models={k:LeafForest.load(out/'models'/f'{algo}_s{seed}_{k}.npz') for k in MODELS};locked=None if split=='calibration' else json.loads((out/'locked_settings.json').read_text())['settings'][algo]
 rows=[];raw=[]
 for ep in range(SIZES[split]):
  gi=ep//8;g,h=graph(BASES[split]+gi,2+gi%2);case=TRAIN[ep%8];tape=TAPES[split]+gi*10000+(ep%8)*100
  for method in (['SAFE']+MODELS if split=='calibration' else METHODS):
   configs=[dict(abstain=True)]+GRID if method in MODELS and split=='calibration' else [locked[method] if method in MODELS else {}]
   for config,kw in enumerate(configs):
    kw=dict(kw);abstain=kw.pop('abstain',False);kind='SAFE' if abstain else 'LEARN' if method in MODELS else method
    if kind=='AGE':kw=dict(age_limit=8.,confidence=.4 if algo=='dqn' else .6)
    p=policy(kind,a,models.get(method),collect=True,**kw);s=simulation(g,h,case,p,tape);result=s.run();overrides=[r for r in p.candidates if r['rule']=='actor_value_override'];assert len(overrides)<=1
    key=dict(algo=algo,seed=seed,split=split,graph=gi,case=case.name,episode=ep,method=method,config=config)
    rows.append(dict(**key,**episode_metrics(result['rows']),utility_mean=float(np.mean([utility(r) for r in result['rows']])),overrides=len(overrides),accept_overrides=sum(r['accepted'] for r in overrides),reject_overrides=sum(not r['accepted'] for r in overrides),eligible=len(p.candidates)))
    if split=='audit':raw.extend(dict(**key,**r) for r in result['rows'])
 assert weight_hash(a)==before;print(f'EVALUATED {split} {algo} seed={seed}',flush=True);return rows,raw


def select_settings(df):
 settings={};records=[]
 for algo in ['dqn','mappo']:
  z=df[df.algo==algo];safe=z[z.method=='SAFE'].delivery_rate.mean();settings[algo]={}
  for method in MODELS:
   scores=z[z.method==method].groupby('config').agg(delivery=('delivery_rate','mean'),utility=('utility_mean','mean')).reset_index();scores['eligible']=scores.delivery>=safe-.01
   qualified=scores[scores.eligible];best=int(qualified.sort_values(['utility','config'],ascending=[False,True]).iloc[0]['config']) if len(qualified) else 0
   settings[algo][method]=dict(abstain=True) if best==0 else GRID[best-1];scores['selected']=scores.config.eq(best);scores['algo']=algo;scores['method']=method;records.extend(scores.to_dict('records'))
 return settings,records


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',default='out/recovery-gate-study');ap.add_argument('--output',default='out/actor-aware-development');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
 out=Path(args.output).resolve();parent=Path(args.parent).resolve();out.mkdir(parents=True,exist_ok=False)
 for sub in ['labels','factual','models']:(out/sub).mkdir()
 start=time.perf_counter();source=fingerprint();write_json(out/'design.json',dict(**DESIGN,source_hash=source));write_json(out/'pipeline.json',dict(status='collecting_development_data',source_hash=source))
 specs=[(a,s,str(parent),str(out)) for a in ['dqn','mappo'] for s in SEEDS]
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  manifest=[]
  for d in pool.map(collect_job,specs):manifest.extend(d)
  pd.DataFrame(manifest).to_csv(out/'fit_manifest.csv',index=False)
  write_json(out/'pipeline.json',dict(status='calibration',source_hash=source));cal=[]
  for rows,_ in pool.map(evaluate_job,[(a,s,'calibration',p,o) for a,s,p,o in specs]):cal.extend(rows)
  data=pd.DataFrame(cal);data.to_csv(out/'calibration.csv.gz',index=False);settings,selection=select_settings(data);pd.DataFrame(selection).to_csv(out/'selection.csv',index=False)
  assert fingerprint()==source
  write_json(out/'locked_settings.json',dict(status='locked_before_audit',source_hash=source,settings=settings,models={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'models').glob('*.npz'))},routing_models={f'{a}_s{s}_SAFE.pt':hashlib.sha256((parent/'models'/f'{a}_s{s}_SAFE.pt').read_bytes()).hexdigest() for a,s,_,_ in specs}))
  write_json(out/'pipeline.json',dict(status='development_audit',source_hash=source));episodes=[];raw=[]
  for rows,rs in pool.map(evaluate_job,[(a,s,'audit',p,o) for a,s,p,o in specs]):episodes.extend(rows);raw.extend(rs)
  pd.DataFrame(episodes).to_csv(out/'audit_episodes.csv.gz',index=False);pd.DataFrame(raw).to_csv(out/'audit_convoys.csv.gz',index=False)
 assert fingerprint()==source
 write_json(out/'pipeline.json',dict(status='completed',source_hash=source,seconds=time.perf_counter()-start,existing_routing_actors=16,new_routing_training_seeds=0,estimators=32,factual_development_episodes=6144,fit_factual_episodes=4096,calibration_method_episodes=39936,audit_method_episodes=6144))
 print('ACTOR-AWARE DEVELOPMENT COMPLETE',flush=True)
if __name__=='__main__':main()
