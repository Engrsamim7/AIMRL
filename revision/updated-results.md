# Updated reconstructed-simulator results

The stronger rerun is complete. It uses 36 newly trained checkpoints, 60 episodes per model with standard optimizer settings, three training seeds, and 12 convoys. These are exploratory synthetic-network results; convergence, real-world validity and a general communication-gate advantage are not established.

## Execution and validation

- 2,160 training episodes; original data and old smoke artifacts were preserved.
- 6,450 held-out evaluation episode runs: 10 fresh graphs × 5 episodes × 43 instantiated policies in each of three scenarios. The 43 policies comprise 7 heuristics/diagnostics and 36 learned model instances (12 algorithm/communication configurations × 3 seeds).
- 1,032 graph-size inference episode runs across 39, 51, 203 and 483 nodes.
- 12,500 full-factorial gate/response-strength ablation episode runs.
- 7,127 exact single-message interventions, covering every decision-processed packet in 20 factual all/gate episodes, including rejected packets.
- Artifact audit passed: completed manifests, current source hashes, positive optimizer updates, finite training losses, matched convoy schedules, complete per-method evaluation coverage, summary/raw agreement, integer encounter counts, nominal shortest-path bounds, elapsed-time decomposition, zero-strength outcome equality, and replay denominators.

Training worker directories and the merged training directory contain the same checkpoints; their counts must not be added together. Every command and parameter is recorded in its manifest. Runtime excludes allocation instrumentation and is descriptive on shared cloud hardware.

## Held-out delivery

Values average matching graph/episode schedules; learned results also average the three trained seeds. Graph-only delivery intervals in the figure are conditional on these fitted models. See the contrast figure for paired graph and training-seed resampling.

| method     |   Random attacks (%) |   Disrupted / spoofed (%) |   Reactive / targeted (%) |
|:-----------|---------------------:|--------------------------:|--------------------------:|
| B1         |                49.67 |                     49.67 |                     19.83 |
| B2         |                79.17 |                     79.17 |                     27.67 |
| B3         |                79.00 |                     79.00 |                     47.17 |
| NC         |                86.67 |                     86.67 |                     34.33 |
| COMM-ALL   |                89.17 |                     87.17 |                     59.50 |
| GATE       |                87.83 |                     86.67 |                     34.67 |
| ORACLE     |                99.17 |                     99.17 |                     91.17 |
| dqn-none   |                80.17 |                     80.17 |                     62.00 |
| dqn-all    |                79.06 |                     76.94 |                     61.72 |
| dqn-gate   |                78.67 |                     78.67 |                     64.61 |
| ppo-none   |                85.33 |                     85.33 |                     47.89 |
| ppo-all    |                82.00 |                     79.06 |                     42.50 |
| ppo-gate   |                82.61 |                     82.11 |                     49.11 |
| ippo-none  |                40.39 |                     40.39 |                     47.44 |
| ippo-all   |                38.67 |                     37.83 |                     50.39 |
| ippo-gate  |                38.00 |                     37.89 |                     43.22 |
| mappo-none |                79.00 |                     79.00 |                     41.78 |
| mappo-all  |                80.11 |                     76.83 |                     38.72 |
| mappo-gate |                84.83 |                     84.00 |                     46.22 |

## Interpretation

The heuristic travel gate has no clear delivery advantage over accept-all in the random or disrupted/spoofed scenarios. Under reactive/targeted threats it reduces delivery by 24.83 percentage points, with an exploratory paired graph-bootstrap 95% interval of −31.50 to −17.67 points.

Learned gate-versus-all effects are mixed. In the reactive scenario, gated DQN averages 64.61% versus 61.72% for accept-all DQN, but its paired interval crosses zero (−0.22 to +6.17 points). MAPPO's difference is +7.50 points (+0.56 to +14.56); IPPO's difference is −7.17 points (−12.33 to −0.83). These intervals are exploratory and are not adjusted for multiple comparisons. Three training seeds give limited evidence about retraining variability.

The disrupted-scenario strength-12 ablation shows 0.02 spoofed packets accepted per episode by the travel F/R/C gate versus 157.88 by accept-all. Genuine accepted packets also fall from 34.46 to 0.38 per episode. This supports a filtering-versus-information tradeoff; rejecting spoofed messages alone does not establish a delivery benefit. At strength zero all communication/filter variants produce identical movement outcomes, as intended.

Exact replay changes 18 receiver paths out of 7,127 interventions. All 18 occur with accept-all (3,554 processed packets), with one helpful and three harmful receiver-delivery effects. The remaining 7,123 interventions do not change receiver delivery. The gate has no changed paths or receiver-delivery effects in its 3,573 replayed packets. Replay effects are conditional realized continuations, not expectations over unseen future randomness. Controlled replay uses random attacks and exogenous spoofing; reactive/targeted traces are policy-dependent and are evaluated separately.

Larger-network results hold convoy population and attack budget fixed, so threat density varies with size. High delivery on large graphs does not establish robustness at constant threat density. The true-state oracle is a diagnostic, not a proven optimal upper bound. Confidence scores are simulated and do not provide authentication.

## Figures and reproduction

[Seven regenerated figures and combined PDF](updated-visualisations/README.md) cover the overview, training curves, scenario delivery, paired gate contrasts, graph-size inference/runtime, filtering/strength ablation, and message replay.

[Experiment protocol](rerun-protocol.md). From `simulator/`:

```bash
python validate_results.py out/reviewer-rerun-v2
python plot_updated_results.py --run-root out/reviewer-rerun-v2 --output ../revision/updated-visualisations
```

Source SHA-256: `596294a014a198d970957e41fc6bf55b92563518b0e73ac507159553cb50babd`.
