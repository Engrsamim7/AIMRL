# Delivery-primary learned routing: completed v3 experiment

The revised model is implemented and evaluated, but **the learned receiver gate does not establish a delivery advantage**. LEARN achieves 67.151% on-time delivery, versus 67.278% for the same frozen routing actors accepting all eligible reports. The primary one-percentage-point superiority target is unmet. Transmission savings are not substituted for delivery improvement.

## What changed from the submitted technique

The submitted family used tabular Q routing and a fixed FRC receiver filter. This experiment trains cooperative, parameter-sharing independent Double-DQN routing with 26 public/local belief, history, topology and timing features. A planning prior plus a bounded learned action residual replaces the hub-only Q table. The reward is undiscounted fleet on-time delivery, with potential shaping that preserves that objective; there is no bandwidth reward.

The new receiver gate fits 96-tree ensembles to actual complete-fleet admit-minus-reject packet interventions. Its 24 deployed features do not contain remote closure truth or future outcomes. All communication-enabled actor arms share the same transport and frozen routing weights. The experiment isolates receiver admission effects; it is not a benchmark in which every receiver has its own independently optimized routing policy.

The timed model includes blocked entry, time-consuming inspection, FIFO hub service, holding, noisy local sensing, finite serialized radio capacity and fixed deadlines. In v3, repeated same-time noisy samples preserve confirmed encounter evidence, preventing a zero-inspection retry cycle. Later observations can still report reopening. This correction applies to every arm. Historical timed-network code and results remain unchanged.

## Executed evidence and selection

There are eight independent 500-episode routing runs, 3,200 attempted labeling episodes, **2,784 paired packet interventions**, eight fitted gates, 960 gate-validation method episodes and **21,600 held-out method episodes / 172,800 convoy outcomes**. Actor and gate choices were locked before testing. Seven selected routing checkpoints have optimizer updates; seed 2 retains the initial planning policy. Six runs improve actor-validation delivery, one selects a trained tie and one retains the initial policy. These are validation selections, not convergence or test-benefit evidence.

Gate validation selected beta 0 / margin 0 / risk limit 0.1: 57.227% on time versus 56.901% for its disabled ALL fallback. The positive 0.326-point validation gain did not carry over to testing. **Beta 0 omits the tree-dispersion penalty**; the result therefore does not demonstrate a benefit from uncertainty penalization. Tree dispersion and estimated admission-benefit frequencies are heuristic, not calibrated guarantees. Gate parameters remain frozen during evaluation.

Each learned gate can reject at most one packet per fleet episode under a shared public token, then uses ALL. NONE, ALL, FIXED_RX, KEEP_ONE, KEEP and LEARN share the eight routing actors. The two planner references run once per environment. Each actor method has 3,456 episodes; each planner has 432. Episode totals are not independent training replications.

| Method | On-time delivery | Whole-horizon delivery |
|---|---:|---:|
| NONE | 64.591% | 96.723% |
| ALL | 67.278% | 97.146% |
| FIXED_RX | 64.959% | 96.741% |
| KEEP_ONE | 67.278% | 97.150% |
| KEEP | 67.332% | 97.078% |
| LEARN | 67.151% | 97.117% |
| PLANNER_WARN | 64.931% | 96.817% |
| PLANNER_RAW | 64.786% | 96.817% |

Primary paired contrasts use 20,000 crossed routing-seed/weighted-graph/environment bootstrap draws with Bonferroni correction for three comparisons:

| LEARN minus baseline | Mean difference, percentage points | Corrected interval |
|---|---:|---:|
| ALL | -0.127 | [-0.503, 0.228] |
| KEEP | -0.181 | [-0.716, 0.365] |
| PLANNER_RAW | +2.365 | [-1.190, 6.327] |

All corrected intervals include zero. The planner mean difference cannot be attributed specifically to gating, because the methods also differ in routing. Across the LEARN/ALL comparison's 27,648 convoy outcomes, ALL has 18,601 on-time arrivals and LEARN has 18,566: **35 fewer with the learned gate**. This is an observed loss, not statistically established inferiority or equivalence. All twelve declared conditions remain in the tables and figures; no favorable subset replaces the pooled comparison.

## What the packet evidence explains

Of 2,464 training labels selected by the buffer-only actor-change proxy, admitting the packet harms delivery in 103, helps in 102 and has no delivery effect in 2,259. Another 320 no-change controls are retained separately and excluded from gate fitting. A routing change alone is therefore a weak label for delivery harm.

The best hindsight choice among the sampled active training interventions yields only 0.352 percentage points averaged over all 3,200 attempted episodes, assigning zero when no sampled helpful rejection exists. This diagnostic is **not** a deployable policy or an upper bound over unobserved packets, other gate budgets, other routers or other conditions. It exposes limited useful signal in this sampled one-rejection design; it does not establish technical impossibility.

On test, LEARN rejects 1,567 packets: 130 rejections improve fleet on-time delivery, 153 worsen it and 1,284 leave it unchanged. Because there is one rejection and ALL thereafter, paired LEARN/ALL outcomes identify each rejected packet's complete downstream effect under the frozen actor. Non-rejection episodes exactly match ALL. This denominator is rejected packets, not all transmissions or a general FIR estimate.

For those selected rejected packets, the model's mean predicted admission-minus-rejection effect is -0.900 percentage points; the actual paired mean is +0.279 points. These selected-case measurements show that the fitted predictor does not isolate harmful admissions reliably on this test. They do not measure calibration over all messages. The record cannot by itself separate insufficient rare-event data, imperfect features, transfer shift and validation noise as causes.

## Claim boundaries and next research step

A defensible description is: **a delivery-only learned-routing simulator and a causal packet-value gate were implemented and evaluated under consequential synthetic closures; the tested gate did not establish superiority over the declared baselines.** The original manuscript's general superiority claim remains unsupported.

The gate's eligibility probe temporarily changes its packet buffer while holding accepted-report history summaries fixed. It is not an exact full-admission action probe; actual causal labels do perform full admission. The one-token controller is not fully decentralized coordination or an optimal-stopping solution. Six weighted graph instances use fixed adjacency templates within 19/51/131-node families ; 131-node transfer is not arbitrary-topology generalization. Only two instances per size, one inherited report interpreter and eight training seeds limit uncertainty assessment. There is no convergence proof, realistic geographic validation, adaptive adversary, destruction model or operational military claim.

The next algorithmic work should address the measured prediction failure and authority limit: collect more representative rare-effect continuations with documented sampling/weighting; use full admission/history features; validate conditional return and harm estimates on separate policy rollouts; and, if multiple rejections are introduced, label their remaining-budget continuations rather than adding isolated effects. End-to-end superiority also needs matched receiver-specific routing training and adequate convergence assessment. Any redesign informed by these test results requires a fresh reserved test set. Another freshness-threshold sweep or selecting favorable cases would not resolve the evidence gap. Manuscript equations, tables, abstract and response letter still need revision against supported results.

## Verification and accessible artifacts

All **153 tests pass**. The reporter independently verifies checkpoint/setting selection, frozen model hashes, all 432 reconstructed closure schedules, route continuity and nominal costs, integer blocked-entry totals, deadline classification, nonnegative time components, elapsed-time balances and episode/convoy aggregates. It reproduces saved gate decisions and identifies rejected-packet effects.

The two stopped development passes, their exact source and training records remain in the ZIP. The first exposed unstable training; the second exposed the same-time sensor loop. Neither reached a locked setting or held-out test. Final results use corrected v3 physics and fresh training only. Artifact integrity and portable report regeneration are recorded in the delivery validation JSON.

- [Seven-figure PDF](../deliverables/AIMRL-delivery-learning-figures.pdf).
- [Complete code, original uploads, models and raw-data ZIP](../deliverables/AIMRL-delivery-learning-study.zip).
- [Tables and reproduction commands](delivery-learning-results/README.md), [offline figures](delivery-learning-results/index.html).
- [Prospective protocol and development corrections](delivery-learning-protocol.md), [reviewer coverage and remaining gaps](delivery-learning-reviewer-map.md).
