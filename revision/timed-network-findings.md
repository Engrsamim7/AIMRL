# Timed network revision: what is implemented and what the evidence supports

The work now includes an executed network revision, not only an audit or a proposed protocol. It fixes several conditions that made the original gate experiment uninformative. It does **not** establish the manuscript's MARL or gate-superiority claim. The original source, reproductions and negative results are preserved.

## Implemented changes

| Earlier limitation | Executed revision |
|---|---|
| Most routing preceded the first attack; no blocked alternatives were encountered in the recorded test decisions. | Finite, policy-independent closure budgets include initial/early/late onsets and explicit reopening. Closures physically prevent entry. |
| Failed route choices could be repaired immediately without meaningful time loss. | Blocked attempts consume inspection time; rerouting, holding, hub service, queues and travel enter exact elapsed accounting. Zero inspection delay remains a control. |
| Delivery stayed at 100%. | Fixed on-time deadlines and a broad deadline/persistence/load surface expose missed missions. No destruction probability is invented. |
| A hub-indexed Q table ignored most peer-score changes. | A shared information-conditioned planning actor uses observations, report age, public topology, estimated traversal time and expected inspection delay. This is a planner, not a newly trained MARL policy. |
| Receiver admission counts were confused with communication savings. | A finite serialized broadcast channel measures started/completed frames, bytes, queue delay and partial-frame airtime. Sender filtering actually avoids transmissions. |
| Sender confidence was constant and report validity was assumed. | A common report-validity table is fitted on 76,800 synthetic training labels; noisy, delayed and confidence-miscalibrated sensing are evaluated. Calibration quality is measured, not guaranteed. |
| Only tiny-network gate results were available in the original-family study. | The same engine is run at 19, 51 and 131 nodes, including new graph instances. This is model/algorithm scaling evidence, not neural training convergence. |
| Admission, scheduling and response strength could be conflated. | All planning comparators use the same interpretation/objective where applicable. AGE_ALL -> LATEST -> VALUE_PRIORITY -> VALUE separates coalescing, value scheduling and admission. |

The VALUE sender is an explicitly new heuristic: estimated closure-belief change multiplied by public route-deletion cost and route demand. Its score uses public manifests, not live remote convoy positions. It is not the original receiver FRC, a learned causal message-value predictor, or a guarantee of beneficial messages. Honest observation accuracy and sender confidence are distinguished in the miscalibration test.

## Executed study

The initial pilot has nine cases, three channel capacities, six graphs and six schedules per cell. A frozen-model response surface subsequently crosses four deadline ratios, three closure durations, two closure budgets, two scout leads, two inspection costs and three channel rates on six new graphs with four schedules per cell. The matched admission ablation replays every pilot/surface cell with the same value scheduler and zero admission threshold.

Together these contain **63,072 method episodes / 504,576 convoy records**, including **864 distinct size/physical-case/channel cells** in the response surface. There is one training-fitted report interpreter, 648 validation method episodes, and no new routing-policy training seeds. Raw episode counts must not be described as independent trained-model replication. All favorable and adverse cases are retained.

The physics is synthetic: directed closures with finite budgets, no attack-induced destruction, grandfathered open entries already in transit, service-only FIFO hub occupancy, local sensor masks and an abstract shared radio channel. Units are model units. This is not operational military validation.

## Results that must be reported together

The full surface, with equal weighting over the declared grid, gives:

| Method | On-time delivery | Mean bytes charged for started broadcast frames |
|---|---:|---:|
| NONE | 67.5673% | 0 |
| RAW_ALL | 68.9091% | 6,005.79 |
| AGE_ALL | 68.2346% | 6,151.51 |
| LATEST | 68.2418% | 6,134.69 |
| WARN_PRIORITY | 68.6578% | 6,134.93 |
| VALUE_PRIORITY: same value scheduling, no admission filtering | 68.6343% | 6,132.15 |
| VALUE: locked admission threshold 0.05 | 68.3919% | 1,477.02 |
| Original-style receiver FRC | 68.2219% | 6,180.15 |

VALUE reduces started-frame bytes by approximately **76%** relative to AGE_ALL or the matched VALUE_PRIORITY scheduler. But it loses **0.2423 percentage points** of on-time delivery to VALUE_PRIORITY, **0.2658 points** to WARN_PRIORITY, and **0.5172 points** to RAW_ALL. Descriptive paired graph/environment 95% intervals for those delivery contrasts are respectively [-0.3581,-0.1284], [-0.4069,-0.1429] and [-0.9115,-0.1465]. They are not fresh confirmatory tests or a prespecified noninferiority analysis.

Relative to AGE_ALL, VALUE gains 0.1573 points, with a descriptive interval [-0.0289,0.3979]. The initial pilot's small positive mean does not carry over as established superiority on the wider surface. RAW_ALL must remain in the paper: adding an age-aware model did not make it the strongest delivery policy in this study. On a common held-out sensor/query probe, age-aware and age-ignorant report Brier losses are 0.058457 and 0.058151; neither supports a claim that this fitted aging model is uniformly better. Both improve on the no-report prior loss 0.085189 under that synthetic probe distribution.

The capacity figures, all-condition tables and paired contrasts show the tradeoff rather than selecting only finite-capacity cases that favor the proposed sender. In the response surface, the VALUE actor changes its next hop relative to an own-only probe at 13,829 actual routing calls; the original-family frozen-policy audit had no such ALL-versus-NONE changes. The new model therefore exercises information use, but information activity is not evidence of gate superiority.

## What has been resolved, and what has not

Resolved in code and checked: blocked roads cannot be traversed; failed attempts can consume time; physical deadlines create consequential outcomes; observations can arrive before commitments; old versus current information can change routing; radio waiting increases message age; FIFO capacity and time/path sums balance; all methods share closure schedules; sender decisions do not read live remote positions; the actor does not read remote closure truth; transmitted bytes are distinct from admission counts; and the admission ablation isolates filtering from priority/coalescing.

The new results identify a narrower algorithmic weakness: **the admission rule saves traffic but discards some useful information.** A static public-route relevance score and absolute belief change are not the actual marginal effect of a packet on a receiver's or fleet's on-time return. A receiver may reroute away from its nominal public route, already know a report, or need a clearance about an alternative. The fitted aging table also averages over persistent and recovering regimes and retains only limited information history. Better probability scoring alone need not improve on-time routing under this approximate planning objective.

Still missing for the intended MARL paper:

1. Train compatible belief/history-conditioned routing actors under matched communication methods, with documented features, true update rules, equal budgets, independent seeds and training diagnostics. Do not label the present planning comparison MARL.
2. Replace the heuristic admission score with receiver/fleet return effects estimated from complete-state paired packet interventions on training schedules. Features must remain public/actor-visible; neither simulator truth nor future outcomes enter the deployed gate.
3. Estimate uncertainty and validate harm/benefit decisions on separate data, including persistent warnings, genuine clearances, redundant packets, queue delays and confidence miscalibration. A posterior/count dispersion is not a calibrated safety certificate.
4. Compare against RAW_ALL, age-aware communication, warning/value priority without filtering, and matched safeguards. A resource-efficient claim requires an explicitly chosen delivery tolerance or cost objective before a new confirmation. The original primary delivery objective is not silently replaced with that alternative.
5. Freeze a final independent test and practically meaningful effect criterion; assess seed/graph uncertainty, scale, congestion and domain assumptions; then rewrite the manuscript and point-by-point response. No journal-ready claim or acceptance promise is warranted now.

The simulator-validity work is implemented and the complete development surface is executed. The delivery-superiority research goal remains unmet. The appropriate next work is a trained, consequential value-of-information policy, rather than another sweep that changes only a freshness threshold.

## Verification and delivery

The suite passes **142 tests**, including actual scout-warning benefit, stale/persistent report interpretation, queue-time expiry, path/time conservation, packet serialization, zero inspection delay, hidden-truth isolation, matched admission and partial-frame accounting. The reporter audits all convoy records, routing counts and packet logs; the full surface traces are losslessly partitioned and checked against original CSV hashes.

- [Eight-figure PDF](../deliverables/AIMRL-timed-network-figures.pdf).
- [Code, fitted model, primary raw data and results ZIP](../deliverables/AIMRL-timed-network-study.zip).
- [Tables and reproduction commands](timed-network-results/README.md), [offline figures](timed-network-results/index.html).
- [Pilot protocol](timed-network-development-protocol.md), [surface protocol](timed-network-surface-protocol.md), [matched admission protocol](timed-network-ablation-protocol.md).

Full decision/packet traces are provided in additional verified ZIPs to stay below GitHub's per-file size limit. After extracting the core ZIP, run `python simulator/fetch_timed_traces.py` to download, verify and extract all trace archives. The package manifest records every core and trace file. Archive verification and public download checks are recorded in the delivery validation JSON.
