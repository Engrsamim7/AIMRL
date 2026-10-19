import copy
import heapq
import numpy as np
from ammarl2.sim import DEPART
from research_cases import CASES,fork_graph
from run_cover_traffic_stress import simulation
from run_matched_gate_study import policy
from diagnose_gate_decisions import audited,effects,intervention

class Constant:
    def __init__(self,v):self.v=v
    def predict(self,x):return self.v,0.


def test_diagnostic_policy_matches_original_actions_and_outcomes():
    g,h=fork_graph(59000,3)
    for method in ['SAFE','COMBINED']:
        model=Constant(-2.)
        a=simulation(g,h,CASES[1],policy(method,None,model),65000001)
        b=simulation(g,h,CASES[1],audited(method,None,model,collect=True),65000001)
        x,y=a.run(),b.run()
        assert x['rows']==y['rows'] and x['decisions']==y['decisions'] and x['stats']==y['stats']
        assert x['message_audit']==y['message_audit']


def fixture():
    g,h=fork_graph(59000,3);p=audited('COMBINED',None,Constant(80.),collect=True)
    s=simulation(g,h,CASES[0],p,65000001);cv=s.cv[2];cv.node=int(g.src[h[0]])
    cv.peer[h[0]]=(True,1.,.9)
    cv.inbox=[dict(id='a',sender=0,e=h[0],blocked=False,t_obs=2.,conf=.9,genuine=False)]
    return s,cv,h[0]


def test_final_admission_intervention_can_override_a_guard_without_faking_prediction():
    s,cv,e=fixture();s.policy.force={(cv.id,3.,'a'):True}
    s.policy.decide(s,cv,3.)
    assert s.policy.force_hits==1 and not cv.peer[e][0]
    assert s.message_audit[-1]['predicted_value']==80.
    assert s.message_audit[-1]['admission_rule']=='require_clearance_corroboration'


def test_keep_warning_blocks_even_corroborated_peer_clearance():
    s,cv,e=fixture();s.policy=audited('SAFE',None,keep_warning=True)
    cv.inbox.append(dict(id='b',sender=1,e=e,blocked=False,t_obs=2.,conf=.9,genuine=True))
    s.policy.decide(s,cv,3.)
    assert cv.peer[e][0] and all(r['reason']=='predicted_low_value' for r in s.message_audit)


def test_truth_annotations_do_not_change_policy_or_public_features():
    s,cv,e=fixture();b=copy.deepcopy(s);b.active.clear();b.cv[2].inbox[0]['genuine']=True
    assert s.policy.decide(s,cv,3.)==b.policy.decide(b,b.cv[2],3.)
    assert cv.peer==b.cv[2].peer
    x=s.policy.audit_records[0];y=b.policy.audit_records[0]
    for name in ['genuine','truth_at_decision']:x.pop(name);y.pop(name)
    assert x==y


def test_replays_restore_target_decision_without_changing_factual_trajectory():
    g,h=fork_graph(59000,3);p=audited('COMBINED',None,Constant(0.));snaps=[]
    def capture(s,cv,t):
        if not cv.inbox or snaps:return
        hook=s.before_decision;s.before_decision=None
        try:b=copy.deepcopy(s)
        finally:s.before_decision=hook
        trial=copy.deepcopy(b);first=len(trial.message_audit);trial.policy.decide(trial,trial.cv[cv.id],t)
        if not any(r['reason'] in ['accepted','predicted_low_value'] for r in trial.message_audit[first:]):return
        heapq.heappush(b.ev,(t,-1,DEPART,cv.id));snaps.append((b,cv.id,t))
    s=simulation(g,h,CASES[0],p,65000001);s.before_decision=capture
    factual=s.run();plain=simulation(g,h,CASES[0],audited('COMBINED',None,Constant(0.)),65000001).run()
    assert factual['rows']==plain['rows'] and snaps
    b,cid,t=snaps[0]
    trial=copy.deepcopy(b);n=len(trial.message_audit);trial.run()
    valid=[r for r in trial.message_audit[n:] if r['convoy']==cid and r['decision_t']==t and r['reason'] in ['accepted','predicted_low_value']]
    assert valid
    effect=effects(b,cid,t,valid[0]['id'])
    assert effect['delta_delivery'] in [-1,0,1] and np.isfinite(effect['delta_utility'])
    assert not b.policy.force and b.policy.force_hits==0
