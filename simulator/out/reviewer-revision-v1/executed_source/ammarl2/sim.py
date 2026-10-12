"""Discrete-event simulator for multi-convoy contested routing.

Semantics (all documented so the paper's Eq. 2/12/13 can be matched 1:1):
  * traversal time  T_e = c_e * (1 + 0.2 * flow_e / q_e)            (Eq. 2, flow-coupled)
  * hub: `hub_cap` convoys in service at once, others wait FIFO; decision is taken at
    service end, so belief ages while a convoy queues (AoI accrues during queueing).
  * adversary blocks edge e at t0 for a duration; block is *observable* only after
    t0 + tau_reveal. A convoy entering a blocked edge is an ENCOUNTER (integer B_i); it
    is destroyed with probability p_kill (pre-sampled per (convoy, hop) => CRN-safe),
    otherwise it crosses `blocked_slow` times slower.
  * messages: broadcast by observers, delay tau_msg, loss p_loss, adversary spoofing.
"""
import heapq, hashlib
from .graph import optimal_nominal_cost
from collections import deque
from dataclasses import dataclass, field
import numpy as np

DEPART, ARRIVE, SERVE_END, ATTACK, UNBLOCK, MSG, SPOOF, DEATH = range(8)


@dataclass
class Cfg:
    n_convoys: int = 12
    stagger: float = 2.0
    hub_cap: int = 2
    hub_service: float = 1.0
    tau_reveal: float = 5.0
    tau_msg: float = 2.0
    tau_stale: float = 8.0
    p_loss: float = 0.0
    spoof_rate: float = 0.0
    obs_radius: int = 1
    adv: str = "random"          # random | reactive
    attack_rate: float = 0.35
    attack_dur: tuple = (15.0, 30.0)
    budget: int = 3
    p_kill: float = 0.5
    blocked_slow: float = 2.0
    react_delay: float = 2.0  # adversary sees traffic entries only after this delay
    react_eps: float = 0.2
    react_halflife: float = 10.0
    horizon: float = 2000.0
    conf_mu: float = 1.0          # genuine-message confidence ~ clip(N(mu, sd), 0.05, 1); default = perfectly informative
    spoof_mode: str = "exogenous" # exogenous permits controlled single-message replay; targeted adapts to policy
    congestion_factor: float = 0.2
    conf_sd: float = 0.0
    allow_base_transit: bool = False  # original bidirectional graph has multiple bases


    def __post_init__(self):
        if self.n_convoys < 1 or self.hub_cap < 1 or self.obs_radius < 0:
            raise ValueError("Invalid convoy, hub or observation count")
        if self.adv not in ("random", "reactive") or self.spoof_mode not in ("exogenous", "targeted"):
            raise ValueError("Unknown adversary mode")
        for value in (self.p_loss, self.p_kill, self.react_eps):
            if not 0 <= value <= 1:
                raise ValueError("Probabilities must be in [0,1]")
        if min(self.tau_reveal, self.tau_msg, self.hub_service, self.stagger,
               self.attack_rate, self.spoof_rate, self.congestion_factor, self.conf_sd, self.react_delay) < 0:
            raise ValueError("Rates, delays and scales must be nonnegative")
        if self.tau_stale <= 0 or self.horizon <= 0 or self.react_halflife <= 0 or self.budget < 0:
            raise ValueError("Invalid horizon, expiry, budget or decay")
        if not 0 < self.attack_dur[0] <= self.attack_dur[1] or self.blocked_slow < 1:
            raise ValueError("Invalid attack duration or slowdown")


@dataclass
class Convoy:
    id: int
    target: int
    depart_t: float
    node: int = 0
    alive: bool = True
    delivered: bool = False
    finished_t: float = float("nan")
    nominal: float = 0.0
    travel: float = 0.0
    service: float = 0.0
    surprise_enc: int = 0
    believed_blocked: set = field(default_factory=set)
    enc: int = 0
    hops: int = 0
    wait: float = 0.0
    queued_t: float = 0.0
    path: list = field(default_factory=list)
    edge_entered: float = 0.0
    service_started: object = None
    waiting: bool = False
    cur_edge: int = -1
    own: dict = field(default_factory=dict)    # e -> (blocked, t_obs, conf)
    peer: dict = field(default_factory=dict)
    inbox: list = field(default_factory=list)
    sent: dict = field(default_factory=dict)
    entries: list = field(default_factory=list)   # (t, edge, was_blocked)


def _u(*key):
    return np.random.default_rng(np.random.SeedSequence(list(key))).random()


class Sim:
    def __init__(self, g, cfg, policy, seed):
        self.g, self.cfg, self.policy, self.seed = g, cfg, policy, seed
        ss = lambda tag: np.random.default_rng(np.random.SeedSequence([seed, tag]))
        r = ss(1)
        self.adv_rng = ss(2)
        self.spoof_rng = ss(3)
        tg = r.choice(g.targets, size=cfg.n_convoys)
        dep = np.arange(cfg.n_convoys) * cfg.stagger + r.uniform(0, 1.0, cfg.n_convoys)
        self.cv = [Convoy(i, int(tg[i]), float(dep[i]), node=g.depot) for i in range(cfg.n_convoys)]
        self.t = 0.0
        self.ev = []
        self.event_seq = 0
        self.active = {}                     # e -> (t0, t1)
        self.flow = np.zeros(g.m, int)
        self.use = np.zeros(g.m)             # decayed traffic (reactive adversary)
        self.use_t = 0.0
        self.traffic_history = []
        self.busy = np.zeros(g.n, int)
        self.queue = [deque() for _ in range(g.n)]
        self.trace = []
        self.attack_log = []
        self.stats = dict(msg_sent=0, msg_lost=0, msg_delivered=0, spoof_sent=0,
                          spoof_accepted=0, true_accepted=0, rejected=0, attacks=0)
        self.message_audit = []
        self.decisions = []
        self.suppressed_messages = set()
        self.before_decision = None
        self.closed = False
        self.spoof_seq = 0

    # ---- event plumbing
    def push(self, t, typ, payload=None):
        heapq.heappush(self.ev, (t, self.event_seq, typ, payload))
        self.event_seq += 1

    def observable(self, e, t):
        a = self.active.get(e)
        return a is not None and t >= a[0] + self.cfg.tau_reveal

    def observation_edges(self, cv):
        """Declared sensor coverage; missing edges remain unknown, not known-open."""
        return self.edges_in_radius(cv.node)

    def edges_in_radius(self, node):
        seen, fr, out = {node}, [node], []
        for _ in range(self.cfg.obs_radius):
            nf = []
            for u in fr:
                for e in self.g.out[u]:
                    out.append(e)
                    v = int(self.g.dst[e])
                    if v not in seen:
                        seen.add(v); nf.append(v)
            fr = nf
        return out

    # ---- comms
    def estimated_travel_times(self, cv):
        """Only locally visible flow is available; remote flow is unknown (nominal estimate)."""
        times = self.g.c.copy()
        edges = self.observation_edges(cv)
        if edges:
            times[edges] *= 1 + self.cfg.congestion_factor * self.flow[edges] / self.g.q[edges]
        return times

    @staticmethod
    def message_id(sender, receiver, edge, t, blocked):
        return f"peer:{sender}:{receiver}:{edge}:{float(t).hex()}:{int(blocked)}"

    def broadcast(self, cv, items, t):
        for e, blocked, conf in items:
            for o in self.cv:
                if o.id == cv.id:
                    continue
                # Delivery existence/loss does not depend on iteration counters or
                # recipient survival. Dead recipients simply ignore arrival events.
                mid = self.message_id(cv.id, o.id, e, t, blocked)
                key = int.from_bytes(hashlib.sha256(mid.encode()).digest()[:8], 'big')
                rng = np.random.default_rng(np.random.SeedSequence([self.seed, 5, key]))
                self.stats["msg_sent"] += 1
                loss, score = rng.random(), rng.normal()
                if loss < self.cfg.p_loss:
                    self.stats["msg_lost"] += 1
                    continue
                confidence = float(np.clip(self.cfg.conf_mu + self.cfg.conf_sd * score, 0.05, 1.0))
                self.push(t + self.cfg.tau_msg, MSG,
                          (o.id, dict(id=mid, sender=cv.id, e=e, blocked=blocked,
                                      t_obs=t, genuine=True, conf=confidence)))

    # ---- adversary
    def decayed_use(self, t):
        self.use *= 0.5 ** ((t - self.use_t) / self.cfg.react_halflife)
        self.use_t = t

    def do_attack(self, t):
        c, g, rng = self.cfg, self.g, self.adv_rng
        gap = rng.exponential(1.0 / c.attack_rate)
        u1, u2, u3 = rng.random(3)
        self.push(t + gap, ATTACK)
        if len(self.active) >= c.budget:
            return
        cand = np.array([e for e in range(g.m) if e not in self.active])
        if len(cand) == 0:
            return
        if c.adv == "reactive" and u3 > c.react_eps:
            self.decayed_use(t)
            # Delayed, exponentially decayed observed entries. Live private
            # route plans and future actions are unavailable to the adversary.
            observed = np.zeros(g.m)
            for entered_t, edge in self.traffic_history:
                if entered_t <= t - c.react_delay:
                    observed[edge] += 0.5 ** ((t - c.react_delay - entered_t) / c.react_halflife)
            sc = observed[cand] + 1e-6 * g.rho[cand]
            e = int(cand[int(np.argmax(sc))])
        else:
            w = g.rho[cand]; cdf = np.cumsum(w / w.sum())
            e = int(cand[min(int(np.searchsorted(cdf, u1)), len(cand) - 1)])
        dur = c.attack_dur[0] + u2 * (c.attack_dur[1] - c.attack_dur[0])
        self.active[e] = (t, t + dur)
        self.stats["attacks"] += 1
        self.attack_log.append((round(t, 9), e))
        self.push(t + dur, UNBLOCK, e)

    def do_spoof(self, t):
        c = self.cfg
        gap = self.spoof_rng.exponential(1.0 / c.spoof_rate)
        u = self.spoof_rng.random(3)
        self.push(t + gap, SPOOF)
        seq = self.spoof_seq
        self.spoof_seq += 1
        live = self.cv if c.spoof_mode == "exogenous" else [o for o in self.cv if o.alive and not o.delivered]
        if not live:
            return
        o = live[int(u[0] * len(live))]
        # worst-case spoof: claim a block on an edge of the victim's own least-threat route
        from .graph import dijkstra
        plan = list(range(self.g.m)) if c.spoof_mode == "exogenous" else (
            dijkstra(self.g, o.node, o.target, self.g.c * (1 + 6.0 * self.g.rho)) or [int(u[1] * self.g.m)])
        e = plan[min(int(u[1] * len(plan)), len(plan) - 1)]
        self.stats["spoof_sent"] += 1
        self.push(t + c.tau_msg, MSG, (o.id, dict(id=f"spoof:{seq}:{o.id}", sender=-1, e=e, blocked=True, t_obs=t - 0.5,
                                                  conf=0.4 + 0.6 * u[2], genuine=False)))

    # ---- movement
    def enter_edge(self, cv, e, t):
        g, c = self.g, self.cfg
        if e not in g.out[cv.node] or (not c.allow_base_transit and
                                      int(g.dst[e]) in g.targets and int(g.dst[e]) != cv.target):
            raise ValueError("Policy selected an invalid next-hop edge")
        T = g.c[e] * (1 + c.congestion_factor * self.flow[e] / g.q[e])
        self.flow[e] += 1
        cv.cur_edge = e
        cv.edge_entered = t
        cv.path.append(e)
        cv.nominal += g.c[e]
        self.decayed_use(t)
        self.use[e] += 1.0
        self.traffic_history.append((t, e))
        blocked = e in self.active
        cv.entries.append((t, e, blocked))
        if blocked:
            cv.enc += 1
            cv.surprise_enc += int(e not in cv.believed_blocked)
            if _u(self.seed, 4, cv.id, cv.hops) < c.p_kill:
                cv.hops += 1
                self.push(t + 0.5 * T, DEATH, cv.id)
                return
            T *= c.blocked_slow
        cv.hops += 1
        self.push(t + T, ARRIVE, (cv.id, int(g.dst[e])))

    def leave_edge(self, cv):
        if cv.cur_edge >= 0:
            cv.travel += self.t - cv.edge_entered
            self.flow[cv.cur_edge] -= 1
            cv.cur_edge = -1

    def start_service(self, cv, t):
        self.busy[cv.node] += 1
        cv.service_started = t
        cv.waiting = False
        cv.wait += t - cv.queued_t
        self.push(t + self.cfg.hub_service, SERVE_END, cv.id)

    def depart(self, cv, t):
        if self.before_decision is not None:
            self.before_decision(self, cv, t)
        e = self.policy.decide(self, cv, t)
        self.enter_edge(cv, e, t)

    # ---- main loop
    def run(self, until=None):
        """Run to completion, or (until=T) pause just before time T so the live state can be inspected; call run() again to resume."""
        if self.closed:
            return self.summary()
        if not getattr(self, "_started", False):
            self._started = True
            for cv in self.cv:
                self.push(cv.depart_t, DEPART, cv.id)
            if self.cfg.attack_rate > 0 and self.cfg.budget > 0:
                self.push(self.adv_rng.exponential(1.0 / self.cfg.attack_rate), ATTACK)
            if self.cfg.spoof_rate > 0:
                self.push(self.spoof_rng.exponential(1.0 / self.cfg.spoof_rate), SPOOF)
        remaining = sum(1 for c in self.cv if c.alive and not c.delivered)
        while self.ev and remaining > 0:
            if until is not None and self.ev[0][0] > until:
                self.t = min(until, self.cfg.horizon); return None
            t, _, typ, p = heapq.heappop(self.ev)
            if t > self.cfg.horizon:
                self.t = self.cfg.horizon
                break
            self.t = t
            if typ == DEPART:
                self.depart(self.cv[p], t)
            elif typ == ARRIVE:
                cid, node = p
                cv = self.cv[cid]
                self.leave_edge(cv)
                cv.node = node
                if node == cv.target:
                    cv.delivered = True; cv.finished_t = t; remaining -= 1
                    getattr(self.policy, 'terminal', lambda *a, **kw: None)(self, cv, t, False)
                else:
                    cv.queued_t = t
                    cv.waiting = True
                    if self.busy[node] < self.cfg.hub_cap:
                        self.start_service(cv, t)
                    else:
                        self.queue[node].append(cv)
            elif typ == SERVE_END:
                cv = self.cv[p]
                self.busy[cv.node] -= 1
                cv.service += t - cv.service_started
                cv.service_started = None
                if self.queue[cv.node]:
                    self.start_service(self.queue[cv.node].popleft(), t)
                self.depart(cv, t)
            elif typ == DEATH:
                cv = self.cv[p]
                self.leave_edge(cv)
                cv.alive = False; cv.finished_t = t; remaining -= 1
                getattr(self.policy, 'terminal', lambda *a, **kw: None)(self, cv, t, True)
            elif typ == ATTACK:
                self.do_attack(t)
            elif typ == UNBLOCK:
                self.active.pop(p, None)
            elif typ == SPOOF:
                self.do_spoof(t)
            elif typ == MSG:
                cid, m = p
                o = self.cv[cid]
                if o.alive and not o.delivered:
                    o.inbox.append(m)
                    self.stats["msg_delivered"] += 1
        # A finite-horizon non-delivery is an explicit failure, not a silently
        # discarded training transition. Never close during a requested pause.
        self.closed = True
        for cv in self.cv:
            if cv.alive and not cv.delivered:
                getattr(self.policy, 'terminal', lambda *a, **kw: None)(self, cv, self.t, False, truncated=True)
        return self.summary()

    def summary(self):
        rows = []
        for cv in self.cv:
            ps = [1 - self.g.rho[e] for e in cv.path]
            rows.append(dict(
                route_surv=float(np.mean(ps)) if ps else float("nan"),
                max_thr=float(max((self.g.rho[e] for e in cv.path), default=float("nan"))),
                convoy=cv.id, target=cv.target, depart_t=cv.depart_t,
                survived=int(cv.delivered), delivered=int(cv.delivered),
                destroyed=int(not cv.alive), censored=int(cv.alive and not cv.delivered),
                nominal=cv.nominal,
                nominal_optimal=optimal_nominal_cost(self.g, self.g.depot, cv.target),
                elapsed=(cv.finished_t if not np.isnan(cv.finished_t) else max(self.t, cv.depart_t)) - cv.depart_t,
                travel=cv.travel + (max(0., self.t - cv.edge_entered) if cv.cur_edge >= 0 else 0.),
                service=cv.service + (self.t - cv.service_started if cv.service_started is not None else 0.),
                realized=(cv.finished_t - cv.depart_t) if cv.delivered else float("nan"),
                blocked_enc=int(cv.enc), surprise_blocked_enc=int(cv.surprise_enc), hops=cv.hops, wait=cv.wait + (self.t - cv.queued_t if cv.waiting else 0.)))
        return dict(rows=rows, trace=self.trace, decisions=self.decisions,
                    message_audit=self.message_audit, attacks=self.attack_log,
                    stats=dict(self.stats), complete=all(not c.alive or c.delivered for c in self.cv),
                    config=__import__('dataclasses').asdict(self.cfg), seed=self.seed, end_time=self.t)
