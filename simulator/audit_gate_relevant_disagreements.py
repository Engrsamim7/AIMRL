"""Exploratory follow-up: exhaust the public-state relevant disagreements.

Added after chronological sampling revealed many irrelevant early packets.
Reuses the same 512 trajectories; these are not independent new evaluations.
"""
import argparse
import copy
import hashlib
import heapq
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import pandas as pd
import torch
from ammarl2.sim import DEPART
from research_cases import fork_graph
from research_gate import ValueEnsemble
from run_matched_gate_study import TEST_CASES, load_actor, weight_hash
from run_cover_traffic_stress import simulation
from run_reviewer_revision import write_json
from diagnose_gate_decisions import audited, effects, encoded_rows, fingerprint as parent_hash


def fingerprint():
    h=hashlib.sha256(parent_hash().encode());h.update(Path(__file__).read_bytes());return h.hexdigest()


def selected(record,reachable):
    return record['category']=='disagreement' and (record['action_change']>.5 or (record['peer_blocked']>.5 and reachable))


def job(args):
    algo,seed,parent=args;torch.set_num_threads(1);parent=Path(parent)
    actor=load_actor(parent/'models'/f'{algo}_s{seed}_COMBINED.pt');initial=weight_hash(actor)
    model=ValueEnsemble.load(json.loads((parent/'value_models'/f'{algo}_s{seed}.json').read_text())['model'])
    rows=[];raw=[]
    for gi in range(2):
        g,h=fork_graph(59000+gi,3+gi%2)
        for ci,case in enumerate(TEST_CASES):
            for ep in range(2):
                key=dict(algo=algo,seed=seed,graph=gi,case=case.name,episode=ep)
                p=audited('COMBINED',actor,model,collect=True);snaps=[]
                def capture(s,cv,t):
                    if not cv.inbox:return
                    hook=s.before_decision;s.before_decision=None;logs=p.audit_records;p.audit_records=[]
                    try:b=copy.deepcopy(s)
                    finally:s.before_decision=hook;p.audit_records=logs
                    b.policy.collect=False;heapq.heappush(b.ev,(t,-1,DEPART,cv.id));snaps.append((b,cv.id,float(t)))
                s=simulation(g,h,case,p,65000000+gi*10000+ci*100+ep);s.before_decision=capture;result=s.run()
                raw.extend(dict(**key,method='COMBINED',**r) for r in result['rows'])
                for b,cid,t in snaps:
                    for r in p.audit_records:
                        if r['convoy']!=cid or r['t']!=t:continue
                        reachable=b.policy.relevant(b,b.cv[cid],r['edge'],[])
                        if not selected(r,reachable):continue
                        measured=effects(b,cid,t,r['id'])
                        assert measured['accept_rows' if r['accepted'] else 'reject_rows']==encoded_rows(result['rows'])
                        rows.append(dict(**key,**r,public_reachable=reachable,**measured))
    assert weight_hash(actor)==initial
    print(f'RELEVANT {algo} seed={seed}: {len(rows)} exhaustive replay pairs',flush=True)
    return rows,raw


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',default='out/matched-gate-study');ap.add_argument('--output',default='out/gate-decision-targeted-audit');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False);initial=fingerprint()
    write_json(out/'design.json',dict(source_hash=initial,status='exploratory_targeted_followup_after_initial_diagnosis',reason='chronological sample includes many irrelevant packets; exhaust action-changing or reachable peer-warning disagreements',selection='category disagreement AND (public actor action-probe changes OR existing peer warning on publicly reachable edge)',coverage='all qualifying packets on same 512 original COMBINED trajectories; no outcome/origin selection; no new independent tapes',new_confirmatory_tests=0))
    write_json(out/'pipeline.json',dict(status='running',source_hash=initial))
    rows=[];raw=[]
    tasks=[(x,s,str(Path(a.parent).resolve())) for x in ['dqn','mappo'] for s in range(8)]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for effects_,outcomes in pool.map(job,tasks):rows.extend(effects_);raw.extend(outcomes)
    pd.DataFrame(rows).to_csv(out/'effects.csv.gz',index=False);pd.DataFrame(raw).to_csv(out/'reference_convoys.csv.gz',index=False)
    assert fingerprint()==initial
    write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,reused_original_episodes=512,replay_pairs=len(rows),reference_convoys=len(raw),new_confirmatory_tests=0))
    print('RELEVANT AUDIT COMPLETE',flush=True)

if __name__=='__main__':main()
