# Fresh communication opportunity study

This study was specified before inspecting its test results. It tests a bounded hypothesis: **actor-specific message value filtering can improve delivery or mission utility over specified communication baselines when physically leading scouts supply novel corridor information**. It does not attempt to reproduce the original manuscript's headline percentages, establish universal superiority, or validate real military operations.

## Why this is different from the earlier study

The earlier adaptive gate produced no network next-action changes, and its low block prior plus evidence decay weakened useful warnings. This study builds physical opportunities for communication and trains a new value model from causal replay labels. The routing algorithms, packet interpretation and motion simulator are matched across communication modes. Original simulation source, checkpoints, results and audit artifacts remain preserved.

## Physical cases

Fresh randomized layouts contain two or three forks, with 11 or 16 nodes and 14 or 21 directed edges. Each fork has two cheaper potentially interdicted branches and a more expensive alternative. Public costs and prior risks do not depend on the episode's blocked-branch assignment. One of the cheaper branches at each fork is selected independently for an exogenous block. Each block has a declared duration; no algorithm knows its identity or expiry from simulator state.

Two scouts and three followers travel toward the same assigned target. Scouts depart near time zero; followers depart near the declared lead time. The same random departure jitter applies across policies. Scouts use radius-two sensing, so approaching a fork can reveal its outgoing hazard corridors; followers use radius-one sensing and cannot observe the two potentially interdicted outgoing fork corridors except in the redundant-sensing control. There are no extra observation links, scripted safety routes, privileged messages, or fabricated honest reports. The scouts choose their routes using the evaluated policy or trained actor. All vehicles count in full-delivery metrics; follower delivery is also reported separately.

The nine declared cases vary scout lead, message delay/loss, hazard persistence, misleading reports and sensing overlap. They include timely honest warnings; timely and delayed misleading reports; zero-lead late warnings; redundant sensing; short-lived hazards with honest and misleading reports; multiple impersonated identities; and no-hazard misleading reports. The executed `design.json` records their exact settings. All cases are retained regardless of outcome.

False reports use the same confidence distribution as honest reports. The attacker knows its own active interdictions but not future receiver routes. Its spoof schedule is exogenous. Reports can falsely clear active edges or falsely block other edges; claimed identities can be forged. Identifiers are opaque hashes and are never model features. Claimed independent senders are not authenticated observers.

The original 19-node topology is also evaluated as a descriptive transfer check. It uses stochastic exogenous attacks, reveal delay five, the original topology-based follower coverage gaps, two radius-two scouts and a common assigned destination. Its `short_lived` case labels do **not** change the original stochastic attack-duration distribution; only the constructed fork cases use that duration switch. Transfer results must therefore be interpreted under the actual recorded configuration, rather than treating identically configured bridge labels as distinct persistence conditions.

Channel-loss probabilities apply to honest broadcasts. Forged packets model receiver-side injection and do not undergo stochastic transport loss. This is an explicit threat-model assumption shared by all compared methods, rather than a claim about losses on a real contested radio network.

## Shared interpreter and routing actors

Every communicating method receives timestamped binary reports under the same outer TTL, rejects future/expired messages, and gives equally new or newer own observations precedence. Its retained peer belief uses the latest valid report for an edge. Hazard warnings enter the planner's shared additive penalty; the penalty is selected on separate validation schedules from 12, 40 and 80. Selection prioritizes delivery, then delivered time, then a smaller penalty. This is a validated discrete hazard response, not a calibrated probability posterior.

The planner is a deterministic shortest-path actor using public costs and prior threats plus the common binary hazard penalty. Fresh DQN and MAPPO actors use the existing local binary observation contract and two-layer GNN implementation. Three independent training seeds per algorithm receive 600 training episodes each, under communication ALL. Training covers all nine cases and separate layouts. MAPPO's privileged context is restricted to its centralized training critic; its actor and gate use local/public information. Actors are frozen for gate training, validation and testing. In each actor/seed comparison, all communication methods use exactly the same trained weights and training budget. This isolates filtering; it does not claim separate gated actor training or convergence.

## Learned actor-specific message value

For each frozen actor—including the planner—100 new training episodes produce chronological-prefix message interventions. At each of the first four nonempty routing inboxes, each eligible message is compared with its omission conditional on earlier packets. The remaining packets in the current inbox are removed from **both** branches, avoiding duplicate messages masking the usefulness of the first warning. Both branches retain later transmissions and run to completion. Full simulator, convoy, event and RNG state is copied; the complete attack schedule over shared time is checked for equality.

The receiver-utility label is inclusion minus omission, where

`utility = 40 × delivered − 40 × destroyed − 40 × censored − elapsed time`.

This captures a message's effect on actual delivery and time for the specified actor. It is a conditional marginal label, not a game-theoretic allocation of interacting messages' total value. It can be positive, negative or zero. The message's evaluation-only genuine/spoof flag is retained in the dataset for auditing and excluded from all model features.

Public features include age, reported confidence, prior own/peer beliefs, later-local-observation sender agreement, conflicting reports, public reference-route alternatives, changed actual actor action, and counts of fresh claimed source support. Actor action probes use the frozen actor's logits or Q action ranking; no centralized critic values, active-attack sets, future outcomes or packet-origin identifiers enter the feature vector. Prefix probes are isolated from factual state and random streams.

Episodes 0–79 fit five bootstrap ridge regressors per actor; episodes 80–99 provide an internal held-out error diagnostic. Feature normalization uses fit data only. Ridge strength is fixed at 10. The gate admits a valid packet when

`mean predicted utility − uncertainty_weight × ensemble disagreement > threshold`.

Disagreement is a heuristic uncertainty measure, not a calibrated confidence interval. Rejected valid reports still enter local agreement/corroboration bookkeeping. Agreement updates use later declared own observations; they do not certify honesty and can be affected by changing hazards. Fresh episode state starts empty.

## Baselines, selection and tests

NC disables peer use and broadcasts. ALL admits every otherwise valid report. FRC adds corridor-travel freshness, confidence and public reachability filtering at admission; all methods then retain reports under the common TTL. Its freshness multiplier is validated over 1, 2, 4 and 8, and confidence threshold over 0.4, 0.6 and 0.8, using the same validation schedules and pooled selection criteria as VALUE. SAFE-ALL rejects a lone clear report that would erase a fresh warning, allowing two fresh claimed clear sources; it is a simple conservative comparator. VALUE uses learned utility filtering. No-uncertainty and no-feedback variants ablate the fitted gate while preserving actor weights and other settings. All receiver filters send reports before admission, so reduced admissions are not bandwidth savings.

Separate validation selects one threshold from −1, 0 and 1, and one uncertainty weight from 0 or 0.5, pooled across actor families and seeds. It prioritizes delivery, then delivered elapsed time, then fewer admissions, requiring at least 5% genuine admission. Selected settings and a source hash are saved before unlocking testing.

Testing uses ten new randomized layouts, 20 independent episode schedules per layout/case, and an original-topology transfer check with 10 schedules per case. Environment tapes and departure/target assignments are shared across methods and training seeds. This yields 92,610 paired-method evaluation episodes and 463,050 convoy records. Parameter, training, validation and test namespaces are separate and recorded in the design. Neither prior adaptive-v1/v2 test episodes nor the opportunity audit is used as training data.

Primary comparisons are VALUE against ALL, FRC and SAFE-ALL in each of nine cases for three actor families: **81 comparisons**. Report absolute delivery differences with simultaneous paired bootstrap intervals, sampling layouts and episodes and crossing independent training seeds with the same environment schedules. Full convoy delivery is primary; follower delivery, mission utility, time, cost, packet admission, ablations and original-topology transfer are complementary endpoints. Common-survivor time/cost comparisons retain only convoy pairs delivered by both methods.

Any supported claim must name the actor, baseline and condition. A gain over ALL that vanishes against SAFE-ALL supports a conservative filtering mechanism rather than a learned-value advantage. A gain in the constructed benchmark without transfer to the original topology remains a benchmark result. Adverse and zero-effect conditions remain part of the reported evidence.

## Guarded confirmation after the unconstrained learned study

The unconstrained value model sometimes rejected useful warnings in the first frozen-test study. Its complete data and corrected results are retained. The next architecture adds two public-state constraints: a fresh confident hazard warning on a public-reachable edge is preserved regardless of predicted utility; a lone clear report cannot erase a fresh warning. Once a clearance is corroborated by two claimed sources, learned utility still decides its admission. This is a hybrid conservative/learned gate, not an unconstrained optimal message-value policy. Predicted utility is logged unchanged; an explicit admission-rule field records constraint overrides. No simulator labels or future states enter either constraint.

The guarded study reuses the six actors, seven utility models and training data from the first study; it does not fit to that study's test labels. Its numeric threshold and uncertainty weight are selected on new validation layouts 47500–47509 and tapes 41100000+. It then tests on layouts 48000–48009 and tapes 44000000+, again publishing all nine cases and the original-topology bridge. It yields another 92,610 evaluation episodes and 463,050 convoy records. Warning-confidence and FRC settings inherit the earlier validation selection. This study records guard-removal ablations rather than the earlier uncertainty/feedback ablations.

The guard change responds to observed first-study failures, so the second study is a new confirmation experiment, not an independent method chosen without any exploratory evidence. Its intervals use a conservative 162-test correction accounting for 81 earlier and 81 current comparisons. Training seeds remain shared across the two studies; they must not be counted as six independent training seeds per algorithm. All initial negative/adverse results remain accessible. Multiple forged identities can still satisfy a nominal quorum, and learned utility may misclassify reports; these cases bound the resulting claim.

## Frozen-model balanced cover-traffic stress

The original spoof process preferentially sent clear statements about active blocks. A sufficiently strong neural actor can learn that the presence of such a report is itself correlated with an interdicted corridor. A third robustness check removes that target/payload correlation: forged packets choose public potential hazard corridors uniformly and assert block/open with a fair coin, independently of current truth and victim plans. Some forged statements are correct by coincidence; `genuine=False` denotes forged origin, not guaranteed false content. This new attack distribution is **not** used to retrain actors, utility models or select numeric parameters.

Four predeclared conditions cross rates 2/6 and delays 1/4, with loss 0.1, scout lead 4 and 90% claimed-identity impersonation. Fresh layouts use 49000–49009 and environment tapes 45000000+. All five methods use identical frozen actor weights within each actor/seed, inherited FRC and VALUE settings, and matched physical states. All four conditions are retained. This adds 28,000 evaluation episodes and 140,000 convoy records, for **213,220 total fresh-study test episodes and 1,066,100 convoy records** across the three stages. The later two stages add no training seeds.

Its 36 delivery comparisons use a conservative 198-test correction accounting for the preceding 162 comparisons. Interpret any neural gains as resilience of these frozen actors under a specified corruption shift; superiority after all baselines retrain on cover traffic remains untested. Compare against SAFE-ALL to distinguish learned utility from conservative warning protection. Raw episode and convoy data are exported for the cover stress; its individual packet logs are not exported, and communication counts remain available per episode.

The final combined reports recompute the earlier two studies' intervals with the same **198-comparison correction**, so the total published family uses one conservative correction across all three stages. Original prospective designs and settings remain recorded; raw outcomes, fitted weights and numeric settings are unchanged by this reporting adjustment.
