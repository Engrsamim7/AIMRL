"""Portable full-source, checkpoint, raw-data and figure delivery."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from run_recovery_gate_study import fingerprint
ROOT=Path(__file__).resolve().parents[1]

def main():
 run=ROOT/'simulator/out/recovery-gate-study';report=ROOT/'revision/recovery-gate-results'
 check=json.loads((report/'verification.json').read_text());meta=json.loads((run/'pipeline.json').read_text())
 assert check['status']=='passed' and meta['status']=='completed' and check['source_hash']==fingerprint()
 files=[]
 for p in (ROOT/'simulator').rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix=='.pyc':continue
  rel=p.relative_to(ROOT/'simulator')
  if rel.parts[0]=='figs':continue
  if rel.parts[0]=='out' and (len(rel.parts)<3 or rel.parts[1]!='recovery-gate-study'):continue
  files.append(p)
 files.extend(p for p in report.rglob('*') if p.is_file())
 for name in ['requirements-lock.txt','setup_local.sh','.gitignore','.gitattributes','revision/submission-code-audit/original_network_seed42.json','revision/recovery-gate-protocol.md','revision/recovery-gate-findings.md','revision/recovery-gate-reviewer-map.md','revision/gate-decision-diagnosis-findings.md']:files.append(ROOT/name)
 dest=ROOT/'deliverables';dest.mkdir(exist_ok=True);shutil.copy2(report/'recovery_gate_report.pdf',dest/'AIMRL-recovery-gate-figures.pdf');files.append(dest/'AIMRL-recovery-gate-figures.pdf')
 start=('# Dynamic-recovery learned gate study\n\n'
 'Read revision/recovery-gate-findings.md for the claim and limitations; revision/recovery-gate-results/README.md for complete tables; open revision/recovery-gate-results/recovery_gate_report.pdf or index.html for eight figures.\n\n'
 'This package contains full Python source,80 final routing checkpoints,32 initial/refreshed gate estimators, all training records, paired causal labels with accept/reject convoy outcomes encoded as JSON in CSV cells, validation candidates and locked settings,102400 final-test method episodes (512000 convoy records),7680 descriptive fixed-actor ablation episodes, all result tables and figures. Large tables are CSV.gz. These routing checkpoints support inference; optimizer/replay state is not serialized for exact training resumption. Rerun training from the deterministic source workflow. Older study raw data are in their separate historical ZIPs.\n\n'
 'Run bash setup_local.sh for the pinned environment. Reproduction commands are in revision/recovery-gate-results/README.md and the prospective protocol. Run from the extracted root. Use a fresh output folder for a new experiment.\n\n'
 'The gate cannot access hidden hazard schedules or real packet origin. Its estimated risk and bootstrap disagreement are heuristic, not calibrated safety guarantees. Utility success requires delivery noninferiority within a declared simulation tolerance; this is not operational validation or universal superiority. Auxiliary label fitting has extra compute. All test conditions and failures are retained.\n')
 files=sorted(set(files));hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};hashes['START_HERE.md']=hashlib.sha256(start.encode()).hexdigest()
 archive=dest/'AIMRL-recovery-gate-study.zip';prefix='AIMRL-recovery-gate-study/'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,prefix+str(p.relative_to(ROOT)))
  z.writestr(prefix+'START_HERE.md',start);z.writestr(prefix+'BUNDLE_MANIFEST.json',json.dumps(dict(source_hash=fingerprint(),files=hashes),indent=2)+'\n')
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,h in hashes.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==h
 digest=hashlib.sha256(archive.read_bytes()).hexdigest();archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
 print(json.dumps(dict(path=str(archive),files=len(hashes),bytes=archive.stat().st_size,sha256=digest)))
if __name__=='__main__':main()
