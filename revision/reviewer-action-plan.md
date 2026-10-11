# Revision plan for IoT-66126-2026

Historical initial inspection plan. The manuscript was subsequently provided,
and the code was reconstructed. Use [the current model](complete-model.md),
[coverage](simulator-reviewer-coverage.md), and
[complete experiment protocol](complete-protocol.md) for current implementation
and experiment status; the observations below describe the original ZIP.

Based on the editor letter dated 1 July 2026 and an initial inspection of the unpacked simulator. This is an evidence and implementation plan, not a claim that the reviews are resolved. No manuscript was available for inspection.

## Submission requirements

The editor invites a reworked manuscript as a new submission with another peer review. Mention IoT-66126-2026 in the cover letter and Author Comments; provide a detailed point-by-point response and a manuscript with highlighted or underlined changes.

## Reviewer 1

| Item | Required revision | Current evidence and remaining work |
|---|---|---|
| 1: state and partial observability | Formally define observations, information history/beliefs, decision times, transition and reward model. Avoid claiming a Markov state or solved POMDP without justification. | GNN observations include hazard flags/ages and congestion. Audit information available to each actor: build_ctx currently reads network-wide busy/queue/flow arrays. Explain or restrict observability before making decentralization claims. |
| 2: deep learning and scale | Evaluate function approximation on larger networks with held-out graphs, multiple seeds, runtime and memory. | GNN agents and scaling scripts exist; README describes 39–483 nodes. Audit actual graph sizes, train/test separation and outputs. Synthetic scale does not establish real-world military validity. |
| 3: delivery cost | Separate nominal path cost, realized travel time, training reward and threat penalties. Define failure conditioning and compare identical starts/targets. | Core test checks delivered realized time against a nominal shortest-path lower bound. Add a direct nominal-cost invariant and inspect aggregation, including survivor selection. Do not compare survivor-only means as if they prove per-convoy path optimality. |
| 4: FIR | Either implement paired replay with one message suppressed and all other exogenous randomness controlled, or replace the original metric and clearly change its definition. | fir.py measures policy-level paired outcomes and decision changes, not isolated message effects. Its first-five-attack check is insufficient to verify full replay. Reactive attacks depend on policy and need separate causal treatment. |
| 5: freshness | Define and validate a congestion-aware corridor-specific expiry rule; sweep parameters across delay and network scales. | Scaled rule exists but uses distance to the reported edge source plus message delay, capped by tau_stale. Audit whether that distance reflects current traversal/congestion and whether it answers the requested corridor traversal scaling. |
| 6: baseline implementation | Document actor/critic features, reachable outgoing-action masks, rewards, optimization, budgets and tuning; compare under matched settings. | DQN/PPO/IPPO/MAPPO code exists. Audit masks, privileged actor information, centralized critic, update correctness and matched budgets. Passing checkpoint inference does not establish baseline fairness or convergence. |
| 7: queueing and AoI | State that age increases with elapsed time during waiting/service; verify expiry at departure decisions with an explicit queue-delay test. | Decisions occur at service end and age is computed from simulation time. Existing capacity test does not specifically validate information expiry while queued. |
| 8: adversary | Evaluate traffic-reactive threats with explicit observation, budget, response delay and adaptation rules; report limitations. | Reactive and spoofing modes exist. Audit reproducibility and attack comparability; a synthetic reactive rule is not a validated military adversary. |
| 9: blocked encounters | Define integer counts per convoy, episode totals, averaged counts and denominators; report uncertainty and exposure. | Integer-count invariant exists. Audit every table/figure aggregation; fractional averages are valid when explicitly labeled. |
| 10: ablation confound | Factor information filtering and response strength independently; compare no communication, all communication and gate across response weights. | Ablation/sweep scripts exist, but their existence does not prove that the original penalty confound is isolated. Design matched response-strength experiments; distinguish heuristic and learned responses. |

## Reviewer 2

| Item | Required revision |
|---|---|
| Abstract | Rewrite around problem, approach, evaluation and supported quantitative findings after final experiments. |
| Military adaptation | Explain the modeled interdiction, delayed/lost reports, spoofing, constrained hubs and threat uncertainty; delimit the synthetic model's applicability. |
| MARL motivation | Explain coupled congestion, distributed decisions and imperfect information; justify learning against strong planning baselines. |
| Gate rationale | Present freshness, relevance and confidence as hypotheses with costs and tradeoffs, not guaranteed benefits. |
| Gate operation | Provide equations/pseudocode, message fields, expiry/update ordering, confidence assumptions and a worked example. |
| Figure 1 | Match diagram labels to manuscript sections or explicitly distinguish them; audit once manuscript is provided. |
| Nine algorithms | Describe every final comparator, observations, action space, objective, communication, training and evaluation protocol. Reconcile the revised comparator list with Table III. |

## Work order

1. Obtain the submitted manuscript and any supplementary reviewer attachments. Preserve the original submission as a reference.
2. Audit simulator semantics, actor information access, baseline updates, metric aggregation and saved experiment provenance before launching costly runs.
3. Add targeted correctness tests and implement agreed methodological repairs in the development source with a clear version-controlled source strategy (currently code is shipped inside a tracked ZIP).
4. Freeze configurations and run matched held-out comparisons, response-strength ablations, congestion/freshness checks, reactive-adversary checks and scale measurements with multiple seeds and uncertainty intervals.
5. Rewrite manuscript claims and generate tables/figures from audited outputs; draft a point-by-point response linking each answer to an exact section, experiment or limitation.

## Claims to handle carefully

The repository README reports that unrestricted sharing helps in several settings, the heuristic gate is not a clear overall winner, and learned agents trade survival for shorter realized travel time. These are README statements pending experiment audit. Do not preserve claims that ungated communication is inherently harmful or gating is necessary and sufficient. Do not fabricate improvements or treat earlier setup smoke tests as scientific validation.

## Initial environment evidence

Five existing core tests passed during onboarding; 13 figures were regenerated, while training-curve Figure 2 was skipped; DQN/IPPO/MAPPO checkpoint inference and a two-episode DQN smoke training run passed. These establish executable development capabilities, not publication-ready experimental validity.
