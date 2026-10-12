"""Audit executed follow-up records and make shareable plots/HTML/PDF from CSV."""
import argparse,base64,hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ammarl2.reviewer import original_graph,ReviewerSim,m4_sensing
from ammarl2.metrics import episode_metrics
from run_reviewer_revision import source_hash,scenario,heuristics


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='out/reviewer-revision-v2');ap.add_argument('--output',default='../revision/reviewer-revision-results');a=ap.parse_args()
    run=Path(a.input).resolve();dest=Path(a.output).resolve();dest.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((run/'pipeline.json').read_text());assert manifest['status']=='completed' and manifest['source_hash']==source_hash()
    ep=pd.read_csv(run/'episodes.csv');cv=pd.read_csv(run/'convoys.csv');messages=pd.read_csv(run/'messages.csv');summary=pd.read_csv(run/'summary.csv');con=pd.read_csv(run/'contrasts.csv');train=pd.concat([pd.read_csv(f) for f in (run/'models').glob('*_training.csv')],ignore_index=True)
    keys=['scenario','method','training_seed','episode']
    assert len(ep)==len(ep[keys].drop_duplicates())
    assert len(cv)==3*len(ep)
    raw=cv.groupby(keys).agg(delivery=('delivered','mean'),blocked=('blocked_enc','sum'),nominal=('nominal','mean')).reset_index()
    joined=ep.merge(raw,on=keys,validate='one_to_one')
    assert np.allclose(joined.delivery_rate,joined.delivery) and np.allclose(joined.blocked_encounters_total,joined.blocked)
    assert np.allclose(joined.nominal_all_mean,joined.nominal)
    for col in ['delivered','destroyed','censored','blocked_enc','surprise_blocked_enc']:
        assert np.equal(cv[col],np.floor(cv[col])).all()
    assert (cv.delivered+cv.destroyed+cv.censored).eq(1).all()
    survivors=cv[cv.delivered==1];assert(survivors.nominal>=survivors.nominal_optimal-1e-8).all()
    assert np.allclose(cv.elapsed,cv.travel+cv.wait+cv.service,atol=1e-7)
    assert messages.age.ge(0).all()
    accepted=messages[messages.reason=='accepted'];ttl=8.
    assert accepted.age.le(ttl+1e-8).all()
    common=[]
    for name in ep.scenario.unique():
        for left,right in [('GATE-reachable','ALL')]+[(x+'-gate',x+'-all') for x in ['DQN','PPO','IPPO','MAPPO']]:
            pa=cv[(cv.scenario==name)&(cv.method==left)];pb=cv[(cv.scenario==name)&(cv.method==right)]
            paired=pa.merge(pb,on=['training_seed','episode','convoy','target','depart_t'],suffixes=('_a','_b'),validate='one_to_one');assert len(paired)==len(pa)==len(pb)
            both=paired[(paired.delivered_a==1)&(paired.delivered_b==1)]
            common.append(dict(scenario=name,comparison=left+' minus '+right,common_delivered=len(both),nominal_difference=float((both.nominal_a-both.nominal_b).mean()),realized_difference=float((both.realized_a-both.realized_b).mean())))
    pd.DataFrame(common).to_csv(dest/'common_survivor_contrasts.csv',index=False)
    for f in ['summary.csv','contrasts.csv','gate_selection.json']:(dest/f).write_bytes((run/f).read_bytes())
    figs=[]
    def save(fig,name,title):
        fig.tight_layout();fig.savefig(dest/(name+'.png'),dpi=180);fig.savefig(dest/(name+'.pdf'));figs.append((fig,name,title))
    scenarios=list(ep.scenario.unique());fig,axs=plt.subplots(2,2,figsize=(13,9),sharey=True)
    for ax,name in zip(axs.flat,scenarios):
        sub=summary[summary.scenario==name];ax.bar(sub.method,100*sub.delivery,color=['#326fa8' if 'gate' not in m.lower() else '#df9540' for m in sub.method]);ax.set_title(name);ax.tick_params(axis='x',rotation=75,labelsize=8);ax.set_ylim(0,105);ax.set_ylabel('Actual delivery (%)')
    save(fig,'01_delivery','Held-out delivery: original topology')
    fig,axs=plt.subplots(2,2,figsize=(11,8),sharex=True)
    for ax,name in zip(axs.flat,scenarios):
        sub=con[con.scenario==name];y=np.arange(len(sub));ax.errorbar(sub.difference_pp,y,xerr=[sub.difference_pp-sub.lower_pp,sub.upper_pp-sub.difference_pp],fmt='o');ax.axvline(0,color='black',lw=1);ax.set_yticks(y,sub.group);ax.set_title(name);ax.set_xlabel('Gate minus ALL (percentage points)')
    save(fig,'02_gate_contrasts','Paired uncertainty: episodes and training seeds on fixed topology')
    fig,axs=plt.subplots(1,2,figsize=(12,4))
    for algo in train.algo.unique():
        sub=train[train.algo==algo].groupby('episode')[['delivery_rate','last_loss']].mean()
        axs[0].plot(sub.index,100*sub.delivery_rate.rolling(20,min_periods=1).mean(),label=algo.upper())
        axs[1].plot(sub.index,sub.last_loss.rolling(20,min_periods=1).mean(),label=algo.upper())
    axs[0].set_ylabel('Training delivery (20-episode rolling %, five seeds)');axs[1].set_ylabel('Last optimizer loss (algorithm-specific scale)')
    for ax in axs:ax.set_xlabel('Executed training episode');ax.legend()
    save(fig,'03_training','Executed training diagnostics; no convergence guarantee')
    cc=pd.read_csv(run/'cc2_episodes.csv');fig,axs=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,loss in zip(axs,[0.,.2]):
        for mode in ['none','all','gate']:
            sub=cc[(cc.loss==loss)&(cc['mode']==mode)].groupby('delay').delivery_rate.mean();ax.plot(sub.index,100*sub,'o-',label=mode)
        ax.set_title(f'Packet loss {loss:.0%}');ax.set_xlabel('Message delay (model units)');ax.legend()
    axs[0].set_ylabel('Actual delivery (%)');save(fig,'04_cc2','Controlled scout/follower fixture: actual interdiction and declared blind corridors')
    ab=pd.read_csv(run/'ablation.csv',dtype={'mask':str});fig,axs=plt.subplots(1,2,figsize=(12,4),sharey=True)
    for ax,name in zip(axs,['mixed-disrupted','mixed-reactive']):
        for strength in [0.,8.,12.]:
            sub=ab[(ab.scenario==name)&(ab.strength==strength)].groupby('mask').delivery_rate.mean();ax.plot(sub.index,100*sub,'o-',label=f'response {strength:g}')
        ax.set_title(name);ax.set_xlabel('Freshness / relevance / confidence switches');ax.legend()
    axs[0].set_ylabel('Actual delivery (%)');save(fig,'05_ablation','Filtering versus response strength; zero-strength invariance checked')
    fig,axs=plt.subplots(1,2,figsize=(11,4))
    reasons=messages.groupby(['scenario','reason']).size().unstack(fill_value=0);reasons.div(reasons.sum(axis=1),axis=0).plot.bar(stacked=True,ax=axs[0]);axs[0].tick_params(axis='x',rotation=35);axs[0].set_ylabel('Fraction of processed packets')
    packet=summary[summary.method.isin(['NC','ALL','GATE-reachable'])].pivot(index='scenario',columns='method',values='sent');packet.plot.bar(ax=axs[1]);axs[1].tick_params(axis='x',rotation=35);axs[1].set_ylabel('Attempted genuine transmissions / episode')
    save(fig,'06_communication','Admission is not bandwidth reduction; routing can change later transmissions')
    # Fixed first held-out episode, validated against raw evaluation before plotting.
    selection=json.loads((run/'gate_selection.json').read_text());g=original_graph();cfg,mixed=scenario('mixed-disrupted');policy=heuristics(selection['eta'],selection['kappa'])[-1]
    sim=ReviewerSim(g,cfg,policy,3100000,m4_sensing(g,mixed));res=sim.run()
    expected=cv[(cv.scenario=='mixed-disrupted')&(cv.method=='GATE-reachable')&(cv.episode==0)].set_index('convoy')
    for row in res['rows']:
        for field in ['delivered','destroyed','censored','nominal','elapsed','blocked_enc']:
            assert np.isclose(row[field],expected.loc[row['convoy'],field])
    positions={0:(0,1.5)}
    for i in range(1,13):positions[i]=(1+(i-1)//4,(i-1)%4)
    for i in range(13,19):positions[i]=(4,(i-13)*.6)
    fig,ax=plt.subplots(figsize=(10,5))
    for e in range(g.m):
        x,y=positions[int(g.src[e])];u,v=positions[int(g.dst[e])];ax.plot([x,u],[y,v],color='#ddd',lw=.7,zorder=1)
    for node,(x,y) in positions.items():ax.scatter(x,y,color='#eee',edgecolor='black',s=220,zorder=3);ax.text(x,y,str(node),ha='center',va='center',zorder=4)
    colors=['#2366ac','#db7b24','#33915b']
    for convoy,color in zip(sim.cv,colors):
        for e in convoy.path:
            x,y=positions[int(g.src[e])];u,v=positions[int(g.dst[e])];ax.plot([x,u],[y,v],color=color,lw=2,alpha=.7,zorder=2)
        ax.plot([],[],color=color,label=f'Convoy {convoy.id}: '+('delivered' if convoy.delivered else 'failed/censored'))
        for t,e,blocked in convoy.entries:
            if blocked:
                x,y=positions[int(g.src[e])];u,v=positions[int(g.dst[e])];ax.scatter((x+u)/2,(y+v)/2,marker='x',s=90,color=color,zorder=5)
    ax.legend(loc='upper left');ax.set_title('Original topology: fixed first mixed-disrupted episode\nX marks actual blocked entries; node layout is schematic');ax.axis('off');save(fig,'07_original_routes','Illustrative routes checked against raw held-out records')
    scaling=pd.read_csv(run/'scaling.csv');fig,axs=plt.subplots(1,2,figsize=(11,4))
    for method,sub in scaling.groupby('method'):
        means=sub.groupby('nodes')[['seconds','delivery_rate']].mean();axs[0].plot(means.index,means.seconds,'o-',label=method);axs[1].plot(means.index,100*means.delivery_rate,'o-',label=method)
    axs[0].set_ylabel('Episode runtime (shared-machine seconds)');axs[1].set_ylabel('Actual delivery (%)')
    for ax in axs:ax.set_xlabel('Synthetic graph nodes');ax.legend(fontsize=7)
    save(fig,'08_scaling','Descriptive heuristic scaling, two schedules; fixed convoy population and attack budget')
    fixture_folder=run/'gate-fixtures'
    fixture_manifest=json.loads((fixture_folder/'manifest.json').read_text())
    assert fixture_manifest['status']=='completed' and fixture_manifest['source_hash']==source_hash()
    assert fixture_manifest['fixture_source_sha256']==hashlib.sha256((Path(__file__).parent/'run_gate_fixtures.py').read_bytes()).hexdigest()
    fixture_summary=pd.read_csv(fixture_folder/'summary.csv')
    fixture_raw=pd.read_csv(fixture_folder/'convoys.csv')
    fixture_ep=pd.read_csv(fixture_folder/'episodes.csv')
    assert len(fixture_raw)==3*len(fixture_ep)
    fixture_means=fixture_raw.groupby(['case','mode']).delivered.mean().reset_index()
    checked=fixture_summary.merge(fixture_means,on=['case','mode'],validate='one_to_one')
    assert np.allclose(checked.delivery_rate,checked.delivered)
    fixture_replay=pd.read_csv(fixture_folder/'replay.csv')
    fixture_summary.to_csv(dest/'controlled_filtering_summary.csv',index=False)
    fig,ax=plt.subplots(figsize=(11,4))
    data=fixture_summary.pivot(index='case',columns='mode',values='delivery_rate')*100
    data.plot.bar(ax=ax);ax.tick_params(axis='x',rotation=15);ax.set_ylabel('Actual delivery (%)');ax.set_ylim(0,105)
    ax.set_title('Constructed filtering probes: low-confidence false reports rejected; high-confidence false reports pass')
    save(fig,'09_controlled_filtering','Filtering benefit and failure boundary, fixed confidence threshold 0.6')
    with PdfPages(dest/'reviewer_revision_report.pdf') as pdf:
        for fig,name,title in figs:pdf.savefig(fig);plt.close(fig)
    replay=pd.read_csv(run/'m4_replay.csv');ccreplay=pd.read_csv(run/'cc2_replay.csv')
    audit=dict(status='passed',training_episodes=len(train),models=len(list((run/'models').glob('*.pt'))),heldout_episodes=len(ep),convoy_records=len(cv),processed_messages=len(messages),cc2_episodes=len(cc),ablation_episodes=len(ab),m4_packet_interventions=len(replay),cc2_packet_interventions=len(ccreplay),controlled_filtering_episodes=len(fixture_ep),controlled_packet_interventions=len(fixture_replay),checks=['raw/summary agreement','integer counts and exhaustive outcome categories','Dijkstra bound','time decomposition','packet timestamp/TTL validity','matched common-survivor schedules','illustrative route raw-record match'],source_hash=source_hash())
    (dest/'verification.json').write_text(json.dumps(audit,indent=2)+'\n')
    intro='Reviewer follow-up on the recovered original network. Twenty fresh models were trained with ALL communication and evaluated with frozen weights in none/all/gate modes. Five training seeds, 300 episodes per model, separate validation and 50 held-out schedules per scenario. This is a scientific diagnostic, not reproduction of submitted numbers or proof of general gate superiority.'
    limits='One original topology; fixed-weight inference contrasts; gate thresholds selected on heuristic validation; no convergence proof or full algorithm-specific hyperparameter tuning. CC2 is an explicit sensing-asymmetry fixture with actual binary attacks. Scaling is heuristic inference only. Communication counts distinguish transmissions from admission. Original manuscript values and generated curves are excluded.'
    md='# Executed reviewer revision\n\n'+intro+'\n\n'+pd.DataFrame([audit]).drop(columns=['checks','source_hash']).to_markdown(index=False)+'\n\n## Held-out delivery\n\n'+summary[['scenario','method','delivery']].to_markdown(index=False)+'\n\n## Gate contrasts\n\n'+con.to_markdown(index=False)+'\n\n## Controlled filtering probes\n\n'+fixture_summary.to_markdown(index=False)+'\n\nThese deliberately constructed cases demonstrate a filtering benefit for low-confidence false clear reports and failure against high-confidence false clear reports. They do not establish general superiority.\n\n'+limits+'\n'
    for _,name,title in figs:md+='\n## '+title+'\n\n!['+title+']('+name+'.png)\n'
    (dest/'README.md').write_text(md)
    html='<!doctype html><html><head><meta charset="utf-8"><title>Reviewer revision results</title><style>body{font:16px system-ui;max-width:1150px;margin:auto;padding:24px}img{width:100%}table{border-collapse:collapse;font-size:13px}td,th{padding:5px;border:1px solid #ccc}</style></head><body><h1>Executed reviewer revision</h1><p>'+intro+'</p><p>'+limits+'</p>'+con.to_html(index=False)
    for _,name,title in figs:html+='<h2>'+title+'</h2><img alt="'+title+'" src="data:image/png;base64,'+base64.b64encode((dest/(name+'.png')).read_bytes()).decode()+'">'
    (dest/'index.html').write_text(html+'</body></html>')
    print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
