import copy
from dataclasses import replace
from research_cases import CASES,fork_graph
from run_cover_traffic_stress import simulation
from run_research_study import make_policy
from ammarl2.sim import MSG

def test_cover_targets_and_payloads_do_not_reveal_private_active_edges():
    g,h=fork_graph(49000)
    case=replace(CASES[1],spoof=6.,impersonation=.9)
    a=simulation(g,h,case,make_policy('ALL',12.),45000000)
    b=copy.deepcopy(a);b.active.clear()
    start=a.event_seq;a.do_spoof(5.);b.do_spoof(5.)
    left=[payload[1] for _,seq,typ,payload in a.ev if typ==MSG and seq>=start]
    right=[payload[1] for _,seq,typ,payload in b.ev if typ==MSG and seq>=start]
    assert len(left)==len(right)==1
    assert (left[0]['e'],left[0]['blocked'])==(right[0]['e'],right[0]['blocked'])
    assert left[0]['e'] in h and left[0]['genuine'] is False

def test_cover_experiment_preserves_physically_declared_role_departures():
    g,h=fork_graph(49001)
    case=replace(CASES[1],spoof=6.,delay=4.,lead=4.)
    a=simulation(g,h,case,make_policy('ALL',12.),45000001)
    b=simulation(g,h,case,make_policy('NC',12.),45000001)
    assert [(c.id,c.target,c.depart_t) for c in a.cv]==[(c.id,c.target,c.depart_t) for c in b.cv]
    assert all(c.depart_t<1 for c in a.cv[:2]) and all(4<=c.depart_t<5 for c in a.cv[2:])
    assert a.sensing==b.sensing
