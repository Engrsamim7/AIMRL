"""Report frozen-policy diagnostics and an exact model-validation reference."""
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
from information_value_reference import Contract,exact_cell,grid


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--audit',default='simulator/out/tabular-decision-audit-verified');ap.add_argument('--output',default='revision/journal-readiness');args=ap.parse_args()
    audit=Path(args.audit);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    verification=json.loads((audit/'verification.json').read_text());assert verification['status']=='passed'
    d=pd.read_csv(audit/'decisions.csv.gz');assert len(d)==518400
    assert d.all_frc_change.eq(0).all() and d.all_none_change.eq(0).all() and d.frc_none_change.eq(0).all()
    group=d.groupby(['sensing','mode']).agg(decisions=('t','size'),after_first_wave=('after_first_wave','sum'),
        blocked_options=('any_blocked_option','sum'),chosen_blocked=('chosen_blocked','sum'),
        report_candidates=('buffered_candidates','sum'),eligible_candidates=('eligible_candidates','sum'),
        peer_score_applications=('score_applications','sum'),all_frc_changes=('all_frc_change','sum'),all_none_changes=('all_none_change','sum'),
        q_gap_larger_than_max_penalty=('q_margin_exceeds_any_penalty','sum'),median_q_gap=('q_gap','median'))
    group.to_csv(out/'decision_audit.csv')
    d.groupby(['weight','sensing','mode','graph','case']).agg(decisions=('t','size'),after_first_wave=('after_first_wave','sum'),blocked_options=('any_blocked_option','sum'),eligible_candidates=('eligible_candidates','sum'),score_applications=('score_applications','sum'),all_frc_change=('all_frc_change','sum'),all_none_change=('all_none_change','sum')).to_csv(out/'all_audit_conditions.csv')
    cells=[];branches=[]
    for i,c in enumerate(grid()):
        row,raw=exact_cell(c);cells.append(dict(cell=i,**row));branches.extend(dict(cell=i,**r) for r in raw)
    cells=pd.DataFrame(cells);cells.to_csv(out/'exact_reference_cells.csv',index=False);pd.DataFrame(branches).to_csv(out/'exact_reference_branches.csv',index=False)
    diff=cells.frc_minus_all;counts=dict(FRC_lower_cost=int((diff < -1e-10).sum()),FRC_higher_cost=int((diff > 1e-10).sum()),equal=int((diff.abs()<=1e-10).sum()))
    figures=[]
    with PdfPages(out/'journal_readiness.pdf') as pdf:
        def save(fig,name):
            fig.tight_layout();pdf.savefig(fig);fig.savefig(out/(name+'.png'),dpi=150);plt.close(fig);figures.append(name)
        fig,axes=plt.subplots(1,2,figsize=(12,4.8))
        labels=['all decisions','eligible peer report','peer enters score','ALL vs FRC changes','ALL vs NONE changes']
        vals=[len(d),int(d.eligible_candidates.gt(0).sum()),int(d.score_applications.gt(0).sum()),int(d.all_frc_change.sum()),int(d.all_none_change.sum())]
        axes[0].bar(range(5),vals);axes[0].set_xticks(range(5),labels,rotation=30,ha='right',fontsize=8);axes[0].set_ylabel('Number of decision calls')
        for i,v in enumerate(vals):axes[0].text(i,v,f'{v:,}',ha='center',va='bottom',fontsize=9)
        z=[int(d.after_first_wave.sum()),int(d.any_blocked_option.sum()),int(d.chosen_blocked.sum())];axes[1].bar(range(3),z);axes[1].set_xticks(range(3),['at/after wave 1','blocked option offered','blocked edge chosen'],rotation=25,ha='right',fontsize=8)
        for i,v in enumerate(z):axes[1].text(i,v,f'{v:,}',ha='center',va='bottom')
        fig.suptitle('Original-family test: the gate never changes the frozen next-hop choice\nRead-only score probes; not independent fleet counterfactual outcomes',fontsize=11);save(fig,'01_decision_opportunity')
        fig,axes=plt.subplots(1,2,figsize=(11,4.5))
        for ax,(weight,cap) in zip(axes,[('code',8.),('manuscript',12.)]):
            for sensing in ['uniform','mixed']:
                v=np.sort(d[(d.weight==weight)&(d.sensing==sensing)&d.choices.gt(1)].q_gap.to_numpy());ax.plot(v,np.arange(1,len(v)+1)/len(v),label=sensing)
            ax.axvline(cap,color='black',ls='--',label='max response penalty');ax.set_title(weight+' scoring');ax.set_xlabel('Top-two raw Q gap');ax.set_ylabel('Cumulative fraction of multi-option decisions');ax.legend(fontsize=8)
        fig.suptitle('Large learned Q margins often dominate the bounded correction\nThis is one explanation; zero decision changes is the directly observed result',fontsize=11);save(fig,'02_q_response')
        fig,axes=plt.subplots(1,2,figsize=(11,4.4))
        for ax,visible in zip(axes,[False,True]):
            t=cells[cells.own_visible==visible].groupby(['rate','age']).frc_minus_all.mean().unstack().reindex(index=[0.,.1,.5],columns=[0.,2.,4.,8.]);im=ax.imshow(t,vmin=-1.5,vmax=1.5,cmap='RdBu_r',aspect='auto')
            ax.set_xticks(range(4),[0,2,4,8]);ax.set_yticks(range(3),[0,.1,.5]);ax.set_xlabel('Report age');ax.set_ylabel('Closure transition rate');ax.set_title('current local state '+('visible' if visible else 'hidden'))
            for i in range(3):
                for j in range(4):ax.text(j,i,f'{t.iloc[i,j]:.3f}',ha='center',va='center')
        fig.suptitle('Exact decision reference: filtering can help, hurt, or be redundant\nUnweighted averages over artificial grid; blue = lower FRC cost; not network results',fontsize=10)
        # Explicit margins keep the shared colorbar clear.
        fig.subplots_adjust(top=.78,bottom=.15,wspace=.35,right=.83);cax=fig.add_axes([.88,.15,.02,.63]);fig.colorbar(im,cax=cax,label='FRC minus ALL expected travel loss');pdf.savefig(fig);fig.savefig(out/'03_exact_reference.png',dpi=150);plt.close(fig);figures.append('03_exact_reference')
        examples=[('Persistent, old',Contract(accuracy=1.,rate=0.,age=8.)),('Changing, old',Contract(accuracy=1.,rate=.5,age=8.,detour=1.)),('Current own state',Contract(accuracy=1.,rate=.5,age=8.,own_visible=True))]
        fig,axes=plt.subplots(1,3,figsize=(12,4.8))
        for ax,(label,c) in zip(axes,examples):
            row,_=exact_cell(c);methods=['NONE','ALL','FRC','AGE_AWARE'];v=[row[m+'_expected_cost'] for m in methods];ax.bar(range(4),v);ax.set_xticks(range(4),methods,rotation=35,ha='right',fontsize=8);ax.set_title(label);ax.set_ylabel('Exact expected travel loss')
            for i,x in enumerate(v):ax.text(i,x,f'{x:.3f}',ha='center',va='bottom',fontsize=8)
        fig.suptitle('Model-validation examples, not manuscript performance evidence\nAGE_AWARE knows the generating law; all 432 cells are published',fontsize=11);save(fig,'04_reference_baselines')
    summary=dict(status='passed',scope='diagnostic and exact model validation; not submission-ready network superiority evidence',
        audit_episodes=verification['parent_outcomes_reproduced'],decisions=len(d),
        all_frc_action_changes=int(d.all_frc_change.sum()),all_none_action_changes=int(d.all_none_change.sum()),
        decisions_at_or_after_first_wave=int(d.after_first_wave.sum()),decisions_with_blocked_option=int(d.any_blocked_option.sum()),
        decisions_q_gap_exceeds_any_penalty=int(d.q_margin_exceeds_any_penalty.sum()),exact_cells=len(cells),exact_branches=len(branches),exact_cell_counts=counts,
        original_sources_or_models_changed=False,figures=len(figures),
        code_hashes={name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ['audit_tabular_decisions.py','information_value_reference.py','report_journal_readiness.py']})
    (out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    html='<!doctype html><meta charset="utf-8"><title>Journal-readiness diagnosis</title><style>body{font-family:system-ui;max-width:1150px;margin:2em auto}img{width:100%}</style><h1>Journal-readiness diagnosis</h1><p>Original gate never changes recorded frozen-policy actions. Exact decision examples are model validation, not new network superiority evidence. Read revision/journal-readiness-assessment.md.</p>'
    for name in figures:html+='<h2>'+name.replace('_',' ')+'</h2><img alt="'+name+'" src="data:image/png;base64,'+base64.b64encode((out/(name+'.png')).read_bytes()).decode()+'">'
    (out/'index.html').write_text(html)
    readme='''# Journal-readiness diagnostics

These files do not establish a new network performance claim. Read ../journal-readiness-assessment.md first.

- decision_audit.csv and all_audit_conditions.csv: all 518,400 routing calls from a read-only replay of the original-family study. Existing episode metrics reproduce, Q checkpoints remain fixed, and every factual score probe matches the actual next hop.
- exact_reference_cells.csv: all 432 analytical decision conditions; exact_reference_branches.csv: all 3,456 probability-weighted states. Costs are expected travel loss under a declared two-state closure model with known sensor accuracy and dynamics. They are not MARL training or field observations.
- journal_readiness.pdf and index.html: four diagnostic figures.
- verification.json: counts, scope and code hashes.

From root, with the base pinned environment: python simulator/audit_tabular_decisions.py --parent simulator/out/original-tabular-study --output simulator/out/tabular-decision-audit-reproduction --workers 4; then python simulator/report_journal_readiness.py --audit simulator/out/tabular-decision-audit-reproduction. Use fresh output directories and MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1. Original-study parent models and raw episode metrics are included in the diagnosis ZIP. See ../journal-readiness-protocol.md for the prospective grid and diagnostic limitations.
'''
    (out/'README.md').write_text(readme);print(json.dumps(summary))

if __name__=='__main__':main()
