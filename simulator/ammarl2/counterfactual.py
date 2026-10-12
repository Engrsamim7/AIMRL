"""Exact deterministic single-message intervention for a frozen evaluation policy.

Fork immediately before the receiver's decision and suppress one delivered
message. All other pre-intervention state is copied, including RNGs and event
queue. Later actions, observations, honest transmissions and congestion may
change causally. Random attacks and exogenous spoofs share random tapes; reactive
attacks and targeted spoofing are explicitly disallowed for this controlled FIR.
"""
import copy
import heapq
import pandas as pd
from .sim import Sim, DEPART


def single_message_effects(graph, cfg, policy, seed, max_messages=None, simulator_factory=None):
    if policy.comm not in ('all', 'gate'):
        raise ValueError('FIR requires a communicating policy')
    if getattr(policy, 'train', False):
        raise ValueError('Counterfactual evaluation requires a frozen policy')
    if cfg.adv != 'random' or cfg.spoof_mode != 'exogenous':
        raise ValueError('Controlled FIR requires random attacks and exogenous spoofing')
    if max_messages is not None and max_messages < 1:
        raise ValueError('max_messages must be positive or None')
    snapshots = []
    selected = 0

    def capture(sim, cv, t):
        nonlocal selected
        if not cv.inbox or selected == max_messages:
            return
        messages = [dict(m) for m in cv.inbox]
        if max_messages is not None:
            messages = messages[:max_messages-selected]
        hook = sim.before_decision
        sim.before_decision = None
        try:
            shadow = copy.deepcopy(sim)
        finally:
            sim.before_decision = hook
        # Current event was popped and its service bookkeeping already executed.
        # Reinsert only its pending routing decision ahead of same-time events.
        heapq.heappush(shadow.ev, (t, -1, DEPART, cv.id))
        snapshots.append((shadow, cv.id, t, messages))
        selected += len(messages)

    factual = (simulator_factory or Sim)(graph, cfg, copy.deepcopy(policy), seed)
    factual.before_decision = capture
    result = factual.run()
    factual.before_decision = None
    factual_rows = {r['convoy']: r for r in result['rows']}
    effects = []
    for state, convoy_id, t, messages in snapshots:
        for message in messages:
            shadow = copy.deepcopy(state)
            shadow.suppressed_messages.add(message['id'])
            alternative = shadow.run()
            common_end = min(factual.t, shadow.t)
            # Check all attacks in the shared time interval, not just a few.
            fa = [a for a in factual.attack_log if a[0] <= common_end]
            sa = [a for a in shadow.attack_log if a[0] <= common_end]
            if fa != sa:
                raise AssertionError('Exogenous attack replay diverged')
            alt_rows = {r['convoy']: r for r in alternative['rows']}
            a, b = factual_rows[convoy_id], alt_rows[convoy_id]
            ds = a['delivered'] - b['delivered']
            db = a['blocked_enc'] - b['blocked_enc']
            dr = a['route_surv'] - b['route_surv']
            dsurprise = a['surprise_blocked_enc'] - b['surprise_blocked_enc']
            effects.append(dict(message_id=message['id'], convoy=convoy_id,
                                edge=message['e'], decision_t=t,
                                delta_delivery=ds, delta_blocked_encounters=db,
                                delta_route_surv=dr, delta_surprise_blocked_encounters=dsurprise,
                                failed_delivery_information=int(db >= 0 and ds <= 0),
                                failed_route_information=int(dsurprise >= 0 and dr <= 0) if pd.notna(dr) else None,
                                changed_receiver_path=a['nominal'] != b['nominal'] or
                                factual.cv[convoy_id].path != shadow.cv[convoy_id].path,
                                delta_episode_deliveries=sum(r['delivered'] for r in result['rows']) -
                                sum(r['delivered'] for r in alternative['rows'])))
    total_processed = len(result['message_audit'])
    metadata = dict(intervention='one delivered message suppressed before receiver decision',
                    selected_messages=len(effects), processed_messages=total_processed,
                    selection='all' if max_messages is None else 'first messages in decision order (diagnostic subset)',
                    fir_delivery=sum(r['failed_delivery_information'] for r in effects) / len(effects) if effects else None,
                    fir_route=pd.DataFrame(effects).failed_route_information.mean() if effects else None)
    return pd.DataFrame(effects), metadata, result
