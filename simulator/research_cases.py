"""Declared physical scout/follower cases, with random fresh layouts and tapes."""
from dataclasses import dataclass
import hashlib
import numpy as np
from ammarl2.graph import Graph
from ammarl2.reviewer import ReviewerSim, Sensing, m4_sensing
from ammarl2.sim import Cfg, MSG, UNBLOCK

@dataclass(frozen=True)
class Case:
    name:str
    lead:float=4.
    delay:float=1.
    loss:float=0.
    spoof:float=0.
    full_sensing:bool=False
    short_lived:bool=False
    no_hazards:bool=False
    impersonation:float=.25

CASES=[Case('timely-honest'),Case('timely-misleading',loss=.1,spoof=.8),
       Case('delayed-misleading',delay=4.,loss=.2,spoof=.8),
       Case('late-warning',lead=0.,delay=8.,spoof=.8),
       Case('redundant-sensing',spoof=.8,full_sensing=True),
       Case('short-lived-honest',short_lived=True),
       Case('short-lived-misleading',short_lived=True,spoof=.8),
       Case('multiple-impersonation',spoof=2.,impersonation=.9),
       Case('no-hazards',spoof=.8,no_hazards=True)]

def fork_graph(seed, stages=2):
    rng=np.random.default_rng(seed);edges=[];hazards=[];approach=0;next_node=1
    for stage in range(stages):
        fork=next_node;branches=list(range(next_node+1,next_node+4));next_approach=next_node+4;next_node+=5
        edges.append((approach,fork,rng.uniform(1.5,2.5),.08))
        for k,node in enumerate(branches):
            if k<2:hazards.append(len(edges))
            edges.append((fork,node,rng.uniform(.9,1.8) if k<2 else rng.uniform(2.8,4.5),.15 if k<2 else .05))
            edges.append((node,next_approach,rng.uniform(.6,1.2),.08))
        approach=next_approach
    src=np.array([e[0] for e in edges]);dst=np.array([e[1] for e in edges]);out=[[] for _ in range(next_node)]
    for e,u in enumerate(src):out[u].append(e)
    g=Graph(next_node,0,[approach],src,dst,np.array([e[2] for e in edges]),np.array([e[3] for e in edges]),np.full(len(edges),4.),np.arange(len(edges)),out)
    return g,tuple(hazards)

class ResearchSim(ReviewerSim):
    def __init__(self,g,cfg,policy,seed,sensing,case,preblocked=()):
        super().__init__(g,cfg,policy,seed,sensing)
        self.case=case
        target=int(self.cv[0].target)
        for cv in self.cv:
            cv.target=target
            cv.depart_t=(0. if cv.id<2 else case.lead)+cv.depart_t%1.
        rng=np.random.default_rng(np.random.SeedSequence([seed,7148]))
        if preblocked and not case.no_hazards:
            for i in range(0,len(preblocked),2):
                e=int(rng.choice(preblocked[i:i+2]))
                duration=float(rng.uniform(2.2,3.) if case.short_lived else rng.uniform(35.,50.))
                self.active[e]=(0.,duration);self.attack_log.append((0.,e))
                self.stats['attacks']+=1;self.push(duration,UNBLOCK,e)

    def do_spoof(self,t):
        first=self.event_seq
        super().do_spoof(t)
        rng=np.random.default_rng(np.random.SeedSequence([self.seed,9912,self.spoof_seq]))
        for at,seq,typ,payload in self.ev:
            if typ!=MSG or seq<first:continue
            cid,packet=payload;clear=rng.random()<.65
            choices=sorted(self.active) if clear else [e for e in range(self.g.m) if e not in self.active]
            if choices:packet['e']=int(rng.choice(choices))
            packet['blocked']=not clear
            packet['conf']=float(np.clip(rng.normal(.85,.1),.05,1.))
            packet['sender']=int(rng.integers(self.cfg.n_convoys)) if rng.random()<self.case.impersonation else -1
            # Opaque identifiers prevent origins from becoming predictive features.
            packet['id']=hashlib.sha256(f'{self.seed}:{self.spoof_seq}:{seq}:{cid}'.encode()).hexdigest()[:24]

    @staticmethod
    def message_id(sender,receiver,edge,t,blocked):
        raw=f'{sender}:{receiver}:{edge}:{float(t).hex()}:{int(blocked)}'
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

def factory(g,hazards,case,policy,seed,bridge=False):
    cfg=Cfg(n_convoys=5,stagger=0.,hub_cap=2,hub_service=.4,tau_reveal=5. if bridge else 0.,
            tau_msg=case.delay,p_loss=case.loss,spoof_rate=case.spoof,conf_mu=.85,conf_sd=.1,
            p_kill=.8,horizon=200.,congestion_factor=.15,allow_base_transit=True,
            attack_rate=.5 if bridge and not case.no_hazards else 0.,budget=5 if bridge else 0,
            attack_dur=(15.,30.))
    if bridge:
        base=m4_sensing(g,not case.full_sensing)
        sensing=Sensing((0,1),2,base.follower_blind_edges)
    else:sensing=Sensing((0,1),2,() if case.full_sensing else hazards)
    return ResearchSim(g,cfg,policy,seed,sensing,case,preblocked=hazards)
