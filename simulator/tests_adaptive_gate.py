import copy
import numpy as np
from adaptive_gate import AdaptiveGate
from ammarl2.reviewer import cc2_graph,cc2_factory
from ammarl2.sim import Cfg
from run_gate_fixtures import fixture_factory
from functools import partial
from ammarl2.counterfactual import single_message_effects


def cfg():return Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=1,tau_reveal=0,p_kill=1)
def policy(**kwargs):return AdaptiveGate('value',weights='threat',use_obs=True,relevance_scope='reachable',forced_scout_routes=True,**kwargs)

def test_ground_truth_label_does_not_affect_actions_or_evidence():
    g,_,e=cc2_graph();p=policy();s=cc2_factory(g,cfg(),p,1);cv=s.cv[1];cv.node=2
    cv.inbox=[dict(id='x',sender=0,e=e,t_obs=1.,blocked=True,conf=1.,genuine=True)]
    other=copy.deepcopy(s);other.cv[1].inbox[0]['genuine']=False
    assert p.decide(s,cv,2.)==other.policy.decide(other,other.cv[1],2.)
    assert p.state(cv)['reports']==other.policy.state(other.cv[1])['reports']

def test_value_warning_avoids_actual_loss_and_replay_attributes_it():
    g,_,_=cc2_graph();p=policy()
    frame,meta,result=single_message_effects(g,cfg(),p,1,simulator_factory=partial(cc2_factory,hot=4))
    assert sum(r['delivered'] for r in result['rows'])==3
    assert frame.delta_delivery.eq(1).all()

def test_conflicting_sources_do_not_silently_overwrite_each_other():
    g,_,e=cc2_graph();p=policy(mode='all');s=fixture_factory(g,cfg(),p,3,hot=4,false_confidence=.9);r=s.run()
    assert sum(x['delivered'] for x in r['rows'])==3
    assert len([m for m in p.state(s.cv[1])['reports'].values() if m['e']==e])==2

def test_repeated_sender_is_not_counted_as_independent_evidence():
    g,_,e=cc2_graph();p=policy(mode='all');s=cc2_factory(g,cfg(),p,1);cv=s.cv[1];cv.node=2
    cv.inbox=[dict(id=str(i),sender=9,e=e,t_obs=1.+i*.01,blocked=True,conf=1.,genuine=True) for i in range(10)]
    p.decide(s,cv,2.)
    assert len(p.state(cv)['reports'])==1

def test_episode_state_is_fresh_and_negative_age_rejected():
    g,_,e=cc2_graph();p=policy();s=cc2_factory(g,cfg(),p,1);s.run();fresh=cc2_factory(g,cfg(),p,2)
    assert p.state(fresh.cv[1])['reports']=={}
    cv=fresh.cv[1];cv.node=2;cv.inbox=[dict(id='future',sender=0,e=e,t_obs=100.,blocked=True,conf=1.,genuine=True)]
    p.decide(fresh,cv,3.);assert fresh.message_audit[-1]['reason']=='stale'

def test_local_feedback_updates_agreement_without_label():
    g,_,e=cc2_graph();p=policy();s=cc2_factory(g,cfg(),p,1);cv=s.cv[0]
    st=p.state(cv);st['feedback']['m']=dict(id='m',sender=7,e=e,t_obs=1.,blocked=True,conf=.9);cv.own[e]=(True,2.,1.)
    before=p.trust(st,7);p.confirm(cv,2.)
    assert p.trust(st,7)>before
    first=st['reputation'][7];p.confirm(cv,2.);assert st['reputation'][7]==first

def test_hidden_remote_state_cannot_change_gate_estimates():
    g,_,e=cc2_graph();p=policy();s=cc2_factory(g,cfg(),p,1);cv=s.cv[1];cv.node=2
    before=p.distribution(s,cv,2.)
    s.active.clear();s.flow[e]=100
    after=p.distribution(s,cv,2.)
    assert all(np.array_equal(a,b) for a,b in zip(before,after))


def test_single_impersonated_clear_cannot_erase_warning():
    from ammarl2.sim import MSG
    g,_,e=cc2_graph();p=policy();s=cc2_factory(g,cfg(),p,3)
    for receiver in [1,2]:
        s.push(3.,MSG,(receiver,dict(id=f'impersonation:{receiver}',sender=0,e=e,t_obs=2.,blocked=False,conf=.9,genuine=False)))
    result=s.run()
    assert sum(r['delivered'] for r in result['rows'])==3


def test_two_forged_identities_expose_clearance_quorum_limit():
    from ammarl2.sim import MSG
    g,_,e=cc2_graph();p=policy();s=cc2_factory(g,cfg(),p,3)
    for receiver in [1,2]:
        for sender in [-1,-2]:
            s.push(3.,MSG,(receiver,dict(id=f'collusion:{receiver}:{sender}',sender=sender,e=e,t_obs=2.,blocked=False,conf=.99,genuine=False)))
    result=s.run()
    assert sum(r['delivered'] for r in result['rows'])==1

def test_direct_local_clear_overrides_remote_warning():
    g,_,e=cc2_graph();p=policy();s=cc2_factory(g,cfg(),p,3);cv=s.cv[1];cv.node=2
    state=p.state(cv);m=dict(id='warning',sender=0,e=e,t_obs=1.,blocked=True,conf=1.)
    state['anchors'][(e,0)]=m;state['reports'][(e,0)]=m
    cv.own[e]=(False,3.,1.)
    probability,uncertainty,weights=p.distribution(s,cv,3.)
    assert probability[e]==0. and uncertainty[e]==0.


def test_exogenous_mixed_spoof_stream_is_independent_of_routing_policy():
    from run_adaptive_experiments import MixedSpoofSim,config
    from ammarl2.reviewer import original_graph,m4_sensing
    from ammarl2.policies import Policy
    from ammarl2.sim import MSG
    g=original_graph();c=config('delayed-spoof')
    a=MixedSpoofSim(g,c,Policy('NC'),19,m4_sensing(g,True))
    b=MixedSpoofSim(g,c,policy(),19,m4_sensing(g,True))
    a.active[0]=(0.,50.);b.active[0]=(0.,50.)
    for t in [1.,2.,3.]:a.do_spoof(t);b.do_spoof(t)
    # Filter before unpacking: SPOOF scheduler events have an empty payload.
    packets=lambda s:[(t,payload[0],payload[1]) for t,k,typ,payload in s.ev if typ==MSG]
    assert packets(a)==packets(b)


def test_adaptive_actor_preserves_weights_and_local_feature_contract():
    import torch
    from ammarl2.learn import LearnedPolicy
    from adaptive_actor import AdaptiveActor
    g,_,e=cc2_graph();fitted=LearnedPolicy('dqn',algo='dqn',comm='all',train=False,seed=1)
    p=AdaptiveActor.from_fitted(fitted,{'min_value':.02,'risk_aversion':0.,'age_scale':2.})
    s=cc2_factory(g,cfg(),p,3);cv=s.cv[1];cv.node=2
    cv.inbox=[dict(id='true-warning',sender=0,e=e,t_obs=1.,blocked=True,conf=1.,genuine=True)]
    weights={k:v.clone() for k,v in p.net.state_dict().items()};p.decide(s,cv,2.)
    assert e in cv.peer and cv.peer[e][0] is True
    assert all(torch.equal(v,weights[k]) for k,v in p.net.state_dict().items())
    assert len(s.trace)==1 and s.decisions[-1]['selector'].startswith('frozen dqn')
