"""Constructed clearance probes: legitimate clearance delay and two forged IDs.

External observation messages are injected test inputs; their platforms are not
modeled. The policy cannot read their genuine/spoof evaluation labels.
"""
import argparse,json,hashlib
from pathlib import Path
import pandas as pd
from dataclasses import asdict
from ammarl2.sim import Cfg,MSG,UNBLOCK
from ammarl2.reviewer import cc2_graph,cc2_factory,ScoutFixturePolicy
from run_adaptive_experiments import adaptive,fingerprint,write_json


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='out/adaptive-gate-v2');a=ap.parse_args();run=Path(a.input);out=run/'clearance-stress';out.mkdir(exist_ok=False)
    params=json.loads((run/'selected.json').read_text())['parameters'];c=Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=1,tau_reveal=0,p_kill=1)
    rows=[];raw=[]
    for case in ['one-legitimate-clear','two-legitimate-clear','two-forged-clear']:
        for ep in range(50):
            g,_,e=cc2_graph(4);g.c[6]=3.4 # a small measurable detour for withholding clearance
            for mode in ['NC','COMM-ALL','FRC','SOFT-ALL','VALUE-GATE']:
                if mode in ['NC','COMM-ALL','FRC']:
                    p=ScoutFixturePolicy(mode,comm={'NC':'none','COMM-ALL':'all','FRC':'gate'}[mode],weights='threat',use_obs=True,relevance_scope='reachable')
                else:p=adaptive(mode,params,mode='all' if mode=='SOFT-ALL' else 'value',forced_scout_routes=True)
                s=cc2_factory(g,c,p,18000000+ep,hot=4)
                legitimate=case!='two-forged-clear'
                if legitimate:
                    s.active[e]=(0.,2.);s.attack_log[-1]=(0.,e,2.);s.push(2.,UNBLOCK,e)
                senders=[10] if case=='one-legitimate-clear' else [10,11]
                for recipient in [1,2]:
                    for sender in senders:
                        s.push(3.,MSG,(recipient,dict(id=f'clear:{ep}:{recipient}:{sender}',sender=sender,e=e,t_obs=2.,blocked=False,conf=1.,genuine=legitimate)))
                result=s.run();key=dict(case=case,episode=ep,method=mode)
                rows.append(dict(**key,**__import__('ammarl2.metrics',fromlist=['episode_metrics']).episode_metrics(result['rows'])))
                raw.extend(dict(**key,**r) for r in result['rows'])
    df=pd.DataFrame(rows);df.to_csv(out/'episodes.csv',index=False);pd.DataFrame(raw).to_csv(out/'convoys.csv',index=False)
    summary=df.groupby(['case','method'])[['delivery_rate','nominal_delivered_mean','realized_delivered_mean']].mean().reset_index();summary.to_csv(out/'summary.csv',index=False)
    write_json(out/'manifest.json',dict(status='completed',source_hash=fingerprint(),helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),episodes=len(rows),params=params,config=asdict(c),scope='injected external-observer messages, small detour, fixed hot branch; constructed mechanism checks only'))
    print(summary.to_string(index=False))

if __name__=='__main__':main()
