# Reviewer coverage: reconstructed simulator

Source: `simulator/`. Submitted PDF and reviewer letter were read as reference material. The submitted manuscript is not yet rewritten, and no final scientific performance claims are made here.

The current original-topology revision is documented in [code changes and protocol](reviewer-code-changes.md) and [executed results](reviewer-revision-results/README.md). It adds declared sensing roles and an active hazard pathway, 43 tests, fresh five-seed models, matched frozen-weight communication contrasts and raw-data plots. The original submission code is preserved and its evidence provenance is audited separately.

The historical complete executable workflow, 300-episode training protocol, raw artifacts,
offline report and portable delivery are described in
[complete model](complete-model.md) and [protocol](complete-protocol.md).
The [executed report](complete-visualisations/README.md) retains positive,
negative and inconclusive outcomes. Implementation completeness is distinct
from resolving every scientific or manuscript revision concern.

| Review concern | Implemented change | Evidence / remaining work |
|---|---|---|
| R1.1: hub-only state | Local belief-conditioned sparse GNN observations include report age/confidence, knowledge masks and elapsed time; remote live state is hidden from the actor. | Actor isolation and feature tests. Timestamped summaries are not claimed to be sufficient Markov states or a full POMDP solution. |
| R1.2: tiny tabular network | Deep DQN/PPO/IPPO/MAPPO; sparse graph inference and held-out graph-size evaluation at 39/51/203/483 nodes. | Multi-size inference smoke validation; larger-network convergence, realistic geographic/operational data and runtime comparisons still require scientific experiments. |
| R1.3: cost inconsistency | Nominal path sums are separate from reward and realized time. Per-target Dijkstra lower bounds, explicit survivor denominators and common-delivery pairing. | Direct nominal-optimality/path-sum tests and runtime metric assertions. The submitted numerical table must be replaced, not carried forward. |
| R1.4: FIR attribution | Fork the complete pre-decision simulator, suppress one packet, continue a frozen policy and compare receiver outcomes; verify all random attacks in shared time. | Positive saving-message and rejected-message zero-effect tests; full-message synthetic replay. Route-proxy and delivery FIR are separately labeled. Denominator is decision-processed messages; do not silently equate it to all attempted transmissions. |
| R1.5: static freshness | Configurable corridor-traversal freshness using visible congestion, capped by outer TTL; retained reports rechecked at each decision. | Congestion sensitivity, hidden remote-flow and retained-expiry tests. Static and historical ETA rules retained for comparison; sweeps supported. Remote congestion estimates use nominal cost until better telemetry is supplied. |
| R1.6: unclear baselines | Explicit observation/action contract; reachable next-hop mask; masked Double-DQN bootstrap; elapsed-time discounts and terminal-masked GAE; separate PPO/IPPO/MAPPO implementations. | Real optimizer tests for all four algorithms and checkpoint train/load/evaluation validation. Hyperparameter/convergence and matched-budget scientific assessment remain outstanding. |
| R1.7: queues and AoI | FIFO service capacity; age uses actual elapsed time including waiting and service; departure-time report rejection. | Explicit congested-queue expiry test, capacity invariant and successful time decomposition. Horizon accounting accrues only actual elapsed travel/service/wait. |
| R1.8: static adversary | Traffic-reactive interdictions with observation delay, decayed traffic, exploration and block budget; distinct targeted/exogenous spoof modes. | Delayed-observation test and reactive/targeted smoke runs. Operational adversary validation is outside this synthetic benchmark. |
| R1.9: fractional counts | Integer blocked-entry counts and separate unexpected entries; explicit episode totals and per-convoy averages, delivery/destruction/censoring. | Integer-count tests, known-vs-unexpected distinction and raw convoy CSVs. Time units remain model units, not assumed minutes. |
| R1.10: filtering/penalty confound | Independent gate flags, static/travel freshness, eta and response-strength factors; same own/peer response weight within heuristic variants. | Factorial ablation runner and zero-strength outcome check. Deep policies use learned belief features rather than the original fixed Q-score penalty; heuristic sweeps must not be generalized to deep agents. |
| R2: gate operation / comparator descriptions | Complete pseudocode-level implementation, feature list, reward, hyperparameters, gate ordering and baseline distinctions in `simulator/METHODS.md`. | Rewrite manuscript Sections III–V to match these semantics. |
| R2: motivation / military specificity | Explicit synthetic threat, delay/loss, spoofing, hub-resource and partial-observation assumptions. | Rewrite motivation without presuming ungated harm; distinguish model assumptions from validated military use. |
| R2: abstract / Figure 1 labels | No unsupported editorial claims inserted. | Update abstract, architecture labels and contribution claims after audited experiments and manuscript revision. |

## Scientific work that remains

1. Tune only on separate validation graphs; assess training convergence and sensitivity with adequate seeds and matched environment interaction budgets. The 300-episode, three-seed run extends the earlier smoke runs but does not presume convergence or sufficient retraining replication.
2. Run the full held-out comparison with documented uncertainty, fair survivor conditioning, larger graphs, congestion/delay/loss/confidence sweeps and clean/adversarial training comparisons.
3. Evaluate single-message FIR with sufficient independent episodes. Controlled replay excludes endogenous reactive/targeted attack schedules; analyze those scenarios as total policy effects with explicit causal assumptions.
4. Original source and its 19-node/64-edge topology have now been supplied, preserved and adapted. Exact submitted numerical reproduction remains unverified: its presentation pipeline constructs curves and fixes headline values, while its M4 runner has no connected hazard source. Current replacement results come only from executed simulations.
5. Update manuscript equations, units, tables, figures and claims and prepare point-by-point responses. Highlight the changes and cite original paper IoT-66126-2026 when resubmitting as the editor requests.

The original manuscript asserts strong gated superiority. The archived README reports mixed gate results. Neither is taken as evidence of superiority for the reconstructed version; new results must decide the claim.
