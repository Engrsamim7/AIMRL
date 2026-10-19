"""Delivery-only learned-routing results, exact causal labels and gate effects."""
import argparse,ast,base64,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from run_delivery_learning import fingerprint,SEEDS,TEST,SETTINGS,model_for
from delivery_learning import FEATURES,GATE_FEATURES,DeliveryNetwork
from timed_network import graph_for

METHODS=['NONE','ALL','FIXED_RX','KEEP_ONE','KEEP','LEARN','PLANNER_WARN','PLANNER_RAW']
PRIMARY=['ALL','KEEP','PLANNER_RAW']


def paired_inference(df):
    index=pd.MultiIndex.from_product([range(6),range(8),[c.name for c in TEST],range(6)],names=['graph','seed','case','episode'])
    d=df[df.seed>=0].pivot(index=index.names,columns='method',values='on_time').reindex(index)
    planner=df[df.method=='PLANNER_RAW'].set_index(['graph','case','episode']).on_time
    d['PLANNER_RAW']=[planner.loc[(g,c,e)] for g,s,c,e in index]
    assert not d[['LEARN']+PRIMARY].isna().any().any()
    values=np.stack([(d.LEARN-d[m]).to_numpy().reshape(6,8,12,6) for m in PRIMARY],axis=-1)
    rng=np.random.default_rng(859902);samples=[]
    for _ in range(80):
        n=250;g=rng.integers(6,size=(n,6));s=rng.integers(8,size=(n,8));e=rng.integers(6,size=(n,6,12,6))
        z=values[g[:,:,None,None,None],s[:,None,:,None,None],np.arange(12)[None,None,None,:,None],e[:,:,None,:,:],:]
        samples.append(z.mean(axis=(1,2,3,4)))
    samples=np.concatenate(samples);lo,hi=np.quantile(samples,[.05/(2*3),1-.05/(2*3)],axis=0)
    return pd.DataFrame([dict(method='LEARN',baseline=m,difference_pp=100*values[...,i].mean(),lower_pp=100*lo[i],upper_pp=100*hi[i],corrected_positive=bool(lo[i]>0),mean_reaches_1pp=bool(values[...,i].mean()>=.01),draws=20000,correction=3) for i,m in enumerate(PRIMARY)])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/delivery-learning-v3');ap.add_argument('--output',default='revision/delivery-learning-results');args=ap.parse_args();run=Path(args.run);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((run/'pipeline.json').read_text());lock=json.loads((run/'locked_settings.json').read_text());assert meta['status']=='completed' and meta['source_hash']==fingerprint()==lock['source_hash']
    for key,folder in [('actors','actors'),('gates','gates')]:
        for name,h in lock[key].items():assert hashlib.sha256((run/folder/name).read_bytes()).hexdigest()==h
    selected=[]
    for p in sorted((run/'actors').glob('*.json')):
        row=json.loads(p.read_text());assert row['actor']['features']==FEATURES and row['source_hash']==fingerprint()
        selected.append(dict(seed=row['seed'],selected_episode=row['selected_episode'],validation_on_time=row['validation_on_time'],optimizer_updates=row['actor']['updates']))
    selected=pd.DataFrame(selected);assert len(selected)==8;selected.to_csv(out/'selected_routing_models.csv',index=False)
    training=pd.concat([pd.read_csv(run/'training'/f's{s}.csv.gz') for s in SEEDS]);assert len(training)==4000
    validations=pd.concat([pd.read_csv(run/'training'/f's{s}_validation.csv') for s in SEEDS]);validations.to_csv(out/'routing_validation.csv',index=False)
    for r in selected.itertuples(index=False):
        scores=validations[validations.seed==r.seed].groupby('checkpoint').on_time.mean().reset_index().sort_values(['on_time','checkpoint'],ascending=[False,False])
        assert int(scores.iloc[0].checkpoint)==r.selected_episode and np.isclose(scores.iloc[0].on_time,r.validation_on_time)
        candidate=json.loads((run/'actor_candidates'/f's{r.seed}_ep{r.selected_episode}.json').read_text())
        assert candidate['actor']==json.loads((run/'actors'/f's{r.seed}.json').read_text())['actor']
    val=pd.read_csv(run/'validation.csv.gz');assert len(val)==960 and not val.duplicated(['seed','graph','case','episode','setting']).any()
    ranking=val.groupby('setting').agg(on_time=('on_time','mean'),rejections=('rejections','mean')).reset_index().sort_values(['on_time','rejections','setting'],ascending=[False,True,True]);assert int(ranking.iloc[0].setting)==lock['setting_id'];ranking.to_csv(out/'gate_validation_selection.csv',index=False)
    labels=pd.concat([pd.read_csv(run/'labels'/f's{s}.csv.gz') for s in SEEDS],ignore_index=True)
    attempts=pd.concat([pd.read_csv(run/'labels'/f's{s}_episodes.csv.gz') for s in SEEDS]);assert len(attempts)==3200
    for r in labels.itertuples(index=False):
        x=json.loads(r.features);a=json.loads(r.admit_convoys);b=json.loads(r.reject_convoys);assert len(x)==len(GATE_FEATURES) and len(a)==len(b)==8
        assert np.isclose(r.admit_on_time,np.mean([c['on_time'] for c in a])) and np.isclose(r.reject_on_time,np.mean([c['on_time'] for c in b]))
        assert np.isclose(r.delta,r.admit_on_time-r.reject_on_time) and np.isclose(8*r.delta,round(8*r.delta))
        for convoy in a+b:assert np.isclose(convoy['elapsed'],sum(convoy[k] for k in ['travel','service','wait','inspection','hold']),atol=1e-7)
    label_summary=labels.groupby(['seed','control']).agg(labels=('delta','size'),admit_harms=('delta',lambda x:(x<0).sum()),no_delivery_effect=('delta',lambda x:(x==0).sum()),admit_helps=('delta',lambda x:(x>0).sum()),mean_delta=('delta','mean')).reset_index();label_summary.to_csv(out/'causal_label_summary.csv',index=False)
    attempts.groupby('seed').agg(attempts=('episode','size'),captured=('captured','sum'),candidate_calls=('candidate_count','sum')).to_csv(out/'label_opportunities.csv')
    # A hindsight diagnostic over sampled training interventions only. This is
    # neither a deployable policy nor an upper bound over unsampled packets.
    opportunities=[]
    for s in SEEDS:
        best=(-labels[(labels.seed==s)&(~labels.control)].groupby('episode').delta.min()).clip(lower=0)
        opportunities.append(dict(seed=s,attempted_episodes=int((attempts.seed==s).sum()),episodes_with_sampled_helpful_rejection=int(best.gt(0).sum()),sampled_hindsight_gain_pp=100*best.sum()/(attempts.seed==s).sum()))
    pd.DataFrame(opportunities).to_csv(out/'sampled_training_opportunity.csv',index=False)
    df=pd.read_csv(run/'episodes.csv.gz');raw=pd.read_csv(run/'convoys.csv.gz');keys=['seed','graph','size','case','episode','method']
    assert len(df)==21600 and len(raw)==172800 and not df.duplicated(keys).any() and not raw.duplicated(keys+['convoy']).any()
    assert df.groupby(['graph','case','episode']).schedule_hash.nunique().eq(1).all()
    graphs={gi:graph_for(850010+gi,size) for gi,size in enumerate([19,19,51,51,131,131])};environments=[];departures={}
    graph_records={str(gi):dict(seed=850010+gi,n=g.n,depot=g.depot,targets=g.targets,**{name:getattr(g,name).tolist() for name in ['src','dst','c','rho','q','corridor']}) for gi,g in graphs.items()}
    for gi,g in graphs.items():
        for ci,case in enumerate(TEST):
            for ep in range(6):
                seed=850000000+gi*10000+ci*100+ep;env=DeliveryNetwork(g,case,'NONE',seed,model_for(run))
                recorded_hash=df[(df.graph==gi)&(df.case==case.name)&(df.episode==ep)].schedule_hash.unique();assert len(recorded_hash)==1 and recorded_hash[0]==env.schedule.digest
                units=[dict(convoy=u.cid,target=u.target,depart=u.depart,deadline=u.deadline) for u in env.units]
                environments.append(dict(graph=gi,case=case.name,episode=ep,environment_seed=seed,schedule_hash=env.schedule.digest,closures=[[e,a,b] for e,(a,b) in sorted(env.schedule.intervals.items())],reference=env.reference,horizon=env.horizon,scale=env.scale,units=units))
                for u in env.units:departures[(gi,case.name,ep,u.cid)]=(u.depart,u.deadline,u.target)
    (out/'test_environment_manifest.json').write_text(json.dumps(dict(source_hash=fingerprint(),graphs=graph_records,environments=environments),indent=2)+'\n')
    for r in raw.itertuples(index=False):
        g=graphs[r.graph];route=ast.literal_eval(r.path);assert isinstance(route,list) and all(isinstance(e,int) and 0<=e<g.m for e in route)
        assert np.isclose(r.nominal,sum(g.c[e] for e in route),rtol=0,atol=1e-8)
        node=g.depot
        for e in route:assert int(g.src[e])==node;node=int(g.dst[e])
        depart,deadline,target=departures[(r.graph,r.case,r.episode,r.convoy)];assert np.isclose(deadline,r.deadline) and target==r.target
        assert not r.delivered or node==target
        if abs(r.elapsed+depart-deadline)>1e-9:assert r.on_time==int(bool(r.delivered) and r.elapsed+depart<=deadline)
    assert (raw.delivered+raw.censored).eq(1).all() and (raw.on_time<=raw.delivered).all()
    assert np.allclose(raw.elapsed,raw[['travel','service','wait','inspection','hold']].sum(axis=1),rtol=0,atol=1e-7)
    rebuilt=raw.groupby(keys).agg(on_time=('on_time','mean'),delivery=('delivered','mean'),elapsed=('elapsed','mean')).sort_index();recorded=df.set_index(keys).sort_index();assert rebuilt.index.equals(recorded.index)
    for col in rebuilt:assert np.allclose(rebuilt[col],recorded[col],rtol=0,atol=1e-8),col
    assert df[df.method=='LEARN'].rejections.between(0,1).all() and df[df.method=='KEEP_ONE'].rejections.between(0,1).all()
    assert df[df.method=='ALL'].rejections.eq(0).all()
    summary=df.groupby('method').agg(episodes=('on_time','size'),routing_models=('seed',lambda x:x[x>=0].nunique()),on_time_pct=('on_time',lambda x:100*x.mean()),delivery_pct=('delivery',lambda x:100*x.mean()),elapsed=('elapsed','mean'),mean_rejections=('rejections','mean'),rejections=('rejections','sum'),routing_calls=('routing_calls','sum')).reindex(METHODS);summary.to_csv(out/'summary.csv')
    df.groupby(['size','case','method']).agg(on_time_pct=('on_time',lambda x:100*x.mean()),delivery_pct=('delivery',lambda x:100*x.mean()),mean_rejections=('rejections','mean')).to_csv(out/'all_conditions.csv')
    paired=paired_inference(df);paired.to_csv(out/'primary_contrasts.csv',index=False)
    pair=df[df.method=='LEARN'].merge(df[df.method=='ALL'],on=['seed','graph','size','case','episode'],suffixes=('_learn','_all'),validate='one_to_one')
    pair['difference_pp']=100*(pair.on_time_learn-pair.on_time_all)
    assert pair[pair.rejections_learn==0].difference_pp.eq(0).all()
    # With one permitted rejection and ALL thereafter, these paired outcomes are
    # effects of that single rejected packet, including its downstream feedback.
    active=pair[pair.rejections_learn==1].copy();active['effect']=np.where(active.difference_pp>0,'beneficial_rejection',np.where(active.difference_pp<0,'harmful_rejection','no_delivery_effect'))
    active[['seed','graph','size','case','episode','difference_pp','effect']].to_csv(out/'heldout_rejection_effects.csv',index=False)
    activity=active.groupby(['seed','effect']).size().unstack(fill_value=0);activity.to_csv(out/'heldout_rejection_summary.csv')
    gate=pd.read_csv(run/'gate_decisions.csv.gz');rejected=gate[~gate.accepted]
    assert len(rejected)==len(active) and not rejected.duplicated(['seed','graph','case','episode']).any()
    effects=active.merge(rejected,on=['seed','graph','size','case','episode'],validate='one_to_one');effects[['seed','graph','size','case','episode','packet','t','receiver','difference_pp','effect']].to_csv(out/'identified_packet_effects.csv',index=False)
    figures=[];plt.rcParams.update({'font.size':9})
    with PdfPages(out/'delivery_learning_report.pdf') as pdf:
        def save(fig,name):fig.tight_layout();pdf.savefig(fig);fig.savefig(out/(name+'.png'),dpi=150);plt.close(fig);figures.append(name)
        fig,axes=plt.subplots(1,2,figsize=(12,4.7))
        for s in SEEDS:
            t=training[training.seed==s].sort_values('episode');axes[0].plot(t.episode,100*t.on_time.rolling(25,min_periods=1).mean(),alpha=.55)
            v=validations[validations.seed==s].groupby('checkpoint').on_time.mean();axes[1].plot(v.index,100*v,marker='o',label=f's{s}, selected{int(selected[selected.seed==s].selected_episode.iloc[0])}')
        axes[0].set_xlabel('Training episode');axes[0].set_ylabel('Training on-time delivery (%) /25episode smoothing');axes[1].set_xlabel('Checkpoint episode');axes[1].set_ylabel('Separate validation on-time (%)');axes[1].legend(fontsize=7,ncol=2);fig.suptitle('Eight independent routing runs; initial-policy fallback is disclosed\nObserved learning traces, not a convergence proof',fontsize=11);save(fig,'01_routing_training')
        fig,ax=plt.subplots(figsize=(11,4.6));ax.bar(range(len(METHODS)),summary.on_time_pct);ax.set_xticks(range(len(METHODS)),METHODS,rotation=30,ha='right',fontsize=8);ax.set_ylabel('Held-out fleet on-time delivery (%)');ax.set_ylim(0,105);fig.suptitle('Delivery is primary; no bandwidth reward\nCommon frozen routing actors isolate receiver-gate effects; planners run once per environment',fontsize=11);save(fig,'02_heldout_delivery')
        fig,ax=plt.subplots(figsize=(10,4.4));y=np.arange(3);ax.errorbar(paired.difference_pp,y,xerr=np.maximum(0,np.vstack([paired.difference_pp-paired.lower_pp,paired.upper_pp-paired.difference_pp])),fmt='o',capsize=4);ax.set_yticks(y,['LEARN - '+m for m in PRIMARY]);ax.axvline(0,color='black');ax.axvline(1,color='gray',ls='--',label='1pp practical mean target');ax.set_xlabel('On-time delivery difference (percentage points)');ax.legend();fig.suptitle('Primary paired contrasts,20000crossed draws /Bonferroni3\nPositive mean alone does not establish superiority',fontsize=11);save(fig,'03_primary_uncertainty')
        fig,axes=plt.subplots(3,1,figsize=(14,9))
        for ax,baseline in zip(axes,PRIMARY):
            index=['seed','graph','size','case','episode'];l=df[df.method=='LEARN'].set_index(index).on_time
            if baseline.startswith('PLANNER'):
                b=df[df.method==baseline].set_index(['graph','size','case','episode']).on_time;diff=l.to_frame('learn');diff['baseline']=[b.loc[(g,size,c,e)] for s,g,size,c,e in diff.index]
            else:diff=l.to_frame('learn').join(df[df.method==baseline].set_index(index).on_time.rename('baseline'))
            diff['value']=100*(diff.learn-diff.baseline);z=diff.reset_index().groupby(['size','case']).value.mean().unstack().reindex(index=[19,51,131],columns=[c.name for c in TEST]);ax.imshow(z,cmap='RdBu',vmin=-10,vmax=10,aspect='auto');ax.set_yticks(range(3),[19,51,131]);ax.set_xticks(range(12),[c.name for c in TEST],rotation=25,ha='right',fontsize=8);ax.set_ylabel('Nodes');ax.set_title('LEARN minus '+baseline+' (pp)')
            for i in range(3):
                for j in range(12):ax.text(j,i,f'{z.iloc[i,j]:+.1f}',ha='center',va='center',fontsize=7)
        fig.suptitle('Every declared condition; no favorable-case selection',fontsize=11);save(fig,'04_all_conditions')
        fig,axes=plt.subplots(1,2,figsize=(12,4.8));z=labels[~labels.control];counts=z.assign(kind=np.where(z.delta<0,'admit_harms',np.where(z.delta>0,'admit_helps','no_delivery_effect'))).groupby(['seed','kind']).size().unstack(fill_value=0).reindex(range(8),fill_value=0);counts.plot.bar(stacked=True,ax=axes[0]);axes[0].set_ylabel('Complete-fleet packet intervention labels');axes[0].set_title('Training labels')
        if len(activity):activity.reindex(range(8),fill_value=0).plot.bar(stacked=True,ax=axes[1])
        axes[1].set_ylabel('Held-out rejected packets');axes[1].set_title('Actual single-rejection delivery effects');fig.suptitle('Training labels and held-out effects are separate\nZero delivery effect may still change time/cost; no all-transmission FIR claim',fontsize=11);save(fig,'05_packet_effects')
        fig,axes=plt.subplots(1,2,figsize=(12,4.7));ranking.sort_values('setting').plot.bar(x='setting',y='on_time',ax=axes[0],legend=False);axes[0].set_ylabel('Gate-validation on-time fraction');axes[0].set_title('Setting0 is disabled ALL fallback')
        df.groupby('method').rejections.mean().reindex(METHODS).plot.bar(ax=axes[1]);axes[1].set_ylabel('Rejected packets per fleet episode');axes[1].set_title('Deployed gate activity');fig.suptitle('Validation locks the gate before held-out testing\nTree dispersion is heuristic uncertainty, not calibrated safety',fontsize=11);save(fig,'06_gate_selection_activity')
        fig,axes=plt.subplots(1,2,figsize=(12,4.6))
        for method in METHODS:
            a=df[df.method==method].groupby('size')[['on_time','delivery']].mean();axes[0].plot(a.index,100*a.on_time,marker='o',label=method);axes[1].plot(a.index,100*a.delivery,marker='o',label=method)
        for ax in axes:ax.set_xlabel('Network nodes');ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.2)
        axes[0].set_ylabel('On-time delivery (%)');axes[1].set_ylabel('Whole-horizon delivery (%)');fig.suptitle('Task completion and deadline success remain distinct\n131-node graphs are outside routing-training sizes',fontsize=11);save(fig,'07_network_scale')
    criteria=bool((paired.corrected_positive & paired.mean_reaches_1pp).all())
    verification=dict(status='passed',source_hash=fingerprint(),report_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),training_episodes=len(training),routing_models=8,selected_trained_checkpoints=int(selected.selected_episode.gt(0).sum()),label_attempts=len(attempts),causal_labels=len(labels),active_labels=int((~labels.control).sum()),gate_models=8,test_episodes=len(df),test_convoys=len(raw),reconstructed_environments=len(environments),heldout_rejections=len(active),primary_target_supported=criteria,gate_setting=lock['setting'],figures=len(figures),bandwidth_reward=False)
    (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    text='# Delivery-primary learned routing and causal gate\n\nRead ../delivery-learning-findings.md for the supported claim and limitations. No bandwidth savings are substituted for delivery.\n\n'+summary.to_markdown(floatfmt='.5f')+'\n\n'+paired.to_markdown(index=False,floatfmt='.5f')+'\n\n'
    text+='## Reproduce\n\nInstall the base environment with `bash setup_local.sh`, then `.venv/bin/python -m pip install -r requirements-actor-aware.txt` for gate fitting. From root run `.venv/bin/python simulator/run_delivery_learning.py --output simulator/out/delivery-learning-reproduction --workers 4`; then `.venv/bin/python simulator/report_delivery_learning.py --run simulator/out/delivery-learning-reproduction`. A fresh run folder is required. Use `MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`.\n\nThe runner uses the preserved timed-network calibration file, included in the ZIP. Models are inference checkpoints, not complete optimizer/replay resumes. Eight routing seeds and gates are stored separately. One selected initial actor, if present, is explicit in selected_routing_models.csv. Source and training records of both stopped development passes are archived; neither reached held-out testing. The final comparison uses the corrected v3physics and retrained actors only.\n\nRun `.venv/bin/python -m pytest -q simulator/tests_*.py` for the complete test suite.\n\nOpen delivery_learning_report.pdf or index.html for seven figures. Raw training, checkpoint validation, causal labels with both fleet branches, gate validation, held-out convoy outcomes and gate decisions are included. test_environment_manifest.json reconstructs and hash-checks every held-out closure schedule, weighted graph and convoy departure/deadline. sampled_training_opportunity.csv is a hindsight diagnostic over sampled training interventions only, not a deployable oracle or an upper bound over unobserved packets. Identified packet effects use the one-rejection-per-fleet constraint; their denominator is actual rejected packets, not all transmissions.\n'
    (out/'README.md').write_text(text)
    html='<!doctype html><meta charset="utf-8"><title>Delivery-primary learning</title><style>body{font-family:system-ui;max-width:1200px;margin:2em auto}img{width:100%}</style><h1>Delivery-primary learned routing and causal gate</h1><p>Primary objective: fleet on-time delivery. Common frozen routing actors and actual paired packet outcomes. Read findings for limitations.</p>'
    for name in figures:html+='<h2>'+name.replace('_',' ')+'</h2><img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
    (out/'index.html').write_text(html);print(json.dumps(verification),flush=True)
if __name__=='__main__':main()
