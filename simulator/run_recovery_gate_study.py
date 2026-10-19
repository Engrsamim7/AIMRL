"""Prospective dynamic-recovery experiment with complete-inbox causal labels."""
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
from ammarl2.sim import DEPART
from recovery_gate import FEATURES, METHODS, TRAIN, TEST, HurdleEnsemble, graph, policy, simulation
from run_matched_gate_study import frozen, weight_hash, fingerprint as parent_hash
from run_research_study import utility
from run_reviewer_revision import write_json
ROOT=Path(__file__).resolve().parent
SEEDS=list(range(8))
DESIGN=dict(status='specified_before_training_and_test',algorithms=['dqn','mappo'],seeds=SEEDS,methods=METHODS,
 warmup_episodes=300,adaptation_episodes=300,warmup_gate='SAFE',
 label_episodes_initial=64,label_episodes_refresh=64,label_fit_episodes_each=56,label_holdout_episodes_each=8,
 label_selection='uniform without replacement within public strata per episode: 4 clear-against-warning, 2 warnings, 2 other; no borrowing unused slots; full chronological episode reservoir, never outcome/origin selected',
 label_context='one eligible packet forced accepted versus rejected; retain full current inbox and all future messages; actual factual branch must reproduce every convoy outcome',
 label_target='receiver complete-episode utility acceptance minus rejection; delivery head predicts receiver delivery difference -1,0,+1',
 model='3 bootstrap two-layer 48-Tanh hurdle networks; impact abs(delta utility)>.1; conditional utility scale80; three-class delivery head; 100 Adam .003 steps; head risk and .5 bootstrap disagreement heuristic, not calibrated',
 refresh='after150 LEARN adaptation episodes collect64 fresh episodes with frozen current actor; refit on initial56+refresh56 episodes; holdouts never fitted; refresh conflates more data and actor transport',
 gate='SAFE fallback; both acceptance and rejection authority on publicly reachable edges; estimated abs(mean)-.5std > margin; estimated adverse delivery head <= risk limit; at most2 overrides per receiver per episode; outer timestamp/TTL/own precedence unchanged',
 fairness='600 routing episodes per final actor; deepcopy identical SAFE-warmup optimizer/replay/RNG; paired adaptation tapes; auxiliary data and compute extra for learned gate, not equal FLOPs',
 validation='8 fresh layouts,8 training conditions,2 episodes each per seed; select pooled frozen-actor utility, delivery >= SAFE-1pp; if no eligible option choose highest delivery then utility; no test retuning',
 validation_candidates=dict(LEARN=[dict(risk_limit=r,margin=m) for r in [.05,.15,.30] for m in [0.,1.]],AGE=[dict(age_limit=a,confidence=c) for a in [1.,2.,4.,8.] for c in [.4,.6,.8]]),
 training_settings=dict(risk_limit=.15,margin=.25,age_limit=4.,confidence=.6),
 primary='LEARN minus SAFE/KEEP/AGE, equal-case pooled mission utility and delivery separately per algorithm:12 contrasts',
 success='for a named baseline/algorithm utility corrected lower bound>0 AND delivery lower bound>-1 percentage point; this engineering noninferiority tolerance is not an operational safety guarantee',
 secondary='LEARN minus ALL/SAFE/KEEP/AGE,8 cases,2 algorithms,utility and delivery:128 contrasts',
 correction='140 new contrasts plus248 previously tested comparisons=388; two-sided Bonferroni intervals,200000 crossed seed/layout/episode bootstrap draws; historical intervals unchanged',
 endpoints='mission utility=40 delivered-40 destroyed-40 censored-elapsed per convoy, averaged over all5; delivery all5; no conditioning primary on survival',
 layouts=dict(train='80000..80079,2/3 forks',labels_initial='81000..81063,2/3',labels_refresh='81100..81163,2/3',validation='82000..82007,2/3',test='83000..83015,3/4;4-fork size held out',mechanism='84000..84003,3/4'),
 tapes=dict(warmup=70000000,adaptation=71000000,labels_initial=72000000,labels_refresh=73000000,validation=74000000,test=75000000,mechanism=76000000),
 physics='one initially blocked cheap branch per stage; independent recovery coin; expiry earliest nominal arrival at approach + uniform1.2..3.5 if temporary,35..50 otherwise; scouts physically observe changes; no injected honest reports; hidden schedule never a feature; graph expensive bypass scale uniform1..1.5 train,1..2 test',
 forgery='public corridor targets uniform; blocked payload faircoin independent of truth; honest confidence distribution;90percent claimed identity impersonation; only honest channel subject to loss',
 train_cases=[asdict(c) for c in TRAIN],test_cases=[asdict(c) for c in TEST],
 test_episodes=102400,mechanism='LEARN trained actor swapped among LEARN,REJECT_ONLY,INITIAL_MODEL on4 fresh layouts,5 episodes/case; descriptive only; initial-vs-refreshed conflates data quantity and actor change',
 limitations=['constructed fork topology, not realistic operational validation','8 paired training seeds per algorithm; convoy count not replication','receiver filtering does not reduce transmitted bandwidth','validation tunes inference settings of default-trained actors','all cases and failures retained','no assumed win or universal superiority'])


def fingerprint():
 h=hashlib.sha256(parent_hash().encode())
 for name in ['recovery_gate.py','run_recovery_gate_study.py']:h.update(name.encode());h.update((ROOT/name).read_bytes())
 return h.hexdigest()


def encoded_rows(rows):
 return json.dumps([{k:(None if isinstance(v,(float,np.floating)) and not np.isfinite(v) else v) for k,v in r.items()} for r in rows],default=lambda x:x.item(),allow_nan=False)


def causal_examples(g,h,case,p,seed):
 assert p.actor is None or not p.actor.train
 p.collect=True;snapshots={}
 def capture(s,cv,t):
  if not cv.inbox:return
  hook=s.before_decision;s.before_decision=None;logs=s.policy.candidates;s.policy.candidates=[]
  try:shadow=copy.deepcopy(s)
  finally:s.before_decision=hook;s.policy.candidates=logs
  shadow.policy.collect=False;heapq.heappush(shadow.ev,(t,-1,DEPART,cv.id));snapshots[(cv.id,float(t))]=shadow
 s=simulation(g,h,case,p,seed);s.before_decision=capture;factual=s.run();chosen=[]
 rng=np.random.default_rng(np.random.SeedSequence([seed,594]))
 groups=[([r for r in p.candidates if r['clear_against_warning']>.5],4),([r for r in p.candidates if r['blocked_report']],2),([r for r in p.candidates if not r['blocked_report'] and r['clear_against_warning']<.5],2)]
 for candidates,cap in groups:
  if candidates:chosen.extend(candidates[i] for i in sorted(rng.choice(len(candidates),min(cap,len(candidates)),replace=False)))
 rows=[]
 for r in chosen:
  snapshot=snapshots[(r['convoy'],r['t'])];branches=[]
  for accept in [True,False]:
   b=copy.deepcopy(snapshot);b.policy.force={(r['convoy'],r['t'],r['id']):accept};b.policy.force_hits=0
   result=b.run();assert b.policy.force_hits==1
   if accept==r['accepted']:assert encoded_rows(result['rows'])==encoded_rows(factual['rows'])
   branches.append((b,result['rows']))
  (a,ra),(b,rb)=branches;common=min(a.t,b.t)
  assert [x for x in a.attack_log if x[0]<=common]==[x for x in b.attack_log if x[0]<=common]
  assert a.recovery_schedule==b.recovery_schedule
  cid=r['convoy'];rows.append(dict(**r,utility_gain=utility(ra[cid])-utility(rb[cid]),delivery_gain=ra[cid]['delivered']-rb[cid]['delivered'],accept_rows=encoded_rows(ra),reject_rows=encoded_rows(rb)))
 return rows


def fit_model(data,seed):
 fit=data[data.episode<56];hold=data[data.episode>=56]
 assert len(fit)>50 and len(hold)>5
 m=HurdleEnsemble().fit(fit[FEATURES],fit.utility_gain,fit.delivery_gain,seed)
 predictions=np.array([m.predict(x)[0] for x in hold[FEATURES].to_numpy()])
 return m,dict(examples=len(data),fit_examples=len(fit),holdout_examples=len(hold),holdout_mae=float(np.abs(predictions-hold.utility_gain).mean()),holdout_zero_mae=float(np.abs(hold.utility_gain).mean()),holdout_effect_fraction=float((hold.utility_gain.abs()>.1).mean()))


def checkpoint(a,path):
 torch.save(dict(source_hash=fingerprint(),observation_version=OBSERVATION_VERSION,parameters=asdict(a),state_dict=a.net.state_dict(),weight_hash=weight_hash(a)),path)


def load_actor(path):
 d=torch.load(path,map_location='cpu',weights_only=True);assert d['source_hash']==fingerprint() and d['observation_version']==OBSERVATION_VERSION
 params=d['parameters'];params.update(train=False,eps=0.);a=LearnedPolicy(**params);a.net.load_state_dict(d['state_dict']);assert weight_hash(a)==d['weight_hash'];return a


def train_job(task):
 algo,seed,folder=task;torch.set_num_threads(1);out=Path(folder);start=time.perf_counter();rows=[]
 a=LearnedPolicy(algo,algo=algo,seed=seed,train=True,comm='all',use_obs=True,weights='threat',relevance_scope='reachable')
 for ep in range(300):
  g,h=graph(80000+ep%80,2+(ep//8)%2);a.eps=max(.03,.5*(1-ep/420.))
  result=simulation(g,h,TRAIN[ep%8],policy('SAFE',a),70000000+seed*10000+ep).run();a.end_episode()
  rows.append(dict(algo=algo,seed=seed,method='WARMUP',episode=ep,updates=a.nupd,**episode_metrics(result['rows'])))
 initial=weight_hash(a);warmupdates=a.nupd;probe=frozen(a);examples=[]
 for ep in range(64):
  g,h=graph(81000+ep,2+(ep//8)%2);method=['ALL','SAFE','KEEP','AGE'][(ep//8)%4]
  examples.extend(dict(stage='initial',episode=ep,case=TRAIN[ep%8].name,**r) for r in causal_examples(g,h,TRAIN[ep%8],policy(method,probe),72000000+seed*10000+ep))
 data=pd.DataFrame(examples);model,diagnostic=fit_model(data,90000+seed)
 write_json(out/'value_models'/f'{algo}_s{seed}_initial.json',dict(source_hash=fingerprint(),warmup_weight_hash=initial,diagnostic=diagnostic,model=model.state()))
 manifest=[]
 for method in METHODS:
  actor=copy.deepcopy(a);assert weight_hash(actor)==initial;armstart=time.perf_counter();current=model
  for ep in range(300):
   if method=='LEARN' and ep==150:
    probe=frozen(actor);fresh=[]
    for j in range(64):
     g,h=graph(81100+j,2+(j//8)%2)
     fresh.extend(dict(stage='refresh',episode=j,case=TRAIN[j%8].name,**r) for r in causal_examples(g,h,TRAIN[j%8],policy('LEARN',probe,current),73000000+seed*10000+j))
    data=pd.concat([data,pd.DataFrame(fresh)],ignore_index=True);current,diagnostic=fit_model(data,91000+seed)
    write_json(out/'value_models'/f'{algo}_s{seed}_refreshed.json',dict(source_hash=fingerprint(),refresh_actor_weight_hash=weight_hash(actor),diagnostic=diagnostic,model=current.state()))
   g,h=graph(80000+ep%80,2+(ep//8)%2);actor.eps=max(.03,.5*(1-(300+ep)/420.))
   result=simulation(g,h,TRAIN[ep%8],policy(method,actor,current),71000000+seed*10000+ep).run();actor.end_episode()
   rows.append(dict(algo=algo,seed=seed,method=method,episode=300+ep,updates=actor.nupd,**episode_metrics(result['rows'])))
  assert actor.nupd>warmupdates;checkpoint(actor,out/'models'/f'{algo}_s{seed}_{method}.pt')
  manifest.append(dict(algo=algo,seed=seed,method=method,warmup_weight_hash=initial,final_weight_hash=weight_hash(actor),warmup_updates=warmupdates,adaptation_updates=actor.nupd-warmupdates,actor_exposure_episodes=600,seconds=time.perf_counter()-armstart))
 data.to_csv(out/'value_models'/f'{algo}_s{seed}_examples.csv.gz',index=False)
 pd.DataFrame(rows).to_csv(out/'training'/f'{algo}_s{seed}.csv.gz',index=False)
 print(f'TRAINED {algo} seed={seed}: {len(data)} labels; {time.perf_counter()-start:.1f}s',flush=True);return manifest


def evaluate_job(task):
 algo,seed,gi,split,folder=task;torch.set_num_threads(1);out=Path(folder)
 m=HurdleEnsemble.load(json.loads((out/'value_models'/f'{algo}_s{seed}_refreshed.json').read_text())['model'])
 methods=METHODS if split!='mechanism' else ['LEARN','REJECT_ONLY','INITIAL_MODEL']
 actors={k:load_actor(out/'models'/f'{algo}_s{seed}_{k}.pt') for k in (METHODS if split!='mechanism' else ['LEARN'])}
 hashes={k:weight_hash(v) for k,v in actors.items()};cases=TRAIN if split=='validation' else TEST
 g,h=graph(dict(validation=82000,test=83000,mechanism=84000)[split]+gi,2+gi%2 if split=='validation' else 3+gi%2,test=split!='validation')
 settings={} if split=='validation' else json.loads((out/'locked_settings.json').read_text())['settings'][algo]
 initial=HurdleEnsemble.load(json.loads((out/'value_models'/f'{algo}_s{seed}_initial.json').read_text())['model']) if split=='mechanism' else None
 n=dict(validation=2,test=10,mechanism=5)[split];namespace=dict(validation=74000000,test=75000000,mechanism=76000000)[split];rows=[];raw=[]
 for ci,c in enumerate(cases):
  for ep in range(n):
   schedule=None
   for method in methods:
    candidates=DESIGN['validation_candidates'][method] if split=='validation' and method in ['LEARN','AGE'] else [settings.get('LEARN' if split=='mechanism' else method,{})]
    for configid,kw in enumerate(candidates):
     actor=actors['LEARN'] if split=='mechanism' else actors[method]
     p=policy('LEARN' if split=='mechanism' else method,actor,initial if method=='INITIAL_MODEL' else m,collect=True,reject_only=method=='REJECT_ONLY',**kw)
     s=simulation(g,h,c,p,namespace+gi*10000+ci*100+ep);current=[(x.id,x.target,x.depart_t) for x in s.cv]
     if schedule is None:schedule=current
     assert schedule==current
     result=s.run();key=dict(split=split,graph=gi,stages=2+gi%2 if split=='validation' else 3+gi%2,algo=algo,seed=seed,case=c.name,episode=ep,method=method,config=configid)
     packets=p.candidates;overrides=[r for r in packets if r['rule']=='learned_override']
     rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats'],utility_mean=float(np.mean([utility(r) for r in result['rows']])),follower_delivery=episode_metrics([r for r in result['rows'] if r['convoy']>=2])['delivery_rate'],eligible=len(packets),genuine_clears=sum(r['genuine'] and not r['blocked_report'] for r in packets),genuine_warning_clears=sum(r['genuine'] and r['clear_against_warning']>.5 for r in packets),overrides=len(overrides),accept_overrides=sum(r['accepted'] for r in overrides),reject_overrides=sum(not r['accepted'] for r in overrides)))
     if split!='validation':raw.extend(dict(**key,**r) for r in result['rows'])
 assert all(weight_hash(v)==hashes[k] for k,v in actors.items());return rows,raw


def select_settings(df):
 settings={};audit=[]
 for algo in ['dqn','mappo']:
  z=df[df.algo==algo];safe=z[z.method=='SAFE'].delivery_rate.mean();settings[algo]={}
  for method in ['LEARN','AGE']:
   stats=z[z.method==method].groupby('config').agg(delivery=('delivery_rate','mean'),utility=('utility_mean','mean')).reset_index();stats['eligible']=stats.delivery>=safe-.01
   choices=stats[stats.eligible];order=['utility','delivery','config'] if len(choices) else ['delivery','utility','config']
   if not len(choices):choices=stats
   selected=int(choices.sort_values(order,ascending=[False,False,True]).iloc[0]['config']);settings[algo][method]=DESIGN['validation_candidates'][method][selected]
   stats['algo']=algo;stats['method']=method;stats['selected']=stats.config.eq(selected);stats['safe_delivery']=safe;audit.extend(stats.to_dict('records'))
 return settings,audit


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='out/recovery-gate-study');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
 out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
 for d in ['models','value_models','training']:(out/d).mkdir()
 src=fingerprint();start=time.perf_counter();write_json(out/'design.json',dict(**DESIGN,source_hash=src));write_json(out/'pipeline.json',dict(status='training',source_hash=src))
 specs=[(a,s,str(out)) for a in ['dqn','mappo'] for s in SEEDS]
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  manifest=[]
  for result in pool.map(train_job,specs):manifest.extend(result)
  pd.DataFrame(manifest).to_csv(out/'training_manifest.csv',index=False);validation=[]
  write_json(out/'pipeline.json',dict(status='validation',source_hash=src))
  for i,(rows,_) in enumerate(pool.map(evaluate_job,[(a,s,g,'validation',str(out)) for a,s,_ in specs for g in range(8)])):
   validation.extend(rows)
   if (i+1)%16==0:print(f'VALIDATION {i+1}/128 jobs',flush=True)
  df=pd.DataFrame(validation);df.to_csv(out/'validation.csv.gz',index=False);settings,audit=select_settings(df);pd.DataFrame(audit).to_csv(out/'validation_selection.csv',index=False)
  assert fingerprint()==src
  write_json(out/'locked_settings.json',dict(status='locked_before_test',source_hash=src,settings=settings,checkpoints={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'models').glob('*.pt'))},estimators={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'value_models').glob('*.json'))}))
  write_json(out/'pipeline.json',dict(status='testing',source_hash=src))
  for split,graphs in [('test',16),('mechanism',4)]:
   episodes=[]
   import gzip
   with gzip.open(out/(split+'_convoys.csv.gz'),'wt') as dest:
    for i,(rows,raw) in enumerate(pool.map(evaluate_job,[(a,s,g,split,str(out)) for a,s,_ in specs for g in range(graphs)])):
     episodes.extend(rows);pd.DataFrame(raw).to_csv(dest,index=False,header=i==0)
     if (i+1)%16==0:print(f'{split} {i+1}/{len(specs)*graphs} jobs; {len(episodes)} episodes',flush=True)
   pd.DataFrame(episodes).to_csv(out/(split+'_episodes.csv.gz'),index=False)
 assert fingerprint()==src
 write_json(out/'pipeline.json',dict(status='completed',source_hash=src,seconds=time.perf_counter()-start,checkpoints=80,independent_seeds_per_algorithm=8,unique_warmup_episodes=4800,arm_adaptation_episodes=24000,auxiliary_factual_episodes=2048,validation_episodes=43008,test_episodes=102400,mechanism_episodes=7680))
 print('RECOVERY STUDY COMPLETE',flush=True)
if __name__=='__main__':main()
