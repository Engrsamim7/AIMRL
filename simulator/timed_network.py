"""Timed, partially observed network development model.

This is an explicitly new network revision. Original experiments are immutable.
Closures prevent entry; encounters cost inspection time rather than destruction.
A finite shared broadcast channel serializes actual packets. The planning actor
uses only public topology, local observations and delivered timestamped reports.
This module does not label that actor as MARL or claim an optimal controller.
"""
from collections import deque
from bisect import bisect_right
from dataclasses import dataclass,field
import hashlib
import heapq
import math
import numpy as np
from ammarl2.graph import Graph,dijkstra,dists,make_graph
from ammarl2.reviewer import original_graph

METHODS=['NONE','RAW_ALL','FRC','AGE_ALL','LATEST','WARN_PRIORITY','VALUE']
AGE_BINS=np.array([0.,.25,.5,1.,2.,4.,8.,np.inf])
PHASE_BINS=np.array([0.,.25,.5,1.,2.,4.,np.inf])
CONF_BINS=np.array([0.,.8,.99,1.01])


def uniform(seed,tag,*items):
    digest=hashlib.sha256(repr((int(seed),int(tag),items)).encode()).digest()
    return int.from_bytes(digest[:8],'big')/2**64


def graph_for(seed,size):
    if size==19:
        g=original_graph();rng=np.random.default_rng([seed,401]);g.c=g.c*rng.uniform(.8,1.2,g.m)
        return g
    if size not in [51,131]:raise ValueError('Declared graph sizes:19,51,131')
    return make_graph(seed,layers=6 if size==51 else 16,width=8,n_targets=2)


def path(g,node,target,weights,banned=()):
    banned=set(banned)|{e for e in range(g.m) if int(g.dst[e]) in g.targets and int(g.dst[e])!=target}
    return dijkstra(g,node,target,weights,banned)


@dataclass(frozen=True)
class Scenario:
    name:str='transient'
    closure_fraction:float=.2
    duration:float=1.
    coverage:float=.25
    delay:float=.5
    detection_delay:float=0.
    loss:float=0.
    accuracy_scale:float=1.
    deadline_ratio:float=1.75
    inspection:float=1.
    packet_time:float=.25
    late_onset:bool=False
    n_convoys:int=8
    scout_lead:float=2.
    hub_service:float=.2
    hub_capacity:int=2
    perfect_sensors:bool=False

    def validate(self):
        if not 0<=self.closure_fraction<=1 or not 0<=self.coverage<=1 or not 0<=self.loss<=1:raise ValueError('Invalid probability')
        if min(self.delay,self.detection_delay,self.inspection,self.packet_time,self.scout_lead,self.hub_service)<0:raise ValueError('Negative duration')
        if self.duration<=0 or self.deadline_ratio<=1 or self.n_convoys<1 or self.hub_capacity<1 or not 0<self.accuracy_scale<=1:raise ValueError('Invalid scenario')


class Schedule:
    """Complete immutable exogenous closure schedule, independently of policies.

    Exactly round(fraction*m) unique edges are interdicted at most once each.
    Half begin at time zero; others begin within half a free-flow mission time.
    Persistent/late controls change onset/duration without increasing budget.
    """
    def __init__(self,g,case,seed,reference):
        case.validate();self.intervals={};rng=np.random.default_rng([seed,803])
        budget=int(round(case.closure_fraction*g.m))
        edges=rng.choice(g.m,size=budget,replace=False)
        for i,e in enumerate(edges):
            start=(reference*1.5+rng.uniform(0,reference*.5)) if case.late_onset else (0. if i%2==0 else float(rng.uniform(0,reference*.5)))
            duration=case.duration*reference
            self.intervals[int(e)]=(start,start+duration)
        self.digest=hashlib.sha256(repr(sorted(self.intervals.items())).encode()).hexdigest()
    def closed(self,e,t):
        interval=self.intervals.get(int(e))
        return interval is not None and interval[0]<=t<interval[1]


class Calibration:
    """Training-only empirical report validity with hierarchical backoff.

    Counts condition on public elapsed age/typical edge cost, mission phase,
    claimed-confidence bin and reported state. True closure labels are used only
    offline. Counts are not Bayesian safety guarantees or a causal value model.
    """
    def __init__(self):
        self.count=np.zeros((2,7,6,3));self.success=np.zeros_like(self.count)
        self.prior_count=np.zeros(6);self.prior_success=np.zeros(6)
    @staticmethod
    def indices(blocked,age,phase,confidence):
        return (int(blocked),max(0,min(6,bisect_right(AGE_BINS,age)-1)),
            max(0,min(5,bisect_right(PHASE_BINS,phase)-1)),
            max(0,min(2,bisect_right(CONF_BINS,confidence)-1)))
    def add(self,blocked,age,phase,confidence,truth):
        k=self.indices(blocked,age,phase,confidence);self.count[k]+=1;self.success[k]+=truth
    def prior(self,phase):
        k=self.indices(0,0,phase,.75)[2]
        return float((self.prior_success[k]+1)/(self.prior_count[k]+2))
    def probability(self,blocked,age,phase,confidence,age_aware=True):
        b,a,p,c=self.indices(blocked,max(0.,age) if age_aware else 0.,phase,confidence)
        n=self.count[b,a,p,c];s=self.success[b,a,p,c]
        if n<12:n=self.count[b,a,:,c].sum();s=self.success[b,a,:,c].sum()
        if n<12:n=self.count[b,a].sum();s=self.success[b,a].sum()
        if n<12:n=self.count[b,:,:,c].sum();s=self.success[b,:,:,c].sum()
        return float((s+1)/(n+2)) if n else self.prior(phase)
    def state(self):return {k:getattr(self,k).tolist() for k in ['count','success','prior_count','prior_success']}
    @classmethod
    def load(cls,state):
        model=cls()
        for k,v in state.items():setattr(model,k,np.array(v,float))
        return model


@dataclass
class Unit:
    cid:int
    target:int
    depart:float
    deadline:float
    node:int=0
    status:str='pending'
    own:dict=field(default_factory=dict)
    peer:dict=field(default_factory=dict)
    advertised:dict=field(default_factory=dict)
    own_emitted:dict=field(default_factory=dict)
    path:list=field(default_factory=list)
    nominal:float=0.
    travel:float=0.
    service:float=0.
    wait:float=0.
    inspection:float=0.
    hold:float=0.
    finish:float=math.nan
    entered:float=0.
    current_edge:int=-1
    segment_start:float=0.
    queue_start:float=0.
    encounters:int=0


class TimedNetwork:
    def __init__(self,g,case,method,seed,calibration,value_threshold=.05,record=False):
        if method not in METHODS+['ORACLE']:raise ValueError(method)
        case.validate();self.g=g;self.case=case;self.method=method;self.seed=seed;self.model=calibration;self.value_threshold=value_threshold;self.record=record
        self.scale=float(np.median(g.c));rng=np.random.default_rng([seed,701])
        targets=[int(g.targets[i%len(g.targets)]) for i in range(case.n_convoys)]
        lower={target:sum(g.c[e]+case.hub_service for e in path(g,g.depot,target,g.c+case.hub_service)) for target in g.targets}
        self.reference=float(np.median(list(lower.values())))
        self.horizon=(case.n_convoys*.15*self.scale+case.scout_lead*self.scale+4*self.reference)
        self.units=[]
        for i,target in enumerate(targets):
            depart=(0. if i==0 else case.scout_lead*self.scale+(i-1)*.15*self.scale)
            self.units.append(Unit(i,target,depart,depart+case.deadline_ratio*lower[target],node=g.depot))
        self.schedule=Schedule(g,case,seed,self.reference)
        self.flow=np.zeros(g.m,int);self.busy=np.zeros(g.n,int);self.queues=[deque() for _ in range(g.n)]
        self.events=[];self.sequence=0;self.t=0.;self.radio_busy=False;self.radio=[];self.packet_sequence=0
        self.stats=dict(observations=0,generated=0,transmitted=0,coalesced=0,value_rejected=0,lost=0,delivered_packets=0,radio_queue_delay=0.,routing_calls=0,peer_action_changes=0,peer_available_calls=0,blocked_options=0,blocked_attempts=0,report_brier_sum=0.,report_brier_n=0)
        self.decisions=[];self.packets=[];self.observations=[];self.distance_cache={};self.movements=[]
        # Public manifest and topology only; no live remote convoy positions.
        self.reference_paths={target:path(g,g.depot,target,g.c) for target in g.targets}
        demand=np.zeros(g.m);detour=np.zeros(g.m)
        for target in targets:
            route=self.reference_paths[target];base=sum(g.c[e] for e in route)
            for e in route:
                alternative=path(g,g.depot,target,g.c,[e]);extra=sum(g.c[a] for a in alternative)-base if alternative is not None else self.reference
                demand[e]+=1/len(targets);detour[e]+=max(0.,min(extra,self.reference))/len(targets)
        self.public_demand=demand;self.public_detour=detour
    def push(self,t,typ,payload):
        if t<=self.horizon:self.sequence+=1;heapq.heappush(self.events,(float(t),self.sequence,typ,payload))
    def observation_edges(self,u):
        frontier={u.node};seen={u.node};edges=[]
        for _ in range(2 if u.cid==0 else 1):
            new=set()
            for node in frontier:
                for e in self.g.out[node]:
                    if u.cid==0 or uniform(self.seed,812,u.cid,int(e))<self.case.coverage:edges.append(int(e))
                    new.add(int(self.g.dst[e]))
            frontier=new-seen;seen|=new
        return sorted(set(edges))
    def distance(self,node):
        if node not in self.distance_cache:self.distance_cache[node]=dists(self.g,node,self.g.c)
        return self.distance_cache[node]
    def observe(self,u):
        claimed=1. if self.case.perfect_sensors or u.cid==0 else .85
        actual_accuracy=max(.5,claimed*self.case.accuracy_scale)
        timestamp=max(0.,self.t-self.case.detection_delay*self.scale)
        for e in self.observation_edges(u):
            truth=self.schedule.closed(e,timestamp)
            blocked=truth if uniform(self.seed,813,u.cid,e,float(timestamp).hex())<actual_accuracy else not truth
            previous=u.own.get(e)
            if previous is not None and previous[1]>=timestamp and previous[2]>claimed:continue
            u.own[e]=(bool(blocked),timestamp,claimed)
            self.stats['observations']+=1
            if self.record:self.observations.append(dict(convoy=u.cid,t=self.t,edge=e,t_obs=timestamp,blocked=int(blocked),truth_at_observation=int(truth),claimed_confidence=claimed))
            emitted=u.own_emitted.get(e)
            if self.method not in ['NONE','ORACLE'] and (emitted is None or blocked!=emitted[0] or timestamp-emitted[1]>=2*self.scale):
                self.offer(u,e,bool(blocked),timestamp,claimed);u.own_emitted[e]=(bool(blocked),timestamp)
    def offer(self,u,e,blocked,t_obs,confidence):
        self.stats['generated']+=1;self.packet_sequence+=1
        packet=dict(id=hashlib.sha256(repr((self.seed,u.cid,e,self.packet_sequence)).encode()).hexdigest()[:24],sender=u.cid,edge=int(e),blocked=bool(blocked),t_obs=float(t_obs),confidence=float(confidence),offered=self.t,number=self.packet_sequence)
        old=u.advertised.get(e)
        phase=(self.t+self.case.delay*self.scale)/self.reference
        age=(self.t+self.case.delay*self.scale-t_obs)/self.scale
        newp=self.model.probability(blocked,age,phase,confidence)
        oldp=self.model.probability(old[0],(self.t+self.case.delay*self.scale-old[1])/self.scale,phase,old[2]) if old else self.model.prior(phase)
        # Public route deletion cost and calibrated change in closure probability.
        # This is a heuristic value estimate, not learned counterfactual return.
        score=abs(newp-oldp)*(self.public_detour[e]/self.scale+self.public_demand[e]*self.case.inspection)
        packet['score']=float(score)
        if self.method=='VALUE' and score<self.value_threshold:
            self.stats['value_rejected']+=1;return
        if self.method in ['LATEST','WARN_PRIORITY','VALUE']:
            old_queue=len(self.radio);self.radio=[p for p in self.radio if not(p['sender']==u.cid and p['edge']==e)]
            self.stats['coalesced']+=old_queue-len(self.radio)
        self.radio.append(packet);self.start_radio()
    def start_radio(self):
        if self.radio_busy or not self.radio:return
        if self.method=='WARN_PRIORITY':key=lambda p:(-int(p['blocked']),-self.public_demand[p['edge']],p['number'])
        elif self.method=='VALUE':key=lambda p:(-p['score'],p['number'])
        else:key=lambda p:(p['number'],)
        packet=min(self.radio,key=key);self.radio.remove(packet);self.radio_busy=True
        packet['tx_start']=self.t
        self.stats['radio_queue_delay']+=self.t-packet['offered']
        self.push(self.t+self.case.packet_time*self.scale,'TX_END',packet)
    def finish_radio(self,packet):
        self.radio_busy=False;self.stats['transmitted']+=1
        packet=dict(packet,tx_end=self.t)
        u=self.units[packet['sender']];u.advertised[packet['edge']]=(packet['blocked'],packet['t_obs'],packet['confidence'])
        if self.record:self.packets.append(packet)
        for receiver in self.units:
            if receiver.cid==packet['sender']:continue
            if uniform(self.seed,814,packet['id'],receiver.cid)<self.case.loss:self.stats['lost']+=1
            else:self.push(self.t+self.case.delay*self.scale,'MESSAGE',(receiver.cid,packet))
        self.start_radio()
    def beliefs(self,u,own_only=False):
        merged=dict(u.own)
        if not own_only and self.method not in ['NONE','ORACLE']:
            for e,r in u.peer.items():
                if e in merged and merged[e][1]>=r[1]:continue
                if self.method=='FRC' and (self.t-r[1]>3.2 or r[2]<.6):continue
                merged[e]=r
        return merged
    def choose(self,u,own_only=False):
        g=self.g
        if self.method=='ORACLE':
            banned=[e for e in g.out[u.node] if self.schedule.closed(e,self.t)]
            weights=g.c.copy()+self.case.hub_service
            for e in range(g.m):
                if self.schedule.closed(e,self.t):weights[e]+=self.case.inspection*g.c[e]
            p=path(g,u.node,u.target,weights,banned)
            return (p[0] if p else None),[],0.
        merged=self.beliefs(u,own_only);prior=self.model.prior(self.t/self.reference)
        weights=g.c.copy()+self.case.hub_service+prior*self.case.inspection*g.c
        local=set(self.observation_edges(u))
        for e in local:weights[e]+=g.c[e]*.2*self.flow[e]/max(g.q[e],1)
        at=self.distance(u.node)
        available=[];banned=[]
        for e,(blocked,ts,conf) in merged.items():
            if ts>self.t or not math.isfinite(at[int(g.src[e])]):continue
            future=float(at[int(g.src[e])]);phase=(self.t+future)/self.reference
            probability=self.model.probability(blocked,(self.t+future-ts)/self.scale,phase,conf,age_aware=self.method not in ['RAW_ALL','FRC'])
            if e in u.own and ts==u.own[e][1] and conf>=1. and self.t==ts and future==0.:probability=float(blocked)
            weights[e]+=(probability-prior)*self.case.inspection*g.c[e]
            if e in g.out[u.node] and e in u.own and u.own[e][2]>=1 and u.own[e][0] and self.t-u.own[e][1]<.5*self.scale:banned.append(e)
            if e in u.peer and ts==u.peer[e][1] and e not in banned:available.append((e,probability))
        p=path(g,u.node,u.target,weights,banned)
        return (p[0] if p else None),available,prior
    def request_service(self,u):
        if self.busy[u.node]<self.case.hub_capacity:
            self.busy[u.node]+=1;u.status='service';u.segment_start=self.t
            self.push(self.t+self.case.hub_service,'SERVICE_END',u.cid)
        else:u.status='queue';u.queue_start=self.t;self.queues[u.node].append(u.cid)
    def release(self,node):
        self.busy[node]-=1
        if self.queues[node]:
            u=self.units[self.queues[node].popleft()];u.wait+=self.t-u.queue_start;self.request_service(u)
    def decide(self,u):
        if u.status=='done':return
        self.observe(u);edge,reports,_=self.choose(u);own_edge,_,_=self.choose(u,own_only=True)
        self.stats['routing_calls']+=1;self.stats['peer_available_calls']+=bool(reports);self.stats['peer_action_changes']+=edge!=own_edge
        blocked_options=sum(self.schedule.closed(e,self.t) for e in self.g.out[u.node]);self.stats['blocked_options']+=blocked_options
        if self.record:
            self.decisions.append(dict(convoy=u.cid,t=self.t,node=u.node,edge=edge,own_only_edge=own_edge,peer_action_change=int(edge!=own_edge),blocked_options=blocked_options,peer_reports=len(reports),remaining_deadline=u.deadline-self.t))
        # Evaluator labels do not enter choose()/actor features.
        for e,prob in reports:self.stats['report_brier_sum']+=(prob-float(self.schedule.closed(e,self.t+float(self.distance(u.node)[int(self.g.src[e])]))))**2;self.stats['report_brier_n']+=1
        if edge is None:
            u.status='hold';u.segment_start=self.t;self.push(self.t+.5*self.scale,'HOLD_END',u.cid);return
        if self.schedule.closed(edge,self.t):
            u.encounters+=1;self.stats['blocked_attempts']+=1
            u.own[edge]=(True,self.t,1.);u.status='inspection';u.segment_start=self.t
            if self.method not in ['NONE','ORACLE']:self.offer(u,edge,True,self.t,1.)
            # Even zero inspection delay must permit time progress in a dead end.
            self.push(self.t+self.case.inspection*self.g.c[edge],'INSPECT_END',u.cid);return
        if self.record:self.movements.append(dict(convoy=u.cid,edge=edge,t=self.t))
        u.status='travel';u.current_edge=edge;u.entered=self.t
        duration=self.g.c[edge]*(1+.2*self.flow[edge]/max(self.g.q[edge],1));self.flow[edge]+=1
        self.push(self.t+duration,'ARRIVE',u.cid)
    def run(self):
        for u in self.units:self.push(u.depart,'START',u.cid)
        while self.events:
            self.t,_,kind,payload=heapq.heappop(self.events)
            if kind=='TX_END':self.finish_radio(payload);continue
            if kind=='MESSAGE':
                cid,p=payload;u=self.units[cid];old=u.peer.get(p['edge']);self.stats['delivered_packets']+=1
                if old is None or p['t_obs']>old[1]:u.peer[p['edge']]=(p['blocked'],p['t_obs'],p['confidence'])
                continue
            u=self.units[payload]
            if kind=='START':self.request_service(u)
            elif kind=='SERVICE_END':
                u.service+=self.t-u.segment_start;self.release(u.node);self.decide(u)
            elif kind=='ARRIVE':
                e=u.current_edge;self.flow[e]-=1;u.travel+=self.t-u.entered;u.nominal+=self.g.c[e];u.path.append(int(e));u.node=int(self.g.dst[e]);u.current_edge=-1
                if u.node==u.target:u.finish=self.t;u.status='done'
                else:self.request_service(u)
            elif kind=='INSPECT_END':u.inspection+=self.t-u.segment_start;self.decide(u)
            elif kind=='HOLD_END':u.hold+=self.t-u.segment_start;self.decide(u)
            if all(x.status=='done' for x in self.units):break
        self.t=self.horizon
        rows=[]
        for u in self.units:
            end=u.finish if u.status=='done' else self.horizon
            if u.status=='travel':u.travel+=end-u.entered
            elif u.status=='service':u.service+=end-u.segment_start
            elif u.status=='inspection':u.inspection+=end-u.segment_start
            elif u.status=='hold':u.hold+=end-u.segment_start
            elif u.status=='queue':u.wait+=end-u.queue_start
            elapsed=end-u.depart
            assert abs(elapsed-u.travel-u.service-u.wait-u.inspection-u.hold)<1e-7,(u.cid,elapsed,u)
            rows.append(dict(convoy=u.cid,target=u.target,depart=u.depart,deadline=u.deadline,delivered=int(u.status=='done'),on_time=int(u.status=='done' and end<=u.deadline),censored=int(u.status!='done'),elapsed=elapsed,travel=u.travel,service=u.service,wait=u.wait,inspection=u.inspection,hold=u.hold,nominal=u.nominal,encounters=u.encounters,path=repr(u.path)))
        return dict(delivery=np.mean([r['delivered'] for r in rows]),on_time=np.mean([r['on_time'] for r in rows]),elapsed=np.mean([r['elapsed'] for r in rows]),nominal=np.mean([r['nominal'] for r in rows]),encounters=sum(r['encounters'] for r in rows),tx_bytes=64*self.stats['transmitted'],**self.stats),rows
