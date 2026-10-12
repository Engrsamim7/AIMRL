"""Model-based value gate with uncertain multi-source evidence and local feedback.

The probability/utility estimates are heuristic model quantities, not calibrated
posteriors or guarantees. No genuine/spoof labels or hidden global state are read.
State is attached to each convoy, so it resets each episode and survives replay.
"""
from dataclasses import dataclass
import math
import numpy as np
from ammarl2.policies import Policy
from ammarl2.graph import dijkstra,dists


def sigmoid(x):return 1./(1.+math.exp(-float(np.clip(x,-30,30))))
def logit(p):return math.log(float(np.clip(p,.001,.999))/(1.-float(np.clip(p,.001,.999))))

@dataclass
class AdaptiveGate(Policy):
    mode: str = 'value'          # none | all | frc | value
    min_value: float = .1
    innovation_weight: float = 1.
    age_scale: float = 4.
    risk_aversion: float = .25
    unknown_block_probability: float = .05
    prior_success: float = 2.
    prior_failure: float = 1.
    confirmation_window: float = 8.
    adapt_reliability: bool = True
    forced_scout_routes: bool = False
    clearance_guard: bool = True
    clearance_quorum: int = 2

    def __post_init__(self):
        super().__post_init__()
        if self.mode not in ['none','all','frc','value'] or min(self.min_value,self.innovation_weight,self.risk_aversion)<0 or min(self.age_scale,self.confirmation_window,self.prior_success,self.prior_failure)<=0:
            raise ValueError('Invalid adaptive gate parameters')
        if not 0<self.unknown_block_probability<1:raise ValueError('Invalid unknown-block prior')
        self.comm='none' if self.mode=='none' else 'all'

    def state(self,cv):
        if not hasattr(cv,'value_state'):
            cv.value_state=dict(reports={},feedback={},confirmed=set(),seen=set(),reputation={},anchors={})
        return cv.value_state

    def trust(self,state,sender):
        good,bad=state['reputation'].get(sender,(self.prior_success,self.prior_failure))
        return good/(good+bad)

    def confirm(self,cv,t):
        state=self.state(cv)
        if not self.adapt_reliability:return
        for mid,m in state['feedback'].items():
            own=cv.own.get(m['e']);age=t-m['t_obs']
            if mid in state['confirmed'] or own is None or own[1]<m['t_obs'] or not 0<=age<=self.confirmation_window:continue
            weight=math.exp(-age/self.confirmation_window)
            good,bad=state['reputation'].get(m['sender'],(self.prior_success,self.prior_failure))
            matches=bool(own[0])==bool(m['blocked'])
            state['reputation'][m['sender']]=(good+weight*matches,bad+weight*(not matches))
            state['confirmed'].add(mid)

    def corroborated_clear(self,sim,cv,t,e,reports):
        state=self.state(cv)
        anchors=[m for m in state['anchors'].values() if m['e']==e and 0<=t-m['t_obs']<=sim.cfg.tau_stale]
        since=max([m['t_obs'] for m in anchors],default=-1e9)
        observed={m['id']:m for m in state['feedback'].values()}
        observed.update({m['id']:m for m in reports.values()})
        sources={m['sender'] for m in observed.values() if m['e']==e and not m['blocked'] and m['t_obs']>=since and 0<=t-m['t_obs']<=sim.cfg.tau_stale and m['conf']>=self.kappa_min and self.trust(state,m['sender'])>=.6}
        return len(sources)>=self.clearance_quorum

    def distribution(self,sim,cv,t,reports=None):
        g=sim.g;state=self.state(cv);records=state['reports'] if reports is None else reports
        times=sim.estimated_travel_times(cv);eta=dists(g,cv.node,times)
        evidence=np.zeros(g.m);mass=np.zeros(g.m);positive=np.zeros(g.m);negative=np.zeros(g.m)
        for m in records.values():
            e=m['e'];age=t-m['t_obs']
            if not 0<=age<=sim.cfg.tau_stale:continue
            own=cv.own.get(e)
            if own is not None and own[1]>=m['t_obs'] and 0<=t-own[1]<=sim.cfg.tau_stale:continue
            if not np.isfinite(eta[int(g.src[e])]):continue
            credibility=.5+.49*float(np.clip(m['conf'],0,1))*self.trust(state,m['sender'])
            decay=math.exp(-(age+eta[int(g.src[e])])/(self.age_scale*max(times[e],.001)))
            contribution=decay*logit(credibility)
            evidence[e]+=contribution*(1 if m['blocked'] else -1);mass[e]+=abs(contribution)
            if m['blocked']:positive[e]+=contribution
            else:negative[e]+=contribution
        probability=np.array([sigmoid(logit(p)+x) for p,x in zip(np.full(g.m,self.unknown_block_probability),evidence)])
        disagreement=2*np.minimum(positive,negative)/np.maximum(mass,1e-12)
        uncertainty=np.minimum(1.,1./(1.+mass)+disagreement)
        for e,own in cv.own.items():
            if 0<=t-own[1]<=sim.cfg.tau_stale:probability[e]=float(own[0]);uncertainty[e]=0.
        risk=np.clip(probability+self.risk_aversion*uncertainty*np.sqrt(probability*(1-probability)),0,1)
        if self.mode=='value' and self.clearance_guard:
            anchor_mass=np.zeros(g.m)
            for m in state['anchors'].values():
                e=m['e'];age=t-m['t_obs']
                if not 0<=age<=sim.cfg.tau_stale or not np.isfinite(eta[int(g.src[e])]):continue
                credibility=.5+.49*float(np.clip(m['conf'],0,1))*self.trust(state,m['sender'])
                decay=math.exp(-(age+eta[int(g.src[e])])/(self.age_scale*max(times[e],.001)))
                anchor_mass[e]+=decay*logit(credibility)
            for e in np.flatnonzero(negative>0):
                own=cv.own.get(e)
                if own is not None and 0<=t-own[1]<=sim.cfg.tau_stale:continue
                if self.corroborated_clear(sim,cv,t,e,records):continue
                floor_p=sigmoid(logit(self.unknown_block_probability)+anchor_mass[e])
                floor_u=1./(1.+anchor_mass[e])
                floor_risk=min(1.,floor_p+self.risk_aversion*floor_u*math.sqrt(floor_p*(1-floor_p)))
                probability[e]=max(probability[e],floor_p)
                risk[e]=max(risk[e],floor_risk)
        return probability,uncertainty,self.w(g)+self.response_strength*risk

    def decide(self,sim,cv,t):
        g,cfg=sim.g,sim.cfg;state=self.state(cv)
        for e in sim.observation_edges(cv):
            blocked=sim.observable(e,t);prev=cv.own.get(e);cv.own[e]=(blocked,t,1.)
            if self.comm!='none' and ((blocked and (prev is None or not prev[0] or t-cv.sent.get(e,-1e9)>cfg.tau_stale)) or (not blocked and prev is not None and prev[0])):
                sim.broadcast(cv,[(e,blocked,1.)],t);cv.sent[e]=t
        self.confirm(cv,t)
        state['reports']={k:m for k,m in state['reports'].items() if 0<=t-m['t_obs']<=cfg.tau_stale and (self.mode!='frc' or t-m['t_obs']<=self.freshness_limit(sim,cv,m['e']))}
        state['anchors']={k:m for k,m in state['anchors'].items() if 0<=t-m['t_obs']<=cfg.tau_stale}
        state['feedback']={mid:m for mid,m in state['feedback'].items() if 0<=t-m['t_obs']<=self.confirmation_window}
        accepted=[];n_in=len(cv.inbox)
        for packet in sorted(cv.inbox,key=lambda m:(m['t_obs'],m.get('id',''))):
            # Extract only public envelope/payload; genuine is read solely when logging evaluation.
            m={k:packet[k] for k in ['id','e','t_obs','conf','blocked']};m['sender']=packet.get('sender','unidentified')
            e=m['e'];age=t-m['t_obs'];reason='accepted';utility=0.;innovation=0.;reliability=self.trust(state,m['sender'])
            key=(e,m['sender']);previous=state['reports'].get(key);own=cv.own.get(e)
            if m['id'] in sim.suppressed_messages:reason='suppressed'
            elif not 0<=age<=cfg.tau_stale:reason='stale'
            elif m['id'] in state['seen']:reason='duplicate'
            elif self.mode=='none':reason='communication_off'
            else:
                state['feedback'][m['id']]=m
                if own is not None and own[1]>=m['t_obs'] and 0<=t-own[1]<=cfg.tau_stale:reason='local_newer'
                elif previous is not None and previous['t_obs']>=m['t_obs']:reason='superseded'
                else:
                    before,uncertainty,weights=self.distribution(sim,cv,t)
                    plan=dijkstra(g,cv.node,cv.target,weights) or []
                    proposed=dict(state['reports']);proposed[key]=m
                    after,_,new_weights=self.distribution(sim,cv,t,proposed)
                    new_plan=dijkstra(g,cv.node,cv.target,new_weights) or []
                    utility=max(0.,sum(new_weights[a] for a in plan)-sum(new_weights[a] for a in new_plan))
                    innovation=abs(after[e]-before[e])
                    relevant=self.relevant(sim,cv,e,plan)
                    if self.mode=='frc':
                        if age>self.freshness_limit(sim,cv,e):reason='freshness'
                        elif m['conf']<self.kappa_min:reason='confidence'
                        elif not relevant:reason='relevance'
                    elif self.mode=='value':
                        if not relevant:reason='relevance'
                        elif utility+self.innovation_weight*innovation*uncertainty[e]<self.min_value:
                            reason='uncorroborated_clearance' if self.clearance_guard and not m['blocked'] and not self.corroborated_clear(sim,cv,t,e,proposed) else 'low_estimated_value'
            state['seen'].add(m['id'])
            sim.message_audit.append(dict(id=m['id'],convoy=cv.id,edge=e,decision_t=t,t_obs=m['t_obs'],age=age,reason=reason,genuine=packet.get('genuine'),estimated_route_regret=utility,innovation=innovation,estimated_sender_agreement=reliability))
            if reason=='accepted':
                state['reports'][key]=m;accepted.append(m['id'])
                if m['blocked'] and m['conf']>=self.kappa_min:state['anchors'][key]=m
                sim.stats['true_accepted' if packet.get('genuine') else 'spoof_accepted']+=1
            else:sim.stats['rejected']+=1
        cv.inbox.clear();self.confirm(cv,t)
        probability,uncertainty,weights=self.distribution(sim,cv,t)
        path=dijkstra(g,cv.node,cv.target,weights)
        if not path:raise ValueError('No route to assigned target')
        edge=path[0]
        if self.forced_scout_routes and cv.node==0:
            wanted=3 if cv.id==0 else 1;edge=next(e for e in g.out[0] if g.dst[e]==wanted)
        cv.believed_blocked={e for e in range(g.m) if probability[e]>=.5}
        sim.trace.append((cv.id,t,cv.node,edge,edge,n_in,len(accepted)))
        sim.decisions.append(dict(convoy=cv.id,t=t,node=cv.node,edge=edge,accepted_ids=accepted,blocked_belief=sorted(cv.believed_blocked),estimated_probability=float(probability[edge]),uncertainty=float(uncertainty[edge]),reputation_sources=len(state['reputation'])))
        return edge
