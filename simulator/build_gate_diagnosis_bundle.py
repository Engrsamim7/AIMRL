"""Complete decision-diagnosis source, models, raw effects, labels and figures."""
import gzip
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from diagnose_gate_decisions import fingerprint
ROOT=Path(__file__).resolve().parents[1]


def main():
    run=ROOT/'simulator/out/gate-decision-diagnosis';report=ROOT/'revision/gate-decision-diagnosis'
    check=json.loads((report/'verification.json').read_text());meta=json.loads((run/'pipeline.json').read_text())
    assert check['status']=='passed' and meta['status']=='completed' and check['source_hash']==fingerprint()
    for name in ['packets','effects','episodes','convoys']:
        p=run/(name+'.csv')
        with p.open('rb') as src,p.with_suffix('.csv.gz').open('wb') as target:
            with gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as dst:shutil.copyfileobj(src,dst)
    files=[]
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
        rel=p.relative_to(ROOT/'simulator')
        if rel.parts[0]=='figs':continue
        if rel.parts[0]=='out':
            if len(rel.parts)<3 or rel.parts[1] not in ['matched-gate-study','gate-decision-diagnosis','gate-decision-targeted-audit']:continue
            if p.suffix=='.csv' and p.with_suffix('.csv.gz').exists():continue
        files.append(p)
    for name in ['gate-decision-diagnosis','matched-gate-results']:
        files.extend(p for p in (ROOT/'revision'/name).rglob('*') if p.is_file())
    for name in ['requirements-lock.txt','setup_local.sh','.gitignore','.gitattributes','revision/submission-code-audit/original_network_seed42.json','revision/gate-decision-diagnosis-protocol.md','revision/gate-decision-targeted-followup.md','revision/gate-decision-diagnosis-findings.md','revision/matched-gate-protocol.md','revision/matched-gate-claim-draft.md','revision/matched-gate-figure-guide.md']:files.append(ROOT/name)
    dest=ROOT/'deliverables';shutil.copy2(report/'gate_decision_diagnosis.pdf',dest/'AIMRL-gate-decision-diagnosis-figures.pdf');files.append(dest/'AIMRL-gate-decision-diagnosis-figures.pdf')
    start=('# Gate decision diagnosis\n\n'
        'Read revision/gate-decision-diagnosis-findings.md for the evidence and concrete next-design recommendation. Open revision/gate-decision-diagnosis/gate_decision_diagnosis.pdf or index.html for seven figures. Its README.md contains all diagnostic tables and limitations.\n\n'
        'This package contains full simulator/diagnostic source; 64 original final routing checkpoints and 16 reconstructed hash-verified warmup checkpoints; the original fitted value models; all matched-study data for context; all eligible diagnostic packet records; selected full/prefix accept-versus-reject effects with complete per-branch convoy outcomes encoded as JSON in CSV cells; static-rule outcomes; and new warmup/adapted prediction labels. Large tables are CSV.gz.\n\n'
        'No original gate or final actor was changed or refitted. The reconstructed warmup actors reproduce original weights; they are not additional independent training seeds. Selection is chronological and stratified, and all diagnostic findings are exploratory. These datasets must not be used as a fresh held-out superiority trial for a gate redesigned using their outcomes.\n\n'
        'Run bash setup_local.sh to create the pinned environment. Reproduction commands are in revision/gate-decision-diagnosis-protocol.md and the diagnostic report README. Use a new output folder when rerunning. Earlier historical packages remain separately available in GitHub.\n')
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
    archive=dest/'AIMRL-gate-decision-diagnosis.zip';prefix='AIMRL-gate-decision-diagnosis/'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,prefix+str(p.relative_to(ROOT)))
        z.writestr(prefix+'START_HERE.md',start);z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),files=hashes),indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,h in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==h
    h=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(h+'  '+archive.name+'\n')
    print(json.dumps(dict(path=str(archive),bytes=archive.stat().st_size,files=len(hashes),sha256=h)))

if __name__=='__main__':main()
