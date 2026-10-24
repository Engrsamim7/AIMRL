"""Retrospective development ablation of multi-output target units.

No new held-out test and no changes to the completed v3 source or models.
Only target scaling changes: fleet fractions versus on-time convoy counts.
Predicted mean/dispersion are converted back before applying identical rules.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np
import pandas as pd
import torch
from delivery_learning import ReturnGate
from run_delivery_learning import SEEDS, SETTINGS, fingerprint, validate_job


def fit_scaled(task):
    seed, parent, dest = task
    torch.set_num_threads(1)
    frame = pd.read_csv(Path(parent) / 'labels' / f's{seed}.csv.gz')
    frame = frame[~frame.control]
    x = np.array([json.loads(v) for v in frame.features], np.float32)
    y = frame.delta.to_numpy()
    # Re-fitting scale1 must reproduce the existing estimator before a new
    # scale is tested; this checks input order, parameters and serialization.
    original = ReturnGate.load(Path(parent) / 'gates' / f's{seed}.npz')
    reproduced = ReturnGate().fit(x, y, 8400 + seed)
    for row in x:
        assert np.array_equal(original.predict(row), reproduced.predict(row))
    gate = ReturnGate().fit(x, 8*y, 8400 + seed)
    gate.values[:, :, 0] /= 8.
    gate.save(Path(dest) / 'gates' / f's{seed}.npz')
    print(f'FITTED SCALED VALUE seed={seed}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent', default='simulator/out/delivery-learning-v3')
    ap.add_argument('--output', default='simulator/out/delivery-value-scale-development')
    ap.add_argument('--report', default='revision/delivery-mathematical-analysis')
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    parent, dest, report = Path(args.parent).resolve(), Path(args.output).resolve(), Path(args.report)
    expected = json.loads((parent/'pipeline.json').read_text())['source_hash']
    assert expected == fingerprint()
    lock = json.loads((parent/'locked_settings.json').read_text())
    for folder in ['actors','gates']:
        for name,h in lock[folder].items():
            assert hashlib.sha256((parent/folder/name).read_bytes()).hexdigest() == h
    dest.mkdir(parents=True, exist_ok=False)
    for folder in ['actors','gates']:
        (dest/folder).mkdir()
    for p in (parent/'actors').glob('*.json'): shutil.copy2(p, dest/'actors'/p.name)
    shutil.copy2(parent/'calibration.json', dest/'calibration.json')
    design = dict(scope='Retrospective development ablation; no held-out testing.',
        source_hash=expected,ablation_script_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        value_scales=[1,8],model_seeds=SEEDS,settings=SETTINGS,
        changed='Only regression-target scale during multi-output tree fitting; value mean and dispersion divided by8 before identical decisions.',
        fixed='Same labels, actor checkpoints, random tree seeds, hyperparameters, physical validation contexts, benefit-risk rule and thresholds.',
        primary_development_comparison='Scale8 minus scale1 at existing setting1; all five settings retained. No new winner is declared confirmatory.',
        dependence='192 actor rows per setting share24 physical contexts on two weighted graphs.',
        caution='A scale effect is an estimator-design sensitivity, not evidence of new-test superiority.')
    (dest/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    start=time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(fit_scaled,[(s,str(parent),str(dest)) for s in SEEDS]))
        rows=[]
        for i, block in enumerate(pool.map(validate_job,[(s,g,str(dest)) for s in SEEDS for g in range(2)])):
            rows.extend(block)
            print(f'VALIDATION {i+1}/16',flush=True)
    scaled=pd.DataFrame(rows)
    scaled.to_csv(dest/'validation.csv.gz',index=False)
    old=pd.read_csv(parent/'validation.csv.gz')
    keys=['seed','graph','case','episode','setting']
    paired=scaled.merge(old,on=keys,suffixes=('_scaled','_original'),validate='one_to_one')
    assert len(paired)==960 and fingerprint()==expected
    disabled=paired[paired.setting==0]
    assert disabled.on_time_scaled.eq(disabled.on_time_original).all()
    paired['difference_pp']=100*(paired.on_time_scaled-paired.on_time_original)
    records=[]
    for setting,frame in paired.groupby('setting'):
        clusters=frame.groupby(['graph','case','episode']).difference_pp.mean()
        records.append(dict(setting=int(setting),original_on_time_pct=100*frame.on_time_original.mean(),scaled_on_time_pct=100*frame.on_time_scaled.mean(),difference_pp=frame.difference_pp.mean(),
            original_rejections_per_episode=frame.rejections_original.mean(),scaled_rejections_per_episode=frame.rejections_scaled.mean(),
            actor_rows=len(frame),shared_environment_clusters=len(clusters),cluster_difference_sd_pp=clusters.std(ddof=1)))
    report.mkdir(parents=True,exist_ok=True)
    table=pd.DataFrame(records)
    table.to_csv(report/'value_scale_development_ablation.csv',index=False)
    paired[keys+['difference_pp','on_time_scaled','on_time_original','rejections_scaled','rejections_original']].to_csv(report/'value_scale_development_pairs.csv',index=False)
    meta=dict(status='completed_development_only',source_hash=expected,ablation_script_hash=design['ablation_script_hash'],
        seconds=time.perf_counter()-start,original_models_reproduced_exactly=8,validation_rows=len(paired),new_test_episodes=0,
        primary_setting1_difference_pp=float(table[table.setting==1].difference_pp.iloc[0]))
    (dest/'pipeline.json').write_text(json.dumps(meta,indent=2)+'\n')
    (report/'value_scale_development_verification.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta),flush=True)


if __name__=='__main__': main()
