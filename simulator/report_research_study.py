"""Report actual fresh-study data, including corrected effects and counterexamples."""
import argparse
import base64
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from research_gate import FEATURES, ValueEnsemble
from run_research_study import fingerprint, DESIGN

ROOT=Path(__file__).resolve().parents[1]
ACTORS=['planner','dqn','mappo']
CASES=[c['name'] for c in DESIGN['cases']]
MAIN=['NC','ALL','FRC','SAFE-ALL','VALUE']
CORRECTION=81


def read(run,name):
    p=run/(name+'.csv');return pd.read_csv(p if p.exists() else p.with_suffix('.csv.gz'))


def intervals(differences, seed=914, draws=20000):
    """Cross training seeds with clustered graph/within-graph episode sampling."""
    # graph x independent training seed x shared environment episode
    a=np.asarray(differences,float);g,s,e=a.shape
    rng=np.random.default_rng(seed)
    gi=rng.integers(g,size=(draws,g));si=rng.integers(s,size=(draws,s));ei=rng.integers(e,size=(draws,g,e))
    sampled=a[gi[:,:,None,None],si[:,None,:,None],ei[:,:,None,:]].mean(axis=(1,2,3))
    tail=.05/(2*CORRECTION)
    return float(a.mean()),*np.quantile(sampled,[tail,1-tail]).tolist()


def main():
    global fingerprint,CORRECTION
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/research-opportunity-study');ap.add_argument('--output',default='revision/research-opportunity-results');ap.add_argument('--guarded',action='store_true');ap.add_argument('--correction',type=int);args=ap.parse_args()
    if args.guarded:
        from run_guarded_research_study import fingerprint as guarded_hash
        fingerprint=guarded_hash;CORRECTION=162
    if args.correction:
        assert args.correction>=81
        CORRECTION=args.correction
    run,out=Path(args.run).resolve(),Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((run/'pipeline.json').read_text());locked=json.loads((run/'locked_settings.json').read_text())
    assert manifest['status']=='completed' and manifest['source_hash']==fingerprint()
    assert locked['status']=='locked_before_test' and locked['source_hash']==fingerprint()
    df,raw=read(run,'episodes'),read(run,'convoys')
    assert len(df)==92610 and len(raw)==463050
    assert (df.n_delivered+df.n_destroyed+df.n_censored).eq(5).all()
    assert raw.delivered.add(raw.destroyed).add(raw.censored).eq(1).all()
    assert np.allclose(raw.elapsed,raw.travel+raw.service+raw.wait)
    assert (raw[raw.delivered.eq(1)].nominal>=raw[raw.delivered.eq(1)].nominal_optimal-1e-8).all()
    keys=['family','graph','algo','seed','case','episode','method']
    recomputed=raw.groupby(keys).agg(n_delivered=('delivered','sum'),n_destroyed=('destroyed','sum'),n_censored=('censored','sum'))
    original=df.set_index(keys).sort_index()
    assert original.index.equals(recomputed.index)
    assert (original[recomputed.columns]==recomputed).all().all()
    paired_keys=['family','graph','algo','seed','case','episode','convoy']
    schedules=raw.pivot(index=paired_keys,columns='method',values='depart_t')
    targets=raw.pivot(index=paired_keys,columns='method',values='target')
    assert schedules.nunique(axis=1).eq(1).all() and targets.nunique(axis=1).eq(1).all()
    summary=df.groupby(['family','algo','case','method']).agg(
        episodes=('episode','size'),delivery=('delivery_rate','mean'),follower_delivery=('follower_delivery','mean'),
        utility=('utility_mean','mean'),nominal_delivered=('nominal_delivered_mean','mean'),
        elapsed_delivered=('realized_delivered_mean','mean'),true_admitted=('true_accepted','sum'),spoof_admitted=('spoof_accepted','sum'),sent=('msg_sent','sum'),censored=('n_censored','sum')).reset_index()
    summary['delivery_pct']=summary.delivery*100;summary['follower_delivery_pct']=summary.follower_delivery*100
    summary.to_csv(out/'summary.csv',index=False)
    contrasts=[];common=[]
    for ai,algo in enumerate(ACTORS):
        for ci,case in enumerate(CASES):
            z=df[(df.family=='constructed-forks') & (df.algo==algo) & (df.case==case)]
            pivot=z.pivot(index=['graph','seed','episode'],columns='method',values='delivery_rate').sort_index()
            seeds=1 if algo=='planner' else 3
            assert len(pivot)==10*seeds*20
            for bi,base in enumerate(['ALL','FRC','SAFE-ALL']):
                diff=(pivot.VALUE-pivot[base]).to_numpy().reshape(10,seeds,20)
                mean,lo,hi=intervals(diff,seed=914+ai*100+ci*3+bi)
                contrasts.append(dict(algo=algo,case=case,baseline=base,difference_pp=100*mean,lower_pp=100*lo,upper_pp=100*hi,superiority_supported=lo>0,disadvantage_supported=hi<0,correction=f'{CORRECTION} simultaneous comparisons; paired clustered graphs/episodes, crossed training seeds'))
                a=raw[(raw.family=='constructed-forks') & (raw.algo==algo) & (raw.case==case) & (raw.method=='VALUE')]
                b=raw[(raw.family=='constructed-forks') & (raw.algo==algo) & (raw.case==case) & (raw.method==base)]
                joined=a.merge(b,on=paired_keys,suffixes=('_value','_base'),validate='one_to_one')
                survivors=joined[joined.delivered_value.eq(1)&joined.delivered_base.eq(1)]
                common.append(dict(algo=algo,case=case,baseline=base,common_survivors=len(survivors),nominal_difference=(survivors.nominal_value-survivors.nominal_base).mean(),elapsed_difference=(survivors.realized_value-survivors.realized_base).mean()))
    contrasts=pd.DataFrame(contrasts);contrasts.to_csv(out/'contrasts.csv',index=False)
    pd.DataFrame(common).to_csv(out/'common_survivors.csv',index=False)
    value_info=[];calibration=[]
    for p in sorted((run/'value_models').glob('*.json')):
        state=json.loads(p.read_text());examples=read(run/'value_models',p.stem+'_examples')
        holdout_info=dict(state['internal_holdout']);holdout_info['holdout_positive_delivery_labels']=holdout_info.pop('positive_delivery_labels')
        value_info.append(dict(algo=state['actor'],seed=state['seed'],examples=len(examples),fitted_examples=state['fitted_examples'],positive_delivery_labels=int((examples.delivery_gain>0).sum()),negative_delivery_labels=int((examples.delivery_gain<0).sum()),**holdout_info))
        model=ValueEnsemble.load(state['model']);hold=examples[examples.episode>=80]
        for _,row in hold.iterrows():calibration.append(dict(algo=state['actor'],seed=state['seed'],observed=row.utility_gain,predicted=model.predict(row[FEATURES].to_numpy(float))[0]))
    values=pd.DataFrame(value_info);values.to_csv(out/'value_training_summary.csv',index=False)
    pd.DataFrame(calibration).to_csv(out/'value_internal_holdout_predictions.csv',index=False)
    packet_counts={};total_packets=0
    packet_path=run/'messages.csv'
    for chunk in pd.read_csv(packet_path if packet_path.exists() else packet_path.with_suffix('.csv.gz'),chunksize=100000):
        assert chunk.age.ge(0).all()
        accepted=chunk[chunk.reason.eq('accepted')];assert accepted.age.le(8.+1e-10).all()
        total_packets+=len(chunk)
        for key,count in chunk.groupby(['family','algo','case','method','reason']).size().items():packet_counts[key]=packet_counts.get(key,0)+int(count)
    reason=pd.DataFrame([dict(zip(['family','algo','case','method','reason'],key),packets=count) for key,count in packet_counts.items()])
    reason.to_csv(out/'packet_reasons.csv',index=False)
    admitted=reason[reason.reason.eq('accepted')].groupby(['family','algo','case','method']).packets.sum()
    expected=summary.set_index(['family','algo','case','method'])
    assert (admitted.reindex(expected.index,fill_value=0)==expected.true_admitted+expected.spoof_admitted).all()
    plt.rcParams.update({'font.size':9,'figure.dpi':140})
    images=[]
    with PdfPages(out/'research_opportunity_report.pdf') as pdf:
        def save(fig,name):
            fig.savefig(out/(name+'.png'),bbox_inches='tight');fig.savefig(out/(name+'.pdf'),bbox_inches='tight');pdf.savefig(fig,bbox_inches='tight');images.append(name);plt.close(fig)
        fig,axes=plt.subplots(3,1,figsize=(13,11),sharex=True)
        for ax,algo in zip(axes,ACTORS):
            z=summary[(summary.family=='constructed-forks')&(summary.algo==algo)]
            x=np.arange(len(CASES))
            for mi,m in enumerate(MAIN):
                vals=z[z.method==m].set_index('case').reindex(CASES).delivery_pct
                ax.bar(x+(mi-2)*.16,vals,.16,label=m)
            ax.set_ylim(0,105);ax.set_ylabel('Actual delivery (%)');ax.set_title(algo.upper());ax.grid(axis='y',alpha=.15)
        axes[0].legend(ncol=5,loc='lower center',bbox_to_anchor=(.5,1.1));axes[-1].set_xticks(x,[c.replace('-','\n') for c in CASES]);fig.tight_layout();save(fig,'01_delivery')
        fig,axes=plt.subplots(1,3,figsize=(12,7),sharey=True)
        for ax,algo in zip(axes,ACTORS):
            z=contrasts[contrasts.algo==algo].pivot(index='case',columns='baseline',values='difference_pp').reindex(CASES)[['ALL','FRC','SAFE-ALL']]
            vmax=max(10.,float(np.abs(contrasts.difference_pp).max()))
            im=ax.imshow(z,cmap='RdBu',vmin=-vmax,vmax=vmax,aspect='auto')
            for i,case in enumerate(CASES):
                for j,base in enumerate(z.columns):
                    r=contrasts[(contrasts.algo==algo)&(contrasts.case==case)&(contrasts.baseline==base)].iloc[0]
                    marker='*' if r.superiority_supported else '†' if r.disadvantage_supported else ''
                    ax.text(j,i,f'{r.difference_pp:+.1f}{marker}',ha='center',va='center',color='white' if abs(r.difference_pp)>.55*vmax else 'black',fontsize=9)
            ax.set_xticks(range(3),z.columns);ax.set_yticks(range(9),CASES);ax.set_title(algo.upper())
        fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.65,label='VALUE delivery difference (percentage points)')
        fig.suptitle(f'Paired differences: * corrected benefit, † corrected disadvantage ({CORRECTION}-test correction)');save(fig,'02_corrected_effects')
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        for algo in ['dqn','mappo']:
            frames=[pd.read_csv(p) for p in (run/'models').glob(algo+'*.training.csv')]
            train=pd.concat(frames);curve=train.groupby('episode').delivery_rate.mean().rolling(45,min_periods=10).mean()
            axes[0].plot(curve.index,100*curve,label=algo.upper())
            updates=train.groupby('episode').updates.mean();axes[1].plot(updates.index,updates,label=algo.upper())
        axes[0].set_ylabel('Training actual delivery (%), rolling 45');axes[0].set_xlabel('Training episode');axes[1].set_ylabel('Mean completed optimizer updates');axes[1].set_xlabel('Training episode');axes[0].legend();axes[1].legend();fig.tight_layout();save(fig,'03_actual_training')
        fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
        predictions=pd.DataFrame(calibration)
        for ax,algo in zip(axes,ACTORS):
            z=predictions[predictions.algo==algo];ax.scatter(z.observed,z.predicted,alpha=.35,s=15)
            low=min(z.observed.min(),z.predicted.min());high=max(z.observed.max(),z.predicted.max());ax.plot([low,high],[low,high],'--',color='gray')
            ax.set_xlabel('Observed intervention utility');ax.set_title(algo.upper())
        axes[0].set_ylabel('Predicted utility');fig.suptitle('Internal held-out causal labels: episodes excluded from model fitting');fig.tight_layout();save(fig,'04_value_prediction')
        fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
        for ax,algo in zip(axes,ACTORS):
            z=summary[(summary.family=='constructed-forks')&(summary.algo==algo)]
            for m in ['ALL','SAFE-ALL','VALUE']:
                a=z[z.method==m].set_index('case').reindex(CASES);ax.plot(range(9),(a.true_admitted+a.spoof_admitted)/a.episodes,marker='o',label=m)
            ax.set_title(algo.upper());ax.set_ylabel('Admitted packets / episode')
        axes[0].legend(ncol=3);axes[-1].set_xticks(range(9),[c.replace('-','\n') for c in CASES]);fig.tight_layout();save(fig,'05_admission')
        fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
        for ax,algo in zip(axes,ACTORS):
            z=summary[(summary.family=='constructed-forks')&(summary.algo==algo)]
            for m in (['VALUE','VALUE-NO-WARNING-GUARD','VALUE-NO-CLEARANCE-GUARD'] if args.guarded else ['VALUE','VALUE-NO-UNCERTAINTY','VALUE-NO-FEEDBACK']):
                a=z[z.method==m].set_index('case').reindex(CASES);ax.plot(range(9),a.delivery_pct,marker='o',label=m)
            ax.set_title(algo.upper());ax.set_ylabel('Actual delivery (%)');ax.set_ylim(0,105)
        axes[0].legend(ncol=3);axes[-1].set_xticks(range(9),[c.replace('-','\n') for c in CASES]);fig.tight_layout();save(fig,'06_ablations')
        fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
        for ax,algo in zip(axes,ACTORS):
            z=summary[(summary.family=='original-topology')&(summary.algo==algo)]
            for m in MAIN:
                a=z[z.method==m].set_index('case').reindex(CASES);ax.plot(range(9),a.delivery_pct,marker='o',label=m)
            ax.set_title(algo.upper());ax.set_ylabel('Actual delivery (%)');ax.set_ylim(0,105)
        axes[0].legend(ncol=5);axes[-1].set_xticks(range(9),[c.replace('-','\n') for c in CASES]);fig.suptitle('Original-topology transfer: descriptive check, not a trained deployment guarantee');fig.tight_layout();save(fig,'07_original_transfer')
        fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
        for ax,algo in zip(axes,ACTORS):
            z=summary[(summary.family=='constructed-forks')&(summary.algo==algo)]
            for m in MAIN:
                a=z[z.method==m].set_index('case').reindex(CASES);ax.plot(range(9),a.utility,marker='o',label=m)
            ax.set_title(algo.upper());ax.set_ylabel('Receiver utility / convoy')
        axes[0].legend(ncol=5);axes[-1].set_xticks(range(9),[c.replace('-','\n') for c in CASES]);fig.tight_layout();save(fig,'08_mission_utility')
    supported=contrasts[contrasts.superiority_supported];adverse=contrasts[contrasts.disadvantage_supported]
    body='# Fresh actor-specific value gate: executed results\n\n'
    training_note='The guarded study reuses the first study’s 3,600 fresh DQN/MAPPO training episodes and 700 causal-label-generation episodes; no additional actor or utility fitting is claimed.' if args.guarded else 'The study includes 3,600 fresh DQN/MAPPO training episodes and 700 separate causal-label-generation episodes.'
    body+=f"Completed **{len(df):,} frozen-test episodes** and **{len(raw):,} convoy records**. {training_note} Value regressors fit episodes 0–79 of each 100-episode label study; 80–99 are internal held-out diagnostics. All nine declared cases and the original-topology transfer check are retained.\n\n"
    body+=f"Across 81 primary delivery comparisons with a **{CORRECTION}-test correction**, **{len(supported)} supported superiority** and **{len(adverse)} supported a disadvantage**. These are actor/baseline/case-specific results on constructed physical scout/follower benchmarks, not general superiority.\n\n"
    if args.guarded:
        body+='The unconstrained learned version is retained in ../research-opportunity-results. It sometimes discarded useful warnings. This guarded version preserves fresh confident public-reachable hazard reports and requires two claimed clear sources before erasing a warning; learned utility filters the remaining reports. Actual model predictions and admission overrides are recorded separately. Its layouts, validation tapes and final test tapes are new. Final combined reporting accounts for 81 initial, 81 guarded and 36 cover-stress comparisons when correction=198. Claimed sources remain unauthenticated.\n\n'
    body+='## Frozen settings\n\n```json\n'+json.dumps(locked,indent=2)+'\n```\n\n'
    body+='## Supported positive comparisons\n\n'+(supported.drop(columns='correction').to_markdown(index=False) if len(supported) else 'None after correction.')+'\n\n'
    body+='## Supported adverse comparisons\n\n'+(adverse.drop(columns='correction').to_markdown(index=False) if len(adverse) else 'None after correction; lack of detected disadvantage is not proof of noninferiority.')+'\n\n'
    body+='## All delivery results\n\n'+summary[summary.method.isin(MAIN)][['family','algo','case','method','episodes','delivery_pct','follower_delivery_pct','utility','censored']].to_markdown(index=False)+'\n\n'
    body+='## All corrected comparisons\n\n'+contrasts.drop(columns='correction').to_markdown(index=False)+'\n\n'
    body+='## Value learning diagnostics\n\n'+values.to_markdown(index=False)+'\n\n'
    body+=('## What these results can establish\n\nA positive result must identify the actor, baseline and declared condition shown above. Gains over ALL or tuned FRC that do not persist against SAFE-ALL do not establish a learned-value contribution beyond conservative clearance filtering. Cross-actor, no-hazard, redundant-sensing, late-warning and impersonation cases bound any claim. Original-topology transfer is descriptive, with different sensing/attack timing and no actor retraining on that graph. Constructed layouts randomize costs, stages and hot branches; they remain designed mechanism benchmarks, not representative sampled military networks.\n\n'
             'Methods use the same actor weights, sensors, target/departure schedules and exogenous tapes. Training, validation and test namespaces are disjoint. All gates are receiver-side filters: admission counts are not bandwidth savings. Public feature vectors exclude genuine labels, simulator attacks, future outcomes, packet origins and privileged critic state. Sender agreement and ensemble uncertainty remain approximate. Full-episode training labels are conditional on chronological prefixes and may differ from the distribution induced by the learned gate.\n\n'
             f'Confidence intervals use 20,000 paired bootstrap draws, clustering graph and within-graph episodes while crossing independent training seeds with shared environment tapes. Two-sided Bonferroni tails cover {CORRECTION} tests. With only three training seeds and ten constructed layouts, uncertainty estimates have limited support; no real-world confidence guarantee or convergence claim follows. Common-survivor time/cost contrasts are in common_survivors.csv and exclude pairs where either method fails delivery. No test outcome was used to fit the utility models or select frozen numeric settings; the guarded architecture responds to the earlier study’s failures and is tested on a new split.\n\n')
    body+='## Reproduce\n\n```bash\nbash setup_local.sh\ncd simulator\n../.venv/bin/python run_research_study.py --workers 3 --output out/research-opportunity-study-new\ncd ..\nMPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_research_study.py --correction 198 --run simulator/out/research-opportunity-study-new --output revision/research-opportunity-results-new\n```\n\nRead ../research-opportunity-methods.md for exact semantics and assumptions. Open index.html locally for the eight-figure offline report, or research_opportunity_report.pdf.\n'
    if args.guarded:
        body+='\nAfter the first run, generate the guarded study and report:\n\n```bash\ncd simulator\n../.venv/bin/python run_guarded_research_study.py --parent out/research-opportunity-study-new --output out/guarded-research-study-new --workers 3\ncd ..\nMPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_research_study.py --guarded --correction 198 --run simulator/out/guarded-research-study-new --output revision/guarded-research-results-new\n```\n'
    (out/'README.md').write_text(body)
    html='<!doctype html><html><meta charset="utf-8"><title>Fresh value-gate study</title><style>body{font:16px system-ui;max-width:1300px;margin:2rem auto;padding:1rem}img{width:100%}</style><h1>Fresh actor-specific value study</h1><p>Read README.md for full corrected results, settings and caveats.</p>'
    for name in images:html+=f'<h2>{name.replace("_"," ")}</h2><img src="data:image/png;base64,{base64.b64encode((out/(name+".png")).read_bytes()).decode()}" alt="{name}">'
    (out/'index.html').write_text(html+'</html>')
    verification=dict(status='passed',source_hash=fingerprint(),evaluation_episodes=len(df),convoys=len(raw),processed_packets=total_packets,fresh_actor_training_episodes=0 if args.guarded else 3600,reused_actor_training_episodes=3600 if args.guarded else 0,causal_generation_episodes=0 if args.guarded else 700,reused_causal_generation_episodes=700 if args.guarded else 0,primary_tests=81,correction_tests=CORRECTION,supported_positive=len(supported),supported_adverse=len(adverse),figures=len(images),schedules_matched=True,integer_delivery_counts_verified=True)
    (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))


if __name__=='__main__':main()
