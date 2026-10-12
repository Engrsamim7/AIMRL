"""Controlled mechanism probes: false clear reports with explicit confidence.

These constructed cases test filtering, not general algorithm superiority.
The actor never receives the genuine/spoof evaluation label.
"""
import argparse,hashlib,json
from pathlib import Path
from functools import partial
import pandas as pd
from ammarl2.sim import Cfg,MSG
from ammarl2.reviewer import cc2_graph,cc2_factory,ScoutFixturePolicy
from ammarl2.metrics import episode_metrics
from ammarl2.counterfactual import single_message_effects
from run_reviewer_revision import source_hash,write_json


def fixture_factory(g,cfg,policy,seed,hot=4,false_confidence=None):
    s=cc2_factory(g,cfg,policy,seed,hot=hot)
    if false_confidence is not None:
        blocked=4 if hot==4 else 6
        for receiver in [1,2]:
            s.stats['spoof_sent']+=1
            s.push(3.,MSG,(receiver,dict(id=f'false-clear:{seed}:{receiver}',sender=-1,e=blocked,
                 blocked=False,t_obs=2.,conf=false_confidence,genuine=False)))
    return s


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='out/reviewer-revision-v2/gate-fixtures');ap.add_argument('--episodes',type=int,default=50);a=ap.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cfg=Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=1,tau_reveal=0,p_kill=1)
    rows=[];raw=[];messages=[]
    for case,confidence in [('accurate-only',None),('low-confidence-false-clear',.2),('high-confidence-false-clear',.9)]:
        for ep in range(a.episodes):
            hot=4 if ep%2==0 else 5;g,_,_=cc2_graph(hot)
            for comm in ['none','all','gate']:
                p=ScoutFixturePolicy(comm,comm=comm,use_obs=True,relevance_scope='reachable',kappa_min=.6)
                result=fixture_factory(g,cfg,p,7100000+ep,hot=hot,false_confidence=confidence).run()
                key=dict(case=case,episode=ep,mode=comm,hot=hot)
                rows.append(dict(**key,**episode_metrics(result['rows']),**result['stats']))
                raw.extend(dict(**key,**r) for r in result['rows']);messages.extend(dict(**key,**m) for m in result['message_audit'])
    df=pd.DataFrame(rows);df.to_csv(out/'episodes.csv',index=False);pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False);pd.DataFrame(messages).to_csv(out/'messages.csv',index=False)
    df.groupby(['case','mode']).delivery_rate.mean().reset_index().to_csv(out/'summary.csv',index=False)
    replay=[]
    for ep in range(10):
        g,_,_=cc2_graph(4)
        for comm in ['all','gate']:
            p=ScoutFixturePolicy(comm,comm=comm,use_obs=True,relevance_scope='reachable')
            frame,meta,_=single_message_effects(g,cfg,p,7200000+ep,simulator_factory=partial(fixture_factory,hot=4,false_confidence=.2))
            frame['episode']=ep;frame['mode']=comm;replay.append(frame)
    pd.concat(replay,ignore_index=True).to_csv(out/'replay.csv',index=False)
    write_json(out/'manifest.json',dict(status='completed',source_hash=source_hash(),fixture_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),episodes=len(rows),replay_interventions=sum(len(x) for x in replay),config=__import__('dataclasses').asdict(cfg),cases=['accurate warnings only','fresh low-confidence misleading clear reports','fresh high-confidence misleading clear reports'],notes=['Fixed .6 confidence threshold, independent of M4-selected threshold','Constructed mechanisms, not sampled operational threat distributions','Warning truthful at t=1.25; forged clear sent at t=2 and received at t=3','Wrong report location follows prespecified episode hot branch; actor does not inspect ground-truth label']))
    print(df.groupby(['case','mode']).delivery_rate.mean().to_string())

if __name__=='__main__':main()
