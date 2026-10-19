"""Losslessly partition large CSV trace streams for portable GitHub delivery."""
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path


def partition(name):
 folder=Path('simulator/out/timed-network-surface');source=folder/(name+'.csv.gz');dest=folder/(name+'_parts');dest.mkdir(exist_ok=False)
 digest=hashlib.sha256();parts=[];count=0
 with gzip.open(source,'rb') as inp:
  header=inp.readline();digest.update(header);index=0
  while True:
   first=inp.readline()
   if not first:break
   target=dest/f'part{index:03d}.csv.gz';n=0
   with gzip.open(target,'wb',compresslevel=6) as out:
    out.write(header);line=first
    for i in range(200000):
     if not line:break
     out.write(line);digest.update(line);n+=1
     if i<199999:line=inp.readline()
   parts.append(dict(file=str(target.relative_to(folder)),rows=n,sha256=hashlib.sha256(target.read_bytes()).hexdigest()));count+=n;index+=1
 # Verify that headers and rows reconstruct precisely the original CSV stream.
 check=hashlib.sha256();seen=0
 for i,part in enumerate(parts):
  with gzip.open(folder/part['file'],'rb') as inp:
   h=inp.readline();assert h==header
   if i==0:check.update(h)
   for line in inp:check.update(line);seen+=1
 assert seen==count and check.hexdigest()==digest.hexdigest()
 return dict(name=name,rows=count,original_gzip_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),csv_sha256=digest.hexdigest(),parts=parts)


def main():
 with ProcessPoolExecutor(max_workers=2) as pool:result=list(pool.map(partition,['decisions','packets']))
 path=Path('simulator/out/timed-network-surface/TRACE_LAYOUT.json');path.write_text(json.dumps(dict(status='lossless_verified',traces=result),indent=2)+'\n')
 print(json.dumps({r['name']:dict(rows=r['rows'],parts=len(r['parts'])) for r in result}),flush=True)
if __name__=='__main__':main()
