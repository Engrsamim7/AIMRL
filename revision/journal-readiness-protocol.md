# Journal-readiness audit and decision-reference protocol

19 October 2026. This phase audits already published test outcomes and executes an exact model-validation benchmark. It is not a fresh superiority test. The original sources, trained models, historical experiments and null findings remain unchanged.

## Read-only frozen-policy audit

Replay every configuration and schedule from the original-tabular study: 43,200 episodes. At every actual routing call compute greedy NONE, ALL, FRC and TRAVEL choices from exactly the same frozen Q table, candidates, own beliefs and buffered reports. Only the receiver mode changes in these local probes. Assert that the factual probe equals the actual action. Assert that all factual delivery, route-prior, nominal-cost, elapsed-time, blocked-entry and communication metrics reproduce the parent results. Assert that checkpoint Q tables never change.

Record opportunity exposure, available physically blocked options, candidate reports, own-observation precedence, actual score applications, next-hop changes, and Q gaps. Physical block truth is evaluator-only. These are diagnostic action probes, not causal single-packet fleet-outcome effects. A large number of repeated decisions is not a large number of independent training seeds.

## Exact decision reference

Separate binary road closure from static route-prior scores. A stationary two-state continuous-time Markov chain has open-to-closed rate k*pi and closed-to-open rate k*(1-pi). A binary report has known symmetric sensor accuracy r. Its age is a, with known prior closure probability pi. These assumptions are analytical, not field-calibrated or estimates learned from the supplied simulator.

Bayes' rule yields p0=P(closed at observation | report). At the decision time, p(a)=pi+(p0-pi)*exp(-k*a). A short route costs 1 plus closure-delay L if closed; the safe detour costs 1+d. All methods select the smaller expected cost using a common action rule. Closure delay is an elapsed-time loss, not destruction or combat survival.

NONE uses pi. ALL uses p0 without age propagation. FRC uses the same p0 if age<=3.2 and accuracy>=0.6, otherwise pi. AGE_AWARE uses p(a). Full current own visibility takes precedence for every method. AGE_AWARE knows the generating law: it is a model-reference baseline, not a trained MARL system. Its expected-cost dominance follows from conditional minimization; this is not empirical network superiority.

Enumerate all 432 cells: pi in {0.1,0.3}; r in {0.55,0.75,1}; k in {0,0.1,0.5}; age in {0,2,4,8}; detour in {1,4,8}; full current own visibility in {false,true}; closure delay fixed at 12. Enumerate all eight combinations of old closure, current closure and report. Retain every cell and probability. No simulation confidence intervals are needed for this exact finite expectation. Grid means are unweighted descriptions of this artificial grid, not population effects.

Inspect persistent honest reports, changing stale reports and redundant current observations. A fixed age threshold need not help persistent truth, and a confidence cutoff is not meaningful without calibrated confidence. The report probability/value functions use public reports and declared model parameters, never current hidden closure labels. Perfect law knowledge is explicitly disclosed.

## Submission decision

Publication readiness is judged on consistency of claim, method and evidence, rather than on whether a plotted difference is positive. Original numerical discrepancies, missing attacked decision opportunities, inactive filtering, nonstandard baseline labels, state adequacy, scale, causal FIR, confidence calibration and manuscript alignment remain explicit blockers. A corrected diagnostic or exact toy benchmark does not resolve these network-level concerns.
