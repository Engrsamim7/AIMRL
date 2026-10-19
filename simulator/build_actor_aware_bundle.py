"""Portable development study, with existing parent SAFE inference checkpoints."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from run_actor_aware_development import fingerprint
ROOT=Path(__file__).resolve().parents[1]

def main():
 report=ROOT/'revision/actor-aware-development-results';run=ROOT/'simulator/out/actor-aware-development';parent=ROOT/'simulator/out/recovery-gate-study'
 verify=json.loads((report/'verification.json').read_text());meta=json.loads((run/'pipeline.json').read_text());assert verify['status']=='passed' and meta['status']=='completed' and verify['source_hash']==fingerprint()
 lock=json.loads((run/'locked_settings.json').read_text());files=[]
 for p in (ROOT/'simulator').rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
  rel=p.relative_to(ROOT/'simulator')
  if rel.parts[0]=='figs':continue
  if rel.parts[0]=='out' and (len(rel.parts)<3 or rel.parts[1]!='actor-aware-development'):continue
  files.append(p)
 for name in lock['routing_models']:files.append(parent/'models'/name)
 files.extend(p for p in report.rglob('*') if p.is_file())
 for name in ['requirements-lock.txt','requirements-actor-aware.txt','setup_local.sh','.gitignore','.gitattributes','revision/submission-code-audit/original_network_seed42.json','revision/actor-aware-development-protocol.md','revision/actor-aware-development-findings.md','revision/recovery-gate-findings.md','revision/recovery-gate-protocol.md']:files.append(ROOT/name)
 dest=ROOT/'deliverables';shutil.copy2(report/'actor_aware_development.pdf',dest/'AIMRL-actor-aware-development-figures.pdf');files.append(dest/'AIMRL-actor-aware-development-figures.pdf')
 start=('# Actor-aware fleet-value development\n\n'
 'Start with revision/actor-aware-development-findings.md and revision/actor-aware-development-results/README.md. Open actor_aware_development.pdf or index.html in that report folder for six figures.\n\n'
 'This is development evidence, not a new superiority confirmation. Sixteen parent SAFE-trained actors are frozen existing checkpoints, not new routing-training seeds. The32 new forest estimators use complete-inbox public actor probes and fleet-value labels. One learned override is allowed over the entire fleet episode, then SAFE resumes. Tree dispersion is heuristic, not calibrated safety.\n\n'
 'Includes full simulator/new-study Python source, parent SAFE inference checkpoints, new estimators in non-pickle NPZ form, selected intervention labels with both full-fleet branches as JSON CSV cells, all6144 factual development episodes,39936 calibration method episodes,6144 audit method episodes/30720 convoy records, settings, tables and figures. Older studies and their raw data remain in separate historical ZIPs.\n\n'
 'Reproduce from extracted root: bash setup_local.sh; .venv/bin/python -m pip install -r requirements-actor-aware.txt. See report README for exact commands. Inference forest loading uses NumPy; fitting additionally requires the pinned scikit-learn packages. Routing checkpoints support inference, not exact optimizer/replay training resumption. Every listed file has a SHA-256 hash in BUNDLE_MANIFEST.json.\n')
 files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest();archive=dest/'AIMRL-actor-aware-development.zip';prefix='AIMRL-actor-aware-development/'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,prefix+str(p.relative_to(ROOT)))
  z.writestr(prefix+'START_HERE.md',start);z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),files=hashes),indent=2)+'\n')
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,h in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==h
 digest=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n');print(json.dumps(dict(path=str(archive),files=len(hashes),bytes=archive.stat().st_size,sha256=digest)))
if __name__=='__main__':main()
