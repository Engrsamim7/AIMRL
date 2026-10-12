import copy
import numpy as np
from ammarl2.graph import Graph
from ammarl2.sim import Sim,Cfg
from manuscript_gate import ManuscriptGate

def fixture(**kw):
    g=Graph(3,0,[2],np.array([0,0,1]),np.array([2,1,2]),np.ones(3),np.array([.5,.1,.1]),np.ones(3),np.array([0,1,1]),[[0,1],[2],[]])
    p=ManuscriptGate('test',comm='gate',**kw)
    s=Sim(g,Cfg(n_convoys=1,obs_radius=0,attack_rate=0),p,1)
    return s,p,s.cv[0]

def packet(cv,age=0,conf=1):
    cv.inbox=[dict(id='x',e=0,t_obs=-age,conf=conf,blocked=True,genuine=True)]

def test_fresh_warning_changes_route_and_q_is_frozen():
    s,p,cv=fixture(); p.q[(0,0)]=5; p.q[(0,1)]=0
    original=copy.deepcopy(p.q); packet(cv)
    assert p.decide(s,cv,0)==1
    assert p.q==original

def test_stale_low_confidence_and_retained_age_are_checked_at_use():
    for age,conf in [(3.3,1),(0,.59)]:
        s,p,cv=fixture();p.q[(0,0)]=5;packet(cv,age,conf)
        assert p.decide(s,cv,0)==0
    s,p,cv=fixture();p.q[(0,0)]=5;packet(cv)
    assert p.decide(s,cv,0)==1
    assert p.decide(s,cv,3.3)==0

def test_nonfork_and_off_next_hop_do_not_change_action():
    s,p,cv=fixture();s.g.rho[:]=.1;p.q[(0,0)]=5;packet(cv)
    assert p.decide(s,cv,0)==0
    s,p,cv=fixture();p.q[(0,0)]=5;packet(cv);cv.inbox[0]['e']=2
    assert p.decide(s,cv,0)==0

def test_zero_response_and_new_local_clear_evidence():
    s,p,cv=fixture(local_strength=0,peer_strength=0);p.q[(0,0)]=5;packet(cv)
    assert p.decide(s,cv,0)==0
    s,p,cv=fixture();p.q[(0,0)]=5;cv.peer[0]=(True,0,1);cv.own[0]=(False,1,1)
    assert p.decide(s,cv,1)==0

def test_terminal_learning_has_no_bootstrap():
    s,p,cv=fixture(training=True);p.pending[0]=0;p.q[(0,0)]=10
    cv.alive=False;p.terminal(s,cv,1,True)
    assert np.isclose(p.q[(0,0)],2.5)
