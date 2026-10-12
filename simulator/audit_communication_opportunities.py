"""Diagnostic replay of fixed schedules; never supplies private state to actors.

Instrumentation uses no random draws and changes no simulator event or action.
Shallow simulator forks with isolated convoy/log state support one-decision
probes. These probes are not full-trajectory causal effects. Separate complete
episode forks suppress whole inbox batches under exogenous adversaries only.
"""
import argparse
import copy
import hashlib
import heapq
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from adaptive_gate import AdaptiveGate
from ammarl2.graph import dijkstra
from ammarl2.metrics import episode_metrics
from ammarl2.reviewer import ReviewerSim, cc2_graph, m4_sensing
from ammarl2.sim import Cfg, DEPART, MSG
from run_adaptive_experiments import (
    MixedSpoofSim, REGIMES, adaptive, config, controlled_factory,
    fingerprint, graph_cases,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'simulator/out/adaptive-gate-v2'
METHODS = [('SOFT-NC', 'none'), ('SOFT-ALL', 'all'), ('VALUE-GATE', 'value')]


def decision_probe(sim, cv, t, erase_history=False):
    """Execute policy on an isolated convoy without entering an edge."""
    shadow = copy.copy(sim)
    other = copy.deepcopy(cv)
    other.inbox = []
    if erase_history:
        other.peer = {}
        if hasattr(other, 'value_state'):
            del other.value_state
    shadow.cv = list(sim.cv)
    shadow.cv[cv.id] = other
    shadow.stats = dict(sim.stats)
    shadow.trace, shadow.decisions, shadow.message_audit = [], [], []
    shadow.broadcast = lambda *args: None
    edge = shadow.policy.decide(shadow, other, t)
    _, _, weights = shadow.policy.distribution(shadow, other, t)
    route = dijkstra(sim.g, other.node, other.target, weights) or []
    return edge, route, weights, other


class AuditMixin:
    def __init__(self, *args, **kwargs):
        self.init_audit()
        super().__init__(*args, **kwargs)

    def init_audit(self):
        self.envelopes = []
        self.opportunities = []
        self.action_probes = []

    def push(self, t, typ, payload=None):
        super().push(t, typ, payload)
        if typ == MSG:
            cid, packet = payload
            # Keep the same packet reference: MixedSpoofSim modifies the public
            # payload after scheduling it. Finalized below, never changed here.
            self.envelopes.append((float(t), int(cid), packet))

    def depart(self, cv, t):
        packets = [dict(m) for m in cv.inbox]
        old, route, weights, perceived = decision_probe(self, cv, t)
        local, _, _, _ = decision_probe(self, cv, t, erase_history=True)
        first = len(self.message_audit)
        drafts = []
        for m in packets:
            e = m['e']
            age = t - m['t_obs']
            own = perceived.own.get(e)
            local_newer = own is not None and own[1] >= m['t_obs'] and 0 <= t-own[1] <= self.cfg.tau_stale
            fresh = 0 <= age <= self.cfg.tau_stale
            relevant = self.policy.relevant(self, perceived, e, route)
            on_route = e in route
            alternative = dijkstra(self.g, cv.node, cv.target, weights, banned={e}) if on_route else None
            # All current-state truth below is evaluator-only and is recorded
            # AFTER public policy probes. It never changes admission or actions.
            active = e in self.active
            opportunity = bool(m['genuine'] and m['blocked'] and fresh and not local_newer and on_route and alternative is not None)
            drafts.append(dict(
                id=m['id'], convoy=cv.id, edge=e, node=cv.node,
                decision_t=t, t_obs=m['t_obs'], age=age,
                arrival_t=m['t_obs'] + self.cfg.tau_msg if m['genuine'] else np.nan,
                genuine=bool(m['genuine']), blocked_report=bool(m['blocked']),
                sender=m.get('sender'), fresh=fresh, local_newer=local_newer,
                reachable=relevant, on_without_inbox_route=on_route,
                alternative_exists=alternative is not None,
                alternative_extra_model_cost=(sum(weights[a] for a in alternative)-sum(weights[a] for a in route)) if alternative is not None else np.nan,
                active_at_decision=active,
                alternative_clear_now=(not any(a in self.active for a in alternative)) if alternative is not None else False,
                structural_warning_opportunity=opportunity,
                current_hazard_opportunity=opportunity and active,
            ))
        super().depart(cv, t)
        actual = cv.path[-1]
        audits = {m['id']: m for m in self.message_audit[first:]}
        for d in drafts:
            a = audits.get(d['id'], {})
            d.update(reason=a.get('reason', 'not_processed'),
                     estimated_route_regret=a.get('estimated_route_regret', np.nan),
                     innovation=a.get('innovation', np.nan),
                     new_inbox_changes_next_edge=actual != old,
                     all_history_changes_next_edge=actual != local)
            self.opportunities.append(d)
        self.action_probes.append(dict(
            convoy=cv.id, t=t, node=cv.node, edge=actual,
            without_inbox_edge=old, local_only_edge=local, inbox_size=len(packets),
            new_inbox_changes_next_edge=actual != old,
            all_history_changes_next_edge=actual != local,
            local_only_selected_edge_active=local in self.active,
            selected_edge_active=actual in self.active,
        ))

    def finalized_envelopes(self):
        processed = {(p['id'], p['convoy']): p for p in self.opportunities}
        records = []
        for arrival, cid, m in self.envelopes:
            cv = self.cv[cid]
            decision = processed.get((m['id'], cid))
            entries = [entered for entered, e, _ in cv.entries if e == m['e'] and entered >= m['t_obs']]
            records.append(dict(
                id=m['id'], convoy=cid, edge=m['e'], t_obs=m['t_obs'], arrival_t=arrival,
                genuine=bool(m['genuine']), blocked_report=bool(m['blocked']),
                processed=decision is not None,
                decision_t=decision['decision_t'] if decision else np.nan,
                pending_at_episode_end=decision is None and arrival <= self.t,
                scheduled_after_episode_end=arrival > self.t,
                receiver_finished_by_arrival=bool(np.isfinite(cv.finished_t) and cv.finished_t <= arrival),
                traversed_reported_edge_after_observation=bool(entries),
                entered_reported_edge_before_arrival=bool(entries and min(entries) < arrival),
            ))
        return records


class AuditedMixed(AuditMixin, MixedSpoofSim):
    pass


class AuditedReviewer(AuditMixin, ReviewerSim):
    pass


def instrument_control(sim):
    sim.__class__ = AuditedReviewer
    sim.init_audit()
    for t, _, typ, payload in sim.ev:
        if typ == MSG:
            cid, m = payload
            sim.envelopes.append((float(t), int(cid), m))
    return sim


def check_original(result, expected, convoy_expected):
    """Prove instrumented replay reproduces physical metrics and comm counts."""
    actual = dict(episode_metrics(result['rows']), **result['stats'])
    for key in expected.index:
        if key not in actual:
            continue
        x, y = actual[key], expected[key]
        if isinstance(x, bool):
            assert x == (str(y).lower() == 'true' if isinstance(y, str) else bool(y)), key
        else:
            assert np.isclose(x, y, rtol=1e-11, atol=1e-11, equal_nan=True), (key, x, y)
    if convoy_expected is not None:
        for row in result['rows']:
            expected_row = convoy_expected.loc[row['convoy']]
            for key, value in row.items():
                if key == 'convoy':
                    assert value == expected_row.name
                    continue
                assert np.isclose(value, expected_row[key], rtol=1e-11, atol=1e-11, equal_nan=True), (key, value, expected_row[key])


def emit(out, key, sim, result, first):
    for name, records in [
        ('packets', sim.opportunities), ('envelopes', sim.finalized_envelopes()),
        ('decisions', sim.action_probes), ('convoys', result['rows']),
    ]:
        if not records:
            continue
        frame = pd.DataFrame(dict(**key, **r) for r in records)
        path = out / (name+'.csv')
        frame.to_csv(path, index=False, mode='a' if path.exists() else 'w', header=not path.exists())


def batch_effects(g, cfg, policy, seed, sensing):
    """Complete-episode suppression of all delivered packets in one inbox.

    Maintains previously admitted reports. Selection: all nonempty inboxes in
    the declared first-five-episode diagnostic subset, without outcome selection.
    """
    if cfg.adv != 'random' or cfg.spoof_mode != 'exogenous':
        raise ValueError('Batch causal replay requires exogenous adversaries')
    snapshots = []
    def capture(sim, cv, t):
        if not cv.inbox:
            return
        hook = sim.before_decision
        sim.before_decision = None
        try:
            shadow = copy.deepcopy(sim)
        finally:
            sim.before_decision = hook
        heapq.heappush(shadow.ev, (t, -1, DEPART, cv.id))
        snapshots.append((shadow, cv.id, t, [m['id'] for m in cv.inbox]))
    sim = MixedSpoofSim(g, cfg, copy.deepcopy(policy), seed, sensing)
    sim.before_decision = capture
    factual = sim.run()
    rows = []
    for shadow, cid, t, ids in snapshots:
        shadow.suppressed_messages.update(ids)
        other = shadow.run()
        common = min(sim.t, shadow.t)
        assert [a for a in sim.attack_log if a[0] <= common] == [a for a in shadow.attack_log if a[0] <= common]
        a, b = factual['rows'][cid], other['rows'][cid]
        rows.append(dict(convoy=cid, t=t, packets_removed=len(ids),
                         changed_receiver_path=sim.cv[cid].path != shadow.cv[cid].path,
                         delta_delivery=a['delivered']-b['delivered'],
                         delta_episode_deliveries=sum(r['delivered'] for r in factual['rows'])-sum(r['delivered'] for r in other['rows']),
                         delta_nominal=a['nominal']-b['nominal'],
                         delta_realized_common_survivor=a['realized']-b['realized'] if a['delivered'] and b['delivered'] else np.nan))
    return rows


def run(out, graphs=10, episodes=30):
    start = time.perf_counter()
    source_hash = fingerprint()
    archived = json.loads((SOURCE/'pipeline.json').read_text())
    assert archived['status'] == 'completed' and archived['source_hash'] == source_hash
    params = json.loads((SOURCE/'selected.json').read_text())['parameters']
    keys = ['family', 'graph', 'regime', 'episode', 'method']
    expected = pd.read_csv(SOURCE/'episodes.csv')
    expected = expected[expected.method.isin([m for m, _ in METHODS])].set_index(keys).sort_index()
    convoy_expected = pd.read_csv(SOURCE/'convoys.csv')
    convoy_expected = convoy_expected[convoy_expected.method.isin([m for m, _ in METHODS])].set_index(keys+['convoy']).sort_index()
    checked = 0
    for gid, family, g in graph_cases(False, graphs):
        for ri, regime in enumerate(REGIMES):
            for ep in range(episodes):
                for name, mode in METHODS:
                    key = dict(family=family, graph=gid, regime=regime, episode=ep, method=name)
                    index = tuple(key[k] for k in keys)
                    sim = AuditedMixed(g, config(regime), adaptive(name, params, mode=mode),
                                       14000000+gid*1000+ri*100+ep, m4_sensing(g, True))
                    result = sim.run()
                    check_original(result, expected.loc[index], convoy_expected.loc[index])
                    checked += 1
                    emit(out, dict(scope='network', **key), sim, result, checked == 1)
        print(f'Checked {family} graph {gid}; {checked} unchanged episodes', flush=True)
    controls = pd.read_csv(SOURCE/'controlled_episodes.csv').set_index(['case','delay','loss','episode','method'])
    control_count = 0
    for case in ['accurate', 'low-clear', 'high-clear', 'impersonated-clear']:
        for delay in [1., 4.]:
            for loss in [0., .2]:
                for ep in range(50):
                    hot = 4 if ep % 2 == 0 else 5
                    g, _, _ = cc2_graph(hot)
                    cfg = Cfg(n_convoys=3, stagger=0, hub_service=.25, attack_rate=0,
                              budget=0, tau_msg=delay, p_loss=loss, tau_reveal=0, p_kill=1)
                    for name, mode in METHODS:
                        p = adaptive(name, params, mode=mode, forced_scout_routes=True)
                        sim = controlled_factory(g, cfg, p, 15000000+ep, hot=hot, case=case)
                        sim.ev = [(2.+delay if typ == MSG and payload[1].get('genuine') is False else t,
                                   seq, typ, payload) for t, seq, typ, payload in sim.ev]
                        heapq.heapify(sim.ev)
                        sim = instrument_control(sim)
                        result = sim.run()
                        check_original(result, controls.loc[(case,delay,loss,ep,name)], None)
                        key = dict(scope='controlled',family=case,graph=0,regime=f'delay={delay},loss={loss}',episode=ep,method=name)
                        emit(out, key, sim, result, False)
                        control_count += 1
        print(f'Checked control {case}', flush=True)
    batches = []
    for gid, family, g in graph_cases(False, 1):
        for ri, regime in enumerate(REGIMES[:3]):
            for ep in range(5):
                for name, mode in METHODS[1:]:
                    effects = batch_effects(g, config(regime), adaptive(name, params, mode=mode),
                                           14000000+gid*1000+ri*100+ep, m4_sensing(g, True))
                    batches.extend(dict(family=family, graph=gid, regime=regime, episode=ep, method=name, **r) for r in effects)
        print(f'Batch causal audit {family}', flush=True)
    pd.DataFrame(batches).to_csv(out/'batch_effects.csv', index=False)
    assert fingerprint() == source_hash
    manifest = dict(status='completed', source_hash=source_hash,
                    audit_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    reproduced_network_episodes=checked, reproduced_control_episodes=control_count,
                    batch_interventions=len(batches), arguments=dict(graphs=graphs,episodes=episodes),
                    seconds=time.perf_counter()-start,
                    scope='Diagnostic replay of existing frozen test schedules, not new evidence of superiority or training data',
                    private_truth='Evaluator-only instantaneous active edges; never passed to policy or gate',
                    batch_subset='All nonempty inboxes in first five episodes on original and first graph of each synthetic family; three exogenous regimes; both communicating soft methods',
                    limitations=['One-decision probes keep factual prior movement and local observation history',
                                 'Current-hazard opportunity is not an optimal-control bound; hazards may change before arrival',
                                 'No causal claims for reactive/targeted regime',
                                 'Envelope log excludes lost packets and records pending scheduled arrivals separately',
                                 'Genuine warns about perceived revealed state, not perfect ground truth'])
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='out/communication-opportunity-audit')
    ap.add_argument('--graphs', type=int, default=10)
    ap.add_argument('--episodes', type=int, default=30)
    args = ap.parse_args()
    if not 1 <= args.graphs <= 10 or not 1 <= args.episodes <= 30:
        ap.error('Audit must stay within archived schedules: graphs 1..10; episodes 1..30')
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=False)
    run(out, args.graphs, args.episodes)


if __name__ == '__main__':
    main()
