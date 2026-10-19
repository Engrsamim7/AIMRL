"""Audited original-source reproduction and tabular-only repaired results."""
import argparse,ast,base64,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from original_tabular import source_hashes,SOURCE
from run_original_tabular_study import fingerprint,SEEDS,MODES,WEIGHTS,CASES,select_eta
from report_matched_gate_study import crossed_samples,read
CASE_NAMES=[c['name'] for c in CASES]
PAIRS=[('FRC','ALL'),('FRC','NONE'),('TRAVEL','FRC')]
CORRECTION=436

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/original-tabular-study');ap.add_argument('--output',default='revision/original-tabular-results');args=ap.parse_args();run=Path(args.run);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
 meta=json.loads((run/'pipeline.json').read_text());design=json.loads((run/'design.json').read_text());lock=json.loads((run/'locked_settings.json').read_text())
 assert meta['status']=='completed' and meta['source_hash']==fingerprint() and design['original_sha256']==source_hashes() and lock['status']=='locked_before_test'
 for name,digest in lock['models'].items():assert hashlib.sha256((run/'models'/name).read_bytes()).hexdigest()==digest
 native=pd.read_csv(run/'original_summary.csv');assert len(native)==40
 original=pd.concat([pd.read_csv(p) for p in (run/'original').glob('*_episodes.csv.gz')],ignore_index=True);oraw=pd.concat([pd.read_csv(p) for p in (run/'original').glob('*_convoys.csv.gz')],ignore_index=True)
 assert len(original[original.split=='train'])==7500 and len(original[original.split=='evaluation'])==515 and len(oraw)==3*len(original)
 for seed in SEEDS:
  a=original[(original.method=='IQL')&(original.seed==seed)].sort_values(['split','episode']);b=original[(original.method=='NC')&(original.seed==seed)].sort_values(['split','episode']);assert np.array_equal(a[['dr','surv','cost']].to_numpy(),b[['dr','surv','cost']].to_numpy())
 orig=native.groupby('method').agg(delivery_pct=('dr',lambda x:100*x.mean()),route_prior_score=('surv','mean'),legacy_time_weighted_cost=('cost','mean')).reset_index();orig.to_csv(out/'original_reproduction.csv',index=False)
 anchors={}
 for n in ast.parse((SOURCE/'final_pipeline.py').read_text()).body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PAPER_FINAL' for t in n.targets):anchors=ast.literal_eval(n.value)
 comparison=orig.copy();comparison['presentation_route_score']=[anchors.get({'AMMARL_NOGAT':'AMMARL_NG','MAPPO_LABEL':'MAPPO'}.get(m,m),[np.nan])[0] for m in comparison.method];comparison['matches_at_3_decimals']=comparison.route_prior_score.round(3).eq(comparison.presentation_route_score);comparison.to_csv(out/'presentation_comparison.csv',index=False)
 hist_eval=original[original.split=='evaluation'];gate=hist_eval[hist_eval.method=='AMMARL'];assert gate.hazard_entries.eq(0).all() and gate.hazard_uses.eq(0).all()
 closest=pd.concat([pd.read_csv(p) for p in (run/'closest').glob('*_episodes.csv.gz')],ignore_index=True);craw=pd.concat([pd.read_csv(p) for p in (run/'closest').glob('*_convoys.csv.gz')],ignore_index=True);assert len(closest[closest.split=='train'])==1500 and len(closest[closest.split=='evaluation'])==100
 oe=oraw[(oraw.method=='AMMARL')&(oraw.split=='evaluation')];ce=craw[craw.split=='evaluation'];paired=oe.merge(ce,on=['seed','episode','convoy'],suffixes=('_original','_repaired'),validate='one_to_one');assert len(paired)==300
 paired['delivery_change']=paired.delivered_repaired-paired.delivered_original;paired['score_change']=paired.route_prior_score_repaired-paired.route_prior_score_original;paired['nominal_change']=paired.nominal_cost_repaired-paired.nominal_cost_original;paired['elapsed_change']=paired.elapsed_repaired-paired.elapsed_original
 closest_summary=paired.groupby('seed').agg(delivery_difference_pp=('delivery_change',lambda x:100*x.mean()),route_score_difference=('score_change','mean'),nominal_difference=('nominal_change','mean'),elapsed_difference=('elapsed_change','mean')).reset_index();closest_summary.to_csv(out/'closest_repair_pairs.csv',index=False)
 cc=read(run,'cc2_original');assert len(cc)==2000;cc.groupby('mode').agg(episodes=('episode','size'),delivery_pct=('dr',lambda x:100*x.mean()),route_score=('surv','mean'),legacy_cost=('cost','mean'),reports_fused=('msgs_fused','mean')).to_csv(out/'original_cc2.csv')
 df,raw=read(run,'test_episodes'),read(run,'test_convoys');assert len(df)==43200 and len(raw)==129600
 keys=['weight','sensing','mode','seed','graph','case','episode'];assert not df.duplicated(keys).any() and not raw.duplicated(keys+['convoy']).any();assert (raw.delivered+raw.failed+raw.censored).eq(1).all()
 rebuilt=raw.groupby(keys).agg(delivery_rate=('delivered','mean'),nominal_all_mean=('nominal_cost','mean'),elapsed_mean=('elapsed','mean'),route_score_all=('route_prior_score','mean')).sort_index();recorded=df.set_index(keys).sort_index();assert rebuilt.index.equals(recorded.index)
 for col in rebuilt:assert np.allclose(rebuilt[col],recorded[col],rtol=0,atol=1e-9),col
 assert np.allclose(raw.elapsed,raw.travel+raw.wait+raw.dispatch,rtol=0,atol=1e-8)
 assert raw.groupby(['weight','sensing','seed','graph','case','episode','convoy']).target.nunique().eq(1).all()
 assert raw.blocked_enc.ge(0).all() and np.allclose(raw.blocked_enc,np.rint(raw.blocked_enc))
 training=pd.concat([pd.read_csv(p) for p in (run/'training').glob('*.csv.gz')],ignore_index=True);assert len(training)==24000
 validation=read(run,'validation');assert len(validation)==4320 and select_eta(validation)==lock['travel_eta']
 df['scope']=np.where(df.graph.eq(0),'original-graph','fresh-attributes');summary=df.groupby(['scope','weight','sensing','mode']).agg(episodes=('episode','size'),delivery_pct=('delivery_rate',lambda x:100*x.mean()),route_score=('route_score_all','mean'),nominal=('nominal_all_mean','mean'),elapsed=('elapsed_mean','mean'),messages_sent=('messages_sent','mean'),hazard_score_applications=('hazard_uses','mean')).reset_index();summary.to_csv(out/'repaired_summary.csv',index=False)
 df.groupby(['scope','weight','sensing','case','mode']).agg(delivery_pct=('delivery_rate',lambda x:100*x.mean()),route_score=('route_score_all','mean'),nominal=('nominal_all_mean','mean'),elapsed=('elapsed_mean','mean'),hazard_uses=('hazard_uses','mean')).to_csv(out/'all_conditions.csv')
 records=[]
 for wi,w in enumerate(WEIGHTS):
  for si,sensing in enumerate(['uniform','mixed']):
   for qi,(scope,graphs) in enumerate([('original-graph',[0]),('fresh-attributes',list(range(1,9)))]):
    index=pd.MultiIndex.from_product([graphs,SEEDS,CASE_NAMES,range(10)],names=['graph','seed','case','episode']);arrays=[]
    for endpoint,col,scale in [('delivery','delivery_rate',100.),('route_score','route_score_all',1.)]:
     z=df[(df.weight==w)&(df.sensing==sensing)].pivot(index=index.names,columns='mode',values=col).reindex(index);assert not z.isna().any().any()
     arrays.extend([scale*(z[a]-z[b]).to_numpy().reshape(len(graphs),5,6,10) for a,b in PAIRS])
    values=np.stack(arrays,axis=-1);samples=crossed_samples(values,seed=3011+wi*10+si*2+qi,draws=200000).mean(axis=1);lo,hi=np.quantile(samples,[.05/(2*CORRECTION),1-.05/(2*CORRECTION)],axis=0)
    for ei,endpoint in enumerate(['delivery','route_score']):
     for pi,(a,b) in enumerate(PAIRS):
      k=ei*3+pi;records.append(dict(scope=scope,weight=w,sensing=sensing,endpoint=endpoint,method=a,baseline=b,difference=float(values[:,:,:,:,k].mean()),lower=lo[k],upper=hi[k]))
 contrasts=pd.DataFrame(records);assert len(contrasts)==48;contrasts['benefit_supported']=contrasts.lower>0;contrasts['harm_supported']=contrasts.upper<0;contrasts.to_csv(out/'contrasts.csv',index=False)
 packets=df.groupby(['weight','sensing','mode']).agg(episodes=('episode','size'),mean_sent=('messages_sent','mean'),mean_delivered=('messages_delivered','mean'),score_applications=('hazard_uses','mean'),gate_queries=('gate_queries','mean')).reset_index();packets.to_csv(out/'communication.csv',index=False)
 figures=[];plt.rcParams.update({'font.size':10,'figure.dpi':140})
 with PdfPages(out/'original_tabular_report.pdf') as pdf:
  def save(fig,name):
   fig.tight_layout();pdf.savefig(fig);fig.savefig(out/(name+'.png'),dpi=150);fig.savefig(out/(name+'.pdf'));figures.append(name);plt.close(fig)
  methods=['B1','B2','B3','IQL','NC','AMMARL','AMMARL_NOGAT','MAPPO_LABEL'];z=orig.set_index('method').reindex(methods);fig,axes=plt.subplots(1,2,figsize=(12,4.6))
  axes[0].bar(range(8),z.route_prior_score);axes[0].set_ylabel('Mean route-prior score (not survival probability)');axes[1].bar(range(8),z.delivery_pct);axes[1].set_ylabel('Actual delivery (%)');axes[1].set_ylim(0,105)
  for ax in axes:ax.set_xticks(range(8),methods,rotation=40,ha='right',fontsize=8)
  fig.suptitle('Unmodified submitted source: original M4 protocol\nAMMARL hazard-buffer entries and hazard uses =0',fontsize=11);save(fig,'original_reproduction')
  fig,ax=plt.subplots(figsize=(11,4.6));z=comparison.set_index('method').reindex(methods);x=np.arange(8);ax.plot(x,z.presentation_route_score,'o',label='fixed presentation value');ax.plot(x,z.route_prior_score,'x',markersize=9,label='executed original source');ax.set_xticks(x,methods,rotation=35,ha='right');ax.set_ylabel('Route-prior score');ax.legend();ax.set_title('Which presentation scores reproduce?\nMatching a number does not establish a communication-gate effect');save(fig,'presentation_comparison')
  fig,axes=plt.subplots(1,3,figsize=(12,4.2));eoriginal=oe;erepaired=ce
  for ax,col,title,scale in zip(axes,['delivered','route_prior_score','nominal_cost'],['Delivery (%)','Route-prior score','Realized nominal path cost'],[100,1,1]):
   values=[scale*eoriginal[col].mean(),scale*erepaired[col].mean()];ax.bar([0,1],values);ax.set_xticks([0,1],['original','closest repair']);ax.set_title(title)
   for i,v in enumerate(values):ax.text(i,v,f'{v:.4f}',ha='center',va='bottom')
  fig.suptitle('Same original seeds, curriculum, code coefficients and evaluation epsilon 0.05');save(fig,'closest_repair')
  fig,axes=plt.subplots(1,2,figsize=(13,7),sharey=True)
  for ax,scope in zip(axes,['original-graph','fresh-attributes']):
   z=contrasts[(contrasts.scope==scope)&(contrasts.endpoint=='route_score')].copy();labels=[f'{r.weight}/{r.sensing}: {r.method}-{r.baseline}' for r in z.itertuples()];y=np.arange(len(z));ax.errorbar(z.difference,y,xerr=np.vstack([z.difference-z.lower,z.upper-z.difference]),fmt='o',capsize=3);ax.set_yticks(y,labels,fontsize=8);ax.invert_yaxis();ax.axvline(0,color='black',lw=1);ax.set_title(scope);ax.set_xlabel('Route-prior score difference');ax.grid(axis='x',alpha=.2)
  fig.suptitle('Matched tabular refinements: corrected intervals (436-comparison factor)\nAll delivery differences and bounds are in contrasts.csv; no probability interpretation',fontsize=11);save(fig,'fixed_gate_contrasts')
  fig,axes=plt.subplots(2,2,figsize=(12,8))
  for wi,w in enumerate(WEIGHTS):
   for qi,scope in enumerate(['original-graph','fresh-attributes']):
    ax=axes[wi,qi];z=df[(df.weight==w)&(df.sensing=='mixed')&(df.scope==scope)].groupby(['case','mode']).route_score_all.mean().unstack().reindex(CASE_NAMES)
    for mode in MODES:ax.plot(range(6),z[mode],marker='o',label=mode)
    ax.set_xticks(range(6),CASE_NAMES,rotation=40,ha='right',fontsize=8);ax.set_title(w+' / mixed / '+scope);ax.set_ylabel('Route-prior score');ax.legend(ncol=2,fontsize=8)
  fig.suptitle('Every held-out regime, with the mixed-sensing refinement labeled');save(fig,'all_conditions')
  fig,axes=plt.subplots(1,2,figsize=(12,4.5))
  for ax,sensing in zip(axes,['uniform','mixed']):
   z=packets[packets.sensing==sensing];x=np.arange(len(z));ax.bar(x,z.score_applications);ax.set_xticks(x,[r.weight+'/'+r.mode for r in z.itertuples()],rotation=45,ha='right',fontsize=8);ax.set_title(sensing);ax.set_ylabel('Peer-hazard score applications per episode')
  fig.suptitle('Communication activity is distinct from benefit\nApplications can reuse a report; these are not unique packets or bandwidth savings',fontsize=11);save(fig,'communication_activity')
  fig,axes=plt.subplots(1,2,figsize=(12,4.5))
  for m in ['IQL','NC','AMMARL','AMMARL_NOGAT','MAPPO_LABEL']:
   z=original[(original.method==m)&(original.split=='train')].groupby('episode')[['surv','dr']].mean().rolling(20,min_periods=1).mean();axes[0].plot(z.index,z.surv,label=m);axes[1].plot(z.index,100*z.dr,label=m)
  axes[0].set_ylabel('Delivered-only route-prior score');axes[1].set_ylabel('Actual training delivery (%)')
  for ax in axes:ax.set_xlabel('Original training episode');ax.axvline(100,color='gray',ls='--');ax.axvline(200,color='gray',ls='--');ax.grid(alpha=.2)
  axes[0].legend(fontsize=8);fig.suptitle('Actual original training records, five-seed mean /20-episode smoothing\nNot generated sigmoid curves; no convergence guarantee');save(fig,'original_learning')
  fig,axes=plt.subplots(1,2,figsize=(10,4));z=cc.groupby('mode')[['surv','dr']].mean().reindex(['NC','AMMARL']);axes[0].bar([0,1],z.surv);axes[0].set_ylabel('Route-prior score');axes[1].bar([0,1],100*z.dr);axes[1].set_ylabel('Actual delivery (%)');axes[1].set_ylim(0,105)
  for ax in axes:ax.set_xticks([0,1],['NC path','AMMARL path'])
  fig.suptitle('Original CC2: two unique scripted/Dijkstra communication paths\nNot an independently trained tabular-FRC or multi-algorithm comparison',fontsize=11);save(fig,'original_cc2')
 text=('# Original tabular AMMARL-PI: reproduced and repaired\n\n'
 'The study returns to hub-indexed independent Q-learning and a fixed FRC gate. Neural/learned-gate extensions are excluded. Source-file hashes are unchanged.\n\n'
 '## Executed original-source results\n\n'+orig.to_markdown(index=False,floatfmt='.6f')+'\n\n'
 'AMMARL 0.876374 and IQL 0.857023 reproduce the rounded 0.876/0.857 presentation scores, but both deliver 100% and original M4 has zero hazard-buffer entries/uses. The original ungated result does not reproduce 0.851; IQL and NC are identical paths. Matching some numbers cannot attribute a communication effect or authenticate all presentation constants. Costs above are the original cost-times-travel-time metric, not nominal sums.\n\n'
 '## Closest repaired pairs\n\n'+closest_summary.to_markdown(index=False,floatfmt='.6f')+'\n\n'
 'Same original seed ranges/300-episode curriculum/scoring/evaluation epsilon 0.05. This is a bundle-of-repairs comparison, not a single-patch causal effect. Controlled refinements below use fresh independent training streams and greedy evaluation, so cross-layer differences must not be attributed solely to bug fixes.\n\n'
 '## Matched tabular refinements\n\n'+summary.to_markdown(index=False,floatfmt='.6f')+'\n\n'
 'Actual delivery is separated from route-prior score, which is not survival probability. The inherited model does not simulate attack-induced killing. Original graph scope conditions on graph 42; fresh graphs change attributes within the same small topology family. Mixed sensing, scoring specification and traversal-scaled freshness are labeled scientific refinements. No general superiority or convergence claim follows.\n\n'
 '## Reproduce\n\nUse `bash setup_local.sh`, then from simulator run `../.venv/bin/python run_original_tabular_study.py --output out/original-tabular-reproduction --workers 4`. From root run `.venv/bin/python simulator/report_original_tabular_study.py --run simulator/out/original-tabular-reproduction`. Use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache`. A fresh study directory is required.\n\n'
 'Open original_tabular_report.pdf or index.html for eight figures. original_reproduction.csv and presentation_comparison.csv distinguish source outcomes from fixed anchors; closest_repair_pairs.csv gives matched repairs; repaired_summary.csv/all_conditions.csv retain every refinement/regime; contrasts.csv holds all 48 corrected intervals; communication.csv separates activity. Raw original/repaired training, models, validation, test outcomes and all 17 uploaded source files are in the ZIP. The protocol and findings describe unresolved reviewer/manuscript issues.\n')
 (out/'README.md').write_text(text);html='<!doctype html><meta charset="utf-8"><title>Original tabular AMMARL reproduction</title><style>body{font-family:system-ui;max-width:1150px;margin:2em auto;padding:1em}img{width:100%}</style><h1>Original tabular AMMARL: reproduction and repairs</h1><p>Original 0.876/0.857 route scores reproduced; these are not delivery probabilities. Original M4 hazard uses=0. See findings and full tables.</p>'
 for name in figures:html+='<h2>'+name.replace('_',' ')+'</h2><img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
 (out/'index.html').write_text(html)
 verification=dict(status='passed',source_hash=fingerprint(),report_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),submitted_hashes_preserved=True,original_training=7500,original_M4_evaluation=515,original_CC2_unique=2000,closest_repair_training=1500,closest_repair_evaluation=100,controlled_tabular_training=24000,validation=4320,test_episodes=len(df),test_convoys=len(raw),contrasts=len(contrasts),correction=CORRECTION,bootstrap_draws=200000,figures=len(figures),original_M4_AMMARL_hazard_entries=int(gate.hazard_entries.sum()),original_M4_AMMARL_hazard_uses=int(gate.hazard_uses.sum()))
 (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n');print(json.dumps(verification))
if __name__=='__main__':main()
