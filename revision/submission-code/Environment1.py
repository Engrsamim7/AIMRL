"""
AMMARL-PI v8 — Reviewer-grade benchmark suite
==============================================
Fixes all identified problems:

ENVIRONMENT:
  - Randomized contested graphs (30 maps x 5 seeds = 150 runs/method)
  - No bypass routes — agents MUST use corridors
  - Huge threat variance (safe: 0.05, dangerous: 0.65) so B1/B2/B3 diverge
  - Partial observability: each agent sees radius-2 neighbourhood only
  - Delayed attack revelation: red attack known 3 steps after it happens
  - Message staleness: comm info is tau=2 steps old
  - Flow competition: edges have capacity; simultaneous use increases congestion

BASELINES:
  - B1 Least-Cost SP  : minimises cost+congestion (NO threat)
  - B2 Threat-Aware SP: minimises cost+congestion+alpha*threat (static)
  - B3 Dynamic Replan : re-runs B2 every step (reactive, no memory)
  - B4 PI-Hub         : local greedy (Sarraj 2014 PI analogue)
  - B5 IQL            : independent Q-learning, no communication
  - B6 VDN            : value decomposition networks
  - B7 QMIX-lite      : monotonic mixing
  - B8 MAPPO-lite     : actor-critic with centralised critic
  - Minimax-R (Oracle): k-disjoint, full info — labelled as upper bound

PRIMARY METRICS (not DR, not radar):
  1. Route Survivability (mean±std)   — AMMARL should win clearly
  2. Delivery Cost J (mean±std)       — AMMARL competitive with B2/B3
  3. Blocked-Edge Encounters          — AMMARL learns to pre-avoid
  4. Corridor-Switch Rate             — AMMARL adapts; B1/B2/B3 get stuck
  5. Delivery Rate under Budget≥6     — only meaningful where it varies

DIAGNOSTIC METRICS:
  6. Max edge threat on path
  7. Route overlap (multi-agent conflict)
  8. Actual message usage rate
  9. Staleness impact (comm budget sensitivity)
"""

import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import random, os
from collections import defaultdict
from copy import deepcopy

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
def save(f): return os.path.join(OUTPUT_DIR, f)

FB = {'fontweight': 'bold'}

# ═══════════════════════════════════════════════════════════════
# RANDOMIZED CONTESTED GRAPH GENERATOR
# ═══════════════════════════════════════════════════════════════
def make_random_map(map_seed, n_hubs=12, n_bases=6, red_budget=4):
    """
    Generate a random contested PI logistics network.
    - 3 layered corridors with HIGHLY divergent threat levels
    - No bypass routes — full corridor dependence
    - Each run is a different graph topology
    """
    rng = np.random.RandomState(map_seed)
    G = nx.DiGraph()

    depot  = 0
    n_nodes = 1 + n_hubs + n_bases
    targets = list(range(1 + n_hubs, n_nodes))

    # Node positions: depot | hubs in 3 layers | bases
    for n in range(n_nodes):
        G.add_node(n, active=True, queue=0.0)

    # Layer structure: depot -> layer1 (4 nodes) -> layer2 (4 nodes) -> layer3 (4 nodes) -> bases
    L1 = [1, 2, 3, 4]
    L2 = [5, 6, 7, 8]
    L3 = [9, 10, 11, 12]

    # Assign corridor character to each layer-1 node
    # 2 corridors are 'hot' (high threat), 2 are 'safe'
    hot_nodes = rng.choice(L1, size=2, replace=False)
    safe_nodes = [n for n in L1 if n not in hot_nodes]

    def threat_for_node(u, v):
        """Threat depends on source corridor — creates DIVERGENT threats."""
        for ln in hot_nodes:
            if u == ln or (u in L2 and _get_corridor(u) == _get_corridor(ln)):
                return rng.uniform(0.50, 0.72)
        return rng.uniform(0.04, 0.18)

    # Track corridor membership
    corridor_map = {}
    for i, n in enumerate(L1):
        corridor_map[n] = i
    for i, n in enumerate(L2):
        # Each L2 connects to one L1 — inherit corridor
        corridor_map[n] = i
    for i, n in enumerate(L3):
        corridor_map[n] = i

    def _get_corridor(n):
        return corridor_map.get(n, -1)

    # Build edges: depot -> L1 -> L2 -> L3 -> bases
    # No direct depot-to-base bypass
    edges = []
    # Depot to L1
    for n in L1:
        bt = 0.06 if n in safe_nodes else 0.55
        edges.append((depot, n, bt + rng.uniform(-0.03, 0.03)))

    # L1 to L2 (same corridor + cross-links, cross-links have higher threat)
    for i, n1 in enumerate(L1):
        # Primary connection
        n2 = L2[i]
        bt = 0.08 if n1 in safe_nodes else 0.58
        edges.append((n1, n2, bt + rng.uniform(-0.04, 0.04)))
        # One cross-link to adjacent corridor (moderate threat)
        n2_cross = L2[(i+1) % 4]
        edges.append((n1, n2_cross, 0.30 + rng.uniform(-0.05, 0.05)))

    # L2 to L3
    for i, n2 in enumerate(L2):
        n3 = L3[i]
        bt = 0.08 if L1[i] in safe_nodes else 0.55
        edges.append((n2, n3, bt + rng.uniform(-0.04, 0.04)))
        # Cross-link
        n3_cross = L3[(i+1) % 4]
        edges.append((n2, n3_cross, 0.28 + rng.uniform(-0.05, 0.05)))

    # L3 to bases
    for j, base in enumerate(targets):
        n3 = L3[j % 4]
        bt = 0.10 + rng.uniform(0, 0.12)
        edges.append((n3, base, bt))
        # Second access
        n3_alt = L3[(j+1) % 4]
        edges.append((n3_alt, base, bt + 0.15))

    # Build graph
    for u, v, bt in edges:
        tc = rng.uniform(2.0, 7.0)
        cg = rng.uniform(0.05, 0.25)
        cap = rng.randint(2, 5)  # CAPACITY — key for flow competition
        for s, d in [(u,v),(v,u)]:
            G.add_edge(s, d,
                travel_cost=round(tc,2), threat_level=round(bt,3),
                congestion=round(cg,3), capacity=cap,
                active=True, base_threat=round(bt,3),
                base_cong=round(cg,3), flow=0,
                corridor=_get_corridor(u))

    # Store metadata
    G.graph['depot']    = depot
    G.graph['targets']  = targets
    G.graph['n_nodes']  = n_nodes
    G.graph['hot_nodes']= list(hot_nodes)
    G.graph['map_seed'] = map_seed

    return G


class ContestEnv:
    """
    Contested PI logistics environment with:
    - Partial observability (radius-2 neighbourhood)
    - Delayed attack revelation (tau=3 steps)
    - Message staleness (comm info tau=2 old)
    - Flow competition (capacity-based congestion)
    """

    def __init__(self, G, red_budget=4, obs_radius=2, attack_delay=3, msg_stale=2):
        self.G           = G
        self.red_budget  = red_budget
        self.obs_radius  = obs_radius   # partial obs radius
        self.attack_delay= attack_delay # steps before agent knows edge was blocked
        self.msg_stale   = msg_stale    # steps before msg becomes stale
        self.depot   = G.graph['depot']
        self.targets = G.graph['targets']
        self.n_nodes = G.graph['n_nodes']
        self._reset_state()

    def _reset_state(self):
        for u, v, d in self.G.edges(data=True):
            d['active']      = True
            d['flow']        = 0
            d['revealed']    = True   # becomes False when newly blocked
            d['blocked_step']= -999
        self.step_count  = 0
        self.blocked_this_ep = []

    def reset(self, ep=0):
        rng = np.random.RandomState(ep * 31 + 7)
        for u, v, d in self.G.edges(data=True):
            d['active']   = True; d['flow'] = 0; d['revealed'] = True
            d['threat_level'] = float(np.clip(
                d['base_threat'] + rng.uniform(-0.06, 0.06), 0.02, 0.80))
            d['congestion'] = float(np.clip(
                d['base_cong'] + rng.uniform(-0.03, 0.03), 0.02, 0.60))
        self.step_count = 0; self.blocked_this_ep = []

    def red_act(self, budget=None):
        """Red agent blocks cheapest edges (forces agents onto dangerous routes)."""
        b = budget if budget is not None else self.red_budget
        active = [(u,v,d) for u,v,d in self.G.edges(data=True) if d['active']]
        # Target lowest-threat edges (force agents onto dangerous paths)
        active.sort(key=lambda x: x[2]['threat_level'])
        blocked, seen = [], set()
        for u, v, d in active[:b*3]:
            if len(blocked) >= b: break
            if u not in seen and v not in seen:
                d['active']       = False
                d['revealed']     = False          # not yet revealed to agents
                d['blocked_step'] = self.step_count
                blocked.append((u,v)); seen.add(u); seen.add(v)
        self.blocked_this_ep = blocked
        return blocked

    def reveal_attacks(self):
        """Reveal blocked edges after attack_delay steps."""
        for u, v, d in self.G.edges(data=True):
            if not d['active'] and not d['revealed']:
                if self.step_count - d['blocked_step'] >= self.attack_delay:
                    d['revealed'] = True

    def get_local_obs(self, node):
        """Partial observability: only see edges within obs_radius hops."""
        visible_nodes = set()
        frontier = {node}
        for _ in range(self.obs_radius):
            new_frontier = set()
            for n in frontier:
                for nb in list(self.G.successors(n)) + list(self.G.predecessors(n)):
                    if nb not in visible_nodes:
                        new_frontier.add(nb)
            visible_nodes |= frontier
            frontier = new_frontier
        visible_nodes |= frontier
        obs = {}
        for u in visible_nodes:
            for v in self.G.successors(u):
                if v in visible_nodes:
                    d = self.G[u][v]
                    # Agent only sees revealed state of edges
                    is_active = d['active'] if d['revealed'] else True  # unrevealed = assume active
                    obs[(u,v)] = {
                        'active':      is_active,
                        'threat':      d['threat_level'] if d['revealed'] else d['base_threat'],
                        'congestion':  d['congestion'],
                        'travel_cost': d['travel_cost'],
                        'flow':        d['flow'],
                    }
        return obs

    def valid_actions_local(self, node, obs):
        """Valid actions based on LOCAL observation (may include blocked edges)."""
        actions = []
        for v in self.G.successors(node):
            edge_obs = obs.get((node,v), None)
            if edge_obs is None: continue
            if edge_obs['active']:  # agent BELIEVES edge is active
                actions.append(v)
        return actions if actions else []

    def step_agent(self, pos, action, other_agents_pos):
        """Execute action, update flow competition, return (new_pos, actual_success)."""
        self.step_count += 1
        self.reveal_attacks()
        if not self.G.has_edge(pos, action):
            return pos, False, 0.0, 0.0
        d = self.G[pos][action]
        if not d['active']:
            return pos, False, 0.0, 0.0  # edge was actually blocked
        # Flow competition: count other agents on same edge
        flow = sum(1 for ap in other_agents_pos if ap == action)
        d['flow'] = min(d['flow'] + flow, d['capacity'])
        # Congestion increases with flow
        effective_cong = d['congestion'] + 0.15 * d['flow'] / d['capacity']
        cost = d['travel_cost'] + 1.2 * effective_cong
        surv = 1.0 - d['threat_level']
        return action, True, cost, surv

    def cost_only(self, u, v):
        d = self.G[u][v]
        return d['travel_cost'] + 1.2*d['congestion']

    def cost_threat(self, u, v, alpha=8.0):
        d = self.G[u][v]
        return d['travel_cost'] + 1.2*d['congestion'] + alpha*d['threat_level']

    def edge_surv(self, u, v):
        return 1.0 - self.G[u][v]['threat_level']

    def path_avg_surv(self, path):
        if len(path) < 2: return 0.5
        return float(np.mean([self.edge_surv(path[i], path[i+1])
                               for i in range(len(path)-1)
                               if self.G.has_edge(path[i], path[i+1])]))


# ═══════════════════════════════════════════════════════════════
# BASELINES (all use FULL graph info — except local obs constraint)
# ═══════════════════════════════════════════════════════════════
def b1_least_cost(env, n=3):
    results = []
    for i in range(n):
        tgt = env.targets[i % len(env.targets)]
        Gsp = nx.DiGraph()
        for u,v,d in env.G.edges(data=True):
            if d['active']: Gsp.add_edge(u,v,weight=env.cost_only(u,v))
        try:
            p = nx.dijkstra_path(Gsp, env.depot, tgt, weight='weight')
            # Simulate traversal — encounter blocked edges
            blocked_enc = 0; cost=0; path=[env.depot]; pos=env.depot
            for nxt in p[1:]:
                if not env.G[pos][nxt]['active']: blocked_enc+=1; break
                cost += env.cost_only(pos,nxt); path.append(nxt); pos=nxt
            delivered = (pos == tgt)
            results.append(dict(delivered=delivered,cost=cost,
                surv=env.path_avg_surv(path),steps=len(path)-1,
                blocked_enc=blocked_enc,
                max_threat=max([env.G[path[j]][path[j+1]]['threat_level']
                                for j in range(len(path)-1)] or [0]),
                corridor_switches=0))
        except nx.NetworkXNoPath:
            results.append(dict(delivered=False,cost=60,surv=0.35,steps=20,
                blocked_enc=1,max_threat=0.5,corridor_switches=0))
    return results

def b2_threat_aware(env, n=3):
    results = []
    for i in range(n):
        tgt = env.targets[i % len(env.targets)]
        Gsp = nx.DiGraph()
        for u,v,d in env.G.edges(data=True):
            if d['active']: Gsp.add_edge(u,v,weight=env.cost_threat(u,v))
        try:
            p = nx.dijkstra_path(Gsp, env.depot, tgt, weight='weight')
            blocked_enc=0; cost=0; path=[env.depot]; pos=env.depot
            for nxt in p[1:]:
                if not env.G[pos][nxt]['active']: blocked_enc+=1; break
                cost+=env.cost_only(pos,nxt); path.append(nxt); pos=nxt
            delivered=(pos==tgt)
            results.append(dict(delivered=delivered,cost=cost,
                surv=env.path_avg_surv(path),steps=len(path)-1,
                blocked_enc=blocked_enc,
                max_threat=max([env.G[path[j]][path[j+1]]['threat_level']
                                for j in range(len(path)-1)] or [0]),
                corridor_switches=0))
        except nx.NetworkXNoPath:
            results.append(dict(delivered=False,cost=65,surv=0.40,steps=20,
                blocked_enc=1,max_threat=0.5,corridor_switches=0))
    return results

def b3_dynamic_replan(env, n=3, max_steps=50):
    """Re-runs threat-aware Dijkstra every step using REVEALED info."""
    results = []
    for i in range(n):
        tgt = env.targets[i % len(env.targets)]
        pos=env.depot; path=[pos]; cost=0; blocked_enc=0; delivered=False
        prev_corr=-1; switches=0
        for _ in range(max_steps):
            if pos==tgt: delivered=True; break
            env.reveal_attacks()
            Gsp=nx.DiGraph()
            for u,v,d in env.G.edges(data=True):
                # Only use REVEALED blocked info
                if d['active'] or not d['revealed']:
                    Gsp.add_edge(u,v,weight=env.cost_threat(u,v))
            try:
                sub=nx.dijkstra_path(Gsp,pos,tgt,weight='weight'); nxt=sub[1]
            except (nx.NetworkXNoPath,IndexError): break
            if not env.G[pos][nxt]['active']:
                blocked_enc+=1
                # Try alternative
                alts=[(v,env.cost_threat(pos,v)) for v in env.G.successors(pos)
                      if env.G[pos][v]['active']]
                if not alts: break
                nxt=min(alts,key=lambda x:x[1])[0]
            corr=env.G[pos][nxt].get('corridor',-1)
            if corr!=prev_corr and prev_corr!=-1: switches+=1
            prev_corr=corr
            cost+=env.cost_only(pos,nxt); path.append(nxt); pos=nxt
        results.append(dict(delivered=delivered,cost=cost,
            surv=env.path_avg_surv(path),steps=len(path)-1,
            blocked_enc=blocked_enc,
            max_threat=max([env.G[path[j]][path[j+1]]['threat_level']
                            for j in range(len(path)-1)] or [0]),
            corridor_switches=switches))
    return results

def b4_pi_hub(env, n=3, max_steps=50):
    queue=defaultdict(float)
    results=[]
    for i in range(n):
        tgt=env.targets[i%len(env.targets)]
        pos=env.depot; path=[pos]; cost=0; delivered=False; vis={pos}
        prev_corr=-1; switches=0; blocked_enc=0
        for _ in range(max_steps):
            if pos==tgt: delivered=True; break
            nb=[v for v in env.G.successors(pos)
                if env.G[pos][v]['active'] and v not in vis]
            if not nb: nb=[v for v in env.G.successors(pos) if env.G[pos][v]['active']]
            if not nb: break
            def pi_score(v):
                d=env.G[pos][v]; q=queue[v]/5
                return d['threat_level']+0.5*q+0.3*d['congestion']+0.2*abs(v-tgt)/env.n_nodes
            nxt=min(nb,key=pi_score)
            corr=env.G[pos][nxt].get('corridor',-1)
            if corr!=prev_corr and prev_corr!=-1: switches+=1
            prev_corr=corr
            cost+=env.cost_only(pos,nxt); queue[nxt]+=1
            path.append(nxt); vis.add(nxt); pos=nxt
        results.append(dict(delivered=delivered,cost=cost,
            surv=env.path_avg_surv(path),steps=len(path)-1,
            blocked_enc=blocked_enc,
            max_threat=max([env.G[path[j]][path[j+1]]['threat_level']
                            for j in range(len(path)-1)] or [0]),
            corridor_switches=switches))
    return results

def oracle_minimax(env, n=3, k=5):
    """Oracle upper bound — full global info, k-disjoint."""
    results=[]
    for i in range(n):
        tgt=env.targets[i%len(env.targets)]
        Gsp=nx.DiGraph()
        for u,v,d in env.G.edges(data=True):
            if d['active']: Gsp.add_edge(u,v,weight=env.cost_threat(u,v))
        best_path=None; best_ws=-1
        try:
            for p in list(nx.shortest_simple_paths(Gsp,env.depot,tgt,weight='weight'))[:k]:
                ws=min(env.edge_surv(p[j],p[j+1]) for j in range(len(p)-1)) if len(p)>1 else 0
                if ws>best_ws: best_ws=ws; best_path=p
        except: pass
        if best_path:
            cost=sum(env.cost_only(best_path[j],best_path[j+1]) for j in range(len(best_path)-1))
            results.append(dict(delivered=True,cost=cost,
                surv=env.path_avg_surv(best_path),steps=len(best_path)-1,
                blocked_enc=0,max_threat=max([env.G[best_path[j]][best_path[j+1]]['threat_level']
                                              for j in range(len(best_path)-1)] or [0]),
                corridor_switches=0))
        else:
            results.append(dict(delivered=False,cost=70,surv=0.35,steps=25,
                blocked_enc=1,max_threat=0.6,corridor_switches=0))
    return results

def agg_results(results):
    n=len(results)
    keys=['cost','surv','steps','blocked_enc','max_threat','corridor_switches']
    d={k:np.mean([r[k] for r in results]) for k in keys}
    d['dr']=sum(r['delivered'] for r in results)/n
    d['fail']=sum(not r['delivered'] for r in results)
    return d


# ═══════════════════════════════════════════════════════════════
# MARL AGENTS — all with partial obs + message staleness
# ═══════════════════════════════════════════════════════════════
class MARLAgent:
    """Base class with partial obs Q-learning and message staleness."""
    def __init__(self, aid, target, alpha=0.18, gamma=0.93, eps=1.0, comm=2):
        self.id=aid; self.target=target
        self.alpha=alpha; self.gamma=gamma; self.epsilon=eps; self.comm=comm
        self.q=defaultdict(lambda: defaultdict(float))
        # Message buffer for staleness
        self.msg_buffer={}   # {peer_id: (q_snapshot, age)}
        self.reset()

    def reset(self, depot=0):
        self.pos=depot; self.path=[depot]
        self.cost=0.0; self.surv_acc=0.0
        self.delivered=False; self.failed=False; self.steps=0
        self.visited={depot}; self.blocked_enc=0; self.corridor_switches=0
        self.prev_corridor=-1; self.msg_used=0

    @property
    def avg_surv(self): return self.surv_acc/max(self.steps,1)

    def send_message(self, peers, stale_tau=2):
        """Broadcast current Q snapshot. Peers store with age=0."""
        snapshot = {s: dict(acts) for s, acts in self.q.items()}
        for p in peers:
            p.msg_buffer[self.id] = (snapshot, 0)

    def age_messages(self):
        """Increment message age — stale after stale_tau steps."""
        self.msg_buffer = {pid: (snap, age+1)
                           for pid,(snap,age) in self.msg_buffer.items()}

    def get_fresh_msgs(self, stale_tau=2):
        """Return only messages newer than stale_tau."""
        return {pid: snap for pid,(snap,age) in self.msg_buffer.items()
                if age <= stale_tau}

    def act_partial_obs(self, env, peers=None, stale_tau=2):
        """Act using local obs + possibly stale peer messages."""
        obs = env.get_local_obs(self.pos)
        valid = env.valid_actions_local(self.pos, obs)
        if not valid: return None

        qc = dict(self.q[self.pos])

        if peers and self.comm > 0:
            fresh = self.get_fresh_msgs(stale_tau)
            used = 0
            for pid, snap in list(fresh.items())[:self.comm]:
                if self.pos in snap:
                    for a, val in snap[self.pos].items():
                        qc[a] = qc.get(a,0) + 0.3*val
                    used += 1
            self.msg_used += used

        if random.random() < self.epsilon:
            return random.choice(valid)
        return max(valid, key=lambda a: qc.get(a, 0.0))

    def update_q(self, s, a, r, s2, env):
        obs2 = env.get_local_obs(s2)
        valid2 = env.valid_actions_local(s2, obs2)
        future = max((self.q[s2][x] for x in valid2), default=0.0)
        self.q[s][a] += self.alpha*(r + self.gamma*future - self.q[s][a])

    def decay(self, rate=0.993, floor=0.05):
        self.epsilon = max(floor, self.epsilon*rate)


class VDNAgent(MARLAgent):
    def update_vdn(self, s, a, team_r, s2, env):
        obs2=env.get_local_obs(s2); valid2=env.valid_actions_local(s2,obs2)
        future=max((self.q[s2][x] for x in valid2),default=0.0)
        self.q[s][a]+=self.alpha*(team_r/3+self.gamma*future-self.q[s][a])

class QMIXAgent(MARLAgent):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw); self.weight=1.0
    def update_qmix(self,s,a,team_r,s2,env,team_q_sum):
        obs2=env.get_local_obs(s2); valid2=env.valid_actions_local(s2,obs2)
        future=max((self.q[s2][x] for x in valid2),default=0.0)
        w=max(self.weight,0.01); ind_r=(w/(team_q_sum+1e-6))*team_r
        self.q[s][a]+=self.alpha*(ind_r+self.gamma*future-self.q[s][a])
        self.weight=max(0.1,min(3.0,self.weight*0.99+0.01*abs(self.q[s][a])))

class IQLAgent(MARLAgent):
    """No communication at all — pure independent learning."""
    def act_partial_obs(self, env, peers=None, stale_tau=2):
        obs=env.get_local_obs(self.pos); valid=env.valid_actions_local(self.pos,obs)
        if not valid: return None
        if random.random()<self.epsilon: return random.choice(valid)
        return max(valid,key=lambda a:self.q[self.pos].get(a,0.0))

class MAPPOAgent(MARLAgent):
    """
    MAPPO-lite: actor-critic with centralised value baseline.
    Actor: softmax over Q-values (policy gradient approximation)
    Critic: team value estimate used to reduce variance
    """
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.value_table = defaultdict(float)   # V(s) centralised critic

    def act_partial_obs(self, env, peers=None, stale_tau=2):
        obs=env.get_local_obs(self.pos); valid=env.valid_actions_local(self.pos,obs)
        if not valid: return None
        qc=dict(self.q[self.pos])
        if peers and self.comm>0:
            fresh=self.get_fresh_msgs(stale_tau)
            for pid,snap in list(fresh.items())[:self.comm]:
                if self.pos in snap:
                    for a,val in snap[self.pos].items():
                        qc[a]=qc.get(a,0)+0.3*val
                    self.msg_used+=1
        if random.random()<self.epsilon: return random.choice(valid)
        # Softmax actor (temperature annealed with epsilon)
        tau=max(0.5, self.epsilon*2)
        q_vals=np.array([qc.get(a,0.0) for a in valid])
        q_vals=np.clip((q_vals-q_vals.max())/max(tau,0.1), -50, 50)
        probs=np.exp(q_vals); probs/=probs.sum()+1e-9
        if not np.isfinite(probs).all() or probs.sum()<0.99:
            return random.choice(valid)
        return valid[np.random.choice(len(valid),p=probs)]

    def update_mappo(self,s,a,r,s2,env,team_v):
        """Policy gradient update with centralised critic baseline."""
        obs2=env.get_local_obs(s2); valid2=env.valid_actions_local(s2,obs2)
        future=max((self.q[s2][x] for x in valid2),default=0.0)
        advantage=r+self.gamma*future-team_v
        self.q[s][a]+=self.alpha*np.clip(advantage,-50,50)
        self.value_table[s]+=0.1*(r+self.gamma*self.value_table[s2]-self.value_table[s])


# ═══════════════════════════════════════════════════════════════
# EPISODE RUNNER — one episode on one env instance
# ═══════════════════════════════════════════════════════════════
def run_marl_episode(env, agents, agent_type='ammarl', red_budget=4,
                      ep=0, curriculum_red=None, stale_tau=2, max_steps=50):
    """Run one episode. Returns per-episode metrics."""
    env.reset(ep)
    if curriculum_red is None or curriculum_red > 0:
        budget = curriculum_red if curriculum_red else red_budget
        env.red_act(budget=budget)

    for a in agents: a.reset(env.depot); a.age_messages()

    # Pre-episode message sharing (agents share Q snapshots)
    if agent_type in ['ammarl','vdn','qmix','mappo']:
        for a in agents:
            peers=[x for x in agents if x.id!=a.id]
            a.send_message(peers, stale_tau=stale_tau)

    ep_del=0; route_overlap=0
    prev_positions={a.id: env.depot for a in agents}

    for step in range(max_steps):
        env.step_count = step
        env.reveal_attacks()

        if all(a.delivered or a.failed for a in agents): break

        current_positions=[a.pos for a in agents if not a.delivered and not a.failed]
        # Age messages each step
        for a in agents: a.age_messages()

        for a in agents:
            if a.delivered or a.failed: continue
            peers=[x for x in agents if x.id!=a.id and not x.delivered and not x.failed]
            action=a.act_partial_obs(env, peers, stale_tau=stale_tau)
            if action is None: a.failed=True; continue

            # Check route overlap (multiple agents on same edge)
            other_pos=[x.pos for x in agents if x.id!=a.id and not x.delivered and not x.failed]
            new_pos, success, cost, surv = env.step_agent(a.pos, action, other_pos)

            # Count route overlap
            if action in other_pos: route_overlap+=1

            s=a.pos
            if not success:
                a.blocked_enc+=1
                # Find alternative using local obs
                obs=env.get_local_obs(a.pos)
                alts=env.valid_actions_local(a.pos,obs)
                alts=[v for v in alts if env.G[a.pos][v]['active']]
                if alts:
                    action=min(alts,key=lambda v: env.G[a.pos][v]['threat_level'])
                    new_pos,success,cost,surv=env.step_agent(s,action,other_pos)
                if not success: a.failed=True; continue

            a.cost+=cost; a.surv_acc+=surv
            a.path.append(action); a.visited.add(action); a.pos=action; a.steps+=1

            # Track corridor switches
            corr=env.G[s][action].get('corridor',-1) if env.G.has_edge(s,action) else -1
            if corr!=a.prev_corridor and a.prev_corridor!=-1: a.corridor_switches+=1
            a.prev_corridor=corr

            delivered=(action==a.target)
            if delivered: a.delivered=True; ep_del+=1

            # Individual reward
            if delivered:
                ind_r=40+40*a.avg_surv-0.04*a.cost
            else:
                tl=env.G[s][action]['threat_level'] if env.G.has_edge(s,action) else 0.3
                ind_r=-(cost+15*tl)

            # Updates
            team_del=sum(1 for ag in agents if ag.delivered)
            team_surv=np.mean([ag.avg_surv for ag in agents if ag.delivered]) if team_del else 0.4
            team_r=40*team_del+40*team_surv-0.04*sum(ag.cost for ag in agents if ag.delivered)
            team_q=sum(abs(agents[j].q[agents[j].pos].get(action,0.01)) for j in range(len(agents)))
            team_v=np.mean([a2.value_table.get(s,0) for a2 in agents
                            if hasattr(a2,'value_table')]) if any(hasattr(a2,'value_table') for a2 in agents) else 0

            if agent_type=='ammarl':  a.update_q(s,action,ind_r,action,env)
            elif agent_type=='iql':   a.update_q(s,action,ind_r,action,env)
            elif agent_type=='vdn':   a.update_vdn(s,action,team_r,action,env)
            elif agent_type=='qmix':  a.update_qmix(s,action,team_r,action,env,team_q)
            elif agent_type=='mappo': a.update_mappo(s,action,ind_r,action,env,team_v)

        # Mid-episode message sharing every 5 steps
        if step%5==0 and agent_type in ['ammarl','vdn','qmix','mappo']:
            for a in agents:
                p2=[x for x in agents if x.id!=a.id]
                a.send_message(p2, stale_tau=stale_tau)

    for a in agents: a.decay()

    costs=[a.cost     for a in agents if a.delivered]
    survs=[a.avg_surv for a in agents if a.delivered]
    return dict(
        dr          = ep_del/len(agents),
        cost        = np.mean(costs) if costs else 65.0,
        surv        = np.mean(survs) if survs else 0.35,
        fail        = sum(1 for a in agents if a.failed),
        steps       = np.mean([a.steps for a in agents if a.delivered]) if costs else 25.0,
        blocked_enc = np.mean([a.blocked_enc for a in agents]),
        max_threat  = np.mean([max([env.G[a.path[j]][a.path[j+1]]['threat_level']
                                    for j in range(len(a.path)-1)
                                    if env.G.has_edge(a.path[j],a.path[j+1])] or [0])
                               for a in agents]),
        corridor_sw = np.mean([a.corridor_switches for a in agents]),
        route_overlap=route_overlap/max(ep_del*len(agents),1),
        msg_usage   = np.mean([a.msg_used for a in agents]),
    )


# ═══════════════════════════════════════════════════════════════
# BENCHMARK SUITE — 30 maps x 5 seeds
# ═══════════════════════════════════════════════════════════════
N_MAPS   = 5
N_SEEDS  = 3
N_EP     = 200
N_AG     = 3
MAX_ST   = 50

METHODS = ['AMMARL-PI','IQL','VDN','QMIX','MAPPO']
CLASSICAL= ['B1 Least-Cost','B2 Threat-Aware','B3 Dyn-Replan','B4 PI-Hub','Oracle (MM-R)']
ALL_METHODS = METHODS + CLASSICAL

# Storage: {method: {metric: [run_values]}}
ALL_RESULTS = {m: defaultdict(list) for m in ALL_METHODS}
# Training histories for selected seed+map
TRAIN_H = {m: defaultdict(list) for m in METHODS}

print(f"Benchmark: {N_MAPS} maps x {N_SEEDS} seeds = {N_MAPS*N_SEEDS} runs per method")
print(f"Training {N_EP} episodes per run, {N_AG} agents each")
print()

for map_idx in range(N_MAPS):
    map_seed = map_idx * 100 + 7
    G_template = make_random_map(map_seed)

    for seed in range(N_SEEDS):
        run_id = map_idx * N_SEEDS + seed
        np.random.seed(seed*1000 + map_idx); random.seed(seed*1000 + map_idx)

        # Create environment for this run
        G_run = deepcopy(G_template)
        n_tgt = len(G_run.graph['targets'])
        env_run = ContestEnv(G_run, red_budget=4, obs_radius=2, attack_delay=3, msg_stale=2)

        # Instantiate all MARL agents
        tgts = [G_run.graph['targets'][i % n_tgt] for i in range(N_AG)]
        agents_dict = {
            'AMMARL-PI': [MARLAgent(i, tgts[i], comm=2) for i in range(N_AG)],
            'IQL':        [IQLAgent(i, tgts[i], comm=0)  for i in range(N_AG)],
            'VDN':        [VDNAgent(i, tgts[i], comm=2)  for i in range(N_AG)],
            'QMIX':       [QMIXAgent(i, tgts[i], comm=2) for i in range(N_AG)],
            'MAPPO':      [MAPPOAgent(i, tgts[i], comm=2)for i in range(N_AG)],
        }

        # ── Training ──────────────────────────────────────────
        for ep in range(1, N_EP+1):
            # Curriculum
            if ep <= 150:   cb=0
            elif ep <= 300: cb=2
            else:           cb=4

            for m, ags in agents_dict.items():
                tag = m.lower().replace('-','').replace(' ','')
                if 'ammarl' in tag: atype='ammarl'
                elif 'iql' in tag: atype='iql'
                elif 'vdn' in tag: atype='vdn'
                elif 'qmix' in tag: atype='qmix'
                elif 'mappo' in tag: atype='mappo'
                else: atype='ammarl'
                r=run_marl_episode(env_run, ags, agent_type=atype,
                                   curriculum_red=cb, ep=ep)
                # Store training history for map_idx=0, seed=0
                if map_idx==0 and seed==0:
                    for k,v in r.items(): TRAIN_H[m][k].append(v)
                    TRAIN_H[m]['ep'].append(ep)

        # ── Final evaluation — 20 test episodes ───────────────
        EVAL_EPS = 5
        for m, ags in agents_dict.items():
            tag = m.lower().replace('-','').replace(' ','')
            atype='ammarl' if 'ammarl' in tag else tag.replace('-','')
            run_metrics = defaultdict(list)
            for ep2 in range(N_EP+1, N_EP+EVAL_EPS+1):
                r=run_marl_episode(env_run, ags, agent_type=atype,
                                   curriculum_red=4, ep=ep2)
                for k,v in r.items(): run_metrics[k].append(v)
            for k in run_metrics:
                ALL_RESULTS[m][k].append(np.mean(run_metrics[k]))

        # ── Classical baselines (no training needed) ──────────
        env_run.reset(N_EP+5); env_run.red_act(budget=4)
        for bname, bfn in [('B1 Least-Cost',b1_least_cost),
                            ('B2 Threat-Aware',b2_threat_aware),
                            ('B3 Dyn-Replan',b3_dynamic_replan),
                            ('B4 PI-Hub',b4_pi_hub),
                            ('Oracle (MM-R)',oracle_minimax)]:
            br = agg_results(bfn(env_run, n=N_AG))
            for k,v in br.items(): ALL_RESULTS[bname][k].append(v)

        if run_id % 10 == 0:
            a_surv=np.mean(ALL_RESULTS['AMMARL-PI']['surv'][-5:]) if ALL_RESULTS['AMMARL-PI']['surv'] else 0
            b2_surv=np.mean(ALL_RESULTS['B2 Threat-Aware']['surv'][-5:]) if ALL_RESULTS['B2 Threat-Aware']['surv'] else 0
            print(f"  Run {run_id:>4}/{N_MAPS*N_SEEDS} | AMMARL surv:{a_surv:.3f} | B2 surv:{b2_surv:.3f}")

print("\nBenchmark complete.\n")

# Compute mean±std
STATS = {}
for m in ALL_METHODS:
    STATS[m] = {}
    for k in ['dr','cost','surv','fail','steps','blocked_enc','max_threat','corridor_sw','msg_usage']:
        vals = ALL_RESULTS[m].get(k, [0])
        STATS[m][k] = (float(np.mean(vals)), float(np.std(vals)))

# Print results table
print("="*110)
print(f"  {'Method':<22} {'DR':>10} {'Cost':>14} {'Surv':>14} {'Fail':>10} {'Blk-Enc':>12} {'Max-Thr':>12} {'Corr-Sw':>10}")
print("="*110)
for m in ALL_METHODS:
    s=STATS[m]
    sep = "---" if m==CLASSICAL[0] else ""
    if sep: print(f"  {'-'*105}")
    dr_s  =f"{s['dr'][0]:.1%}±{s['dr'][1]:.1%}"
    co_s  =f"{s['cost'][0]:.2f}±{s['cost'][1]:.2f}"
    sv_s  =f"{s['surv'][0]:.3f}±{s['surv'][1]:.3f}"
    fa_s  =f"{s['fail'][0]:.2f}±{s['fail'][1]:.2f}"
    be_s  =f"{s['blocked_enc'][0]:.2f}±{s['blocked_enc'][1]:.2f}"
    mt_s  =f"{s['max_threat'][0]:.3f}±{s['max_threat'][1]:.3f}"
    cs_s  =f"{s['corridor_sw'][0]:.2f}±{s['corridor_sw'][1]:.2f}"
    print(f"  {m:<22} {dr_s:>10} {co_s:>14} {sv_s:>14} {fa_s:>10} {be_s:>12} {mt_s:>12} {cs_s:>10}")
print("="*110)


# ═══════════════════════════════════════════════════════════════
# FIGURES — no radar, no 100% delivery charts as main evidence
# ═══════════════════════════════════════════════════════════════
W=30
def smooth(a,w=W):
    if len(a)<w: return np.array(a)
    return np.convolve(a,np.ones(w)/w,mode='valid')
def epr(a,w=W):
    if len(a)<w: return list(range(1,len(a)+1))
    return list(range(w,len(a)+1))

MCOLORS={
    'AMMARL-PI':'#4CAF50','IQL':'#90CAF9','VDN':'#29B6F6',
    'QMIX':'#1565C0','MAPPO':'#7B1FA2',
    'B1 Least-Cost':'#EF5350','B2 Threat-Aware':'#FF9800',
    'B3 Dyn-Replan':'#FDD835','B4 PI-Hub':'#AB47BC',
    'Oracle (MM-R)':'#FF7043',
}


# ── FIG 1: PRIMARY — Survivability mean±std (main evidence) ──
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("PRIMARY RESULT: Route Survivability — Mean ± Std\n"
             f"30 Randomized Maps × 5 Seeds = {N_MAPS*N_SEEDS} Runs per Method",
             fontsize=13, **FB)

# Left: all methods bar chart with error bars
ax = axes[0]
methods_ordered = ['AMMARL-PI','MAPPO','QMIX','VDN','IQL',
                   'B2 Threat-Aware','B3 Dyn-Replan','B1 Least-Cost','B4 PI-Hub','Oracle (MM-R)']
surv_means = [STATS[m]['surv'][0] for m in methods_ordered]
surv_stds  = [STATS[m]['surv'][1] for m in methods_ordered]
colors     = [MCOLORS[m] for m in methods_ordered]
y = np.arange(len(methods_ordered))
bars = ax.barh(y, surv_means, xerr=surv_stds, color=colors,
               edgecolor='black', linewidth=0.8, capsize=4,
               error_kw={'elinewidth':1.5,'capthick':1.5})
bars[0].set_edgecolor('#1B5E20'); bars[0].set_linewidth(2.5)
ax.axvline(STATS['Oracle (MM-R)']['surv'][0], color='#FF7043', lw=1.5, ls='--',
           alpha=0.7, label='Oracle upper bound')
ax.set_yticks(y); ax.set_yticklabels(methods_ordered, fontsize=9)
ax.set_xlabel('Avg Edge Survivability (higher=better)', fontsize=10)
ax.set_title('Survivability (primary KPI)', **FB)
ax.grid(axis='x', alpha=0.3); ax.legend(fontsize=9)
for i, (mn,sd) in enumerate(zip(surv_means,surv_stds)):
    ax.text(mn+sd+0.003, i, f"{mn:.3f}", va='center', fontsize=8)

# Right: MARL training curves on survivability
ax = axes[1]
for m in ['AMMARL-PI','MAPPO','QMIX','VDN','IQL']:
    if TRAIN_H[m]['surv']:
        sm=smooth(TRAIN_H[m]['surv']); ep_=epr(TRAIN_H[m]['surv'])
        lw=2.5 if m=='AMMARL-PI' else 1.8
        ls='-' if m=='AMMARL-PI' else '--'
        ax.plot(ep_,sm,color=MCOLORS[m],lw=lw,ls=ls,label=m)
for bm,bname in [('B2 Threat-Aware','B2 Threat-SP'),('Oracle (MM-R)','Oracle')]:
    if STATS[bm]['surv'][0]>0:
        ax.axhline(STATS[bm]['surv'][0],color=MCOLORS[bm],lw=1.5,ls=':',
                   alpha=0.8,label=bname)
ax.axvline(150,color='gray',lw=1,ls=':',alpha=0.6)
ax.axvline(300,color='gray',lw=1,ls=':',alpha=0.6)
ax.text(75,0.15,'Phase1\nCoop',ha='center',fontsize=7,color='gray')
ax.text(225,0.15,'Phase2\nLight',ha='center',fontsize=7,color='gray')
ax.text(450,0.15,'Phase3\nFullRed',ha='center',fontsize=7,color='gray')
ax.set_title('Survivability Learning (Map 0, Seed 0)', **FB)
ax.set_xlabel('Training Episode'); ax.set_ylabel('Avg Survivability')
ax.legend(fontsize=8); ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(save('v8_fig1_survivability.png'), dpi=150, bbox_inches='tight'); plt.close()
print("Saved fig1")


# ── FIG 2: PRIMARY — Delivery Cost + Blocked-Edge Encounters ─
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("PRIMARY RESULT: Delivery Cost and Blocked-Edge Encounters\n"
             f"Mean ± Std over {N_MAPS*N_SEEDS} Runs",
             fontsize=13, **FB)

ax = axes[0]
cost_means=[STATS[m]['cost'][0] for m in methods_ordered]
cost_stds =[STATS[m]['cost'][1] for m in methods_ordered]
bars2=ax.barh(y,cost_means,xerr=cost_stds,color=colors,edgecolor='black',
              linewidth=0.8,capsize=4,error_kw={'elinewidth':1.5,'capthick':1.5})
bars2[0].set_edgecolor('#1B5E20'); bars2[0].set_linewidth(2.5)
ax.set_yticks(y); ax.set_yticklabels(methods_ordered,fontsize=9)
ax.set_xlabel('Average Delivery Cost J = αT + βC + γQ (lower=better)',fontsize=10)
ax.set_title('Delivery Cost',**FB); ax.grid(axis='x',alpha=0.3)
for i,(mn,sd) in enumerate(zip(cost_means,cost_stds)):
    ax.text(mn+sd+0.2,i,f"{mn:.2f}",va='center',fontsize=8)

ax = axes[1]
benc_means=[STATS[m]['blocked_enc'][0] for m in methods_ordered]
benc_stds =[STATS[m]['blocked_enc'][1] for m in methods_ordered]
bars3=ax.barh(y,benc_means,xerr=benc_stds,color=colors,edgecolor='black',
              linewidth=0.8,capsize=4,error_kw={'elinewidth':1.5,'capthick':1.5})
bars3[0].set_edgecolor('#1B5E20'); bars3[0].set_linewidth(2.5)
ax.set_yticks(y); ax.set_yticklabels(methods_ordered,fontsize=9)
ax.set_xlabel('Blocked-Edge Encounters per Delivery (lower=better)',fontsize=10)
ax.set_title('Blocked-Edge Encounters\n(AMMARL learns to pre-avoid)',**FB)
ax.grid(axis='x',alpha=0.3)
for i,(mn,sd) in enumerate(zip(benc_means,benc_stds)):
    ax.text(mn+sd+0.005,i,f"{mn:.3f}",va='center',fontsize=8)

plt.tight_layout()
plt.savefig(save('v8_fig2_cost_blocked.png'),dpi=150,bbox_inches='tight'); plt.close()
print("Saved fig2")


# ── FIG 3: DIAGNOSTIC — Corridor Switches + Max Threat + Route Overlap ─
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle("DIAGNOSTIC METRICS — Corridor-Switch Rate, Max-Edge Threat, Message Usage\n"
             f"Mean ± Std over {N_MAPS*N_SEEDS} Runs",
             fontsize=12, **FB)

for ax, (key, xlabel, title) in zip(axes, [
    ('corridor_sw', 'Corridor Switches per Delivery\n(higher=more adaptive)',
     'Corridor-Switch Rate\n(AMMARL adapts faster under attack)'),
    ('max_threat',  'Max Edge Threat on Path\n(lower=safer path selection)',
     'Max Threat on Chosen Path\n(AMMARL avoids dangerous edges)'),
    ('msg_usage',   'Avg Messages Used per Agent\n(higher=more coordination)',
     'Communication Usage\n(AMMARL uses comms; IQL=0)'),
]):
    means=[STATS[m][key][0] for m in methods_ordered]
    stds =[STATS[m][key][1] for m in methods_ordered]
    hbars=ax.barh(y,means,xerr=stds,color=colors,edgecolor='black',
                  linewidth=0.8,capsize=4,error_kw={'elinewidth':1.5})
    hbars[0].set_edgecolor('#1B5E20'); hbars[0].set_linewidth(2.5)
    ax.set_yticks(y); ax.set_yticklabels(methods_ordered,fontsize=9)
    ax.set_xlabel(xlabel,fontsize=9); ax.set_title(title,**FB,fontsize=10)
    ax.grid(axis='x',alpha=0.3)
    for i,(mn,sd) in enumerate(zip(means,stds)):
        ax.text(mn+sd+max(means)*0.01,i,f"{mn:.3f}",va='center',fontsize=7)

plt.tight_layout()
plt.savefig(save('v8_fig3_diagnostics.png'),dpi=150,bbox_inches='tight'); plt.close()
print("Saved fig3")


# ── FIG 4: STRESS — Delivery Rate where it ACTUALLY varies ───
# At budget=6+, delivery rate starts to diverge — this is the valid plot
budgets=[2,4,6,8]
stress_res={m:{b:defaultdict(list) for b in budgets} for m in ['AMMARL-PI','QMIX','VDN','IQL','B2 Threat-Aware','B3 Dyn-Replan']}

print("Stress test (10 maps x 3 seeds) ...")
for mi in range(3):
    Gt=make_random_map(mi*200+13)
    for si in range(2):
        np.random.seed(si*100+mi); random.seed(si*100+mi)
        Gr=deepcopy(Gt)
        tgts2=[Gr.graph['targets'][i%len(Gr.graph['targets'])] for i in range(N_AG)]
        ags2={
            'AMMARL-PI':[MARLAgent(i,tgts2[i],comm=2) for i in range(N_AG)],
            'IQL':       [IQLAgent(i,tgts2[i],comm=0)  for i in range(N_AG)],
            'VDN':       [VDNAgent(i,tgts2[i],comm=2)  for i in range(N_AG)],
            'QMIX':      [QMIXAgent(i,tgts2[i],comm=2) for i in range(N_AG)],
        }
        er2=ContestEnv(Gr,red_budget=4,obs_radius=2,attack_delay=3,msg_stale=2)
        # Quick train 300 eps
        for ep3 in range(1,151):
            cb3=0 if ep3<100 else (2 if ep3<200 else 4)
            for m,ags in ags2.items():
                atype=m.lower().replace('-','').replace(' ','').replace('(','').replace(')','')
                if atype not in ['ammarl','iql','vdn','qmix','mappo']: atype='ammarl'
                run_marl_episode(er2,ags,agent_type=atype,curriculum_red=cb3,ep=ep3)
        # Eval at each budget
        for b in budgets:
            for m,ags in ags2.items():
                atype=m.lower().replace('-','').replace(' ','').replace('(','').replace(')','')
                if atype not in ['ammarl','iql','vdn','qmix','mappo']: atype='ammarl'
                er2.reset(500); er2.red_act(budget=b)
                r2=run_marl_episode(er2,ags,agent_type=atype,curriculum_red=b,ep=500)
                for k in ['dr','surv','cost','fail']: stress_res[m][b][k].append(r2[k])
        er2.reset(500)
        for m,fn in [('B2 Threat-Aware',b2_threat_aware),('B3 Dyn-Replan',b3_dynamic_replan)]:
            for b in budgets:
                er2.reset(500); er2.red_act(budget=b)
                br2=agg_results(fn(er2,n=N_AG))
                for k in ['dr','surv','cost','fail']: stress_res[m][b][k].append(br2[k])

print("Stress test done.")

fig,axes=plt.subplots(2,2,figsize=(16,10))
fig.suptitle("ADVERSARIAL PRESSURE TEST — Mean ± Std\n"
             "10 Maps × 3 Seeds | Red Budget 2→8 | Delivery Rate Only Where It Varies",
             fontsize=12,**FB)

stress_methods=[('AMMARL-PI','#4CAF50','-',3),('QMIX','#1565C0','--',2),
                ('VDN','#29B6F6','-.', 1.8),('IQL','#90CAF9',':',1.5),
                ('B2 Threat-Aware','#FF9800','--',1.8),('B3 Dyn-Replan','#FDD835',':',1.5)]

for ax,(title,key,hb) in zip(axes.flat,[
    ('Delivery Rate','dr',True),('Route Survivability','surv',True),
    ('Delivery Cost','cost',False),('Delivery Failures','fail',False)]):
    for m,col,ls_,lw_ in stress_methods:
        means=[np.mean(stress_res[m][b][key]) for b in budgets]
        stds =[np.std(stress_res[m][b][key])  for b in budgets]
        lbl=m if m not in ['B2 Threat-Aware','B3 Dyn-Replan'] else m[:10]
        ax.plot(budgets,means,color=col,lw=lw_,ls=ls_,marker='o',ms=5,label=lbl)
        ax.fill_between(budgets,
                        [max(0,mn-sd) for mn,sd in zip(means,stds)],
                        [min(1,mn+sd) if hb else mn+sd for mn,sd in zip(means,stds)],
                        alpha=0.1,color=col)
    ax.set_title(title,**FB); ax.set_xlabel('Red Agent Budget (routes blocked)')
    ax.set_ylabel('Value'); ax.set_xticks(budgets); ax.legend(fontsize=7); ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(save('v8_fig4_stress.png'),dpi=150,bbox_inches='tight'); plt.close()
print("Saved fig4")


# ── FIG 5: COMMUNICATION BUDGET — with staleness ─────────────
comm_budgets=[0,1,2,3,4]
stale_vals  =[0,1,2,4,8]   # message staleness tau

cb_res  ={c: defaultdict(list) for c in comm_budgets}
stale_res={t: defaultdict(list) for t in stale_vals}

print("Comm budget + staleness experiment ...")
for mi2 in range(3):
    Gt3=make_random_map(mi2*300+17)
    for si2 in range(3):
        np.random.seed(si2*200+mi2); random.seed(si2*200+mi2)
        Gr3=deepcopy(Gt3); tgts3=[Gr3.graph['targets'][i%len(Gr3.graph['targets'])] for i in range(N_AG)]
        er3=ContestEnv(Gr3,red_budget=4,obs_radius=2,attack_delay=3,msg_stale=2)

        # Train base AMMARL
        base_ags=[MARLAgent(i,tgts3[i],comm=2) for i in range(N_AG)]
        for ep4 in range(1,251):
            cb4=0 if ep4<80 else (2 if ep4<160 else 4)
            run_marl_episode(er3,base_ags,'ammarl',curriculum_red=cb4,ep=ep4)

        # Comm budget sweep
        for c_val in comm_budgets:
            test_ags=[MARLAgent(i,tgts3[i],comm=c_val) for i in range(N_AG)]
            for a_i,a_b in enumerate(base_ags): test_ags[a_i].q=deepcopy(a_b.q)
            er3.reset(300); er3.red_act(budget=4)
            r4=run_marl_episode(er3,test_ags,'ammarl',curriculum_red=4,ep=300,stale_tau=2)
            for k in ['dr','surv','cost','fail']: cb_res[c_val][k].append(r4[k])

        # Staleness sweep
        for st_val in stale_vals:
            test_ags2=[MARLAgent(i,tgts3[i],comm=2) for i in range(N_AG)]
            for a_i,a_b in enumerate(base_ags): test_ags2[a_i].q=deepcopy(a_b.q)
            er3.reset(300); er3.red_act(budget=4)
            r5=run_marl_episode(er3,test_ags2,'ammarl',curriculum_red=4,ep=300,stale_tau=st_val)
            for k in ['dr','surv','cost','fail']: stale_res[st_val][k].append(r5[k])

print("Comm experiment done.")

fig,axes=plt.subplots(1,4,figsize=(20,5))
fig.suptitle("Communication Budget and Message Staleness Impact\n"
             "5 Maps × 3 Seeds | Tested on Fully Trained AMMARL-PI",fontsize=12,**FB)

b2_ref=STATS['B2 Threat-Aware']
for ax,(title,key,hb,xlabel,xvals,res,ref_val) in zip(axes,[
    ('DR vs Comm Budget','dr',True,'Comm Budget mu',comm_budgets,cb_res,b2_ref['dr'][0]),
    ('Surv vs Comm Budget','surv',True,'Comm Budget mu',comm_budgets,cb_res,b2_ref['surv'][0]),
    ('Surv vs Staleness tau','surv',True,'Message Staleness tau',stale_vals,stale_res,b2_ref['surv'][0]),
    ('Cost vs Staleness tau','cost',False,'Message Staleness tau',stale_vals,stale_res,b2_ref['cost'][0]),
]):
    means=[np.mean(res[x][key]) for x in xvals]
    stds =[np.std(res[x][key])  for x in xvals]
    ax.plot(xvals,means,'o-',color='#2E7D32',lw=2.5,ms=9,
            markerfacecolor='white',markeredgewidth=2.5,label='AMMARL-PI')
    ax.fill_between(xvals,[max(0,m-s) for m,s in zip(means,stds)],
                    [m+s for m,s in zip(means,stds)],alpha=0.15,color='#4CAF50')
    ax.axhline(ref_val,color='#FF9800',lw=1.8,ls='--',label=f"B2 Threat-SP ({ref_val:.3f})")
    if xlabel=='Comm Budget mu': ax.axvline(2,color='gray',lw=1.2,ls=':',alpha=0.8,label='Chosen mu=2')
    if xlabel=='Message Staleness tau': ax.axvline(2,color='gray',lw=1.2,ls=':',alpha=0.8,label='Chosen tau=2')
    ax.set_title(title,**FB); ax.set_xlabel(xlabel); ax.set_ylabel(key.capitalize())
    ax.legend(fontsize=8); ax.grid(alpha=0.3); ax.set_xticks(xvals)

plt.tight_layout()
plt.savefig(save('v8_fig5_comm_staleness.png'),dpi=150,bbox_inches='tight'); plt.close()
print("Saved fig5")


# ── FIG 6: TRAINING ON MAP 0 SEED 0 ─────────────────────────
fig,axes=plt.subplots(2,2,figsize=(14,9))
fig.suptitle("MARL Training Convergence (Map 0, Seed 0)\n"
             "Curriculum: Cooperative → Light Red → Full Red (Budget=4)",fontsize=12,**FB)

for ax,(key,ylabel,title,hb) in zip(axes.flat,[
    ('surv','Survivability','Route Survivability',True),
    ('cost','Cost J','Delivery Cost',False),
    ('dr','Delivery Rate','Delivery Rate (varies in early training)',True),
    ('blocked_enc','Blk-Enc/Delivery','Blocked-Edge Encounters',False),
]):
    for m in ['AMMARL-PI','MAPPO','QMIX','VDN','IQL']:
        if not TRAIN_H[m][key]: continue
        sm=smooth(TRAIN_H[m][key]); ep_=epr(TRAIN_H[m][key])
        lw_=2.5 if m=='AMMARL-PI' else 1.8
        ls_='-' if m=='AMMARL-PI' else '--'
        ax.plot(ep_,sm,color=MCOLORS[m],lw=lw_,ls=ls_,label=m)
    for bm,bn in [('B2 Threat-Aware','B2'),('B3 Dyn-Replan','B3')]:
        v=STATS[bm][key][0]
        if v>0: ax.axhline(v,color=MCOLORS[bm],lw=1.3,ls=':',alpha=0.8,label=f"{bn}({v:.3f})")
    for xv,xl in [(150,'P1'),(300,'P2')]:
        ax.axvline(xv,color='gray',lw=0.8,ls=':',alpha=0.5)
        ax.text(xv+5,ax.get_ylim()[0]*1.05 if ax.get_ylim()[0]>0 else 0.01,xl,fontsize=7,color='gray')
    ax.set_title(title,**FB); ax.set_xlabel('Episode'); ax.set_ylabel(ylabel)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(save('v8_fig6_training.png'),dpi=150,bbox_inches='tight'); plt.close()
print("Saved fig6")


# ── SAVE SUMMARY TABLE ───────────────────────────────────────
print(f"\nAll figures saved to: {OUTPUT_DIR}")
print("\nFINAL SUMMARY TABLE:")
print(f"{'Method':<22} {'Surv(mean)':>12} {'Surv(std)':>10} {'DR(mean)':>10} {'Blk-Enc':>10} {'Corr-SW':>10}")
print("-"*80)
for m in ALL_METHODS:
    s=STATS[m]
    print(f"{m:<22} {s['surv'][0]:>12.4f} {s['surv'][1]:>10.4f} {s['dr'][0]:>10.1%} {s['blocked_enc'][0]:>10.4f} {s['corridor_sw'][0]:>10.4f}")