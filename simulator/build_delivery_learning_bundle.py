"""Deliver the delivery-primary study without changing historical archives."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from run_delivery_learning import fingerprint

ROOT = Path(__file__).resolve().parents[1]


def main():
    run = ROOT / 'simulator/out/delivery-learning-v3'
    report = ROOT / 'revision/delivery-learning-results'
    verify = json.loads((report / 'verification.json').read_text())
    assert verify['status'] == 'passed' and verify['source_hash'] == fingerprint()
    assert json.loads((run / 'pipeline.json').read_text())['status'] == 'completed'
    stopped = {}
    for version, folder in [('v1', 'delivery-learning'), ('v2', 'delivery-learning-v2')]:
        old = ROOT / 'simulator/out' / folder
        archived = ROOT / 'revision' / f'delivery-learning-{version}-source'
        h = hashlib.sha256()
        for name in ['delivery_learning.py', 'run_delivery_learning.py']:
            h.update((archived / name).read_bytes())
        for name in ['timed_network.py', 'ammarl2/graph.py', 'ammarl2/reviewer.py', '../revision/submission-code-audit/original_network_seed42.json']:
            h.update((ROOT / 'simulator' / name).read_bytes())
        meta = json.loads((old / 'pipeline.json').read_text())
        assert meta['source_hash'] == h.hexdigest() and meta['status'].startswith('stopped_before_test')
        assert not (old / 'locked_settings.json').exists() and not (old / 'episodes.csv.gz').exists()
        stopped[version] = dict(source_hash=h.hexdigest(), status=meta['status'])
    files = []
    for p in (ROOT / 'simulator').rglob('*'):
        if not p.is_file() or any(x in p.parts for x in ['__pycache__', '.pytest_cache']) or p.suffix == '.pyc':
            continue
        rel = p.relative_to(ROOT / 'simulator')
        if rel.parts[0] == 'figs':
            continue
        if rel.parts[0] == 'out' and (len(rel.parts) < 3 or rel.parts[1] not in ['delivery-learning-v3', 'delivery-learning-v2', 'delivery-learning']):
            continue
        files.append(p)
    for folder in [report, ROOT / 'revision/submission-code', ROOT / 'revision/delivery-learning-v1-source', ROOT / 'revision/delivery-learning-v2-source']:
        files.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    for name in ['requirements-lock.txt', 'requirements-actor-aware.txt', 'setup_local.sh', '.gitignore', '.gitattributes',
                 'revision/submission-code-audit/original_network_seed42.json',
                 'simulator/out/timed-network-development-v2/calibration.json',
                 'revision/delivery-learning-protocol.md', 'revision/delivery-learning-findings.md',
                 'revision/delivery-learning-reviewer-map.md',
                 'revision/timed-network-findings.md']:
        files.append(ROOT / name)
    start = '''# Delivery-primary learned routing and causal gate

Read revision/delivery-learning-findings.md for actual results and limitations.
Open revision/delivery-learning-results/delivery_learning_report.pdf or index.html
for seven figures; summary.csv and primary_contrasts.csv contain primary results.

The package contains complete simulator source, the original submitted code,
eight selected routing checkpoints and all checkpoint candidates, eight gate
estimators, all training and validation records, complete paired causal labels,
locked settings, raw held-out episode/convoy/gate decisions, tables and figures.
Both stopped development passes and their exact source are retained separately;
neither executed held-out testing. Earlier studies have separate archives.

Install with bash setup_local.sh, followed by
.venv/bin/python -m pip install -r requirements-actor-aware.txt.
Run from this extracted root. Full commands are in the results README.
The fixed parent calibration file is included at its original relative path.
Models support inference, not exact optimizer/replay training resumption.

Fleet on-time delivery is the objective. The common frozen routing policies
isolate gate effects; comparators are not each independently retrained for their
receiver. The gate has one shared fleet rejection token. Tree dispersion is
heuristic uncertainty. Neither universal superiority, learning convergence,
fully decentralized coordination nor operational validity is established.
'''
    dest = ROOT / 'deliverables'
    dest.mkdir(exist_ok=True)
    shutil.copy2(report / 'delivery_learning_report.pdf', dest / 'AIMRL-delivery-learning-figures.pdf')
    files = sorted(set(files))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    hashes['START_HERE.md'] = hashlib.sha256(start.encode()).hexdigest()
    manifest = json.dumps(dict(source_hash=fingerprint(), files=hashes), indent=2) + '\n'
    archive = dest / 'AIMRL-delivery-learning-study.zip'
    prefix = 'AIMRL-delivery-learning-study/'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, prefix + str(p.relative_to(ROOT)), compress_type=zipfile.ZIP_STORED if p.suffix == '.gz' else zipfile.ZIP_DEFLATED)
        z.writestr(prefix + 'START_HERE.md', start)
        z.writestr(prefix + 'BUNDLE_MANIFEST.json', manifest)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name, digest in hashes.items():
            assert hashlib.sha256(z.read(prefix + name)).hexdigest() == digest
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
    result = dict(status='archive_integrity_passed', archive=archive.name, bytes=archive.stat().st_size,
                  sha256=digest, manifest_files=len(hashes), extracted_package_tests=None,
                  report_regeneration_exact=None, stopped_development_sources=stopped, public_downloads_verified=False)
    assert result['bytes'] < 100 * 1024**2, 'Split traces before GitHub delivery if this exceeds its file limit'
    (dest / 'AIMRL-delivery-learning-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
