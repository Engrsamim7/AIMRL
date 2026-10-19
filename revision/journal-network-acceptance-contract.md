# Acceptance contract for the next network study

Status: prospective specification, not implemented network results. The read-only audit and exact decision reference are implemented separately. This contract prevents another large experiment in which the gate cannot affect consequential decisions. It does not require the gate to win.

## One canonical model and a declared claim

Retain the original event-driven logistics graph family as the continuity case. Extend the same documented model to larger held-out graph families; do not combine results from unrelated simulator definitions under one algorithm label. Archive the original and repaired versions for provenance.

Primary task claim: on-time delivery under declared synthetic physical closures, information delays and resource constraints, against specified matched baselines over a frozen evaluation range. Report nominal travel cost and elapsed time separately. Static route-risk score is descriptive and is not destruction probability. A different survival claim requires an independently justified destruction model and data; do not invent killing probabilities to obtain an improvement.

Use a timed partially observed control formulation: graph/public attributes, convoy positions and in-transit states, queues, true closure processes, local sensing, timestamped reports, decision times, action feasibility, reward and terminal/censoring rules. Actors receive only declared local observations/history; centralized critic privileges, if any, are explicit. Hub-only tabular Q is the historical comparator. A refined actor conditions on information state, own/peer uncertainty and remaining mission time; timed discounting must match the declared objective.

## Physical and information semantics

Separate these variables for every edge: nominal travel cost; background threat/risk proxy; actual open/closed state; observed open/closed state; observation time; observation reliability; and confidence claimed by a sender. A report about a block is not encoded only as an arbitrary increase to the static threat penalty.

Specify attack onset, number of targeted closures, duration/reopening, reveal/detection behavior and recovery time independently of the method's results. Include early and late onsets relative to policy-independent free-flow mission duration. Freeze total per-episode threat budgets when varying onset; do not silently increase the number of attacks by shortening a repeated-wave period.

A blocked attempt consumes a declared inspection/recovery time if that is the modeled mechanism; never teleport through a blocked edge. Retain zero-delay inspection as a control. Mission deadlines, if used, are fixed relative to a public free-flow lower bound or an independently specified service requirement. Do not select deadlines to maximize a reported percentage improvement.

Observations arise from sensor/convoy position and time. Sensor masks and scout departure leads are declared independently of hidden closures and identical across methods. A departure lead changes actual movement, not just the report timestamp. An old honest report remains valid if its state persists; fresh false information can be harmful. Queue waiting contributes to age. Current own observations take precedence for every comparator.

## Shared interpretation before gating

Fit the observation-error and closure-persistence model on training trajectories; check calibration on validation trajectories, including selective confirmation. Use report age, public traversal estimates and calibrated reliability to estimate closure at the expected traversal time. Sender confidence alone is not known accuracy. The exact reference module validates only the special case of known transition law and known symmetric sensor accuracy.

Use the same report interpreter, action-cost objective, feasible-action rules and penalty units across ALL, FRC and a refined gate. The refined gate may estimate marginal action/return value and uncertainty, but its labels use frozen-policy branch outcomes from training only. Any safety fallback must also appear in matched baselines.

Always include a strong age-aware ALL comparator that may retain all information and reason about it. Without an explicit communication/processing cost, discarding observations has no general information-theoretic advantage. If the contribution is resource efficiency, model actual attempted transmissions or measured processing cost and optimize that declared objective; receiver admission alone is not bandwidth saving.

## Mechanism acceptance before large training

Required deterministic fixtures include:

1. Timely novel warning changes a responsive actor and avoids a costly blocked attempt under a known schedule.
2. An obsolete warning can cause a detour under an age-ignorant interpreter; a persistence-aware interpreter handles both reopening and persistent-state controls correctly.
3. Local current information makes a redundant report irrelevant for every method.
4. Queue/service waiting makes a report older at the actual departure decision; the actor uses elapsed time rather than event count.
5. Physical accounting balances nominal path cost and elapsed travel/inspection/wait; delivery, failure and censoring are mutually exclusive.
6. Changing remote hidden truth while holding actor-visible inputs fixed leaves the action unchanged; evaluator labels never enter actor features.
7. Counterfactual packet branches use identical complete exogenous closure/sensor/loss schedules, with independent RNG streams. Traffic-reactive interventions require separately stated causal assumptions.
8. Matched baselines share all safeguards and response coefficients. Freshness/confidence/relevance ablations vary only the named factor.

These fixtures are assertions about known mechanisms, not held-out performance evidence. Development distributions must have measurable nonredundant information opportunities, but no cell is retained, removed or tuned based on which method wins.

## Confirmation design and stopping rules

Use new non-overlapping training, validation and test namespaces and held-out graph families. Refit compatible routing policies under each communication method using matched interactions and comparable validation-only tuning budgets. Include a frozen-actor analysis to distinguish online filtering from training effects.

Retain no-communication, age-ignorant ALL, fixed FRC, age-aware ALL, uncertainty-aware/value-aware gate, and strong shortest-path/replanning baselines. If standard neural MARL names appear, implement their actual update rules and disclose actor/critic inputs; do not relabel a custom tabular policy as MAPPO.

Freeze the scenario range, objective, primary gate-versus-strong-ALL contrast, secondary endpoints, meaningful effect size, sample-size method and multiplicity plan before releasing test outcomes. Choose replication from validation variance at the independent training-seed and graph levels, not from the raw number of correlated convoy decisions. Report every declared condition and negative result. A fixed number of episodes does not prove convergence.

Proceed to a superiority claim only if the independent network test supports the prespecified practically meaningful advantage over the relevant strong baseline, without hidden objective changes. If ALL already extracts the information value and filtering adds no benefit, report an interpreter contribution or a null gate result. Do not continue changing scenarios against the same test set until the gate wins.
