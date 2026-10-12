"""All four cover-traffic conditions, with corrected paired effects."""
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
import report_research_study as paired
from run_cover_traffic_stress import fingerprint,CONDITIONS

def read(run,name):
    p=run/(name+'.csv');return pd.read_csv(p if p.exists() else p.with_suffix('.csv.gz'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',default='simulator/out/cover-traffic-stress');ap.add_argument('--output',default='revision/cover-traffic-results');a=ap.parse_args()
    run,out=Path(a.run).resolve(),Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((run/'pipeline.json').read_text());assert meta['status']=='completed' and meta['source_hash']==fingerprint()
    df,raw=read(run,'episodes'),read(run,'convoys');assert len(df)==28000 and len(raw)==140000
    assert (df.n_delivered+df.n_destroyed+df.n_censored).eq(5).all()
    assert (raw.delivered+raw.destroyed+raw.censored).eq(1).all()
    assert np.allclose(raw.elapsed,raw.travel+raw.service+raw.wait)
    keys=['graph','algo','seed','case','episode','method']
    counted=raw.groupby(keys).delivered.sum();expected=df.set_index(keys).n_delivered.sort_index()
    assert expected.index.equals(counted.index) and expected.eq(counted).all()
    pairkeys=['graph','algo','seed','case','episode','convoy']
    assert raw.pivot(index=pairkeys,columns='method',values='depart_t').nunique(axis=1).eq(1).all()
    assert raw.pivot(index=pairkeys,columns='method',values='target').nunique(axis=1).eq(1).all()
    summary=df.groupby(['algo','case','method']).agg(episodes=('episode','size'),delivery=('delivery_rate','mean'),follower_delivery=('follower_delivery','mean'),utility=('utility_mean','mean'),time=('realized_delivered_mean','mean'),true_admitted=('true_accepted','sum'),forged_admitted=('spoof_accepted','sum')).reset_index()
    summary['delivery_pct']=100*summary.delivery;summary['follower_delivery_pct']=100*summary.follower_delivery
    summary.to_csv(out/'summary.csv',index=False);paired.CORRECTION=198;contrasts=[];survivors=[]
    cases=[x[0] for x in CONDITIONS];actors=['planner','dqn','mappo'];methods=['NC','ALL','FRC','SAFE-ALL','VALUE']
    for ai,algo in enumerate(actors):
        for ci,case in enumerate(cases):
            z=df[(df.algo==algo)&(df.case==case)].pivot(index=['graph','seed','episode'],columns='method',values='delivery_rate').sort_index()
            seeds=1 if algo=='planner' else 3
            for bi,base in enumerate(['ALL','FRC','SAFE-ALL']):
                diff=(z.VALUE-z[base]).to_numpy().reshape(10,seeds,20)
                mean,lo,hi=paired.intervals(diff,seed=919+ai*100+ci*3+bi,draws=200000)
                contrasts.append(dict(algo=algo,case=case,baseline=base,difference_pp=100*mean,lower_pp=100*lo,upper_pp=100*hi,superiority_supported=lo>0,disadvantage_supported=hi<0))
                va=raw[(raw.algo==algo)&(raw.case==case)&(raw.method=='VALUE')]
                vb=raw[(raw.algo==algo)&(raw.case==case)&(raw.method==base)]
                both=va.merge(vb,on=pairkeys,suffixes=('_value','_base'),validate='one_to_one')
                both=both[both.delivered_value.eq(1)&both.delivered_base.eq(1)]
                survivors.append(dict(algo=algo,case=case,baseline=base,common_survivors=len(both),nominal_difference=(both.nominal_value-both.nominal_base).mean(),elapsed_difference=(both.realized_value-both.realized_base).mean()))
    contrasts=pd.DataFrame(contrasts);contrasts.to_csv(out/'contrasts.csv',index=False);pd.DataFrame(survivors).to_csv(out/'common_survivors.csv',index=False)
    images=[];plt.rcParams.update({'font.size':10,'figure.dpi':140})
    with PdfPages(out/'cover_traffic_report.pdf') as pdf:
        def save(fig,name):
            fig.savefig(out/(name+'.png'),bbox_inches='tight');fig.savefig(out/(name+'.pdf'),bbox_inches='tight');pdf.savefig(fig,bbox_inches='tight');images.append(name);plt.close(fig)
        for metric,title,name in [('delivery_pct','Actual delivery (%)','01_delivery'),('follower_delivery_pct','Follower delivery (%)','02_follower_delivery'),('utility','Receiver utility / convoy','03_utility')]:
            fig,axes=plt.subplots(3,1,figsize=(11,10),sharex=True)
            for ax,algo in zip(axes,actors):
                z=summary[summary.algo==algo];x=np.arange(4)
                for mi,m in enumerate(methods):
                    vals=z[z.method==m].set_index('case').reindex(cases)[metric];ax.bar(x+(mi-2)*.16,vals,.16,label=m)
                ax.set_title(algo.upper());ax.set_ylabel(title)
                if metric!='utility':ax.set_ylim(0,105)
            axes[0].legend(ncol=5,loc='lower center',bbox_to_anchor=(.5,1.1));axes[-1].set_xticks(range(4),[c.replace('-','\n') for c in cases]);fig.tight_layout();save(fig,name)
        fig,axes=plt.subplots(1,3,figsize=(12,5),sharey=True)
        limit=max(10.,float(np.abs(contrasts.difference_pp).max()))
        for ax,algo in zip(axes,actors):
            z=contrasts[contrasts.algo==algo].pivot(index='case',columns='baseline',values='difference_pp').reindex(cases)[['ALL','FRC','SAFE-ALL']]
            im=ax.imshow(z,cmap='RdBu',vmin=-limit,vmax=limit,aspect='auto')
            for i,c in enumerate(cases):
                for j,b in enumerate(z.columns):
                    r=contrasts[(contrasts.algo==algo)&(contrasts.case==c)&(contrasts.baseline==b)].iloc[0]
                    ax.text(j,i,f'{r.difference_pp:+.1f}'+('*' if r.superiority_supported else '†' if r.disadvantage_supported else ''),ha='center',va='center',fontsize=9,color='white' if abs(r.difference_pp)>.55*limit else 'black')
            ax.set_xticks(range(3),z.columns);ax.set_yticks(range(4),cases);ax.set_title(algo.upper())
        fig.colorbar(im,ax=axes.ravel().tolist(),shrink=.75,label='Difference in percentage points');fig.suptitle('Frozen-model cover stress: * corrected benefit, † disadvantage (198-test correction)');save(fig,'04_corrected_effects')
    positive=contrasts[contrasts.superiority_supported];adverse=contrasts[contrasts.disadvantage_supported]
    body='# Balanced cover-traffic stress: frozen-model results\n\n'
    body+=f"Completed **28,000 new evaluation episodes**, **140,000 convoy records**, and all four declared stress conditions with unchanged routing actors, value models and inherited numeric settings. **{len(positive)} of 36 comparisons supported delivery superiority** after a conservative 198-test correction; **{len(adverse)} supported a disadvantage**. The correction accounts for 162 earlier and 36 current comparisons.\n\n"
    body+=('The earlier attacker preferentially sent clear statements about active blocks. Strong neural actors could exploit report presence as a clue even when the statement was false. This stress distributes forged targets uniformly over public potential hazard corridors and draws block/open payloads with a fair coin, independently of live truth and receiver plans. Forged reports may be correct by coincidence; forged origin is not equivalent to false content. Confidence matches honest reports. Ninety percent of forged packets claim a convoy identity. Rates 2/6 and delays 1/4 are crossed; loss is 0.1 and physical scout lead is 4.\n\n'
             'This is a **frozen-model corruption-shift robustness test** on new layouts and tapes. Models were not retrained on cover traffic. It establishes only the named stress conditions and baselines; it does not establish superiority after every baseline retrains on this new attacker. Costs, sensors, targets, departures, exogenous blocks and environment tapes are matched across methods. All four conditions are published. No forged origin, simulator attack state or future outcome enters the gate.\n\n')
    body+='Loss 0.1 applies to honest broadcasts. Forged packets model receiver-side injection and do not undergo stochastic transport loss; this assumption is common to every method.\n\n'
    body+='## Supported comparisons\n\n'+(positive.to_markdown(index=False) if len(positive) else 'None after correction.')+'\n\n'
    body+='## All performance results\n\n'+summary[['algo','case','method','episodes','delivery_pct','follower_delivery_pct','utility','time']].to_markdown(index=False)+'\n\n'
    body+='## All paired comparisons\n\n'+contrasts.to_markdown(index=False)+'\n\n'
    body+=('The shared interpreter and guarded actor-specific value model are unchanged from the guarded study. NC, ALL, tuned FRC, SAFE-ALL and VALUE use identical weights within each actor/seed. Two scouts and three followers count in full delivery; follower-only rates use the three followers. Claims of gate-specific utility beyond simple conservative filtering require the SAFE-ALL comparison, not just ALL/FRC. A high-confidence forged block can induce detours under warning preservation; common-survivor cost/time effects are retained in common_survivors.csv. This is an explicit safety/efficiency tradeoff, not superiority on every KPI.\n\n'
             'Intervals use 200,000 graph/episode clustered, training-seed-crossed paired bootstrap draws and two-sided Bonferroni tails over 198 tests. Higher draw count improves resolution in the extreme corrected tails. Three training seeds and ten small structured layouts limit extrapolation. The original-topology transfer and initial unconstrained failures remain in the earlier reports. Packet communication counts are retained per episode; individual cover packet logs are not exported. Receiver-side admission does not reduce transmission bandwidth.\n\n')
    body+='## Reproduce\n\nRun the first and guarded studies using the commands in ../guarded-research-results/README.md, then:\n\n```bash\ncd simulator\n../.venv/bin/python run_cover_traffic_stress.py --parent out/guarded-research-study-new --output out/cover-traffic-stress-new --workers 3\ncd ..\nMPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_cover_stress.py --run simulator/out/cover-traffic-stress-new --output revision/cover-traffic-results-new\n```\n'
    (out/'README.md').write_text(body)
    html='<!doctype html><html><meta charset="utf-8"><title>Cover traffic stress</title><style>body{font:16px system-ui;max-width:1200px;margin:2rem auto;padding:1rem}img{width:100%}</style><h1>Frozen-model cover traffic stress</h1><p>Read README.md for corrected effects, all conditions and limits.</p>'
    for name in images:html+=f'<h2>{name.replace("_"," ")}</h2><img src="data:image/png;base64,{base64.b64encode((out/(name+".png")).read_bytes()).decode()}" alt="{name}">'
    (out/'index.html').write_text(html+'</html>')
    check=dict(status='passed',source_hash=fingerprint(),evaluation_episodes=28000,convoys=140000,new_training_episodes=0,primary_tests=36,correction_tests=198,bootstrap_draws=200000,supported_positive=len(positive),supported_adverse=len(adverse),figures=len(images),matched_schedules=True,integer_counts_verified=True)
    (out/'verification.json').write_text(json.dumps(check,indent=2)+'\n');print(json.dumps(check))

if __name__=='__main__':main()
