"""Extend the verified adaptive package without altering the earlier deliverable."""
import gzip
import hashlib
import json
import zipfile
from pathlib import Path

from run_adaptive_experiments import fingerprint

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = ROOT/'revision/communication-opportunity-audit'
    raw = ROOT/'simulator/out/communication-opportunity-audit'
    verification = json.loads((report/'verification.json').read_text())
    manifest = json.loads((raw/'manifest.json').read_text())
    assert verification['status']=='passed' and verification['network_episodes']==7560
    assert verification['control_episodes']==2400 and manifest['source_hash']==fingerprint()
    base = ROOT/'deliverables/AIMRL-adaptive-gate.zip'
    assert hashlib.sha256(base.read_bytes()).hexdigest()==base.with_suffix('.zip.sha256').read_text().split()[0]
    # Raw packet tables are shipped losslessly compressed; local CSVs retained.
    for name in ['packets','envelopes','decisions','convoys']:
        source=raw/(name+'.csv');target=source.with_suffix('.csv.gz')
        with source.open('rb') as src,target.open('wb') as dest:
            with gzip.GzipFile(fileobj=dest,mode='wb',mtime=0) as zipped:
                for block in iter(lambda:src.read(1024*1024),b''):
                    zipped.write(block)
    extra=[]
    extra.extend(p for p in report.rglob('*') if p.is_file())
    extra.extend(p for p in raw.iterdir() if p.is_file() and not (p.suffix=='.csv' and p.with_suffix('.csv.gz').exists()))
    extra.extend(ROOT/'simulator'/n for n in ['audit_communication_opportunities.py','audit_warning_response.py','report_communication_audit.py','build_communication_audit_bundle.py','tests_communication_audit.py'])
    extra.extend([ROOT/'README.md',ROOT/'revision/communication-audit-next-experiments.md'])
    replacements={str(p.relative_to(ROOT)):p for p in extra}
    dest=ROOT/'deliverables/AIMRL-communication-audit.zip'
    prefix='AIMRL-communication-audit/'
    hashes={}
    with zipfile.ZipFile(base) as original,zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as package:
        old_manifest=json.loads(original.read('AIMRL-adaptive-gate/BUNDLE_MANIFEST.json'))
        for name,digest in old_manifest['files'].items():
            assert hashlib.sha256(original.read('AIMRL-adaptive-gate/'+name)).hexdigest()==digest
        for info in original.infolist():
            name=info.filename.removeprefix('AIMRL-adaptive-gate/')
            if name in replacements:
                continue
            if name=='BUNDLE_MANIFEST.json':
                name='BASE_BUNDLE_MANIFEST.json'
            elif name=='START_HERE.md':
                name='BASE_START_HERE.md'
            data=original.read(info.filename)
            package.writestr(prefix+name,data)
            hashes[name]=hashlib.sha256(data).hexdigest()
        for name,p in sorted(replacements.items()):
            package.write(p,prefix+name)
            hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
        start=('# Communication opportunity audit package\n\n'
               'Open revision/communication-opportunity-audit/index.html for the six-figure offline report, or communication_opportunity_report.pdf in that folder. README.md in the report folder defines the diagnostics and caveats. Read revision/communication-audit-next-experiments.md for the proposed fresh experiment design.\n\n'
               'This ZIP includes all source, original frozen model weights and executed adaptive results from the previous verified package, plus audit code and raw audit tables. Raw large CSVs are shipped as CSV.gz. No original evaluated simulator or gate source was changed; no new training or superiority claim is made. BASE_BUNDLE_MANIFEST.json records the earlier package.\n\n'
               'Run bash setup_local.sh from the package directory to install pinned dependencies; reproduction commands are in the audit README.\n')
        package.writestr(prefix+'START_HERE.md',start)
        hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
        package.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),base_package_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),files=hashes),indent=2)+'\n')
    with zipfile.ZipFile(dest) as package:
        assert package.testzip() is None
        for name,digest in hashes.items():
            assert hashlib.sha256(package.read(prefix+name)).hexdigest()==digest
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n')
    print(json.dumps(dict(path=str(dest),files=len(hashes),bytes=dest.stat().st_size,sha256=digest)))


if __name__=='__main__':
    main()
