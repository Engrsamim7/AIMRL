"""Audit and render every condition of the predeclared recovery study."""
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
from recovery_gate import METHODS, TEST
from run_recovery_gate_study import fingerprint, SEEDS
from report_matched_gate_study import crossed_samples, audit, read
CASES=[c.name for c in TEST]
BASES=['ALL','SAFE','KEEP','AGE']
CORRECTION=388
DRAWS=200000

def bounds(samples):return np.quantile(samples,[.05/(2*CORRECTION),1-.05/(2*CORRECTION)],axis=0)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/recovery-gate-study');ap.add_argument('--output',default='revision/recovery-gate-results');args=ap.parse_args()
 run,out=Path(args.run).resolve(),Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
 meta=json.loads((run/'pipeline.json').read_text());locked=json.loads((run/'locked_settings.json').read_text());assert meta['status']=='completed' and meta['source_hash']==fingerprint()
 assert locked['status']=='locked_before_test' and locked['source_hash']==fingerprint()
 for folder,key in [('models','checkpoints'),('value_models','estimators')]:
  for name,digest in locked[key].items():assert hashlib.sha256((run/folder/name).read_bytes()).hexdigest()==digest
 df,raw=read(run,'test_episodes'),read(run,'test_convoys');audit(df,raw,102400,METHODS)
 mech,mraw=read(run,'mechanism_episodes'),read(run,'mechanism_convoys');audit(mech,mraw,7680,['LEARN','REJECT_ONLY','INITIAL_MODEL'])
 assert df.overrides.le(10).all() and df.accept_overrides.add(df.reject_overrides).eq(df.overrides).all()
 assert df[df.method!='LEARN'].overrides.eq(0).all()
 train=pd.concat([pd.read_csv(p) for p in sorted((run/'training').glob('*.csv.gz'))],ignore_index=True);assert len(train)==28800
 manifest=read(run,'training_manifest');assert len(manifest)==80 and manifest.actor_exposure_episodes.eq(600).all() and manifest.adaptation_updates.gt(0).all()
 assert manifest.groupby(['algo','seed']).warmup_weight_hash.nunique().eq(1).all()
 val=read(run,'validation');assert len(val)==43008
 from run_recovery_gate_study import select_settings
 recovered,selection=select_settings(val);assert recovered==locked['settings']
 pd.DataFrame(selection).to_csv(out/'validation_selection.csv',index=False)
 summary=df.groupby(['algo','case','method']).agg(episodes=('episode','size'),delivery_pct=('delivery_rate',lambda x:100*x.mean()),utility=('utility_mean','mean'),follower_delivery_pct=('follower_delivery',lambda x:100*x.mean()),eligible=('eligible','sum'),genuine_clears=('genuine_clears','sum'),genuine_warning_clears=('genuine_warning_clears','sum'),overrides=('overrides','sum'),accept_overrides=('accept_overrides','sum'),reject_overrides=('reject_overrides','sum'),true_admitted=('true_accepted','sum'),forged_admitted=('spoof_accepted','sum'),sent=('msg_sent','sum')).reset_index()
 summary.to_csv(out/'summary.csv',index=False)
 df.groupby(['algo','method']).agg(delivery_pct=('delivery_rate',lambda x:100*x.mean()),utility=('utility_mean','mean'),overrides=('overrides','sum'),accept_overrides=('accept_overrides','sum'),reject_overrides=('reject_overrides','sum')).to_csv(out/'pooled_means.csv')
 records=[];seedrows=[]
 for ai,algo in enumerate(['dqn','mappo']):
  index=pd.MultiIndex.from_product([range(16),SEEDS,CASES,range(10)],names=['graph','seed','case','episode']);arrays=[]
  for endpoint in ['utility','delivery']:
   z=df[df.algo==algo].pivot(index=index.names,columns='method',values='utility_mean' if endpoint=='utility' else 'delivery_rate').reindex(index);assert not z.isna().any().any()
   scale=1. if endpoint=='utility' else 100.
   arrays.extend([scale*(z.LEARN-z[b]).to_numpy().reshape(16,8,8,10) for b in BASES])
  a=np.stack(arrays,axis=-1);sampled=crossed_samples(a,seed=8831+ai,draws=DRAWS);lo,hi=bounds(sampled);pl,pu=bounds(sampled.mean(axis=1))
  for ei,endpoint in enumerate(['utility','delivery']):
   for bi,baseline in enumerate(BASES):
    q=ei*4+bi
    for ci,case in enumerate(CASES):records.append(dict(algo=algo,scope='case',case=case,baseline=baseline,endpoint=endpoint,difference=a[:,:,ci,:,q].mean(),lower=lo[ci,q],upper=hi[ci,q]))
    if baseline!='ALL':
     records.append(dict(algo=algo,scope='primary',case='equal-case-average',baseline=baseline,endpoint=endpoint,difference=a[:,:,:,:,q].mean(),lower=pl[q],upper=pu[q]))
     for si,seed in enumerate(SEEDS):seedrows.append(dict(algo=algo,seed=seed,baseline=baseline,endpoint=endpoint,difference=a[:,si,:,:,q].mean()))
  print(f'BOOTSTRAP {algo} complete',flush=True)
 contrasts=pd.DataFrame(records);assert len(contrasts)==140
 contrasts['improvement_supported']=contrasts.lower>0;contrasts['harm_supported']=contrasts.upper<0
 contrasts.to_csv(out/'contrasts.csv',index=False);pd.DataFrame(seedrows).to_csv(out/'primary_seed_effects.csv',index=False)
 primary=contrasts[contrasts.scope=='primary'];success=[]
 for (algo,b),z in primary.groupby(['algo','baseline']):
  u=z[z.endpoint=='utility'].iloc[0];d=z[z.endpoint=='delivery'].iloc[0]
  success.append(dict(algo=algo,baseline=b,utility_difference=u.difference,utility_lower=u.lower,utility_upper=u.upper,delivery_difference_pp=d.difference,delivery_lower_pp=d.lower,delivery_upper_pp=d.upper,utility_superiority=bool(u.lower>0),delivery_noninferiority=bool(d.lower> -1.),joint_success=bool(u.lower>0 and d.lower> -1.)))
 success=pd.DataFrame(success);success.to_csv(out/'primary_decisions.csv',index=False)
 mech.groupby(['algo','case','method']).agg(delivery_pct=('delivery_rate',lambda x:100*x.mean()),utility=('utility_mean','mean'),overrides=('overrides','sum'),accept_overrides=('accept_overrides','sum')).to_csv(out/'fixed_actor_ablation.csv')
 diagnostics=[];labelcounts=[]
 for p in sorted((run/'value_models').glob('*.json')):
  algo,tail=p.stem.split('_s');seed,stage=tail.split('_');d=json.loads(p.read_text());diagnostics.append(dict(algo=algo,seed=int(seed),stage=stage,**d['diagnostic']))
 for p in sorted((run/'value_models').glob('*_examples.csv.gz')):
  data=pd.read_csv(p);algo,tail=p.name.split('_s');seed=int(tail.split('_')[0]);assert len(data)>50 and data.delivery_gain.isin([-1,0,1]).all()
  for stage,z in data.groupby('stage'):labelcounts.append(dict(algo=algo,seed=seed,stage=stage,examples=len(z),fit_examples=int((z.episode<56).sum()),holdout_examples=int((z.episode>=56).sum()),nonzero_utility=int(z.utility_gain.abs().gt(.1).sum()),delivery_help=int(z.delivery_gain.gt(0).sum()),delivery_harm=int(z.delivery_gain.lt(0).sum()),genuine_clears=int((z.genuine & ~z.blocked_report).sum())))
 diagnostics=pd.DataFrame(diagnostics);diagnostics.to_csv(out/'prediction_diagnostics.csv',index=False);pd.DataFrame(labelcounts).to_csv(out/'label_diagnostics.csv',index=False)
 df.groupby(['algo','stages','case','method']).agg(delivery_pct=('delivery_rate',lambda x:100*x.mean()),utility=('utility_mean','mean')).to_csv(out/'topology_size.csv')
 images=[];plt.rcParams.update({'font.size':10,'figure.dpi':140})
 with PdfPages(out/'recovery_gate_report.pdf') as pdf:
  def save(fig,name):
   fig.tight_layout();pdf.savefig(fig);fig.savefig(out/(name+'.png'),dpi=150);fig.savefig(out/(name+'.pdf'));images.append(name);plt.close(fig)
  for endpoint,title,unit in [('utility','Pooled mission utility: learned gate minus baseline','utility units per convoy'),('delivery','Pooled delivery: learned gate minus baseline','percentage points')]:
   fig,axes=plt.subplots(1,2,figsize=(11,4.4),sharex=True)
   for ax,algo in zip(axes,['dqn','mappo']):
    z=primary[(primary.algo==algo)&(primary.endpoint==endpoint)].set_index('baseline').reindex(['SAFE','KEEP','AGE']);y=np.arange(3)
    ax.errorbar(z.difference,y,xerr=np.vstack([z.difference-z.lower,z.upper-z.difference]),fmt='o',capsize=4);ax.axvline(0,color='black',lw=1)
    if endpoint=='delivery':ax.axvline(-1,color='orange',ls='--',label='noninferiority margin -1 pp');ax.legend(fontsize=8)
    ax.set_yticks(y,['SAFE','KEEP','AGE']);ax.invert_yaxis();ax.set_title(algo.upper());ax.set_xlabel(unit);ax.grid(axis='x',alpha=.25)
   fig.suptitle(title+'\nConservative intervals: 388-comparison correction, 8 paired training seeds',fontsize=11);save(fig,'pooled_'+endpoint)
  for endpoint,title in [('utility','Mission utility differences'),('delivery','Delivery differences (percentage points)')]:
   fig,axes=plt.subplots(1,2,figsize=(12,6.6),sharey=True);z=contrasts[(contrasts.scope=='case')&(contrasts.endpoint==endpoint)];lim=max(abs(z.difference).max(),.1)
   for ax,algo in zip(axes,['dqn','mappo']):
    v=z[z.algo==algo].pivot(index='case',columns='baseline',values='difference').reindex(index=CASES,columns=BASES);im=ax.imshow(v,cmap='RdBu',vmin=-lim,vmax=lim,aspect='auto')
    for i in range(8):
     for j in range(4):
      r=z[(z.algo==algo)&(z.case==CASES[i])&(z.baseline==BASES[j])].iloc[0];mark='*' if r.lower>0 else '!' if r.upper<0 else ''
      ax.text(j,i,f'{v.iloc[i,j]:+.2f}{mark}',ha='center',va='center',fontsize=9,color='white' if abs(v.iloc[i,j])>.6*lim else 'black')
    ax.set_xticks(range(4),BASES);ax.set_yticks(range(8),CASES);ax.set_title(algo.upper());ax.set_xlabel('LEARN minus baseline')
   fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.6,pad=.03);fig.suptitle(title+'\n* corrected benefit; ! corrected harm; unmarked = unresolved',fontsize=11);fig.subplots_adjust(left=.20,right=.85,top=.88,wspace=.25);pdf.savefig(fig);fig.savefig(out/('case_'+endpoint+'.png'),dpi=150);fig.savefig(out/('case_'+endpoint+'.pdf'));images.append('case_'+endpoint);plt.close(fig)
  fig,axes=plt.subplots(2,2,figsize=(12,8))
  for ri,algo in enumerate(['dqn','mappo']):
   z=summary[summary.algo==algo]
   for ci,(metric,title) in enumerate([('utility','Mean mission utility'),('delivery_pct','Delivery (%)')]):
    ax=axes[ri,ci]
    for method in METHODS:
     v=z[z.method==method].set_index('case').reindex(CASES);ax.plot(range(8),v[metric],marker='o',label=method,lw=2 if method=='LEARN' else 1)
    ax.set_xticks(range(8),CASES,rotation=55,ha='right',fontsize=8);ax.set_title(algo.upper()+': '+title);ax.grid(alpha=.25)
  axes[0,0].legend(ncol=3,fontsize=8);fig.suptitle('All conditions and all matched-trained methods (means; see contrasts for uncertainty)');save(fig,'all_methods')
  fig,axes=plt.subplots(1,2,figsize=(12,5))
  for ax,algo in zip(axes,['dqn','mappo']):
   z=summary[(summary.algo==algo)&(summary.method=='LEARN')].set_index('case').reindex(CASES);n=z.episodes
   ax.bar(range(8),z.accept_overrides/n,label='accept over SAFE');ax.bar(range(8),z.reject_overrides/n,bottom=z.accept_overrides/n,label='reject over SAFE');ax.set_xticks(range(8),CASES,rotation=55,ha='right',fontsize=8);ax.set_title(algo.upper());ax.set_ylabel('Overrides per five-convoy episode');ax.legend(fontsize=8)
  fig.suptitle('Actual bounded decision authority used; maximum 2 per receiver');save(fig,'gate_authority')
  fig,axes=plt.subplots(1,2,figsize=(11,4.5))
  for ax,algo in zip(axes,['dqn','mappo']):
   z=diagnostics[diagnostics.algo==algo].groupby('stage')[['holdout_mae','holdout_zero_mae']].mean().reindex(['initial','refreshed']);x=np.arange(2)
   ax.bar(x-.18,z.holdout_mae,.36,label='hurdle ensemble');ax.bar(x+.18,z.holdout_zero_mae,.36,label='zero-effect prediction');ax.set_xticks(x,['initial holdout','combined holdouts']);ax.set_title(algo.upper());ax.set_ylabel('Mean absolute utility prediction error');ax.legend(fontsize=8)
  fig.suptitle('Internal label holdouts: different contexts; not a causal test of refresh');save(fig,'prediction_errors')
  fig,axes=plt.subplots(1,2,figsize=(11,4.5))
  for ax,algo in zip(axes,['dqn','mappo']):
   for method in METHODS:
    v=train[(train.algo==algo)&(train.method==method)].groupby('episode').delivery_rate.mean().rolling(20,min_periods=1).mean();ax.plot(v.index,100*v,label=method)
   ax.set_title(algo.upper());ax.set_xlabel('Routing episode (300 common warmup precedes adaptation)');ax.set_ylabel('Training delivery %, 20-episode mean');ax.grid(alpha=.2)
  axes[0].legend(ncol=3,fontsize=8);fig.suptitle('Matched adaptation trajectories; eight-seed means, exploration during training');save(fig,'training_curves')
 supported=success[success.joint_success];claim=('No primary comparison met both predeclared requirements. These results do not establish the learned gate as superior to a conservative baseline.' if supported.empty else 'The joint predeclared criterion was met for: '+', '.join(r.algo.upper()+' versus '+r.baseline for r in supported.itertuples())+'. This is limited to the declared constructed distribution and utility/delivery criterion.')
 def table(d):return d.to_markdown(index=False,floatfmt='.3f')
 text=('# Dynamic-recovery gate results\n\n'+claim+'\n\n'
 'This new study follows earlier negative results; it does not replace them. All 8 cases are reported. These are constructed logistics graphs, not operational validation. Filtering at the receiver does not save transmitted bandwidth.\n\n'
 '## Primary decisions\n\n'+table(success)+'\n\n'
 'Success requires corrected utility lower bound >0 and delivery lower bound >−1 percentage point. Delivery noninferiority alone is not superiority. Two-sided Bonferroni correction388, 200,000 crossed paired bootstrap draws,8 independent paired training seeds per algorithm. Historical intervals unchanged.\n\n'
 '## All means\n\n'+table(summary[['algo','case','method','delivery_pct','utility']])+'\n\n'
 '## Gate use and genuine clearances\n\n'+table(summary[summary.method=='LEARN'][['algo','case','genuine_clears','genuine_warning_clears','accept_overrides','reject_overrides']])+'\n\n'
 '## Locked validation settings\n\n```json\n'+json.dumps(locked['settings'],indent=2)+'\n```\n\n'
 '## Reproduce\n\nFrom repository root, `bash setup_local.sh`, then `cd simulator` and `../.venv/bin/python run_recovery_gate_study.py --output out/recovery-gate-reproduction --workers 4`. From root regenerate this report with `.venv/bin/python simulator/report_recovery_gate_study.py --run simulator/out/recovery-gate-reproduction`. The runner refuses to overwrite an existing study directory. Model/checkpoint hashes, paired physical schedules and convoy accounting are checked during reporting.\n\n'
 'Open `recovery_gate_report.pdf` or `index.html` for8 figures. `contrasts.csv` contains all140 intervals, `primary_decisions.csv` the co-required decisions, `summary.csv` every mean, `validation_selection.csv` all selection options, `prediction_diagnostics.csv` internal error, and `fixed_actor_ablation.csv` descriptive swaps. Raw CSV.gz, all80 final neural routing checkpoints, initial/refreshed gate estimators and training/causal labels are in the complete ZIP. No after-test retuning.\n')
 (out/'README.md').write_text(text)
 html='<!doctype html><meta charset="utf-8"><title>AIMRL recovery gate results</title><style>body{font-family:system-ui;max-width:1150px;margin:2em auto;padding:1em}img{width:100%}p{line-height:1.5}</style><h1>Dynamic-recovery gate study</h1><p>'+claim+'</p><p>102,400 final-test episodes;8 paired training seeds per algorithm; all conditions retained. See README and CSV tables for definitions, uncertainty and limitations.</p>'
 for name in images:html+='<h2>'+name.replace('_',' ')+'</h2><img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
 (out/'index.html').write_text(html)
 verification=dict(status='passed',source_hash=fingerprint(),test_episodes=len(df),test_convoys=len(raw),mechanism_episodes=len(mech),training_episodes=len(train),checkpoints=len(locked['checkpoints']),validation_episodes=len(val),new_contrasts=len(contrasts),correction=CORRECTION,bootstrap_draws=DRAWS,primary_joint_successes=len(supported),figures=len(images))
 (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))
if __name__=='__main__':main()
