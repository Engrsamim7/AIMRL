"""Frozen-model robustness check with forged-report targets independent of truth.

The earlier attacker preferentially clears active edges. A strong actor can
learn that report-presence correlation. Here forged payload/target choices use
public potential corridors only, so forged reports can be true by coincidence.
No new actor/gate fitting or test-dependent numeric selection occurs.
"""
import argparse
import hashlib
import json
import shutil
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from ammarl2.sim import MSG
from ammarl2.metrics import episode_metrics
from research_cases import CASES,factory,fork_graph,ResearchSim
from run_research_study import actor_specs,load_actor,utility
from research_gate import ValueEnsemble
from run_guarded_research_study import policy,fingerprint as parent_hash
from run_reviewer_revision import write_json

ROOT=Path(__file__).resolve().parent
METHODS=['NC','ALL','FRC','SAFE-ALL','VALUE']
CONDITIONS=[('cover-rate2-delay1',2.,1.),('cover-rate6-delay1',6.,1.),
            ('cover-rate2-delay4',2.,4.),('cover-rate6-delay4',6.,4.)]

def fingerprint():
    h=hashlib.sha256(parent_hash().encode());h.update(Path(__file__).read_bytes());return h.hexdigest()

class CoverSim(ResearchSim):
    def do_spoof(self,t):
        first=self.event_seq
        super().do_spoof(t)
        rng=np.random.default_rng(np.random.SeedSequence([self.seed,4512,self.spoof_seq]))
        for at,seq,typ,payload in self.ev:
            if typ!=MSG or seq<first:continue
            _,m=payload
            m['e']=int(rng.choice(self.cover_edges))
            m['blocked']=bool(rng.random()<.5)
            # Targets/payloads are independent of live attacks and receiver plans.

def simulation(g,h,case,p,seed):
    s=factory(g,h,case,p,seed);s.__class__=CoverSim;s.cover_edges=h
    return s

def job(args):
    gi,algo,seed,folder=args;torch.set_num_threads(1);out=Path(folder)
    locked=json.loads((out/'locked_settings.json').read_text());strength=locked['strength'];settings=locked['gate'];frc=locked['frc']
    actor=load_actor(out/'models'/f'{algo}_s{seed}.pt') if algo!='planner' else None
    model=ValueEnsemble.load(json.loads((out/'value_models'/f'{algo}_s{seed}.json').read_text())['model'])
    weights={k:v.clone() for k,v in actor.net.state_dict().items()} if actor else {}
    g,h=fork_graph(49000+gi,2+gi%2);rows=[];raw=[]
    for ci,(name,rate,delay) in enumerate(CONDITIONS):
        case=replace(CASES[1],name=name,spoof=rate,delay=delay,loss=.1,impersonation=.9)
        for ep in range(20):
            schedules=None
            for method in METHODS:
                p=policy(method,strength,actor,model,settings,frc)
                s=simulation(g,h,case,p,45000000+gi*10000+ci*100+ep)
                current=[(c.id,c.target,c.depart_t) for c in s.cv]
                if schedules is None:schedules=current
                assert current==schedules
                result=s.run();key=dict(graph=gi,algo=algo,seed=seed,case=name,episode=ep,method=method)
                rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats'],follower_delivery=episode_metrics([r for r in result['rows'] if r['convoy']>=2])['delivery_rate'],utility_mean=np.mean([utility(r) for r in result['rows']])))
                raw.extend(dict(**key,**r) for r in result['rows'])
    if actor:assert all(torch.equal(v,weights[k]) for k,v in actor.net.state_dict().items())
    return rows,raw

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',default='out/guarded-research-study');ap.add_argument('--output',default='out/cover-traffic-stress');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    parent,out=Path(a.parent).resolve(),Path(a.output).resolve();meta=json.loads((parent/'pipeline.json').read_text())
    assert meta['status']=='completed' and meta['source_hash']==parent_hash()
    out.mkdir(parents=True,exist_ok=False);initial=fingerprint()
    for folder in ['models','value_models']:shutil.copytree(parent/folder,out/folder)
    locked=json.loads((parent/'locked_settings.json').read_text());locked.update(source_hash=initial,inherited_numeric_settings=True)
    write_json(out/'locked_settings.json',locked)
    write_json(out/'design.json',dict(status='specified_before_test',source_hash=initial,conditions=CONDITIONS,
                layout_seeds='49000..49009',episode_seeds='45000000 + graph*10000 + case*100 + episode',
                cases='two leading radius-two scouts, three blind-fork radius-one followers; lead 4, loss 0.1, 90% identity impersonation; same fork costs/blocks as the parent distribution',
                forgery='public potential hazard corridors uniformly; block/open payload fair coin, independent of live truth; confidence identical to honest distribution; forged origin can be correct by coincidence',
                settings='inherited frozen actors, value models, penalty, threshold, uncertainty weight and FRC selection; no new training/validation',
                comparisons='36 VALUE vs ALL/FRC/SAFE-ALL conditions across planner/DQN/MAPPO, conservative 198-test correction including earlier 162',
                limits='Unseen corruption distribution stress; does not show performance after baselines retrain on this new attack'))
    write_json(out/'pipeline.json',dict(status='running',source_hash=initial))
    specs=[(algo,seed) for algo,seed,_ in actor_specs(out)];tasks=[(g,a,s,str(out)) for g in range(10) for a,s in specs]
    episodes=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for i,(rows,raw) in enumerate(pool.map(job,tasks)):
            episodes.extend(rows);pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False,mode='w' if i==0 else 'a',header=i==0)
            if (i+1)%7==0:print(f'Cover stress layout {i//7}: {len(episodes)} episodes',flush=True)
    pd.DataFrame(episodes).to_csv(out/'episodes.csv',index=False);assert fingerprint()==initial
    write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,parent_source_hash=parent_hash(),evaluation_episodes=len(episodes),new_training_episodes=0,new_test_schedules=True))
    print('COVER COMPLETE',flush=True)

if __name__=='__main__':main()
