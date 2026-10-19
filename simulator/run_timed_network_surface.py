"""Predeclared response surface with a frozen development model/threshold.

This expands physical sensitivity, not algorithm tuning or fresh confirmation.
Every declared cell is retained. Original pilot results remain immutable.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time
import pandas as pd
from timed_network import Calibration,Scenario,TimedNetwork,METHODS,graph_for
from run_timed_network_development import fingerprint as parent_fingerprint

CASES=[Scenario(name=f'd{d}_t{t}_b{b}_l{lead}_i{inspection}',deadline_ratio=d,duration=t,closure_fraction=b,scout_lead=lead,inspection=inspection)
 for d,t,b,lead,inspection in itertools.product([1.1,1.35,1.75,2.5],[.25,1.,4.],[.1,.3],[0.,2.],[0.,1.])]
BANDWIDTHS=[0.,.25,1.]

def fingerprint():
 return hashlib.sha256((parent_fingerprint()+Path(__file__).read_text()).encode()).hexdigest()


def job(task):
 gi,size,ci,bw,ep,parent=task;parent=Path(parent)
 from dataclasses import replace
 case=replace(CASES[ci],packet_time=bw);g=graph_for(720010+gi,size);seed=720000000+gi*1000000+ci*100+ep
 model=Calibration.load(json.loads((parent/'calibration.json').read_text())['model']);threshold=json.loads((parent/'locked_settings.json').read_text())['value_threshold']
 es=[];rs=[];ds=[];ps=[]
 for method in METHODS:
  sim=TimedNetwork(g,case,method,seed,model,value_threshold=threshold,record=True);stats,rows=sim.run()
  key=dict(graph=gi,size=size,case_id=ci,case=case.name,deadline_ratio=case.deadline_ratio,duration=case.duration,closure_fraction=case.closure_fraction,scout_lead=case.scout_lead,inspection_scale=case.inspection,bandwidth=bw,episode=ep,seed=seed,method=method,schedule_hash=sim.schedule.digest)
  es.append(dict(**key,**stats));rs.extend(dict(**key,**r) for r in rows);ds.extend(dict(**key,**r) for r in sim.decisions);ps.extend(dict(**key,**r) for r in sim.packets)
 return es,rs,ds,ps


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',default='simulator/out/timed-network-development-v2');ap.add_argument('--output',default='simulator/out/timed-network-surface');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
 parent=Path(args.parent).resolve();out=Path(args.output);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();initial=fingerprint()
 lock=json.loads((parent/'locked_settings.json').read_text());assert lock['source_hash']==parent_fingerprint()
 design=dict(status='specified_before_surface_run',scope='development response surface; frozen pilot calibration/threshold, no algorithm tuning',source_hash=initial,parent_source_hash=parent_fingerprint(),
  sizes=[19,19,51,51,131,131],cases=[asdict(c) for c in CASES],packet_times=BANDWIDTHS,episodes_per_cell=4,methods=METHODS,
  namespace='720000000+graph*1000000+case*100+episode; graph seeds720010+graph; new graphs/schedules',
  expected_episodes=48384,expected_convoys=387072,selection='none; parent threshold/model frozen; all864 size/case/channel cells retained',
  purpose='separate deadline, persistence, closure budget, lead, inspection cost and channel capacity; assess opportunity beyond pilot delivery ceilings',
  limits=['development expansion after pilot, not an independent confirmatory superiority study','only two graphs per size and one report interpreter','no trained MARL actor or convergence evidence'])
 (out/'design.json').write_text(json.dumps(design,indent=2)+'\n')
 (out/'locked_parent.json').write_text(json.dumps(dict(threshold=lock['value_threshold'],calibration_sha256=hashlib.sha256((parent/'calibration.json').read_bytes()).hexdigest()),indent=2)+'\n')
 tasks=[(gi,size,ci,bw,ep,str(parent)) for gi,size in enumerate(design['sizes']) for ci in range(len(CASES)) for bw in BANDWIDTHS for ep in range(4)]
 episodes=[]
 with ProcessPoolExecutor(max_workers=args.workers) as pool,gzip.open(out/'convoys.csv.gz','wt') as convoy_file,gzip.open(out/'decisions.csv.gz','wt') as decision_file,gzip.open(out/'packets.csv.gz','wt') as packet_file:
  for i,(es,rs,ds,ps) in enumerate(pool.map(job,tasks)):
   episodes.extend(es);pd.DataFrame(rs).to_csv(convoy_file,index=False,header=i==0);pd.DataFrame(ds).to_csv(decision_file,index=False,header=i==0);pd.DataFrame(ps).to_csv(packet_file,index=False,header=i==0)
   if (i+1)%200==0:print(f'SURFACE {i+1}/{len(tasks)}',flush=True)
 pd.DataFrame(episodes).to_csv(out/'episodes.csv.gz',index=False)
 assert fingerprint()==initial and len(episodes)==design['expected_episodes']
 meta=dict(status='completed',source_hash=initial,episodes=len(episodes),convoys=len(episodes)*8,seconds=time.perf_counter()-start)
 (out/'pipeline.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta),flush=True)
if __name__=='__main__':main()
