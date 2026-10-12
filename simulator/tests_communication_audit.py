import copy
import numpy as np
import pytest

from audit_communication_opportunities import (
    AuditedMixed, batch_effects, decision_probe, instrument_control,
)
from ammarl2.reviewer import cc2_graph, m4_sensing, original_graph
from run_adaptive_experiments import adaptive, config, controlled_factory, MixedSpoofSim

PARAMS = dict(risk_aversion=0., age_scale=2., min_value=.02)


def test_instrumentation_preserves_all_physical_and_policy_outputs():
    g = original_graph()
    for regime in ['reliable', 'heavy-spoof', 'reactive-spoof']:
        for mode in ['none', 'all', 'value']:
            p = adaptive('test', PARAMS, mode=mode)
            c = config(regime)
            a = MixedSpoofSim(g, c, copy.deepcopy(p), 14000201, m4_sensing(g, True)).run()
            b = AuditedMixed(g, c, copy.deepcopy(p), 14000201, m4_sensing(g, True)).run()
            assert a['stats'] == b['stats']
            assert a['trace'] == b['trace']
            assert a['message_audit'] == b['message_audit']
            for left, right in zip(a['rows'], b['rows']):
                for k in left:
                    assert np.isclose(left[k], right[k], equal_nan=True)


def test_probe_does_not_mutate_events_convoy_or_gate_state():
    g = original_graph()
    s = AuditedMixed(g, config('heavy-spoof'), adaptive('test', PARAMS), 19, m4_sensing(g, True))
    before = copy.deepcopy(s.cv[0].__dict__)
    ev = copy.deepcopy(s.ev)
    counts = dict(s.stats)
    decision_probe(s, s.cv[0], 0.)
    decision_probe(s, s.cv[0], 0., erase_history=True)
    assert s.cv[0].__dict__ == before
    assert s.ev == ev and s.stats == counts
    assert s.trace == [] and s.envelopes == []


def test_opportunity_audit_detects_known_timely_scout_benefit():
    from ammarl2.sim import Cfg
    g, _, _ = cc2_graph(4)
    c = Cfg(n_convoys=3, stagger=0, hub_service=.25, attack_rate=0, budget=0,
            tau_msg=1, tau_reveal=0, p_kill=1)
    s = instrument_control(controlled_factory(g,c,adaptive('value',PARAMS,forced_scout_routes=True),15000000,case='accurate'))
    result = s.run()
    assert sum(r['delivered'] for r in result['rows']) == 3
    useful = [r for r in s.opportunities if r['current_hazard_opportunity']]
    assert len(useful) == 2
    assert all(r['new_inbox_changes_next_edge'] for r in useful)
    assert all(r['alternative_clear_now'] for r in useful)


def test_batch_replay_rejects_endogenous_attack_attribution():
    g = original_graph()
    with pytest.raises(ValueError, match='exogenous'):
        batch_effects(g, config('reactive-spoof'), adaptive('value',PARAMS),19,m4_sensing(g,True))


def test_warning_action_intervention_applies_once_and_resumes_policy():
    from audit_warning_response import OneAction
    from ammarl2.sim import Cfg
    g, _, _ = cc2_graph(4)
    c = Cfg(n_convoys=3, stagger=0, hub_service=.25, attack_rate=0, budget=0,
            tau_msg=1, tau_reveal=0, p_kill=1)
    s = controlled_factory(g,c,adaptive('local',PARAMS,mode='none',forced_scout_routes=True),19)
    cv = s.cv[1];cv.node=2
    s.policy = OneAction(s.policy,1,2.,6,4)
    assert s.policy.decide(s,cv,2.) == 6
    assert s.policy.used and s.decisions[-1]['edge'] == 6
    assert s.policy.decide(s,cv,2.) == 4
