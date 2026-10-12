"""Safety constraints around the fitted actor-specific utility estimate.

Preserve fresh credible reachable hazard statements and require corroboration
before erasing warnings. Prediction remains the fitted model's actual output;
the admission override is recorded explicitly. No evaluation label is used.
"""
from dataclasses import dataclass
from research_gate import ResearchPolicy


class ConstrainedModel:
    def __init__(self, base, threshold, beta, confidence, warning_guard, clearance_guard, reachable):
        self.base,self.threshold,self.beta,self.confidence=base,threshold,beta,confidence
        self.warning_guard,self.clearance_guard=warning_guard,clearance_guard
        self.reachable=reachable
        self.calls=[]

    def predict(self,x):
        mean,std=self.base.predict(x);rule='learned_value'
        score=mean
        if self.warning_guard and x[0]>.5 and x[1]>=self.confidence and self.reachable():
            rule='preserve_credible_warning';score=max(mean,self.threshold+self.beta*std+1.)
        elif self.clearance_guard and x[0]<.5 and x[6]>.5 and x[21]<.5:
            rule='require_clearance_corroboration';score=min(mean,self.threshold+self.beta*std-1.)
        self.calls.append((mean,std,rule))
        return score,std


@dataclass
class GuardedResearchPolicy(ResearchPolicy):
    warning_guard:bool=True
    clearance_guard:bool=True
    warning_confidence:float=.4

    def features(self,sim,cv,m,t):
        result=super().features(sim,cv,m,t)
        self._candidate_reachable=self.relevant(sim,cv,m['e'],[])
        return result

    def decide(self,sim,cv,t):
        if self.mode!='value':return super().decide(sim,cv,t)
        base=self.value_model
        adapter=ConstrainedModel(base,self.value_threshold,self.uncertainty_weight,self.warning_confidence,self.warning_guard,self.clearance_guard,lambda:self._candidate_reachable)
        start=len(sim.message_audit);self.value_model=adapter
        try:edge=super().decide(sim,cv,t)
        finally:self.value_model=base
        queried=iter(adapter.calls)
        for record in sim.message_audit[start:]:
            if record['reason'] in ['accepted','predicted_low_value']:
                mean,std,rule=next(queried)
                # Never present a constraint-adjusted score as learned utility.
                record.update(predicted_value=mean,value_uncertainty=std,admission_rule=rule)
        assert next(queried,None) is None
        return edge
