"""Portable evidence for the journal-readiness diagnosis, without superiority claims."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    report=ROOT/'revision/journal-readiness'
    verify=json.loads((report/'verification.json').read_text());assert verify['status']=='passed'
    audit=ROOT/'simulator/out/tabular-decision-audit-verified'
    assert json.loads((audit/'verification.json').read_text())['status']=='passed'
    files=[]
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
        rel=p.relative_to(ROOT/'simulator')
        if rel.parts[0]=='figs':continue
        if rel.parts[0]=='out' and (len(rel.parts)<3 or rel.parts[1] not in ['original-tabular-study','tabular-decision-audit-verified']):continue
        files.append(p)
    for folder in ['revision/journal-readiness','revision/original-tabular-results','revision/submission-code']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    for name in ['requirements-lock.txt','requirements-actor-aware.txt','setup_local.sh','.gitignore','.gitattributes',
                 'revision/submission-code-audit/original_network_seed42.json',
                 'revision/journal-readiness-assessment.md','revision/journal-readiness-protocol.md',
                 'revision/journal-network-acceptance-contract.md','revision/original-tabular-protocol.md',
                 'revision/original-tabular-findings.md']:
        files.append(ROOT/name)
    dest=ROOT/'deliverables';dest.mkdir(exist_ok=True)
    shutil.copy2(report/'journal_readiness.pdf',dest/'AIMRL-journal-readiness-figures.pdf')
    files.append(dest/'AIMRL-journal-readiness-figures.pdf')
    start='''# Journal-readiness diagnosis: the current superiority manuscript is not ready

Start with revision/journal-readiness-assessment.md. Open revision/journal-readiness/journal_readiness.pdf or index.html for four figures. The original-family study is archived unchanged; the new audit reproduces its outcomes and finds no ALL/FRC/NONE next-hop changes across 518,400 frozen-policy decisions. None offers a physically blocked available outgoing option.

The 432-cell exact decision benchmark is model validation, NOT a new logistics/MARL performance experiment. It uses known closure dynamics and calibrated sensor accuracy to demonstrate the limits of fixed freshness filtering and the role of an age-aware baseline. It does not establish journal readiness, combat survival, general superiority or a deployed learned gate.

Includes complete simulator source, all 17 preserved uploads, the original-tabular parent raw data and 110 inference checkpoints, all audit decisions, exact-reference cells and branches, tables, figures, protocol and an explicitly prospective next-network acceptance contract. Other historical study data remain in their original ZIPs.

Reproduce from extracted root: bash setup_local.sh. Install requirements-actor-aware.txt additionally to run all historical tests, then .venv/bin/python -m pytest simulator/tests*.py. The current suite has 129 tests. Use Python 3.12. The new audit and exact reference only require the base environment. See revision/journal-readiness/README.md for reproduction commands. Set MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1. BUNDLE_MANIFEST.json records every included file hash.
'''
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
    archive=dest/'AIMRL-journal-readiness.zip';prefix='AIMRL-journal-readiness/'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,prefix+str(p.relative_to(ROOT)))
        z.writestr(prefix+'START_HERE.md',start)
        z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(scope=verify['scope'],code_hashes=verify['code_hashes'],files=hashes),indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==digest
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
    print(json.dumps(dict(path=str(archive),bytes=archive.stat().st_size,files=len(hashes),sha256=digest)))

if __name__=='__main__':main()
