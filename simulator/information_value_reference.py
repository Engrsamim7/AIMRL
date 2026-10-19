"""Exact, small decision benchmark; NOT a network/MARL performance result.

A reported binary road closure is distinct from a static route-risk score.
Closure follows a stationary two-state continuous-time Markov chain with
known prior pi and total transition rate k: open->closed k*pi,
closed->open k*(1-pi). A symmetric sensor has known accuracy r.
The shared response minimizes expected travel loss. No convoy destruction
or empirically calibrated transition/sensor model is implied.
"""
from dataclasses import dataclass
import itertools
import math


@dataclass(frozen=True)
class Contract:
    prior: float = .3
    accuracy: float = .75
    rate: float = .1
    age: float = 2.
    detour: float = 4.
    closure_delay: float = 12.
    own_visible: bool = False

    def validate(self):
        if not 0 < self.prior < 1 or not .5 <= self.accuracy <= 1:
            raise ValueError('Require interior prior and calibrated accuracy in [.5,1].')
        if min(self.rate,self.age,self.detour,self.closure_delay) < 0:
            raise ValueError('Time, rate and cost inputs must be nonnegative.')


def transition_probability(old_state, age, prior, rate):
    if old_state not in [0,1] or age < 0 or rate < 0 or not 0 < prior < 1:
        raise ValueError('Invalid closure transition input.')
    return prior + (old_state-prior)*math.exp(-rate*age)


def report_posterior(report, prior, accuracy):
    if report not in [0,1] or not 0 < prior < 1 or not .5 <= accuracy <= 1:
        raise ValueError('Invalid calibrated report input.')
    positive_given_closed=accuracy if report else 1-accuracy
    positive_given_open=1-accuracy if report else accuracy
    numerator=prior*positive_given_closed
    return numerator/(numerator+(1-prior)*positive_given_open)


def current_report_probability(report, prior, accuracy, age, rate):
    # Marginalize unknown observation-time closure; no current hidden truth.
    return propagate_probability(report_posterior(report,prior,accuracy),age,prior,rate)


def propagate_probability(old_probability, age, prior, rate):
    if not 0<=old_probability<=1 or age<0 or rate<0 or not 0<prior<1:
        raise ValueError('Invalid marginal transition input.')
    return prior+(old_probability-prior)*math.exp(-rate*age)


def action(probability, detour, closure_delay):
    # Base short-route travel cost is one; a closure adds an elapsed delay.
    # Stable ties choose SHORT for every method.
    return 'DETOUR' if detour < probability*closure_delay else 'SHORT'


def expected_cost(chosen, probability, detour, closure_delay):
    if chosen not in ['SHORT','DETOUR']:
        raise ValueError('Unknown route action.')
    return 1+(detour if chosen=='DETOUR' else probability*closure_delay)


def report_value(report, contract):
    """Known-model improvement from using a report rather than ignoring it.

    Conditional improvement is nonnegative under this known-model reference:
    the posterior-optimal action can retain the prior action. Realized sampled
    outcomes can still be worse; this is not a learned safety guarantee.
    """
    contract.validate()
    p=current_report_probability(report,contract.prior,contract.accuracy,contract.age,contract.rate)
    default=action(contract.prior,contract.detour,contract.closure_delay)
    informed=action(p,contract.detour,contract.closure_delay)
    return dict(probability=p,prior_action=default,posterior_action=informed,
        conditional_gain=expected_cost(default,p,contract.detour,contract.closure_delay)-expected_cost(informed,p,contract.detour,contract.closure_delay))


def exact_cell(c):
    c.validate()
    totals={m:0. for m in ['NONE','ALL','FRC','AGE_AWARE']}
    mass=0.;changes=0.;transitions=[]
    for old,now,report in itertools.product([0,1],repeat=3):
        pold=c.prior if old else 1-c.prior
        pclosed=transition_probability(old,c.age,c.prior,c.rate)
        pnow=pclosed if now else 1-pclosed
        preport=c.accuracy if report==old else 1-c.accuracy
        weight=pold*pnow*preport
        p0=report_posterior(report,c.prior,c.accuracy)
        current=current_report_probability(report,c.prior,c.accuracy,c.age,c.rate)
        probabilities=dict(NONE=c.prior,ALL=p0,FRC=p0 if c.age<=3.2 and c.accuracy>=.6 else c.prior,AGE_AWARE=current)
        choices={m:action(float(now) if c.own_visible else p,c.detour,c.closure_delay) for m,p in probabilities.items()}
        for m,chosen in choices.items():
            cost=1+(c.detour if chosen=='DETOUR' else c.closure_delay*now)
            totals[m]+=weight*cost
        mass+=weight;changes+=weight*(choices['FRC']!=choices['ALL'])
        transitions.append(dict(old=old,current=now,report=report,probability=weight,**{m:choices[m] for m in choices}))
    assert abs(mass-1)<1e-12
    assert totals['AGE_AWARE']<=min(totals.values())+1e-12
    return dict(**c.__dict__,**{m+'_expected_cost':v for m,v in totals.items()},
        frc_minus_all=totals['FRC']-totals['ALL'],gate_action_change_probability=changes,
        information_gain=totals['NONE']-totals['AGE_AWARE']),transitions


def grid():
    for prior,accuracy,rate,age,detour,own_visible in itertools.product([.1,.3],[.55,.75,1.],[0.,.1,.5],[0.,2.,4.,8.],[1.,4.,8.],[False,True]):
        yield Contract(prior=prior,accuracy=accuracy,rate=rate,age=age,detour=detour,own_visible=own_visible)
