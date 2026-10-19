# Prospective matched-training gate study — 19 October 2026

This protocol and executable design are saved before new training or evaluation. Earlier frozen-model results motivated the question; their outcomes do not select new test episodes. Every declared condition will be reported, including negative and inconclusive results.

## Question and factorial comparison

Does learned message value add delivery benefit beyond conservative safeguards when each routing model adapts to its own communication method under the same corruption distribution?

Four arms form a 2×2 comparison: ALL (no learned filtering, no guards), SAFE (guards only), VALUE (learned filtering only), and COMBINED (both). Both guard arms use exactly the same warning preservation and clearance corroboration code. SAFE is therefore a new factorial baseline; it is not silently equated with the earlier SAFE-ALL implementation, whose handling of own versus peer warnings differs. A constant admit score replaces learned prediction when the learned factor is off. The ALL arm is checked against ordinary unfiltered communication.

## Matched routing training and auxiliary data

DQN and MAPPO each use eight fresh paired seeds, increased from three. Each seed starts from a fresh initialization and receives 300 common ALL warmup episodes. Four copies preserve identical network, optimizer, replay and random-generator state. Each copy then receives 300 additional episodes under its assigned arm, using identical environment tapes and the same case cycle. Each final actor has 600 episode exposures. This is matched adaptation after a common warmup, not gate-specific training from initialization. Routing architecture, optimizer settings, sensing, costs and reward remain shared. Episode budgets are equal; realized transition and optimizer-update counts can differ because trajectories differ, and are recorded.

For each frozen warmup actor, 160 auxiliary factual episodes generate chronological-prefix inclusion/omission utility labels using the independent cover-traffic attacker. Episodes 0–127 fit five bootstrap ridge regressors; 128–159 are internal prediction holdout. All four arms have the same auxiliary dataset available, but only VALUE and COMBINED use it by definition. The extra replay and regression compute is disclosed; this is not a claim of equal total computation. The value model stays fixed during adaptation. It estimates value for the warmup actor and may become stale as routing adapts. No post-test refitting is permitted.

Training covers cover-traffic rates 2/6 and delays 1/4, honest reports, late warnings, redundant sensing and no hazards, on 2/3-fork layouts. Two scouts have radius-two sensing; three followers have radius-one sensing with declared fork blind spots. Most conditions have scout lead four. Every vehicle counts in delivery. Forged targets and block/clear payloads are independent of live hazards and future routes; claimed identities remain unauthenticated. Honest channel loss does not apply to receiver-injected forged packets. No private attack state, origin label or future outcome is a gate feature.

Fixed settings are inherited explicitly from earlier methodological choices: response strength 12, gate threshold −1, uncertainty weight 0.5, warning confidence 0.4. New validation is diagnostic only; it does not tune or select models, thresholds, epochs or cases. No early stopping. Checkpoint hashes and settings are locked before opening final tests.

## Held-out evaluations

Training layout namespace: 55000–55059; auxiliary: 56000–56039; validation: 57000–57003; final: 58000–58015. Random tape namespaces 60,000,000 through 65,000,000 are distinct and recorded by the executable design. The exact layout generator and seed identify each graph.

Final testing crosses eight cases, sixteen layouts, ten environment episodes, eight training seeds, two algorithms and four methods: 81,920 method-evaluation episodes. Layouts alternate three and four forks: the four-fork size is absent from training. Four cover conditions match training parameter values but use new graphs and tapes. Two conditions have unseen rates 4/8, loss 0.2, and delay 2/1. Late-warning and no-hazard controls remain. All eight cases receive equal weight in the pooled primary endpoint.

An additional 10,240 descriptive evaluations hold the COMBINED-trained actor fixed and swap SAFE versus COMBINED filtering on four further layouts/tapes. This separates immediate filtering effects from actor coadaptation. It is not an independent training replication or an additional confirmatory hypothesis family.

## Hypotheses and statistics

The primary endpoint is COMBINED minus SAFE full-delivery rate, averaged equally across all eight cases, separately for DQN and MAPPO: two hypotheses. Forty-eight secondary confirmatory comparisons contrast COMBINED against ALL, SAFE and VALUE in each algorithm/case. Report all fifty, regardless of outcome.

Use paired bootstrap sampling of graph clusters and within-graph episodes, crossing the resampled independent training seeds with the shared environment tapes. For pooled comparisons, preserve the same seed and layout resamples across cases; resample within-case environment episodes. Use 200,000 draws and two-sided Bonferroni intervals over 248 comparisons (50 new plus 198 earlier). A named superiority claim requires lower bound strictly above zero. The earlier 198 comparisons are conservatively accounted for, not reclassified as independent new replications. Bootstraps are approximate, not exact finite-sample guarantees. Eight seeds and sixteen structured graphs still limit extrapolation.

Follower delivery, utility, training time, packet admission, conditional common-survivor travel time/cost, topology-size breakdowns, fixed-actor swaps and prediction error are descriptive. Survivor-only costs have selection limitations. Receiver admission is not transmitted-bandwidth savings. No noninferiority, convergence, universal superiority or real-world validation claim follows from nonsignificant differences. An inconclusive primary result means the added learned component remains unestablished, even if some secondary conditions improve.

## Reproduction

From the repository root, after the existing pinned environment setup:

```bash
cd simulator
MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache ../.venv/bin/python run_matched_gate_study.py --output out/matched-gate-study --workers 4
cd ..
MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache .venv/bin/python simulator/report_matched_gate_study.py --run simulator/out/matched-gate-study --output revision/matched-gate-results
```

The output directory must be new. Existing studies, checkpoints, claims and adverse results remain unchanged. See the generated source hash, design, settings lock, training manifest, episode/convoy records, and verification report for the executed run.
