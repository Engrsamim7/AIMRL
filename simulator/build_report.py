"""Build an offline, self-contained HTML report and GitHub-readable results."""
import argparse
import base64
import html
import json
from pathlib import Path
import pandas as pd

TITLES = {
    '00_overview':'Results overview', '01_training':'Training curves',
    '02_scenario_delivery':'Held-out delivery and uncertainty',
    '03_gate_contrasts':'Paired gate-versus-all effects',
    '04_scaling':'Network-size transfer and CPU runtime',
    '05_ablation':'Filtering and response-strength ablation',
    '06_message_replay':'Exact single-message replay',
    '07_network_routes':'Illustrative network and realized convoy routes',
    '08_episode_timeline':'Illustrative travel, queues, service and packet decisions',
}


def main(root, figures):
    from visualize_episode import main as visualize
    visualize(root,figures)
    summary=json.loads((figures/'summary.json').read_text())
    manifest=json.loads((root/'train/manifest.json').read_text())
    args=manifest['arguments']
    results=pd.read_csv(figures/'scenario_summary.csv')
    contrasts=pd.read_csv(figures/'paired_contrasts.csv')
    curves=pd.read_csv(root/'train/training_curves.csv')
    windows=[]
    for (algo,comm,seed),group in curves.groupby(['algo','comm','seed']):
        group=group.sort_values('episode')
        window=min(50,len(group)//2)
        windows.append(dict(algo=algo,comm=comm,seed=int(seed),window_episodes=window,
                            preceding_window_delivery=float(group.iloc[-2*window:-window].delivery_rate.mean()),
                            final_window_delivery=float(group.iloc[-window:].delivery_rate.mean()),
                            optimizer_updates=int(group.optimizer_updates.iloc[-1]),
                            decisions=int(group.decisions.sum())))
    pd.DataFrame(windows).to_csv(figures/'training_window_diagnostics.csv',index=False)
    values=results.pivot(index='method',columns='scenario',values='delivery')[['random','spoof','reactive']]*100
    values.columns=['Random (%)','Disrupted/spoofed (%)','Reactive/targeted (%)']
    replay=pd.read_csv(root/'fir/single_message_effects.csv')
    replay_table=replay.groupby('method').agg(packets=('message_id','size'),
                changed_paths=('changed_receiver_path','sum'),
                helped_receiver=('delta_delivery',lambda v:(v>0).sum()),
                harmed_receiver=('delta_delivery',lambda v:(v<0).sum()),
                changed_episode_delivery=('delta_episode_deliveries',lambda v:(v!=0).sum()))
    replay_table.to_csv(figures/'replay_summary.csv')
    note=(f"{summary['checkpoints']} models; {args['episodes']} episodes/model; "
          f"{len(args['seeds'])} training seeds; {args['convoys']} convoys/episode. "
          'Synthetic exploratory results. A fixed budget and smoothed training curves do not establish convergence.')
    limits=('Intervals are exploratory and not adjusted for multiple comparisons. Scenario delivery intervals '
            'resample graphs conditional on the fitted models. Learned gate-versus-all contrasts resample matched '
            'graphs and training seeds; only three training seeds are available. Reactive attack and targeted '
            'spoof traces respond to policy behavior. Controlled single-message replay uses random/exogenous '
            'threats and includes rejected packets. Scaling fixes population and attack budget, so threat density '
            'changes with graph size. The oracle is a diagnostic, not a proven optimal bound. Time is in arbitrary '
            'model units. Delivered-only cost/time averages have survivor conditioning and do not prove a '
            'per-convoy improvement. Military applicability is not established by synthetic networks.')
    overview=['# Complete simulator: executed results','',note,'',
        f"Executed {summary['training_episodes']:,} training episodes, {summary['heldout_episodes']:,} held-out evaluation runs, "
        f"{summary['scaling_episodes']:,} size-transfer runs, {summary['ablation_episodes']:,} ablations and "
        f"{summary['message_interventions']:,} individual-message interventions.",'',
        '## Delivery results','',values.to_markdown(floatfmt='.2f'),'',
        '## Single-message replay','',replay_table.to_markdown(),'',
        '## Limitations and interpretation','',limits,'',
        'Gate superiority is a hypothesis to test. Positive, negative and inconclusive differences are all retained in the report. '
        'The CSV files preserve full precision. Window diagnostics summarize training behavior; they are not a statistical convergence test.','',
        '## Read or download','',
        '[Combined seven-page vector PDF](updated_results_report.pdf).',
        '[Two-page illustrative simulation PDF](simulation_episode_report.pdf).',
        '[Self-contained HTML](index.html): download it and open it locally; no web server or Internet is needed.','',
        '## Figures','']
    sections=[]
    for name,title in TITLES.items():
        encoded=base64.b64encode((figures/f'{name}.png').read_bytes()).decode()
        sections.append(f'<section id="{name}"><h2>{html.escape(title)}</h2><img alt="{html.escape(title)}" src="data:image/png;base64,{encoded}"></section>')
        overview += [f'### {title}','',f'![{title}]({name}.png)','',f'[Vector PDF]({name}.pdf)','']
    graph_seeds=json.loads((root/'random/manifest.json').read_text())['arguments']['graphs']
    overview += ['## Provenance','',f"Held-out graph seeds: {graph_seeds}. Training graphs: 1–40. Complete parameters and commands are in the run manifests.",'',
                 f"Source SHA-256: `{summary['source_hash']}`.",'',
                 'From `simulator/`, validate and regenerate with fresh figure output:', '',
                 f'```bash\npython validate_results.py out/{root.name}\npython plot_updated_results.py --run-root out/{root.name} --output ../revision/regenerated-figures\npython build_report.py --run-root out/{root.name} --figures ../revision/regenerated-figures\n```','']
    (figures/'README.md').write_text('\n'.join(overview))
    contrast_display=contrasts.copy()
    contrast_display[['difference','lower','upper']]*=100
    (figures/'paired_contrasts_percentage_points.csv').write_text(contrast_display.to_csv(index=False))
    buttons=' '.join(f'<a href="#{name}">{html.escape(title)}</a>' for name,title in TITLES.items())
    payload=json.dumps(results.to_dict('records')).replace('<','\\u003c')
    content='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIMRL complete simulator report</title><style>
body{font:16px/1.6 system-ui,sans-serif;margin:0;background:#f4f6f8;color:#14232d}main{max-width:1250px;margin:auto;padding:24px}
h1,h2{line-height:1.2}section,.card{padding:24px;background:white;border-radius:10px;margin:22px 0}img{width:100%;height:auto}
nav{display:flex;gap:12px;flex-wrap:wrap}a{color:#087f8c}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{border-bottom:1px solid #dbe1e5;padding:8px;text-align:left}select{font:inherit;padding:8px}small{color:#475569}
</style><main><h1>AIMRL complete simulation model and results</h1><p>'''+html.escape(note)+'''</p><nav>'''+buttons+'''</nav>
<section><h2>Explore delivery outcomes</h2><label>Scenario <select id="scenario"><option value="random">Random attacks</option><option value="spoof">Disrupted / spoofed communication</option><option value="reactive">Reactive attacks / targeted spoofing</option></select></label>
<table><thead><tr><th>Method</th><th>Delivered (%)</th><th>Graph interval (%)</th><th>Evaluated episode runs</th></tr></thead><tbody id="rows"></tbody></table>
<small>Graph-bootstrap 95% intervals conditional on these trained models. Paired learned contrasts additionally resample training seeds in the contrast figure.</small></section>
'''+''.join(sections)+'''<section><h2>Interpretation and limitations</h2><p>'''+html.escape(limits)+'''</p><p>Gating is not assumed superior. Every reported result is generated from audited run artifacts.</p><p>Source SHA-256: <code>'''+summary['source_hash']+'''</code></p></section></main>
<script>const data='''+payload+''';function render(){const selected=document.getElementById('scenario').value;const body=document.getElementById('rows');body.replaceChildren();for(const r of data.filter(x=>x.scenario===selected)){const tr=document.createElement('tr');for(const value of [r.method,(r.delivery*100).toFixed(2),`${(r.lower*100).toFixed(2)} – ${(r.upper*100).toFixed(2)}`,r.episode_records]){const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}body.appendChild(tr);}}document.getElementById('scenario').addEventListener('change',render);render();</script></html>'''
    (figures/'index.html').write_text(content)
    print(f'Built offline HTML and GitHub-readable report: {figures}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root',type=Path,required=True)
    parser.add_argument('--figures',type=Path,required=True)
    args=parser.parse_args(); main(args.run_root,args.figures)
