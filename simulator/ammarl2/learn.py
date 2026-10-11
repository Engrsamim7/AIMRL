"""Belief-conditioned deep routing with local actors and a MAPPO-only central critic.

This is a finite-history observation approximation for a partially observable
semi-Markov process, not a claim that the observed features are a Markov state.
Topology, nominal costs and prior threats are public; remote live queues, flow,
and attack state never enter the actor. Hazard beliefs do not remove actions:
the hard mask consists only of outgoing edges with a path to the assigned target.
"""
from dataclasses import dataclass
import heapq
import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from .policies import Policy

OBSERVATION_VERSION = 'local-belief-v2'
FN, FE, FG = 10, 9, 4
_GC = {}


def _revdist(g, target):
    incoming = [[] for _ in range(g.n)]
    for e, v in enumerate(g.dst):
        incoming[int(v)].append(e)
    d = np.full(g.n, np.inf); d[target] = 0
    heap = [(0., target)]
    while heap:
        du, v = heapq.heappop(heap)
        if du > d[v]:
            continue
        for e in incoming[v]:
            u = int(g.src[e]); nd = du + g.c[e]
            if nd < d[u]:
                d[u] = nd; heapq.heappush(heap, (nd, u))
    return d


def gctx(g):
    key = (g.n, tuple(g.targets), g.src.tobytes(), g.dst.tobytes(), g.c.tobytes())
    if key not in _GC:
        # Sparse symmetric message-passing adjacency, O(V+E) storage.
        pairs = {(i, i) for i in range(g.n)}
        pairs.update((int(u), int(v)) for u, v in zip(g.src, g.dst))
        pairs.update((int(v), int(u)) for u, v in zip(g.src, g.dst))
        pairs = sorted(pairs)
        degree = np.bincount([u for u, v in pairs], minlength=g.n)
        indices = torch.tensor(pairs, dtype=torch.long).T
        values = torch.tensor([1 / degree[u] for u, v in pairs], dtype=torch.float32)
        adjacency = torch.sparse_coo_tensor(indices, values, (g.n, g.n), check_invariants=True).coalesce()
        distances = {target: _revdist(g, target) for target in g.targets}
        scale = max(1., max(v[np.isfinite(v)].max() for v in distances.values()))
        if len(_GC) >= 64:
            _GC.clear()
        _GC[key] = adjacency, distances, float(scale)
    return _GC[key]


@dataclass
class Ctx:
    X: torch.Tensor
    A: torch.Tensor
    u: int
    dst: torch.Tensor
    EF: torch.Tensor
    edges: list
    glob: torch.Tensor


def build_ctx(sim, cv, ban, merged, t, tau_stale):
    g = sim.g
    A, rd, scale = gctx(g); distances = rd[cv.target]
    visible_edges = set(sim.edges_in_radius(cv.node))
    visible_nodes = {cv.node} | {int(g.src[e]) for e in visible_edges}
    # A radius-1 report is outgoing-edge sensing, not live telemetry at its head.
    X = np.zeros((g.n, FN), np.float32)
    X[:, 2] = np.where(np.isfinite(distances), distances / scale, 1.5)
    X[cv.node, 0] = 1; X[cv.target, 1] = 1
    X[:, 8] = t / sim.cfg.horizon
    for u in range(g.n):
        edges = g.out[u]
        if u in visible_nodes:
            X[u, 3] = sim.busy[u] / sim.cfg.hub_cap
            X[u, 4] = len(sim.queue[u]) / sim.cfg.n_convoys
            X[u, 7] = 1
        if edges:
            X[u, 5] = np.mean([e in ban for e in edges])
            X[u, 6] = g.rho[edges].mean()
            X[u, 9] = np.mean([e in merged for e in edges])
    edges = [e for e in g.out[cv.node] if np.isfinite(distances[int(g.dst[e])])]
    EF = np.zeros((len(edges), FE), np.float32)
    for k, e in enumerate(edges):
        belief = merged.get(e)
        age = (t - belief[1]) / tau_stale if belief else 0.
        flow_known = e in visible_edges
        flow = sim.flow[e] / g.q[e] if flow_known else 0.
        EF[k] = [g.c[e] / 5, g.rho[e], flow, float(e in ban), age,
                 distances[int(g.dst[e])] / scale, belief[2] if belief else 0.,
                 float(belief is not None), float(flow_known)]
    # Privileged training context is consumed only by the centralized value head.
    glob = torch.tensor([len(sim.active) / max(1, sim.cfg.budget),
                         sum(o.alive and not o.delivered for o in sim.cv) / sim.cfg.n_convoys,
                         float(np.mean(sim.flow / g.q)),
                         float(sim.busy.sum() / (g.n * sim.cfg.hub_cap))], dtype=torch.float32)
    return Ctx(torch.tensor(X), A, cv.node,
               torch.tensor([int(g.dst[e]) for e in edges], dtype=torch.long),
               torch.tensor(EF), edges, glob)


class Net(nn.Module):
    def __init__(self, hid=48, central=False):
        super().__init__(); self.central = central
        self.inp = nn.Linear(FN, hid)
        self.g1 = nn.Linear(2 * hid, hid); self.g2 = nn.Linear(2 * hid, hid)
        self.eh = nn.Sequential(nn.Linear(2 * hid + FE, hid), nn.ReLU(), nn.Linear(hid, 1))
        self.vh = nn.Sequential(nn.Linear(hid + (FG if central else 0), hid), nn.ReLU(), nn.Linear(hid, 1))

    def forward(self, c):
        h = F.relu(self.inp(c.X))
        h = F.relu(self.g1(torch.cat([h, torch.sparse.mm(c.A, h)], 1)))
        h = F.relu(self.g2(torch.cat([h, torch.sparse.mm(c.A, h)], 1)))
        scores = self.eh(torch.cat([h[c.u].expand(len(c.dst), -1), h[c.dst], c.EF], 1)).squeeze(1)
        value_input = torch.cat([h[c.u], c.glob]) if self.central else h[c.u]
        return scores, self.vh(value_input).squeeze()


def gae(trajectory, lam):
    """Reverse returns with explicit terminal masking and elapsed-time discounts."""
    result = []; advantage = 0.
    for i in range(len(trajectory) - 1, -1, -1):
        c, a, lp, value, reward, done, discount = trajectory[i]
        next_value = trajectory[i + 1][3] if not done and i + 1 < len(trajectory) else 0.
        delta = reward + discount * next_value - value
        advantage = delta + (0. if done else discount * lam * advantage)
        result.append((c, a, lp, advantage, advantage + value))
    return result


@dataclass
class LearnedPolicy(Policy):
    algo: str = 'dqn'
    train: bool = False
    eps: float = 0.
    seed: int = 0
    learning_rate: float = 1e-3
    gamma: float = 0.99
    discount_time_unit: float = 1.
    gae_lambda: float = 0.95
    ppo_epochs: int = 4
    ppo_clip: float = 0.2
    minibatch_size: int = 64
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    time_weight: float = 1.
    nominal_weight: float = 0.
    death_penalty: float = 40.
    delivery_reward: float = 40.
    timeout_penalty: float = 40.
    dqn_warmup: int = 256
    dqn_batch_size: int = 32
    dqn_update_interval: int = 8
    target_interval: int = 100

    def __post_init__(self):
        super().__post_init__()
        if self.algo not in ('dqn', 'ppo', 'ippo', 'mappo'):
            raise ValueError('Unknown deep baseline')
        if not 0 < self.gamma <= 1 or self.discount_time_unit <= 0:
            raise ValueError('Invalid semi-Markov discount')
        if min(self.dqn_warmup, self.dqn_batch_size, self.dqn_update_interval,
               self.target_interval, self.minibatch_size, self.ppo_epochs) < 1:
            raise ValueError('Invalid update sizes')
        if self.dqn_warmup < self.dqn_batch_size:
            raise ValueError('DQN warmup must cover a batch')
        torch.manual_seed(self.seed)
        self.net = Net(central=self.algo == 'mappo')
        self.opt = torch.optim.Adam(self.net.parameters(), lr=self.learning_rate)
        if self.algo == 'dqn':
            self.tgt = Net(); self.tgt.load_state_dict(self.net.state_dict())
        self.buf, self.nupd, self.nstep = [], 0, 0
        self.pend, self.traj = {}, {}
        self.rng = np.random.default_rng(self.seed)
        self.torch_rng = torch.Generator().manual_seed(self.seed)
        self.losses = []
        self.agent_nets = {0: self.net}
        self.agent_opts = {0: self.opt}

    def agent_network(self, convoy_id):
        """IPPO uses one independently optimized actor/critic per convoy slot.

        PPO shares a local actor/critic across the population; MAPPO shares
        its actor and adds privileged centralized critic context.
        """
        if self.algo != 'ippo':
            return self.net
        if convoy_id not in self.agent_nets:
            if not self.train:
                raise ValueError('IPPO evaluation population exceeds trained convoy slots')
            with torch.random.fork_rng():
                torch.manual_seed(self.seed + 1009 * convoy_id)
                net = Net()
            self.agent_nets[convoy_id] = net
            self.agent_opts[convoy_id] = torch.optim.Adam(net.parameters(), lr=self.learning_rate)
        return self.agent_nets[convoy_id]

    def select(self, sim, cv, w, ban, merged, t):
        c = build_ctx(sim, cv, ban, merged, t, sim.cfg.tau_stale)
        if not c.edges:
            raise ValueError('Reachability mask has no valid action')
        if self.train:
            self._advance(cv, c, t)
        with torch.no_grad():
            scores, value = self.agent_network(cv.id)(c)
        if self.algo == 'dqn':
            a = int(self.rng.integers(len(c.edges))) if self.train and self.rng.random() < self.eps else int(scores.argmax())
            lp = 0.
        else:
            probs = scores.softmax(0)
            a = int(torch.multinomial(probs, 1, generator=self.torch_rng)) if self.train else int(scores.argmax())
            lp = float(scores.log_softmax(0)[a])
        if self.train:
            self.pend[cv.id] = c, a, t, lp, float(value), cv.nominal
        return c.edges[a]

    def _advance(self, cv, c_next, t, done=False, death=False, truncated=False):
        pending = self.pend.pop(cv.id, None)
        if pending is None:
            return
        c, a, t0, lp, value, nominal0 = pending
        duration = t - t0
        reward = -self.time_weight * duration - self.nominal_weight * (cv.nominal - nominal0)
        if done:
            reward += -self.death_penalty if death else (-self.timeout_penalty if truncated else self.delivery_reward)
        discount = self.gamma ** (duration / self.discount_time_unit)
        if self.algo == 'dqn':
            self.buf.append((c, a, reward, c_next, done, discount)); self.buf = self.buf[-20000:]
            self.nstep += 1
            if self.nstep % self.dqn_update_interval == 0 and len(self.buf) >= self.dqn_warmup:
                self._dqn_update()
        else:
            self.traj.setdefault(cv.id, []).append((c, a, lp, value, reward, done, discount))

    def terminal(self, sim, cv, t, death, truncated=False):
        if self.train:
            self._advance(cv, None, t, done=True, death=death, truncated=truncated)

    def _dqn_update(self):
        indices = self.rng.choice(len(self.buf), size=self.dqn_batch_size, replace=False)
        losses = []
        for i in indices:
            c, a, reward, cn, done, discount = self.buf[i]
            q = self.net(c)[0][a]
            with torch.no_grad():
                # Double DQN: same reachability mask in selection and bootstrap.
                target = reward
                if not done and cn is not None and cn.edges:
                    next_a = self.net(cn)[0].argmax()
                    target += discount * float(self.tgt(cn)[0][next_a])
            losses.append(F.smooth_l1_loss(q, q.new_tensor(target)))
        loss = torch.stack(losses).mean()
        self._step(loss)
        if self.nupd % self.target_interval == 0:
            self.tgt.load_state_dict(self.net.state_dict())

    def _step(self, loss, convoy_id=0):
        if not torch.isfinite(loss):
            raise FloatingPointError('Nonfinite training loss')
        net = self.agent_network(convoy_id)
        optimizer = self.agent_opts[convoy_id] if self.algo == 'ippo' else self.opt
        optimizer.zero_grad(); loss.backward()
        nn.utils.clip_grad_norm_(net.parameters(), 5.)
        optimizer.step(); self.nupd += 1; self.losses.append(float(loss.detach()))

    def end_episode(self):
        if self.pend:
            raise RuntimeError('Unclosed transitions; simulator must finalize horizon failures')
        if self.algo == 'dqn' or not self.traj:
            self.traj.clear(); return
        groups = self.traj.items() if self.algo == 'ippo' else [(0, None)]
        for convoy_id, trajectory in groups:
            data = gae(trajectory, self.gae_lambda) if trajectory is not None else [
                item for tr in self.traj.values() for item in gae(tr, self.gae_lambda)]
            advantages = torch.tensor([item[3] for item in data])
            advantages = (advantages - advantages.mean()) / (advantages.std(unbiased=False) + 1e-6)
            net = self.agent_network(convoy_id)
            for _ in range(self.ppo_epochs):
                indices = self.rng.permutation(len(data))
                for start in range(0, len(indices), self.minibatch_size):
                    batch_losses = []
                    for i in indices[start:start + self.minibatch_size]:
                        c, a, old_lp, _, ret = data[i]
                        scores, value = net(c)
                        dist = torch.distributions.Categorical(logits=scores)
                        ratio = (dist.log_prob(torch.tensor(a)) - old_lp).exp()
                        surrogate = torch.minimum(ratio * advantages[i],
                                                  ratio.clamp(1-self.ppo_clip, 1+self.ppo_clip) * advantages[i])
                        batch_losses.append(-surrogate + self.value_coef * (value - ret).square()
                                            - self.entropy_coef * dist.entropy())
                    self._step(torch.stack(batch_losses).mean(), convoy_id)
        self.traj.clear()
