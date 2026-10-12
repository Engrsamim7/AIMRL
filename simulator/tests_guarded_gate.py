import copy
from research_cases import CASES,factory,fork_graph
from guarded_research_gate import GuardedResearchPolicy

class Constant:
    def __init__(self,value):self.value=value
    def predict(self,x):return self.value,0.

def setup(value):
    g,h=fork_graph(44111)
    p=GuardedResearchPolicy('value',mode='value',value_model=Constant(value),value_threshold=-1.,weights='threat',use_obs=True,response_strength=12.,relevance_scope='reachable')
    s=factory(g,h,CASES[0],p,40012345);cv=s.cv[2];cv.node=int(g.src[h[0]])
    return s,p,cv,h[0]

def test_warning_constraint_keeps_true_prediction_in_audit():
    s,p,cv,e=setup(-80.)
    cv.inbox=[dict(id='x',sender=0,e=e,blocked=True,t_obs=1.,conf=.9,genuine=True)]
    p.decide(s,cv,2.)
    r=s.message_audit[-1]
    assert r['reason']=='accepted' and r['predicted_value']==-80.
    assert r['admission_rule']=='preserve_credible_warning'
    assert cv.peer[e][0]

def test_clearance_constraint_blocks_unsupported_clear_even_if_model_favors_it():
    s,p,cv,e=setup(80.);cv.peer[e]=(True,1.,.9)
    cv.inbox=[dict(id='x',sender=0,e=e,blocked=False,t_obs=2.,conf=.9,genuine=False)]
    p.decide(s,cv,3.)
    r=s.message_audit[-1]
    assert r['reason']=='predicted_low_value' and r['predicted_value']==80.
    assert r['admission_rule']=='require_clearance_corroboration'
    assert cv.peer[e][0]

def test_guarded_policy_does_not_receive_truth_label_or_global_attacks():
    s,p,cv,e=setup(-80.)
    cv.inbox=[dict(id='x',sender=0,e=e,blocked=True,t_obs=1.,conf=.9,genuine=True)]
    other=copy.deepcopy(s);other.active.clear();other.cv[2].inbox[0]['genuine']=False
    assert p.decide(s,cv,2.)==other.policy.decide(other,other.cv[2],2.)
    assert cv.peer==other.cv[2].peer
