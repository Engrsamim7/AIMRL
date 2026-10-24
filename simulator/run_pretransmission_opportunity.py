"""Specified development mechanism study; no learned controller or new test."""
import argparse
import copy
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict,replace
import hashlib
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import torch
from delivery_learning import DeliveryNetwork
from pretransmission import PreTransmissionNetwork,paired_radio,RADIO_FEATURES
from run_delivery_learning import SEEDS,TEST,load_actor,model_for,fingerprint as parent_fingerprint
from timed_network import graph_for

ROOT=Path(__file__).resolve().parent


def fingerprint():
    h=hashlib.sha256(parent_fingerprint().encode())
    for name in ['pretransmission.py','run_pretransmission_opportunity.py']:h.update((ROOT/name).read_bytes())
    return h.hexdigest()


def job(task):
    si,gi,parent,output=task;torch.set_num_threads(1)
    actor=load_actor(parent,si);model=model_for(parent);g=graph_for(860010+gi,[19,51,131][gi])
    episodes=[];batch_episodes=[];labels=[];raw=[]
    for ci,original in enumerate(TEST):
        capacities=[0.] if original.name=='unlimited' else [.25,1.]
        for bi,bw in enumerate(capacities):
            case=replace(original,packet_time=bw)
            for ep in range(2):
                seed=860000000+gi*100000+ci*1000+bi*100+ep
                target=[1,3,8,16][(si+gi+ci+bi+ep)%4];captured=[]
                s=PreTransmissionNetwork(g,case,'VALUE',seed,model,value_threshold=0.,actor=actor,receiver='ALL')
                def capture(env):
                    if env.reservation_count==target:
                        captured.append(dict(t=env.t,packet=copy.deepcopy(env.reservation['packet']),features=env.radio_features().tolist()))
                        return True
                    return False
                s.radio_capture=capture;out=s.run();pair={}
                if out is None:
                    actions=['send','drop']
                    if bw>0:actions.append('defer')
                    if any(p.get('ready_at',-np.inf)<=s.t for p in s.radio):actions.append('swap')
                    pair=paired_radio(s,actions)
                    s.radio_capture=None;s.intervene('send');out=s.advance(initialize=False)
                    assert pair['send']==out,'Factual reservation continuation must reproduce uninterrupted outcome'
                result,convoys=out
                if ci==0 and bi==0 and ep==0:
                    reference=DeliveryNetwork(g,case,'VALUE',seed,model,value_threshold=0.,actor=actor,receiver='ALL')
                    assert reference.run()==out,'No-op pilot must preserve original actor/physics exactly'
                key=dict(actor_seed=si,graph=gi,size=g.n,case=case.name,packet_time=bw,episode=ep,
                         environment_seed=seed,schedule_hash=s.schedule.digest)
                episodes.append(dict(**key,target_reservation=target,captured=bool(captured),reservations=s.reservation_count,**result))
                raw.extend(dict(**key,action='send',**row) for row in convoys)
                batched=PreTransmissionNetwork(g,case,'VALUE',seed,model,value_threshold=0.,actor=actor,receiver='ALL',batch_priority=True)
                br,brows=batched.run();assert batched.schedule.digest==s.schedule.digest
                batch_episodes.append(dict(**key,**br));raw.extend(dict(**key,action='batched_priority',**row) for row in brows)
                for action,(r,rows) in pair.items():
                    if action=='send':continue
                    c=captured[0];p=c['packet']
                    labels.append(dict(**key,action=action,t=c['t'],packet=p['id'],offer_number=p['number'],sender=p['sender'],edge=p['edge'],features=json.dumps(c['features']),
                        factual_on_time=result['on_time'],alternative_on_time=r['on_time'],gain=r['on_time']-result['on_time'],
                        factual_transmitted=result['transmitted'],alternative_transmitted=r['transmitted'],
                        factual_airtime=result['radio_airtime'],alternative_airtime=r['radio_airtime'],
                        factual_convoys=json.dumps(convoys),alternative_convoys=json.dumps(rows)))
                    raw.extend(dict(**key,action=action,**row) for row in rows)
    pd.DataFrame(episodes).to_csv(Path(output)/f'episodes_s{si}_g{gi}.csv.gz',index=False)
    pd.DataFrame(batch_episodes).to_csv(Path(output)/f'batched_s{si}_g{gi}.csv.gz',index=False)
    pd.DataFrame(labels).to_csv(Path(output)/f'labels_s{si}_g{gi}.csv.gz',index=False)
    pd.DataFrame(raw).to_csv(Path(output)/f'convoys_s{si}_g{gi}.csv.gz',index=False)
    print(f'COMPLETE actor={si} graph={gi} episodes={len(episodes)} interventions={len(labels)}',flush=True)
    return len(episodes),len(labels)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',default='simulator/out/delivery-learning-v3');ap.add_argument('--output',default='simulator/out/pretransmission-opportunity');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    parent=Path(args.parent).resolve();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    lock=json.loads((parent/'locked_settings.json').read_text());assert lock['source_hash']==parent_fingerprint()
    for name,h in lock['actors'].items():assert hashlib.sha256((parent/'actors'/name).read_bytes()).hexdigest()==h
    source=fingerprint();start=time.perf_counter()
    design=dict(scope='Prospectively specified development mechanism study; hindsight interventions, no deployed gate, no new superiority test.',
        source_hash=source,parent_source_hash=parent_fingerprint(),actor_hashes=lock['actors'],
        graph_seeds=[860010,860011,860012],sizes=[19,51,131],actors=SEEDS,episodes_per_cell=2,
        cases=[asdict(c) for c in TEST],packet_times='0 for unlimited; .25 and1 for every other case',
        namespace='860000000+graph*100000+case*1000+bandwidth_index*100+episode',
        intervention='One reservation per episode at predetermined index1/3/8/16, rotated by actor/graph/case/capacity/episode; never chosen by future effect.',
        actions='send reference; drop one unsent offer; defer selected packet by one service time allowing other packets immediately; swap with next reference-priority ready packet when available.',
        features=RADIO_FEATURES,continuation='VALUE priority, zero sender threshold, ALL receiver and original frozen actor after a single action.',
        constraints='Shared-MAC queue metadata only; no remote live positions/flow, hidden closure truth or future events in decision features. No new telemetry.',
        accounting='Atomic zero-airtime reservation after enclosing routing event; send preserves exact original ordering; rolled-back reservation never charged as real transmission.',
        expected_baseline_episodes=1104,negative_controls='All12 conditions retained; unlimited may still show information-removal effects, so not assumed an all-zero action control.',
        analysis='All action gains and harms; sampled hindsight best action only labeled a diagnostic, not deployable performance or a bound over unsampled actions.',
        stronger_reference='An additional full-episode arm reselects the highest VALUE-priority ready packet after each atomic event; isolates benefits from simple batching before any learned-controller claim.',
        limits=['One weighted instance per size, fixed adjacency families; no topology-generalization inference','Frozen routing actors, one selected initial policy; no new routing training','No controller is fitted in this stage','Reservation alternatives may change subsequent endogenous traffic; that is part of their fleet effect'])
    (out/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    (out/'pipeline.json').write_text(json.dumps(dict(status='running_development',source_hash=source),indent=2)+'\n')
    with ProcessPoolExecutor(max_workers=args.workers) as pool:counts=list(pool.map(job,[(s,g,str(parent),str(out)) for s in SEEDS for g in range(3)]))
    assert fingerprint()==source and sum(a for a,b in counts)==1104
    meta=dict(status='completed',source_hash=source,parent_source_hash=parent_fingerprint(),baseline_episodes=sum(a for a,b in counts),batched_reference_episodes=sum(a for a,b in counts),isolated_interventions=sum(b for a,b in counts),seconds=time.perf_counter()-start)
    (out/'pipeline.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta),flush=True)


if __name__=='__main__':main()
