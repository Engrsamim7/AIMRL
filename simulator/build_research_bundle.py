"""Portable complete fresh-study source, fitted weights, data and figures."""
import gzip
import hashlib
import json
import zipfile
from pathlib import Path
from run_cover_traffic_stress import fingerprint

ROOT=Path(__file__).resolve().parents[1]


def main():
    run=ROOT/'simulator/out/cover-traffic-stress';report=ROOT/'revision/cover-traffic-results'
    meta=json.loads((run/'pipeline.json').read_text());checks=json.loads((report/'verification.json').read_text())
    assert meta['status']=='completed' and checks['status']=='passed' and meta['source_hash']==fingerprint()
    assert checks['evaluation_episodes']==28000 and checks['convoys']==140000
    for dataset in [run,ROOT/'simulator/out/research-opportunity-study',ROOT/'simulator/out/guarded-research-study']:
        for name in ['messages','convoys']:
            p=dataset/(name+'.csv')
            if not p.exists():continue
            with p.open('rb') as src,p.with_suffix('.csv.gz').open('wb') as dest:
                with gzip.GzipFile(fileobj=dest,mode='wb',mtime=0) as compressed:
                    for block in iter(lambda:src.read(1024*1024),b''):compressed.write(block)
    files=[]
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
        rel=p.relative_to(ROOT/'simulator')
        if rel.parts[0]=='figs':continue
        if rel.parts[0]=='out':
            if rel.parts[1] not in ['research-opportunity-study','guarded-research-study','cover-traffic-stress']:continue
            if p.suffix=='.csv' and p.with_suffix('.csv.gz').exists():continue
        files.append(p)
    for folder in ['research-opportunity-results','guarded-research-results','cover-traffic-results','submission-code','submission-code-audit']:
        files.extend(p for p in (ROOT/'revision'/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    files.extend(ROOT/name for name in ['README.md','requirements-lock.txt','setup_local.sh','.gitignore','.gitattributes'])
    files.append(ROOT/'revision/research-opportunity-methods.md')
    files.append(ROOT/'revision/research-manuscript-claim-draft.md')
    files.append(ROOT/'deliverables/AIMRL-research-figures.pdf')
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    start=('# Fresh actor-specific value study\n\n'
           'Open revision/cover-traffic-results/index.html or cover_traffic_report.pdf for the latest frozen neural robustness stress. Open revision/guarded-research-results/index.html or research_opportunity_report.pdf for the main guarded study. Read both README.md files for corrected positive, adverse and zero-effect results; read revision/research-opportunity-methods.md for exact mechanisms and assumptions. The initial unconstrained learned study and its failures remain in revision/research-opportunity-results.\n\n'
           'This complete package contains simulator and experiment code, original submitted source, six newly trained DQN/MAPPO checkpoints, seven fitted message-value models, causal training examples, validation and locked settings, all episode/convoy records for THREE fresh studies, individual packet records for the first two, aggregate communication records for cover stress, and all 20 figures. The later studies reuse training-only models and use new layouts/tapes. Large raw tables are shipped as CSV.gz. Prior adaptive/audit data remain preserved in earlier separate repository packages.\n\n'
           'All 20 figures are also combined in deliverables/AIMRL-research-figures.pdf: latest cover stress first, guarded study second, initial unconstrained failures last. Run bash setup_local.sh in the package root. Reproduction commands are in the report README. Use a new output directory to preserve executed results. Results apply to declared physical mechanism benchmarks and named baselines; no universal superiority or real-world operational validation follows.\n')
    hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
    dest=ROOT/'deliverables/AIMRL-research-opportunity-study.zip';prefix='AIMRL-research-opportunity-study/'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,prefix+str(p.relative_to(ROOT)))
        z.writestr(prefix+'START_HERE.md',start)
        z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),files=hashes),indent=2)+'\n')
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for name,digest in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==digest
    digest=hashlib.sha256(dest.read_bytes()).hexdigest();dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n')
    print(json.dumps(dict(path=str(dest),bytes=dest.stat().st_size,files=len(hashes),sha256=digest)))


if __name__=='__main__':main()
