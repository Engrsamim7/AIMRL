"""Exploratory, exact decision replay; never refits or changes deployed weights."""
import argparse
import copy
import hashlib
import heapq
import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, fields
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from ammarl2.learn import LearnedPolicy
from ammarl2.sim import DEPART
from guarded_research_gate import GuardedResearchPolicy, ConstrainedModel
from research_gate import ResearchPolicy, ValueEnsemble, FEATURES
from research_cases import fork_graph
from run_cover_traffic_stress import simulation
from run_matched_gate_study import (policy, load_actor, weight_hash, frozen, examples,
                                   TRAIN_CASES, TEST_CASES, fingerprint as parent_hash)
from run_research_study import utility
from run_reviewer_revision import write_json

ROOT=Path(__file__).resolve().parent
CAPS={'disagreement':2,'warning_override':1,'clearance_override':1,'agreement':1}
DESIGN=dict(purpose='diagnosis after null matched-study primary result; exploratory, no superiority tests or tuning',
    original_source_hash=parent_hash(), actors='COMBINED actors, both algorithms, all eight paired seeds',
    replay_subset='mechanism graphs 59000/59001 (3/4 forks), all 8 cases, episodes 0/1; 512 original COMBINED trajectories',
    reference='exact original episode/convoy outcomes must reproduce before any interpretation',
    selection=dict(caps_per_episode=CAPS,order='first eligible packets chronologically in each public decision category; no selection using origin, truth or outcome'),
    causal='force one otherwise eligible packet accepted versus rejected after guard/value logic, same complete state and RNG; retain remaining current inbox and all future events',
    prefix_check='first selected disagreement and warning override per episode additionally remove later current-inbox packets in both branches, matching the training credit convention',
    static='keep fresh peer warning against every peer clearance, even corroborated; own observations and common TTL unchanged; same COMBINED-trained actor; diagnostic only, not retrained',
    warmup='reconstruct exact 300-episode warmup for 16 actor/seed pairs; verify recorded warmup network hash; freeze; no parameter changes to original final models',
    drift='16 new ALL episodes per warmup/final actor on layouts 61000..61015, balanced 2/3 forks; same cases/tapes across actors; fit old value model to neither dataset',
    drift_tapes='66000000 + seed*10000 + episode',
    drift_limits='warmup and final actors can encounter different packets/states; error differences diagnose transport, not proof that staleness caused the primary null',
    limits=['subset replay, not population effect estimate','conditional marginal packet effects need not add up','prefix removal changes credit context','fixed actor comparisons do not compare separately retrained systems','all original results preserved; any updated gate needs fresh confirmation'])


def fingerprint():
    h=hashlib.sha256(parent_hash().encode());h.update(Path(__file__).read_bytes());return h.hexdigest()


class DiagnosticAdapter(ConstrainedModel):
    def __init__(self, p, sim, cv, t):
        super().__init__(p.value_model,p.value_threshold,p.uncertainty_weight,p.warning_confidence,
                         p.warning_guard,p.clearance_guard,lambda:p._candidate_reachable)
        self.p,self.cv,self.t=p,cv,t
        self.details=[]

    def predict(self,x):
        score,std=super().predict(x)
        mean,_,rule=self.calls[-1]
        forced=self.p.force.get((self.cv.id,float(self.t),self.p._packet_id))
        if self.p.keep_warning and x[0]<.5 and x[6]>.5:
            score=self.threshold+self.beta*std-1.
        if forced is not None:
            score=self.threshold+self.beta*std+(1. if forced else -1.)
            self.p.force_hits+=1
        self.details.append((mean,std,rule,list(x),forced))
        return score,std


@dataclass
class AuditPolicy(GuardedResearchPolicy):
    collect:bool=False
    keep_warning:bool=False
    force:object=None

    def __post_init__(self):
        super().__post_init__();self.force=dict(self.force or {});self.force_hits=0;self.audit_records=[]

    def features(self,sim,cv,m,t):
        x=super().features(sim,cv,m,t);self._packet_id=m['id'];return x

    def decide(self,sim,cv,t):
        base=self.value_model; adapter=DiagnosticAdapter(self,sim,cv,t)
        start=len(sim.message_audit)
        packets={m['id']:m for m in cv.inbox}
        self.value_model=adapter
        try:edge=ResearchPolicy.decide(self,sim,cv,t)
        finally:self.value_model=base
        queries=iter(adapter.details)
        for record in sim.message_audit[start:]:
            if record['reason'] not in ['accepted','predicted_low_value']:continue
            mean,std,rule,x,forced=next(queries)
            record.update(predicted_value=mean,value_uncertainty=std,admission_rule=rule)
            if not self.collect:continue
            accepted=record['reason']=='accepted'
            safe=not(x[0]<.5 and x[6]>.5 and x[21]<.5)
            raw=mean-self.uncertainty_weight*std>self.value_threshold
            category=('disagreement' if accepted!=safe else
                      'warning_override' if rule=='preserve_credible_warning' and not raw else
                      'clearance_override' if rule=='require_clearance_corroboration' and raw else 'agreement')
            m=packets[record['id']]
            self.audit_records.append(dict(id=record['id'],convoy=cv.id,t=float(t),edge=m['e'],
                genuine=bool(m['genuine']),blocked_report=bool(m['blocked']),truth_at_decision=bool(m['e'] in sim.active),
                accepted=accepted,same_prefix_safe_accept=safe,raw_accept=raw,rule=rule,category=category,
                predicted_value=mean,value_uncertainty=std,**dict(zip(FEATURES,x))))
        assert next(queries,None) is None
        return edge


def audited(method,actor,model=None,collect=False,keep_warning=False):
    p=policy(method,actor,model)
    return AuditPolicy(**{f.name:getattr(p,f.name) for f in fields(GuardedResearchPolicy)},collect=collect,keep_warning=keep_warning)


def intervention(snapshot,cid,t,pid,accept,prefix=False):
    s=copy.deepcopy(snapshot);s.before_decision=None;s.policy.collect=False;s.policy.audit_records=[]
    s.policy.force={(cid,float(t),pid):bool(accept)};s.policy.force_hits=0
    if prefix:
        ordered=sorted(s.cv[cid].inbox,key=lambda m:(m['t_obs'],m['id']))
        target=next(i for i,m in enumerate(ordered) if m['id']==pid)
        s.cv[cid].inbox=ordered[:target+1]
    first=len(s.decisions); result=s.run()
    assert s.policy.force_hits==1
    return s,result,first


def encoded_rows(rows):
    return json.dumps([{k:(None if isinstance(v,(float,np.floating)) and not np.isfinite(v) else v) for k,v in r.items()} for r in rows],default=lambda x:x.item(),allow_nan=False)


def effects(snapshot,cid,t,pid,prefix=False):
    a,ra,first=intervention(snapshot,cid,t,pid,True,prefix)
    b,rb,_=intervention(snapshot,cid,t,pid,False,prefix)
    common=min(a.t,b.t)
    assert [v for v in a.attack_log if v[0]<=common]==[v for v in b.attack_log if v[0]<=common]
    assert [(c.id,c.target,c.depart_t) for c in a.cv]==[(c.id,c.target,c.depart_t) for c in b.cv]
    x,y=ra['rows'][cid],rb['rows'][cid]
    return dict(accept_rows=encoded_rows(ra['rows']),reject_rows=encoded_rows(rb['rows']),context='prefix' if prefix else 'full',delta_delivery=x['delivered']-y['delivered'],
        delta_elapsed=x['elapsed']-y['elapsed'],delta_utility=utility(x)-utility(y),
        delta_team_deliveries=sum(r['delivered'] for r in ra['rows'])-sum(r['delivered'] for r in rb['rows']),
        delta_team_utility=sum(utility(r) for r in ra['rows'])-sum(utility(r) for r in rb['rows']),
        changed_next_edge=a.decisions[first]['edge']!=b.decisions[first]['edge'],
        changed_receiver_path=a.cv[cid].path!=b.cv[cid].path,
        delivered_accept=x['delivered'],delivered_reject=y['delivered'])


def recover_warmup(job):
    algo,seed,parent,output=job;torch.set_num_threads(1);parent=Path(parent);out=Path(output)
    actor=LearnedPolicy(algo,algo=algo,seed=seed,train=True,comm='all',use_obs=True,weights='threat',relevance_scope='reachable')
    for ep in range(300):
        g,h=fork_graph(55000+ep%60,2+(ep//8)%2);actor.eps=max(.03,.5*(1-ep/420.))
        simulation(g,h,TRAIN_CASES[ep%8],policy('ALL',actor),60000000+seed*10000+ep).run();actor.end_episode()
    meta=json.loads((parent/'value_models'/f'{algo}_s{seed}.json').read_text())
    assert weight_hash(actor)==meta['warmup_weight_hash']
    torch.save(dict(parameters={f.name:getattr(actor,f.name) for f in fields(LearnedPolicy)},state_dict=actor.net.state_dict(),weight_hash=weight_hash(actor)),out/'warmup_models'/f'{algo}_s{seed}.pt')
    print(f'WARMUP VERIFIED {algo} seed={seed}',flush=True)
    return dict(algo=algo,seed=seed,verified_hash=weight_hash(actor),episodes=300)


def load_warm(path):
    data=torch.load(path,map_location='cpu',weights_only=True);params=data['parameters'];params.update(train=False,eps=0.)
    a=LearnedPolicy(**params);a.net.load_state_dict(data['state_dict']);assert weight_hash(a)==data['weight_hash'];return a


def drift_job(job):
    algo,seed,parent,output=job;torch.set_num_threads(1);parent=Path(parent);out=Path(output)
    model=ValueEnsemble.load(json.loads((parent/'value_models'/f'{algo}_s{seed}.json').read_text())['model'])
    rows=[]
    for stage,actor in [('warmup',load_warm(out/'warmup_models'/f'{algo}_s{seed}.pt')),('adapted',load_actor(parent/'models'/f'{algo}_s{seed}_COMBINED.pt'))]:
        initial=weight_hash(actor)
        for ep in range(16):
            g,h=fork_graph(61000+ep,2+(ep//8)%2)
            for r in examples(g,h,TRAIN_CASES[ep%8],policy('ALL',actor),66000000+seed*10000+ep):
                mean,std=model.predict([r[f] for f in FEATURES])
                rows.append(dict(algo=algo,seed=seed,stage=stage,episode=ep,case=TRAIN_CASES[ep%8].name,predicted_value=mean,uncertainty=std,**r))
        assert weight_hash(actor)==initial
    print(f'DRIFT LABELS {algo} seed={seed}: {len(rows)}',flush=True)
    return rows


def audit_job(job):
    algo,seed,parent,output=job;torch.set_num_threads(1);parent=Path(parent)
    actor=load_actor(parent/'models'/f'{algo}_s{seed}_COMBINED.pt');initial=weight_hash(actor)
    model=ValueEnsemble.load(json.loads((parent/'value_models'/f'{algo}_s{seed}.json').read_text())['model'])
    packet_rows=[];effect_rows=[];episodes=[];raw=[]
    for gi in range(2):
        g,h=fork_graph(59000+gi,3+gi%2)
        for ci,case in enumerate(TEST_CASES):
            for ep in range(2):
                key=dict(algo=algo,seed=seed,graph=gi,case=case.name,episode=ep)
                p=audited('COMBINED',actor,model,collect=True);snapshots=[]
                def capture(sim,cv,t):
                    if not cv.inbox:return
                    hook=sim.before_decision;sim.before_decision=None
                    logs=sim.policy.audit_records;sim.policy.audit_records=[]
                    try:shadow=copy.deepcopy(sim)
                    finally:sim.before_decision=hook;sim.policy.audit_records=logs
                    shadow.policy.collect=False
                    heapq.heappush(shadow.ev,(t,-1,DEPART,cv.id));snapshots.append((shadow,cv.id,float(t)))
                s=simulation(g,h,case,p,65000000+gi*10000+ci*100+ep);s.before_decision=capture;result=s.run()
                packet_rows.extend(dict(**key,**r) for r in p.audit_records)
                selected={k:0 for k in CAPS};prefix_done=set()
                for snapshot,cid,t in snapshots:
                    candidates=[r for r in p.audit_records if r['convoy']==cid and r['t']==t]
                    for r in candidates:
                        cat=r['category']
                        if selected[cat]>=CAPS[cat]:continue
                        selected[cat]+=1
                        measured=effects(snapshot,cid,t,r['id'])
                        assert measured['accept_rows' if r['accepted'] else 'reject_rows']==encoded_rows(result['rows'])
                        effect_rows.append(dict(**key,**r,**measured))
                        if cat in ['disagreement','warning_override'] and cat not in prefix_done:
                            prefix_done.add(cat);effect_rows.append(dict(**key,**r,**effects(snapshot,cid,t,r['id'],prefix=True)))
                episodes.append(dict(**key,method='COMBINED',delivered=sum(r['delivered'] for r in result['rows']),utility_mean=float(np.mean([utility(r) for r in result['rows']])),processed_messages=len(result['message_audit']),eligible_candidates=len(p.audit_records),routing_decisions=len(result['decisions'])))
                raw.extend(dict(**key,method='COMBINED',**r) for r in result['rows'])
                static=simulation(g,h,case,audited('SAFE',actor,keep_warning=True),65000000+gi*10000+ci*100+ep).run()
                episodes.append(dict(**key,method='KEEP-WARNING',delivered=sum(r['delivered'] for r in static['rows']),utility_mean=float(np.mean([utility(r) for r in static['rows']]))))
                raw.extend(dict(**key,method='KEEP-WARNING',**r) for r in static['rows'])
    assert weight_hash(actor)==initial
    print(f'AUDITED {algo} seed={seed}: {len(packet_rows)} candidates, {len(effect_rows)} replay pairs',flush=True)
    return packet_rows,effect_rows,episodes,raw


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',default='out/matched-gate-study');ap.add_argument('--output',default='out/gate-decision-diagnosis');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    parent,out=Path(a.parent).resolve(),Path(a.output).resolve();meta=json.loads((parent/'pipeline.json').read_text())
    assert meta['status']=='completed' and meta['source_hash']==parent_hash()
    out.mkdir(parents=True,exist_ok=False);(out/'warmup_models').mkdir();initial=fingerprint();start=time.perf_counter()
    write_json(out/'design.json',dict(**DESIGN,source_hash=initial));write_json(out/'pipeline.json',dict(status='running',source_hash=initial))
    jobs=[(algo,seed,str(parent),str(out)) for algo in ['dqn','mappo'] for seed in range(8)]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        recovered=list(pool.map(recover_warmup,jobs));write_json(out/'warmup_verification.json',recovered)
        drift=[]
        for rows in pool.map(drift_job,jobs):drift.extend(rows)
        pd.DataFrame(drift).to_csv(out/'drift_labels.csv.gz',index=False)
        totals={k:0 for k in ['packets','effects','episodes','convoys']}
        for i,parts in enumerate(pool.map(audit_job,jobs)):
            for name,rows in zip(totals,parts):
                pd.DataFrame(rows).to_csv(out/(name+'.csv'),index=False,mode='w' if i==0 else 'a',header=i==0);totals[name]+=len(rows)
    assert fingerprint()==initial
    write_json(out/'pipeline.json',dict(status='completed',source_hash=initial,parent_source_hash=parent_hash(),seconds=time.perf_counter()-start,totals=totals,warmup_recovery_episodes=4800,drift_factual_episodes=512,drift_interventions=len(drift),drift_replay_branches=2*len(drift),decision_replay_branches=2*totals['effects']))
    print('DIAGNOSIS COMPLETE',flush=True)

if __name__=='__main__':main()
