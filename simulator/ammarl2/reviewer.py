"""Original graph adapter and declared heterogeneous sensing, without legacy imports."""
import json
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np
from .graph import Graph
from .sim import Sim, Cfg
from .policies import Policy

NETWORK = Path(__file__).resolve().parents[2]/'revision/submission-code-audit/original_network_seed42.json'

def original_graph(path=NETWORK):
    data=json.loads(Path(path).read_text());edges=data['edges'];nodes=data['nodes']
    if sorted(n['id'] for n in nodes)!=list(range(len(nodes))):
        raise ValueError('Original graph requires contiguous node IDs')
    src=np.array([e['source'] for e in edges]);dst=np.array([e['target'] for e in edges]);out=[[] for _ in nodes]
    for e,u in enumerate(src):out[int(u)].append(e)
    return Graph(len(nodes),data['metadata']['depot'],data['metadata']['targets'],src,dst,
                 np.array([e['travel_cost'] for e in edges],dtype=float),
                 np.array([e['threat_level'] for e in edges],dtype=float),
                 np.array([e['capacity'] for e in edges],dtype=float),
                 np.array([e['corridor'] for e in edges]),out)

@dataclass(frozen=True)
class Sensing:
    scout_slots: tuple = (0,)
    scout_radius: int = 2
    follower_blind_edges: tuple = ()
    # Declared extra observation links for a controlled scout fixture, not ordinary M4.
    scout_extra: dict = field(default_factory=dict)

class ReviewerSim(Sim):
    def __init__(self,g,cfg,policy,seed,sensing=None):
        super().__init__(g,cfg,policy,seed)
        self.sensing=sensing or Sensing(scout_slots=(),scout_radius=cfg.obs_radius)

    def observation_edges(self,cv):
        radius=self.sensing.scout_radius if cv.id in self.sensing.scout_slots else self.cfg.obs_radius
        seen={cv.node};front=[cv.node];edges=[]
        for _ in range(radius):
            new=[]
            for node in front:
                for e in self.g.out[node]:
                    edges.append(e);v=int(self.g.dst[e])
                    if v not in seen:seen.add(v);new.append(v)
            front=new
        if cv.id in self.sensing.scout_slots:
            edges+=list(self.sensing.scout_extra.get(cv.node,()))
        else:
            edges=[e for e in edges if e not in self.sensing.follower_blind_edges]
        return sorted(set(edges))

    def summary(self):
        result=super().summary()
        result['sensing']=__import__('dataclasses').asdict(self.sensing)
        return result


def m4_sensing(g,mixed):
    # Coverage gaps are fixed by topology, independently of attacks and algorithms.
    blind=tuple(e for e in range(g.m) if (int(g.src[e])*17+int(g.dst[e])*31)%5==0) if mixed else ()
    return Sensing((0,) if mixed else (),2,blind)


def cc2_graph(hot=4):
    """Explicit communication-critical fixture with actual binary interdiction.

    Followers cannot sense the fork corridors; the scout has declared observation
    links at node 3. All public priors are independent of the episode's hot branch.
    """
    edges=[(0,3,1.),(3,2,2.),(0,1,1.5),(1,2,1.5),
           (2,4,3.),(4,7,1.),(2,5,3.),(5,7,1.),(2,6,3.5),(6,7,2.)]
    src=np.array([e[0] for e in edges]);dst=np.array([e[1] for e in edges]);out=[[] for _ in range(8)]
    for e,u in enumerate(src):out[int(u)].append(e)
    g=Graph(8,0,[7],src,dst,np.array([e[2] for e in edges]),np.full(10,.15),np.full(10,10.),np.arange(10),out)
    risky=(4,6);sensing=Sensing((0,),1,risky,{3:risky})
    return g,sensing,4 if hot==4 else 6

@dataclass
class ScoutFixturePolicy(Policy):
    def select(self,sim,cv,w,ban,merged,t):
        if cv.node==0:
            wanted=3 if cv.id==0 else 1
            return next(e for e in sim.g.out[0] if sim.g.dst[e]==wanted)
        return super().select(sim,cv,w,ban,merged,t)


def cc2_factory(g,cfg,policy,seed,hot=4,sensing=None):
    _,default,blocked=cc2_graph(hot)
    s=ReviewerSim(g,cfg,policy,seed,sensing or default)
    for cv in s.cv:cv.target=7;cv.depart_t=0.
    s.active[blocked]=(0.,50.)
    # Fixed exogenous block, documented in traces, lasts beyond completion.
    s.attack_log.append((0.,blocked,50.))
    return s
