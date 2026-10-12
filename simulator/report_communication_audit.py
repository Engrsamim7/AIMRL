"""Generate a portable opportunity-audit report from diagnostic raw records."""
import argparse
import base64
import hashlib
import json
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

from run_adaptive_experiments import fingerprint
from adaptive_gate import sigmoid, logit

ROOT = Path(__file__).resolve().parents[1]
GROUP = ['scope','family','regime','method']


def read(run, name):
    p = run/(name+'.csv')
    return pd.read_csv(p if p.exists() else p.with_suffix('.csv.gz'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run',default='simulator/out/communication-opportunity-audit')
    ap.add_argument('--output',default='revision/communication-opportunity-audit')
    args = ap.parse_args()
    run, out = Path(args.run).resolve(), Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((run/'manifest.json').read_text())
    assert manifest['status'] == 'completed' and manifest['source_hash'] == fingerprint()
    audit = ROOT/'simulator/audit_communication_opportunities.py'
    assert hashlib.sha256(audit.read_bytes()).hexdigest() == manifest['audit_script_sha256']
    packets, envelopes, decisions, convoys, batch = [read(run,n) for n in ['packets','envelopes','decisions','convoys','batch_effects']]
    assert len(packets) == int(envelopes.processed.sum())
    assert int(decisions.inbox_size.sum()) == len(packets)
    assert not packets.duplicated(['scope','family','graph','regime','episode','method','id','convoy']).any()
    assert manifest['batch_interventions'] == len(batch)
    assert len(convoys) == 3*(manifest['reproduced_network_episodes']+manifest['reproduced_control_episodes'])
    warning_effects = read(run,'warning_action_effects')
    warning_meta = json.loads((run/'warning_response_manifest.json').read_text())
    assert warning_meta['status']=='completed' and warning_meta['source_hash']==fingerprint()
    assert warning_meta['script_sha256']==hashlib.sha256((ROOT/'simulator/audit_warning_response.py').read_bytes()).hexdigest()
    assert len(warning_effects)==warning_meta['interventions']
    warning = packets.genuine & packets.blocked_report
    packets['genuine_warning'] = warning
    packets['fresh_warning'] = warning & packets.fresh
    packets['not_locally_superseded_warning'] = packets.fresh_warning & ~packets.local_newer
    packets['on_route_warning'] = packets.not_locally_superseded_warning & packets.on_without_inbox_route
    packets['current_clear_alternative_opportunity'] = packets.current_hazard_opportunity & packets.alternative_clear_now
    summary = packets.groupby(GROUP).agg(
        processed=('id','size'), genuine_warnings=('genuine_warning','sum'),
        fresh_warnings=('fresh_warning','sum'),
        not_locally_superseded=('not_locally_superseded_warning','sum'),
        on_route=('on_route_warning','sum'),
        structural_opportunities=('structural_warning_opportunity','sum'),
        current_hazard_opportunities=('current_hazard_opportunity','sum'),
        clear_alternative_opportunities=('current_clear_alternative_opportunity','sum'),
    ).reset_index()
    actions = decisions.groupby(GROUP).agg(
        decisions=('edge','size'), decisions_with_inbox=('inbox_size',lambda x:int((x>0).sum())),
        next_edge_changes_from_new_inbox=('new_inbox_changes_next_edge','sum'),
        next_edge_changes_from_all_history=('all_history_changes_next_edge','sum'),
        selected_active_edges=('selected_edge_active','sum'),
    ).reset_index()
    timing = envelopes.groupby(GROUP).agg(
        scheduled_packets=('id','size'), processed=('processed','sum'),
        receiver_finished_by_arrival=('receiver_finished_by_arrival','sum'),
        after_episode_end=('scheduled_after_episode_end','sum'),
        enters_reported_edge_before_arrival=('entered_reported_edge_before_arrival','sum'),
    ).reset_index()
    reasons = packets.groupby(GROUP+['reason']).size().reset_index(name='packets')
    causal = batch.groupby(['family','regime','method']).agg(
        interventions=('convoy','size'), changed_paths=('changed_receiver_path','sum'),
        helpful_receiver_delivery=('delta_delivery',lambda x:int((x>0).sum())),
        harmful_receiver_delivery=('delta_delivery',lambda x:int((x<0).sum())),
        changes_episode_delivery=('delta_episode_deliveries',lambda x:int((x!=0).sum())),
        changes_nominal_cost=('delta_nominal',lambda x:int((x.abs()>1e-10).sum())),
    ).reset_index()
    outcome = convoys.groupby(GROUP).agg(convoys=('convoy','size'),delivered=('delivered','sum'),destroyed=('destroyed','sum')).reset_index()
    outcome['delivery_pct'] = 100*outcome.delivered/outcome.convoys
    warning_response = warning_effects.groupby(['family','regime']).agg(
        interventions=('convoy','size'), currently_blocked=('active_at_decision','sum'),
        changed_paths=('changed_receiver_path','sum'),
        helpful_delivery=('gain_delivery',lambda x:int((x>0).sum())),
        harmful_delivery=('gain_delivery',lambda x:int((x<0).sum())),
        fewer_blocked_encounters=('delta_blocked_encounters',lambda x:int((x<0).sum())),
    ).reset_index()
    for name, frame in [('warning_funnel',summary),('action_influence',actions),('packet_timing',timing),('packet_reasons',reasons),('batch_summary',causal),('delivery_summary',outcome)]:
        frame.to_csv(out/(name+'.csv'),index=False)
    warning_response.to_csv(out/'warning_response_summary.csv',index=False)
    network_packets = packets[packets.scope=='network']
    network_actions = decisions[decisions.scope=='network']
    net_summary = summary[summary.scope=='network'].groupby('method').sum(numeric_only=True)
    net_actions = actions[actions.scope=='network'].groupby('method').sum(numeric_only=True)
    net_batch = causal.groupby('method').sum(numeric_only=True)
    plt.rcParams.update({'font.size':10,'figure.dpi':140})
    images = []
    with PdfPages(out/'communication_opportunity_report.pdf') as pdf:
        def save(fig, name):
            fig.savefig(out/(name+'.png'),bbox_inches='tight')
            fig.savefig(out/(name+'.pdf'),bbox_inches='tight')
            pdf.savefig(fig,bbox_inches='tight')
            images.append(name)
            plt.close(fig)
        stages = ['genuine_warnings','fresh_warnings','not_locally_superseded','on_route','structural_opportunities','current_hazard_opportunities']
        labels = ['Genuine block\nreports','Within TTL','Not superseded\nby own sensing','On proposed\nroute','Alternative\nexists','Still blocked\nnow']
        fig, ax = plt.subplots(figsize=(11,4.5))
        x = np.arange(len(stages))
        for i,m in enumerate(['SOFT-ALL','VALUE-GATE']):
            vals = net_summary.loc[m,stages].to_numpy(dtype=float)
            ax.bar(x+(i-.5)*.36,vals,.36,label=m)
            for xx,v in zip(x+(i-.5)*.36,vals):
                ax.text(xx,v+max(vals)*.012,str(int(v)),ha='center',fontsize=8)
        ax.set_xticks(x,labels);ax.set_ylabel('Processed warning packets')
        ax.set_title('Network warning opportunity funnel (same fixed test schedules)')
        ax.legend();ax.margins(y=.15);save(fig,'01_warning_funnel')
        fig, ax = plt.subplots(figsize=(10,4))
        groups = network_actions.groupby(['family','method']).agg(total=('edge','size'),changed=('all_history_changes_next_edge','sum'))
        families = list(network_actions.family.unique());x=np.arange(len(families))
        for i,m in enumerate(['SOFT-ALL','VALUE-GATE']):
            vals=[100*groups.loc[(f,m),'changed']/groups.loc[(f,m),'total'] for f in families]
            ax.bar(x+(i-.5)*.36,vals,.36,label=m)
            for xx,f,v in zip(x+(i-.5)*.36,families,vals):
                ax.text(xx,v+.02,f"{int(groups.loc[(f,m),'changed'])}/{int(groups.loc[(f,m),'total'])}",ha='center',fontsize=8)
        ax.set_xticks(x,families);ax.set_ylabel('Decisions with changed next edge (%)')
        ax.set_title('One-step influence of all peer history versus local-only probe')
        ax.legend();ax.set_ylim(0,max(.5,ax.get_ylim()[1]*1.35));save(fig,'02_action_influence')
        fig, axes = plt.subplots(1,2,figsize=(11,4))
        for ax,m in zip(axes,['SOFT-ALL','VALUE-GATE']):
            z=reasons[(reasons.scope=='network') & (reasons.method==m)].groupby('reason').packets.sum().sort_values()
            ax.barh(z.index,z.values);ax.set_title(m);ax.set_xlabel('Processed packets')
        fig.suptitle('Admission reasons: rejection counts alone do not establish benefit')
        fig.tight_layout();save(fig,'03_admission_reasons')
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        for ax,m in zip(axes,['SOFT-ALL','VALUE-GATE']):
            z=causal[causal.method==m].groupby('family').sum(numeric_only=True)
            x=np.arange(len(z));width=.25
            for i,(c,label) in enumerate([('changed_paths','Changed receiver path'),('helpful_receiver_delivery','Helpful delivery'),('harmful_receiver_delivery','Harmful delivery')]):
                ax.bar(x+(i-1)*width,z[c],width,label=label)
            ax.set_xticks(x,z.index,rotation=15);ax.set_title(m);ax.set_ylabel('Inbox interventions')
            ax.set_ylim(0,max(1,ax.get_ylim()[1]*1.2))
        axes[0].legend(fontsize=8);fig.suptitle('Complete-episode removal of whole inbox batches (diagnostic subset)')
        fig.tight_layout();save(fig,'04_batch_causal_replay')
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        control=actions[(actions.scope=='controlled') & (actions.family=='accurate')]
        delivery=outcome[(outcome.scope=='controlled') & (outcome.family=='accurate')]
        for ax,loss in zip(axes,[0.,.2]):
            regimes=[f'delay={d},loss={loss}' for d in [1.,4.]];x=np.arange(2)
            for i,m in enumerate(['SOFT-NC','SOFT-ALL','VALUE-GATE']):
                vals=[delivery[(delivery.regime==r)&(delivery.method==m)].delivery_pct.iloc[0] for r in regimes]
                ax.bar(x+(i-1)*.24,vals,.24,label=m)
            ax.set_xticks(x,['Delay 1','Delay 4']);ax.set_ylim(0,110)
            ax.set_title(f'Controlled accurate warnings; loss={loss}');ax.set_ylabel('Actual delivery (%)')
        axes[0].legend(fontsize=8);fig.tight_layout();save(fig,'05_controlled_timing')
        fig,axes=plt.subplots(1,2,figsize=(11,4))
        active=warning_effects[warning_effects.active_at_decision]
        axes[0].scatter(active.alternative_extra_model_cost,12*active.innovation,alpha=.7)
        limit=max(1.,active.alternative_extra_model_cost.max())
        axes[0].plot([0,limit],[0,limit],'--',color='gray',label='Equal incremental cost')
        axes[0].set_xlabel('Extra reference cost of avoiding warned edge')
        axes[0].set_ylabel('Warning increment in edge penalty (12 × innovation)')
        axes[0].set_title('Risk response in active-hazard cases');axes[0].legend(fontsize=8)
        bars=[len(warning_effects),int(warning_effects.changed_receiver_path.sum()),int((warning_effects.gain_delivery>0).sum()),int((warning_effects.gain_delivery<0).sum())]
        axes[1].bar(['Interventions','Changed\npath','Helped\ndelivery','Harmed\ndelivery'],bars)
        for i,v in enumerate(bars):axes[1].text(i,v+.3,str(v),ha='center')
        axes[1].set_title('One warning-driven detour, then resume policy')
        axes[1].set_ylim(0,max(bars)*1.15+1);fig.tight_layout();save(fig,'06_warning_response')
    # All statements below are calculated from the executed audit, not target values.
    causal_paths=int(batch.changed_receiver_path.sum())
    causal_help=int((batch.delta_delivery>0).sum());causal_harm=int((batch.delta_delivery<0).sum())
    body = '# Communication opportunity audit\n\n'
    body += f"Replayed **{manifest['reproduced_network_episodes']:,} network episodes** and **{manifest['reproduced_control_episodes']:,} controlled episodes** with the original parameters and schedules. All checked physical metrics, packet admission counts and network convoy records reproduced the archived experiment. No training or parameter selection was performed.\n\n"
    body += '## What the audit found\n\n'
    for m in ['SOFT-ALL','VALUE-GATE']:
        s=net_summary.loc[m];a=net_actions.loc[m]
        body += f"- **{m}:** {int(s.genuine_warnings):,} genuine blocked-edge reports; {int(s.not_locally_superseded):,} fresh reports not superseded by own sensing; {int(s.on_route):,} concerned the proposed route; {int(s.current_hazard_opportunities):,} met the current-hazard opportunity definition. All peer history changed the next edge in {int(a.next_edge_changes_from_all_history):,}/{int(a.decisions):,} decisions; new inboxes changed it in {int(a.next_edge_changes_from_new_inbox):,} decisions.\n"
    body += f"- **Whole-inbox causal replay:** {len(batch):,} interventions, {causal_paths:,} changed receiver paths, {causal_help:,} helpful and {causal_harm:,} harmful receiver delivery effects. This is a declared subset, not every episode.\n\n"
    body += f"- **Warning-driven action intervention:** {len(warning_effects):,} structural warning opportunities in exogenous regimes; taking one public-weight next hop that avoids the warned edge changed {int(warning_effects.changed_receiver_path.sum()):,} receiver paths, helped receiver delivery in {int((warning_effects.gain_delivery>0).sum()):,} cases and harmed it in {int((warning_effects.gain_delivery<0).sum()):,} cases. This targeted mechanism probe is not an algorithm comparison.\n\n"
    params=json.loads((ROOT/'simulator/out/adaptive-gate-v2/selected.json').read_text())['parameters']
    initial_trust=2/3;credibility=.5+.49*initial_trust
    single_probability=sigmoid(logit(.05)+logit(credibility))
    body += '## Why warnings can fail to change routes\n\n'
    body += f"With the declared 0.05 block prior and initial sender agreement 2/3, even a confidence-1 warning with no age or distance decay gives a single-report probability of only **{single_probability:.4f}**. Decay reduces its increment. The chosen risk-aversion parameter is {params['risk_aversion']}; the edge penalty is 12 times the estimated risk. This is a model assumption, not calibrated hazard probability. A warning therefore need not overcome the reference cost of a detour. The figure compares the observed innovation penalty and detour cost in currently blocked cases; other simultaneous evidence can also affect a decision.\n\n"
    body += 'The next model should be tested for whether it responds to useful observations before testing whether filtering adds value. Calibrate report interpretation and predicted decision benefit on new training data; evaluate a stronger matched ALL estimator as well as the gate. Predefine a sweep of scout lead time, sensing overlap, warning delay and hazard persistence, including cases where communication is redundant or late. Do not train on this diagnostic test set or select only favorable scenarios.\n\n'
    body += '## Definitions and limits\n\n'
    body += ('The warning funnel counts packets, not independent episodes. A structural warning opportunity requires a genuine blocked report within the common TTL, no equally new or newer fresh own observation, membership in the reference route without the current inbox, and an alternative route avoiding that edge. A current-hazard opportunity additionally requires that the reported edge is actually blocked at decision time. The separate clear-alternative count requires the alternative to avoid all currently active blocks. These last two labels use evaluator-only state; the actor never receives them. This is an instantaneous diagnostic, not a promise that the warning or alternative stays valid until traversal.\n\n'
             'The without-inbox probe retains old admitted reports. The local-only probe removes peer reports, warning anchors, agreement feedback and sender reputation, while preserving factual previous movement and own observations. These are isolated one-decision probes, not complete no-communication trajectories. Complete SOFT-NC trajectories are also reproduced.\n\n'
             'Whole-inbox causal replay removes all packets waiting at one routing decision, retains earlier reports, and runs both futures to completion. Exact simulator/event/RNG state is copied, and the entire shared-time attack schedule is checked. It covers all nonempty inboxes in the first five episodes on the original graph and first graph of each synthetic family, in the three exogenous regimes, for SOFT-ALL and VALUE-GATE. Reactive/targeted cases appear only in observational and one-step diagnostics.\n\n'
             'The warning-response probe selects every structural warning opportunity for SOFT-ALL in exogenous network regimes, collapsing duplicate warnings for the same decision and edge. It changes only the next hop to the public-weight shortest route avoiding the reported edge, then resumes the original policy. It does not force continued avoidance after later decisions. Genuine labels define the diagnostic population; this is not a deployable perfect-message selector. Gain values are intervention minus factual, whereas batch delta values are factual minus suppression. Exogenous attack schedules are checked in both probes.\n\n'
             'Envelope logs cover scheduled packets; lost packets are excluded. Packets scheduled after episode completion, arriving after receiver completion, or never consumed at a decision are retained separately. The timing table counts reported-edge entry before arrival on the factual path; a report about an untraversed edge is not classified as late. Admission does not save transmission bandwidth: both communicating methods broadcast before filtering.\n\n'
             'This audit reuses previously inspected test schedules for diagnosis. It must not be used as training data for a later claimed fresh test. A subsequent design needs new training/validation/test schedules and a preregistered range of conditions. Genuine reports describe revealed observations; they are not perfect ground truth.\n\n')
    body += '## Warning funnel by network family and regime\n\n'+summary[summary.scope=='network'].drop(columns='scope').to_markdown(index=False)+'\n\n'
    body += '## Action influence\n\n'+actions.to_markdown(index=False)+'\n\n'
    body += '## Batch causal effects\n\n'+causal.to_markdown(index=False)+'\n\n'
    body += '## Warning-driven action effects\n\n'+warning_response.to_markdown(index=False)+'\n\n'
    body += '## Packet timing\n\n'+timing.to_markdown(index=False)+'\n\n'
    body += '## Reproduce\n\n```bash\nbash setup_local.sh\ncd simulator\n../.venv/bin/python audit_communication_opportunities.py --output out/communication-opportunity-audit-new\n../.venv/bin/python audit_warning_response.py --run out/communication-opportunity-audit-new\ncd ..\nMPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_communication_audit.py --run simulator/out/communication-opportunity-audit-new --output revision/communication-opportunity-audit-new\n```\n\n'
    body += f"Original experiment source hash: `{manifest['source_hash']}`. Audit script SHA256: `{manifest['audit_script_sha256']}`.\n"
    (out/'README.md').write_text(body)
    html='<!doctype html><html><meta charset="utf-8"><title>Communication opportunity audit</title><style>body{font:16px system-ui;max-width:1200px;margin:2rem auto;padding:1rem}img{width:100%}pre{white-space:pre-wrap}</style><h1>Communication opportunity audit</h1><p>Diagnostic replay; no new superiority claim. Read README.md for definitions, raw counts and limitations.</p>'
    for name in images:
        html+=f'<h2>{name.replace("_"," ")}</h2><img src="data:image/png;base64,{base64.b64encode((out/(name+".png")).read_bytes()).decode()}" alt="{name}">'
    html+='</html>'
    (out/'index.html').write_text(html)
    verification=dict(status='passed',network_episodes=manifest['reproduced_network_episodes'],control_episodes=manifest['reproduced_control_episodes'],processed_packets=len(packets),scheduled_envelopes=len(envelopes),decisions=len(decisions),batch_interventions=len(batch),network_current_hazard_opportunities=int(network_packets.current_hazard_opportunity.sum()),network_next_edge_changes=int(network_actions.all_history_changes_next_edge.sum()),batch_changed_paths=causal_paths,batch_helpful=causal_help,batch_harmful=causal_harm,warning_action_interventions=len(warning_effects),warning_action_helpful=int((warning_effects.gain_delivery>0).sum()),warning_action_harmful=int((warning_effects.gain_delivery<0).sum()),figures=len(images),source_hash=manifest['source_hash'])
    (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps(verification))


if __name__=='__main__':
    main()
