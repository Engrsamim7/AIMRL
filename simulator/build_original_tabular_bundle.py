"""Package the faithful original tabular reproduction and repaired study."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from run_original_tabular_study import fingerprint
ROOT = Path(__file__).resolve().parents[1]

def main():
    report = ROOT / 'revision/original-tabular-results'
    run = ROOT / 'simulator/out/original-tabular-study'
    verify = json.loads((report / 'verification.json').read_text())
    meta = json.loads((run / 'pipeline.json').read_text())
    assert verify['status'] == 'passed' and meta['status'] == 'completed'
    assert verify['source_hash'] == meta['source_hash'] == fingerprint()
    for name in ['design.json', 'pipeline.json', 'locked_settings.json']:
        shutil.copy2(run / name, report / name)
    files = []
    for p in (ROOT / 'simulator').rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix == '.pyc':
            continue
        rel = p.relative_to(ROOT / 'simulator')
        if rel.parts[0] == 'figs':
            continue
        if rel.parts[0] == 'out' and (len(rel.parts) < 3 or rel.parts[1] != 'original-tabular-study'):
            continue
        files.append(p)
    files.extend(p for p in report.rglob('*') if p.is_file())
    files.extend(p for p in (ROOT / 'revision/submission-code').rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    for name in ['requirements-lock.txt', 'requirements-actor-aware.txt', 'setup_local.sh',
                 '.gitignore', '.gitattributes',
                 'revision/submission-code-audit/original_network_seed42.json',
                 'revision/original-tabular-protocol.md', 'revision/original-tabular-findings.md']:
        files.append(ROOT / name)
    dest = ROOT / 'deliverables'
    dest.mkdir(exist_ok=True)
    shutil.copy2(report / 'original_tabular_report.pdf', dest / 'AIMRL-original-tabular-figures.pdf')
    files.append(dest / 'AIMRL-original-tabular-figures.pdf')
    start = '''# Original tabular AMMARL: reproduction and repairs

Start with revision/original-tabular-findings.md and revision/original-tabular-results/README.md. Open original_tabular_report.pdf or index.html in that report folder for eight figures.

The original hub-indexed tabular Q learner and fixed FRC gate are retained. Original AMMARL/IQL route scores reproduce 0.876/0.857, but actual delivery is 100% and original M4 hazard use is zero. The original ungated 0.851 presentation score is not reproduced. Repaired FRC and ALL also tie in this test. These findings do not establish gate superiority or survival probability.

Includes all 17 byte-preserved uploads and their inventory, full simulator Python source, 25 historical inference models, five closest-repair models, 80 controlled models, raw training/validation/evaluation records, locked settings, CSV tables and eight figures. Prior studies remain in separate historical ZIPs; their raw data are not duplicated here.

From the extracted root run bash setup_local.sh. The new tabular study uses the base pinned requirements. Install requirements-actor-aware.txt additionally to run all historical regression tests: .venv/bin/python -m pip install -r requirements-actor-aware.txt. Then .venv/bin/python -m pytest simulator/tests*.py. See the report README for study/report commands. Use the same Python 3.12 environment for reproducibility. Checkpoints support inference, not exact interrupted-training resumption. SHA-256 hashes are in BUNDLE_MANIFEST.json.
'''
    files = sorted(set(files))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    hashes['START_HERE.md'] = hashlib.sha256(start.encode()).hexdigest()
    archive = dest / 'AIMRL-original-tabular-study.zip'
    prefix = 'AIMRL-original-tabular-study/'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, prefix + str(p.relative_to(ROOT)))
        z.writestr(prefix + 'START_HERE.md', start)
        z.writestr(prefix + 'BUNDLE_MANIFEST.json', json.dumps(dict(source_hash=fingerprint(), files=hashes), indent=2) + '\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name, digest in hashes.items():
            assert hashlib.sha256(z.read(prefix + name)).hexdigest() == digest
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
    print(json.dumps(dict(path=str(archive), files=len(hashes), bytes=archive.stat().st_size, sha256=digest)))

if __name__ == '__main__':
    main()
