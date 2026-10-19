# Actor-aware fleet-value admission: development protocol

Specified before model fitting and the development audit, 19 October 2026. This follows a null corrected recovery study; that study is preserved and never reused as new confirmation. A feasibility check on the first32 fitting episodes counted actor responsiveness only, with no outcome-based setting selection. It found17–27 action-changing candidates per DQN seed and16–25 per MAPPO seed among roughly1,030 eligible packets.

## Hypotheses and scope

The prior gate's reference shortest-route features may fail to capture the neural actor's actual response. Receiver utility labels may also misalign with fleet utility. We will test public full-inbox neural-actor probes and fleet-level intervention targets, with a single override over the entire fleet episode. This makes post-override behavior exactly SAFE, matching the training rollout continuation. It deliberately restricts joint-message interventions and may miss deferred opportunities.

Use all sixteen existing final SAFE-trained DQN/MAPPO actors from the recovery study, frozen. They are existing routing-training seeds, not sixteen new independent algorithm-training replicates. No routing-network optimization occurs. This is a fixed-actor development experiment, not another matched-training superiority trial.

## Public probes and causal labels

At an otherwise eligible packet, copy the receiver's public/observed state. Interpret that packet once as accepted and once as rejected; retain and interpret the rest of the current inbox with SAFE, including timestamps, own-evidence precedence, seen IDs and claimed-source corroboration. Query the frozen actor scores in each completed public context. Never export or use the MAPPO privileged critic value; zero its global input before the diagnostic call. Hidden future events, active hazards, true packet origin and case labels are unavailable to deployed gate features.

Append23 public features to the original30: actual action change, SAFE choice, action relation to reported edge, actor score/probability margins (uncalibrated), nominal costs, resulting action beliefs and differences between the actor input contexts. Exact names/scales are in `actor_aware_gate.py`. These are public reference continuations. The changed-action predicate is not a claim that an unchanged next action implies zero future effect.

For training labels, clone the complete pre-decision simulator and force one eligible packet accepted/rejected. Retain every remaining current-inbox packet and all future events under SAFE. Verify the factual branch exactly reproduces all five outcomes, both next edges equal the public probes, and recovery/common-time attack schedules agree. Target the mean fleet utility and fleet delivery change from **flipping SAFE**, not the absolute packet truth or recipient-only effect.

Sample at most6 reachable action-changing candidates and2 other eligible candidates uniformly without replacement over each factual episode, with no unused-slot borrowing. Selection cannot use real origin or outcomes. Retain both branch outcomes and all selected zero effects.

## Opportunity reference, not a fabricated success

For each factual episode, compute the best nonnegative utility gain from a **single sampled flip**. Its chosen branch's delivery change must also be reported. This is an offline hindsight reference using future outcomes. It is not a public-information deployable policy, a globally optimized bound, a sum of packet effects, or proof that the gain is learnable. It covers selected packets only; an online gate can choose other packets, so it is not a guaranteed bound on that gate.

## Estimator and deployment

Fit two ExtraTrees regressors per existing actor/seed on identical reachable action-changing fitting examples, each with160 trees, depth8, minimum leaf8,80% bootstrap sample,80% feature fraction, seed95000+actor seed, two regression outputs. TREE_BASE sees the original30 features. ACTOR_AWARE sees all53. Both receive the same action-change eligibility restriction, one-override budget, data and setting grid. No scaling is fitted or needed for tree thresholds. Retain sampled non-action-changing cases for separate diagnostics; they are outside this gate's override authority, not assumed causally inert.

The gate falls back to SAFE unless the episode has used no override, the edge is publicly reachable and the completed-inbox actor action changes. Override SAFE only when predicted fleet utility gain minus beta times tree standard deviation exceeds the margin and predicted delivery change minus beta times its tree standard deviation is at least minus the tolerance. Tree dispersion is heuristic and not a calibrated uncertainty or safety bound. After the first learned override all later admissions are SAFE.

## Development splits and selection

Every layout is crossed with all8 original training conditions. No final-test conditions are loaded.

| Split | Layouts | Episodes per existing actor | Purpose |
|---|---|---:|---|
| Fit | 91000..91031,2/3 forks |256 | Fit estimators, labels only from this split |
| Calibration |92000..92007,2/3 forks |64 | Select inference settings and assess selection tradeoffs |
| Audit |93000..93007,2/3 forks |64 | Freeze settings first; evaluate development performance |

Environment tapes are800000000/810000000/820000000 plus layout-index*10000 plus condition-index*100, paired across methods and routing seeds. Layout and tape namespaces do not overlap previous studies. This yields6,144 factual episodes and4,096 fitting episodes across sixteen actors. Per-actor models maintain separate fitting labels. Very low support is a reportable failure, not permission to silently change this protocol.

Calibration tries beta0/.5/1, utility margin0/.5/1, delivery tolerance0/.01, plus explicit abstention to SAFE. Separately for algorithm and model, choose greatest pooled calibration utility among settings with delivery at least SAFE minus1 percentage point; ties prefer abstention then fixed candidate order. If no eligible setting, abstain. This tolerance is a development choice, not a safety guarantee. No audit-driven retraining, threshold change or physics change.

Lock estimator and parent checkpoint hashes before audit evaluation. On audit evaluate ALL, SAFE, KEEP, AGE, TREE_BASE and ACTOR_AWARE with the same frozen SAFE-trained routing actor. AGE uses the previous locked age8/confidence .4(DQN) or .6(MAPPO); it is a fixed baseline, not a separately retrained actor here. Audit comprises6,144 method episodes /30,720 convoy outcomes. Calibration evaluates39 configurations per actor/episode,39,936 method episodes.

## Decision and reporting

Report fleet utility and delivery together, all eight conditions, per-seed effects, actual overrides, sampled hindsight opportunity, and prediction error/decision sign on relevant and consequential examples versus zero prediction. Keep the feature ablation distinct from any improvement caused by changing estimator architecture or label target. Exploration intervals are conditional on these existing routing checkpoints; they do not create new independent training replication or establish superiority after earlier null studies.

A promising development mean is a reason to specify fresh matched retraining and untouched confirmation, not to rewrite the current paper as proven superior. If the opportunity reference is small, the estimator remains weak, or the deployment audit fails, report that result and identify the bottleneck. Do not manufacture helpful cases, remove unfavorable conditions, silently increase tolerance, or present privileged hindsight as an achieved method.
