"""Adaptive admission before a frozen deep actor; retain its binary feature contract.

The value proxy is a reference risk planner, not the neural actor's learned value.
No new neural weights or privileged centralized-critic scores drive the gate.
"""
from dataclasses import dataclass,field,asdict
from adaptive_gate import AdaptiveGate
from ammarl2.learn import LearnedPolicy

@dataclass
class AdaptiveActor(LearnedPolicy):
    gate_parameters: dict = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        if self.train:raise ValueError('This adapter evaluates frozen weights; gate-specific training is a separate experiment')
        self.comm='all'
        self.value_gate=AdaptiveGate(self.name+'-admission',weights=self.weights,alpha=self.alpha,use_obs=True,relevance_scope='reachable',**self.gate_parameters)

    def decide(self,sim,cv,t):
        self.value_gate.decide(sim,cv,t)
        state=self.value_gate.state(cv);peer={}
        for e in range(sim.g.m):
            messages=[m for m in state['reports'].values() if m['e']==e and 0<=t-m['t_obs']<=sim.cfg.tau_stale]
            anchors=[m for m in state['anchors'].values() if m['e']==e and 0<=t-m['t_obs']<=sim.cfg.tau_stale]
            # Actor receives hazard statements, not untrained continuous-probability features.
            if anchors and not self.value_gate.corroborated_clear(sim,cv,t,e,state['reports']):
                chosen=max(anchors,key=lambda m:m['t_obs']);peer[e]=(True,chosen['t_obs'],chosen['conf'])
            elif messages:
                chosen=max(messages,key=lambda m:m['t_obs']);peer[e]=(chosen['blocked'],chosen['t_obs'],chosen['conf'])
        cv.peer=peer;merged=dict(peer)
        for e,own in cv.own.items():
            if e not in merged or own[1]>=merged[e][1]:merged[e]=own
        merged={e:v for e,v in merged.items() if 0<=t-v[1]<=sim.cfg.tau_stale}
        blocked=self.banned(merged,t,sim.cfg.tau_stale)
        cv.believed_blocked=blocked
        selected=self.select(sim,cv,self.w(sim.g),blocked,merged,t)
        last=sim.trace[-1];sim.trace[-1]=(last[0],last[1],last[2],selected,selected,last[5],last[6])
        probabilities,uncertainty,_=self.value_gate.distribution(sim,cv,t)
        sim.decisions[-1].update(edge=selected,blocked_belief=sorted(blocked),estimated_probability=float(probabilities[selected]),uncertainty=float(uncertainty[selected]),selector='frozen '+self.algo+' actor; reference-planner gate proxy')
        return selected

    @classmethod
    def from_fitted(cls,fitted,parameters):
        args=asdict(fitted);args.update(name=fitted.algo.upper()+'-ADAPTIVE',train=False,eps=0.,gate_parameters=parameters)
        actor=cls(**args);actor.net.load_state_dict(fitted.net.state_dict())
        if actor.algo=='ippo':
            actor.train=True
            for slot,net in fitted.agent_nets.items():actor.agent_network(slot).load_state_dict(net.state_dict())
            actor.train=False
        return actor
