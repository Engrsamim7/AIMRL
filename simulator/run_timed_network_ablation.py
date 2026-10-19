"""Matched admission ablation: same VALUE priority/coalescing, threshold zero.

Replay the entire pilot and surface, not selected favorable cells. This isolates
sender admission from the value-priority/coalescing package. No refitting.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import time
import pandas as pd
from timed_network import Calibration,TimedNetwork,graph_for
from run_timed_network_development import CASES as PILOT_CASES,fingerprint as parent_hash
from run_timed_network_surface import CASES as SURFACE_CASES,fingerprint as surface_hash


def fingerprint():return hashlib.sha256((parent_hash()+surface_hash()+Path(__file__).read_text()).encode()).hexdigest()


def job(task):
 split,gi,size,ci,bw,ep,parent=task;parent=Path(parent)
 case=replace((PILOT_CASES if split=='pilot' else SURFACE_CASES)[ci],packet_time=bw)
 seed=712000000+gi*100000+ci*1000+ep if split=='pilot' else 720000000+gi*1000000+ci*100+ep
 g=graph_for((712010 if split=='pilot' else 720010)+gi,size)
 model=Calibration.load(json.loads((parent/'calibration.json').read_text())['model'])
 sim=TimedNetwork(g,case,'VALUE',seed,model,value_threshold=0.,record=True);stats,rows=sim.run()
 key=dict(graph=gi,size=size,case=case.name,bandwidth=bw,episode=ep,method='VALUE_PRIORITY',schedule_hash=sim.schedule.digest)
 if split=='surface':key.update(case_id=ci,deadline_ratio=case.deadline_ratio,duration=case.duration,closure_fraction=case.closure_fraction,scout_lead=case.scout_lead,inspection_scale=case.inspection,seed=seed)
 return [dict(**key,**stats)],[dict(**key,**r) for r in rows],[dict(**key,**r) for r in sim.decisions],[dict(**key,**r) for r in sim.packets]


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--parent',default='simulator/out/timed-network-development-v2');ap.add_argument('--output',default='simulator/out/timed-network-ablation');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=False);parent=Path(args.parent).resolve();start=time.perf_counter();initial=fingerprint()
 design=dict(status='specified_before_ablation_run',source_hash=initial,parent_hash=parent_hash(),surface_hash=surface_hash(),
  contrast='VALUE versus VALUE_PRIORITY changes admission threshold only: locked0.05 versus0; same calibration, public value score, routing actor, priority, coalescing and safeguard rules',
  scope='all original pilot/surface cells, same existing schedules, no refitting or favorable-cell selection; descriptive development ablation',expected_episodes=7884)
 (out/'design.json').write_text(json.dumps(design,indent=2)+'\n')
 total=0
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  for split,cases,ne in [('pilot',PILOT_CASES,6),('surface',SURFACE_CASES,4)]:
   folder=out/split;folder.mkdir();tasks=[(split,gi,size,ci,bw,ep,str(parent)) for gi,size in enumerate([19,19,51,51,131,131]) for ci in range(len(cases)) for bw in [0.,.25,1.] for ep in range(ne)];episodes=[]
   with gzip.open(folder/'convoys.csv.gz','wt') as cv,gzip.open(folder/'decisions.csv.gz','wt') as ds,gzip.open(folder/'packets.csv.gz','wt') as ps:
    for i,(es,rs,dec,pkt) in enumerate(pool.map(job,tasks)):
     episodes.extend(es);pd.DataFrame(rs).to_csv(cv,index=False,header=i==0);pd.DataFrame(dec).to_csv(ds,index=False,header=i==0);pd.DataFrame(pkt).to_csv(ps,index=False,header=i==0)
     if (i+1)%300==0:print(f'ABLATION {split} {i+1}/{len(tasks)}',flush=True)
   pd.DataFrame(episodes).to_csv(folder/'episodes.csv.gz',index=False)
   (folder/'pipeline.json').write_text(json.dumps(dict(status='completed',source_hash=initial,episodes=len(episodes)),indent=2)+'\n');total+=len(episodes)
 assert fingerprint()==initial and total==7884
 meta=dict(status='completed',source_hash=initial,episodes=total,seconds=time.perf_counter()-start);(out/'pipeline.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta),flush=True)
if __name__=='__main__':main()
