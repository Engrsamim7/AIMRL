"""Confirm guarded admission on another untouched layout/tape split.

Retains all first-study results. Reuses its training-only actors/value models;
does not fit to earlier test outcomes. New guard rules and selection grid are
specified before validation and before unlocking this second test.
"""
import argparse
import copy
import hashlib
import json
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
import torch

from research_cases import CASES,factory,fork_graph
from research_gate import ValueEnsemble
from guarded_research_gate import GuardedResearchPolicy
from run_research_study import actor_specs,load_actor,utility,DESIGN,fingerprint as parent_hash
from ammarl2.reviewer import original_graph
from ammarl2.metrics import episode_metrics
from run_reviewer_revision import write_json

ROOT=Path(__file__).resolve().parent
METHODS=['NC','ALL','FRC','SAFE-ALL','VALUE','VALUE-NO-WARNING-GUARD','VALUE-NO-CLEARANCE-GUARD']

def fingerprint():
    h=hashlib.sha256(parent_hash().encode())
    for name in ['guarded_research_gate.py','run_guarded_research_study.py']:
        h.update(name.encode());h.update((ROOT/name).read_bytes())
    return h.hexdigest()

def policy(method,strength,actor,model,settings,frc):
    mode={'NC':'none','ALL':'all','FRC':'frc','SAFE-ALL':'safe'}.get(method,'value')
    extra=settings if mode=='value' else {}
    return GuardedResearchPolicy(method,weights='threat',use_obs=True,response_strength=strength,relevance_scope='reachable',mode=mode,actor=actor,value_model=model,
                                 warning_guard=method!='VALUE-NO-WARNING-GUARD',clearance_guard=method!='VALUE-NO-CLEARANCE-GUARD',
                                 warning_confidence=frc['kappa_min'],**extra,**(frc if method=='FRC' else {}))

def models(out):
    return {(a,s):ValueEnsemble.load(json.loads((out/'value_models'/f'{a}_s{s}.json').read_text())['model']) for a,s,_ in actor_specs(out)}

def validate(out,strength,frc,values):
    rows=[]
    for threshold in [-1.,0.,1.]:
        for beta in [0.,.5]:
            settings=dict(value_threshold=threshold,uncertainty_weight=beta)
            for algo,seed,actor in actor_specs(out):
                for ci,case in enumerate(CASES):
                    for ep in range(10):
                        g,h=fork_graph(47500+ep,2+ep%2)
                        result=factory(g,h,case,policy('VALUE',strength,actor,values[(algo,seed)],settings,frc),41100000+ci*100+ep).run()
                        rows.append(dict(threshold=threshold,beta=beta,algo=algo,seed=seed,case=case.name,episode=ep,**episode_metrics(result['rows']),**result['stats']))
            print(f'Guarded validation threshold={threshold}, beta={beta}',flush=True)
    df=pd.DataFrame(rows);df.to_csv(out/'gate_validation.csv',index=False)
    ranked=df.groupby(['threshold','beta']).agg(delivery=('delivery_rate','mean'),elapsed=('realized_delivered_mean','mean'),accepted=('true_accepted','sum'),spoof=('spoof_accepted','sum')).reset_index()
    ranked['total_admitted']=ranked.accepted+ranked.spoof
    ranked=ranked.sort_values(['delivery','elapsed','total_admitted','threshold','beta'],ascending=[False,True,True,True,True])
    ranked.to_csv(out/'gate_selection.csv',index=False);best=ranked.iloc[0]
    settings=dict(value_threshold=float(best.threshold),uncertainty_weight=float(best.beta))
    write_json(out/'locked_settings.json',dict(status='locked_before_test',source_hash=fingerprint(),strength=strength,gate=settings,frc=frc,test_results_inspected=False))
    return settings

def job(args):
    gi,algo,seed,strength,settings,frc,folder=args;torch.set_num_threads(1);out=Path(folder)
    family='constructed-forks' if gi<10 else 'original-topology'
    g,h=fork_graph(48000+gi,2+gi%2) if gi<10 else (original_graph(),())
    actor=load_actor(out/'models'/f'{algo}_s{seed}.pt') if algo!='planner' else None
    model=ValueEnsemble.load(json.loads((out/'value_models'/f'{algo}_s{seed}.json').read_text())['model'])
    weights={k:v.clone() for k,v in actor.net.state_dict().items()} if actor else {}
    rows=[];raw=[];messages=[]
    for ci,case in enumerate(CASES):
        for ep in range(20 if gi<10 else 10):
            schedule=None
            for method in METHODS:
                p=policy(method,strength,actor,model,settings,frc)
                s=factory(g,h,case,p,44000000+gi*10000+ci*100+ep,bridge=gi==10)
                current=[(c.id,c.target,c.depart_t) for c in s.cv]
                if schedule is None:schedule=current
                assert schedule==current
                result=s.run();key=dict(family=family,graph=gi,algo=algo,seed=seed,case=case.name,episode=ep,method=method)
                follower=episode_metrics([r for r in result['rows'] if r['convoy']>=2])
                rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats'],follower_delivery=follower['delivery_rate'],decisions=len(result['decisions']),utility_mean=np.mean([utility(r) for r in result['rows']])))
                raw.extend(dict(**key,**r) for r in result['rows']);messages.extend(dict(**key,**m) for m in result['message_audit'])
    if actor:assert all(torch.equal(v,weights[k]) for k,v in actor.net.state_dict().items())
    return rows,raw,messages

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',default='out/research-opportunity-study');ap.add_argument('--output',default='out/guarded-research-study');ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
    parent,out=Path(a.parent).resolve(),Path(a.output).resolve();meta=json.loads((parent/'pipeline.json').read_text())
    assert meta['status']=='completed' and meta['source_hash']==parent_hash()
    out.mkdir(parents=True,exist_ok=False);initial=fingerprint();start=time.perf_counter();torch.set_num_threads(1)
    for folder in ['models','value_models']:shutil.copytree(parent/folder,out/folder)
    for name in ['training_manifest.json','penalty_selection.csv','penalty_validation.csv','frc_selection.csv','frc_validation.csv']:shutil.copy2(parent/name,out/name)
    frc=meta['settings']['frc'];strength=meta['settings']['strength']
    design=dict(parent_training_source_hash=parent_hash(),source_hash=initial,status='specified_before_validation_and_test',
                changes='preserve fresh confident reachable hazard warnings; require two claimed clear sources before warning erasure; learned value still filters other reports',
                new_validation_layouts='47500..47509',new_validation_tapes='41100000 + case*100 + episode',
                new_test_layouts='48000..48009',new_test_tapes='44000000 + graph*10000 + case*100 + episode',
                reused_training='six actors and seven value models from original training only; no test-label fitting',
                inherited_design=DESIGN,correction='162 tests accounting for the 81 previous primary comparisons and 81 new guarded comparisons')
    write_json(out/'design.json',design);write_json(out/'pipeline.json',dict(status='running',source_hash=initial))
    values=models(out);settings=validate(out,strength,frc,values);assert fingerprint()==initial
    specs=[(algo,seed) for algo,seed,_ in actor_specs(out)];tasks=[(gi,algo,seed,strength,settings,frc,str(out)) for gi in range(11) for algo,seed in specs]
    episodes=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for i,(rows,raw,messages) in enumerate(pool.map(job,tasks)):
            episodes.extend(rows)
            for name,records in [('convoys',raw),('messages',messages)]:pd.DataFrame(records).to_csv(out/(name+'.csv'),index=False,mode='w' if i==0 else 'a',header=i==0)
            if (i+1)%7==0:print(f'Guarded test layout {i//7}: {len(episodes)} episodes',flush=True)
    pd.DataFrame(episodes).to_csv(out/'episodes.csv',index=False);assert fingerprint()==initial
    write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,parent_source_hash=parent_hash(),settings=dict(strength=strength,**settings,frc=frc),evaluation_episodes=len(episodes),new_offline_actor_training_episodes=0,reused_fresh_actor_training_episodes=3600,reused_causal_generation_episodes=700,seconds=time.perf_counter()-start,new_test_schedules=True))
    print('GUARDED COMPLETE',flush=True)

if __name__=='__main__':main()
