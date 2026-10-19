"""Fetch and verify the optional full trace archives after extracting the core ZIP."""
import hashlib
import json
from pathlib import Path
import shutil
import time
from urllib.request import urlopen
import zipfile
ROOT=Path(__file__).resolve().parents[1]


def main():
    downloads=json.loads((ROOT/'TRACE_DOWNLOADS.json').read_text())
    manifest=json.loads((ROOT/'BUNDLE_MANIFEST.json').read_text())['files']
    cache=ROOT/'trace_downloads';cache.mkdir(exist_ok=True)
    for part in downloads['archives']:
        local=cache/part['name']
        if not local.exists() or hashlib.sha256(local.read_bytes()).hexdigest()!=part['sha256']:
            for attempt in range(3):
                try:
                    with urlopen(part['url'],timeout=120) as src,local.open('wb') as dest:shutil.copyfileobj(src,dest)
                    assert hashlib.sha256(local.read_bytes()).hexdigest()==part['sha256']
                    break
                except Exception:
                    if attempt==2:raise
                    time.sleep(attempt+1)
        with zipfile.ZipFile(local) as z:
            assert z.testzip() is None
            for member in z.namelist():
                prefix='AIMRL-timed-network-study/'
                if not member.startswith(prefix):raise ValueError('Unexpected archive prefix')
                relative=member[len(prefix):]
                if relative.startswith('TRACE_PART_'):continue
                if relative not in manifest:raise ValueError('Unexpected archive member')
                target=(ROOT/relative).resolve()
                if not target.is_relative_to(ROOT):raise ValueError('Unsafe archive path')
                data=z.read(member)
                assert hashlib.sha256(data).hexdigest()==manifest[relative]
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        print('Verified and extracted',part['name'],flush=True)
    for name,digest in manifest.items():
        p=ROOT/name
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
    print('Complete code, model, results and trace manifest verified.',flush=True)
if __name__=='__main__':main()
