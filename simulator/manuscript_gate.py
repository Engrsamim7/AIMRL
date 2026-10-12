"""Synthetic manuscript-mechanism comparator; not exact paper reproduction.

Hub-only per-slot Q is intentionally historical. Reward ambiguity is resolved as
negative nominal/threat step cost, terminal delivery bonus and explicit death cost.
These choices are logged and must be reconciled against original submission code.
"""
from dataclasses import dataclass, field
import numpy as np
from ammarl2.policies import Policy
from ammarl2.graph import dijkstra

@dataclass
class ManuscriptGate(Policy):
    q: dict = field(default_factory=dict)
    local_strength: float = 8.
    peer_strength: float = 12.
    fork_delta: float = .15
    training: bool = False
    learner_seed: int = 0
    alpha_q: float = .15
    gamma_q: float = .93
    pending: dict = field(default_factory=dict)
    steps: int = 0

    def __post_init__(self):
        super().__post_init__()
        self.scaling = 'static'
        self.eta = .4
        self.rng = np.random.default_rng(self.learner_seed)

    def candidates(self, sim, cv):
        return [e for e in sim.g.out[cv.node]
                if dijkstra(sim.g, int(sim.g.dst[e]), cv.target, sim.g.c) is not None]

    def key(self, cv, e):
        # Targets are fixed by convoy slot in the runner; historical hub/edge Q.
        return (cv.id, int(e))

    def value(self, cv, e):
        return self.q.get(self.key(cv,e), 0.)

    def fork(self, sim, cv):
        es=sim.g.out[cv.node]
        return len(es)>=2 and np.ptp(sim.g.rho[es])>self.fork_delta

    def update(self, sim, cv, terminal=False, truncated=False):
        old=self.pending.pop(cv.id,None)
        if old is None or not self.training:
            return
        e=old
        reward=-float(sim.g.c[e])-14.*float(sim.g.rho[e])
        if terminal:
            reward=(40.+float(np.prod(1.-sim.g.rho[cv.path]))-.04*cv.nominal
                    if cv.delivered else -40.)
        future=0. if terminal else max(self.value(cv,a) for a in self.candidates(sim,cv))
        k=self.key(cv,e)
        self.q[k]=self.value(cv,e)+self.alpha_q*(reward+self.gamma_q*future-self.value(cv,e))

    def terminal(self, sim, cv, t, death=False, truncated=False):
        self.update(sim,cv,terminal=True,truncated=truncated)

    def decide(self, sim, cv, t):
        self.update(sim,cv)
        g,cfg=sim.g,sim.cfg
        for e in sim.edges_in_radius(cv.node):
            b=sim.observable(e,t); prev=cv.own.get(e)
            cv.own[e]=(b,t,1.)
            if self.comm!='none' and ((b and (prev is None or not prev[0] or t-cv.sent.get(e,-1e9)>cfg.tau_stale)) or (not b and prev is not None and prev[0])):
                sim.broadcast(cv,[(e,b,1.)],t); cv.sent[e]=t
        cv.peer={e:v for e,v in cv.peer.items() if 0<=t-v[1]<=cfg.tau_stale}
        for m in sorted(cv.inbox,key=lambda m:(m['t_obs'],m['id'])):
            e=m['e']; age=t-m['t_obs']; current=max(cv.own.get(e,(0,-1e9,0))[1],cv.peer.get(e,(0,-1e9,0))[1])
            reason='accepted'
            if self.comm=='none': reason='communication_off'
            elif m['id'] in sim.suppressed_messages: reason='suppressed'
            elif age<0 or age>cfg.tau_stale: reason='stale'
            elif m['t_obs']<=current: reason='superseded'
            # Buffer first; gate is evaluated at use, not packet arrival/admission.
            if reason=='accepted': cv.peer[e]=(m['blocked'],m['t_obs'],m['conf'])
            sim.message_audit.append(dict(id=m['id'],convoy=cv.id,edge=e,decision_t=t,reason=reason))
        cv.inbox.clear()
        es=self.candidates(sim,cv); fork=self.fork(sim,cv); scores={}; accepted=[]; blocked=set()
        for e in es:
            peer=cv.peer.get(e); own=cv.own.get(e)
            own_valid=own is not None and 0<=t-own[1]<=cfg.tau_stale
            # Newer local evidence supersedes buffered peer evidence, including clear reports.
            valid=peer is not None and (not own_valid or peer[1]>own[1])
            reason='no_peer'
            if valid:
                reason='accepted'
                if self.comm=='gate':
                    if self.gate_fresh and t-peer[1]>.4*cfg.tau_stale: reason='freshness'
                    elif self.gate_rel and not fork: reason='relevance'
                    elif self.gate_conf and peer[2]<self.kappa_min: reason='confidence'
            use=valid and reason=='accepted' and self.comm!='none'
            score=self.value(cv,e)
            if fork:
                hazard=bool(peer[0]) if use else bool(own[0]) if own_valid else False
                score-=(self.peer_strength if use else self.local_strength)*hazard
                if hazard: blocked.add(e)
            if use and fork: accepted.append(e)
            scores[e]=score
            if peer is not None:
                sim.decisions.append(dict(convoy=cv.id,t=t,node=cv.node,candidate=e,peer_used=bool(use and fork),reason=reason,score=score))
        epsilon=max(.05,.990**self.steps) if self.training else 0.
        selected=int(self.rng.choice(es)) if self.rng.random()<epsilon else max(es,key=lambda e:scores[e])
        self.steps+=1; self.pending[cv.id]=selected
        cv.believed_blocked=blocked
        sim.trace.append((cv.id,t,cv.node,selected,selected,0,len(accepted)))
        return selected
