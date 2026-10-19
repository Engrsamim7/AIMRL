# What is limiting the learned gate?

The diagnosis identifies a more specific bottleneck than simply insufficient training: **the learned gate changes many admissions, but has very limited influence over consequential routing decisions, and the benchmark rarely tests the information updates that could reward more adaptive behavior.** Prediction quality is also weak. A consistent deterioration after actor adaptation was not observed.

These are exploratory mechanism findings, not a new superiority claim. All original final checkpoints, estimators and results remain unchanged.

## 1. The architecture gives learning limited decision authority

On an identical earlier-packet interpretation, COMBINED can only add rejections to SAFE. Both share hard warning-preservation and clearance-corroboration constraints. Learning cannot admit a useful single-source clearance that SAFE's hard rule rejects; it also cannot reject a fresh, confident, reachable warning that the warning guard preserves.

The gate therefore does not learn a general accept/reject decision over all messages. Its available role is mainly extra rejection of other reports, including already corroborated clearances. This structural restriction should be explicit in the manuscript and in any next design.

## 2. Admission activity greatly exceeds routing influence

Across 512 reproduced COMBINED trajectories, the audit found **42,596 eligible packet candidates** and **18,429 admissions different from same-prefix SAFE (43.26%)**. This is an active filter, not a disabled component.

However, many differences concern reports with little routing relevance. All **7,493 extra warning rejections** concern publicly unreachable edges. The remaining extra rejections are clear reports. Under a public-state predicate—an immediate actor action-probe change, or an existing warning on a reachable edge—only **154 disagreements** qualify: **0.84% of disagreements**, or **0.36% of all eligible candidates**. That predicate is a diagnostic coverage rule, not proof that every excluded message has zero possible downstream effect.

The initial chronological sample had mostly selected inconsequential early packets. We therefore preserved it and added an explicit exploratory follow-up replaying **every one of those 154 relevant disagreements**, using no truth or outcome information for selection. Six packets overlap the initial sample; the two samples must not be treated as independent.

| Actor | Relevant packet pairs | Changed next edge | Changed receiver path | Actual rejection helped receiver delivery | Actual rejection harmed receiver delivery |
|---|---:|---:|---:|---:|---:|
| DQN | 106 | 28 | 30 | 7 | 4 |
| MAPPO | 48 | 9 | 9 | 2 | 2 |

Each pair forces admission versus rejection of one packet, preserves the remaining inbox and future messages, and runs both futures to completion. These are conditional packet effects; **9 helpful and 6 harmful effects cannot be summed into a fleet-level gain**, because packets and trajectories can interact. Most selected relevant packets still have no delivery effect.

This explains why high rejection activity is not persuasive evidence of improved routing, resilience or communication efficiency.

## 3. A simple conservative rule nearly matches the combined method

On exactly the same COMBINED-trained actors and diagnostic tapes:

| Actor | SAFE delivery | COMBINED delivery | KEEP-WARNING delivery |
|---|---:|---:|---:|
| DQN | 80.6250% | 81.2500% | 81.2500% |
| MAPPO | 81.7969% | 81.8750% | 81.7188% |

KEEP-WARNING never lets a peer clearance erase a fresh peer warning, even after claimed corroboration. Own observations and the existing TTL still apply. Its DQN delivery exactly matches COMBINED in this subset; MAPPO differs by two convoy outcomes out of 1,280. Utility and route costs can differ even when delivery matches.

These are descriptive fixed-actor results, not a retrained comparison, equivalence proof or independent confirmation. They nevertheless expose a strong simple alternative that any proposed learned benefit should be tested against.

## 4. The observed cases do not test useful genuine clearances

Among the **42,596 eligible candidates**, there are **zero genuine clear reports**, hence zero eligible genuine clearances challenging a warning. This statement applies to this audited subset; it does not assert that no honest clearance could ever occur elsewhere.

Some forged clear reports are correct by coincidence: there are 1,584 correct clear payloads challenging warnings. Genuine origin and current content correctness are different. Those reports must not be silently treated as genuine reopening observations.

Long-lived initial blocks and forward sensing often favor retaining warnings. Without decision-eligible genuine reopening information, the study gives little evidence about when a gate should safely accept a useful clearance. A learned model cannot demonstrate that capability when hard constraints forbid it and the evaluated opportunities are absent.

## 5. Prediction quality is weak before and after actor adaptation

All sixteen recovered warmup actors exactly match their recorded network hashes. Using 512 fresh factual label-generation episodes and 3,170 original-definition packet interventions, the unchanged estimator produced:

| Actor | Warmup-actor MAE | Adapted-actor MAE | Zero-predictor MAE, adapted actor |
|---|---:|---:|---:|
| DQN | 6.4503 | 6.6262 | 3.9802 |
| MAPPO | 6.6073 | 6.5027 | 3.2432 |

Values are mean absolute receiver-utility errors, equally weighted across eight seeds per actor family. DQN error increases slightly; MAPPO error decreases slightly. Individual seeds vary in both directions. **This does not support a uniform staleness explanation.** The earlier suggestion that stale estimates caused the weak result remains unproven.

The zero predictor has lower aggregate MAE, but that is not proof it makes safer decisions: most labels are zero, while rare consequential messages have large effects. `prediction_strata.csv` separately reports zero/nonzero targets and public action-change cases. On nonzero labels the original model is approximately as inaccurate as the zero predictor for DQN and only slightly better for MAPPO. Training the current regressor longer is therefore not an evidence-based solution by itself.

Warmup and adapted actors can encounter different states and messages even on matched physical tapes, so error differences do not isolate actor drift causally. These are diagnostic transport measurements, not an estimator ablation trial.

## 6. The training credit convention sometimes overstates an individual packet's deployment effect

For selected disagreement and warning-override packets, a second intervention removes later current-inbox packets in both futures, as in the original training labels. Some packets then affect delivery or utility even though they have no effect with the complete inbox. Future transmissions remain present in both conventions.

This shows a credit-context mismatch and message redundancy in some cases. It does not establish that all prediction error comes from the convention or that all messages with zero conditional effect are unnecessary. Joint effects need not equal the sum of single-packet effects.

## Concrete next design

1. **Fix the learning target and assess consequential updates.** Generate training labels from the actual deployed actor/gate states with the complete remaining inbox and future transmissions retained. Evaluate receiver and team effects, and handle rare large effects explicitly while retaining representative no-effect cases. Report prediction and decision quality separately on consequential updates; do not optimize aggregate MAE alone.
2. **Give learning a meaningful, risk-controlled choice.** A redesigned gate must be able to weigh genuine clearance against warning preservation under observable evidence, rather than being restricted to extra rejections. Keep a conservative fallback and test harmful as well as helpful overrides. Do not simply remove the guards that prevented earlier failures.
3. **Improve benchmark coverage for a justified operational reason.** Add physically observed temporary disruptions, genuine reopening updates, stale and false warnings, and costly or congested alternatives. Apply identical physics and information to all methods. Keep persistent-hazard, late-warning and no-hazard controls. Do not select durations, cases or outcomes to guarantee a winner.
4. **Include strong simple baselines from the start.** Train SAFE, KEEP-WARNING, appropriate fixed confidence/age rules and the learned method with matched actor budgets. Disclose auxiliary-label compute. Fix objectives, margins and success criteria before new validation/test results. If cost/latency becomes a primary objective, preregister it with an explicit delivery-risk constraint rather than relabeling the current delivery null.
5. **Then confirm on untouched data.** The diagnostic subset and targeted follow-up are now development evidence. Any redesigned gate needs new layouts, tapes and a locked confirmation protocol. The present findings do not promise that a more complex model will win.

The immediate research priority is **meaningful decision authority, representative communication opportunities, and useful value predictions**. Refreshing the estimator solely because the actor changed should not be treated as the established fix.

## Files and verification

See [all diagnostic tables and seven figures](gate-decision-diagnosis/README.md), [the original diagnostic specification](gate-decision-diagnosis-protocol.md), and [the targeted follow-up specification](gate-decision-targeted-followup.md).

The original 512 trajectories and 2,560 convoy outcomes reproduce exactly. Every full-inbox forced-original-choice branch reproduces the factual convoy outcomes. All 64 original checkpoint file hashes remain unchanged. Selected effects export both branches' complete convoy outcomes as JSON cells; raw data, code, reconstructed warmup weights and original matched-study context are included in the diagnostic ZIP.
