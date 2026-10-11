"""Updated exploratory results: matched scenarios, longer training, graph uncertainty."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from run_experiments import source_hash,write_json

BASE=['B1','B2','B3','NC','COMM-ALL','GATE','ORACLE']
METHODS=BASE+[f'{a}-{c}' for a in ['dqn','ppo','ippo','mappo'] for c in ['none','all','gate']]
COLORS={'none':'#64748b','all':'#e08a36','gate':'#087f8c'}
SCENARIOS={'random':'Random attacks','spoof':'Delayed / lost / spoofed reports','reactive':'Reactive attacks + targeted spoofing'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})


def bootstrap(values,n=3000):
    values=np.asarray(values)
    r=np.random.default_rng(2026)
    samples=r.choice(values,size=(n,len(values))).mean(1)
    return float(values.mean()),float(np.percentile(samples,2.5)),float(np.percentile(samples,97.5))


def main(root,out):
    out.mkdir(parents=True,exist_ok=True)
    audit=json.loads((root/'validation.json').read_text())
    assert audit['source_hash']==source_hash()
    train=pd.read_csv(root/'train/training_curves.csv')
    scenarios={k:pd.read_csv(root/k/'episode_metrics.csv') for k in SCENARIOS}
    scaling=pd.read_csv(root/'scaling/episode_metrics.csv')
    ablate=pd.read_csv(root/'ablate/ablation_metrics.csv')
    # Argparse defaults may label integral eta as "1" rather than "1.0".
    ablate['method']=ablate.method.str.replace(r'eta(\d+)$',r'eta\1.0',regex=True)
    effects=pd.read_csv(root/'fir/single_message_effects.csv')
    train_manifest=json.loads((root/'train/manifest.json').read_text())
    budget=train_manifest['arguments']['episodes']
    seed_count=len(train_manifest['arguments']['seeds'])
    model_count=train.groupby(['algo','comm','seed']).ngroups
    assert len(train)==model_count*budget
    rows=[]
    for scenario,frame in scenarios.items():
        for method,g in frame.groupby('method'):
            graphmeans=g.groupby('graph_seed').delivery_rate.mean()
            mean,lo,hi=bootstrap(graphmeans)
            rows.append(dict(scenario=scenario,method=method,delivery=mean,lower=lo,upper=hi,
                             graphs=len(graphmeans),episode_records=len(g),
                             delivered_nominal=g.nominal_delivered_mean.mean(),
                             delivered_time=g.realized_delivered_mean.mean(),
                             blocked_per_convoy=g.blocked_encounters_per_convoy.mean()))
    summary=pd.DataFrame(rows);summary.to_csv(out/'scenario_summary.csv',index=False)
    contrasts=[]
    for scenario,frame in scenarios.items():
        graph=frame.groupby(['method','graph_seed']).delivery_rate.mean().unstack('method')
        for a,b in [('GATE','COMM-ALL'),('COMM-ALL','NC'),('GATE','NC')]:
            m,l,h=bootstrap(graph[a]-graph[b])
            contrasts.append(dict(scenario=scenario,comparison=f'{a} minus {b}',difference=m,lower=l,upper=h,uncertainty='paired graph bootstrap'))
        # Matched training seeds AND graph clusters for learned gate-vs-all contrasts.
        for algo in ['dqn','ppo','ippo','mappo']:
            f=frame[frame.method.isin([f'{algo}-gate',f'{algo}-all'])]
            p=f.groupby(['training_seed','graph_seed','method']).delivery_rate.mean().unstack('method')
            d=(p[f'{algo}-gate']-p[f'{algo}-all']).unstack('graph_seed').to_numpy()
            rng=np.random.default_rng(2026); samples=[]
            for _ in range(3000):
                seeds=rng.integers(d.shape[0],size=d.shape[0]);graphs=rng.integers(d.shape[1],size=d.shape[1])
                samples.append(d[np.ix_(seeds,graphs)].mean())
            contrasts.append(dict(scenario=scenario,comparison=f'{algo.upper()} gate minus all',difference=float(d.mean()),
                                  lower=float(np.percentile(samples,2.5)),upper=float(np.percentile(samples,97.5)),
                                  uncertainty='paired graph and training-seed bootstrap'))
    contrasts=pd.DataFrame(contrasts);contrasts.to_csv(out/'paired_contrasts.csv',index=False)
    figures=[]
    warning=f'EXPLORATORY RESULTS • {budget} episodes/model • {seed_count} training seeds • convergence not assumed'
    def save(fig,name,title,note):
        fig.suptitle(title,x=.04,ha='left',fontsize=17,fontweight='bold')
        fig.text(.04,.027,note,fontsize=9,color='#475569')
        fig.text(.04,.006,warning,fontsize=8,color='#9a3412')
        fig.tight_layout(rect=[.02,.075,.99,.94])
        fig.savefig(out/f'{name}.png',dpi=180);fig.savefig(out/f'{name}.pdf')
        figures.append((name,title,fig))

    fig,axes=plt.subplots(2,2,figsize=(12,8),sharex=True,sharey=True)
    for ax,algo in zip(axes.flat,['dqn','ppo','ippo','mappo']):
        for comm in ['none','all','gate']:
            f=train[(train.algo==algo)&(train.comm==comm)]
            lines=[]
            for seed,g in f.groupby('seed'):
                g=g.sort_values('episode')
                smooth=g.delivery_rate.rolling(10,min_periods=1).mean()
                ax.plot(g.episode+1,smooth*100,color=COLORS[comm],alpha=.18,lw=1)
                lines.append(pd.Series(smooth.to_numpy(),index=g.episode.to_numpy()+1))
            means=pd.concat(lines,axis=1).mean(axis=1)
            ax.plot(means.index,means*100,color=COLORS[comm],label=comm,lw=2)
        ax.set(title=algo.upper(),ylim=(0,105),xlabel='Training episode',ylabel='Delivered (%)');ax.grid(alpha=.2)
    axes[0,0].legend(title='Communication',ncol=3,fontsize=9)
    save(fig,'01_training','Longer training under contested conditions',
         '10-episode moving averages. Bold: three-seed mean; faint: individual seeds. Stochastic training outcomes, not fixed-policy convergence tests.')

    fig,axes=plt.subplots(1,3,figsize=(17,9),sharey=True)
    for ax,(scenario,title) in zip(axes,SCENARIOS.items()):
        s=summary[summary.scenario==scenario].set_index('method').reindex(METHODS)
        y=np.arange(len(s));mean=s.delivery.to_numpy()*100
        ax.errorbar(mean,y,xerr=np.vstack([mean-s.lower.to_numpy()*100,s.upper.to_numpy()*100-mean]),fmt='o',
                    color='#087f8c',ecolor='#94a3b8',capsize=2)
        ax.set(xlim=(0,105),title=title,xlabel='Mean delivered convoys (%)',yticks=y,
               yticklabels=[m.upper() for m in METHODS]);ax.grid(axis='x',alpha=.2)
    axes[0].invert_yaxis()
    save(fig,'02_scenario_delivery','Matched held-out comparisons with uncertainty',
         'Same 10 held-out graphs × 5 episodes across scenarios. Bars: graph-cluster 95% bootstrap intervals conditional on trained models; 12 convoys.')

    fig,axes=plt.subplots(1,3,figsize=(16,6),sharey=True)
    comparisons=['GATE minus COMM-ALL','DQN gate minus all','PPO gate minus all','IPPO gate minus all','MAPPO gate minus all']
    for ax,(scenario,title) in zip(axes,SCENARIOS.items()):
        s=contrasts[contrasts.scenario==scenario].set_index('comparison').reindex(comparisons)
        y=np.arange(len(s));mean=s.difference.to_numpy()*100
        ax.axvline(0,color='#64748b',lw=1,ls='--')
        ax.errorbar(mean,y,xerr=np.vstack([mean-s.lower.to_numpy()*100,s.upper.to_numpy()*100-mean]),fmt='o',color='#087f8c',capsize=3)
        ax.set(title=title,xlabel='Gate minus accept-all (percentage points)',yticks=y,yticklabels=comparisons)
        ax.grid(axis='x',alpha=.2)
    axes[0].invert_yaxis()
    save(fig,'03_gate_contrasts','Does the gate improve delivery?',
         'Paired 95% bootstrap intervals. Learned contrasts resample matched graph clusters and training seeds; zero-crossing intervals are inconclusive.')

    fig,axes=plt.subplots(1,2,figsize=(13,8))
    values=scaling.groupby(['method','nodes']).delivery_rate.mean().unstack().reindex(METHODS)
    im=axes[0].imshow(values.to_numpy()*100,vmin=0,vmax=100,cmap='viridis',aspect='auto')
    axes[0].set(xticks=range(len(values.columns)),xticklabels=values.columns,yticks=range(len(METHODS)),
                yticklabels=[x.upper() for x in METHODS],xlabel='Network nodes',title='Delivery on larger graphs')
    for i in range(len(values)):
        for j in range(len(values.columns)):
            v=values.iloc[i,j]*100;axes[0].text(j,i,f'{v:.1f}',ha='center',va='center',fontsize=8,color='#17212b' if v>60 else 'white')
    fig.colorbar(im,ax=axes[0],label='Delivered (%)',pad=.02)
    for family,color in [('heuristics','#64748b'),('dqn','#377eb8'),('ppo','#087f8c'),('ippo','#e08a36'),('mappo','#8b5cf6')]:
        mask=scaling.method.isin(BASE) if family=='heuristics' else scaling.method.str.startswith(family+'-')
        g=scaling[mask].groupby('nodes').seconds.median()
        axes[1].plot(g.index,g,'o-',label=family.upper(),color=color)
    axes[1].set(yscale='log',xlabel='Network nodes',ylabel='Median wall seconds per episode',title='CPU size-transfer runtime');axes[1].legend()
    save(fig,'04_scaling','Larger-network inference with newly trained models',
         '3 graphs × 2 episodes per size; population/attack budget fixed. Threat density therefore varies. Timing excludes Python allocation instrumentation.')

    selected=['NC','ALL','static-F1-R1-C1-eta0.4','static-F1-R1-C1-eta1.0','static-F1-R1-C1-eta2.0',
              'travel-F1-R1-C1-eta0.4','travel-F1-R1-C1-eta1.0','travel-F1-R1-C1-eta2.0']
    labels=['No communication','Accept all','Static FRC eta=.4','Static FRC eta=1','Static FRC eta=2',
            'Travel FRC eta=.4','Travel FRC eta=1','Travel FRC eta=2']
    fig,axes=plt.subplots(1,2,figsize=(14,7),sharey=True)
    for ax,metric,title in zip(axes,['delivery_rate','spoof_accepted'],['Delivered convoys (%)','Spoofed packets accepted / episode']):
        m=ablate.groupby(['method','response_strength'])[metric].mean().unstack().reindex(selected)
        m.to_csv(out/f'ablation_{metric}.csv')
        display=m*100 if metric=='delivery_rate' else m
        vmax=100 if metric=='delivery_rate' else max(1,display.max().max())
        im=ax.imshow(display.to_numpy(),vmin=0,vmax=vmax,cmap='viridis',aspect='auto')
        ax.set(xticks=range(len(m.columns)),xticklabels=m.columns,yticks=range(len(labels)),yticklabels=labels,
               title=title,xlabel='Blocked-edge response strength')
        for i in range(len(m)):
            for j in range(len(m.columns)):
                v=display.iloc[i,j]
                label=f'{v:.2f}' if metric=='spoof_accepted' and 0<v<1 else f'{v:.1f}'
                ax.text(j,i,label,ha='center',va='center',fontsize=9,color='#17212b' if v>vmax*.6 else 'white')
        fig.colorbar(im,ax=ax,pad=.02)
    save(fig,'05_ablation','Gate filtering and response strength are separate factors',
         'Delayed/lost/spoofed scenario; all methods share the same 10 graphs × 5 episodes. Full factorial data also includes every F/R/C switch combination.')

    fig,axes=plt.subplots(1,2,figsize=(12,5))
    counts=effects.groupby('method').changed_receiver_path.agg(['sum','count']).reindex(['all','gate'])
    axes[0].bar(['ALL','GATE'],counts['count']-counts['sum'],color='#cbd5e1',label='Unchanged path')
    axes[0].bar(['ALL','GATE'],counts['sum'],bottom=counts['count']-counts['sum'],color='#e08a36',label='Changed path')
    for i,r in enumerate(counts.itertuples()):axes[0].text(i,r.count*1.02,f'{int(r.sum)} / {int(r.count)} changed',ha='center')
    axes[0].set(ylim=(0,counts['count'].max()*1.15),ylabel='Interventions',title='Single-message route effects');axes[0].legend(loc='lower right')
    for i,(comm,color) in enumerate([('all','#e08a36'),('gate','#087f8c')]):
        c=effects[effects.method==comm].delta_delivery.value_counts().reindex([-1,0,1],fill_value=0)
        # Only nonzero effects here; unchanged totals are stated explicitly.
        axes[1].bar(np.arange(2)+i*.35,[c[-1],c[1]],width=.35,color=color,label=comm.upper())
        for x,n in zip(np.arange(2)+i*.35,[c[-1],c[1]]):axes[1].text(x,n+.2,str(n),ha='center')
    axes[1].set(xticks=[.175,1.175],xticklabels=['Message harmed delivery','Message helped delivery'],ylabel='Interventions',title='Factual minus one-packet-suppressed outcome');axes[1].legend()
    highest=max(int((effects.delta_delivery<0).sum()),int((effects.delta_delivery>0).sum()))
    axes[1].set_ylim(0,max(1,highest)+1)
    axes[1].set_yticks(range(max(1,highest)+2))
    save(fig,'06_message_replay','Exact single-message replay under stronger threats',
         f'{len(effects):,} interventions; all processed packets replayed, not sampled. Effects are realized counterfactuals; messages can have interacting effects.')

    fig,axes=plt.subplots(2,2,figsize=(13,9))
    chosen=['B1','NC','COMM-ALL','GATE','dqn-gate','ppo-gate','ippo-gate','mappo-gate']
    ax=axes[0,0]
    for i,(scenario,title) in enumerate(SCENARIOS.items()):
        s=summary[summary.scenario==scenario].set_index('method').reindex(chosen)
        ax.bar(np.arange(len(chosen))+i*.25,s.delivery*100,width=.25,label=title)
    ax.set(xticks=np.arange(len(chosen))+.25,xticklabels=[x.upper() for x in chosen],ylim=(0,125),yticks=range(0,101,20),ylabel='Delivered (%)',title='Matched scenarios, selected methods')
    ax.tick_params(axis='x',rotation=50,labelsize=8);ax.legend(fontsize=7)
    ax=axes[0,1]
    for algo in ['dqn','ppo','ippo','mappo']:
        f=train[(train.algo==algo)&(train.comm=='gate')]
        mean=f.groupby('episode').delivery_rate.mean().rolling(10,min_periods=1).mean()
        ax.plot(mean.index+1,mean*100,label=algo.upper())
    ax.set(ylim=(0,105),xlabel='Training episode',ylabel='Delivered (%)',title='Gated models: 10-episode training averages');ax.legend(fontsize=8)
    ax=axes[1,0]
    for method,label,color in [('NC','No communication','#64748b'),('ALL','Accept all','#e08a36'),('travel-F1-R1-C1-eta1.0','Travel gate eta=1','#087f8c')]:
        s=ablate[ablate.method==method].groupby('response_strength').delivery_rate.mean()
        ax.plot(s.index,s*100,'o-',label=label,color=color)
    ax.set(ylim=(0,105),xlabel='Response strength',ylabel='Delivered (%)',title='Response-strength ablation');ax.legend(fontsize=8)
    ax=axes[1,1]
    beneficial=int((effects.delta_delivery>0).sum());harmful=int((effects.delta_delivery<0).sum());same=int((effects.delta_delivery==0).sum())
    ax.bar(['Harmful','No delivery change','Helpful'],[harmful,same,beneficial],color=['#c2413c','#64748b','#087f8c'])
    for i,n in enumerate([harmful,same,beneficial]):ax.text(i,n+len(effects)*.015,str(n),ha='center')
    ax.set(ylim=(0,len(effects)*1.15),ylabel='Single-packet interventions',title=f'Exact replay: {len(effects):,} packets')
    save(fig,'00_overview','Updated results — longer training and harder threats',
         'Three seeds, matched fresh held-out graphs, explicit graph uncertainty and independent gate/penalty ablation. Exploratory results, not a convergence claim.')

    with PdfPages(out/'updated_results_report.pdf') as pdf:
        for name,title,fig in figures[-1:]+figures[:-1]:pdf.savefig(fig)
    write_json(out/'summary.json',dict(source_hash=source_hash(),training_episodes=len(train),checkpoints=model_count,
                                     heldout_episodes=sum(len(f) for f in scenarios.values()),
                                     scaling_episodes=len(scaling),ablation_episodes=len(ablate),
                                     message_interventions=len(effects),changed_paths=int(effects.changed_receiver_path.sum()),
                                     delivery_helped=beneficial,delivery_harmed=harmful,delivery_unchanged=same,
                                     scenario_results=summary.to_dict('records'),paired_contrasts=contrasts.to_dict('records')))
    md=['# Updated exploratory results','',warning,'','All reported figures are regenerated from the rerun data, not the old smoke results.','',
        'The paired comparison intervals are exploratory and are not adjusted for multiple comparisons. Three training seeds do not establish robust retraining uncertainty. The oracle is a true-state diagnostic, not an optimal performance bound. Larger networks retain the same population and attack budget, so threat density changes.', '',
        '[Combined PDF report](updated_results_report.pdf)','']
    for name,title,fig in figures[-1:]+figures[:-1]:
        md.extend([f'## {title}','',f'![{title}]({name}.png)','',f'[Vector PDF]({name}.pdf)','']);plt.close(fig)
    (out/'README.md').write_text('\n'.join(md))
    print('Generated seven updated PNG/PDF figures, combined PDF, summary tables and paired contrasts')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-root',type=Path,default=Path('out/reviewer-rerun-v2'))
    p.add_argument('--output',type=Path,default=Path('../revision/updated-visualisations'))
    a=p.parse_args();main(a.run_root,a.output)
