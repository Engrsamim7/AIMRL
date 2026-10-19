import copy
import numpy as np
import torch
from dataclasses import replace
from recovery_gate import FEATURES, TRAIN, graph, simulation, policy, HurdleEnsemble
from run_recovery_gate_study import causal_examples, select_settings

class Constant:
 def __init__(self,mu,risk=0.):self.mu=mu;self.risk=risk
 def predict(self,x):return self.mu,0.,self.risk,self.risk

def fixture(method='LEARN',mu=20.,risk=0.):
 g,h=graph(80000,2);p=policy(method,model=Constant(mu,risk),collect=True)
 s=simulation(g,h,TRAIN[0],p,70000000);cv=s.cv[2];cv.node=int(g.src[h[0]])
 cv.peer[h[0]]=(True,1.,.9);cv.inbox=[dict(id='a',sender=0,e=h[0],blocked=False,t_obs=2.,conf=.9,genuine=True)]
 return s,cv,h[0]

def test_natural_sensor_clearances_reach_followers():
 g,h=graph(80000,2);p=policy('SAFE',collect=True)
 s=simulation(g,h,replace(TRAIN[3],spoof=0.,loss=0.,recovery_window=(1.5,1.5)),p,70000000);s.run()
 clears=[r for r in p.candidates if r['genuine'] and not r['blocked_report'] and r['convoy']>=2]
 assert len(clears)>0 and any(r['clear_against_warning'] for r in clears)
 assert any(not r['accepted'] for r in clears)

def test_two_sided_authority_and_risk_fallback():
 s,cv,e=fixture();s.policy.decide(s,cv,3.);assert not cv.peer[e][0] and s.policy.candidates[0]['rule']=='learned_override'
 for risk,mu in [(1.,20.),(0.,-20.)]:
  s,cv,e=fixture(risk=risk,mu=mu);s.policy.decide(s,cv,3.);assert cv.peer[e][0]
 s,cv,e=fixture(mu=-20.);cv.peer.clear();cv.inbox[0]['blocked']=True
 s.policy.decide(s,cv,3.);assert e not in cv.peer and s.policy.candidates[0]['rule']=='learned_override'

def test_authority_budget_and_reject_only_ablation():
 s,cv,e=fixture();s.policy.state(cv)['recovery_overrides']=2;s.policy.decide(s,cv,3.);assert cv.peer[e][0]
 s,cv,e=fixture();s.policy.reject_only=True;s.policy.decide(s,cv,3.);assert cv.peer[e][0]

def test_private_annotations_do_not_change_admission_or_features():
 s,cv,e=fixture();b=copy.deepcopy(s);b.active.clear();b.cv[2].inbox[0]['genuine']=False
 assert s.policy.decide(s,cv,3.)==b.policy.decide(b,b.cv[2],3.)
 assert cv.peer==b.cv[2].peer
 assert [s.policy.candidates[0][k] for k in FEATURES]==[b.policy.candidates[0][k] for k in FEATURES]

def test_outer_ttl_and_own_observation_precedence_survive_forcing():
 s,cv,e=fixture();s.policy.force={(2,30.,'a'):True};s.policy.decide(s,cv,30.);assert s.policy.force_hits==0
 s,cv,e=fixture();cv.own[e]=(True,2.5,1.);s.policy.force={(2,3.,'a'):True};s.policy.decide(s,cv,3.);assert s.policy.force_hits==0 and cv.peer[e][0]

def test_full_inbox_causal_replay_and_strata_caps():
 g,h=graph(81000,2);p=policy('SAFE');rows=causal_examples(g,h,TRAIN[2],p,72000000)
 assert rows and len(rows)<=8
 for r in rows:
  assert np.isfinite(r['utility_gain']) and r['delivery_gain'] in [-1,0,1]
  assert r['accept_rows'] and r['reject_rows']
 assert sum(r['clear_against_warning']>.5 for r in rows)<=4

def test_hurdle_roundtrip_finite_and_delivery_probabilities():
 torch.set_num_threads(1);rng=np.random.default_rng(3);x=rng.normal(size=(80,len(FEATURES)));y=np.where(x[:,0]>0,5.,0.);d=np.where(x[:,1]>1,1,0)
 m=HurdleEnsemble().fit(x,y,d,4);b=HurdleEnsemble.load(m.state())
 assert np.allclose(m.predict(x[0]),b.predict(x[0]))
 assert np.isfinite(m.predict(x[0])).all() and all(0<=v<=1 for v in m.predict(x[0])[2:])
