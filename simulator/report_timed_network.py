"""Audited development network results and full response surface."""
import argparse
import ast
import base64
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd
from timed_network import Calibration,Schedule,graph_for,path,METHODS as BASE_METHODS
from run_timed_network_ablation import fingerprint as ablation_hash
METHODS=BASE_METHODS+['VALUE_PRIORITY']
from run_timed_network_development import fingerprint as pilot_hash
from run_timed_network_surface import fingerprint as surface_hash,CASES as SURFACE_CASES

KEYS=['graph','size','case','bandwidth','episode','method']


def csv_chunks(folder,name,usecols=None):
    full=folder/(name+'.csv.gz')
    files=[full] if full.exists() else sorted((folder/(name+'_parts')).glob('part*.csv.gz'))
    assert files,(folder,name)
    for file in files:
        yield from pd.read_csv(file,chunksize=100000,usecols=usecols)


def audit_run(folder,expected_episodes,graph_seed,episodes_per_cell,nmethods=7):
    meta=json.loads((folder/'pipeline.json').read_text());assert meta['status']=='completed'
    df=pd.read_csv(folder/'episodes.csv.gz');assert len(df)==expected_episodes and not df.duplicated(KEYS).any()
    assert df.groupby(['graph','case','episode']).schedule_hash.nunique().eq(1).all()
    assert df.groupby(['graph','case','bandwidth','episode']).method.nunique().eq(nmethods).all()
    assert df.groupby('method').size().nunique()==1
    index=df.set_index(KEYS).sort_index()
    rows=[];nconvoys=0;graph_cache={}
    for chunk in csv_chunks(folder,'convoys'):
        nconvoys+=len(chunk)
        assert not chunk.duplicated(KEYS+['convoy']).any()
        assert (chunk.delivered+chunk.censored).eq(1).all()
        assert (chunk.on_time<=chunk.delivered).all()
        assert np.allclose(chunk.elapsed,chunk[['travel','service','wait','inspection','hold']].sum(axis=1),rtol=0,atol=1e-7)
        for r in chunk[['graph','size','target','path','nominal','delivered']].itertuples(index=False):
            if r.graph not in graph_cache:graph_cache[r.graph]=graph_for(graph_seed+r.graph,r.size)
            g=graph_cache[r.graph];edges=ast.literal_eval(r.path)
            assert np.isclose(r.nominal,sum(g.c[e] for e in edges),rtol=0,atol=1e-8)
            node=g.depot
            for e in edges:assert int(g.src[e])==node;node=int(g.dst[e])
            if r.delivered:assert node==r.target
        agg=chunk.groupby(KEYS).agg(n=('on_time','size'),on_time=('on_time','sum'),delivery=('delivered','sum'),elapsed=('elapsed','sum'),nominal=('nominal','sum'),encounters=('encounters','sum'))
        rows.append(agg)
    assert nconvoys==8*len(df)
    totals=pd.concat(rows).groupby(level=list(range(len(KEYS)))).sum().sort_index();assert totals.n.eq(8).all()
    assert totals.index.equals(index.index)
    for col in ['on_time','delivery','elapsed','nominal']:assert np.allclose(totals[col]/totals.n,index[col],rtol=0,atol=1e-8),col
    assert np.array_equal(totals.encounters,index.encounters)
    decision_counts=[];blocked_calls=0;calls=0
    for c in csv_chunks(folder,'decisions',KEYS+['t','peer_action_change','blocked_options']):
        calls+=len(c);blocked_calls+=int(c.blocked_options.gt(0).sum())
        decision_counts.append(c.groupby(KEYS).agg(routing_calls=('t','size'),peer_action_changes=('peer_action_change','sum'),blocked_options=('blocked_options','sum')))
    decision_counts=pd.concat(decision_counts).groupby(level=list(range(len(KEYS)))).sum().sort_index()
    for col in decision_counts:assert np.array_equal(decision_counts[col],index[col]),col
    packet_sums=[];last={};packet_count=0
    for c in csv_chunks(folder,'packets',KEYS+['tx_start','tx_end','offered','id']):
        packet_count+=len(c);assert (c.tx_start>=c.offered-1e-9).all()
        for key,group in c.groupby(KEYS,sort=False):
            scale=float(np.median(graph_cache[key[0]].c));starts=group.tx_start.to_numpy();ends=group.tx_end.to_numpy()
            assert starts[0]>=last.get(key,-np.inf)-1e-8
            assert np.all(starts[1:]>=ends[:-1]-1e-8)
            assert np.allclose(ends-starts,key[3]*scale,rtol=0,atol=1e-8)
            last[key]=ends[-1]
        c['queue_age']=c.tx_start-c.offered
        packet_sums.append(c.groupby(KEYS).agg(transmitted=('id','size'),radio_queue_delay=('queue_age','sum')))
    packet_sums=pd.concat(packet_sums).groupby(level=list(range(len(KEYS)))).sum().reindex(index.index,fill_value=0)
    assert np.array_equal(packet_sums.transmitted,index.transmitted)
    assert np.allclose(packet_sums.radio_queue_delay,index.radio_queue_delay,rtol=0,atol=1e-7)
    assert index.tx_started.sub(index.transmitted).between(0,1).all()
    assert index.tx_bytes.eq(64*index.transmitted).all() and index.attempted_tx_bytes.eq(64*index.tx_started).all()
    assert index[index.index.get_level_values('method')=='NONE'].tx_started.eq(0).all()
    return df,dict(episodes=len(df),convoys=nconvoys,decisions=calls,blocked_option_decisions=blocked_calls,completed_packets=packet_count)


def contrasts(df):
    cases=list(dict.fromkeys(df.case));ng=df.graph.nunique();ne=df.episode.nunique()
    idx=pd.MultiIndex.from_product([range(ng),cases,[0.,.25,1.],range(ne)],names=['graph','case','bandwidth','episode'])
    pairs=['RAW_ALL','AGE_ALL','LATEST','WARN_PRIORITY','VALUE_PRIORITY'];arrays=[]
    for endpoint in ['on_time','attempted_tx_bytes']:
        p=df.pivot(index=idx.names,columns='method',values=endpoint).reindex(idx);assert not p.isna().any().any()
        arrays.extend([(p.VALUE-p[b]).to_numpy().reshape(ng,len(cases),3,ne) for b in pairs])
    a=np.stack(arrays,axis=-1);rng=np.random.default_rng(838103);samples=[]
    for _ in range(40):
        n=250;gi=rng.integers(ng,size=(n,ng));ei=rng.integers(ne,size=(n,ng,len(cases),ne))
        z=a[gi[:,:,None,None,None],np.arange(len(cases))[None,None,:,None,None],np.arange(3)[None,None,None,:,None],ei[:,:,:,None,:],:]
        samples.append(z.mean(axis=(1,2,3,4)))
    samples=np.concatenate(samples);lo,hi=np.quantile(samples,[.025,.975],axis=0);records=[]
    for i,endpoint in enumerate(['on_time','attempted_tx_bytes']):
        for j,b in enumerate(pairs):
            k=i*len(pairs)+j;scale=100 if endpoint=='on_time' else 1
            records.append(dict(method='VALUE',baseline=b,endpoint=endpoint,difference=float(a[...,k].mean()*scale),lower=lo[k]*scale,upper=hi[k]*scale,scope='descriptive paired graph/environment bootstrap;10000draws;not confirmatory'))
    return pd.DataFrame(records)


def calibration_probe(model):
    rng=np.random.default_rng(729000123);rows=[]
    for gi,size in enumerate([19,19,51,51,131,131]):
        g=graph_for(729010+gi,size);scale=float(np.median(g.c));reference=float(np.median([sum(g.c[e]+.2 for e in path(g,g.depot,t,g.c+.2)) for t in g.targets]))
        for ci,case in enumerate(SURFACE_CASES):
            schedule=Schedule(g,case,729000000+gi*100000+ci*100,reference)
            for _ in range(40):
                e=int(rng.integers(g.m));observed=float(rng.uniform(0,2*reference));age=float(rng.choice([0.,.1,.3,.7,1.5,3.,6.,10.])*scale);query=observed+age;conf=float(rng.choice([.75,.85,1.]))
                was=schedule.closed(e,observed);report=was if rng.random()<conf else not was;truth=int(schedule.closed(e,query))
                rows.append(dict(graph=gi,size=size,case_id=ci,truth=truth,age_aware=model.probability(report,age/scale,query/reference,conf),age_ignorant=model.probability(report,age/scale,query/reference,conf,age_aware=False),prior=model.prior(query/reference)))
    return pd.DataFrame(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pilot',default='simulator/out/timed-network-development-v2');ap.add_argument('--surface',default='simulator/out/timed-network-surface');ap.add_argument('--ablation',default='simulator/out/timed-network-ablation');ap.add_argument('--output',default='revision/timed-network-results');args=ap.parse_args()
    pilot,surface,out=Path(args.pilot),Path(args.surface),Path(args.output);out.mkdir(parents=True,exist_ok=True)
    assert json.loads((pilot/'pipeline.json').read_text())['source_hash']==pilot_hash()
    assert json.loads((surface/'pipeline.json').read_text())['source_hash']==surface_hash()
    lock=json.loads((pilot/'locked_settings.json').read_text());locked=json.loads((surface/'locked_parent.json').read_text())
    assert locked['threshold']==lock['value_threshold'] and locked['calibration_sha256']==hashlib.sha256((pilot/'calibration.json').read_bytes()).hexdigest()
    validation=pd.read_csv(pilot/'validation.csv.gz');rank=validation.groupby('threshold').agg(on_time=('on_time','mean'),bytes=('tx_bytes','mean')).reset_index().sort_values(['on_time','bytes','threshold'],ascending=[False,True,True]);assert float(rank.iloc[0].threshold)==lock['value_threshold'];rank.to_csv(out/'validation_selection.csv',index=False)
    pdf,pv=audit_run(pilot,6804,712010,6);sdf,sv=audit_run(surface,48384,720010,4)
    ablation=Path(args.ablation);assert json.loads((ablation/'pipeline.json').read_text())['source_hash']==ablation_hash()
    pa,pav=audit_run(ablation/'pilot',972,712010,6,nmethods=1);sa,sav=audit_run(ablation/'surface',6912,720010,4,nmethods=1)
    pdf=pd.concat([pdf,pa],ignore_index=True);sdf=pd.concat([sdf,sa],ignore_index=True)
    assert len(pdf)==7776 and len(sdf)==55296
    assert pdf.groupby(['graph','case','bandwidth','episode']).schedule_hash.nunique().eq(1).all()
    assert sdf.groupby(['graph','case','bandwidth','episode']).schedule_hash.nunique().eq(1).all()
    summaries={};comparisons={}
    for label,df in [('pilot',pdf),('surface',sdf)]:
        summary=df.groupby('method').agg(episodes=('on_time','size'),on_time_pct=('on_time',lambda x:100*x.mean()),delivery_pct=('delivery',lambda x:100*x.mean()),attempted_bytes=('attempted_tx_bytes','mean'),completed_bytes=('tx_bytes','mean'),elapsed=('elapsed','mean'),nominal=('nominal','mean'),encounters=('encounters','mean'),peer_changes=('peer_action_changes','sum'),routing_calls=('routing_calls','sum'),radio_airtime=('radio_airtime','mean'))
        summary.to_csv(out/(label+'_summary.csv'));summaries[label]=summary
        df.groupby(['size','bandwidth','method']).agg(on_time_pct=('on_time',lambda x:100*x.mean()),attempted_bytes=('attempted_tx_bytes','mean'),delivery_pct=('delivery',lambda x:100*x.mean())).to_csv(out/(label+'_size_capacity.csv'))
        df.groupby(['size','case','bandwidth','method']).agg(on_time_pct=('on_time',lambda x:100*x.mean()),delivery_pct=('delivery',lambda x:100*x.mean()),attempted_bytes=('attempted_tx_bytes','mean'),elapsed=('elapsed','mean'),encounters=('encounters','mean'),peer_changes=('peer_action_changes','sum')).to_csv(out/(label+'_all_conditions.csv'))
        comparisons[label]=contrasts(df);comparisons[label].to_csv(out/(label+'_contrasts.csv'),index=False)
        df.groupby(['bandwidth','method']).agg(on_time_pct=('on_time',lambda x:100*x.mean()),attempted_bytes=('attempted_tx_bytes','mean'),completed_queue_age=('radio_queue_delay',lambda x:x.sum()),completed_packets=('transmitted','sum')).to_csv(out/(label+'_capacity.csv'))
    assert len(sdf.groupby(['size','case','bandwidth']))==864
    factors=['deadline_ratio','duration','closure_fraction','scout_lead','inspection_scale','bandwidth']
    for factor in factors:
        sdf.groupby([factor,'method']).agg(on_time_pct=('on_time',lambda x:100*x.mean()),attempted_bytes=('attempted_tx_bytes','mean'),encounters=('encounters','mean')).to_csv(out/('factor_'+factor+'.csv'))
    model=Calibration.load(json.loads((pilot/'calibration.json').read_text())['model']);probe=calibration_probe(model);probe.to_csv(out/'calibration_probe.csv.gz',index=False)
    br={m:float(np.mean((probe[m]-probe.truth)**2)) for m in ['age_aware','age_ignorant','prior']};pd.DataFrame([br]).to_csv(out/'common_probe_brier.csv',index=False)
    # Preserve all six surface graph definitions and complete finite schedules.
    graphs=[];closures=[]
    for gi,size in enumerate([19,19,51,51,131,131]):
        g=graph_for(720010+gi,size);ref=float(np.median([sum(g.c[e]+.2 for e in path(g,g.depot,t,g.c+.2)) for t in g.targets]))
        graphs.append(dict(graph=gi,size=size,depot=g.depot,targets=g.targets,src=g.src.tolist(),dst=g.dst.tolist(),cost=g.c.tolist(),capacity=g.q.tolist()))
        for ci,case in enumerate(SURFACE_CASES):
            for ep in range(4):
                schedule=Schedule(g,case,720000000+gi*1000000+ci*100+ep,ref)
                for edge,(start,end) in schedule.intervals.items():closures.append(dict(graph=gi,case_id=ci,episode=ep,edge=edge,start=start,end=end,schedule_hash=schedule.digest))
    (out/'surface_graphs.json').write_text(json.dumps(graphs,indent=2)+'\n');pd.DataFrame(closures).to_csv(out/'surface_closures.csv.gz',index=False)
    figures=[];plt.rcParams.update({'font.size':9})
    with PdfPages(out/'timed_network_report.pdf') as report:
        def save(fig,name,rect=None):
            fig.tight_layout(rect=rect);report.savefig(fig);fig.savefig(out/(name+'.png'),dpi=150);plt.close(fig);figures.append(name)
        fig,axes=plt.subplots(1,2,figsize=(12,4.8))
        for label,marker in [('pilot','o'),('surface','s')]:
            s=summaries[label].reindex(METHODS);axes[0].plot(range(len(METHODS)),s.on_time_pct,marker=marker,label=label);axes[1].plot(range(len(METHODS)),s.attempted_bytes,marker=marker,label=label)
        for ax in axes:ax.set_xticks(range(len(METHODS)),METHODS,rotation=35,ha='right',fontsize=8);ax.legend();ax.grid(alpha=.2)
        axes[0].set_ylabel('On-time delivery (%)');axes[1].set_ylabel('Bytes charged for started broadcast frames / mission');fig.suptitle('Timed network revision: task performance and real transmission cost\nPlanner-based development evidence; no trained MARL superiority claim',fontsize=11);save(fig,'01_task_and_transmissions')
        fig,axes=plt.subplots(1,3,figsize=(13,4.5))
        for ax,bw in zip(axes,[0.,.25,1.]):
            s=sdf[sdf.bandwidth==bw].groupby('method')[['on_time','attempted_tx_bytes']].mean()
            for mi,method in enumerate(METHODS):
                r=s.loc[method];ax.scatter(r.attempted_tx_bytes,100*r.on_time,label=method,marker=['o','s','^','v','D','P','X','*'][mi],color='C'+str(mi),s=45)
                if method=='VALUE':ax.annotate(method,(r.attempted_tx_bytes,100*r.on_time),fontsize=8,xytext=(3,5),textcoords='offset points')
            ax.set_title('Packet service '+str(bw)+' × median edge time');ax.set_xlabel('Started-frame bytes / mission');ax.set_ylabel('On-time delivery (%)');ax.grid(alpha=.2)
        fig.suptitle('Whole declared surface: efficiency tradeoffs at each channel capacity',fontsize=11);fig.legend(*axes[0].get_legend_handles_labels(),loc='lower center',ncol=4,fontsize=8);save(fig,'02_capacity_tradeoff',rect=(0,.15,1,1))
        fig,axes=plt.subplots(2,3,figsize=(13,8));pair=sdf.pivot(index=['graph','case','bandwidth','episode','deadline_ratio','duration','closure_fraction'],columns='method',values='on_time').reset_index();pair['difference']=100*(pair.VALUE-pair.WARN_PRIORITY)
        for ri,fraction in enumerate([.1,.3]):
            for ci,bw in enumerate([0.,.25,1.]):
                ax=axes[ri,ci];z=pair[(pair.closure_fraction==fraction)&(pair.bandwidth==bw)].groupby(['deadline_ratio','duration']).difference.mean().unstack().reindex(index=[1.1,1.35,1.75,2.5],columns=[.25,1.,4.]);im=ax.imshow(z,cmap='RdBu',vmin=-5,vmax=5,aspect='auto')
                ax.set_xticks(range(3),[.25,1,4]);ax.set_yticks(range(4),[1.1,1.35,1.75,2.5]);ax.set_xlabel('Closure duration / reference mission');ax.set_ylabel('Deadline ratio');ax.set_title(f'Budget {fraction:g}, packet service {bw:g}')
                for i in range(4):
                    for j in range(3):ax.text(j,i,f'{z.iloc[i,j]:+.2f}',ha='center',va='center',fontsize=8)
        fig.suptitle('VALUE minus warning-priority on-time delivery (percentage points)\nAll deadline/persistence cells retained; averaged over sizes, leads and inspection factors',fontsize=11);save(fig,'03_full_response_surface')
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for ax,(label,summary) in zip(axes,summaries.items()):
            y=np.arange(len(METHODS));changes=100*summary.reindex(METHODS).peer_changes/summary.reindex(METHODS).routing_calls;ax.barh(y,changes);ax.set_yticks(y,METHODS);ax.set_xlabel('Peer information changes next hop (% of routing calls)');ax.set_title(label)
        fig.suptitle('Online information now changes actual planner choices\nOwn-only probes at recorded decisions; not causal single-packet fleet FIR',fontsize=11);save(fig,'04_active_information')
        fig,axes=plt.subplots(1,2,figsize=(12,4.5))
        for method in METHODS:
            a=sdf.groupby(['inspection_scale','method']).on_time.mean().unstack();b=sdf.groupby(['scout_lead','method']).on_time.mean().unstack();axes[0].plot(a.index,100*a[method],marker='o',label=method);axes[1].plot(b.index,100*b[method],marker='o',label=method)
        axes[0].set_xlabel('Blocked-attempt inspection / edge travel');axes[1].set_xlabel('Scout lead / median edge travel')
        for ax in axes:ax.set_ylabel('On-time delivery (%)');ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.2)
        fig.suptitle('Physical controls: inspection cost and actual scout departure lead',fontsize=11);save(fig,'05_physical_controls')
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for method in METHODS:
            z=sdf.groupby(['size','method']).agg(on_time=('on_time','mean'),bytes=('attempted_tx_bytes','mean')).unstack();axes[0].plot([19,51,131],100*z.on_time[method],marker='o',label=method);axes[1].plot([19,51,131],z.bytes[method],marker='o',label=method)
        axes[0].set_ylabel('On-time delivery (%)');axes[1].set_ylabel('Started-frame bytes / mission')
        for ax in axes:ax.set_xlabel('Network nodes');ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.2)
        fig.suptitle('Same model and fitted interpreter across 19/51/131 nodes\nTwo graph instances per size; this is not learned-policy scale convergence',fontsize=11);save(fig,'06_network_scale')
        fig,axes=plt.subplots(1,2,figsize=(11,4.5));axes[0].bar(range(3),list(br.values()));axes[0].set_xticks(range(3),list(br),rotation=25,ha='right');axes[0].set_ylabel('Brier loss on common held-out sensor/query probe')
        for m in ['age_aware','age_ignorant']:
            probe['bin']=np.minimum((10*probe[m]).astype(int),9);z=probe.groupby('bin').agg(predicted=(m,'mean'),observed=('truth','mean'));axes[1].plot(z.predicted,z.observed,marker='o',label=m)
        axes[1].plot([0,1],[0,1],ls='--',color='gray');axes[1].set_xlabel('Predicted closure probability');axes[1].set_ylabel('Observed closure fraction');axes[1].legend();fig.suptitle('Calibration is measured on a shared probe, not inferred from confidence\nSynthetic labels; no field calibration or uncertainty guarantee',fontsize=11);save(fig,'07_interpreter_validation')
        fig,axes=plt.subplots(1,2,figsize=(12,5))
        for ax,(label,c) in zip(axes,comparisons.items()):
            z=c[c.endpoint=='on_time'];y=np.arange(len(z));ax.errorbar(z.difference,y,xerr=np.maximum(0,np.vstack([z.difference-z.lower,z.upper-z.difference])),fmt='o',capsize=3);ax.set_yticks(y,['VALUE - '+b for b in z.baseline]);ax.axvline(0,color='black',lw=1);ax.set_xlabel('On-time difference (percentage points)');ax.set_title(label);ax.grid(axis='x',alpha=.2)
        fig.suptitle('Descriptive paired graph/environment intervals, all selected comparators\nNot confirmatory tests or evidence of practical noninferiority',fontsize=11);save(fig,'08_paired_uncertainty')
    verification=dict(status='passed',scope='network development and sensitivity; not confirmed MARL superiority',pilot=pv,surface=sv,pilot_ablation=pav,surface_ablation=sav,total_method_episodes=len(pdf)+len(sdf),total_convoys=8*(len(pdf)+len(sdf)),ablation_hash=ablation_hash(),source_hash=pilot_hash(),surface_hash=surface_hash(),report_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),value_threshold=lock['value_threshold'],all_surface_cells=864,calibration_probe_rows=len(probe),common_probe_brier=br,figures=len(figures))
    (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    text='# Timed-network development and response surface\n\nRead ../timed-network-findings.md before interpreting performance. This is a new physical/communication revision with a fitted report interpreter and shared planning actor. It is not newly trained MARL or a confirmation of the original manuscript claim.\n\n'
    for label,s in summaries.items():text+='## '+label+'\n\n'+s.to_markdown(floatfmt='.4f')+'\n\n'+comparisons[label].to_markdown(index=False,floatfmt='.4f')+'\n\n'
    text+='## Reproduce\n\nFrom extracted root: `bash setup_local.sh`; use `.venv/bin/python simulator/run_timed_network_development.py --output simulator/out/timed-network-reproduction --workers 4`, then `.venv/bin/python simulator/run_timed_network_surface.py --parent simulator/out/timed-network-reproduction --output simulator/out/timed-network-surface-reproduction --workers 4`, then `.venv/bin/python simulator/run_timed_network_ablation.py --parent simulator/out/timed-network-reproduction --output simulator/out/timed-network-ablation-reproduction --workers 4`; then `.venv/bin/python simulator/report_timed_network.py --pilot simulator/out/timed-network-reproduction --surface simulator/out/timed-network-surface-reproduction --ablation simulator/out/timed-network-ablation-reproduction`. Use fresh run directories and `MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Default report output is revision/timed-network-results.\n\nOpen timed_network_report.pdf or index.html for eight figures. All condition tables, factor tables, contrasts, common-probe calibration data and full surface graphs/closure schedules are retained. ZIP includes raw calibration, validation, episodes, convoys, routing decisions and completed packet records. Attempted bytes charge 64 bytes for every started frame; completed bytes and actual partial-frame airtime are separate. The model uses abstract time units, no destruction, and one fitted interpreter; no independent routing-training seeds or convergence evidence are supplied.\n'
    (out/'README.md').write_text(text)
    html='<!doctype html><meta charset="utf-8"><title>Timed network development</title><style>body{font-family:system-ui;max-width:1200px;margin:2em auto}img{width:100%}</style><h1>Timed network development</h1><p>Actual physical closures, inspection delays, finite radio, and calibrated report interpretation. Development evidence, not confirmed MARL superiority.</p>'
    for name in figures:html+='<h2>'+name.replace('_',' ')+'</h2><img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
    (out/'index.html').write_text(html);print(json.dumps(verification),flush=True)
if __name__=='__main__':main()
