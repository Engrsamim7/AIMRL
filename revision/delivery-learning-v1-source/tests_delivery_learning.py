import copy
from dataclasses import replace
import hashlib
import json
import numpy as np
import torch
from timed_network import TimedNetwork
from tests_timed_network import diamond,calibration
from timed_network import Scenario
from delivery_learning import Actor,DeliveryNetwork,FEATURES,ReturnGate,paired_packet

def fixture(actor=None,receiver='ALL'):
    case=Scenario(n_convoys=2,coverage=0.,scout_lead=1.,hub_service=0.,closure_fraction=0.,delay=0.,packet_time=0.,inspection=4.,perfect_sensors=True)
    s=DeliveryNetwork(diamond(),case,'VALUE',31,calibration(),value_threshold=0.,actor=actor,receiver=receiver,record=True)
    s.schedule.intervals={1:(0.,5.)};return s


def test_new_event_loop_preserves_base_physics_without_loss_or_learning():
    s=fixture();base=TimedNetwork(s.g,s.case,'VALUE',31,calibration(),value_threshold=0.,record=True);base.schedule.intervals=copy.deepcopy(s.schedule.intervals)
    expected,erows=base.run();actual,arows=s.run()
    for key in ['on_time','delivery','elapsed','routing_calls','blocked_attempts','transmitted','tx_started']:assert np.isclose(actual[key],expected[key]),key
    for a,b in zip(arows,erows):
        for key in ['on_time','delivered','elapsed','nominal','inspection','wait','travel','path']:assert a[key]==b[key],key


def test_semantic_packet_loss_identity_ignores_unrelated_offer_counter():
    a=fixture();b=fixture();a.radio_busy=b.radio_busy=True
    b.offer(b.units[0],3,False,0.,1.)
    a.offer(a.units[0],1,True,0.,1.);b.offer(b.units[0],1,True,0.,1.)
    pa=next(p for p in a.radio if p['edge']==1);pb=next(p for p in b.radio if p['edge']==1)
    assert pa['id']==pb['id'] and pa['number']!=pb['number']


def test_single_packet_factual_branch_reproduces_unintervened_complete_run():
    baseline=fixture();expected,rows=baseline.run();s=fixture();captured=[]
    def capture(env,cid,p,x):captured.append((cid,copy.deepcopy(p)));return True
    s.capture=capture;assert s.run() is None
    pair=paired_packet(s,*captured[0]);assert pair[0][1]==rows
    for key in ['on_time','delivery','elapsed','transmitted','blocked_attempts']:assert pair[0][0][key]==expected[key]
    assert pair[0][0]['on_time']>=pair[1][0]['on_time']


def test_actor_and_gate_features_do_not_read_remote_truth_or_future_flow():
    torch.set_num_threads(1);actor=Actor(91);s=fixture(actor);u=s.units[1];u.status='travel';u.current_edge=0;u.node=0
    p=dict(edge=1,blocked=True,t_obs=0.,confidence=1.,id='opaque')
    before=s.packet_features(1,p);s.schedule.intervals={0:(0.,50.),3:(0.,50.)};s.flow[1]=100
    assert np.array_equal(before,s.packet_features(1,p))
    assert not u.peer and not s.history[1]


def test_team_potential_shaping_preserves_delivery_objective():
    s=fixture();x=np.zeros((2,len(FEATURES)),np.float32)
    s.history[0]=[dict(x=x,chosen=0,phi=-1.,t=0.),dict(x=x,chosen=1,phi=-.4,t=1.)]
    samples=s.transitions(.625);assert np.isclose(sum(r for _,r,_ in samples),.625+1.)
    assert len(samples[-1][2])==0


def test_real_double_dqn_optimizer_and_inference_checkpoint_roundtrip():
    torch.set_num_threads(1);a=Actor(17,training=True);rng=np.random.default_rng(18)
    samples=[(rng.normal(size=len(FEATURES)).astype(np.float32),.5,np.empty((0,len(FEATURES)),np.float32)) for _ in range(160)]
    before={k:v.clone() for k,v in a.net.state_dict().items()};loss=a.learn(samples,steps=3)
    assert len(loss)==3 and all(np.isfinite(loss)) and any(not torch.equal(before[k],v) for k,v in a.net.state_dict().items())
    restored=Actor.load(a.state());x=rng.normal(size=(4,len(FEATURES))).astype(np.float32);assert np.array_equal(a.values(x),restored.values(x))


def test_return_gate_portable_predictions_and_all_fallback(tmp_path):
    rng=np.random.default_rng(12);x=rng.normal(size=(120,24));y=np.where(x[:,0]>0,-.125,.125)
    g=ReturnGate(beta=0.).fit(x,y,13);p=tmp_path/'gate.npz';g.save(p);loaded=ReturnGate.load(p,beta=0.)
    for row in x[:5]:assert np.array_equal(g.predict(row),loaded.predict(row))
    loaded.disabled=True;assert all(loaded.admit(row) for row in x)


def test_fixed_receiver_rechecks_expiry_at_decision_without_feature_leak():
    a=Actor(92);s=fixture(a,receiver='FIXED');u=s.units[1];u.node=1;u.peer[1]=(True,0.,1.)
    s.t=2.;assert 1 in s.beliefs(u)
    s.t=4.;assert 1 not in s.beliefs(u)
    actions,x,_=s.candidate_features(u);assert x[actions.index(1),9]==0


def test_one_fleet_rejection_authority_is_enforced():
    s=fixture(receiver='LEARN')
    class Reject:
        def admit(self,x):return False
    s.gate=Reject();s.packet_features=lambda cid,p:np.ones(24,np.float32)
    s.receive(1,dict(id='a',edge=1,blocked=True,t_obs=0.,confidence=1.))
    s.receive(1,dict(id='b',edge=3,blocked=True,t_obs=0.,confidence=1.))
    assert s.rejections==1 and 1 not in s.units[1].peer and 3 in s.units[1].peer
