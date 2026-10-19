"""Dynamic recovery physics and bounded, two-sided learned admission.

No origin, active hazard, case identity or future recovery enters gate features.
Original simulator and previous studies stay unchanged.
"""
import copy
from dataclasses import dataclass, replace
import numpy as np
import torch
from torch import nn
from ammarl2.graph import dijkstra, dists
from ammarl2.sim import UNBLOCK
from research_cases import Case, fork_graph, factory
from run_cover_traffic_stress import CoverSim
from research_gate import ResearchPolicy

FEATURES=['blocked','confidence','age_fraction','peer_known','peer_blocked','peer_confidence','peer_age',
          'own_known','own_blocked','sender_agreement','clear_sources','warning_sources','clear_quorum',
          'reachable','reference_route_member','reference_action_change','distance_to_source','detour_extra',
          'remaining_reference_cost','edge_cost','clear_against_warning','conflict','follower','time_fraction',
          'later_same_edge','later_clear_sources','later_warning_sources','latest_later_age','edge_at_node',
          'reference_after_length']

@dataclass(frozen=True)
class RecoveryCase(Case):
    recovery:float=.5
    recovery_window:tuple=(1.2,3.5)

TRAIN=[RecoveryCase('train-persistent',recovery=0.,spoof=2.,loss=.1,impersonation=.9),
       RecoveryCase('train-mix25',recovery=.25,spoof=2.,loss=.1,impersonation=.9),
       RecoveryCase('train-mix75',recovery=.75,spoof=2.,loss=.1,impersonation=.9),
       RecoveryCase('train-recovery',recovery=1.,spoof=2.,loss=.1,impersonation=.9),
       RecoveryCase('train-loss',recovery=.75,spoof=2.,loss=.2,impersonation=.9),
       RecoveryCase('train-delay',recovery=.75,spoof=2.,delay=2.,loss=.1,impersonation=.9),
       RecoveryCase('train-late',recovery=.5,spoof=2.,lead=0.,delay=8.,loss=.1,impersonation=.9),
       RecoveryCase('train-no-hazard',recovery=.5,spoof=2.,no_hazards=True,loss=.1,impersonation=.9)]
TEST=[replace(TRAIN[0],name='persistent'),
      RecoveryCase('mixed-recovery',recovery=.5,spoof=2.,loss=.1,impersonation=.9),
      replace(TRAIN[3],name='rapid-recovery'),
      RecoveryCase('unseen-loss',recovery=.5,spoof=2.,loss=.35,impersonation=.9),
      RecoveryCase('unseen-delay',recovery=.5,spoof=2.,delay=3.,loss=.1,impersonation=.9),
      RecoveryCase('unseen-corruption',recovery=.5,spoof=4.,loss=.2,impersonation=.9),
      replace(TRAIN[6],name='late-control'),replace(TRAIN[7],name='no-hazard-control')]
METHODS=['ALL','SAFE','KEEP','AGE','LEARN']


def graph(seed,stages=2,test=False):
    g,h=fork_graph(seed,stages)
    rng=np.random.default_rng(np.random.SeedSequence([seed,411]))
    scale=float(rng.uniform(1.,2. if test else 1.5))
    for k in range(stages):g.c[7*k+5:7*k+7]*=scale
    return g,h


def simulation(g,h,case,p,seed):
    # Suppress legacy initial blocks, retaining the same physical sensors/roles.
    s=factory(g,h,replace(case,no_hazards=True),p,seed)
    s.__class__=CoverSim;s.case=case;s.cover_edges=h;s.recovery_schedule=[]
    rng=np.random.default_rng(np.random.SeedSequence([seed,8812]))
    earliest=dists(g,g.depot,g.c)
    if not case.no_hazards:
        for stage in range(len(h)//2):
            e=int(rng.choice(h[2*stage:2*stage+2]));recover=bool(rng.random()<case.recovery)
            approach=int(g.src[7*stage])
            expiry=float(earliest[approach]+rng.uniform(*case.recovery_window if recover else (35.,50.)))
            s.active[e]=(0.,expiry);s.attack_log.append((0.,e));s.stats['attacks']+=1;s.push(expiry,UNBLOCK,e)
            s.recovery_schedule.append(dict(stage=stage,edge=e,expiry=expiry,temporary=recover))
    return s


class HurdleNet(nn.Module):
    def __init__(self):
        super().__init__();self.body=nn.Sequential(nn.Linear(len(FEATURES),48),nn.Tanh(),nn.Linear(48,48),nn.Tanh());self.head=nn.Linear(48,5)
    def forward(self,x):return self.head(self.body(x))


class HurdleEnsemble:
    """Impact probability × conditional utility; separate delivery-risk head.

    Bootstrap disagreement and head risks are heuristic, not calibrated bounds.
    """
    def __init__(self):self.networks=[]
    def fit(self,x,y,delivery,seed):
        x=np.asarray(x,float);y=np.asarray(y,float);delivery=np.asarray(delivery,int)
        self.mean=x.mean(0);self.scale=np.maximum(x.std(0),.1)
        z=torch.tensor((x-self.mean)/self.scale,dtype=torch.float32)
        target=torch.tensor(y/80.,dtype=torch.float32);impact=torch.tensor(np.abs(y)>.1,dtype=torch.float32)
        risk=torch.tensor(delivery+1,dtype=torch.long);rng=np.random.default_rng(seed)
        for member in range(3):
            torch.manual_seed(seed+member);net=HurdleNet();opt=torch.optim.Adam(net.parameters(),lr=.003)
            ids=torch.tensor(rng.integers(len(z),size=len(z)),dtype=torch.long)
            a,b,c,r=z[ids],target[ids],impact[ids],risk[ids]
            for _ in range(100):
                out=net(a);loss=nn.functional.binary_cross_entropy_with_logits(out[:,0],c)
                mask=c.bool()
                if mask.any():loss=loss+nn.functional.mse_loss(out[mask,1],b[mask])
                loss=loss+.5*nn.functional.cross_entropy(out[:,2:],r)
                opt.zero_grad();loss.backward();nn.utils.clip_grad_norm_(net.parameters(),5.);opt.step()
            net.eval();self.networks.append(net)
        return self
    def predict(self,x):
        z=torch.tensor((np.asarray(x,float)-self.mean)/self.scale,dtype=torch.float32)
        with torch.no_grad():
            out=torch.stack([n(z) for n in self.networks]);mu=(out[:,0].sigmoid()*out[:,1]*80.).numpy();risk=out[:,2:].softmax(-1).numpy()
        return float(mu.mean()),float(mu.std()),float(np.clip(risk[:,0].mean()+.5*risk[:,0].std(),0,1)),float(np.clip(risk[:,2].mean()+.5*risk[:,2].std(),0,1))
    def state(self):
        return dict(features=FEATURES,mean=self.mean.tolist(),scale=self.scale.tolist(),networks=[{k:v.detach().numpy().tolist() for k,v in n.state_dict().items()} for n in self.networks])
    @classmethod
    def load(cls,state):
        assert state['features']==FEATURES
        m=cls();m.mean=np.array(state['mean']);m.scale=np.array(state['scale'])
        for weights in state['networks']:
            n=HurdleNet();n.load_state_dict({k:torch.tensor(v,dtype=torch.float32) for k,v in weights.items()});n.eval();m.networks.append(n)
        return m


class Admission:
    def __init__(self,p):self.p=p;self.records=[]
    def predict(self,x):
        p=self.p;warning=x[0]>.5;peerwarn=x[4]>.5
        safe=not(not warning and peerwarn and x[12]<.5)
        chosen=safe;mu=std=harm_accept=harm_reject=0.;rule='safe_fallback'
        if p.method=='ALL':chosen=True;rule='all'
        elif p.method=='KEEP':chosen=not(not warning and peerwarn);rule='keep_warning'
        elif p.method=='AGE':
            chosen=x[1]>=p.confidence and (not(not warning and peerwarn) or x[6]*8>=p.age_limit or x[12]>.5);rule='age_rule'
        elif p.method=='LEARN' and p.base_model is not None and x[13]>.5:
            mu,std,harm_accept,harm_reject=p.base_model.predict(x)
            proposed=mu>0
            gain=(mu if proposed else -mu)-.5*std
            risk=harm_accept if proposed else harm_reject
            used=p.state(p._cv).get('recovery_overrides',0)
            authority=not(p.reject_only and proposed and not safe)
            if proposed!=safe and authority and gain>p.margin and risk<=p.risk_limit and used<2:
                chosen=proposed;rule='learned_override'
        key=(p._cv.id,float(p._t),p._packet_id)
        forced=p.force.get(key)
        if forced is not None:chosen=bool(forced);p.force_hits+=1;rule='forced_intervention'
        if chosen!=safe and p.method=='LEARN':p.state(p._cv)['recovery_overrides']=p.state(p._cv).get('recovery_overrides',0)+1
        self.records.append(dict(mu=mu,std=std,harm_accept=harm_accept,harm_reject=harm_reject,fallback=safe,chosen=chosen,rule=rule,features=list(x)))
        return (1. if chosen else -1.),0.


@dataclass
class RecoveryPolicy(ResearchPolicy):
    method:str='SAFE'
    base_model:object=None
    risk_limit:float=.15
    margin:float=.25
    age_limit:float=4.
    confidence:float=.6
    reject_only:bool=False
    collect:bool=False
    force:object=None

    def __post_init__(self):
        self.mode='value';self.value_threshold=0.;super().__post_init__();self.force=dict(self.force or {});self.force_hits=0;self.candidates=[]
        if self.method not in METHODS:raise ValueError(self.method)

    def features(self,sim,cv,m,t):
        g=sim.g;e=m['e'];ttl=sim.cfg.tau_stale;before=self.merged(cv,cv.peer,t,ttl)
        peer=cv.peer.get(e);own=cv.own.get(e);prior=before.get(e)
        records=list(self.state(cv)['feedback'].values());since=peer[1] if peer and peer[0] else -1e9
        clear={r['sender'] for r in records if r['e']==e and not r['blocked'] and r['t_obs']>=since and 0<=t-r['t_obs']<=ttl}
        warn={r['sender'] for r in records if r['e']==e and r['blocked'] and 0<=t-r['t_obs']<=ttl}
        banned=self.banned(before,t,ttl);key=tuple(sorted(banned))
        if key not in self._routes:
            w=self.response_weights(self.w(g),banned);path=dijkstra(g,cv.node,cv.target,w) or []
            self._routes[key]=(w,path)
        w,path=self._routes[key]
        proposed=dict(cv.peer);proposed[e]=(bool(m['blocked']),m['t_obs'],m['conf'])
        after=self.merged(cv,proposed,t,ttl);afterkey=tuple(sorted(self.banned(after,t,ttl)))
        if afterkey not in self._routes:
            aw=self.response_weights(self.w(g),set(afterkey));ap=dijkstra(g,cv.node,cv.target,aw) or [];self._routes[afterkey]=(aw,ap)
        afterpath=self._routes[afterkey][1]
        alt=dijkstra(g,cv.node,cv.target,w,banned={e}) if e in path else None
        extra=(sum(w[i] for i in alt)-sum(w[i] for i in path)) if alt is not None else 0.
        later=[r for r in self._ordered[self._positions[m['id']]+1:] if r['e']==e and 0<=t-r['t_obs']<=ttl]
        lc={r['sender'] for r in later if not r['blocked']};lw={r['sender'] for r in later if r['blocked']}
        distance=self._dist[g.src[e]];peerwarn=bool(peer and peer[0]);blocked=bool(m['blocked'])
        x=[float(blocked),m['conf'],(t-m['t_obs'])/ttl,float(peer is not None),float(peerwarn),peer[2] if peer else 0.,(t-peer[1])/ttl if peer else 0.,
           float(own is not None),float(own is not None and own[0]),self.agreement(cv,m['sender']),min(len(clear),3)/3.,min(len(warn),3)/3.,float(len(clear)>=2),
           float(np.isfinite(distance)),float(e in path),float((path[0] if path else -1)!=(afterpath[0] if afterpath else -1)),min(distance,50.)/20.,extra/20.,
           min(sum(w[i] for i in path),100.)/40.,g.c[e]/5.,float(not blocked and peerwarn),float(prior is not None and bool(prior[0])!=blocked),float(cv.id>=2),t/40.,
           min(len(later),4)/4.,min(len(lc),3)/3.,min(len(lw),3)/3.,(t-max(r['t_obs'] for r in later))/ttl if later else 0.,float(g.src[e]==cv.node),len(afterpath)/20.]
        assert len(x)==len(FEATURES) and np.isfinite(x).all()
        self._packet_id=m['id'];return x

    def decide(self,sim,cv,t):
        self._cv=cv;self._t=t;self._routes={};self._dist=dists(sim.g,cv.node,sim.g.c)
        self._ordered=sorted(cv.inbox,key=lambda m:(m['t_obs'],m['id']));self._positions={m['id']:i for i,m in enumerate(self._ordered)}
        packets={m['id']:m for m in cv.inbox};adapter=Admission(self);self.value_model=adapter;start=len(sim.message_audit)
        try:edge=ResearchPolicy.decide(self,sim,cv,t)
        finally:self.value_model=None
        queried=iter(adapter.records)
        for record in sim.message_audit[start:]:
            if record['reason'] not in ['accepted','predicted_low_value']:continue
            q=next(queried);record.update(predicted_value=q['mu'],value_uncertainty=q['std'],admission_rule=q['rule'])
            if self.collect:
                m=packets[record['id']]
                self.candidates.append(dict(id=m['id'],convoy=cv.id,t=float(t),edge=m['e'],genuine=bool(m['genuine']),blocked_report=bool(m['blocked']),accepted=q['chosen'],fallback=q['fallback'],rule=q['rule'],predicted_value=q['mu'],value_uncertainty=q['std'],harm_accept=q['harm_accept'],harm_reject=q['harm_reject'],**dict(zip(FEATURES,q['features']))))
        assert next(queried,None) is None
        return edge


def policy(method,actor=None,model=None,**kwargs):
    return RecoveryPolicy(method,method=method,actor=actor,base_model=model,weights='threat',use_obs=True,response_strength=12.,relevance_scope='reachable',**kwargs)
