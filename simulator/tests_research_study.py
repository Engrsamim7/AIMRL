import copy
import numpy as np
import torch
from research_cases import CASES, factory, fork_graph
from research_gate import ResearchPolicy, ValueEnsemble, FEATURES, public_features
from run_research_study import make_policy, causal_examples


def explicit_hazard_fixture():
    g,h=fork_graph(44111)
    seed=40012345
    probe=factory(g,h,CASES[0],make_policy('NC',80.),seed)
    # A declared unit-test fixture: the cheaper branches are the blocked ones.
    # Scientific layout generation remains independent of attack assignment.
    for e in h:g.c[e]=.9 if e in probe.active else 1.8
    return g,h,seed

def test_physical_scout_reports_improve_timely_delivery_without_privileged_observers():
    g,h,seed=explicit_hazard_fixture()
    results={}
    for mode in ['NC','ALL']:
        s=factory(g,h,CASES[0],make_policy(mode,80.),seed)
        assert set(h).issubset(s.observation_edges(s.cv[0])) is False  # second fork is physically remote
        assert all(e not in s.observation_edges(s.cv[2]) for e in h)
        results[mode]=s.run()
    assert results['ALL']['stats']['true_accepted']>0
    assert sum(r['delivered'] for r in results['ALL']['rows'])>sum(r['delivered'] for r in results['NC']['rows'])


def test_feature_vector_does_not_read_hidden_attacks_or_evaluation_labels():
    g,h=fork_graph(44112);s=factory(g,h,CASES[0],make_policy('ALL',80.),40012346)
    cv=s.cv[2];cv.node=int(g.src[h[0]])
    m=dict(id='opaque',sender=0,e=h[0],blocked=True,t_obs=1.,conf=.9,genuine=True)
    a,_=public_features(s,cv,2.,[],m)
    other=copy.deepcopy(s);other.active.clear();m['genuine']=False
    b,_=public_features(other,other.cv[2],2.,[],m)
    # Only permitted sensors may differ; all hazard edges are outside follower coverage.
    assert np.allclose(a,b)
    assert len(a)==len(FEATURES)


def test_full_episode_prefix_labels_capture_useful_warnings():
    g,h,seed=explicit_hazard_fixture()
    rows=causal_examples(g,h,CASES[0],make_policy('ALL',80.),seed)
    assert rows and any(r['delivery_gain']>0 for r in rows)
    assert all(np.isfinite(r['utility_gain']) for r in rows)


def test_value_ensemble_serialization_and_uncertainty_are_finite():
    rng=np.random.default_rng(3);x=rng.normal(size=(100,len(FEATURES)));y=5*x[:,0]-2*x[:,1]
    model=ValueEnsemble().fit(x,y,3);other=ValueEnsemble.load(model.state())
    assert np.allclose(model.predict(x[0]),other.predict(x[0]))
    assert model.predict(x[0])[1]>=0


def test_rejected_clear_reports_can_supply_later_public_corroboration():
    g,h=fork_graph(44112);p=make_policy('SAFE-ALL',80.);s=factory(g,h,CASES[0],p,40012346)
    cv=s.cv[2];cv.node=int(g.src[h[0]]);cv.peer[h[0]]=(True,1.,.9)
    cv.inbox=[dict(id='a',sender=0,e=h[0],blocked=False,t_obs=2.,conf=.9,genuine=True),
              dict(id='b',sender=1,e=h[0],blocked=False,t_obs=2.,conf=.9,genuine=True)]
    p.decide(s,cv,3.)
    assert [m['reason'] for m in s.message_audit]==['uncorroborated_clearance','accepted']
    assert not cv.peer[h[0]][0]


def test_fresh_episode_does_not_retain_sender_agreement_or_reports():
    g,h=fork_graph(44111);p=make_policy('ALL',80.)
    a=factory(g,h,CASES[0],p,40012345);a.run()
    b=factory(g,h,CASES[0],p,40012346)
    assert all(not cv.peer and not hasattr(cv,'research_state') for cv in b.cv)
