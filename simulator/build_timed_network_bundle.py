"""Core ZIP plus verified trace ZIPs, each below GitHub's per-file size limit."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
ROOT=Path(__file__).resolve().parents[1]


def write_zip(archive,files,extra):
    prefix='AIMRL-timed-network-study/'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,prefix+str(p.relative_to(ROOT)),compress_type=zipfile.ZIP_STORED if p.suffix=='.gz' else zipfile.ZIP_DEFLATED)
        for name,contents in extra.items():z.writestr(prefix+name,contents)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
    return dict(name=archive.name,bytes=archive.stat().st_size,sha256=digest)


def main():
    report=ROOT/'revision/timed-network-results';verify=json.loads((report/'verification.json').read_text());assert verify['status']=='passed'
    surface=ROOT/'simulator/out/timed-network-surface';assert json.loads((surface/'TRACE_LAYOUT.json').read_text())['status']=='lossless_verified'
    files=[]
    runs=['timed-network-development-v2','timed-network-surface','timed-network-ablation']
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
        rel=p.relative_to(ROOT/'simulator')
        if rel.parts[0]=='figs':continue
        if rel.parts[0]=='out':
            if len(rel.parts)<3 or rel.parts[1] not in runs:continue
            if rel.parts[1]=='timed-network-surface' and p.name in ['decisions.csv.gz','packets.csv.gz']:continue
        files.append(p)
    files.extend(p for p in report.rglob('*') if p.is_file())
    files.extend(p for p in (ROOT/'revision/submission-code').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    for name in ['requirements-lock.txt','requirements-actor-aware.txt','setup_local.sh','.gitignore','.gitattributes',
                 'revision/submission-code-audit/original_network_seed42.json','revision/timed-network-findings.md',
                 'revision/timed-network-development-protocol.md','revision/timed-network-surface-protocol.md',
                 'revision/timed-network-ablation-protocol.md','revision/journal-network-acceptance-contract.md']:
        files.append(ROOT/name)
    dest=ROOT/'deliverables';dest.mkdir(exist_ok=True)
    shutil.copy2(report/'timed_network_report.pdf',dest/'AIMRL-timed-network-figures.pdf');files.append(dest/'AIMRL-timed-network-figures.pdf')
    files=sorted(set(files));core=[];traces=[]
    for p in files:
        rel=p.relative_to(ROOT)
        if 'out' in rel.parts and ('decisions_parts' in rel.parts or 'packets_parts' in rel.parts or p.name in ['decisions.csv.gz','packets.csv.gz']):traces.append(p)
        else:core.append(p)
    # Logical, independently extractable archives with a common root folder.
    groups=[];current=[];size=0
    for p in traces:
        if current and size+p.stat().st_size>42*1024**2:groups.append(current);current=[];size=0
        current.append(p);size+=p.stat().st_size
    if current:groups.append(current)
    downloads=[]
    for i,group in enumerate(groups,1):
        name=f'AIMRL-timed-network-traces-{i:02d}.zip';part_manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in group}
        info=write_zip(dest/name,group,{f'TRACE_PART_{i:02d}.json':json.dumps(part_manifest,indent=2)+'\n'})
        info['url']='https://raw.githubusercontent.com/Engrsamim7/AIMRL/reviewer-complete-model-20261012/deliverables/'+name;downloads.append(info)
    download_text=json.dumps(dict(scope='optional full packet/decision traces, extract into same core root; helper verifies hashes',archives=downloads),indent=2)+'\n'
    start='''# Timed-network revision: code, model and results

Start with revision/timed-network-findings.md and revision/timed-network-results/README.md. Open timed_network_report.pdf or index.html in that report folder for eight figures.

This is an executed new network model and a development study, not a trained MARL superiority result. It includes physical closures, time-consuming inspections, FIFO hub service, deadlines, local noisy observations, a training-fitted report interpreter and finite broadcast capacity. Original source files remain preserved. The value sender is a heuristic; its admission ablation and stronger scheduling baselines are retained, including adverse findings.

The core ZIP contains full source, report-interpreter model and calibration labels, validation settings, all 63,072 episode records / 504,576 convoy records, graph definitions, closure schedules, tables, figures and protocols. To retrieve the complete routing and packet traces, run Python 3.12 on simulator/fetch_timed_traces.py from this extracted folder. It downloads the additional public ZIPs, verifies SHA-256 and extracts them into the same root. Alternatively download every ZIP named in TRACE_DOWNLOADS.json and extract all into the same parent folder. BUNDLE_MANIFEST.json records every core and trace file. Every trace ZIP is independently extractable and stays below GitHub's file-size limit.

For execution run bash setup_local.sh. The network phase uses the base pinned environment. The full 142-test historical suite additionally needs requirements-actor-aware.txt. Reproduction commands are in the report README. Raw large surface traces are losslessly partitioned CSV.gz files; the reporter supports the original single stream or these shards. TRACE_LAYOUT.json verifies reconstruction against the original CSV stream hashes. This package does not claim operational military validity, convergence, calibrated safety or universal superiority.
'''
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest();hashes['TRACE_DOWNLOADS.json']=hashlib.sha256(download_text.encode()).hexdigest()
    manifest=json.dumps(dict(scope=verify['scope'],source_hash=verify['source_hash'],surface_hash=verify['surface_hash'],ablation_hash=verify['ablation_hash'],files=hashes),indent=2)+'\n'
    archive=dest/'AIMRL-timed-network-study.zip'
    main=write_zip(archive,core,{'START_HERE.md':start,'TRACE_DOWNLOADS.json':download_text,'BUNDLE_MANIFEST.json':manifest})
    validation=dict(status='archive_integrity_passed',manifest_files=len(hashes),core=main,traces=downloads,extracted_package_tests=None,report_regeneration_exact=None,public_downloads_verified=False)
    (dest/'AIMRL-timed-network-validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    assert all(p['bytes']<100*1024**2 for p in downloads+[main])
    print(json.dumps(dict(core=main,traces=len(downloads),manifest_files=len(hashes))),flush=True)
if __name__=='__main__':main()
