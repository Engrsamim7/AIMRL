# Scientific assessment: do not submit the current superiority claim

The current evidence is not sufficient for the manuscript's gate-superiority, survival or necessity claims. Correct execution and reproducible figures are necessary, but do not establish scientific validity or novelty. The previous delivery should have made this distinction more prominent. This phase addresses mechanism validity before further performance experiments; it does not declare the manuscript ready.

## A newly verified diagnosis

We replayed all 43,200 original-family test episodes using frozen checkpoints and instrumented 518,400 routing calls. Every factual action matches the analytical score probe, every existing episode metric reproduces within numerical tolerance, and Q tables stay unchanged.

| Diagnostic | Executed finding | Scientific implication |
|---|---:|---|
| ALL versus FRC next-hop changes on the same frozen policy/state | 0 / 518,400 | This test cannot establish an online filtering benefit. |
| ALL versus NONE next-hop changes on the same frozen policy/state | 0 / 518,400 | The frozen routing choices are unresponsive to these peer-score corrections on the recorded states. |
| Decisions with an actually blocked available outgoing option | 0 / 518,400 | Blocking exists in the environment, but does not create the relevant encountered decision alternatives here. |
| Decisions at/after first red wave | 2,520 / 518,400 (0.486%) | Almost all decisions occur before the first attack wave. Being after a wave alone does not imply useful warning opportunity. |
| Top-two Q gap larger than the maximum possible response penalty | 457,920 / 518,400 (88.33%) | At these multi-option decisions, the bounded peer/local score correction cannot overcome the raw Q margin. Other decisions also happen to keep the same next hop. |
| Actual test delivery | 100% across every arm | There is no delivery improvement to measure in this test. |

These counts include repeated schedules, methods and training seeds, and must not be treated as 518,400 independent experimental units. The score probes hold the actual state fixed; they are not isolated-message fleet-outcome counterfactuals. They do identify that gate changes fail to alter the deployed next-hop decisions on the recorded trajectories. Differences between separately trained policies must not automatically be called online gate benefits.

The audit code uses physical closure truth only for evaluator labels. No extra random draws or policy information are added. All raw decisions and all condition-level aggregates are preserved.

## The statistical problem is downstream of the model problem

More runs or larger plots will not repair inactive information use. Increasing hazard coefficients until a favorable outcome appears would change the objective/response strength and risk repeating the reviewer's ablation confound. Choosing deadlines, closure schedules or confidence noise after observing which gate wins would also require new independent validation and testing.

The original source has no connected M4 hazard stream; the repair connects genuine observations, but reports still do not change frozen choices. Static route-risk scores, binary physical closures, confidence in an observation and probability of destruction are different quantities. The code does not model attack-induced destruction, so its average route-prior score cannot support a survival-probability claim. Original and repaired cost units must also be reconciled with the manuscript.

The ungated 0.851 presentation score is not reproduced, NC and IQL are executable aliases in the original campaign, and the historical MAPPO label is not a standard MAPPO implementation. These issues require replacing or explicitly correcting manuscript comparisons, not retaining the original table with better-looking figures.

## An implemented mechanism reference

We added an exact, independently checkable two-route decision benchmark. It distinguishes binary closure from static route risk, reports from current hidden truth, and observation-time accuracy from current validity. A known closure transition law propagates a calibrated observation posterior:

`p(closed now | report) = prior + (p(closed then | report) - prior) * exp(-rate * age)`.

A common decision rule minimizes travel loss: short route cost 1 plus a closure delay if blocked, or a safe detour of cost 1 plus its extra travel. This is a model-validation reference, not a replacement logistics simulator or a new MARL performance result. The transition law and sensor accuracy are known by assumption; they have not been calibrated from operational data.

All 432 declared parameter cells and 3,456 probability-weighted branches are published. Fixed FRC has lower expected loss than age-ignorant ALL in 29 cells, higher loss in 37, and ties in 366. These counts describe the chosen artificial grid, not a real-world prevalence or confidence interval. Full current local visibility makes all methods equivalent. Persistent truthful observations do not become invalid simply because they are old. Under changing closures, a stale report can make a naive ALL policy take an unnecessary detour or the wrong shortcut.

The AGE_AWARE reference knows the generating law and weakly dominates the other rules in expected cost under those assumptions. Its role is to expose what an appropriate strong baseline must handle. It is not evidence that an implemented learned model achieves this reference.

There is also a fundamental claim limit: if accepting all information is free and its policy can implement the gate internally, the optimal all-information policy can emulate that gate. A universal strict advantage is then impossible. A gate can outperform a specified restricted interpreter, improve finite-sample learning, or trade task performance against modeled communication/computation cost. Each is a different testable claim.

## Required correction to the network study

The [network acceptance contract](journal-network-acceptance-contract.md) fixes the intended next experiment before its outcomes are known. It requires one canonical event-driven environment and shared observation/report semantics; meaningful but independently specified timing and deadline variation; a belief-conditioned routing learner; matched strong planning and age-aware baselines; explicit costs; and fresh training/validation/test separation. The current exact benchmark is the unit-level reference for posterior and action tests.

The next network version must pass mechanism validation before a superiority campaign: genuine observations can arrive before consequential commitments; both correct and stale messages can affect responsive actors in declared fixtures; blocked inspection/recovery consumes explicitly modeled time; and current local truth does not leak into remote actors. It must also retain zero-attack, full-visibility, late-message and persistent-truth controls, even when the gate loses or ties.

No setting should be admitted or dropped because it produces a favorable gate effect. Calibration and hyperparameters use training/validation only. The full declared test range and seed-level uncertainty must be reported. If filtering adds no value over a well-calibrated interpreter, the contribution must change or the superiority claim must be removed.

## Reviewer and submission status

| Concern | Current evidence | Required before a superiority resubmission |
|---|---|---|
| Mechanism validity / ablation (R1.10) | Read-only matched-state audit completed; no next-hop effect. | Responsive information interpretation and matched response objectives; show marginal gate value beyond the interpreter. |
| State / partial observation (R1.1) | Original Q is hub-indexed; local buffers exist. | State/history and timed decision formalization; belief-conditioned actor and leakage tests; do not claim a solved POMDP. |
| Scale / learning (R1.2) | Original-family test is 19 nodes; earlier neural studies are separate. | Larger independent graph families, matched training budgets, seed-level training curves and runtime/memory; no convergence claim from a fixed episode count. |
| Cost and count semantics (R1.3, R1.9) | Nominal and time-weighted costs separated; raw integer counts retained. | Replace inconsistent manuscript tables and report all denominators and failure/censoring. |
| FIR attribution (R1.4) | Current action probes are diagnostics, not single-packet fleet FIR. | Full-state packet interventions with controlled exogenous schedules, separate endogenous-adversary total effects. |
| Freshness / queue age (R1.5, R1.7) | Exact transition reference implemented; old static/travel rules tested separately. | Validate queue-time aging and traversal-time prediction in the canonical network study; fit/calibrate report validity on training data. |
| Baselines (R1.6) | Historical aliases and mislabeled custom MAPPO identified. | Independently implemented, documented comparators; matched actor inputs, budgets, objective and tuning. |
| Adversary (R1.8) | Synthetic blocks and a traffic-reactive inherited wave exist. | Explicit finite budgets, observations, delays and persistence; paired exogenous schedules for causal claims; delimit operational applicability. |
| Confidence / three-way gate (R2) | Original-family reports have confidence 1. | Honest sensor uncertainty and miscalibrated confidence tests; confidence-only/relevance-only/freshness-only ablations with a common interpreter. |
| Abstract, contribution, Figure 1, algorithm list (R2) | Existing manuscript asserts stronger claims than these results support. | Rewrite after the corrected study; align equations, methods, tables, figure labels and comparator names. |

Passing 129 tests establishes software checks, not that all reviewer concerns are resolved. The exact toy reference and diagnostic report are useful supporting material; they cannot substitute for corrected network-level evidence. Do not send the existing superiority manuscript with these figures as if the scientific issues were resolved. A diagnostic/reproducibility paper would be a different contribution and would need its own novelty and venue assessment.

## Deliverables

- [Four-figure diagnostic PDF](../deliverables/AIMRL-journal-readiness-figures.pdf).
- [Complete diagnostic code, parent models and raw audit ZIP](../deliverables/AIMRL-journal-readiness.zip).
- [Tables and reproduction commands](journal-readiness/README.md), [offline figures](journal-readiness/index.html), and [protocol](journal-readiness-protocol.md).
- [Original reproduction and repairs](original-tabular-findings.md) remain unchanged.
