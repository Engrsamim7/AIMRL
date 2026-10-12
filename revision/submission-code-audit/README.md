# Audit of supplied pre-submission code

The 17 uploaded files are preserved byte-for-byte under `revision/submission-code/`, with SHA256 inventory. This audit distinguishes executable simulation results from generated presentation data. It does not infer intent or establish where fixed constants originally came from.

## Findings

| Issue | Evidence | Implication |
|---|---|---|
| Presentation pipeline contains manuscript numbers as constants | `final_pipeline.py:202` defines `PAPER_FINAL`, including 0.876 gated, 0.857 IQL and 0.851 ungated; `PAPER_STD` is also fixed | These tables are not recomputed from raw simulator episodes in this pipeline. Original provenance of constants remains unverified. |
| Training curves and significance generated mathematically | `gen_traj` uses sigmoid endpoints and Gaussian noise; `pval` tests generated trajectory windows | These curves cannot demonstrate actual optimization or convergence; their p-values cannot validate simulator treatment effects. |
| Sensitivity plots are constructed | `vs_A` peaks around chosen thresholds; `val_B` is a fixed array; `val_C` is a quadratic centered at 8 | They are not executed validation sweeps and cannot establish parameter robustness or global optima. |
| Original M4 gate has no hazard source | `run_gated_episode` receives HAZARD payloads but does not broadcast them; general core defines message scheduling but does not autonomously send hazards | Five original-runner smoke episodes yielded zero hazard-buffer entries and zero hazard uses. Gate benefit cannot be attributed to filtering in those episodes. |
| Claimed ablation changes more than filtering | Gated scores use peer strength 8 and fallback strength 2 at forks; NoGate uses strength 6 wherever a buffered report exists | Original gated/no-gate comparison does not isolate F/R/C filtering. These strengths also differ from manuscript 12/8. |
| Episode information leak possible | `GatedQAgent.reset` does not clear `hazard_buf`; `_gate_check` accepts any age <= threshold, including negative ages | Executed fixture retains a report after reset and accepts a future-dated timestamp. An active hazard source could expose cross-episode contamination. |
| CC2 uses a different sensing contract | `CC2Sim._update_belief` prevents followers from refreshing corridor threats; scout broadcasts actual corridor threat with confidence 1 | Communication can influence this scenario. It resolves the local-sensing overwrite issue specifically for CC2, not general M4. |
| CC2 algorithm labels reuse the same runner | `ammarl_gated_eval.py:625` sends B1/B2/B3/IQL/NC through NC CC2 runner, and AMMARL/MAPPO through AMMARL CC2 runner | This is a communication-mode demonstration, not an independent comparison of all named algorithms in CC2. |
| Survivability is not delivery probability | Core `avg_surv` averages edge values; stats average only delivered convoys | Separate route-prior threat score from delivery, destruction and censoring. Survivor conditioning can bias comparisons. |
| MAPPO label is not PPO implementation | Supplied MAPPOAgent uses softmax tabular Q, local V and additive updates, without PPO clipped optimization or privileged centralized state | Rename as a custom baseline or replace with documented PPO/MAPPO implementations. |
| Supplied tuning contradicts general M4 superiority | All 50 CSV rows have gated M4 route score below IQL | Available tuning output does not substantiate the manuscript's M4 superiority claim. Eight rows have higher gated CC score, so CC results are condition dependent. |

## Executed checks

`simulator/audit_submission_code.py` imports the original core and CC2 definitions and extracts only the selected agent classes and gated episode function using AST. It does not execute final_pipeline or the top-level gated training campaign. Preserved originals are unmodified.

- Five M4 original-runner smoke episodes, fixed original network seed 42: zero hazard entries and uses.
- Twenty paired original CC2 episodes: mean route-prior score AMMARL 0.9500 versus NC 0.8333; both delivery 1.0000. Mean nominal cost AMMARL 62.4614 versus NC 61.9541. Six fused reports per AMMARL episode.
- Direct future-timestamp and reset fixtures reproduce the buffer/freshness issues.
- CSV audit covers all 50 uploaded tuning rows. These are supplied aggregates, not independently reproduced tuning runs.

The CC2 fixture means are descriptive smoke results, not a full five-seed 200-episode reproduction or significance analysis. The 95% route score is not evidence of a 95% delivery probability. In the supplied CC2 runner adversarial attack budget is zero; the scenario communicates hidden route threat rather than measuring actual attack-induced losses.

## Correction of the previous diagnostic's scope

The earlier synthetic comparator made newer local reports supersede delayed peer reports. The original GatedQAgent does not compare its hazard buffer to newer own timestamps; the original M4 pathway is instead inactive because no HAZARD broadcaster is connected. Original CC2 explicitly preserves followers' unknown corridor beliefs and uses a separate fusion/scoring path. Therefore the earlier 24,000-episode finding applies to that synthetic comparator, not to every original code path. The exact original topology can now be exported from `make_network`; the diagram in final_pipeline is a different hard-coded presentation graph and must not be silently substituted.

## Next implementation work

Use the actual original graph and scenario constructors as references. Preserve a historical runner, connect genuine hazard reports through explicit sensing/latency rules, clear transient episode state, reject negative message age, and use one scoring formula with matched coefficients across NC/ALL/FRC. Implement CC2 sensing asymmetry explicitly and separately test each gate condition. Keep the repaired deep baselines and event/queue/replay audits. Generate every scientific table and plot from raw executed records, with model/config hashes and paired scenario schedules. Fit thresholds on validation data only; evaluate on new schedules and disclose negative outcomes.

Before claiming reproduction of the submitted figures, reconcile the presentation constants with original raw logs and confirm which pipeline produced the submitted artifacts. Without those logs, treat them as unverified historical values and replace evidence with executed results.

Run the audit after installing networkx in the existing project environment:

```bash
MPLCONFIGDIR=/tmp/aimrl-mpl python simulator/audit_submission_code.py
```

Raw checks are in `audit.json`, `m4_smoke.csv`, `cc2_smoke.csv`, and `fixed_presentation_anchors.json`. The audit is read-only with respect to original inputs and writes only audit outputs.
