"""Audited descriptive mechanism report, not learned-policy superiority."""
import argparse,ast,base64,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from pretransmission import RADIO_FEATURES
from run_pretransmission_opportunity import fingerprint
from run_delivery_learning import TEST
from timed_network import graph_for


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/pretransmission-opportunity');ap.add_argument('--output',default='revision/pretransmission-opportunity-results');args=ap.parse_args()
    run,out=Path(args.run),Path(args.output);out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((run/'pipeline.json').read_text());assert meta['status']=='completed' and meta['source_hash']==fingerprint()
    def read(prefix):return pd.concat([pd.read_csv(p) for p in sorted(run.glob(prefix+'_s*_g*.csv.gz'))],ignore_index=True)
    episodes,batch,labels,raw=[read(n) for n in ['episodes','batched','labels','convoys']]
    keys=['actor_seed','graph','size','case','packet_time','episode'];assert len(episodes)==len(batch)==1104
    assert len(labels)==meta['isolated_interventions']
    assert not episodes.duplicated(keys).any() and not labels.duplicated(keys+['action']).any()
    assert not raw.duplicated(keys+['action','convoy']).any()
    assert len(raw)==8*(len(episodes)+len(batch)+len(labels))
    assert raw.groupby(keys+['action']).size().eq(8).all()
    assert raw.convoy.between(0,7).all()
    assert raw.groupby(keys).schedule_hash.nunique().eq(1).all()
    assert (raw.delivered+raw.censored).eq(1).all() and (raw.on_time<=raw.delivered).all()
    times=['travel','service','wait','inspection','hold']
    assert raw[times+['elapsed','nominal']].ge(-1e-9).all().all()
    assert np.allclose(raw.elapsed,raw[times].sum(axis=1),rtol=0,atol=1e-7)
    graphs={i:graph_for(860010+i,n) for i,n in enumerate([19,51,131])}
    for r in raw.itertuples(index=False):
        g=graphs[r.graph];route=ast.literal_eval(r.path);node=g.depot
        assert all(isinstance(e,int) and 0<=e<g.m for e in route)
        assert np.isclose(r.nominal,sum(g.c[e] for e in route),rtol=0,atol=1e-8)
        for e in route:assert int(g.src[e])==node;node=int(g.dst[e])
        assert not r.delivered or node==r.target
    rebuilt=raw.groupby(keys+['action']).agg(on_time=('on_time','mean'),delivery=('delivered','mean'),elapsed=('elapsed','mean'),encounters=('encounters','sum')).sort_index()
    for action,frame in [('send',episodes),('batched_priority',batch)]:
        expected=frame.set_index(keys).sort_index();actual=rebuilt.xs(action,level='action')
        assert actual.index.equals(expected.index)
        for col in ['on_time','delivery','elapsed']:assert np.allclose(actual[col],expected[col],rtol=0,atol=1e-8)
        assert actual.encounters.eq(expected.blocked_attempts).all()
    indexed=episodes.set_index(keys)
    for r in labels.itertuples(index=False):
        x=json.loads(r.features);a=json.loads(r.factual_convoys);b=json.loads(r.alternative_convoys)
        assert len(x)==len(RADIO_FEATURES) and np.isfinite(x).all() and len(a)==len(b)==8
        assert np.isclose(r.factual_on_time,np.mean([u['on_time'] for u in a]))
        assert np.isclose(r.alternative_on_time,np.mean([u['on_time'] for u in b]))
        assert np.isclose(r.gain,r.alternative_on_time-r.factual_on_time) and np.isclose(r.gain*8,round(r.gain*8))
        key=tuple(getattr(r,k) for k in keys)
        assert indexed.loc[key].schedule_hash==r.schedule_hash and np.isclose(indexed.loc[key].on_time,r.factual_on_time)
        assert np.isclose(rebuilt.loc[key+(r.action,)].on_time,r.alternative_on_time)
        for unit in a+b:assert np.isclose(unit['elapsed'],sum(unit[k] for k in times),rtol=0,atol=1e-7)
        scale=float(np.median(graphs[r.graph].c));tau=r.packet_time*scale
        for frames,airtime in [(r.factual_transmitted,r.factual_airtime),(r.alternative_transmitted,r.alternative_airtime)]:
            assert frames*tau-1e-7<=airtime<=(frames+1)*tau+1e-7
    for frame in [episodes,batch]:assert (frame.tx_started-frame.transmitted).between(0,1).all()
    action_summary=labels.groupby('action').agg(interventions=('gain','size'),helpful=('gain',lambda v:(v>0).sum()),harmful=('gain',lambda v:(v<0).sum()),no_delivery_effect=('gain',lambda v:(v==0).sum()),mean_gain_when_available_pp=('gain',lambda v:100*v.mean()),gain_sum=('gain','sum'))
    action_summary['mean_gain_over_all_episodes_pp']=100*action_summary.gain_sum/len(episodes)
    action_summary.to_csv(out/'action_effects.csv')
    best=labels.groupby(keys).gain.max().clip(lower=0).rename('sampled_hindsight_gain')
    diagnostic=episodes.join(best,on=keys);diagnostic['sampled_hindsight_gain']=diagnostic.sampled_hindsight_gain.fillna(0)
    diagnostic['sampled_hindsight_on_time']=diagnostic.on_time+diagnostic.sampled_hindsight_gain
    joined=diagnostic.merge(batch[keys+['on_time']],on=keys,suffixes=('_reference','_batched'),validate='one_to_one')
    joined['batch_difference_pp']=100*(joined.on_time_batched-joined.on_time_reference)
    joined.to_csv(out/'all_episode_diagnostics.csv',index=False)
    conditions=joined.groupby(['size','case','packet_time']).agg(reference_on_time_pct=('on_time_reference',lambda v:100*v.mean()),batched_on_time_pct=('on_time_batched',lambda v:100*v.mean()),batch_difference_pp=('batch_difference_pp','mean'),sampled_hindsight_gain_pp=('sampled_hindsight_gain',lambda v:100*v.mean()),captured=('captured','sum'),episodes=('captured','size'))
    conditions.to_csv(out/'all_conditions.csv')
    labels.groupby(['size','case','packet_time','action']).agg(interventions=('gain','size'),gain_pp=('gain',lambda v:100*v.mean()),helpful=('gain',lambda v:(v>0).sum()),harmful=('gain',lambda v:(v<0).sum())).to_csv(out/'all_action_conditions.csv')
    labels[['actor_seed','graph','size','case','packet_time','episode','action','gain','t','packet','offer_number','sender','edge']].to_csv(out/'identified_interventions.csv',index=False)
    summary=pd.DataFrame([dict(arm='Original VALUE priority / ALL receiver',on_time_pct=100*joined.on_time_reference.mean()),dict(arm='Batched VALUE priority / ALL receiver',on_time_pct=100*joined.on_time_batched.mean()),dict(arm='Sampled hindsight best action (not deployable)',on_time_pct=100*joined.sampled_hindsight_on_time.mean())]);summary.to_csv(out/'summary.csv',index=False)
    figures=[]
    with PdfPages(out/'pretransmission_report.pdf') as pdf:
        def save(fig,name):fig.tight_layout();pdf.savefig(fig);fig.savefig(out/(name+'.png'),dpi=150);plt.close(fig);figures.append(name)
        fig,axes=plt.subplots(1,2,figsize=(12,4.8));action_summary[['helpful','harmful','no_delivery_effect']].plot.bar(stacked=True,ax=axes[0]);axes[0].set_ylabel('Isolated interventions');axes[0].set_title('All outcomes retained')
        bars=axes[1].bar(action_summary.index,action_summary.mean_gain_over_all_episodes_pp);axes[1].bar_label(bars,fmt='%+.3f',padding=3);axes[1].margins(y=.22);axes[1].axhline(0,color='black',lw=.8);axes[1].set_ylabel('Delivery change (percentage points)');axes[1].set_title('Single action at the preselected sample point\nIneligible/missing actions retain reference outcome');fig.suptitle('Actual pre-transmission fleet effects; no learned controller',fontsize=12);save(fig,'01_action_effects')
        fig,axes=plt.subplots(1,2,figsize=(12,4.8));z=joined.groupby('size')[['on_time_reference','on_time_batched','sampled_hindsight_on_time']].mean()*100;z.plot.bar(ax=axes[0]);axes[0].set_ylabel('Fleet on-time delivery (%)');axes[0].legend(['Reference','Batched priority','Hindsight sample'],fontsize=8);axes[0].set_title('Hindsight is not a deployed policy')
        byseed=joined.groupby('actor_seed')[['batch_difference_pp','sampled_hindsight_gain']].mean();axes[1].plot(byseed.index,byseed.batch_difference_pp,'o-',label='Batched - reference');axes[1].plot(byseed.index,100*byseed.sampled_hindsight_gain,'o-',label='Hindsight sampled gain');axes[1].axhline(0,color='black',lw=.8);axes[1].set_xlabel('Frozen actor seed');axes[1].set_ylabel('Delivery difference (percentage points)');axes[1].legend();fig.suptitle('Simple batching versus available sampled opportunity\nOne weighted instance per size; descriptive development evidence',fontsize=12);save(fig,'02_batching_and_opportunity')
        fig,axes=plt.subplots(2,1,figsize=(14,7.5))
        for ax,col,title in [(axes[0],'batch_difference_pp','Batched priority minus original reference'),(axes[1],'sampled_hindsight_gain','Sampled hindsight best action minus reference')]:
            z=joined.groupby(['size','case'])[col].mean().unstack().reindex(columns=[c.name for c in TEST]);z=z*(100 if col=='sampled_hindsight_gain' else 1);bound=max(1.,float(np.abs(z.to_numpy()).max()));im=ax.imshow(z,cmap='RdBu',vmin=-bound,vmax=bound,aspect='auto');fig.colorbar(im,ax=ax,label='Percentage points');ax.set_xticks(range(12),z.columns,rotation=25,ha='right',fontsize=8);ax.set_yticks(range(3),z.index);ax.set_ylabel('Nodes');ax.set_title(title)
            for i in range(3):
                for j in range(12):ax.text(j,i,f'{z.iloc[i,j]:+.2f}',ha='center',va='center',fontsize=7,color='white' if abs(z.iloc[i,j])>.65*bound else 'black')
        fig.suptitle('All twelve declared conditions; capacity cells pooled as specified',fontsize=12);save(fig,'03_all_conditions')
    result=dict(status='passed',source_hash=fingerprint(),report_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),baseline_episodes=len(episodes),batched_episodes=len(batch),captured_episodes=int(episodes.captured.sum()),isolated_interventions=len(labels),convoy_records=len(raw),reference_on_time_pct=100*joined.on_time_reference.mean(),batched_on_time_pct=100*joined.on_time_batched.mean(),batch_difference_pp=joined.batch_difference_pp.mean(),sampled_hindsight_gain_pp=100*joined.sampled_hindsight_gain.mean(),figures=len(figures),controller_trained=False,superiority_test=False)
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    text='# Pre-transmission mechanism pilot\n\nDevelopment opportunity measurement with frozen routing, not learned-controller superiority. Hindsight chooses after seeing future outcomes and is not deployable.\n\n'+summary.to_markdown(index=False,floatfmt='.5f')+'\n\n'+action_summary.to_markdown(floatfmt='.5f')+'\n\nRead ../pretransmission-opportunity-findings.md and ../pretransmission-opportunity-protocol.md for assumptions and limitations. Open pretransmission_report.pdf or index.html for three figures.\n\nRerun from root with `.venv/bin/python simulator/run_pretransmission_opportunity.py --output simulator/out/pretransmission-reproduction`; then `.venv/bin/python simulator/report_pretransmission_opportunity.py --run simulator/out/pretransmission-reproduction`. Install using setup_local.sh plus requirements-actor-aware.txt for the historical full test suite. Use MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1.\n'
    (out/'README.md').write_text(text)
    html='<!doctype html><meta charset="utf-8"><title>Pre-transmission mechanism pilot</title><style>body{font-family:system-ui;max-width:1300px;margin:2em auto}img{width:100%}</style><h1>Pre-transmission mechanism pilot</h1><p>Frozen routers; actual isolated interventions; hindsight opportunity is not deployable performance.</p>'
    for name in figures:html+='<h2>'+name.replace('_',' ')+'</h2><img src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
    (out/'index.html').write_text(html);print(json.dumps(result),flush=True)


if __name__=='__main__':main()
