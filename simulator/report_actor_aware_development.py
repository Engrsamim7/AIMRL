"""Report development evidence without relabeling it as confirmation."""
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
from actor_aware_gate import FEATURES,LeafForest
from recovery_gate import TRAIN
from run_actor_aware_development import fingerprint,MODELS,METHODS,SEEDS,select_settings
from report_matched_gate_study import read,audit,crossed_samples
CASES=[c.name for c in TRAIN]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/actor-aware-development');ap.add_argument('--parent',default='simulator/out/recovery-gate-study');ap.add_argument('--output',default='revision/actor-aware-development-results');args=ap.parse_args()
 run,parent,out=Path(args.run),Path(args.parent),Path(args.output);out.mkdir(parents=True,exist_ok=True)
 meta=json.loads((run/'pipeline.json').read_text());lock=json.loads((run/'locked_settings.json').read_text());assert meta['status']=='completed' and meta['source_hash']==fingerprint() and lock['status']=='locked_before_audit' and lock['source_hash']==fingerprint()
 for name,d in lock['models'].items():assert hashlib.sha256((run/'models'/name).read_bytes()).hexdigest()==d
 for name,d in lock['routing_models'].items():assert hashlib.sha256((parent/'models'/name).read_bytes()).hexdigest()==d
 df,raw=read(run,'audit_episodes'),read(run,'audit_convoys');audit(df,raw,6144,METHODS);assert df.overrides.le(1).all()
 keys=['algo','seed','graph','case','episode','method'];u=raw.assign(u=40*raw.delivered-40*raw.destroyed-40*raw.censored-raw.elapsed).groupby(keys).u.mean().sort_index();v=df.set_index(keys).utility_mean.sort_index();assert u.index.equals(v.index) and np.allclose(u,v,rtol=0,atol=1e-10)
 cal=read(run,'calibration');assert len(cal)==39936;settings,selection=select_settings(cal);assert settings==lock['settings'];pd.DataFrame(selection).to_csv(out/'selection.csv',index=False)
 fitting=read(run,'fit_manifest');assert len(fitting)==32 and fitting.fit_examples.ge(24).all()
 summary=df.groupby(['algo','case','method']).agg(episodes=('episode','size'),delivery_pct=('delivery_rate',lambda x:100*x.mean()),utility=('utility_mean','mean'),overrides=('overrides','sum'),accept_overrides=('accept_overrides','sum'),reject_overrides=('reject_overrides','sum')).reset_index();summary.to_csv(out/'summary.csv',index=False)
 pooled=df.groupby(['algo','method']).agg(delivery_pct=('delivery_rate',lambda x:100*x.mean()),utility=('utility_mean','mean'),overrides=('overrides','sum'),accept_overrides=('accept_overrides','sum'),reject_overrides=('reject_overrides','sum')).reset_index();pooled.to_csv(out/'pooled_means.csv',index=False)
 records=[];seed_effects=[]
 for ai,algo in enumerate(['dqn','mappo']):
  index=pd.MultiIndex.from_product([range(8),SEEDS,CASES],names=['graph','seed','case']);arrays=[]
  for endpoint in ['utility','delivery']:
   z=df[df.algo==algo].pivot(index=index.names,columns='method',values='utility_mean' if endpoint=='utility' else 'delivery_rate').reindex(index);assert not z.isna().any().any();scale=1 if endpoint=='utility' else 100
   for baseline in ['SAFE','TREE_BASE']:arrays.append(scale*(z.ACTOR_AWARE-z[baseline]).to_numpy().reshape(8,8,8,1))
  a=np.stack(arrays,axis=-1);samples=crossed_samples(a,seed=9931+ai,draws=20000).mean(axis=1);lo,hi=np.quantile(samples,[.025,.975],axis=0)
  for ei,endpoint in enumerate(['utility','delivery']):
   for bi,baseline in enumerate(['SAFE','TREE_BASE']):
    q=2*ei+bi;records.append(dict(algo=algo,endpoint=endpoint,baseline=baseline,difference=a[:,:,:,:,q].mean(),exploratory_lower=lo[q],exploratory_upper=hi[q],interpretation='development only; no corrected superiority claim'))
    for si,seed in enumerate(SEEDS):seed_effects.append(dict(algo=algo,seed=seed,endpoint=endpoint,baseline=baseline,difference=a[:,si,:,:,q].mean()))
 contrasts=pd.DataFrame(records);contrasts.to_csv(out/'exploratory_contrasts.csv',index=False);pd.DataFrame(seed_effects).to_csv(out/'seed_effects.csv',index=False)
 labels=[];factual=[];quality=[];proposal=[]
 for algo in ['dqn','mappo']:
  for seed in SEEDS:
   data=pd.read_csv(run/'labels'/f'{algo}_s{seed}.csv.gz');labels.append(data);fact=pd.read_csv(run/'factual'/f'{algo}_s{seed}.csv.gz');factual.append(fact)
   z=data[data.split=='audit'].copy();x=z[FEATURES].to_numpy();relevant=z.reachable.gt(.5)&z.probe_action_change.gt(.5)
   for method in MODELS:
    model=LeafForest.load(run/'models'/f'{algo}_s{seed}_{method}.npz');pred=np.array([model.predict(row) for row in x]);z['prediction']=pred[:,0]
    for name,mask in [('all_sampled',np.ones(len(z),bool)),('eligible_action_change',relevant),('eligible_consequential',relevant & z.flip_utility.abs().gt(.1)),('no_immediate_action_change',~relevant)]:
     h=z[mask]
     if len(h):quality.append(dict(algo=algo,seed=seed,method=method,stratum=name,labels=len(h),mae=float((h.prediction-h.flip_utility).abs().mean()),zero_mae=float(h.flip_utility.abs().mean()),mse=float(((h.prediction-h.flip_utility)**2).mean()),zero_mse=float((h.flip_utility**2).mean())))
    kw=settings[algo][method];eligible=np.zeros(len(z),bool) if kw.get('abstain') else relevant.to_numpy()&(pred[:,0]-kw['beta']*pred[:,1]>kw['margin'])&(pred[:,2]-kw['beta']*pred[:,3]>=-kw['delivery_tolerance'])
    selected=z[eligible];proposal.append(dict(algo=algo,seed=seed,method=method,proposed_labels=len(selected),utility_help=int(selected.flip_utility.gt(0).sum()),utility_harm=int(selected.flip_utility.lt(0).sum()),delivery_help=int(selected.flip_delivery.gt(0).sum()),delivery_harm=int(selected.flip_delivery.lt(0).sum()),mean_flip_utility=float(selected.flip_utility.mean()) if len(selected) else None))
 labels=pd.concat(labels,ignore_index=True);factual=pd.concat(factual,ignore_index=True);assert len(factual)==6144
 # All baseline factual audit outcomes must reproduce evaluation SAFE.
 z=factual[factual.split=='audit'];safe=df[df.method=='SAFE'];joined=z.merge(safe,on=['algo','seed','graph','case','episode'],suffixes=('_factual','_evaluation'),validate='one_to_one');assert len(joined)==1024
 assert np.allclose(joined.utility_mean_factual,joined.utility_mean_evaluation) and np.array_equal(joined.n_delivered_factual,joined.n_delivered_evaluation)
 pd.DataFrame(quality).to_csv(out/'prediction_quality.csv',index=False);pd.DataFrame(proposal).to_csv(out/'sampled_proposal_quality.csv',index=False)
 opportunity=factual.groupby(['algo','split','case']).agg(episodes=('episode','size'),eligible=('eligible','sum'),action_candidates=('action_candidates','sum'),sampled=('sampled','sum'),mean_sampled_oracle_gain=('oracle_sampled_gain','mean'),oracle_delivery_gain_pp=('oracle_delivery_gain',lambda x:100*x.mean()),positive_oracle_episodes=('oracle_sampled_gain',lambda x:int((x>0).sum()))).reset_index();opportunity.to_csv(out/'sampled_opportunity.csv',index=False)
 relevant=labels[labels.reachable.gt(.5)&labels.probe_action_change.gt(.5)].copy();relevant['positive_gain']=relevant.flip_utility.clip(lower=0)
 cols=['algo','seed','split','graph','case','episode'];eligible_best=relevant.groupby(cols).positive_gain.max().rename('eligible_sampled_gain').reset_index()
 opportunities=factual.merge(eligible_best,on=cols,how='left',validate='one_to_one');opportunities['eligible_sampled_gain']=opportunities.eligible_sampled_gain.fillna(0.)
 opportunities.groupby(['algo','split','case']).agg(episodes=('episode','size'),all_sampled_gain=('oracle_sampled_gain','mean'),eligible_action_sampled_gain=('eligible_sampled_gain','mean')).to_csv(out/'opportunity_scope.csv')
 label_summary=labels.assign(relevant=labels.reachable.gt(.5)&labels.probe_action_change.gt(.5),consequential=labels.flip_utility.abs().gt(.1),positive=labels.flip_utility.gt(0),negative=labels.flip_utility.lt(0)).groupby(['algo','split']).agg(labels=('id','size'),relevant=('relevant','sum'),consequential=('consequential','sum'),positive=('positive','sum'),negative=('negative','sum')).reset_index();label_summary.to_csv(out/'label_summary.csv',index=False)
 images=[];plt.rcParams.update({'font.size':10,'figure.dpi':140})
 with PdfPages(out/'actor_aware_development.pdf') as pdf:
  def save(fig,name):
   fig.tight_layout();pdf.savefig(fig);fig.savefig(out/(name+'.png'),dpi=150);fig.savefig(out/(name+'.pdf'));images.append(name);plt.close(fig)
  for endpoint,title,unit in [('utility','Fleet utility: actor-aware minus comparator','utility units per convoy'),('delivery','Fleet delivery: actor-aware minus comparator','percentage points')]:
   fig,axes=plt.subplots(1,2,figsize=(11,4.5),sharex=True)
   for ax,algo in zip(axes,['dqn','mappo']):
    z=contrasts[(contrasts.algo==algo)&(contrasts.endpoint==endpoint)].set_index('baseline').reindex(['SAFE','TREE_BASE']);y=np.arange(2)
    ax.errorbar(z.difference,y,xerr=np.vstack([z.difference-z.exploratory_lower,z.exploratory_upper-z.difference]),fmt='o',capsize=4);ax.axvline(0,color='black',lw=1);ax.set_yticks(y,['SAFE','same-tree old features']);ax.invert_yaxis();ax.set_title(algo.upper());ax.set_xlabel(unit);ax.grid(axis='x',alpha=.2)
   fig.suptitle(title+'\nExploratory95% intervals; existing frozen actors; NOT confirmation',fontsize=11);save(fig,'paired_'+endpoint)
  fig,axes=plt.subplots(1,2,figsize=(12,4.8))
  for ax,algo in zip(axes,['dqn','mappo']):
   z=opportunities[(opportunities.algo==algo)&(opportunities.split=='audit')].groupby('case')[['oracle_sampled_gain','eligible_sampled_gain']].mean().reindex(CASES);x=np.arange(8);ax.bar(x-.18,z.oracle_sampled_gain,.36,label='all sampled');ax.bar(x+.18,z.eligible_sampled_gain,.36,label='eligible actor-changing');ax.set_xticks(x,CASES,rotation=55,ha='right',fontsize=8);ax.set_title(algo.upper());ax.set_ylabel('Best sampled single-flip utility gain per episode');ax.legend(fontsize=8)
  fig.suptitle('Privileged hindsight opportunity; selected packets only\nNot a deployed gate, global bound or sum of effects',fontsize=11);save(fig,'sampled_opportunity')
  q=pd.DataFrame(quality);fig,axes=plt.subplots(1,2,figsize=(11,4.7))
  for ax,algo in zip(axes,['dqn','mappo']):
   z=q[(q.algo==algo)&(q.stratum=='eligible_action_change')].groupby('method')[['mae','zero_mae']].mean().reindex(MODELS);x=np.arange(2);ax.bar(x-.18,z.mae,.36,label='model');ax.bar(x+.18,z.zero_mae,.36,label='predict zero flip value');ax.set_xticks(x,['old features + trees','actor-aware + trees']);ax.set_title(algo.upper());ax.set_ylabel('Mean absolute fleet-utility error');ax.legend(fontsize=8)
  fig.suptitle('Audit label error on eligible action-changing candidates\nEight existing actor-seed means; deployment outcomes assessed separately',fontsize=11);save(fig,'prediction_quality')
  fig,axes=plt.subplots(1,2,figsize=(12,5))
  for ax,algo in zip(axes,['dqn','mappo']):
   z=summary[(summary.algo==algo)&summary.method.isin(MODELS)];x=np.arange(8)
   for i,method in enumerate(MODELS):
    v=z[z.method==method].set_index('case').reindex(CASES);ax.bar(x+(i-.5)*.35,v.overrides/v.episodes,.35,label=method)
   ax.set_xticks(x,CASES,rotation=55,ha='right',fontsize=8);ax.set_title(algo.upper());ax.set_ylabel('Overrides per fleet episode (maximum1)');ax.legend(fontsize=8)
  fig.suptitle('Actual deployment authority used, including abstention');save(fig,'authority')
  fig,axes=plt.subplots(1,2,figsize=(12,5))
  for ax,algo in zip(axes,['dqn','mappo']):
   z=summary[summary.algo==algo].pivot(index='case',columns='method',values='utility').reindex(CASES)
   for method in ['KEEP','AGE','TREE_BASE','ACTOR_AWARE']:ax.plot(range(8),z[method]-z.SAFE,marker='o',label=method)
   ax.axhline(0,color='black',lw=1);ax.set_xticks(range(8),CASES,rotation=55,ha='right',fontsize=8);ax.set_title(algo.upper());ax.set_ylabel('Fleet utility difference versus same-actor SAFE');ax.legend(fontsize=8)
  fig.suptitle('Every development condition retained; means, not superiority claims');save(fig,'all_conditions')
 text=('# Actor-aware development results\n\n'
 'This is an algorithm-development audit on new training-distribution layouts and tapes. It uses16 existing frozen SAFE-trained routing actors, not new routing-training seeds or a matched-retraining confirmation. The prior null recovery study is unchanged.\n\n'
 '## Paired exploratory differences\n\n'+contrasts.to_markdown(index=False,floatfmt='.4f')+'\n\n'
 'Intervals are exploratory95% crossed seed/layout bootstrap intervals,20,000 draws; no multiplicity-adjusted superiority conclusion is made. All methods share the same frozen routing actor per seed. The old-feature forest has the same fitting data, estimator family, override rule/budget and setting grid as the actor-aware forest.\n\n'
 '## All pooled means\n\n'+pooled.to_markdown(index=False,floatfmt='.4f')+'\n\n'
 '## Labels and opportunities\n\n'+label_summary.to_markdown(index=False)+'\n\n'
 'The sampled hindsight reference selects at most one privileged best flip from sampled packets per episode. It is not deployable or a global bound. Its delivery tradeoff is in sampled_opportunity.csv. Zero immediate action change does not prove zero future effect. Tree dispersion is heuristic, not calibrated safety.\n\n'
 '## Locked settings\n\n```json\n'+json.dumps(settings,indent=2)+'\n```\n\n'
 '## Reproduce\n\nRun `bash setup_local.sh`, then `.venv/bin/python -m pip install -r requirements-actor-aware.txt`. Use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache`. From `simulator/`, run `../.venv/bin/python run_actor_aware_development.py --output out/actor-aware-reproduction --workers 4` (parent recovery SAFE checkpoints must be available). From root regenerate with `.venv/bin/python simulator/report_actor_aware_development.py --run simulator/out/actor-aware-reproduction`. Existing study directories are never overwritten.\n\n'
 'Open actor_aware_development.pdf or index.html for six figures. All tables, selected paired branch labels, factual baseline outcomes, estimator arrays and locked settings accompany the full source ZIP. No new general or bounded superiority claim follows from these exploratory comparisons. See ../actor-aware-development-findings.md for the research decision.\n')
 (out/'README.md').write_text(text);html='<!doctype html><meta charset="utf-8"><title>AIMRL actor-aware development</title><style>body{font-family:system-ui;max-width:1150px;margin:2em auto;padding:1em}img{width:100%}</style><h1>Actor-aware development audit</h1><p>Existing frozen routing actors. Development evidence only; no confirmed superiority claim. See README and findings.</p>'
 for name in images:html+='<h2>'+name.replace('_',' ')+'</h2><img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
 (out/'index.html').write_text(html)
 verification=dict(status='passed',source_hash=fingerprint(),report_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),existing_routing_actors=16,new_routing_training_seeds=0,estimators=32,factual_episodes=len(factual),labels=len(labels),audit_episodes=len(df),audit_convoys=len(raw),calibration_episodes=len(cal),figures=len(images),exploratory_contrasts=len(contrasts),claim='development only; no superiority established')
 (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))
if __name__=='__main__':main()
