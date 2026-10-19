import copy
import json
from pathlib import Path
import numpy as np
import torch
from ammarl2.learn import LearnedPolicy
from actor_aware_gate import FEATURES,BASE_FEATURES,policy,LeafForest,SingleAdmission
from recovery_gate import TRAIN,graph,simulation,policy as old_policy
from run_actor_aware_development import one_episode, encoded_rows

def actor():return LearnedPolicy('test',algo='dqn',train=False,seed=3)

def fixture():
 a=actor();g,h=graph(91000,2);s=simulation(g,h,TRAIN[0],policy('SAFE',a,collect=True),800000000);cv=s.cv[2];cv.node=int(g.src[h[0]]);cv.peer[h[0]]=(True,1.,.9)
 cv.inbox=[dict(id='a',sender=0,e=h[0],blocked=False,t_obs=2.,conf=.9,genuine=True)];return s,cv,h[0]

def test_full_inbox_probing_preserves_safe_behavior():
 torch.set_num_threads(1);a=actor();g,h=graph(91000,2)
 x=simulation(g,h,TRAIN[0],old_policy('SAFE',a),800000000).run()
 y=simulation(g,h,TRAIN[0],policy('SAFE',a),800000000).run()
 assert encoded_rows(x['rows'])==encoded_rows(y['rows']) and x['decisions']==y['decisions'] and x['stats']==y['stats']

def test_probe_features_exclude_origin_hidden_truth_and_privileged_critic():
 s,cv,e=fixture();b=copy.deepcopy(s);b.active.clear();b.cv[2].inbox[0]['genuine']=False
 s.policy.decide(s,cv,3.);b.policy.decide(b,b.cv[2],3.)
 x=s.policy.candidates[0];y=b.policy.candidates[0]
 assert [x[k] for k in FEATURES]==[y[k] for k in FEATURES] and cv.peer==b.cv[2].peer

def test_later_packet_can_mask_current_packet_before_actual_actor_action():
 s,cv,e=fixture();cv.inbox.append(dict(id='b',sender=1,e=e,blocked=True,t_obs=2.5,conf=.9,genuine=False));s.policy.decide(s,cv,3.)
 r=s.policy.candidates[0]
 assert r['probe_action_change']==0 and r['actor_node_input_difference']==0 and r['actor_edge_input_difference']==0
 assert r['probe_accept_edge']==r['probe_reject_edge']

def test_single_global_override_budget_and_abstention():
 class Constant:
  def predict(self,x):return [10.,0.,0.,0.]
 p=policy('LEARN',actor(),Constant(),margin=0.);p._cv=type('CV',(),{'id':2})();p._t=3.;p._packet_id='x'
 x=np.zeros(len(FEATURES));x[13]=1.;x[len(BASE_FEATURES)]=1.;x[len(BASE_FEATURES)+1]=0.
 a=SingleAdmission(p);assert a.predict(x)[0]>0 and p.override_used
 p._cv.id=3;p._packet_id='y';assert a.predict(x)[0]<0
 assert sum(r['rule']=='actor_value_override' for r in a.records)==1

def test_outer_ttl_and_own_timestamp_checks_still_precede_gate():
 s,cv,e=fixture();s.policy.force={(2,30.,'a'):True};s.policy.decide(s,cv,30.);assert s.policy.force_hits==0
 s,cv,e=fixture();cv.own[e]=(True,2.5,1.);s.policy.force={(2,3.,'a'):True};s.policy.decide(s,cv,3.);assert s.policy.force_hits==0

def test_forest_vectorized_inference_and_safe_npz_roundtrip(tmp_path):
 rng=np.random.default_rng(2);x=rng.normal(size=(100,len(FEATURES)));y=np.column_stack([x[:,0]*2,x[:,1]/5])
 m=LeafForest().fit(x,y,4,n_estimators=12);path=tmp_path/'forest.npz';m.save(path);b=LeafForest.load(path)
 for row in x[:5]:assert np.array_equal(m.predict(row),b.predict(row))

def test_replays_match_factual_branch_and_probed_next_actions():
 g,h=graph(91000,2);rows,s,raw=one_episode(g,h,TRAIN[0],actor(),800000000)
 assert rows and len(rows)<=8 and s['oracle_sampled_gain']>=0
 assert all(np.isfinite(r['flip_utility']) and -.999<=r['flip_delivery']<=.999 for r in rows)
 assert len(raw)==5
 for row in rows:
  flip=json.loads(row['reject_rows'] if row['accepted'] else row['accept_rows'])
  value=lambda r:40*r['delivered']-40*r['destroyed']-40*r['censored']-r['elapsed']
  assert np.isclose(row['flip_utility'],np.mean([value(r) for r in flip])-np.mean([value(r) for r in raw]))
  assert np.isclose(row['flip_delivery'],np.mean([r['delivered'] for r in flip])-np.mean([r['delivered'] for r in raw]))

def test_calibration_excludes_high_utility_setting_with_delivery_loss():
 import pandas as pd
 from run_actor_aware_development import select_settings,GRID,MODELS
 rows=[]
 for algo in ['dqn','mappo']:
  rows.append(dict(algo=algo,method='SAFE',config=0,delivery_rate=.8,utility_mean=0.))
  for method in MODELS:
   for config,d,u in [(0,.8,0.),(1,.7,10.),(2,.8,1.)]:rows.append(dict(algo=algo,method=method,config=config,delivery_rate=d,utility_mean=u))
 settings,_=select_settings(pd.DataFrame(rows))
 assert all(settings[a][m]==GRID[1] for a in settings for m in MODELS)

def test_calibration_prefers_safe_abstention_on_exact_utility_tie():
 import pandas as pd
 from run_actor_aware_development import select_settings,MODELS
 rows=[]
 for algo in ['dqn','mappo']:
  rows.append(dict(algo=algo,method='SAFE',config=0,delivery_rate=.8,utility_mean=0.))
  for method in MODELS:
   for config in [0,1]:rows.append(dict(algo=algo,method=method,config=config,delivery_rate=.8,utility_mean=0.))
 settings,_=select_settings(pd.DataFrame(rows));assert all(settings[a][m]==dict(abstain=True) for a in settings for m in MODELS)
