"""Shared local belief processing and auditable communication filtering.

The gate is a hypothesis, not a guarantee of better routing. All heuristic
communication variants share the same hazard response strength.
"""
from dataclasses import dataclass
import numpy as np
from .graph import dijkstra, dists


@dataclass
class Policy:
    name: str
    weights: str = 'c'
    alpha: float = 6.0
    use_obs: bool = False
    comm: str = 'none'
    gate_fresh: bool = True
    gate_rel: bool = True
    gate_conf: bool = True
    eta: float = 1.0
    scaling: str = 'travel'  # travel: eta * estimated corridor traversal time
    kappa_min: float = 0.60
    noise: float = 0.0
    response_strength: float = 12.0  # additive cost for believed blocked edges
    response_mode: str = 'penalty'   # penalty | avoid (explicit legacy-style comparator)
    relevance_scope: str = 'route'   # route | reachable (all possible future routes)

    def __post_init__(self):
        if self.comm not in ('none', 'all', 'gate', 'oracle'):
            raise ValueError('Unknown communication mode')
        if self.scaling not in ('static', 'scaled', 'travel'):
            raise ValueError('Unknown freshness rule')
        if self.response_mode not in ('penalty', 'avoid'):
            raise ValueError('Unknown hazard response')
        if self.relevance_scope not in ('route', 'reachable'):
            raise ValueError('Unknown relevance scope')
        if self.response_strength < 0 or self.eta <= 0 or not 0 <= self.kappa_min <= 1:
            raise ValueError('Invalid policy parameters')

    def w(self, g):
        return g.c.copy() if self.weights == 'c' else g.c * (1 + self.alpha * g.rho)

    def banned(self, belief, t, tau_stale):
        return {e for e, (b, to, cf) in belief.items() if b and 0 <= t - to <= tau_stale}

    def freshness_limit(self, sim, cv, e):
        if self.scaling == 'static':
            return self.eta * sim.cfg.tau_stale
        travel = sim.estimated_travel_times(cv)
        if self.scaling == 'scaled':  # historical ETA rule, retained as a comparator
            eta_time = dists(sim.g, cv.node, travel)[sim.g.src[e]] + sim.cfg.tau_msg
        else:
            eta_time = travel[e]
        return min(sim.cfg.tau_stale, self.eta * eta_time)

    def response_weights(self, w, blocked):
        result = w.copy()
        if self.response_mode == 'penalty' and blocked:
            result[list(blocked)] += self.response_strength
        return result

    def relevant(self, sim, cv, e, plan):
        if self.relevance_scope == 'route':
            return e in plan
        # Public topology only; covers alternatives a learned actor may choose.
        return (dijkstra(sim.g, cv.node, int(sim.g.src[e]), sim.g.c) is not None
                and dijkstra(sim.g, int(sim.g.dst[e]), cv.target, sim.g.c) is not None)

    def decide(self, sim, cv, t):
        g, cfg = sim.g, sim.cfg
        w = self.w(g)
        if self.noise > 0:
            w *= np.exp(self.noise * np.random.default_rng([sim.seed, cv.id, int(t * 1000)]).normal(size=g.m))
        if self.comm == 'oracle':
            # True state at decision time, including unrevealed attacks. Diagnostic,
            # not an optimal control upper bound under congestion/reactive attacks.
            ban = set(sim.active)
            cv.believed_blocked = ban
            return self._route(g, cv, w, ban)
        if self.use_obs:
            newly = []
            for e in sim.observation_edges(cv):
                blocked = sim.observable(e, t)
                prev = cv.own.get(e)
                cv.own[e] = (blocked, t, 1.0)
                if self.comm != 'none' and (
                    blocked and (prev is None or not prev[0] or t - cv.sent.get(e, -1e9) > cfg.tau_stale)
                    or not blocked and prev is not None and prev[0]
                ):
                    newly.append((e, blocked, 1.0))
                    cv.sent[e] = t
            if newly:
                sim.broadcast(cv, newly, t)
        # Retained messages must still be fresh at departure, after queueing/service.
        cv.peer = {e: v for e, v in cv.peer.items()
                   if 0 <= t - v[1] <= cfg.tau_stale and
                   (self.comm != 'gate' or not self.gate_fresh or
                    t - v[1] <= self.freshness_limit(sim, cv, e))}
        own_ban = self.banned(cv.own, t, cfg.tau_stale)
        plan = dijkstra(g, cv.node, cv.target, self.response_weights(w, own_ban),
                        own_ban if self.response_mode == 'avoid' else ()) or []
        n_in, accepted = len(cv.inbox), []
        if self.comm in ('all', 'gate'):
            for m in sorted(cv.inbox, key=lambda m: (m['t_obs'], m.get('id', ''))):
                e, age = m['e'], t - m['t_obs']
                current = max(cv.own.get(e, (0, -1e9, 0))[1], cv.peer.get(e, (0, -1e9, 0))[1])
                reason = 'accepted'
                if m.get('id') in sim.suppressed_messages:
                    reason = 'suppressed'
                elif age < 0 or age > cfg.tau_stale:
                    reason = 'stale'
                elif m['t_obs'] <= current:
                    reason = 'superseded'
                elif self.comm == 'gate':
                    if self.gate_fresh and age > self.freshness_limit(sim, cv, e):
                        reason = 'freshness'
                    elif self.gate_conf and m['conf'] < self.kappa_min:
                        reason = 'confidence'
                    elif self.gate_rel and m['blocked'] and not self.relevant(sim, cv, e, plan):
                        reason = 'relevance'
                sim.message_audit.append(dict(id=m.get('id'), convoy=cv.id, edge=e,
                                             decision_t=t, t_obs=m['t_obs'], age=age,
                                             reason=reason, genuine=m['genuine']))
                if reason != 'accepted':
                    sim.stats['rejected'] += 1
                    continue
                cv.peer[e] = (m['blocked'], m['t_obs'], m['conf'])
                accepted.append(m.get('id'))
                sim.stats['true_accepted' if m['genuine'] else 'spoof_accepted'] += 1
        cv.inbox.clear()
        merged = dict(cv.peer)
        for e, value in cv.own.items():
            if e not in merged or value[1] >= merged[e][1]:
                merged[e] = value
        # Even clear reports expire: unknown is distinct from known-open.
        merged = {e: v for e, v in merged.items() if 0 <= t - v[1] <= cfg.tau_stale}
        ban = self.banned(merged, t, cfg.tau_stale) if self.use_obs or self.comm != 'none' else set()
        cv.believed_blocked = set(ban)
        e_sel = self.select(sim, cv, w, ban, merged, t)
        # This heuristic-only reference is a diagnostic, never single-message FIR.
        e_own = self._route(g, cv, w, own_ban) if accepted else e_sel
        sim.trace.append((cv.id, t, cv.node, e_sel, e_own, n_in, len(accepted)))
        sim.decisions.append(dict(convoy=cv.id, t=t, node=cv.node, edge=e_sel,
                                  accepted_ids=accepted, blocked_belief=sorted(ban)))
        return e_sel

    def select(self, sim, cv, w, ban, merged, t):
        return self._route(sim.g, cv, w, ban)

    def _route(self, g, cv, w, ban):
        return self._first(g, cv, self.response_weights(w, ban),
                           ban if self.response_mode == 'avoid' else ())

    @staticmethod
    def _first(g, cv, w, ban):
        path = dijkstra(g, cv.node, cv.target, w, ban)
        if path is None:
            path = dijkstra(g, cv.node, cv.target, w)
        if not path:
            raise ValueError('No reachable outgoing action for this convoy target')
        return path[0]


def standard_methods():
    return {
        'B1': Policy('B1'),
        'B2': Policy('B2', weights='threat'),
        'B3': Policy('B3', use_obs=True),
        'NC': Policy('NC', weights='threat', use_obs=True),
        'COMM-ALL': Policy('COMM-ALL', weights='threat', use_obs=True, comm='all'),
        'GATE': Policy('GATE', weights='threat', use_obs=True, comm='gate'),
        'ORACLE': Policy('ORACLE', weights='threat', use_obs=True, comm='oracle', response_mode='avoid'),
    }
