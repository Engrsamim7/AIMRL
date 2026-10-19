# What changed, what the new results support, and what comes next

**The redesigned simulator and experiment are complete, but they still do not establish learned-gate superiority.** None of the six primary baseline/algorithm comparisons met the joint utility-superiority and delivery-noninferiority criterion. None of the 140 new contrasts showed a corrected positive or negative difference. This is an inconclusive result, not proof of equivalence or a proof that no better gate is possible.

The stronger implementation removes two previously demonstrated obstacles: learning now has meaningful acceptance and rejection authority, and the benchmark supplies physically observed, eligible reopening reports. The remaining evidence points toward weak value estimation and sparse consequential packet effects. It does not justify another claim that the gate simply needs more favorable scenarios.

## What was implemented

- Real temporary disruptions and scout-observed reopening broadcasts, with persistent-hazard, delayed-communication and no-hazard controls. No fabricated honest reports, scripted routes or truth-aware feature inputs.
- A bounded learned gate that can override SAFE in either direction, subject to estimated message value, heuristic delivery-risk checks and at most two overrides per receiver/episode. These checks are not calibrated safety guarantees.
- Complete-inbox accept/reject training labels from frozen neural actors; later messages and future events remain present, and the factual branch must reproduce all five convoy outcomes.
- Three nonlinear bootstrap hurdle estimators, a delivery-risk head, training-only normalization and a mid-adaptation label/model refresh. Refresh adds data as well as changing actor context; it does not isolate staleness.
- Five separately adapted methods: ALL, SAFE, KEEP, AGE and LEARN. Every final actor receives the same 300-episode warmup state and 300 paired adaptation episodes. Auxiliary gate computation is additional.
- Eight independent paired training seeds per DQN/MAPPO algorithm, 80 final neural routing checkpoints, validation-only inference setting selection, and settings/checkpoint/estimator hashes locked before final results.
- Eight figures, offline HTML, every condition's means, all corrected contrasts, raw records, complete source and a portable ZIP. See [implementation contract](../simulator/RECOVERY_GATE_METHODS.md) and [reviewer map](recovery-gate-reviewer-map.md).

The prospective [protocol](recovery-gate-protocol.md) was committed before training. Locked settings were published on the review branch before final results. Earlier studies and their fingerprints remain unchanged.

## The actual primary results

The primary objective was fleet mission utility, `40*delivered - 40*destroyed - 40*censored - elapsed`, with delivery required to be noninferior within one percentage point. Utility includes every convoy. This objective was specified before the new run; it does not retroactively turn the earlier delivery null into a success. The tolerance is a simulation engineering choice, not an operational safety standard.

| Algorithm | Baseline | Utility difference, LEARN minus baseline | Corrected interval | Delivery difference, percentage points | Corrected interval, pp | Joint success |
|---|---|---:|---|---:|---|---|
| DQN | SAFE | +0.135 | [−1.857, +2.277] | +0.184 | [−2.753, +3.305] | No |
| DQN | KEEP | +0.591 | [−1.255, +3.068] | +0.811 | [−1.926, +4.398] | No |
| DQN | AGE | −0.024 | [−1.758, +1.537] | −0.059 | [−2.594, +2.223] | No |
| MAPPO | SAFE | +0.360 | [−0.529, +1.295] | +0.516 | [−0.777, +1.846] | No |
| MAPPO | KEEP | +0.170 | [−0.655, +0.958] | +0.266 | [−0.897, +1.383] | No |
| MAPPO | AGE | +0.333 | [−0.510, +1.293] | +0.471 | [−0.717, +1.843] | No |

Intervals use 200,000 crossed paired bootstrap draws over training seeds and layout/episode clusters, with the predeclared conservative 388-comparison correction. Eight seeds, not 512,000 convoy observations, supply training replication. MAPPO meets the pooled delivery-noninferiority criterion against the three conservative baselines, but does not establish utility superiority. DQN does not establish either co-required criterion. Lack of a corrected harm finding does not establish safety.

Mean delivery is 88.252% LEARN versus 88.068% SAFE for DQN, and 88.971% versus 88.455% for MAPPO. These small mean gains are not statistically supported superiority. The full [results tables](recovery-gate-results/README.md) also retain ALL and every per-condition result, including unfavorable means and controls.

## Why the proposed fixes did not produce a defensible win

**The gate is active and reopening opportunities are present.** Across LEARN final-test trajectories, the audit counts 54,392 eligible genuine clearances challenging peer warnings: 27,026 DQN and 27,366 MAPPO. LEARN makes 53,884 overrides of SAFE, including 8,242 acceptances and 45,642 rejections. These are repeated decision counts, not independent samples or proof of benefit. They rule out describing this run as a disabled gate or a benchmark with no genuine reopening evidence.

**Most individual packet labels remain inconsequential.** From 2,048 auxiliary factual episodes, the run exports 12,934 paired intervention labels. Only 1,125 (8.70%) have absolute receiver-utility effect above the declared .1 threshold. Later inbox reports, future observations, route redundancy and the routing actor can mask an individual report's marginal contribution. This count does not mean those messages could all be removed jointly without harm.

**Value estimation remains weak on internal holdouts.** For the refreshed estimator, equally weighted mean absolute error across eight seeds is 3.208 versus 1.523 for predicting zero effect in DQN, and 2.688 versus 0.915 in MAPPO. Even on effects above .1, errors are 22.062 versus 20.147 for DQN, and 20.372 versus 16.848 for MAPPO. These holdouts have few consequential examples, so they are diagnostic rather than a precise estimate of decision risk. See `prediction_strata.csv`; aggregate accuracy on near-zero examples is not sufficient.

**Correct content is not the same as useful action.** Among sampled genuine clearances challenging warnings, accepting the report helps receiver utility in 136 DQN / 82 MAPPO pairs and harms it in 66 / 80 pairs, using the .1 threshold. Delivery effects are rarer. These outcome-independent public-stratum samples are training diagnostics, not population effect estimates; they cannot be added into a fleet gain. A truthful clearance can still change the neural actor's route or timing unfavorably.

**The acceptance-authority ablation does not show a meaningful fleet gain.** On independent descriptive fixed-LEARN-actor tapes, deployed LEARN versus rejection-only delivery is 89.656% versus 89.688% for DQN, and 89.203% versus 89.203% for MAPPO. Utility differs by roughly −0.002 and +0.004 units respectively. This is not an equivalence test, but it gives no persuasive evidence that extra clearance acceptance drives a benefit. The initial-estimator swap also does not demonstrate a refresh advantage; it changes data quantity and actor context together.

## What can be claimed now

A defensible statement is:

> We implement and evaluate bounded, value-based communication admission under physically observed dynamic recovery. Across the specified held-out conditions, the learned method exhibits small mean gains against several baselines, but conservative corrected intervals do not establish superiority. Strong simple baselines remain competitive, and sparse consequential updates and inaccurate value estimates limit the demonstrated benefit.

Do not claim universal superiority, proven delivery improvement, calibrated safety, convergence, bandwidth savings or operational military validation. These are small structured fork graphs: held-out 3/4-fork sizes are 16/21 nodes, not a new large-network scaling or realistic geographic study. The new study does not complete manuscript rewriting or every reviewer concern.

## The next research decision

The immediate recommendation is to **revise the manuscript around the evidence rather than preserve its earlier superiority assertion**. The complete simulator and transparent comparisons are usable; the current estimator's superiority is not established.

If another algorithm-development phase is chosen, first use training-only data to estimate the attainable benefit and held-out decision quality on consequential, actor-relevant messages. Compare the learned gate with an explicitly labeled offline oracle-assisted reference and strong simple rules. Oracle-assisted choices are diagnostics using privileged information, never a deployable comparator or public-information method; a greedy oracle is not a guaranteed global upper bound. A future estimator could target action-conditional or joint-message effects and better align receiver labels with fleet utility. Test calibration and abstention on development holdouts before spending another large final-evaluation budget. Any changed model needs a new protocol and fresh confirmation environments. Adding favorable cases or weakening correction after this result would not validate the current claim.

## Access and verification

- [Eight-figure PDF](recovery-gate-results/recovery_gate_report.pdf) and [offline HTML](recovery-gate-results/index.html).
- [Every result table and reproduction commands](recovery-gate-results/README.md).
- Full delivery: `deliverables/AIMRL-recovery-gate-study.zip`, with source, 80 inference checkpoints, 32 gate estimators, training records, labels, validation selection, locked settings, 102,400 test episodes / 512,000 convoy records and 7,680 ablation episodes.
- `verification.json` records raw-accounting, reconstructed utility, pairing, checkpoint hashes and sample-size audits. The ZIP has a per-file SHA-256 manifest and archive checksum. All 102 regression tests pass. Clean-extraction reproduction and public-download checks are recorded separately in the delivery validation sidecar.
