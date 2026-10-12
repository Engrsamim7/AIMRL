"""Regression tests for original topology and explicit reviewer sensing contracts."""
import copy,json
from functools import partial
import numpy as np
import pytest
import torch
from ammarl2.reviewer import original_graph,NETWORK,ReviewerSim,Sensing,cc2_graph,cc2_factory,ScoutFixturePolicy
from ammarl2.sim import Cfg
from ammarl2.policies import Policy
from ammarl2.learn import build_ctx
from ammarl2.counterfactual import single_message_effects


def config():return Cfg(n_convoys=3,stagger=0,hub_service=.25,attack_rate=0,budget=0,tau_msg=1,tau_reveal=0,p_kill=1)

def test_original_network_attributes_are_preserved():
    g=original_graph();raw=json.loads(NETWORK.read_text());assert(g.n,g.m)==(19,64)
    for e,row in enumerate(raw['edges']):
        assert (int(g.src[e]),int(g.dst[e]),g.c[e],g.rho[e],g.q[e])==(row['source'],row['target'],row['travel_cost'],row['threat_level'],row['capacity'])

def test_follower_unknown_edges_are_not_overwritten_as_clear():
    g,mask,e=cc2_graph();p=ScoutFixturePolicy('all',comm='all',use_obs=True,relevance_scope='reachable')
    s=cc2_factory(g,config(),p,2);cv=s.cv[1];cv.node=2;cv.peer[e]=(True,1.25,1.)
    p.decide(s,cv,3.)
    assert e not in cv.own and e in cv.believed_blocked and e in cv.peer
    assert e not in s.observation_edges(cv)

def test_hidden_sensor_state_does_not_leak_to_actor():
    g,mask,e=cc2_graph();s=cc2_factory(g,config(),Policy('x'),3);cv=s.cv[1];cv.node=2
    before=build_ctx(s,cv,set(),{},3.,8.)
    s.flow[e]=99;s.active.clear()
    after=build_ctx(s,cv,set(),{},3.,8.)
    assert torch.equal(before.X,after.X) and torch.equal(before.EF,after.EF)
    k=before.edges.index(e);assert before.EF[k,7]==0 and before.EF[k,8]==0

def test_scout_broadcast_reaches_followers_and_changes_actual_delivery():
    g,mask,e=cc2_graph();results={}
    for comm in ['none','all','gate']:
        s=cc2_factory(g,config(),ScoutFixturePolicy(comm,comm=comm,use_obs=True,relevance_scope='reachable'),2)
        results[comm]=s.run()
    assert sum(r['delivered'] for r in results['none']['rows'])==1
    assert sum(r['delivered'] for r in results['gate']['rows'])==3
    assert results['gate']['stats']['true_accepted']==2
    assert results['gate']['stats']['msg_sent']==results['all']['stats']['msg_sent']

def test_single_packet_replay_with_custom_sensor_contract_saves_receiver():
    g,mask,e=cc2_graph();p=ScoutFixturePolicy('gate',comm='gate',use_obs=True,relevance_scope='reachable')
    frame,meta,_=single_message_effects(g,config(),p,2,simulator_factory=partial(cc2_factory,hot=4))
    assert len(frame)==meta['processed_messages']==2
    assert frame.delta_delivery.eq(1).all() and meta['fir_delivery']==0

def test_fresh_simulator_has_no_report_state_from_previous_episode():
    g,mask,e=cc2_graph();p=ScoutFixturePolicy('gate',comm='gate',use_obs=True)
    s=cc2_factory(g,config(),p,3);s.run()
    fresh=cc2_factory(g,config(),p,4)
    assert all(not cv.peer and not cv.inbox and not cv.own for cv in fresh.cv)

def test_reachable_relevance_keeps_useful_alternative_warning():
    g,mask,e=cc2_graph();p=Policy('g',relevance_scope='reachable')
    s=ReviewerSim(g,config(),p,1);cv=s.cv[0];cv.node=2
    assert p.relevant(s,cv,6,[4,5])
    assert not p.relevant(s,cv,0,[4,5])

def test_future_report_rejected_with_role_sensing():
    g,mask,e=cc2_graph();p=ScoutFixturePolicy('gate',comm='gate',use_obs=True)
    s=cc2_factory(g,config(),p,2);cv=s.cv[1];cv.node=2
    cv.inbox=[dict(id='future',e=e,t_obs=100.,blocked=True,conf=1.,genuine=True)]
    p.decide(s,cv,3.)
    assert s.message_audit[-1]['reason']=='stale' and not cv.peer


def test_low_confidence_false_clear_is_harmful_only_without_filtering():
    from run_gate_fixtures import fixture_factory
    g,mask,e=cc2_graph();deliveries={}
    for comm in ['all','gate']:
        p=ScoutFixturePolicy(comm,comm=comm,use_obs=True,relevance_scope='reachable')
        result=fixture_factory(g,config(),p,3,hot=4,false_confidence=.2).run()
        deliveries[comm]=sum(r['delivered'] for r in result['rows'])
    assert deliveries=={'all':1,'gate':3}


def test_high_confidence_false_clear_exposes_gate_limit():
    from run_gate_fixtures import fixture_factory
    g,mask,e=cc2_graph();p=ScoutFixturePolicy('gate',comm='gate',use_obs=True,relevance_scope='reachable')
    result=fixture_factory(g,config(),p,3,hot=4,false_confidence=.9).run()
    assert sum(r['delivered'] for r in result['rows'])==1
    assert result['stats']['spoof_accepted']==2
