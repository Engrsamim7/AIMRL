"""Package the current code, fitted models, raw evidence and reports with hashes."""
import hashlib,json,zipfile
from pathlib import Path
from run_reviewer_revision import source_hash

ROOT=Path(__file__).resolve().parents[1]

def main():
    verification=json.loads((ROOT/'revision/reviewer-revision-results/verification.json').read_text())
    manifest=json.loads((ROOT/'simulator/out/reviewer-revision-v2/pipeline.json').read_text())
    if verification['status']!='passed' or manifest['status']!='completed' or manifest['source_hash']!=source_hash():
        raise RuntimeError('Require completed current-source experiments and passed report audit')
    assert verification['controlled_filtering_episodes']==450 and verification['controlled_packet_interventions']==80
    files=[]
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file():continue
        parts=p.relative_to(ROOT/'simulator').parts
        if '__pycache__' in parts or '.pytest_cache' in parts or p.suffix=='.pyc':continue
        if parts[0]=='out' and (len(parts)<2 or parts[1] not in ['reviewer-revision-v1','reviewer-revision-v2']):continue
        if parts[0]=='figs':continue
        files.append(p)
    for name in ['reviewer-revision-results','reviewer-revision-v1-results','submission-code','submission-code-audit']:
        files.extend(p for p in (ROOT/'revision'/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    for name in ['reviewer-code-changes.md','simulator-reviewer-coverage.md','gate-claim-recovery-protocol.md','manuscript-gate-findings.md']:
        files.append(ROOT/'revision'/name)
    files.extend(ROOT/name for name in ['README.md','setup_local.sh','requirements-lock.txt','.gitignore','.gitattributes'])
    files=sorted(set(files));checksums={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    dest=ROOT/'deliverables/AIMRL-reviewer-revision.zip';dest.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,'AIMRL-reviewer-revision/'+str(p.relative_to(ROOT)))
        z.writestr('AIMRL-reviewer-revision/START_HERE.md','# Reviewer revision package\n\nOpen revision/reviewer-revision-results/index.html for all nine figures and tables without a server. Read revision/reviewer-code-changes.md for implementation changes, assumptions and reproduction commands. Use bash setup_local.sh from this directory to install pinned dependencies. The current executed run is simulator/out/reviewer-revision-v2; v1 and supplied submission code are preserved as historical references. Current report audits passed and 43 tests passed. General gate superiority and convergence remain unestablished.\n')
        z.writestr('AIMRL-reviewer-revision/BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=source_hash(),files=checksums),indent=2))
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for name,digest in checksums.items():assert hashlib.sha256(z.read('AIMRL-reviewer-revision/'+name)).hexdigest()==digest
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n')
    print(json.dumps(dict(path=str(dest),bytes=dest.stat().st_size,files=len(files),sha256=digest)))

if __name__=='__main__':main()
