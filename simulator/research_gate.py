"""Actor-specific learned message utility with public-state features only.

The shared interpreter is timestamped binary evidence with a stronger, explicit
hazard penalty. ALL, FRC, SAFE and VALUE use the same interpreter and actor.
The ensemble predicts complete-episode marginal utility from training replays.
Its disagreement is a heuristic uncertainty measure, not a coverage guarantee.
"""
import copy
from dataclasses import dataclass, field
import numpy as np
import torch
from ammarl2.policies import Policy
from ammarl2.graph import dijkstra, dists
from ammarl2.learn import build_ctx

FEATURES = ['blocked','confidence','age_fraction','own_known','own_blocked',
            'peer_known','peer_blocked','sender_agreement','conflicting',
            'route_member','next_edge_before','next_edge_after','action_change',
            'travel_to_source','detour_extra','clear_sources','positive_sources',
            'clear_against_warning','blocked_action_change','clear_action_change',
            'conflict_confidence','clear_corroboration','warning_age','clear_age',
            'clear_peer_age','blocked_route_member']


class ValueEnsemble:
    def __init__(self, mean=None, scale=None, coefficients=None):
        self.mean, self.scale, self.coefficients = mean, scale, coefficients

    def fit(self, x, y, seed, ridge=10., members=5):
        x=np.asarray(x,float);y=np.asarray(y,float)
        self.mean=x.mean(0);self.scale=np.maximum(x.std(0),.1)
        z=np.column_stack([np.ones(len(x)),(x-self.mean)/self.scale])
        rng=np.random.default_rng(seed);models=[]
        penalty=ridge*np.eye(z.shape[1]);penalty[0,0]=.001
        for _ in range(members):
            ids=rng.integers(len(z),size=len(z));a=z[ids]
            models.append(np.linalg.solve(a.T@a+penalty,a.T@y[ids]))
        self.coefficients=np.asarray(models)
        return self

    def predict(self, features):
        x=np.asarray(features,float)
        z=np.r_[1.,(x-self.mean)/self.scale]
        predictions=self.coefficients@z
        return float(predictions.mean()),float(predictions.std())

    def state(self):
        return dict(mean=self.mean.tolist(),scale=self.scale.tolist(),coefficients=self.coefficients.tolist(),features=FEATURES)

    @classmethod
    def load(cls, state):
        assert state['features']==FEATURES
        return cls(*(np.array(state[k]) for k in ['mean','scale','coefficients']))


@dataclass
class ResearchPolicy(Policy):
    mode: str = 'all'
    actor: object = None
    value_model: object = None
    value_threshold: float = 0.
    uncertainty_weight: float = .5
    learn_agreement: bool = True

    def __post_init__(self):
        super().__post_init__()
        if self.mode not in ['none','all','frc','safe','value']:
            raise ValueError('Invalid research gate mode')
        self.comm='none' if self.mode=='none' else 'all'

    def state(self, cv):
        if not hasattr(cv,'research_state'):
            cv.research_state=dict(feedback={},confirmed=set(),agreement={},seen=set())
        return cv.research_state

    def agreement(self, cv, sender):
        if not self.learn_agreement:return 2/3
        good,bad=self.state(cv)['agreement'].get(sender,(2.,1.))
        return good/(good+bad)

    def confirm(self, cv, t, ttl):
        s=self.state(cv)
        for mid,m in list(s['feedback'].items()):
            if t-m['t_obs']>ttl:
                del s['feedback'][mid];continue
            own=cv.own.get(m['e'])
            if not self.learn_agreement or mid in s['confirmed'] or own is None or own[1]<m['t_obs']:continue
            good,bad=s['agreement'].get(m['sender'],(2.,1.))
            weight=np.exp(-(t-m['t_obs'])/ttl)
            same=bool(own[0])==bool(m['blocked'])
            s['agreement'][m['sender']]=(good+weight*same,bad+weight*(not same))
            s['confirmed'].add(mid)

    def merged(self, cv, peer, t, ttl):
        result=dict(peer)
        for e,v in cv.own.items():
            if e not in result or v[1]>=result[e][1]:result[e]=v
        return {e:v for e,v in result.items() if 0<=t-v[1]<=ttl}

    def probe(self, sim, cv, merged, t):
        blocked=self.banned(merged,t,sim.cfg.tau_stale)
        if self.actor is None:return self._route(sim.g,cv,self.w(sim.g),blocked)
        context=build_ctx(sim,cv,blocked,merged,t,sim.cfg.tau_stale)
        with torch.no_grad():scores,_=self.actor.agent_network(cv.id)(context)
        return context.edges[int(scores.argmax())]

    def features(self, sim, cv, m, t):
        g=sim.g;ttl=sim.cfg.tau_stale;e=m['e']
        before=self.merged(cv,cv.peer,t,ttl)
        proposed=dict(cv.peer);proposed[e]=(bool(m['blocked']),m['t_obs'],m['conf'])
        after=self.merged(cv,proposed,t,ttl)
        a,b=self.probe(sim,cv,before,t),self.probe(sim,cv,after,t)
        own=before.get(e) if e in cv.own and before.get(e)==cv.own[e] else None
        peer=cv.peer.get(e)
        weights=self.response_weights(self.w(g),self.banned(before,t,ttl))
        path=dijkstra(g,cv.node,cv.target,weights) or []
        alt=dijkstra(g,cv.node,cv.target,weights,banned={e}) if e in path else None
        extra=(sum(weights[x] for x in alt)-sum(weights[x] for x in path)) if alt is not None else 0.
        distance=dists(g,cv.node,sim.estimated_travel_times(cv))[g.src[e]]
        records=list(self.state(cv)['feedback'].values())
        since=peer[1] if peer and peer[0] else -1e9
        clear={r['sender'] for r in records if r['e']==e and not r['blocked'] and r['t_obs']>=since and 0<=t-r['t_obs']<=ttl}
        positive={r['sender'] for r in records if r['e']==e and r['blocked'] and 0<=t-r['t_obs']<=ttl}
        blocked=float(m['blocked']);conf=float(m['conf']);age=(t-m['t_obs'])/ttl
        prior=before.get(e);conflict=float(prior is not None and bool(prior[0])!=bool(m['blocked']))
        pblocked=float(peer is not None and peer[0]);change=float(a!=b)
        x=[blocked,conf,age,float(own is not None),float(own is not None and own[0]),
           float(peer is not None),pblocked,self.agreement(cv,m.get('sender','unknown')),conflict,
           float(e in path),float(a==e),float(b==e),change,min(float(distance),50.)/20.,extra/20.,
           min(len(clear),3)/3.,min(len(positive),3)/3.,(1-blocked)*pblocked,
           blocked*change,(1-blocked)*change,conflict*conf,(1-blocked)*float(len(clear)>=2),
           blocked*age,(1-blocked)*age,(1-blocked)*(t-peer[1])/ttl if peer else 0.,blocked*float(e in path)]
        assert len(x)==len(FEATURES) and np.isfinite(x).all()
        return x

    def decide(self, sim, cv, t):
        ttl=sim.cfg.tau_stale;s=self.state(cv)
        for e in sim.observation_edges(cv):
            observed=sim.observable(e,t);old=cv.own.get(e);cv.own[e]=(observed,t,1.)
            if self.comm!='none' and ((observed and (old is None or not old[0] or t-cv.sent.get(e,-1e9)>ttl)) or (not observed and old is not None and old[0])):
                sim.broadcast(cv,[(e,observed,1.)],t);cv.sent[e]=t
        cv.peer={e:v for e,v in cv.peer.items() if 0<=t-v[1]<=ttl}
        self.confirm(cv,t,ttl)
        accepted=[];n_in=len(cv.inbox)
        for packet in sorted(cv.inbox,key=lambda m:(m['t_obs'],m['id'])):
            m={k:packet[k] for k in ['id','e','t_obs','conf','blocked','sender']}
            e=m['e'];age=t-m['t_obs'];prior=self.merged(cv,cv.peer,t,ttl).get(e)
            reason='accepted';pred=std=0.;features=None
            if m['id'] in sim.suppressed_messages:reason='suppressed'
            elif not 0<=age<=ttl:reason='stale'
            elif m['id'] in s['seen']:reason='duplicate'
            elif self.mode=='none':reason='communication_off'
            elif prior is not None and prior[1]>=m['t_obs']:reason='superseded'
            else:
                s['feedback'][m['id']]=m
                features=self.features(sim,cv,m,t)
                if self.mode=='frc':
                    if age>self.freshness_limit(sim,cv,e):reason='freshness'
                    elif m['conf']<self.kappa_min:reason='confidence'
                    elif not self.relevant(sim,cv,e,dijkstra(sim.g,cv.node,cv.target,self.w(sim.g)) or []):reason='relevance'
                elif self.mode=='safe':
                    if not m['blocked'] and prior is not None and prior[0] and features[21]<.5:reason='uncorroborated_clearance'
                elif self.mode=='value':
                    if self.value_model is None:raise ValueError('VALUE requires a fitted training-only model')
                    pred,std=self.value_model.predict(features)
                    if pred-self.uncertainty_weight*std<=self.value_threshold:reason='predicted_low_value'
            s['seen'].add(m['id'])
            sim.message_audit.append(dict(id=m['id'],convoy=cv.id,edge=e,decision_t=t,t_obs=m['t_obs'],age=age,reason=reason,genuine=packet.get('genuine'),predicted_value=pred,value_uncertainty=std))
            if reason=='accepted':
                cv.peer[e]=(bool(m['blocked']),m['t_obs'],m['conf']);accepted.append(m['id'])
                sim.stats['true_accepted' if packet.get('genuine') else 'spoof_accepted']+=1
            else:sim.stats['rejected']+=1
        cv.inbox.clear();self.confirm(cv,t,ttl)
        merged=self.merged(cv,cv.peer,t,ttl);blocked=self.banned(merged,t,ttl)
        cv.believed_blocked=blocked
        if self.actor is None:edge=self._route(sim.g,cv,self.w(sim.g),blocked)
        else:edge=self.actor.select(sim,cv,self.w(sim.g),blocked,merged,t)
        sim.trace.append((cv.id,t,cv.node,edge,edge,n_in,len(accepted)))
        sim.decisions.append(dict(convoy=cv.id,t=t,node=cv.node,edge=edge,accepted_ids=accepted,blocked_belief=sorted(blocked)))
        return edge

    def terminal(self, *args, **kwargs):
        if self.actor is not None:self.actor.terminal(*args,**kwargs)


def public_features(sim, cv, t, prefix, packet):
    """Isolated prefix interpretation; never changes factual state or RNGs."""
    shadow=copy.copy(sim);other=copy.deepcopy(cv);other.inbox=copy.deepcopy(prefix)
    shadow.cv=list(sim.cv);shadow.cv[cv.id]=other
    shadow.stats=dict(sim.stats);shadow.trace=[];shadow.decisions=[];shadow.message_audit=[]
    shadow.broadcast=lambda *args:None
    shadow.policy.decide(shadow,other,t)
    shadow.policy.state(other)['feedback'][packet['id']]={k:packet[k] for k in ['id','e','t_obs','conf','blocked','sender']}
    prior=shadow.policy.merged(other,other.peer,t,shadow.cfg.tau_stale).get(packet['e'])
    eligible=0<=t-packet['t_obs']<=shadow.cfg.tau_stale and (prior is None or prior[1]<packet['t_obs'])
    return shadow.policy.features(shadow,other,packet,t),eligible
