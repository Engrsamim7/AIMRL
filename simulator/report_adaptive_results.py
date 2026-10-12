"""Audit fresh adaptive experiments and report paired effects, including failures."""
import argparse,base64,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from run_adaptive_experiments import fingerprint,REGIMES


def read(run,name):
    p=run/(name+'.csv')
    return pd.read_csv(p if p.exists() else run/(name+'.csv.gz'))

def bootstrap(delta,rng,replicates=10000):
    arr=delta.to_numpy();ng,ne=arr.shape
    gi=rng.integers(ng,size=(replicates,ng));ei=rng.integers(ne,size=(replicates,ng,ne))
    return arr[gi[:,:,None],ei].mean(axis=(1,2))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='out/adaptive-gate-v2');ap.add_argument('--output',default='../revision/adaptive-gate-results');a=ap.parse_args();run=Path(a.input).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    pipeline=json.loads((run/'pipeline.json').read_text());assert pipeline['status']=='completed' and pipeline['source_hash']==fingerprint()
    ep=read(run,'episodes');cv=read(run,'convoys');keys=['family','graph','regime','episode','method','training_seed']
    assert len(ep)==len(ep[keys].drop_duplicates()) and len(cv)==len(ep)*3
    raw=cv.groupby(keys).agg(delivery=('delivered','mean'),blocked=('blocked_enc','sum'),nominal=('nominal','mean')).reset_index()
    joined=ep.merge(raw,on=keys,validate='one_to_one');assert np.allclose(joined.delivery_rate,joined.delivery) and np.allclose(joined.blocked_encounters_total,joined.blocked) and np.allclose(joined.nominal_all_mean,joined.nominal)
    assert (cv.delivered+cv.destroyed+cv.censored).eq(1).all()
    for col in ['blocked_enc','surprise_blocked_enc','delivered','destroyed','censored']:assert np.equal(cv[col],np.floor(cv[col])).all()
    assert np.allclose(cv.elapsed,cv.travel+cv.wait+cv.service,atol=1e-7)
    delivered=cv[cv.delivered==1];assert (delivered.nominal>=delivered.nominal_optimal-1e-8).all()
    reason_counts=[];total_packets=0;message_path=run/'messages.csv'
    if not message_path.exists():message_path=run/'messages.csv.gz'
    for chunk in pd.read_csv(message_path,chunksize=100000):
        total_packets+=len(chunk);acc=chunk[chunk.reason=='accepted'];assert acc.age.between(0,8+1e-8).all()
        if 'estimated_route_regret' in chunk:
            val=chunk.estimated_route_regret.dropna();assert val.ge(-1e-8).all()
        reason_counts.append(chunk.groupby(['family','regime','method','reason']).size())
    reasons=pd.concat(reason_counts,axis=1).fillna(0).sum(axis=1).rename('packets').reset_index();reasons.to_csv(out/'packet_reasons.csv',index=False)
    summaries=ep.groupby(['family','regime','method']).agg(delivery=('delivery_rate','mean'),episodes=('delivery_rate','size'),accepted_genuine=('true_accepted','mean'),accepted_spoof=('spoof_accepted','mean'),sent=('msg_sent','mean'),runtime=('seconds','mean'),delivered_time=('realized_delivered_mean','mean'),delivered_cost=('nominal_delivered_mean','mean')).reset_index();summaries.to_csv(out/'summary.csv',index=False)
    comparisons=['NC','COMM-ALL','FRC','FRC-v2','SOFT-NC','SOFT-ALL','SOFT-FRC','NO-CLEARANCE-GUARD','NO-FEEDBACK','NO-RISK-AVERSION','NO-AGE-DISCOUNT']
    rng=np.random.default_rng(20261012);results=[];survivor=[]
    # Two primary baselines x three topology families x four regimes = 24 tests.
    primary_count=24;tail=.05/(2*primary_count)
    for family in ep.family.unique():
        for regime in REGIMES:
            sub=ep[(ep.family==family)&(ep.regime==regime)&(ep.training_seed==-1)]
            pa=sub[sub.method=='VALUE-GATE'].set_index(['graph','episode']).delivery_rate
            for other in comparisons:
                pb=sub[sub.method==other].set_index(['graph','episode']).delivery_rate;delta=pa.subtract(pb);assert not delta.isna().any()
                matrix=delta.unstack();assert not matrix.isna().any().any();samples=bootstrap(matrix,rng)
                lo,hi=np.quantile(samples,[.025,.975]);slo,shi=np.quantile(samples,[tail,1-tail])
                primary=other in ['COMM-ALL','SOFT-ALL']
                results.append(dict(family=family,regime=regime,baseline=other,difference_pp=100*matrix.to_numpy().mean(),lower_pp=100*lo,upper_pp=100*hi,primary=primary,simultaneous_lower_pp=100*slo if primary else None,simultaneous_upper_pp=100*shi if primary else None,superiority_supported=bool(primary and slo>0)))
                if other in ['COMM-ALL','FRC','SOFT-ALL']:
                    arows=cv[(cv.family==family)&(cv.regime==regime)&(cv.method=='VALUE-GATE')];brows=cv[(cv.family==family)&(cv.regime==regime)&(cv.method==other)]
                    paired=arows.merge(brows,on=['graph','episode','convoy','target','depart_t','training_seed'],suffixes=('_a','_b'),validate='one_to_one');assert len(paired)==len(arows)==len(brows)
                    both=paired[(paired.delivered_a==1)&(paired.delivered_b==1)];survivor.append(dict(family=family,regime=regime,baseline=other,common_delivered=len(both),nominal_difference=float((both.nominal_a-both.nominal_b).mean()),elapsed_difference=float((both.realized_a-both.realized_b).mean())))
    con=pd.DataFrame(results);con.to_csv(out/'contrasts.csv',index=False);pd.DataFrame(survivor).to_csv(out/'common_survivor_contrasts.csv',index=False)
    control=read(run,'controlled_episodes');control_raw=read(run,'controlled_convoys');assert len(control_raw)==3*len(control)
    control_summary=control.groupby(['case','delay','loss','method']).delivery_rate.mean().reset_index();control_summary.to_csv(out/'controlled_summary.csv',index=False)
    figs=[]
    def save(fig,name,title):
        fig.tight_layout(rect=(0,0,1,.82) if name=='03_controlled' else None);fig.savefig(out/(name+'.png'),dpi=180);fig.savefig(out/(name+'.pdf'));figs.append((fig,name,title))
    plotted=['NC','COMM-ALL','FRC','SOFT-NC','SOFT-ALL','SOFT-FRC','VALUE-GATE'];families=list(ep.family.unique())
    fig,axs=plt.subplots(3,4,figsize=(18,12),sharey=True)
    for i,family in enumerate(families):
        for j,regime in enumerate(REGIMES):
            s=summaries[(summaries.family==family)&(summaries.regime==regime)].set_index('method').loc[plotted]
            axs[i,j].bar(range(len(s)),100*s.delivery,color=['#377baa']*6+['#d58a26']);axs[i,j].set_xticks(range(len(s)),s.index,rotation=75,fontsize=7);axs[i,j].set_title(family+' / '+regime,fontsize=10);axs[i,j].set_ylim(0,105)
        axs[i,0].set_ylabel('Actual delivery (%)')
    save(fig,'01_delivery','Fresh held-out delivery; soft comparators isolate the estimator from admission')
    fig,axs=plt.subplots(3,2,figsize=(12,11),sharex=True)
    for i,family in enumerate(families):
        for j,base in enumerate(['COMM-ALL','SOFT-ALL']):
            s=con[(con.family==family)&(con.baseline==base)].set_index('regime').loc[REGIMES];ys=np.arange(4)
            axs[i,j].errorbar(s.difference_pp,ys,xerr=[s.difference_pp-s.simultaneous_lower_pp,s.simultaneous_upper_pp-s.difference_pp],fmt='o');axs[i,j].axvline(0,color='black',lw=.8);axs[i,j].set_yticks(ys,REGIMES);axs[i,j].set_title(family+' vs '+base);axs[i,j].set_xlabel('Delivery difference (percentage points)')
    save(fig,'02_primary_contrasts','Bonferroni-adjusted paired bootstrap intervals for 24 prespecified contrasts')
    fig,axs=plt.subplots(1,2,figsize=(12,5),sharey=True)
    for ax,loss in zip(axs,[0.,.2]):
        s=control_summary[(control_summary.delay==1)&(control_summary.loss==loss)&(control_summary.method.isin(plotted))].pivot(index='case',columns='method',values='delivery_rate')*100
        s[plotted].plot.bar(ax=ax);ax.tick_params(axis='x',rotation=25);ax.set_title(f'Delay 1, loss {loss:.0%}');ax.set_ylabel('Actual delivery (%)');ax.get_legend().remove()
    handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.98),ncol=7,fontsize=8)
    save(fig,'03_controlled','Constructed truthful/false/impersonated reports: benefits and identity failure boundary')
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    packet=summaries[summaries.method.isin(['COMM-ALL','FRC','SOFT-ALL','VALUE-GATE'])].groupby('method')[['accepted_genuine','accepted_spoof']].mean();packet.plot.bar(ax=axs[0]);axs[0].set_ylabel('Accepted packets / episode (scenario-weighted)');axs[0].tick_params(axis='x',rotation=20)
    selected=json.loads((run/'selected.json').read_text());reasons[reasons.method=='VALUE-GATE'].groupby('reason').packets.sum().plot.bar(ax=axs[1]);axs[1].set_ylabel('Processed packet decisions');axs[1].tick_params(axis='x',rotation=35)
    save(fig,'04_admission','Selective admission is not transmission bandwidth reduction')
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    s=con[(con.family=='synthetic-39')&(con.baseline.isin(['SOFT-ALL','NO-CLEARANCE-GUARD','NO-FEEDBACK','NO-RISK-AVERSION','NO-AGE-DISCOUNT']))].pivot(index='regime',columns='baseline',values='difference_pp');s.plot.bar(ax=axs[0]);axs[0].set_ylabel('VALUE-GATE minus ablation (delivery pp)');axs[0].tick_params(axis='x',rotation=25)
    summaries[summaries.method.isin(['COMM-ALL','SOFT-ALL','VALUE-GATE'])].groupby(['family','method']).runtime.mean().unstack().plot.bar(ax=axs[1]);axs[1].set_ylabel('Measured seconds / episode');axs[1].tick_params(axis='x',rotation=20)
    save(fig,'05_ablation_runtime','Component effects and implementation overhead; measured on shared machine')
    replay=read(run,'replay');cr=read(run,'controlled_replay');rp=[]
    for kind,data in [('network',replay),('controlled',cr)]:
        for method,s in data.groupby('method'):rp.append(dict(scope=kind,method=method,interventions=len(s),helpful=int((s.delta_delivery>0).sum()),harmful=int((s.delta_delivery<0).sum()),unchanged=int((s.delta_delivery==0).sum()),changed_paths=int(s.changed_receiver_path.sum())))
    rdf=pd.DataFrame(rp);rdf.to_csv(out/'replay_summary.csv',index=False)
    fig,ax=plt.subplots(figsize=(10,4));rdf.set_index(['scope','method'])[['helpful','harmful','unchanged']].plot.bar(stacked=True,ax=ax);ax.set_ylabel('Single-message interventions');ax.tick_params(axis='x',rotation=30)
    save(fig,'06_packet_replay','Complete packet suppression: conditional realized effects, not additive policy benefit')
    stress_dir=run/'clearance-stress'
    stress_manifest=json.loads((stress_dir/'manifest.json').read_text())
    assert stress_manifest['status']=='completed' and stress_manifest['source_hash']==fingerprint()
    assert stress_manifest['helper_sha256']==hashlib.sha256(Path(__file__).with_name('run_clearance_stress.py').read_bytes()).hexdigest()
    stress=read(stress_dir,'episodes');stress_raw=read(stress_dir,'convoys')
    assert len(stress_raw)==3*len(stress)
    stress_summary=read(stress_dir,'summary');stress_summary.to_csv(out/'clearance_stress_summary.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    stress_summary.pivot(index='case',columns='method',values='delivery_rate').mul(100).plot.bar(ax=axs[0]);axs[0].set_ylabel('Actual delivery (%)')
    stress_summary[stress_summary['case']=='one-legitimate-clear'].set_index('method').nominal_delivered_mean.plot.bar(ax=axs[1]);axs[1].set_ylabel('Delivered nominal cost (all convoys survive)')
    for ax in axs:ax.tick_params(axis='x',rotation=25);ax.legend(fontsize=7)
    save(fig,'07_clearance_tradeoffs','Injected confirmation probes: legitimate-clear detour cost and multiple forged identities')
    actor_dir=run/'actor-inference';actor_manifest=json.loads((actor_dir/'manifest.json').read_text())
    assert actor_manifest['status']=='completed' and actor_manifest['source_hash']==fingerprint()
    assert actor_manifest['actor_source_sha256']==hashlib.sha256(Path(__file__).with_name('adaptive_actor.py').read_bytes()).hexdigest()
    assert actor_manifest['runner_sha256']==hashlib.sha256(Path(__file__).with_name('run_adaptive_actor_eval.py').read_bytes()).hexdigest()
    actors=read(actor_dir,'episodes');actor_raw=read(actor_dir,'convoys');assert len(actor_raw)==len(actors)*3
    actor_summary=actors.groupby(['algo','regime','method']).delivery_rate.mean().reset_index();actor_summary.to_csv(out/'actor_summary.csv',index=False)
    actor_contrasts=[]
    for algo in actors.algo.unique():
        for regime in REGIMES:
            sub=actors[(actors.algo==algo)&(actors.regime==regime)]
            left=sub[sub.method==algo.upper()+'-ADAPTIVE'].set_index(['training_seed','episode']).delivery_rate
            for base in ['ALL','FRC']:
                right=sub[sub.method==algo.upper()+'-'+base].set_index(['training_seed','episode']).delivery_rate
                delta=left.subtract(right).unstack();assert not delta.isna().any().any()
                arr=delta.to_numpy();gi=rng.integers(arr.shape[0],size=(10000,arr.shape[0]));ei=rng.integers(arr.shape[1],size=(10000,arr.shape[1]))
                samples=arr[gi[:,:,None],ei[:,None,:]].mean(axis=(1,2))
                lo,hi=np.quantile(samples,[.05/(2*32),1-.05/(2*32)])
                actor_contrasts.append(dict(algo=algo,regime=regime,baseline=base,difference_pp=100*arr.mean(),lower_pp=100*lo,upper_pp=100*hi,secondary_superiority_supported=bool(lo>0),scope='32 corrected exploratory actor comparisons; fixed original topology'))
                pa=actor_raw[(actor_raw.algo==algo)&(actor_raw.regime==regime)&(actor_raw.method==algo.upper()+'-ADAPTIVE')]
                pb=actor_raw[(actor_raw.algo==algo)&(actor_raw.regime==regime)&(actor_raw.method==algo.upper()+'-'+base)]
                joined_actor=pa.merge(pb,on=['training_seed','episode','convoy','target','depart_t'],validate='one_to_one');assert len(joined_actor)==len(pa)==len(pb)
    actor_con=pd.DataFrame(actor_contrasts);actor_con.to_csv(out/'actor_contrasts.csv',index=False)
    fig,axs=plt.subplots(2,2,figsize=(12,8),sharey=True)
    for ax,algo in zip(axs.flat,actors.algo.unique()):
        actor_summary[actor_summary.algo==algo].pivot(index='regime',columns='method',values='delivery_rate').mul(100).plot.bar(ax=ax);ax.set_title(algo.upper()+' (same frozen weights)');ax.set_ylim(0,105);ax.tick_params(axis='x',rotation=25);ax.legend(fontsize=7)
    save(fig,'08_frozen_actors','Adaptive admission before DQN/PPO/IPPO/MAPPO; no actor-specific value learning or retraining')
    with PdfPages(out/'adaptive_gate_report.pdf') as pdf:
        for fig,name,title in figs:pdf.savefig(fig);plt.close(fig)
    verified=dict(status='passed',heldout_episodes=len(ep),convoy_records=len(cv),processed_packets=total_packets,validation_episodes=len(read(run,'validation')),controlled_episodes=len(control),network_interventions=len(replay),controlled_interventions=len(cr),superiority_supported=int(con.superiority_supported.sum()),primary_tests=primary_count,clearance_stress_episodes=len(stress),frozen_actor_episodes=len(actors),actor_secondary_supported=int(actor_con.secondary_superiority_supported.sum()),source_hash=fingerprint(),checks=['summary/raw agreement','integer/outcome invariants','elapsed time decomposition','Dijkstra bound','accepted report ages','common-survivor pairing','source fingerprint'])
    write=(out/'verification.json');write.write_text(json.dumps(verified,indent=2)+'\n')
    intro='An adaptive model-based gate estimates routing regret and evidence innovation, combines independent sender reports with aging, and learns local sender agreement; a conservative clearance quorum protects unverified warnings. It uses only public topology, declared sensor observations and packet contents. Probabilities and agreement scores are approximate model quantities, not calibrated confidence guarantees.'
    limits='Settings were selected on separate validation episodes and three validation topologies, then frozen. Held-out graphs and episode schedules are new. Existing deep baseline models are reused with frozen weights; no new offline model training is claimed. The actor adapter preserves binary feature semantics and uses a reference-planner value proxy, not learned actor-specific message value. Soft-fusion ALL uses the same risk estimator without value filtering, so an advantage over old binary ALL alone cannot establish a gate-specific benefit. Sender identity is unauthenticated; multiple forged identities defeat the clearance quorum. Single unverified clear reports cannot erase fresh warnings or lower unknown risk in VALUE-GATE. No general superiority, convergence or operational validity is claimed.'
    probe=control_summary[(control_summary['case']=='impersonated-clear')&(control_summary.delay==1)&(control_summary.loss==0)].set_index('method').delivery_rate
    finding=f"In the constructed timely single-impersonation probe, actual delivery was {100*probe['VALUE-GATE']:.1f}% for VALUE-GATE, {100*probe['COMM-ALL']:.1f}% for COMM-ALL, {100*probe['FRC']:.1f}% for FRC and {100*probe['SOFT-ALL']:.1f}% for matched SOFT-ALL. Across the broader held-out study, {int(con.superiority_supported.sum())} of 24 primary comparisons and {int(actor_con.secondary_superiority_supported.sum())} of 32 exploratory actor comparisons supported delivery superiority after their corrections. Legitimate clearance has a measured detour cost; two forged identities defeat the quorum. The probe demonstrates a bounded mechanism benefit, not general superiority."
    md='# Adaptive gate: executed results\n\n'+finding+'\n\n'+intro+'\n\n'+limits+'\n\n## Verification\n\n'+pd.DataFrame([verified]).drop(columns=['checks','source_hash']).to_markdown(index=False)+'\n\n## Locked settings\n\n```json\n'+json.dumps(selected,indent=2)+'\n```\n\n## Primary contrasts\n\n'+con[con.primary].drop(columns=['primary','lower_pp','upper_pp']).to_markdown(index=False)+'\n\n## Frozen actor contrasts (exploratory)\n\n'+actor_con.to_markdown(index=False)+'\n\n## Controlled probes: delay 1, no packet loss\n\n'+control_summary[(control_summary.delay==1)&(control_summary.loss==0)].to_markdown(index=False)+'\n'
    for _,name,title in figs:md+='\n## '+title+'\n\n!['+title+']('+name+'.png)\n'
    (out/'README.md').write_text(md)
    html='<!doctype html><html><head><meta charset="utf-8"><title>Adaptive gate results</title><style>body{font:16px system-ui;max-width:1200px;margin:auto;padding:24px}img{width:100%}table{border-collapse:collapse;font-size:12px}td,th{padding:5px;border:1px solid #ccc}</style></head><body><h1>Adaptive gate results</h1><p>'+finding+'</p><p>'+intro+'</p><p>'+limits+'</p>'+con[con.primary].to_html(index=False)
    for _,name,title in figs:html+='<h2>'+title+'</h2><img alt="'+title+'" src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
    (out/'index.html').write_text(html+'</body></html>');print(json.dumps(verified,indent=2))

if __name__=='__main__':main()
