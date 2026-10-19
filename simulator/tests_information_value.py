import numpy as np
import pytest
from information_value_reference import Contract,exact_cell,current_report_probability,report_posterior,transition_probability,report_value,grid
from original_tabular import FixedGateAgent
from audit_tabular_decisions import score_probe


def test_exact_distribution_and_bayes_policy_domination_across_declared_grid():
    cells=list(grid());assert len(cells)==432
    for c in cells:
        row,branches=exact_cell(c)
        assert np.isclose(sum(r['probability'] for r in branches),1.)
        assert all(row['AGE_AWARE_expected_cost']<=row[m+'_expected_cost']+1e-12 for m in ['ALL','FRC','NONE'])
        assert row['information_gain']>=-1e-12


def test_persistent_honest_observation_never_decays_just_because_of_age():
    assert current_report_probability(1,.3,1.,100.,0.)==1.
    assert current_report_probability(0,.3,1.,100.,0.)==0.


def test_old_reports_revert_to_prior_under_rapid_change():
    assert np.isclose(current_report_probability(1,.3,.75,1000.,.5),.3)
    assert np.isclose(current_report_probability(0,.3,.75,1000.,.5),.3)


def test_probability_follows_ctmc_semigroup():
    p0=report_posterior(1,.3,.75)
    from information_value_reference import propagate_probability as propagate
    assert np.isclose(propagate(propagate(p0,2.,.3,.1),4.,.3,.1),propagate(p0,6.,.3,.1))


def test_full_current_local_observation_makes_every_filter_equivalent():
    for c in grid():
        if not c.own_visible:continue
        row,_=exact_cell(c)
        assert np.allclose([row[m+'_expected_cost'] for m in ['ALL','FRC','NONE','AGE_AWARE']],row['NONE_expected_cost'])
        assert row['gate_action_change_probability']==0.


def test_fixed_freshness_can_help_hurt_and_tie_without_parameter_selection():
    differences=np.array([exact_cell(c)[0]['frc_minus_all'] for c in grid()])
    assert np.any(differences< -1e-10) and np.any(differences>1e-10) and np.any(abs(differences)<1e-10)


def test_value_reference_uses_only_report_and_declared_model_and_is_nonnegative():
    for c in grid():
        for report in [0,1]:assert report_value(report,c)['conditional_gain']>=-1e-12
    assert report_value(1,Contract(prior=.1,accuracy=1.,age=0.,detour=4.))['posterior_action']=='DETOUR'


def test_transition_and_report_reject_invalid_inputs():
    with pytest.raises(ValueError):transition_probability(1,-1.,.3,.1)
    with pytest.raises(ValueError):report_posterior(1,.3,1.1)
    with pytest.raises(ValueError):exact_cell(Contract(rate=-1.))


def test_read_only_score_probes_match_original_greedy_agent_with_nonzero_effects():
    a=FixedGateAgent(0,13,mode='ALL',eps=0.);a.pos=1;a.Q[1].update({5:1.,6:2.})
    belief={(1,v):dict(threat=.1,cost=3.,age=-1.) for v in [5,6]}
    a.hazard_buf[(1,6)]=(1.,0.,1.)
    # An old report changes this responsive actor under ALL but not FRC.
    assert score_probe(a,[5,6],belief,4.,1,'ALL')[0]==5
    assert score_probe(a,[5,6],belief,4.,1,'FRC')[0]==6
    for mode in ['NONE','ALL','FRC','TRAVEL']:
        a.mode=mode
        for now in [0.,2.,4.,9.]:
            assert score_probe(a,[5,6],belief,now,1,mode)[0]==a.act([5,6],belief,now,1)
