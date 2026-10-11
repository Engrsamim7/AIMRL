"""Reviewer-focused failure tests for reconstructed simulator semantics."""
import copy
from dataclasses import replace
import numpy as np
import pytest
import torch
from ammarl2.graph import make_graph, Graph, optimal_nominal_cost
from ammarl2.sim import Sim, Cfg, Convoy
from ammarl2.policies import Policy, standard_methods
from ammarl2.learn import LearnedPolicy, build_ctx, gae, gctx
from ammarl2.counterfactual import single_message_effects
from ammarl2.metrics import episode_metrics, paired_delivery_difference


def test_nominal_cost_is_path_sum_and_never_below_dijkstra():
    g = make_graph(8)
    baseline = Sim(g, Cfg(attack_rate=0, p_kill=0), Policy('B1'), 12)
    baseline.run()
    for cv in baseline.cv:
        assert cv.nominal == pytest.approx(optimal_nominal_cost(g, g.depot, cv.target))
    for p in standard_methods().values():
        s = Sim(g, Cfg(p_kill=0), p, 12); out = s.run()
        metrics = episode_metrics(out['rows'])
        assert metrics['n_delivered'] == len(s.cv)
        for cv in s.cv:
            assert cv.nominal == pytest.approx(sum(g.c[e] for e in cv.path))
            assert cv.nominal >= optimal_nominal_cost(g, g.depot, cv.target) - 1e-8
            assert cv.finished_t - cv.depart_t == pytest.approx(cv.travel + cv.wait + cv.service)


def test_actor_cannot_see_remote_live_state_and_critic_does_not_change_actions():
    s = Sim(make_graph(1), Cfg(), Policy('unused'), 1); cv = s.cv[0]
    before = build_ctx(s, cv, set(), {}, 2, 8)
    remote = s.g.targets[0]
    s.busy[remote] = 100; s.queue[remote].append(cv)
    s.active[s.g.m - 1] = (0, 20)
    after = build_ctx(s, cv, set(), {}, 2, 8)
    assert torch.equal(before.X, after.X)
    assert torch.equal(before.EF, after.EF)
    p = LearnedPolicy('MAPPO', algo='mappo')
    assert torch.equal(p.net(before)[0], p.net(after)[0])
    assert not torch.equal(before.glob, after.glob)
    assert not torch.equal(p.net(before)[1], p.net(after)[1])


def test_actor_encodes_belief_age_confidence_and_elapsed_time():
    s = Sim(make_graph(2), Cfg(), Policy('unused'), 2); cv = s.cv[0]; e = s.g.out[0][0]
    c = build_ctx(s, cv, {e}, {e:(True, 1., .7)}, 3., 8.)
    row = c.edges.index(e)
    assert c.EF[row, 3] == 1
    assert c.EF[row, 4] == pytest.approx(.25)
    assert c.EF[row, 6] == pytest.approx(.7)
    assert c.EF[row, 7] == 1
    assert c.X[0, 8] == pytest.approx(3/s.cfg.horizon)


def test_congestion_scaled_freshness_and_departure_expiry():
    s = Sim(make_graph(3), Cfg(obs_radius=0, tau_stale=100), Policy('gate', comm='gate', gate_rel=False), 3)
    cv=s.cv[0]; e=s.g.out[0][0]; p=s.policy
    cv.inbox=[dict(id='one', e=e, t_obs=0., conf=1., genuine=True, blocked=True)]
    p.decide(s,cv,1.)
    assert e in cv.peer
    p.decide(s,cv,float(s.g.c[e]+.1))
    assert e not in cv.peer  # accepted reports cannot persist to the outer TTL
    s.cfg.obs_radius=1
    lim=p.freshness_limit(s,cv,e)
    s.flow[e]=20
    assert p.freshness_limit(s,cv,e)>lim
    remote=s.g.out[1][0]
    old=p.freshness_limit(s,cv,remote)
    s.flow[remote]=200
    assert p.freshness_limit(s,cv,remote)==old  # remote flow unavailable


def test_queue_wait_rejects_report_fresh_at_arrival():
    # One corridor to an intermediate bottleneck then two destinations.
    src=np.array([0,1,1]); dst=np.array([1,2,3])
    g=Graph(4,0,[2,3],src,dst,np.ones(3),np.full(3,.1),np.ones(3),np.zeros(3),[[0],[1,2],[],[]])
    p=Policy('gate',comm='gate',use_obs=False,gate_rel=False,eta=2)
    cfg=Cfg(n_convoys=2, stagger=0, hub_cap=1, hub_service=5, attack_rate=0,tau_msg=0,tau_stale=20)
    s=Sim(g,cfg,p,1)
    s.cv[0].depart_t=0; s.cv[1].depart_t=.1
    from ammarl2.sim import MSG
    s.push(1.2,MSG,(1,dict(id='wait-report', e=1, t_obs=1.2,blocked=True,conf=1.,genuine=True)))
    s.run()
    record=next(x for x in s.message_audit if x['id']=='wait-report')
    assert s.cv[1].wait>0
    assert record['decision_t']>10
    assert record['reason']=='freshness'


def test_full_random_attack_replay_and_message_loss_identity():
    g=make_graph(7)
    a=Sim(g,Cfg(p_kill=0),Policy('B1'),9)
    b=Sim(g,Cfg(p_kill=0),Policy('threat',weights='threat'),9)
    a.run(); b.run(); cutoff=min(a.t,b.t)
    assert [x for x in a.attack_log if x[0]<=cutoff]==[x for x in b.attack_log if x[0]<=cutoff]
    a=Sim(g,Cfg(p_loss=.5),Policy('a'),9); b=copy.deepcopy(a)
    a.broadcast(a.cv[0],[(0,True,1.)],1)
    b.broadcast(b.cv[1],[(1,True,1.)],.5)
    b.broadcast(b.cv[0],[(0,True,1.)],1)
    ids=lambda s:{m['id'] for t,k,typ,(cid,m) in s.ev if m['sender']==0}
    assert ids(a)==ids(b)


def test_single_message_replay_and_rejected_message_zero_effect():
    g=make_graph(2)
    cfg=Cfg(n_convoys=4,attack_rate=0,spoof_rate=2,tau_msg=0,obs_radius=0,horizon=100)
    p=Policy('gate',comm='gate',gate_conf=True,kappa_min=1,gate_rel=False)
    effects,meta,out=single_message_effects(g,cfg,p,5,max_messages=4)
    assert len(effects)==4
    assert not effects.changed_receiver_path.any()
    assert (effects.delta_delivery==0).all()
    assert (effects.delta_blocked_encounters==0).all()
    assert meta['selection'].startswith('first')
    with pytest.raises(ValueError,match='Controlled FIR'):
        single_message_effects(g,replace(cfg,adv='reactive'),p,5)


def test_response_strength_is_independent_of_gate():
    w=np.array([2.,4.])
    for comm in ('none','all','gate'):
        p=Policy(comm,comm=comm,response_strength=0)
        assert np.array_equal(p.response_weights(w,{0}),w)
        p.response_strength=12
        assert np.array_equal(p.response_weights(w,{0}),[14,4])


def test_mask_excludes_unreachable_heads_in_selection_and_bootstrap():
    g=make_graph(1); g.targets=[g.targets[0]]
    g.dst[0]=g.n-1 # disconnected other sink is now not the assigned target
    s=Sim(g,Cfg(n_convoys=1,attack_rate=0),Policy('unused'),1)
    c=build_ctx(s,s.cv[0],set(),{},0,8)
    assert 0 not in c.edges
    p=LearnedPolicy('dqn',train=True,dqn_warmup=1,dqn_batch_size=1,dqn_update_interval=1)
    before=[x.detach().clone() for x in p.net.parameters()]
    p.buf=[(c,0,-1,c,False,.99)]
    p._dqn_update()
    assert p.nupd==1
    assert any(not torch.equal(x,y) for x,y in zip(before,p.net.parameters()))


@pytest.mark.parametrize('algo',['dqn','ppo','ippo','mappo'])
def test_real_optimizer_updates_and_horizon_finalization(algo):
    p=LearnedPolicy(algo,algo=algo,train=True,comm='gate',use_obs=True,
                    dqn_warmup=1,dqn_batch_size=1,dqn_update_interval=1,ppo_epochs=1)
    before=[x.detach().clone() for x in p.net.parameters()]
    s=Sim(make_graph(11),Cfg(n_convoys=2,attack_rate=0,horizon=2),p,3)
    out=s.run(); p.end_episode()
    assert p.nupd>0 and np.isfinite(p.losses).all()
    assert not p.pend
    assert sum(r['censored'] for r in out['rows'])==2
    assert any(not torch.equal(x,y) for x,y in zip(before,p.net.parameters()))


def test_terminal_gae_does_not_leak_across_episodes():
    tr=[(None,0,0.,1.,2.,True,.9),(None,0,0.,100.,100.,True,.9)]
    data=gae(tr,.95)
    assert data[1][3]==pytest.approx(1.)


def test_sparse_adjacency_and_topology_cache_identity():
    g=make_graph(1,layers=20,width=24)
    a=gctx(g)[0]
    assert a.is_sparse and a._nnz() <= g.n+2*g.m
    changed=copy.deepcopy(g); changed.dst[0]=changed.dst[1]
    assert gctx(changed)[0] is not a


def test_pairing_rejects_different_schedules():
    import pandas as pd
    a=pd.DataFrame([dict(convoy=0,target=1,depart_t=0,delivered=1,nominal=3)])
    b=a.copy(); b.depart_t=1
    with pytest.raises(ValueError,match='identical'):
        paired_delivery_difference(a,b)


def test_single_message_intervention_can_save_receiver(monkeypatch):
    import ammarl2.counterfactual as cf
    from ammarl2.sim import MSG, UNBLOCK
    g=Graph(4,0,[3],np.array([0,0,1,2]),np.array([1,2,3,3]),
            np.array([1.,2.,2.,2.]),np.full(4,.1),np.ones(4),np.zeros(4),[[0,1],[2],[3],[]])
    class FixtureSim(Sim):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.cv[0].depart_t=1.
            self.active[0]=(0.,100.)
            self.push(100.,UNBLOCK,0)
            self.push(0.,MSG,(0,dict(id='life-saving',e=0,t_obs=0.,blocked=True,conf=1.,genuine=True)))
    monkeypatch.setattr(cf,'Sim',FixtureSim)
    df,metadata,result=cf.single_message_effects(g,Cfg(n_convoys=1,attack_rate=0,p_kill=1),
                                               Policy('ALL',comm='all'),3)
    assert len(df)==1
    assert df.iloc[0].delta_delivery==1
    assert df.iloc[0].delta_blocked_encounters==-1
    assert df.iloc[0].failed_delivery_information==0
    assert metadata['fir_delivery']==0


def test_ippo_has_independent_agents_and_rejects_untrained_slots():
    p=LearnedPolicy('IPPO',algo='ippo',train=True)
    a=p.agent_network(0); b=p.agent_network(1)
    assert a is not b and p.agent_opts[0] is not p.agent_opts[1]
    p.train=False
    with pytest.raises(ValueError,match='population'):
        p.agent_network(2)


def test_wrong_destination_is_not_delivery():
    g=make_graph(2)
    s=Sim(g,Cfg(n_convoys=1),Policy('unused'),1)
    cv=s.cv[0]
    wrong=next(t for t in g.targets if t!=cv.target)
    edge=next(e for e in range(g.m) if g.dst[e]==wrong)
    cv.node=int(g.src[edge])
    with pytest.raises(ValueError,match='invalid'):
        s.enter_edge(cv,edge,1)


def test_known_blocked_entry_is_distinct_from_surprise_encounter():
    g=make_graph(3); s=Sim(g,Cfg(n_convoys=1,p_kill=0),Policy('unused'),1)
    e=g.out[0][0];s.active[e]=(0,100);s.cv[0].believed_blocked={e}
    s.enter_edge(s.cv[0],e,1)
    assert s.cv[0].enc==1 and s.cv[0].surprise_enc==0


def test_reactive_adversary_observation_delay():
    g=make_graph(3);s=Sim(g,Cfg(n_convoys=1,adv='reactive',react_eps=0,react_delay=5),Policy('unused'),1)
    # Pick the lowest-prior edge so the delayed traffic signal determines choice.
    edge=int(g.rho.argmin());s.traffic_history=[(1.,edge)]
    s.do_attack(2.)
    assert s.attack_log[-1][1]!=edge
    s.active.clear();s.do_attack(7.)
    assert s.attack_log[-1][1]==edge


def test_horizon_times_are_accrued_not_scheduled():
    s=Sim(make_graph(3),Cfg(n_convoys=1,attack_rate=0,horizon=1),Policy('B1'),1)
    s.cv[0].depart_t=.5
    row=s.run()['rows'][0]
    assert row['elapsed']==pytest.approx(.5)
    assert row['travel']==pytest.approx(.5)
    assert row['censored']==1


def test_zero_strength_has_same_routing_outcomes_with_and_without_filtering():
    cfg=Cfg(n_convoys=8,spoof_rate=2,tau_msg=2)
    outcomes=[]
    for comm in ('none','all','gate'):
        p=Policy(comm,comm=comm,use_obs=True,weights='threat',response_strength=0)
        s=Sim(make_graph(300,layers=6,width=6),cfg,p,1500)
        s.run()
        outcomes.append([(cv.path,cv.delivered,cv.nominal,cv.enc,cv.wait) for cv in s.cv])
    assert outcomes[0]==outcomes[1]==outcomes[2]
