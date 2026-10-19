import copy
import numpy as np
import pytest
from research_cases import fork_graph, CASES, factory
from run_research_study import make_policy
from run_matched_gate_study import policy, METHODS, DESIGN, TEST_CASES, TRAIN_CASES

class Constant:
    def __init__(self, v): self.v=v
    def predict(self, x): return self.v,0.

@pytest.mark.parametrize('method,expected',[('ALL',False),('SAFE',True),('VALUE',False),('COMBINED',True)])
def test_exact_same_clearance_constraint_in_both_guard_arms(method,expected):
    g,h=fork_graph(55001)
    p=policy(method,model=Constant(80.));s=factory(g,h,CASES[0],p,60000123)
    cv=s.cv[2];cv.node=int(g.src[h[0]]);cv.peer[h[0]]=(True,1.,.9)
    cv.inbox=[dict(id='clear',sender=0,e=h[0],blocked=False,t_obs=2.,conf=.9,genuine=False)]
    p.decide(s,cv,3.)
    assert bool(cv.peer[h[0]][0])==expected

@pytest.mark.parametrize('method,expected',[('ALL',True),('SAFE',True),('VALUE',False),('COMBINED',True)])
def test_warning_guard_and_value_ablation_are_distinct(method,expected):
    g,h=fork_graph(55001);p=policy(method,model=Constant(-80.));s=factory(g,h,CASES[0],p,60000123)
    cv=s.cv[2];cv.node=int(g.src[h[0]])
    cv.inbox=[dict(id='warning',sender=0,e=h[0],blocked=True,t_obs=1.,conf=.9,genuine=True)]
    p.decide(s,cv,2.)
    assert (h[0] in cv.peer)==expected


def test_factorial_all_reproduces_unfiltered_episode():
    g,h=fork_graph(55003)
    a=factory(g,h,CASES[1],policy('ALL'),60000124).run()
    b=factory(g,h,CASES[1],make_policy('ALL',12.),60000124).run()
    assert a['rows']==b['rows'] and a['stats']==b['stats']


def test_factorial_gate_does_not_read_true_forgery_labels():
    g,h=fork_graph(55003);s=factory(g,h,CASES[0],policy('COMBINED',model=Constant(-80.)),60000124)
    cv=s.cv[2];cv.node=int(g.src[h[0]])
    cv.inbox=[dict(id='warning',sender=0,e=h[0],blocked=True,t_obs=1.,conf=.9,genuine=True)]
    b=copy.deepcopy(s);b.active.clear();b.cv[2].inbox[0]['genuine']=False
    assert s.policy.decide(s,cv,2.)==b.policy.decide(b,b.cv[2],2.)
    assert cv.peer==b.cv[2].peer


def test_declared_counts_and_disjoint_test_conditions():
    assert len(DESIGN['seeds'])==8 and len(METHODS)==4 and len(TEST_CASES)==8
    assert len(DESIGN['seeds'])*2*16*8*10*4==81920
    assert {c.spoof for c in TRAIN_CASES}.isdisjoint({4.,8.})
    assert TEST_CASES[-1].no_hazards and TEST_CASES[-2].lead==0


def test_paired_adaptation_copies_optimizer_and_rng_without_sharing_parameters():
    import torch
    from ammarl2.learn import LearnedPolicy
    a=LearnedPolicy('mappo',algo='mappo',seed=7,train=True,comm='all',use_obs=True)
    g,h=fork_graph(55004)
    factory(g,h,CASES[0],policy('ALL',a),60000125).run();a.end_episode()
    assert a.nupd>0 and a.opt.state
    b=copy.deepcopy(a)
    assert b.agent_nets[0] is b.net
    assert all(p is q for p,q in zip(b.opt.param_groups[0]['params'],b.net.parameters()))
    assert torch.equal(a.torch_rng.get_state(),b.torch_rng.get_state())
    assert a.rng.bit_generator.state==b.rng.bit_generator.state
    for p,q in zip(a.net.parameters(),b.net.parameters()):
        assert p is not q and torch.equal(p,q)
        assert torch.equal(a.opt.state[p]['exp_avg'],b.opt.state[q]['exp_avg'])
    with torch.no_grad():next(b.net.parameters()).add_(1.)
    assert not torch.equal(next(a.net.parameters()),next(b.net.parameters()))
