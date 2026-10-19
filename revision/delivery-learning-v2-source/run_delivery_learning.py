"""Delivery-primary learned routing and causal receiver-gate study."""
import argparse,copy,hashlib,json,time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from timed_network import Calibration,Scenario,graph_for
from delivery_learning import Actor,DeliveryNetwork,ReturnGate,FEATURES,GATE_FEATURES,paired_packet
from run_timed_network_surface import CASES as PHYSICAL

ROOT=Path(__file__).resolve().parent
SEEDS=list(range(8))
BASE=Scenario(name='mixed',duration=1.,deadline_ratio=1.35)
TEST=[BASE,replace(BASE,name='persistent',duration=4.),replace(BASE,name='rapid',duration=.25),replace(BASE,name='tight',deadline_ratio=1.1),replace(BASE,name='loss20',loss=.2),replace(BASE,name='late-reports',delay=2.),replace(BASE,name='miscalibrated',accuracy_scale=.7),replace(BASE,name='full-visibility',coverage=1.,perfect_sensors=True),replace(BASE,name='clean',closure_fraction=0.),replace(BASE,name='unlimited',packet_time=0.),replace(BASE,name='zero-inspection',inspection=0.),replace(BASE,name='zero-lead',scout_lead=0.)]
ARMS=['NONE','ALL','FIXED_RX','KEEP_ONE','KEEP','LEARN']
SETTINGS=[dict(disabled=True,beta=2.,margin=.02)]+[dict(disabled=False,beta=b,margin=m) for b in [0.,1.] for m in [0.,.02]]


def fingerprint():
 h=hashlib.sha256()
 for name in ['delivery_learning.py','run_delivery_learning.py','timed_network.py','ammarl2/graph.py','ammarl2/reviewer.py','../revision/submission-code-audit/original_network_seed42.json']:h.update((ROOT/name).read_bytes())
 return h.hexdigest()


def write(path,value):Path(path).write_text(json.dumps(value,indent=2)+'\n')
def model_for(folder):return Calibration.load(json.loads((Path(folder)/'calibration.json').read_text())['model'])
def train_case(seed,ep):
 r=np.random.default_rng([810000000+seed,ep]);case=PHYSICAL[int(r.integers(len(PHYSICAL)))];return replace(case,packet_time=float(r.choice([0.,.25,1.])),loss=float(r.choice([0.,.2])),delay=float(r.choice([0.,.5,2.])),accuracy_scale=float(r.choice([1.,1.,.7])))
def load_actor(folder,si):return Actor.load(json.loads((Path(folder)/'actors'/f's{si}.json').read_text())['actor'])


def checkpoint_validation(actor,si,folder):
 old=actor.epsilon;actor.epsilon=0.;rows=[]
 for gi,size in enumerate([19,51]):
  g=graph_for(820010+gi,size)
  for ci in [0,1,3,6,8]:
   for ep in range(2):
    actor.training=False;s=DeliveryNetwork(g,TEST[ci],'VALUE',820000000+gi*10000+ci*100+ep,model_for(folder),value_threshold=0.,actor=actor,receiver='ALL');result,_=s.run();rows.append(dict(graph=gi,case=TEST[ci].name,episode=ep,on_time=result['on_time']))
 actor.epsilon=old;actor.training=True
 return rows


def train_job(task):
 si,episodes,folder=task;torch.set_num_threads(1);folder=Path(folder);actor=Actor(8100+si,training=True);rows=[];valid=[];best=-1.;selected=None;selected_ep=0
 checkpoints=sorted(set([0,episodes//2,episodes]))
 for ep in range(episodes+1):
  if ep in checkpoints:
   vr=checkpoint_validation(actor,si,folder);score=float(np.mean([r['on_time'] for r in vr]));valid.extend(dict(seed=si,checkpoint=ep,**r) for r in vr)
   write(folder/'actor_candidates'/f's{si}_ep{ep}.json',dict(seed=si,episode=ep,actor=actor.state()))
   if score>best+1e-12 or (abs(score-best)<=1e-12 and ep>selected_ep):best=score;selected=copy.deepcopy(actor.state());selected_ep=ep
  if ep==episodes:break
  case=train_case(si,ep);g=graph_for(810010+si*100+ep%8,19 if ep%2==0 else 51);actor.epsilon=.2-.18*ep/max(1,episodes-1)
  sim=DeliveryNetwork(g,case,'VALUE',810000000+si*100000+ep,model_for(folder),value_threshold=0.,actor=actor,receiver='ALL',dropout=[0.,.1,.3][ep%3]);result,_=sim.run();loss=actor.learn(sim.transitions(result['on_time']))
  rows.append(dict(seed=si,episode=ep,epsilon=actor.epsilon,loss=np.mean(loss) if loss else np.nan,steps=result['routing_calls'],**result))
 write(folder/'actors'/f's{si}.json',dict(source_hash=fingerprint(),seed=si,selected_episode=selected_ep,validation_on_time=best,actor=selected))
 pd.DataFrame(rows).to_csv(folder/'training'/f's{si}.csv.gz',index=False);pd.DataFrame(valid).to_csv(folder/'training'/f's{si}_validation.csv',index=False)
 print(f'ROUTING TRAINED seed={si} selected={selected_ep} validation={best:.4f}',flush=True)


def labels_job(task):
 si,attempts,folder=task;torch.set_num_threads(1);folder=Path(folder);actor=load_actor(folder,si);model=model_for(folder);labels=[];episodes=[]
 for ep in range(attempts):
  case=train_case(100+si,ep);g=graph_for(830010+si*100+ep%8,19 if ep%2==0 else 51);seed=830000000+si*100000+ep
  sim=DeliveryNetwork(g,case,'VALUE',seed,model,value_threshold=0.,actor=actor,receiver='ALL');captured=[];target=[1,1,1,2,3,5][ep%6];count=[0];control=ep%10==0;episode_labels=[]
  def capture(env,cid,p,x):
   eligible=(x[11]>.5) if not control else (x[11]<.5)
   if eligible:count[0]+=1
   if eligible and count[0]>=target and len(captured)<(1 if control else 3):captured.append((cid,copy.deepcopy(p),x.copy()));return True
   return False
  sim.capture=capture;out=sim.run()
  while out is None:
   cid,p,x=captured[-1];admit,reject=paired_packet(sim,cid,p);delta=admit[0]['on_time']-reject[0]['on_time']
   labels.append(dict(seed=si,episode=ep,candidate=len(captured),environment_seed=seed,graph_seed=830010+si*100+ep%8,size=g.n,control=control,t=sim.t,receiver=cid,packet=p['id'],schedule_hash=sim.schedule.digest,features=json.dumps(x.tolist()),delta=delta,admit_on_time=admit[0]['on_time'],reject_on_time=reject[0]['on_time'],admit_convoys=json.dumps(admit[1]),reject_convoys=json.dumps(reject[1])))
   episode_labels.append(admit)
   sim.admit(cid,p);sim.branch_stop=False
   if len(captured)>=(1 if control else 3):sim.capture=None
   out=sim.advance(initialize=False)
  result=out[0]
  for admit in episode_labels:
   assert admit[1]==out[1] and admit[0]['on_time']==result['on_time'],'Factual branch must reproduce whole-episode continuation'
  episodes.append(dict(seed=si,episode=ep,captured=bool(captured),control=control,candidate_count=count[0],target_index=target,on_time=result['on_time']))
 frame=pd.DataFrame(labels);frame.to_csv(folder/'labels'/f's{si}.csv.gz',index=False);pd.DataFrame(episodes).to_csv(folder/'labels'/f's{si}_episodes.csv.gz',index=False)
 selected=frame[~frame.control] if len(frame) else frame
 if len(selected)==0:raise RuntimeError(f'No actor-changing packet labels for seed{si}; the mechanism must be diagnosed before fitting')
 x=np.array([json.loads(v) for v in selected.features]);gate=ReturnGate().fit(x,selected.delta.to_numpy(),8400+si);gate.save(folder/'gates'/f's{si}.npz')
 print(f'CAUSAL GATE seed={si} labels={len(frame)} active={len(selected)} nonzero={int(selected.delta.ne(0).sum())}',flush=True)


def validate_job(task):
 si,gi,folder=task;torch.set_num_threads(1);folder=Path(folder);actor=load_actor(folder,si);model=model_for(folder);rows=[]
 g=graph_for(840010+gi,19 if gi==0 else 51)
 for setting_id,setting in enumerate(SETTINGS):
  gate=ReturnGate.load(folder/'gates'/f's{si}.npz',**setting)
  for ci in [0,1,3,6]:
   for ep in range(3):
    sim=DeliveryNetwork(g,TEST[ci],'VALUE',840000000+gi*10000+ci*100+ep,model,value_threshold=0.,actor=actor,receiver='LEARN',gate=gate);result,_=sim.run();rows.append(dict(seed=si,graph=gi,case=TEST[ci].name,episode=ep,setting=setting_id,**result))
 return rows


def test_job(task):
 si,gi,folder=task;torch.set_num_threads(1);folder=Path(folder);actor=load_actor(folder,si);model=model_for(folder);lock=json.loads((folder/'locked_settings.json').read_text());gate=ReturnGate.load(folder/'gates'/f's{si}.npz',**lock['setting'])
 size=[19,19,51,51,131,131][gi];g=graph_for(850010+gi,size);episodes=[];raw=[];decisions=[]
 arms=ARMS+(['PLANNER_WARN','PLANNER_RAW'] if si==0 else [])
 for arm in arms:
  receiver={'FIXED_RX':'FIXED'}.get(arm,arm);transport='NONE' if arm=='NONE' else 'WARN_PRIORITY' if arm=='PLANNER_WARN' else 'RAW_ALL' if arm=='PLANNER_RAW' else 'VALUE'
  for ci,case in enumerate(TEST):
   for ep in range(6):
    sim=DeliveryNetwork(g,case,transport,850000000+gi*10000+ci*100+ep,model,value_threshold=0.,actor=None if arm.startswith('PLANNER') else actor,receiver='ALL' if arm.startswith('PLANNER') else receiver,gate=gate,record=False);result,rows=sim.run()
    key=dict(seed=-1 if arm.startswith('PLANNER') else si,graph=gi,size=size,case=case.name,episode=ep,method=arm,schedule_hash=sim.schedule.digest)
    episodes.append(dict(**key,**result));raw.extend(dict(**key,**r) for r in rows)
    decisions.extend(dict(**key,t=r['t'],receiver=r['cid'],packet=r['id'],accepted=r['accepted'],features=json.dumps(r['features'])) for r in sim.gate_log)
 return episodes,raw,decisions


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='simulator/out/delivery-learning-v2');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--train-episodes',type=int,default=500);ap.add_argument('--label-attempts',type=int,default=400);args=ap.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
 for name in ['actors','actor_candidates','training','labels','gates']:(out/name).mkdir()
 initial=fingerprint();start=time.perf_counter();calibration=ROOT/'out/timed-network-development-v2/calibration.json';(out/'calibration.json').write_bytes(calibration.read_bytes())
 design=dict(status='specified_before_training',source_hash=initial,primary='fleet on-time delivery; no bandwidth reward or efficiency substitution',routing_seeds=SEEDS,train_episodes=args.train_episodes,label_attempts=args.label_attempts,actor_features=FEATURES,gate_features=GATE_FEATURES,cases=[asdict(c) for c in TEST],arms=ARMS+['PLANNER_WARN','PLANNER_RAW'],
  architecture='parameter-sharing independent Double-DQN with edge-scoring MLP, planning prior, common state-value head, bounded .05tanh action residual, replay, masked next-action Double-DQN, .5episodic-return anchoring, valid-return target clipping and gamma1 finite-horizon team reward; potential shaping telescopes to team return plus an action-independent initial constant',
  actor_selection='episode0/midpoint/final on20 separate validation episodes; choose on-time then later checkpoint; report any selected0 explicitly',
  gate='96 ExtraTrees trained on actor-specific admit-minus-reject complete-fleet branches; reject only if estimated harmful admission with uncertainty/risk filters; at most one rejection per fleet; default ALL',
  labels='up to3 isolated packet interventions per training episode after index1/1/1/2/3/5;10%no-change controls excluded from fit;all factual branches must reproduce uninterrupted fleet outcomes; no labels from validation/test',
  gate_selection='ALL fallback orbeta0/1 xmargin0/.02, risk_limit.1; pooled actual validation on-time then fewer rejections then safer fixed order; lock before test',
  split_namespaces=dict(training=810000000,actor_validation=820000000,gate_labels=830000000,gate_validation=840000000,test=850000000),
  test='6 new graphs19/51/131,12conditions,6schedules,8frozen common routing actors;6receiver methods plus2planner controls run once per environment,21600method episodes172800convoys',
  inference='20000 paired actor/graph/environment bootstrap draws;three primary LEARN-minus-ALL/KEEP/PLANNER_RAW contrasts;Bonferroni3; practical target1percentage point mean and positive corrected lower bound',
  limits=['frozen common routing policies isolate online receiver effect; not independently optimized routing under each gate','one shared fleet rejection token is a public coordination constraint','tree dispersion is heuristic,not calibrated safety','inference checkpoints are not full optimizer/replay resume snapshots','episode0 may be selected;fixed budget is not convergence evidence','no operational adversary or combat survival claim'])
 design['development_revision']='v1 training validation selected episode0 for all8seeds;stopped during label collection before test. v2changes value architecture and anchors to observed episodic return;primary objective/test namespace unchanged and still untouched.'
 write(out/'design.json',design);write(out/'pipeline.json',dict(status='routing_training',source_hash=initial))
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  list(pool.map(train_job,[(s,args.train_episodes,str(out)) for s in SEEDS]));write(out/'pipeline.json',dict(status='causal_labeling',source_hash=initial))
  list(pool.map(labels_job,[(s,args.label_attempts,str(out)) for s in SEEDS]));validation=[]
  for rows in pool.map(validate_job,[(s,g,str(out)) for s in SEEDS for g in range(2)]):validation.extend(rows)
  val=pd.DataFrame(validation);val.to_csv(out/'validation.csv.gz',index=False);ranking=val.groupby('setting').agg(on_time=('on_time','mean'),rejections=('rejections','mean')).reset_index().sort_values(['on_time','rejections','setting'],ascending=[False,True,True]);chosen=int(ranking.iloc[0].setting)
  lock=dict(status='locked_before_test',source_hash=initial,setting_id=chosen,setting=SETTINGS[chosen],actors={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'actors').glob('*.json')},gates={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'gates').glob('*.npz')});write(out/'locked_settings.json',lock);write(out/'pipeline.json',dict(status='testing',source_hash=initial))
  import gzip
  episodes=[]
  with gzip.open(out/'convoys.csv.gz','wt') as cv,gzip.open(out/'gate_decisions.csv.gz','wt') as gd:
   first_gate=True
   for i,(es,rs,ds) in enumerate(pool.map(test_job,[(s,g,str(out)) for s in SEEDS for g in range(6)])):
    episodes.extend(es);pd.DataFrame(rs).to_csv(cv,index=False,header=i==0)
    if ds:pd.DataFrame(ds).to_csv(gd,index=False,header=first_gate);first_gate=False
    print(f'TEST {i+1}/48',flush=True)
  pd.DataFrame(episodes).to_csv(out/'episodes.csv.gz',index=False)
 assert fingerprint()==initial
 write(out/'pipeline.json',dict(status='completed',source_hash=initial,seconds=time.perf_counter()-start,routing_training_episodes=8*args.train_episodes,causal_attempts=8*args.label_attempts,validation_episodes=len(val),test_episodes=len(episodes),test_convoys=8*len(episodes)))
 print('DELIVERY LEARNING COMPLETE',flush=True)
if __name__=='__main__':main()
