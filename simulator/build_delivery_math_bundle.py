"""Portable analysis/development supplement; historical study ZIP is unchanged."""
import hashlib
import json
from pathlib import Path
import zipfile
from run_delivery_learning import fingerprint

ROOT=Path(__file__).resolve().parents[1]


def main():
    parent=ROOT/'simulator/out/delivery-learning-v3'
    dev=ROOT/'simulator/out/delivery-value-scale-development'
    assert json.loads((parent/'pipeline.json').read_text())['source_hash']==fingerprint()
    assert json.loads((dev/'pipeline.json').read_text())['status']=='completed_development_only'
    old_archive=ROOT/'deliverables/AIMRL-delivery-learning-study.zip'
    old_sha=hashlib.sha256(old_archive.read_bytes()).hexdigest()
    assert old_sha==old_archive.with_suffix('.zip.sha256').read_text().split()[0]
    files=[]
    parent_items={'actors','gates','labels','calibration.json','design.json','pipeline.json','locked_settings.json','validation.csv.gz'}
    for p in (ROOT/'simulator').rglob('*'):
        if not p.is_file() or any(x in p.parts for x in ['__pycache__','.pytest_cache']) or p.suffix=='.pyc':continue
        rel=p.relative_to(ROOT/'simulator')
        if rel.parts[0]=='figs':continue
        if rel.parts[0]=='out':
            if len(rel.parts)<3:continue
            if rel.parts[1]=='delivery-learning-v3':
                if rel.parts[2] not in parent_items:continue
            elif rel.parts[1]!='delivery-value-scale-development':continue
        files.append(p)
    for name in ['revision/delivery-mathematical-analysis','revision/delivery-mathematical-inputs','revision/delivery-learning-results','revision/submission-code']:
        files.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc')
    for name in ['revision/delivery-mathematical-analysis.md','revision/delivery-learning-findings.md',
                 'revision/delivery-learning-protocol.md','revision/delivery-learning-reviewer-map.md',
                 'revision/submission-code-audit/original_network_seed42.json','requirements-lock.txt',
                 'requirements-actor-aware.txt','setup_local.sh','.gitignore','.gitattributes']:
        files.append(ROOT/name)
    start='''# Delivery mathematical diagnosis and controlled development ablation

Read revision/delivery-mathematical-analysis.md for the equations, evidence and
proposed design. The main numeric audit/figure is in
revision/delivery-mathematical-analysis/. No new superiority claim is made.

This supplement contains the audit code, complete simulator source, original
submitted code, numeric inputs, original frozen actors/gates/causal training
labels, saved validation contexts, the target-scale ablation models/results,
and the original published report tables. It excludes bulky original test
packet/convoy logs; those remain in AIMRL-delivery-learning-study.zip:
https://raw.githubusercontent.com/Engrsamim7/AIMRL/reviewer-complete-model-20261012/deliverables/AIMRL-delivery-learning-study.zip

Use the project environment, or bash setup_local.sh followed by
.venv/bin/python -m pip install -r requirements-actor-aware.txt.
The audit alone needs numpy2.3.5, pandas2.2.3 and matplotlib3.10.8.
Run from this extracted root:
.venv/bin/python simulator/analyze_delivery_gap.py

To repeat the controlled development ablation, use a FRESH destination:
.venv/bin/python simulator/run_delivery_value_scale_ablation.py --output simulator/out/value-scale-reproduction --report revision/value-scale-reproduction

Use MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 for both commands.
The ablation uses already-seen validation contexts only. It re-fits eight gates,
retains five fixed settings and runs960 validation method episodes. It reproduces
the eight original estimators exactly before fitting a different target scale.
No new test is run. The fixed-setting scale change did not improve observed
validation delivery. Richer beliefs, deadline-return critics and pre-transmission
control remain proposals, not implemented performance claims in this supplement.
'''
    files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
    dest=ROOT/'deliverables';archive=dest/'AIMRL-delivery-mathematical-analysis.zip';prefix='AIMRL-delivery-mathematical-analysis/'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,prefix+str(p.relative_to(ROOT)),compress_type=zipfile.ZIP_STORED if p.suffix=='.gz' else zipfile.ZIP_DEFLATED)
        z.writestr(prefix+'START_HERE.md',start)
        z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(original_study_fingerprint=fingerprint(),files=hashes),indent=2)+'\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,h in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==h,name
    digest=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
    result=dict(status='archive_integrity_passed',files=len(hashes),bytes=archive.stat().st_size,sha256=digest,original_study_sha256_unchanged=old_sha,
                original_simulator_fingerprint_unchanged=fingerprint(),new_test_episodes=0,public_downloads_verified=False)
    (dest/'AIMRL-delivery-mathematical-analysis-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
