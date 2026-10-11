"""Package complete source, fitted models, raw results and offline figures."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main(repo,run,figures,output):
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite {output}')
    pipeline=json.loads((run/'pipeline.json').read_text())
    assert pipeline['status']=='completed','The complete pipeline has not finished'
    audit=json.loads((run/'validation.json').read_text())
    assert len(audit['runs'])==11,'Expected all training workers and six experiment stages'
    summary=json.loads((figures/'summary.json').read_text())
    assert summary['source_hash']==audit['source_hash']
    assert len(list(figures.glob('*.png')))==9
    files={}
    def include(path,relative):
        files[str(relative).replace('\\','/')]=path
    source=repo/'simulator'
    for path in source.rglob('*'):
        relative=path.relative_to(source)
        if not path.is_file() or any(p in {'out','__pycache__','.pytest_cache','figs'} for p in relative.parts):
            continue
        if path.suffix in {'.py','.md','.txt','.sh'} or path.name=='LICENSE':
            include(path,Path('simulator')/relative)
    for path in run.rglob('*'):
        if path.is_file() and path.suffix in {'.csv','.json','.pt','.log'} and not any(
                p in {'cache','matplotlib-cache'} for p in path.relative_to(run).parts):
            include(path,Path('simulator/out')/run.name/path.relative_to(run))
    for path in figures.iterdir():
        if path.is_file(): include(path,Path('revision')/figures.name/path.name)
    for name in ['complete-protocol.md','complete-model.md']:
        path=repo/'revision'/name
        if path.exists(): include(path,Path('revision')/name)
    for name in ['requirements-lock.txt','setup_local.sh']:
        path=repo/name
        if path.exists(): include(path,name)
    readme=f'''# AIMRL complete simulator package

This package includes the complete reconstructed simulator code, 36 fitted models,
raw convoy/episode CSVs, manifests, logs, audit results, nine PNG/vector-PDF figures,
and an offline report. Training-worker and aggregated checkpoints are copies of the
same models, not additional training. Original manuscripts/review letters,
credentials, environments, caches and old result archives are excluded.

Start by opening `revision/{figures.name}/index.html` in a browser.
It contains the figures and scenario selector and works without Internet access.
The seven-page comparison PDF is `revision/{figures.name}/updated_results_report.pdf`.
The two-page episode PDF is `revision/{figures.name}/simulation_episode_report.pdf`.

## Run the code

The executed environment used Python 3.12 on Linux and CPU PyTorch.
Linux, WSL or a comparable Linux notebook environment is recommended.

```bash
bash setup_local.sh
source .venv/bin/activate
cd simulator
python -m pytest -q tests_core.py tests_revision.py
python validate_results.py out/{run.name}
python run_complete.py --output out/my-new-run --figures ../revision/my-new-figures
```

The full command retrains and regenerates all results. It requires fresh output
directories and may take substantial CPU time. Defaults are 300 episodes/model,
three training seeds, 12 convoys and four workers. No operational data or service
credential is required. To regenerate figures from the included results:

```bash
python plot_updated_results.py --run-root out/{run.name} --output ../revision/regenerated
python build_report.py --run-root out/{run.name} --figures ../revision/regenerated
```

Read `simulator/METHODS.md` for dynamics, observation, gate, learning and metric
definitions. Read `revision/complete-protocol.md` for the executed design.
Results are synthetic and exploratory; a complete implementation does not imply
convergence, real-world validation or consistent gate superiority.

`BUNDLE_MANIFEST.json` records SHA-256 hashes of every packaged file.
Source SHA-256: `{summary['source_hash']}`.
'''
    checksums={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in sorted(files.items())}
    checksums['README.md']=hashlib.sha256(readme.encode()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,path in sorted(files.items()): archive.write(path,'AIMRL-complete/'+name)
        archive.writestr('AIMRL-complete/README.md',readme)
        archive.writestr('AIMRL-complete/BUNDLE_MANIFEST.json',json.dumps(dict(
            source_hash=summary['source_hash'],files=checksums,summary=summary),indent=2))
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        for name,digest in checksums.items():
            assert hashlib.sha256(archive.read('AIMRL-complete/'+name)).hexdigest()==digest
    print(f'Verified complete bundle: {output} ({output.stat().st_size:,} bytes, {len(checksums)} hashed files)')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--run-root',type=Path,required=True)
    parser.add_argument('--figures',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); main(args.repo,args.run_root,args.figures,args.output)
