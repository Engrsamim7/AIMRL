"""Package the complete matched study without replacing previous deliverables."""
import gzip
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from run_matched_gate_study import fingerprint
ROOT=Path(__file__).resolve().parents[1]


def main():
    run=ROOT/'simulator/out/matched-gate-study'; report=ROOT/'revision/matched-gate-results'
    meta=json.loads((run/'pipeline.json').read_text());verify=json.loads((report/'verification.json').read_text())
    assert meta['status']=='completed' and verify['status']=='passed' and meta['source_hash']==fingerprint()
    for name in ['test_convoys','mechanism_convoys']:
        p=run/(name+'.csv')
        if p.exists():
            with p.open('rb') as src,p.with_suffix('.csv.gz').open('wb') as target:
                with gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as dst:shutil.copyfileobj(src,dst)
    files=[]
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
        rel=p.relative_to(ROOT/'simulator')
        if rel.parts[0]=='figs':continue
        if rel.parts[0]=='out':
            if len(rel.parts)<3 or rel.parts[1]!='matched-gate-study':continue
            if p.suffix=='.csv' and p.with_suffix('.csv.gz').exists():continue
        files.append(p)
    files.extend(p for p in report.rglob('*') if p.is_file())
    for name in ['requirements-lock.txt','setup_local.sh','.gitignore','.gitattributes','revision/matched-gate-protocol.md','revision/matched-gate-claim-draft.md']:
        files.append(ROOT/name)
    dest=ROOT/'deliverables';dest.mkdir(exist_ok=True)
    shutil.copy2(report/'matched_gate_report.pdf',dest/'AIMRL-matched-gate-figures.pdf')
    files.append(dest/'AIMRL-matched-gate-figures.pdf')
    start=('# Matched-training gate study\n\n'
        'Open revision/matched-gate-results/README.md first for the actual outcome, all comparisons and limitations. Open deliverables/AIMRL-matched-gate-figures.pdf for all eight figures, or revision/matched-gate-results/index.html for an embedded-image report.\n\n'
        'This is a NEW matched-adaptation experiment: eight paired seeds each for DQN/MAPPO; ALL, SAFE, VALUE and COMBINED arms; 64 final checkpoints; complete training/validation/auxiliary value data, final episode/convoy records, fixed-actor diagnostics, source and tests. Large tables are CSV.gz. The safeguards-only baseline here uses exactly the combined arm\'s constraints and differs from the earlier SAFE-ALL implementation.\n\n'
        'Read revision/matched-gate-protocol.md for the predeclared hypotheses, fixed settings and full reproduction commands. Run bash setup_local.sh to recreate the pinned environment. All previous studies and downloadable packages remain separately available in the GitHub branch; their datasets are not duplicated in this package.\n\n'
        'Primary comparisons include actor adaptation after a common warmup. Learned arms additionally use causal replay labels; compute is not equal. Fixed-actor swaps are descriptive. No broad superiority, convergence, bandwidth savings or operational-validation claim is warranted.\n')
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
    archive=dest/'AIMRL-matched-gate-study.zip';prefix='AIMRL-matched-gate-study/'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,prefix+str(p.relative_to(ROOT)))
        z.writestr(prefix+'START_HERE.md',start)
        z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),files=hashes),indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==digest
    digest=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
    print(json.dumps(dict(path=str(archive),bytes=archive.stat().st_size,files=len(hashes),sha256=digest)))

if __name__=='__main__':main()
