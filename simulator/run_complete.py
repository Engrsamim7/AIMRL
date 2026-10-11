"""Run the complete, matched synthetic experiment protocol from one command.

Existing outputs are never overwritten. All subprocesses use this Python
interpreter, one CPU thread each, and preserve their exact commands and logs.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
ALGOS = ['dqn', 'ppo', 'ippo', 'mappo']


def main(args):
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    figures = Path(args.figures).resolve()
    if figures.exists():
        raise FileExistsError(f'Refusing to overwrite figures: {figures}')
    env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
               MPLCONFIGDIR=str(root/'matplotlib-cache'), XDG_CACHE_HOME=str(root/'cache'))
    common = ['--threads', '1', '--convoys', '12', '--attack-rate', '.9',
              '--attack-duration', '40', '80', '--budget', '12', '--p-kill', '.7',
              '--conf-mu', '.85', '--conf-sd', '.1']
    metadata = dict(status='running', arguments=vars(args),
                    protocol='matched synthetic benchmark; exploratory, convergence not presumed',
                    started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    def save():
        (root/'pipeline.json').write_text(json.dumps(metadata, indent=2)+'\n')
    def run(name, script_args):
        command = [sys.executable, str(ROOT/'run_experiments.py'), *script_args,
                   '--output', str(root/name)]
        print(f'Starting {name}', flush=True)
        with (root/f'{name}.log').open('w') as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'{name} failed; see {root/name}.log')
        print(f'Completed {name}', flush=True)
    def batch(jobs):
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run, name, command) for name,command in jobs]
            for future in futures:
                future.result()
    save()
    start = time.perf_counter()
    try:
        batch([(f'train-{a}', ['train', '--algos', a, '--episodes', str(args.episodes),
                              '--seeds', '0', '1', '2', '--delay', '2', '--loss', '.2',
                              '--spoof', '4', *common]) for a in ALGOS])
        # Merge copies, preserving all four independent worker manifests.
        import pandas as pd
        merged = root/'train'
        merged.mkdir()
        curves=[]; checkpoints=[]; manifests=[]
        for algo in ALGOS:
            worker=root/f'train-{algo}'
            manifests.append(json.loads((worker/'manifest.json').read_text()))
            curves.append(pd.read_csv(worker/'training_curves.csv'))
            for entry in json.loads((worker/'checkpoints.json').read_text()):
                old=Path(entry['path']); new=merged/old.name
                shutil.copy2(old,new); entry['path']=str(new); checkpoints.append(entry)
        pd.concat(curves,ignore_index=True).to_csv(merged/'training_curves.csv',index=False)
        (merged/'checkpoints.json').write_text(json.dumps(checkpoints,indent=2)+'\n')
        manifest=json.loads(json.dumps(manifests[0]))
        manifest['arguments'].update(algos=ALGOS,output=str(merged))
        manifest['argv']=['aggregation of the four completed independent training workers']
        manifest['aggregation_sources']=[str(root/f'train-{a}'/'manifest.json') for a in ALGOS]
        manifest['worker_elapsed_seconds']={a:m['elapsed_seconds'] for a,m in zip(ALGOS,manifests)}
        manifest['elapsed_seconds']=max(manifest['worker_elapsed_seconds'].values())
        manifest['elapsed_seconds_definition']='maximum worker duration, not total training or another run'
        (merged/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        graphs=list(map(str,range(args.graph_start,args.graph_start+10)))
        evaluate=['evaluate','--checkpoints',str(merged),'--graphs',*graphs,
                  '--eval-episodes','5','--sizes','39',*common]
        disrupted=['--delay','4','--loss','.2','--spoof','8']
        batch([('random',evaluate+['--delay','1','--loss','0','--spoof','0']),
               ('spoof',evaluate+disrupted),
               ('reactive',evaluate+disrupted+['--adversary','reactive','--spoof-mode','targeted']),
               ('ablate',['ablate','--graphs',*graphs,'--eval-episodes','5',*common,*disrupted])])
        batch([('scaling',['evaluate','--checkpoints',str(merged),'--graphs',
                           *map(str,range(args.graph_start+100,args.graph_start+103)),
                           '--eval-episodes','2','--sizes','39','51','203','483',*common,*disrupted]),
               ('fir',['fir','--graphs',*map(str,range(args.graph_start+200,args.graph_start+205)),
                       '--eval-episodes','2','--comms','all','gate',*common,*disrupted])])
        for command in [
            ['validate_results.py',str(root)],
            ['plot_updated_results.py','--run-root',str(root),'--output',str(figures)],
            ['build_report.py','--run-root',str(root),'--figures',str(figures)],
        ]:
            subprocess.run([sys.executable,str(ROOT/command[0]),*command[1:]],cwd=ROOT,env=env,check=True)
        metadata.update(status='completed',elapsed_seconds=time.perf_counter()-start)
        print(f'Complete. Open {figures / "index.html"} in a browser.',flush=True)
    except Exception as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='out/complete-model-v1')
    parser.add_argument('--figures',default='../revision/complete-visualisations')
    parser.add_argument('--episodes',type=int,default=300)
    parser.add_argument('--workers',type=int,choices=range(1,5),default=4)
    parser.add_argument('--graph-start',type=int,default=700)
    args=parser.parse_args()
    if args.episodes<1 or args.graph_start<300:
        parser.error('Episodes must be positive and evaluation graphs must start at 300 or later')
    main(args)
