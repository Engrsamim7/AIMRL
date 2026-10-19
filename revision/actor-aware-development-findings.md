# Can the message-value problem be improved?

**There is measurable improvement opportunity, and this development version shows a small MAPPO gain. The problem is not solved broadly, and superiority is still unconfirmed.** The useful next step is a focused development test of why valuable interventions are missed and harmful ones are selected, rather than another large confirmation run of the unchanged estimator.

This phase changes the algorithm, not the benchmark physics. It uses fresh training-distribution layouts and tapes with sixteen existing frozen SAFE-trained DQN/MAPPO actors. It does not create new independent routing-training seeds or replace the previous recovery study. See the [protocol](actor-aware-development-protocol.md), [all tables](actor-aware-development-results/README.md), and [six figures](actor-aware-development-results/actor_aware_development.pdf).

## What was changed

1. **Probe the actual neural actor.** For an eligible packet, construct public accept and reject contexts and interpret the complete remaining inbox with SAFE. Query actor scores in each context. Append23 actor-response/cost/belief features to the original30. No true packet origin, active hazard schedule, future events or privileged MAPPO critic value becomes a gate input.
2. **Predict fleet effects.** The target is the fleet's mean utility and delivery change from flipping SAFE, including all five convoys. Earlier receiver-only targets did not directly optimize this endpoint.
3. **Align training and deployment.** Allow at most one learned override across the entire episode; all later decisions use SAFE. Full-inbox intervention rollouts therefore match the deployed post-override continuation. Both predicted next actions and the factual branch outcomes must reproduce.
4. **Use a controlled feature comparison.** Both TREE_BASE and ACTOR_AWARE use the same ExtraTrees estimator, fitting labels, action-change restriction, override budget and calibration grid. TREE_BASE uses the original30 features; ACTOR_AWARE uses53. This isolates the additional features within this redesign; it does not isolate every difference from the earlier hurdle-network study.
5. **Allow abstention.** Calibration can select SAFE throughout. Settings, estimator hashes and original routing checkpoint hashes were locked before audit evaluation. No settings or physics were changed after audit outcomes.

The phase exports15,397 selected paired intervention labels from6,144 factual development episodes, fits32 estimators, evaluates39,936 calibration configurations and6,144 audit method episodes /30,720 convoy records. All eight training-distribution conditions are retained. All111 regression tests pass.

## There is room to improve, but the hindsight reference is not an achieved method

For each factual episode, select the best nonnegative utility gain among its sampled single-packet flips, using the completed counterfactual futures. On audit data:

| Actor | Best sampled hindsight utility gain per convoy | Delivery change of the hindsight utility choice |
|---|---:|---:|
| DQN | +0.747 | +0.977 percentage points |
| MAPPO | +0.994 | +1.328 percentage points |

This demonstrates available improvements in the sampled trajectories. It is **privileged hindsight**, not deployable performance, a globally optimized bound or a guarantee that the public inputs can predict the right intervention. No packet effects are summed. Selected packets cover only part of the message stream; an online method can select other packets.

Restricting this sampled reference to the new gate's reachable, immediate-action-changing candidates leaves gains of0.745 DQN and0.991 MAPPO. Most of this audit sample's hindsight opportunity lies within the new authority restriction. Some unchanged-action reports still affect later outcomes; neither this finding nor the restriction proves those reports are inert.

## What the deployed gate actually achieved

All methods below use the same frozen SAFE-trained actor within each routing seed. These audit conditions are the original training distribution with new layouts/tapes, not the earlier held-out stress distribution. Therefore the93% delivery levels must not be compared directly with the previous88% levels as an improvement caused by this algorithm.

| Actor | Method | Delivery | Mean fleet utility |
|---|---|---:|---:|
| DQN | SAFE |93.047% |21.510 |
| DQN | TREE_BASE |92.852% |21.341 |
| DQN | ACTOR_AWARE |93.125% |21.522 |
| MAPPO | SAFE |93.086% |21.528 |
| MAPPO | TREE_BASE |93.398% |21.732 |
| MAPPO | ACTOR_AWARE |93.750% |21.974 |

Against SAFE, ACTOR_AWARE gains0.078 percentage points of delivery and0.011 utility for DQN, and0.664 percentage points and0.446 utility for MAPPO. Against the same-tree old-feature comparator, gains are0.273 percentage points /0.181 utility for DQN and0.352 percentage points /0.242 utility for MAPPO.

Exploratory95% paired crossed-bootstrap intervals:

| Actor | Utility difference vs SAFE | Delivery difference vs SAFE, pp |
|---|---|---|
| DQN |+0.011 [−0.733,+0.794] |+0.078 [−0.898,+1.133] |
| MAPPO |+0.446 [−0.036,+1.042] |+0.664 [0.000,+1.445] |

The utility intervals include zero and MAPPO's delivery lower bound equals zero. These exploratory intervals are not corrected superiority evidence or fresh independent routing-training replication. MAPPO's utility mean is positive for seven of eight existing actor seeds; DQN's is positive for only two. The DQN result is especially weak. Every case, baseline and seed effect is available in the tables.

## What remains unsolved

**The selected actor-aware gate made139 DQN and103 MAPPO overrides, all rejections.** It is allowed to accept or reject, but calibration and its predictions produced no clearance-acceptance overrides in audit. This does not validate learning when to accept useful reopening information.

**The clearance opportunity is structurally small in this benchmark.** The sampled hindsight utility gain is2.706 DQN /3.606 MAPPO in persistent-hazard cases, but only0.027 /0.024 in rapid recovery. Each fork has two inexpensive branches and initially blocks only one; a physically open inexpensive alternative remains available. The expensive third bypass does not by itself remove that redundancy. This is consistent with accepting reopenings offering little additional cost benefit in these sampled trajectories, even though genuine clearances exist. It is not a complete causal attribution: timing, misinformation and the actor also matter.

This exposes a benchmark limitation as well as an estimator limitation. A future declared topology study could compare an inexpensive shortcut with a genuinely costly alternative, alongside the current redundant topology and persistent/no-hazard controls. All methods must receive identical physics, and no winner can be assumed. That would test clearance value for a justified route-cost reason; it would not retrospectively validate the current claim.

**Prediction remains imperfect.** On eligible action-changing audit labels, mean absolute error across eight seeds is4.062 for ACTOR_AWARE versus4.089 for TREE_BASE in DQN, and3.857 versus3.798 in MAPPO. Zero-effect prediction has MAE3.599 and3.279. The added features do not show a consistent prediction-error advantage over the same-tree baseline.

Squared error is lower than zero prediction for both forests on eligible and consequential labels, which is useful diagnostic progress for this combined estimator/target/data redesign. It cannot be attributed to actor-aware features alone: TREE_BASE is slightly better on eligible squared error for both algorithms. MAE, squared error, decision selection and fleet outcomes answer different questions.

**The selected interventions still mix help and harm.** Among sampled proposals passing the locked actor-aware thresholds, DQN has88 utility-helpful and93 utility-harmful examples; MAPPO has58 and69. MAPPO's delivery effects favor the helpful side31 to9. These are contextual sampled proposals, not independent trials or effects that can be summed. The actual runtime gate chooses at most the first qualifying override; proposal counts are not the deployed episode count. A model can make many small mistakes yet have a favorable mean through fewer large gains, making uncertainty assessment essential.

**The uncertainty penalty was not retained by calibration.** Selected beta is0 for both actor-aware gates; DQN margin0, MAPPO margin0.5, delivery tolerance0. Tree-dispersion uncertainty was available but did not win this calibration grid. This provides no evidence of calibrated uncertainty or a benefit from the uncertainty penalty. Empirical calibration selection is not a delivery-safety guarantee.

## Research decision

We have a narrower, testable direction: fleet-value rejection informed by the actual routing actor can produce a small MAPPO development gain. We do not have a general gate solution, a useful clearance-acceptance result, or a defensible claim of superiority.

Before another expensive confirmation study, use fitting/calibration data to audit missed valuable candidates and harmful proposals, including public evidence missing from the feature set and whether outcomes remain indistinguishable under the available information. Assess decision precision and regret on consequential messages, not aggregate zero-effect accuracy alone. Any estimator change based on this development audit needs fresh development-audit layouts and tapes.

Advance a clearly specified MAPPO candidate only after a stable development result, then perform new matched actor retraining and untouched confirmation against strong conservative baselines. Do not hide DQN, label the hindsight opportunity as achieved performance, force acceptance activity, or make the delivery tolerance looser to obtain a win. The earlier manuscript's general-superiority assertion remains unsupported.

## Reproducibility and access

The complete ZIP is `deliverables/AIMRL-actor-aware-development.zip`; the standalone six-page figure report is `deliverables/AIMRL-actor-aware-development-figures.pdf`. It contains current simulator/source,16 parent SAFE inference checkpoints,32 new non-pickle NPZ estimators, selected branch labels, factual outcomes, calibration/audit records, locked settings, tables and figures. The original recovery source fingerprint remains unchanged.

The report verifies fleet accounting, reconstructed utility, paired physical schedules, selected settings, model/checkpoint hashes, and exact agreement between factual audit SAFE outcomes and evaluated SAFE outcomes. Clean-extraction tests, regenerated table checks and public-download integrity are recorded in the delivery validation sidecar. Reproduction commands are in the report README.
