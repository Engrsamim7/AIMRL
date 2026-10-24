"""Portable frozen-router radio mechanism pilot; old archives are immutable."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from run_pretransmission_opportunity import fingerprint

ROOT=Path(__file__).resolve().parents[1]


def main():
    run=ROOT/'simulator/out/pretransmission-opportunity';report=ROOT/'revision/pretransmission-opportunity-results'
    verify=json.loads((report/'verification.json').read_text());assert verify['status']=='passed' and verify['source_hash']==fingerprint()
    assert verify['report_hash']==hashlib.sha256((ROOT/'simulator/report_pretransmission_opportunity.py').read_bytes()).hexdigest()
    files=[]
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
        rel=p.relative_to(ROOT/'simulator')
        if rel.parts[0]=='figs':continue
        if rel.parts[0]=='out':
            if len(rel.parts)<3:continue
            if rel.parts[1]=='pretransmission-opportunity':pass
            elif rel.parts[1]=='delivery-learning-v3' and rel.parts[2] in ['actors','calibration.json','locked_settings.json','pipeline.json']:pass
            elif rel.parts[1]=='timed-network-development-v2' and rel.parts[2]=='calibration.json':pass
            else:continue
        files.append(p)
    for folder in [report,ROOT/'revision/submission-code']:
        files.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    for name in ['requirements-lock.txt','requirements-actor-aware.txt','setup_local.sh','.gitignore','.gitattributes',
                 'revision/pretransmission-opportunity-findings.md','revision/pretransmission-opportunity-protocol.md',
                 'revision/delivery-mathematical-analysis.md','revision/submission-code-audit/original_network_seed42.json']:
        files.append(ROOT/name)
    start='''# Implemented pre-transmission mechanism pilot

Read revision/pretransmission-opportunity-findings.md first. Open the three-page
PDF or offline index.html in revision/pretransmission-opportunity-results/.

This is a completed mechanism pilot with frozen routing, not a trained new
communication controller or a superiority confirmation. It includes1104 factual
episodes,1104 full batched-priority reference episodes,3017 isolated alternative
continuations and41800 convoy outcome records. Sampled hindsight opportunity
must not be called a deployable or learned result. All conditions and harms stay.

The package contains complete source, original submitted code, all eight selected
routing checkpoints (including one initial-policy selection), calibration,
prospective design, raw episode/convoy/paired-branch records, tables and figures.
Prior studies and their bulky raw logs remain in separate historical ZIPs.

Install bash setup_local.sh, then
.venv/bin/python -m pip install -r requirements-actor-aware.txt
Run from this extracted root, with MPLCONFIGDIR=/tmp/aimrl-mpl
XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1:
.venv/bin/python -m pytest -q simulator/tests_*.py
.venv/bin/python simulator/run_pretransmission_opportunity.py --output simulator/out/pretransmission-reproduction
.venv/bin/python simulator/report_pretransmission_opportunity.py --run simulator/out/pretransmission-reproduction

A fresh run folder is required. Actor/gate learning is not part of this pilot.
The shared-MAC queue controller does not read live remote states or future truth.
Deferral affects only the selected packet and leaves service available to others.
The original engine, routing checkpoints and previous study archives are preserved.
'''
    dest=ROOT/'deliverables';shutil.copy2(report/'pretransmission_report.pdf',dest/'AIMRL-pretransmission-opportunity-figures.pdf')
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
    archive=dest/'AIMRL-pretransmission-opportunity.zip';prefix='AIMRL-pretransmission-opportunity/'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,prefix+str(p.relative_to(ROOT)),compress_type=zipfile.ZIP_STORED if p.suffix=='.gz' else zipfile.ZIP_DEFLATED)
        z.writestr(prefix+'START_HERE.md',start);z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),files=hashes),indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,h in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==h,name
    h=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(h+'  '+archive.name+'\n')
    result=dict(status='archive_integrity_passed',files=len(hashes),bytes=archive.stat().st_size,sha256=h,extracted_tests=None,report_regeneration_exact=None,public_downloads_verified=False)
    assert result['bytes']<100*1024**2
    (dest/'AIMRL-pretransmission-opportunity-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
