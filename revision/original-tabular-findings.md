# Original tabular AMMARL: what reproduced and what changed

We returned to the submitted hub-indexed independent tabular Q-learning method and its fixed freshness/relevance/confidence (FRC) rule. This study contains no neural routing or learned message-value gate. All 17 uploaded source files remain byte-identical. The supplied-source execution, the closest repair bundle and scientific refinements are reported separately.

## Main result

The original M4 execution reproduces AMMARL's route-prior score **0.876374** and IQL's **0.857023**, matching the rounded **0.876 / 0.857** presentation values. Both methods deliver **100%** of convoys. The original AMMARL run records **zero hazard-buffer entries and zero hazard uses**, so these numerical differences do not demonstrate a communication-filtering benefit.

The original ungated score is **0.875512**, rather than the presentation value 0.851. NC and IQL execute identically and both score 0.857023; the NC presentation value 0.847 is not reproduced. Several classical baseline values also differ. These are reproducibility discrepancies requiring reconciliation, not evidence about the author's intent. The complete comparison is in [presentation_comparison.csv](original-tabular-results/presentation_comparison.csv).

The original field named survival is an average route-prior score, **not an observed survival probability**. Threat does not generate stochastic convoy destruction. The original cost field sums edge cost multiplied by traversal time; the repaired output also provides nominal edge-cost sums. For AMMARL, the original time-weighted cost is 50.703836, whereas realized nominal path cost is 13.949767. They must not be interchanged.

## What was repaired

The implementation retains tabular Q updates, the original reward family, graph, red-block mechanics and fixed FRC thresholds. It connects reports from genuine local hazard observations; identifies directed edges; clears episode state; rejects future, expired and duplicate packets; and gives fresh own observations precedence. It rechecks blocked alternatives, corrects occupancy bookkeeping and learns from completed physical transitions with appropriate terminal handling. It records actual delivery, failure, censoring, nominal cost, elapsed time and route-prior score separately.

The closest comparison preserves the original 300-episode curriculum, scoring coefficients, seed schedules and evaluation exploration. Its five repaired models have **exactly the same evaluated delivery, route-prior score, nominal cost and elapsed time** as the original AMMARL run. These repairs do not create a performance improvement in that setting. Original seed ranges overlap, so those five historical schedules are not described as fully independent environmental streams.

## Controlled refinements

We trained 80 tabular configurations using five non-overlapping training streams, four communication modes, two scoring specifications and two sensing contracts. Training totals 24,000 episodes; validation totals 4,320 method episodes. The locked test contains **43,200 method episodes / 129,600 convoy records**, six conditions, the original graph and eight graphs with fresh attributes in the same topology family.

- NONE ignores peer reports; ALL accepts eligible reports; FRC uses the original fixed rule; TRAVEL scales freshness by estimated traversal time. All modes within a scoring specification use the same routing coefficients.
- The code scoring specification is peer/local 8/2 with fork threshold 0.05. The manuscript specification is 12/8 with threshold 0.15. This changes both coefficients and fork criterion.
- Uniform sensing is closest to the original. Mixed sensing separately introduces a better-informed scout and partially blind followers. This is a scientific assumption change.
- Greedy evaluation and independent training streams differ from the historical experiment. Cross-layer differences cannot be attributed solely to the repairs.

**Every tested configuration delivers 100%. FRC and ALL have exactly equal delivery and route-prior outcomes throughout this test.** Uniform sensing produces zero peer-hazard score applications because fresh local observations dominate. With mixed sensing, FRC uses fewer reports than ALL, but this does not change the measured outcomes. Applications can reuse a packet and do not measure unique accepted messages or bandwidth savings; all modes still emit traffic.

In the code-scoring/mixed-sensing arm, FRC minus NONE changes the route-prior score by -0.000833 on the original graph and +0.008188 on fresh-attribute graphs. Corrected intervals include zero: [-0.004167, 0] and [-0.043195, 0.094000]. Neither is established superiority. The manuscript-scoring arms tie. All 48 comparisons are retained with the conservative 436-comparison correction, including earlier studies. No corrected benefit is supported.

Validation selects TRAVEL eta 0.4 in every scoring/sensing arm. TRAVEL applies zero peer reports in the test and matches NONE. A parameter selected under a delivery ceiling and cost tie-break does not establish a useful adaptive gate. Honest reports have confidence 1; resistance to unreliable confidence is not tested.

## Original CC2 is a separate demonstration

The supplied CC2 code has two unique scripted/Dijkstra paths, with several algorithm labels mapped to those same paths. Across 2,000 unique episodes, AMMARL-path and NC-path route scores are 0.9500 and 0.8282; both deliver 100%. AMMARL fuses reports, but this runner is not the tabular FRC algorithm. Its difference cannot validate the original tabular gate or be presented as seven independently trained algorithms.

## Defensible claim and next research decision

The submitted tabular method can be reproduced at several numerical anchors. The repaired implementation supports auditable physical transitions, communication activity and separated metrics. **This experiment does not establish FRC superiority over accepting all reports, improved delivery, combat survival, convergence or general network superiority.** Fresh graphs vary attributes within the same small topology family, not network scale or structural topology.

The central obstacle is mechanism opportunity: the original missions usually finish before the first red wave, fresh local sensing can make delayed messages redundant, and persistent blocked routes can be bypassed without convoy destruction. A 100% delivery ceiling leaves no delivery improvement to measure. Replacing the routing learner alone does not resolve this.

Before another superiority study, define an explicitly new, reviewer-justified environment with consequential information timing, limited local visibility and a meaningful range of deadlines or resource constraints. Validate these mechanisms independently, show that both useful and harmful messages actually change feasible decisions, and freeze broad evaluation conditions before testing. Include easy and adverse cases and retain null outcomes. This is a proposed next experiment, not evidence that the new gate will win or a retrospective repair of the earlier claim.

## Files and verification

The [eight-figure PDF](../deliverables/AIMRL-original-tabular-figures.pdf), [complete ZIP](../deliverables/AIMRL-original-tabular-study.zip), [tables and reproduction commands](original-tabular-results/README.md), [offline figure report](original-tabular-results/index.html) and [prospective protocol](original-tabular-protocol.md) are available together. The ZIP includes original files, raw training/evaluation records, 110 tabular inference checkpoints, settings and source code. Checkpoints are not exact optimizer/RNG training-resume snapshots. The regression suite passes 120 tests; bundle hashes and extracted-package report regeneration are recorded in the delivery validation file.
