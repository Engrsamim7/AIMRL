"""Audit every arm and report the prospectively declared matched-training study."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from run_matched_gate_study import fingerprint, METHODS, TEST_CASES, SEEDS

CASES=[c.name for c in TEST_CASES]
BASES=['ALL','SAFE','VALUE']
CORRECTION=248
DRAWS=200000


def crossed_samples(a, seed=731, draws=DRAWS, chunk=400):
    """Graph x seed x case x environment episode x contrast.

    Cross seed resampling with graph/within-graph episode clusters. Preserve
    all contrast/case correlations in the pooled primary sampling distribution.
    Multinomial seed weights exactly equal sampling seeds with replacement.
    """
    a=np.asarray(a,float); g,s,c,e,q=a.shape
    rng=np.random.default_rng(seed); samples=np.empty((draws,c,q))
    matrix=a.transpose(1,0,2,3,4).reshape(s,-1)
    for start in range(0,draws,chunk):
        n=min(chunk,draws-start)
        sw=rng.multinomial(s,np.full(s,1/s),size=n)/s
        weighted=(sw@matrix).reshape(n,g,c,e,q)
        gi=rng.integers(g,size=(n,g))
        ei=rng.integers(e,size=(n,g,c,e))
        selected=weighted[np.arange(n)[:,None,None,None],gi[:,:,None,None],np.arange(c)[None,None,:,None],ei]
        samples[start:start+n]=selected.mean(axis=(1,3))
    return samples


def bounds(samples):
    return np.quantile(samples,[.05/(2*CORRECTION),1-.05/(2*CORRECTION)],axis=0)


def read(run,name):
    path=run/(name+'.csv')
    return pd.read_csv(path if path.exists() else path.with_suffix('.csv.gz'))


def audit(df,raw,expected,methods):
    assert len(df)==expected and len(raw)==5*expected
    assert not df.duplicated(['graph','algo','seed','case','episode','method']).any()
    assert set(df.method)==set(methods)
    assert (df.n_delivered+df.n_destroyed+df.n_censored).eq(5).all()
    assert (raw.delivered+raw.destroyed+raw.censored).eq(1).all()
    assert np.allclose(raw.elapsed,raw.travel+raw.service+raw.wait)
    keys=['graph','algo','seed','case','episode','method']
    actual=raw.groupby(keys).delivered.sum().sort_index(); recorded=df.set_index(keys).n_delivered.sort_index()
    assert actual.index.equals(recorded.index) and actual.eq(recorded).all()
    paired=['graph','algo','seed','case','episode','convoy']
    for field in ['depart_t','target']:
        assert raw.pivot(index=paired,columns='method',values=field).nunique(axis=1).eq(1).all()
    # Every algorithm sees the exact same environment schedule under all seeds.
    z=raw.groupby(['graph','case','episode','convoy']).agg(departures=('depart_t','nunique'),targets=('target','nunique'))
    assert z.departures.eq(1).all() and z.targets.eq(1).all()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/matched-gate-study');ap.add_argument('--output',default='revision/matched-gate-results');args=ap.parse_args()
    run,out=Path(args.run).resolve(),Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((run/'pipeline.json').read_text());locked=json.loads((run/'locked_settings.json').read_text())
    assert meta['status']=='completed' and meta['source_hash']==fingerprint()
    assert locked['status']=='locked_before_test' and locked['source_hash']==fingerprint() and not locked['validation_used_for_selection']
    for name,digest in locked['checkpoints'].items(): assert hashlib.sha256((run/'models'/name).read_bytes()).hexdigest()==digest
    df,raw=read(run,'test_episodes'),read(run,'test_convoys'); audit(df,raw,81920,METHODS)
    mech,mraw=read(run,'mechanism_episodes'),read(run,'mechanism_convoys'); audit(mech,mraw,10240,['SAFE','COMBINED'])
    validation=read(run,'validation');assert len(validation)==6144
    training=pd.concat([pd.read_csv(p) for p in sorted((run/'training').glob('*.csv.gz'))],ignore_index=True)
    assert len(training)==24000
    manifest=read(run,'training_manifest'); assert len(manifest)==64 and manifest.actor_exposure_episodes.eq(600).all() and manifest.adaptation_updates.gt(0).all()
    assert manifest.groupby(['algo','seed']).warmup_weight_hash.nunique().eq(1).all()
    summary=df.groupby(['algo','case','method']).agg(episodes=('episode','size'),delivery=('delivery_rate','mean'),follower_delivery=('follower_delivery','mean'),utility=('utility_mean','mean'),elapsed_delivered=('realized_delivered_mean','mean'),nominal_delivered=('nominal_delivered_mean','mean'),true_admitted=('true_accepted','sum'),forged_admitted=('spoof_accepted','sum'),sent=('msg_sent','sum')).reset_index()
    summary['delivery_pct']=100*summary.delivery;summary['follower_delivery_pct']=100*summary.follower_delivery
    summary.to_csv(out/'summary.csv',index=False)
    df.groupby(['algo','stages','case','method']).delivery_rate.mean().mul(100).rename('delivery_pct').to_csv(out/'topology_size.csv')
    records=[]; seed_effects=[]
    for ai,algo in enumerate(['dqn','mappo']):
        z=df[df.algo==algo].pivot(index=['graph','seed','case','episode'],columns='method',values='delivery_rate')
        idx=pd.MultiIndex.from_product([range(16),SEEDS,CASES,range(10)],names=z.index.names)
        z=z.reindex(idx);assert not z.isna().any().any()
        a=np.stack([(z.COMBINED-z[b]).to_numpy().reshape(16,8,8,10) for b in BASES],axis=-1)
        sampled=crossed_samples(a,seed=732+ai);lo,hi=bounds(sampled)
        for ci,c in enumerate(CASES):
            for bi,b in enumerate(BASES):
                records.append(dict(algo=algo,scope='case',case=c,baseline=b,difference_pp=100*a[:,:,ci,:,bi].mean(),lower_pp=100*lo[ci,bi],upper_pp=100*hi[ci,bi]))
        pl,pu=bounds(sampled.mean(axis=1)[:,1])
        records.append(dict(algo=algo,scope='primary',case='equal-case-average',baseline='SAFE',difference_pp=100*a[:,:,:,:,1].mean(),lower_pp=100*pl,upper_pp=100*pu))
        for si,s in enumerate(SEEDS): seed_effects.append(dict(algo=algo,seed=s,difference_pp=100*a[:,si,:,:,1].mean()))
        print(f'BOOTSTRAP {algo} complete',flush=True)
    contrasts=pd.DataFrame(records);contrasts['superiority_supported']=contrasts.lower_pp>0;contrasts['disadvantage_supported']=contrasts.upper_pp<0
    contrasts.to_csv(out/'contrasts.csv',index=False);pd.DataFrame(seed_effects).to_csv(out/'primary_seed_effects.csv',index=False)
    primary=contrasts[contrasts.scope=='primary']; survivors=[]
    pairkeys=['graph','algo','seed','case','episode','convoy']
    va=raw[raw.method=='COMBINED']
    for baseline in BASES:
        both=va.merge(raw[raw.method==baseline],on=pairkeys,suffixes=('_combined','_baseline'),validate='one_to_one')
        both=both[both.delivered_combined.eq(1)&both.delivered_baseline.eq(1)].copy()
        both['elapsed_difference']=both.elapsed_combined-both.elapsed_baseline;both['nominal_difference']=both.nominal_combined-both.nominal_baseline
        stats=both.groupby(['algo','case']).agg(common_survivors=('convoy','size'),elapsed_difference=('elapsed_difference','mean'),nominal_difference=('nominal_difference','mean')).reset_index();stats['baseline']=baseline;survivors.append(stats)
    pd.concat(survivors).to_csv(out/'common_survivors.csv',index=False)
    mz=mech.pivot(index=['algo','seed','graph','case','episode'],columns='method',values='delivery_rate')
    md=(100*(mz.COMBINED-mz.SAFE)).rename('difference_pp').reset_index()
    md.groupby(['algo','case']).difference_pp.mean().to_csv(out/'fixed_actor_diagnostic.csv')
    md.groupby('algo').difference_pp.mean().to_csv(out/'fixed_actor_pooled.csv')
    prediction=pd.DataFrame([dict(algo=p.stem.split('_s')[0],seed=int(p.stem.split('_s')[1]),**{k:v for k,v in json.loads(p.read_text()).items() if k in ['examples','fit_examples','holdout_examples','holdout_mae']}) for p in sorted((run/'value_models').glob('*.json'))])
    prediction.to_csv(out/'prediction_diagnostic.csv',index=False)
    images=[];plt.rcParams.update({'font.size':10,'figure.dpi':140})
    with PdfPages(out/'matched_gate_report.pdf') as pdf:
        def save(fig,name):
            fig.savefig(out/(name+'.png'),bbox_inches='tight');fig.savefig(out/(name+'.pdf'),bbox_inches='tight');pdf.savefig(fig,bbox_inches='tight');images.append(name);plt.close(fig)
        fig,ax=plt.subplots(figsize=(9,4))
        for i,r in enumerate(primary.itertuples()): ax.errorbar(r.difference_pp,i,xerr=[[r.difference_pp-r.lower_pp],[r.upper_pp-r.difference_pp]],fmt='o',capsize=5,label=r.algo.upper())
        ax.axvline(0,color='black',lw=1);ax.set_yticks([0,1],['DQN','MAPPO']);ax.set_xlabel('COMBINED minus SAFE delivery (percentage points)');ax.set_title('Primary endpoint: equal average across all 8 conditions\nSimultaneous intervals, 248-comparison correction');fig.tight_layout();save(fig,'01_primary_effect')
        for metric,title,name in [('delivery_pct','Delivery (%)','02_delivery'),('follower_delivery_pct','Follower delivery (%)','03_follower_delivery'),('utility','Defined utility / convoy','04_utility')]:
            fig,axes=plt.subplots(2,1,figsize=(13,8),sharex=True)
            for ax,algo in zip(axes,['dqn','mappo']):
                z=summary[summary.algo==algo]
                for mi,m in enumerate(METHODS):ax.bar(np.arange(8)+(mi-1.5)*.2,z[z.method==m].set_index('case').reindex(CASES)[metric],.2,label=m)
                ax.set_title(algo.upper());ax.set_ylabel(title)
                if metric!='utility':ax.set_ylim(0,105)
            axes[0].legend(ncol=4);axes[-1].set_xticks(range(8),[c.replace('-','\n') for c in CASES]);fig.tight_layout();save(fig,name)
        fig,axes=plt.subplots(1,2,figsize=(12,7),sharey=True);casecontrasts=contrasts[contrasts.scope=='case'];limit=max(2,float(casecontrasts.difference_pp.abs().max()))
        for ax,algo in zip(axes,['dqn','mappo']):
            z=casecontrasts[casecontrasts.algo==algo].pivot(index='case',columns='baseline',values='difference_pp').reindex(CASES)[BASES]
            im=ax.imshow(z,cmap='RdBu',vmin=-limit,vmax=limit,aspect='auto')
            for ci,c in enumerate(CASES):
                for bi,b in enumerate(BASES):
                    r=casecontrasts[(casecontrasts.algo==algo)&(casecontrasts.case==c)&(casecontrasts.baseline==b)].iloc[0]
                    ax.text(bi,ci,f'{r.difference_pp:+.2f}'+('*' if r.superiority_supported else '†' if r.disadvantage_supported else ''),ha='center',va='center',color='white' if abs(r.difference_pp)>.6*limit else 'black')
            ax.set_xticks(range(3),BASES);ax.set_yticks(range(8),CASES);ax.set_title(algo.upper())
        fig.colorbar(im,ax=axes.ravel().tolist(),label='COMBINED minus baseline (pp)',shrink=.7);fig.suptitle('All case effects: * corrected benefit, † corrected disadvantage');save(fig,'05_case_effects')
        fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=pd.DataFrame(seed_effects);z=z[z.algo==algo];ax.bar(z.seed,z.difference_pp);ax.axhline(0,color='black',lw=1);ax.set_title(algo.upper());ax.set_xlabel('Paired independent training seed')
        axes[0].set_ylabel('COMBINED minus SAFE delivery (pp)');fig.suptitle('Primary effect by seed: descriptive variation');fig.tight_layout();save(fig,'06_seed_variation')
        fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            for m in METHODS:
                y=training[(training.algo==algo)&(training.method==m)].groupby('episode').delivery_rate.mean().rolling(30,min_periods=1).mean()*100
                ax.plot(y.index,y,label=m)
            ax.set_title(algo.upper());ax.set_xlabel('Training episode (300 common warmup episodes precede this)');ax.legend()
        axes[0].set_ylabel('Training delivery (%, rolling 30)');fig.tight_layout();save(fig,'07_real_training')
        fig,axes=plt.subplots(1,2,figsize=(13,5),sharey=True)
        for ax,algo in zip(axes,['dqn','mappo']):
            z=md[md.algo==algo].groupby('case').difference_pp.mean().reindex(CASES)
            ax.bar(range(8),z);ax.axhline(0,color='black',lw=1);ax.set_xticks(range(8),[c.replace('-','\n') for c in CASES],fontsize=8);ax.set_title(algo.upper())
        axes[0].set_ylabel('COMBINED minus SAFE delivery (pp)');fig.suptitle('Same COMBINED-trained actor, gate swap: descriptive only');fig.tight_layout();save(fig,'08_fixed_actor_diagnostic')
    pos=contrasts.superiority_supported.sum();neg=contrasts.disadvantage_supported.sum()
    successful=primary[primary.superiority_supported].algo.tolist()
    body='# Matched-training gate study\n\n'
    body+=f'Completed 81,920 final method-evaluation episodes (409,600 convoy records), 10,240 fixed-actor diagnostic episodes, 64 adapted checkpoints and eight independent paired training seeds per algorithm. **Primary learned-addition superiority supported for: {", ".join(successful) if successful else "neither algorithm"}.**\n\n'
    body+='## Primary question: does learned filtering add benefit beyond safeguards?\n\n'+primary.to_markdown(index=False)+'\n\n'
    body+='Positive numerical differences without a positive corrected lower bound are inconclusive. The intervals jointly correct 50 new and 198 prior comparisons; secondary case wins do not replace the pooled primary endpoint. Eight paired seeds are the training replication, not the number of convoy records.\n\n'
    body+='## All conditions\n\n'+summary[['algo','case','method','episodes','delivery_pct','follower_delivery_pct','utility','elapsed_delivered']].to_markdown(index=False)+'\n\n'
    body+='## All confirmatory comparisons\n\n'+contrasts.to_markdown(index=False)+'\n\n'
    body+='## Interpretation and limits\n\n'
    body+=f'Auxiliary training generated {int(prediction.examples.sum()):,} eligible packet interventions from 2,560 factual episodes, requiring {int(2*prediction.examples.sum()):,} replay branches in addition to the routing training episodes. These are training simulations, not independent final evaluation episodes.\n\n'
    body+='Routing actors have equal episode budgets: 300 shared ALL warmup plus 300 arm-specific adaptation episodes. SAFE and COMBINED share exactly the same safeguards; SAFE differs from the previous SAFE-ALL baseline. Learned arms additionally consume auxiliary causal replay labels available to all arms. Total computation is not matched. Updates and runtime are in training_manifest.csv. A value model fitted to the warmup actor stays fixed, so actor adaptation can make its estimates stale. Validation was diagnostic only; settings and checkpoint hashes were locked before tests. No model selection or retuning used final outcomes.\n\n'
    body+='Final layouts/tapes are new; half the layouts have four forks, a size absent from training. Two corruption conditions have unseen parameters. The pooled endpoint includes late/no-hazard controls equally. This tests bounded structured-network generalization, not operational performance. Forged messages use public target edges and independent fair-coin payloads, may be correct by coincidence and claim unauthenticated identities. Loss applies only to honest transmissions; forgery models receiver injection. Admission does not save transmitted bandwidth.\n\n'
    body+='Fixed-actor swaps isolate immediate filtering under the COMBINED-trained actor, whereas primary contrasts include actor adaptation. Those swaps, topology-size breakdowns, training curves, utility, packet counts, prediction errors and common-survivor cost/time are descriptive. Common-survivor comparisons condition on both methods succeeding and are not unconditional cost guarantees. No nonsignificant result establishes equivalence/noninferiority, and training curves do not establish convergence. All earlier failures remain preserved.\n\n'
    body+='## Reproduce\n\nSee [the locked protocol](../matched-gate-protocol.md). The package includes the full simulator, all 64 checkpoints, fitted regressors, auxiliary examples, training/validation/episode/convoy records and report code.\n'
    (out/'README.md').write_text(body)
    html='<!doctype html><html><meta charset="utf-8"><title>Matched gate study</title><style>body{font:16px system-ui;max-width:1200px;margin:2rem auto;padding:1rem}img{width:100%}table{border-collapse:collapse}td,th{padding:.4rem;border:1px solid #ccc}</style><h1>Matched-training gate study</h1>'+primary.to_html(index=False)+'<p>Read README.md for protocol, all cases and limitations.</p>'
    for name in images:html+=f'<h2>{name.replace("_"," ")}</h2><img src="data:image/png;base64,{base64.b64encode((out/(name+".png")).read_bytes()).decode()}" alt="{name}">'
    (out/'index.html').write_text(html+'</html>')
    check=dict(status='passed',source_hash=fingerprint(),test_episodes=len(df),test_convoys=len(raw),mechanism_episodes=len(mech),validation_episodes=len(validation),unique_training_episodes=len(training),auxiliary_factual_episodes=2560,auxiliary_packet_interventions=int(prediction.examples.sum()),auxiliary_replay_branches=int(2*prediction.examples.sum()),final_checkpoints=64,training_seeds_per_algorithm=8,new_confirmatory_comparisons=50,correction_tests=CORRECTION,bootstrap_draws=DRAWS,supported_positive=int(pos),supported_adverse=int(neg),primary_supported_algorithms=successful,figures=len(images),integer_counts_verified=True,schedules_matched=True,checkpoint_hashes_verified=True)
    (out/'verification.json').write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check),flush=True)

if __name__=='__main__':main()
