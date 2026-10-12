"""Frozen-Q filtering diagnosis on synthetic graphs, not paper-number reproduction."""
import argparse,copy,hashlib,itertools,json
from pathlib import Path
from dataclasses import asdict
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ammarl2.graph import make_graph
from ammarl2.sim import Sim,Cfg
from ammarl2.metrics import episode_metrics
from manuscript_gate import ManuscriptGate

p=argparse.ArgumentParser();p.add_argument('--output',default='out/manuscript-gate-diagnostic');p.add_argument('--train',type=int,default=300);p.add_argument('--graphs',type=int,default=3);p.add_argument('--seeds',type=int,default=5);p.add_argument('--eval',type=int,default=20)
a=p.parse_args();root=Path(a.output);root.mkdir(parents=True,exist_ok=False)
base=Cfg(n_convoys=3,stagger=0,hub_cap=2,congestion_factor=.15,attack_rate=.9,budget=6,attack_dur=(20,40),p_kill=.7)
# Target identity is fixed per slot because a historical hub-only Q does not encode target.
def run(g,cfg,policy,seed):
    s=Sim(g,cfg,policy,seed)
    for cv in s.cv: cv.target=g.targets[0];cv.depart_t=0.
    return s.run()
configs=[]
for local,peer in [(0,0),(8,8),(12,12),(8,12)]:
    for comm,mask in [('none','000'),('all','000')]+[('gate',''.join(map(str,b))) for b in itertools.product((0,1),repeat=3)]:
        configs.append((f'{local}/{peer}:{comm}:{mask}',local,peer,comm,mask))
records=[];convoys=[];training=[];models=[]
for gs in range(1000,1000+a.graphs):
    g=make_graph(gs,layers=3,width=5,n_targets=1)
    # 17 nodes; graph is synthetic and deliberately not labeled as the original 19-node network.
    for ts in range(a.seeds):
        policy=ManuscriptGate('train-local',comm='none',training=True,learner_seed=ts)
        for ep in range(a.train):
            out=run(g,base,policy,1000000+gs*10000+ts*1000+ep)
            training.append(dict(graph=gs,training_seed=ts,episode=ep,delivery=episode_metrics(out['rows'])['delivery_rate']))
        model=dict(graph=gs,training_seed=ts,q=[[k[0],k[1],v] for k,v in sorted(policy.q.items())],steps=policy.steps)
        models.append(model)
        for scenario in ('exogenous','reactive'):
            cfg=copy.deepcopy(base);cfg.spoof_rate=4;cfg.p_loss=.2;cfg.conf_mu=.85;cfg.conf_sd=.1
            if scenario=='reactive':cfg.adv='reactive';cfg.spoof_mode='targeted'
            for ep in range(a.eval):
                schedule=None;zero=[]
                for name,local,peer,comm,mask in configs:
                    tested=ManuscriptGate(name,comm=comm,q=copy.deepcopy(policy.q),local_strength=local,peer_strength=peer,gate_fresh=mask[0]=='1',gate_rel=mask[1]=='1',gate_conf=mask[2]=='1')
                    out=run(g,cfg,tested,2000000+gs*100+ep)
                    actual=[(x['target'],x['depart_t']) for x in out['rows']]
                    if schedule is None:schedule=actual
                    assert actual==schedule and tested.q==policy.q
                    met=episode_metrics(out['rows']);key=dict(graph=gs,training_seed=ts,scenario=scenario,episode=ep,method=name)
                    records.append(dict(**key,**met,processed=len(out['message_audit']),used_candidates=sum(d['peer_used'] for d in out['decisions']),**out['stats']))
                    convoys.extend(dict(**key,**r) for r in out['rows'])
                    if local==peer==0:zero.append([(r['delivered'],r['destroyed'],r['nominal']) for r in out['rows']])
                assert all(z==zero[0] for z in zero)
        print(f'completed graph={gs} training_seed={ts}',flush=True)
        pd.DataFrame(records).to_csv(root/'episodes.csv',index=False)
(root/'models.json').write_text(json.dumps(models))
pd.DataFrame(training).to_csv(root/'training.csv',index=False);pd.DataFrame(convoys).to_csv(root/'convoys.csv',index=False)
df=pd.DataFrame(records);summary=df.groupby(['scenario','method']).delivery_rate.mean().reset_index();summary.to_csv(root/'summary.csv',index=False)
contrasts=[];rng=np.random.default_rng(20261012)
for scenario in ('exogenous','reactive'):
    for local,peer in [(0,0),(8,8),(12,12),(8,12)]:
        sub=df[df.scenario==scenario].pivot(index=['graph','training_seed','episode'],columns='method',values='delivery_rate')
        for other in ('all:000','none:000'):
            delta=(sub[f'{local}/{peer}:gate:111']-sub[f'{local}/{peer}:{other}']).groupby(level=[0,1]).mean().unstack()
            vals=delta.to_numpy();boot=np.array([vals[rng.integers(0,vals.shape[0],vals.shape[0])][:,rng.integers(0,vals.shape[1],vals.shape[1])].mean() for _ in range(3000)])
            lo,hi=np.quantile(boot,[.025,.975]);contrasts.append(dict(scenario=scenario,penalties=f'{local}/{peer}',comparison='gate minus '+other.split(':')[0],difference_pp=100*vals.mean(),lower_pp=100*lo,upper_pp=100*hi))
pd.DataFrame(contrasts).to_csv(root/'contrasts.csv',index=False)
fig,axs=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ax,scenario in zip(axs,('exogenous','reactive')):
    for mode in ('none:000','all:000','gate:111'):
        ys=[100*summary.loc[(summary.scenario==scenario)&(summary.method==f'{l}/{h}:{mode}'),'delivery_rate'].iloc[0] for l,h in [(0,0),(8,8),(12,12),(8,12)]]
        ax.plot(range(4),ys,'o-',label=mode.split(':')[0])
    ax.set_xticks(range(4),['0/0','8/8','12/12','8/12']);ax.set_title(scenario);ax.set_xlabel('Local / peer penalty');ax.grid(alpha=.2)
axs[0].set_ylabel('Actual delivery (%)');axs[1].legend();fig.suptitle('Frozen historical Q: synthetic diagnostic, not manuscript reproduction');fig.tight_layout();fig.savefig(root/'gate_comparison.png',dpi=180);fig.savefig(root/'gate_comparison.pdf')
files=['manuscript_gate.py','run_manuscript_gate.py','ammarl2/sim.py','ammarl2/graph.py']
(root/'manifest.json').write_text(json.dumps(dict(status='completed',arguments=vars(a),base_config=asdict(base),episodes=len(records),training_episodes=len(training),source_sha256={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files},limitations=['Synthetic 17-node graph, not original topology','Frozen local Q; no communication-specific retraining','Negative threat step penalty and explicit death penalty resolve unspecified/ambiguous manuscript choices','Only three test graphs; intervals are diagnostic','Training and test episodes independent on same graph; not unseen-graph transfer'],checks=['Frozen Q equality every evaluation','Identical convoy schedule every comparison','Zero-response outcome equality every episode']),indent=2))
(root/'README.md').write_text('# Manuscript gate diagnosis\n\nThis synthetic mechanism experiment does not reproduce submitted numbers. See manifest.json for assumptions and checks. Models are trained locally then frozen for all communication comparisons. Graphs have 17 nodes, with fixed target and simultaneous departures. Actual delivery is distinct from the manuscript route-survival proxy. Penalty labels are local/peer strengths. Intervals resample graph and training seed; with only three graphs these are diagnostic. Receiving/filtering messages does not itself reduce transmitted bandwidth.\n\n![Comparison](gate_comparison.png)\n\n'+pd.DataFrame(contrasts).to_markdown(index=False)+'\n')
print(json.dumps(dict(status='completed',episodes=len(records),training_episodes=len(training))))
