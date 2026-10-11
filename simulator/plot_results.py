"""Export diagnostic plots from audited reconstruction CSVs (never legacy figures)."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm
from run_experiments import source_hash

COLORS={'none':'#64748b','all':'#e08a36','gate':'#087f8c'}
BASE=['B1','B2','B3','NC','COMM-ALL','GATE','ORACLE']
METHODS=BASE+[f'{a}-{c}' for a in ('dqn','ppo','ippo','mappo') for c in ('none','all','gate')]
WARNING='DIAGNOSTIC SMOKE RUNS • 4 training episodes • 2 graph seeds • not publication evidence'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                     'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})


def main(root,out):
    out.mkdir(parents=True,exist_ok=True)
    audit=json.loads((root/'validation.json').read_text())
    assert audit['source_hash']==source_hash(),'Audit belongs to a different simulator version'
    train=pd.read_csv(root/'train/training_curves.csv')
    evaluate=pd.read_csv(root/'evaluate/episode_metrics.csv')
    reactive=pd.read_csv(root/'reactive/episode_metrics.csv')
    ablate=pd.read_csv(root/'ablate/ablation_metrics.csv')
    effects=pd.read_csv(root/'fir-full/single_message_effects.csv')
    for directory in ('train','evaluate','reactive','ablate','fir-full'):
        m=json.loads((root/directory/'manifest.json').read_text())
        assert m['status']=='completed' and m['source_hash']==source_hash()
        assert m['arguments']['smoke'],'This plot profile assumes the diagnostic smoke protocol'
    figures=[]

    def save(fig,name,title,note):
        fig.suptitle(title,fontsize=17,fontweight='bold',x=.04,ha='left')
        fig.text(.04,.025,note,fontsize=9,color='#475569')
        fig.text(.04,.005,WARNING,fontsize=8,color='#9a3412')
        fig.tight_layout(rect=[.02,.07,.99,.94])
        fig.savefig(out/f'{name}.png',dpi=200)
        fig.savefig(out/f'{name}.pdf')
        figures.append((name,title,fig))

    fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True,sharey=True)
    for ax,algo in zip(axes.flat,('dqn','ppo','ippo','mappo')):
        for comm in ('none','all','gate'):
            rows=train[(train.algo==algo)&(train.comm==comm)]
            for seed,g in rows.groupby('seed'):
                ax.plot(g.episode+1,g.delivery_rate*100,color=COLORS[comm],alpha=.25,lw=1)
            mean=rows.groupby('episode').delivery_rate.mean()
            ax.plot(mean.index+1,mean*100,'o-',label=comm,color=COLORS[comm],lw=2)
        ax.set(title=algo.upper(),ylim=(0,105),xticks=[1,2,3,4],xlabel='Training episode',ylabel='Delivered convoys (%)')
        ax.grid(axis='y',alpha=.2)
    axes[0,0].legend(title='Communication',ncol=3,loc='lower left')
    save(fig,'01_training','Training executes; convergence is not established',
         'Bold lines: two-seed means. Faint lines: individual seeds. Training graph changes by episode.')

    rate=evaluate.groupby(['method','nodes']).delivery_rate.mean().unstack().reindex(METHODS)
    rate.to_csv(out/'delivery_rates.csv')
    fig,ax=plt.subplots(figsize=(9,9))
    im=ax.imshow(rate.to_numpy()*100,cmap='viridis',vmin=0,vmax=100,aspect='auto')
    ax.set(xticks=range(len(rate.columns)),xticklabels=rate.columns,yticks=range(len(rate)),
           yticklabels=[x.upper() for x in rate.index],xlabel='Network nodes')
    for i in range(len(rate)):
        for j in range(len(rate.columns)):
            v=rate.iloc[i,j]*100
            ax.text(j,i,f'{v:.1f}',ha='center',va='center',color='white' if v<60 else '#17212b',fontsize=9)
    fig.colorbar(im,ax=ax,pad=.03,label='Mean delivered convoys (%)')
    save(fig,'02_delivery_by_size','Held-out delivery outcomes across network sizes',
         'Two graphs × one episode; learned methods additionally average two training seeds. Population fixed at 8.')

    runtime=evaluate.groupby(['method','nodes']).seconds.median().unstack().reindex(METHODS)
    runtime.to_csv(out/'runtime_seconds.csv')
    fig,ax=plt.subplots(figsize=(9,9))
    im=ax.imshow(runtime.to_numpy(),norm=LogNorm(vmin=runtime.min().min(),vmax=runtime.max().max()),
                 cmap='magma',aspect='auto')
    ax.set(xticks=range(len(runtime.columns)),xticklabels=runtime.columns,yticks=range(len(runtime)),
           yticklabels=[x.upper() for x in runtime.index],xlabel='Network nodes')
    for i in range(len(runtime)):
        for j in range(len(runtime.columns)):
            ax.text(j,i,f'{runtime.iloc[i,j]:.3f}',ha='center',va='center',fontsize=8,color='white')
    fig.colorbar(im,ax=ax,pad=.03,label='Median wall time / episode (seconds; logarithmic color scale)')
    save(fig,'03_runtime_by_size','Measured execution cost of graph-size inference',
         'CPU, 2 PyTorch threads; includes Python allocation instrumentation. These are not uninstrumented benchmarks.')

    fig,axes=plt.subplots(1,2,figsize=(15,8),sharey=True)
    for ax,frame,title in zip(axes,[evaluate[evaluate.nodes==39],reactive],
                             ['Random attacks • graphs 300/301','Reactive + targeted spoofing • graphs 302/303']):
        graphmeans=frame.groupby(['method','graph_seed']).delivery_rate.mean().unstack().reindex(METHODS)
        means=graphmeans.mean(axis=1)*100
        ax.barh(range(len(means)),means,color=['#64748b' if m in BASE else '#087f8c' for m in means.index],alpha=.85)
        for col in graphmeans.columns:
            ax.scatter(graphmeans[col]*100,range(len(means)),color='#17212b',s=15,zorder=3)
        ax.set(xlim=(0,105),xlabel='Delivered convoys (%)',title=title,yticks=range(len(means)),
               yticklabels=[x.upper() for x in means.index]);ax.grid(axis='x',alpha=.2)
    axes[0].invert_yaxis()
    save(fig,'04_threat_scenarios','Two threat scenarios: separate small samples',
         '39 nodes, 8 convoys. Dots: graph-level means. Different graphs/configurations prevent a paired robustness claim.')

    selected=['NC','ALL','static-F1-R1-C1-eta0.4','static-F1-R1-C1-eta1.0',
              'travel-F1-R1-C1-eta0.4','travel-F1-R1-C1-eta1.0']
    labels=['No communication','Accept all','Static FRC, eta=.4','Static FRC, eta=1',
            'Travel FRC, eta=.4','Travel FRC, eta=1']
    fig,axes=plt.subplots(1,2,figsize=(13,5),sharey=True)
    for ax,metric,title in zip(axes,['delivery_rate','spoof_accepted'],
                             ['Delivery: ceiling in this sample','Spoofed reports accepted per episode']):
        matrix=ablate.groupby(['method','response_strength'])[metric].mean().unstack().reindex(selected)
        matrix.to_csv(out/f'ablation_{metric}.csv')
        display=matrix*100 if metric=='delivery_rate' else matrix
        im=ax.imshow(display.to_numpy(),cmap='viridis',vmin=0,vmax=100 if metric=='delivery_rate' else max(1,display.max().max()),aspect='auto')
        ax.set(xticks=range(len(matrix.columns)),xticklabels=matrix.columns,yticks=range(len(labels)),
               yticklabels=labels,xlabel='Blocked-edge response strength',title=title)
        for i in range(len(display)):
            for j in range(len(display.columns)):
                value=display.iloc[i,j]
                label=f'{value:.0f}' if metric=='delivery_rate' else f'{value:.1f}'
                color='#17212b' if metric=='delivery_rate' or value>display.max().max()*.55 else 'white'
                ax.text(j,i,label,ha='center',va='center',color=color)
        fig.colorbar(im,ax=ax,pad=.02)
    save(fig,'05_filter_and_penalty','Separate filtering from penalty strength',
         'All 204 ablation runs delivered 100%. Filtering changes acceptance; this sample cannot show a delivery advantage.')

    fig,axes=plt.subplots(1,2,figsize=(11,5))
    counts=effects.groupby('method').changed_receiver_path.agg(['sum','count']).reindex(['all','gate'])
    counts.to_csv(out/'message_replay_counts.csv')
    unchanged=counts['count']-counts['sum']
    axes[0].bar(['ALL','GATE'],unchanged,color='#cbd5e1',label='Unchanged path')
    axes[0].bar(['ALL','GATE'],counts['sum'],bottom=unchanged,color='#e08a36',label='Changed path')
    for i,row in enumerate(counts.itertuples()):
        axes[0].text(i,row.count+4,f'{int(row.sum)} changed / {int(row.count)}',ha='center')
    axes[0].set(ylabel='Single-message interventions',title='Receiver route effects',ylim=(0,counts['count'].max()*1.15))
    axes[0].legend(loc='lower right')
    delta=effects.delta_delivery.value_counts().reindex([-1,0,1],fill_value=0)
    axes[1].bar(['Worse','Unchanged','Better'],delta,color=['#c2413c','#64748b','#087f8c'])
    for i,n in enumerate(delta):axes[1].text(i,n+5,str(n),ha='center')
    axes[1].set(title='Delivery effect: factual minus suppressed',ylabel='Interventions',ylim=(0,len(effects)*1.15))
    save(fig,'06_message_counterfactuals','Exact replay isolates individual packet effects',
         f'All {len(effects)} decision-processed packets replayed. Three paths changed; no receiver delivery outcomes changed.')

    # A compact four-panel entry point for viewing in chat.
    fig,axes=plt.subplots(2,2,figsize=(13,9))
    ax=axes[0,0]; small=rate[39]
    ax.bar(range(len(small)),small*100,color=['#64748b' if m in BASE else '#087f8c' for m in small.index])
    ax.set(ylim=(0,105),ylabel='Delivered (%)',title='39-node delivery outcomes',xticks=range(len(small)),
           xticklabels=[m.upper() for m in small.index]);ax.tick_params(axis='x',rotation=75,labelsize=8)
    ax=axes[0,1]
    for family,color in [('heuristics','#64748b'),('dqn','#377eb8'),('ppo','#087f8c'),('ippo','#e08a36'),('mappo','#8b5cf6')]:
        mask=evaluate.method.isin(BASE) if family=='heuristics' else evaluate.method.str.startswith(family+'-')
        grouped=evaluate[mask].groupby('nodes').seconds.median()
        ax.plot(grouped.index,grouped,'o-',label=family.upper(),color=color)
    ax.set(yscale='log',xlabel='Network nodes',ylabel='Median wall seconds / episode',title='Scaling (with allocation instrumentation)')
    ax.legend(fontsize=8);ax.grid(alpha=.2)
    ax=axes[1,0]
    for method,label,color in [('NC','No communication','#64748b'),('ALL','Accept all','#e08a36'),
                               ('travel-F1-R1-C1-eta1.0','Travel gate','#087f8c')]:
        m=ablate[ablate.method==method].groupby('response_strength').delivery_rate.mean()
        ax.plot(m.index,m*100,'o-',label=label,color=color,alpha=.8)
    ax.set(ylim=(0,105),xlabel='Response strength',ylabel='Delivered (%)',title='Ablation: all variants hit the delivery ceiling')
    ax.legend(fontsize=8);ax.text(.04,.3,'No gate advantage established by this sample.',transform=ax.transAxes,fontsize=10)
    ax=axes[1,1]
    ax.bar(['Path unchanged','Path changed'],[len(effects)-int(effects.changed_receiver_path.sum()),int(effects.changed_receiver_path.sum())],color=['#64748b','#e08a36'])
    for i,n in enumerate([len(effects)-int(effects.changed_receiver_path.sum()),int(effects.changed_receiver_path.sum())]):
        ax.text(i,n+6,str(n),ha='center')
    ax.set(ylim=(0,len(effects)*1.2),ylabel='Message interventions',title='Single-packet replay: 413 interventions')
    save(fig,'00_overview','Reconstructed simulator — current diagnostic results',
         '28 tests passed; 24 short-trained models. Three packet interventions changed paths; none changed delivery.')

    with PdfPages(out/'results_report.pdf') as pdf:
        # Overview first, detailed plots after.
        for name,title,fig in figures[-1:]+figures[:-1]:pdf.savefig(fig)
    descriptions={
        '01_training':'Only four episodes per model: these curves do not establish convergence.',
        '02_delivery_by_size':'Held-out outcomes averaged within each method; only two graph seeds.',
        '03_runtime_by_size':'Instrumentation is included; use these timings as diagnostic scaling measurements.',
        '04_threat_scenarios':'Separate scenarios use different graph seeds, so differences are not a controlled threat effect.',
        '05_filter_and_penalty':'Every ablation delivered 100%; reduced spoof acceptance is not proof of improved delivery.',
        '06_message_counterfactuals':'413 full-message interventions; three changed paths and none changed delivery.',
        '00_overview':'A compact summary of execution checks and present limitations.'}
    md=['# Current results visualisations','',WARNING,'',
        'Simulator reconstruction and functional validation are complete. Full convergence training, adequately replicated experiments and revised manuscript tables are still pending.','',
        '[Download the seven-page PDF report](results_report.pdf)','']
    for name,title,fig in figures[-1:]+figures[:-1]:
        md.extend([f'## {title}','',descriptions[name],'',f'![{title}]({name}.png)','',f'[Vector PDF]({name}.pdf)',''])
        plt.close(fig)
    (out/'README.md').write_text('\n'.join(md))
    (out/'provenance.json').write_text(json.dumps(dict(source_hash=source_hash(),run_root=str(root.resolve()),
                                                     purpose='diagnostic smoke visualisations',plots=len(figures)),indent=2)+'\n')
    print(f'Exported {len(figures)} PNG/PDF plots and combined PDF to {out}')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-root',type=Path,default=Path('out/reviewer-validation'))
    p.add_argument('--output',type=Path,default=Path('../revision/visualisations'))
    a=p.parse_args();main(a.run_root,a.output)
