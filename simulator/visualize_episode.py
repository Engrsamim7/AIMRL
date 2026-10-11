"""Illustrate the first fixed held-out episode with routes and exact time phases.

Instrumentation only records events; it does not change randomness or dynamics.
The resulting convoy rows must match the existing held-out evaluation exactly.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.backends.backend_pdf import PdfPages
from ammarl2.graph import make_graph
from ammarl2.sim import Sim,Cfg
from run_experiments import load_models,write_json,source_hash


class RecordedSim(Sim):
    def __init__(self,*args):
        super().__init__(*args)
        self.phases=[]
    def leave_edge(self,cv):
        if cv.cur_edge>=0:
            self.phases.append(dict(convoy=cv.id,phase='travel',start=cv.edge_entered,end=self.t))
        super().leave_edge(cv)
    def start_service(self,cv,t):
        if t>cv.queued_t:
            self.phases.append(dict(convoy=cv.id,phase='wait',start=cv.queued_t,end=t))
        self.phases.append(dict(convoy=cv.id,phase='service',start=t,end=t+self.cfg.hub_service))
        super().start_service(cv,t)


def main(root,figures):
    figures.mkdir(parents=True,exist_ok=True)
    cfg=Cfg(**json.loads((root/'spoof/manifest.json').read_text())['config'])
    gs=min(pd.read_csv(root/'spoof/episode_metrics.csv').graph_seed)
    seed=5*int(gs)
    policy=next(p for p,m in load_models(root/'train',False) if p.name=='dqn-gate' and m['training_seed']==0)
    graph=make_graph(int(gs),layers=6,width=6)
    sim=RecordedSim(graph,cfg,copy.deepcopy(policy),seed)
    result=sim.run()
    rows=pd.DataFrame(result['rows'])
    raw=pd.read_csv(root/'spoof/convoys.csv')
    reference=raw[(raw.method=='dqn-gate')&(raw.training_seed==0)&(raw.graph_seed==gs)&(raw.episode_seed==seed)].sort_values('convoy')
    assert len(reference)==len(rows)
    for field in ['target','depart_t','delivered','destroyed','censored','nominal','travel','wait','service','blocked_enc']:
        assert np.allclose(reference[field],rows.sort_values('convoy')[field],equal_nan=True),field
    for cv in sim.cv:
        if cv.cur_edge>=0:
            sim.phases.append(dict(convoy=cv.id,phase='travel',start=cv.edge_entered,end=sim.t))
        if cv.waiting:
            sim.phases.append(dict(convoy=cv.id,phase='wait',start=cv.queued_t,end=sim.t))
    phases=pd.DataFrame(sim.phases)
    phases['end']=phases.end.clip(upper=sim.t)
    phases['duration']=phases.end-phases.start
    totals=phases.groupby(['convoy','phase']).duration.sum().unstack(fill_value=0).reindex(range(cfg.n_convoys),fill_value=0)
    for phase in ['travel','wait','service']:
        assert np.allclose(totals.get(phase,pd.Series(0,index=totals.index)),rows.set_index('convoy')[phase])
    case=root/'case-study';case.mkdir(exist_ok=True)
    rows.to_csv(case/'convoys.csv',index=False)
    phases.to_csv(case/'time_phases.csv',index=False)
    pd.DataFrame(result['message_audit']).to_csv(case/'packets.csv',index=False)
    pd.DataFrame(result['decisions']).to_csv(case/'decisions.csv',index=False)
    pd.DataFrame(result['attacks'],columns=['time','edge']).to_csv(case/'attacks.csv',index=False)
    write_json(case/'provenance.json',dict(source_hash=source_hash(),method=policy.name,training_seed=0,
               graph_seed=int(gs),episode_seed=seed,config=result['config'],
               selection='first held-out disrupted episode, fixed in advance; illustrative, not an aggregate comparison',
               raw_evaluation_match=True,phase_totals_match=True,
               edges=[dict(id=e,source=int(graph.src[e]),target=int(graph.dst[e]),nominal=float(graph.c[e])) for e in range(graph.m)],
               routes={str(cv.id):list(map(int,cv.path)) for cv in sim.cv}))
    positions={0:(0,2.5)}
    for layer in range(6):
        for column in range(6):positions[1+layer*6+column]=(layer+1,column)
    for i,target in enumerate(graph.targets):positions[target]=(7,2+i)
    segments=[(positions[int(graph.src[e])],positions[int(graph.dst[e])]) for e in range(graph.m)]
    colors=plt.get_cmap('tab20')
    fig,ax=plt.subplots(figsize=(14,8))
    ax.add_collection(LineCollection(segments,colors='#d6dce2',linewidths=1,zorder=1))
    attacked={e for _,e in result['attacks']}
    ax.add_collection(LineCollection([segments[e] for e in attacked],colors='#efb5b5',linewidths=2,zorder=2))
    for cv in sim.cv:
        color=colors(cv.id)
        route=[segments[e] for e in cv.path]
        if not cv.alive and route:
            start,end=route[-1]
            midpoint=((start[0]+end[0])/2,(start[1]+end[1])/2)
            route[-1]=(start,midpoint)
            ax.scatter(*midpoint,marker='x',color=color,s=65,zorder=6)
        ax.add_collection(LineCollection(route,colors=[color],linewidths=2,alpha=.65,zorder=3))
        status='delivered' if cv.delivered else 'destroyed' if not cv.alive else 'censored'
        ax.plot([],[],color=color,lw=2,label=f'Convoy {cv.id}: {status}')
    for node,(x,y) in positions.items():
        ax.scatter(x,y,s=180 if node==0 or node in graph.targets else 90,color='#fff',edgecolor='#253542',zorder=5)
        ax.text(x,y,str(node),ha='center',va='center',fontsize=8,zorder=6)
    ax.set(xlim=(-.5,8.4),ylim=(-.6,5.6),title=f'39-node synthetic network: realized routes, DQN-GATE seed 0\nGraph {gs}, episode {seed}; disrupted/exogenous-spoof scenario')
    ax.set_axis_off();ax.legend(loc='center left',bbox_to_anchor=(.87,.5),fontsize=8,frameon=False)
    fig.text(.03,.035,'Gray: public edges. Pale red: attacked at some time, not necessarily at entry. Colored segments: entered edges; × marks schematic half-edge destruction.',fontsize=9)
    fig.tight_layout(rect=[0,.065,.94,1]);fig.savefig(figures/'07_network_routes.png',dpi=180);fig.savefig(figures/'07_network_routes.pdf')
    route_fig=fig
    fig,axes=plt.subplots(2,1,figsize=(14,9),gridspec_kw={'height_ratios':[3,1]})
    palette={'travel':'#377eb8','wait':'#e08a36','service':'#087f8c'}
    for row in phases.itertuples():
        axes[0].broken_barh([(row.start,row.duration)],(row.convoy-.34,.68),facecolors=palette[row.phase])
    for cv in sim.cv:
        end=cv.finished_t if np.isfinite(cv.finished_t) else sim.t
        axes[0].scatter(end,cv.id,marker='o' if cv.delivered else 'x',color='#17212b',zorder=5)
    for phase,color in palette.items():axes[0].plot([],[],color=color,lw=7,label=phase)
    axes[0].set(yticks=range(cfg.n_convoys),ylabel='Convoy slot',xlabel='Simulation time (model units)',title='Recorded travel, queue wait and hub service; ○ delivered, × destroyed/censored')
    axes[0].legend(ncol=3);axes[0].grid(axis='x',alpha=.2)
    packets=pd.DataFrame(result['message_audit'])
    if len(packets):
        # Packet audit uses decision time: processing can follow physical delivery.
        time_column='t' if 't' in packets.columns else 'decision_t'
        accepted=packets.reason.eq('accepted')
        axes[1].hist([packets.loc[accepted,time_column],packets.loc[~accepted,time_column]],
                     bins=20,stacked=True,color=['#087f8c','#cbd5e1'],label=['Accepted','Rejected'])
    axes[1].set(xlabel='Receiver decision time (model units)',ylabel='Processed packets',title='Gate decisions during the same illustrative episode');axes[1].legend()
    fig.suptitle('Simulation episode: event timing and communication',fontsize=16,fontweight='bold')
    fig.text(.03,.025,'One fixed held-out episode, not a performance estimate. Instrumented outcomes match raw evaluation; phase durations match convoy totals.',fontsize=9)
    fig.tight_layout(rect=[0,.06,1,.95]);fig.savefig(figures/'08_episode_timeline.png',dpi=180);fig.savefig(figures/'08_episode_timeline.pdf')
    with PdfPages(figures/'simulation_episode_report.pdf') as pdf:pdf.savefig(route_fig);pdf.savefig(fig)
    plt.close(route_fig);plt.close(fig)
    print('Generated two episode figures; raw evaluation outcomes and time-phase sums verified.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root',type=Path,required=True);parser.add_argument('--figures',type=Path,required=True)
    args=parser.parse_args();main(args.run_root,args.figures)
