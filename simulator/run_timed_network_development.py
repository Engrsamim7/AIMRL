"""Fixed development grid for the timed network revision; no MARL claim."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
from timed_network import Calibration,Scenario,Schedule,TimedNetwork,METHODS,graph_for,path

CASES=[Scenario('clean-covered',closure_fraction=0.,coverage=1.,perfect_sensors=True),
 Scenario('clean-partial',closure_fraction=0.),Scenario('persistent',duration=4.),
 Scenario('transient',duration=.5),Scenario('rapid-recovery',duration=.15),
 Scenario('late-onset',duration=1.,late_onset=True),Scenario('late-reports',duration=.5,delay=2.),
 Scenario('loss20',duration=.5,loss=.2),Scenario('miscalibrated',duration=.5,accuracy_scale=.7)]
BANDWIDTHS=[0.,.25,1.]
ROOT=Path(__file__).resolve().parent


def fingerprint():
 h=hashlib.sha256()
 for name in ['timed_network.py','run_timed_network_development.py']:h.update((ROOT/name).read_bytes())
 for name in ['ammarl2/graph.py','ammarl2/reviewer.py','../revision/submission-code-audit/original_network_seed42.json']:h.update((ROOT/name).read_bytes())
 return h.hexdigest()


def fit_calibration():
 model=Calibration();rng=np.random.default_rng(710000123);records=[]
 for gi in range(8):
  g=graph_for(710010+gi,19 if gi%2==0 else 51);scale=float(np.median(g.c))
  reference=float(np.median([sum(g.c[e]+.2 for e in path(g,g.depot,target,g.c+.2)) for target in g.targets]))
  for ci,case in enumerate(CASES):
   # Confidence miscalibration is held out, not included in fitting.
   if case.name=='miscalibrated':continue
   for ep in range(3):
    schedule=Schedule(g,case,710000000+gi*10000+ci*100+ep,reference)
    for _ in range(400):
     e=int(rng.integers(g.m));observed=float(rng.uniform(0,2*reference));age=float(rng.choice([0.,.1,.3,.7,1.5,3.,6.,10.])*scale);query=observed+age
     confidence=float(rng.choice([.75,.85,1.]));truth_then=schedule.closed(e,observed)
     report=truth_then if rng.random()<confidence else not truth_then;truth_now=int(schedule.closed(e,query));phase=query/reference
     model.add(report,age/scale,phase,confidence,truth_now)
     pi=model.indices(0,0,phase,confidence)[2];model.prior_count[pi]+=1;model.prior_success[pi]+=truth_now
     records.append(dict(graph=gi,case=case.name,episode=ep,edge=e,t_observed=observed,age=age/scale,phase=phase,confidence=confidence,report=int(report),truth=truth_now,schedule_hash=schedule.digest))
 return model,pd.DataFrame(records)


def job(task):
 gi,size,ci,bandwidth,ep,split,folder=task;folder=Path(folder)
 model=Calibration.load(json.loads((folder/'calibration.json').read_text())['model']);g=graph_for((711010 if split=='validation' else 712010)+gi,size)
 case=replace(CASES[ci],packet_time=bandwidth)
 seed=(711000000 if split=='validation' else 712000000)+gi*100000+ci*1000+ep
 thresholds=[0.,.05,.2] if split=='validation' else [json.loads((folder/'locked_settings.json').read_text())['value_threshold']]
 episodes=[];raw=[];decisions=[];packets=[]
 methods=['VALUE'] if split=='validation' else METHODS
 for method in methods:
  for threshold in (thresholds if method=='VALUE' else [0.]):
   sim=TimedNetwork(g,case,method,seed,model,value_threshold=threshold,record=split=='development')
   stats,rows=sim.run();key=dict(split=split,graph=gi,size=size,case=case.name,bandwidth=bandwidth,episode=ep,method=method,threshold=threshold,schedule_hash=sim.schedule.digest)
   episodes.append(dict(**key,**stats));raw.extend(dict(**key,**row) for row in rows)
   if split=='development':
    decisions.extend(dict(**key,**row) for row in sim.decisions)
    packets.extend(dict(**key,**row) for row in sim.packets)
 return episodes,raw,decisions,packets


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',default='simulator/out/timed-network-development-v2');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--episodes',type=int,default=6);args=ap.parse_args()
 out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False);initial=fingerprint();start=time.perf_counter()
 design=dict(status='specified_before_development_run',scope='new network development benchmark, not fresh confirmatory superiority or a trained MARL result',source_hash=initial,
  methods=METHODS,cases=[asdict(c) for c in CASES],packet_times=BANDWIDTHS,development_graphs=[19,19,51,51,131,131],episodes_per_cell=args.episodes,
  training='8 independent graph instances at sizes19/51;8 fitting cases;3 schedules;400 sensor/query labels per schedule; all held-out miscalibrated cases excluded',
  validation='4 held-out graph instances19/51;9cases x3bandwidths x2episodes x3VALUEthresholds; choose pooled on-time delivery then fewer transmitted bytes',
  endpoint='on-time delivery by fixed1.75x public free-flow-service lower bound; secondary whole-horizon delivery, elapsed, nominal, encounters, actual broadcast bytes, queue age, Brier',
  physical='fixed finite unique closure budget round(.2*m);initial/early/late onset; physical blocked entry forbidden; inspection delay and reroute/wait; no destruction; service-only FIFO occupancy; in-transit entries grandfathered',
  information='position-based scout/follower sensors; fixed masks; actual source observations; independent keyed noise/loss; shared training-fitted report validity; no live remote truth to actor; public static manifest for sender relevance',
  gate='VALUE is a new sender-side heuristic, ranking calibrated belief changes by public detour/demand; it is not the original receiver FRC or a learned causal value gate',
  calibration='offline synthetic labels; empirical table with hierarchical backoff; on-policy Brier is measured, not assumed calibrated',
  limitations=['no neural or tabular routing training in this phase','planner minimizes approximate expected traversal delay, not optimal on-time probability','not a validated operational adversary or field network','development grid may guide design; future confirmation requires untouched seeds','public detour ranking is a heuristic, not causal value estimation'])
 (out/'design.json').write_text(json.dumps(design,indent=2)+'\n')
 model,labels=fit_calibration();labels.to_csv(out/'calibration_labels.csv.gz',index=False);calibration=dict(source_hash=initial,model=model.state(),labels=len(labels));(out/'calibration.json').write_text(json.dumps(calibration,indent=2)+'\n')
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  tasks=[(gi,size,ci,bw,ep,'validation',str(out)) for gi,size in enumerate([19,19,51,51]) for ci in range(len(CASES)) for bw in BANDWIDTHS for ep in range(2)]
  validation=[]
  for i,(es,_,_,_) in enumerate(pool.map(job,tasks)):
   validation.extend(es)
   if (i+1)%50==0:print(f'VALIDATION {i+1}/{len(tasks)}',flush=True)
  val=pd.DataFrame(validation);val.to_csv(out/'validation.csv.gz',index=False)
  ranking=val.groupby('threshold').agg(on_time=('on_time','mean'),bytes=('tx_bytes','mean')).reset_index().sort_values(['on_time','bytes','threshold'],ascending=[False,True,True]);selected=float(ranking.iloc[0].threshold)
  lock=dict(status='locked_before_development_evaluation',value_threshold=selected,source_hash=initial,calibration_sha256=hashlib.sha256((out/'calibration.json').read_bytes()).hexdigest());(out/'locked_settings.json').write_text(json.dumps(lock,indent=2)+'\n')
  tasks=[(gi,size,ci,bw,ep,'development',str(out)) for gi,size in enumerate([19,19,51,51,131,131]) for ci in range(len(CASES)) for bw in BANDWIDTHS for ep in range(args.episodes)]
  import gzip
  episodes=[]
  with gzip.open(out/'convoys.csv.gz','wt') as convoy_file,gzip.open(out/'decisions.csv.gz','wt') as decision_file,gzip.open(out/'packets.csv.gz','wt') as packet_file:
   for i,(es,rs,ds,ps) in enumerate(pool.map(job,tasks)):
    episodes.extend(es);pd.DataFrame(rs).to_csv(convoy_file,index=False,header=i==0);pd.DataFrame(ds).to_csv(decision_file,index=False,header=i==0);pd.DataFrame(ps).to_csv(packet_file,index=False,header=i==0)
    if (i+1)%50==0:print(f'DEVELOPMENT {i+1}/{len(tasks)}',flush=True)
  pd.DataFrame(episodes).to_csv(out/'episodes.csv.gz',index=False)
 assert fingerprint()==initial
 meta=dict(status='completed',source_hash=initial,calibration_labels=len(labels),validation_episodes=len(val),development_episodes=len(episodes),convoys=len(episodes)*8,seconds=time.perf_counter()-start)
 (out/'pipeline.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta),flush=True)
if __name__=='__main__':main()
