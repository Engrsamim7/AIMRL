"""Build a complete portable adaptive-study ZIP, retaining the negative prototype."""
import hashlib,json,zipfile
from pathlib import Path
from run_adaptive_experiments import fingerprint
from run_reviewer_revision import source_hash as core_hash

ROOT=Path(__file__).resolve().parents[1]

def main():
    run=ROOT/'simulator/out/adaptive-gate-v2';report=ROOT/'revision/adaptive-gate-results'
    manifest=json.loads((run/'pipeline.json').read_text());verification=json.loads((report/'verification.json').read_text())
    assert manifest['status']=='completed' and verification['status']=='passed' and manifest['source_hash']==fingerprint()
    assert verification['heldout_episodes']==35040 and verification['frozen_actor_episodes']==7200
    old=ROOT/'simulator/out/adaptive-gate-v1';old_manifest=json.loads((old/'pipeline.json').read_text());h=hashlib.sha256(core_hash().encode())
    for name in ['adaptive_gate.py','run_adaptive_experiments.py']:
        h.update(name.encode());h.update((old/'executed_source'/name).read_bytes())
    assert h.hexdigest()==old_manifest['source_hash']
    files=[]
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
        parts=p.relative_to(ROOT/'simulator').parts
        if parts[0]=='out':
            if parts[1] in ['adaptive-gate-v1','adaptive-gate-v2']:pass
            elif parts[1]=='reviewer-revision-v2' and (parts[2]=='models' or p.name in ['pipeline.json','training_manifest.json']):pass
            else:continue
            if p.suffix=='.csv' and p.with_suffix('.csv.gz').exists():continue
        if parts[0]=='figs':continue
        files.append(p)
    for folder in ['adaptive-gate-results','adaptive-gate-v1-results','submission-code','submission-code-audit']:
        files.extend(p for p in (ROOT/'revision'/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    files.extend(ROOT/'revision'/name for name in ['adaptive-gate-methods.md','reviewer-code-changes.md','simulator-reviewer-coverage.md'])
    files.extend(ROOT/name for name in ['README.md','requirements-lock.txt','setup_local.sh','.gitignore','.gitattributes'])
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    start='# Adaptive gate package\n\nOpen revision/adaptive-gate-results/index.html for the eight-figure offline report, or adaptive_gate_report.pdf in that folder. Read revision/adaptive-gate-methods.md for mechanisms, assumptions and reproduction commands. Run bash setup_local.sh from this directory to install pinned dependencies. The package includes current and negative-prototype data, complete source, existing baseline weights and original training records. Large packet CSVs are losslessly compressed as .csv.gz; pandas reads them directly. The controlled single-impersonation case supports a bounded filtering benefit; broad statistical delivery superiority remains unestablished.\n'
    hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
    dest=ROOT/'deliverables/AIMRL-adaptive-gate.zip'
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,'AIMRL-adaptive-gate/'+str(p.relative_to(ROOT)))
        z.writestr('AIMRL-adaptive-gate/START_HERE.md',start)
        z.writestr('AIMRL-adaptive-gate/BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),files=hashes),indent=2))
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for name,digest in hashes.items():assert hashlib.sha256(z.read('AIMRL-adaptive-gate/'+name)).hexdigest()==digest
    digest=hashlib.sha256(dest.read_bytes()).hexdigest();dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n')
    print(json.dumps(dict(path=str(dest),bytes=dest.stat().st_size,files=len(hashes),sha256=digest)))

if __name__=='__main__':main()
