# Simulator and learning contract

## Dynamics and information

The event-driven global simulator state contains convoy locations/status, traversed paths, hub queues/services, edge flow, active interdictions, delayed message queues and adversary traffic history. Given that state and the stochastic event mechanisms, it defines a controlled partially observable semi-Markov process. Decision epochs occur at dispatch and at completion of non-depot hub service; they are irregularly spaced. FIFO queues have `hub_cap` parallel services, each of duration `hub_service`. Waiting and service are distinct. Target arrival needs to match the convoy's assigned target.

Entering edge e at time t takes `T_e(t)=c_e*(1+congestion_factor*flow_e(t)/q_e)`, with flow counted before the new convoy enters. A blocked entry can destroy a convoy with `p_kill`; otherwise traversal takes `blocked_slow*T_e(t)`. Each blocked entry is counted, independently of whether the convoy knew it was blocked. An additional unexpected-entry count requires that the edge was not in the departure-time blocked belief. The latter corresponds to the belief-open condition in the submitted Equation 13. Destruction draws are keyed by episode, convoy and hop without a finite-hop RNG cap.

Local sensing covers outgoing edges over a directed `obs_radius` traversal. Unrevealed hazards remain unobserved until `tau_reveal`; sensing updates timestamped open/blocked reports, not a Bayesian posterior. Queue length/service occupancy is visible only at local edge-source hubs. Edge flow is visible only on sensed edges. Remote live flow/queues and true interdictions are unavailable to actors. The static graph, nominal costs, capacity, prior threat and assigned target are public. A report's confidence is a synthetic score, not an authentication guarantee.

The actor uses a timestamped information summary and public clock rather than a hub-only Q-table. This is an approximation for partial observability; there is no assertion that this summary is a sufficient Markov state or that training solves the full Dec-POMDP optimally.

Node actor features are: current-node flag, target flag, normalized nominal distance to target, visible service occupancy, visible queue length, believed-blocked outgoing-edge fraction, mean static outgoing threat, visibility flag, normalized clock, and known outgoing-report fraction. Candidate-edge features are: nominal cost, prior threat, visible flow/capacity, blocked belief, normalized age, nominal distance from head to target, confidence, known-report flag, and flow visibility. Unknown reports and known-open reports are distinguishable. Inaccessible dynamics use zero plus visibility indicators; no global live telemetry is substituted.

## Communication and freshness

A packet has a stable identifier, sender, receiver (delivery envelope), edge, blocked flag, observation timestamp, confidence and evaluation-only genuine/spoof label. The label is never used by the gate or actor. Packet loss/confidence draws use stable packet identity, not a global send counter. Sender-policy changes can legitimately change future honest transmissions.

At each decision, expired retained reports are removed, local observations are refreshed, and inbox packets are considered by observation timestamp. A packet must not come from the future, exceed `tau_stale`, or be older than the latest own/peer report. If enabled, the gate additionally requires:

- Freshness: age <= `min(tau_stale, eta*T_hat_e(t))`. Locally visible flow informs `T_hat`; remote flow uses nominal cost. Static `eta*tau_stale` and the historical estimated-time-to-source-plus-delay rule are explicit alternatives.
- Relevance: a blocked report references an edge on the receiver's own-information heuristic plan; clear reports are allowed to revoke an older report. This is an explicit route-based heuristic gate, including when attached to a deep actor; it is not claimed to recover the deep policy's future route.
- Confidence: score >= `kappa_min`.

Accepted peer reports are rechecked for freshness on every subsequent departure. Message age increases with elapsed simulation time, including time in queue and service. Reasons for every processed acceptance/rejection are recorded. Retained reports' relevance/confidence are not reoptimized at every epoch; relevance is an admission rule. Route dependence can reject information that would have helped on an alternative future path, so gate performance must be measured rather than assumed.

Heuristics add `response_strength` to each believed-blocked edge's planning weight. Own and peer information use the same strength, independent of filtering. The `avoid` mode is a separate comparator with explicit fallback when all routes appear blocked. Deep agents use belief features; they do not apply this cost penalty to action scores. Therefore heuristic strength sweeps cannot by themselves establish the same effect in learned policies.

The oracle sees all currently blocked edges, including unrevealed blocks, but still uses a routing heuristic. It is a diagnostic reference, not an optimal upper bound for a coupled stochastic routing problem.

## Threats and counterfactuals

Random attacks sample edges proportional to static prior threat, respect a simultaneous-block budget and have random durations. Reactive attacks select the largest exponentially decayed observed entry count, with configurable exploration and `react_delay` before entries become visible. They do not inspect future routes. This is a synthetic adaptive adversary, not a model validated against operational data.

Exogenous spoofing chooses receiver slots and edges independently of routing/survival. Targeted spoofing uses the victim's current planned route; it is policy-dependent. These modes are explicitly distinct.

Single-message replay checkpoints the complete simulator immediately before processing the receiver's next inbox/decision. A shadow continues with just one delivered packet suppressed, the same frozen evaluation policy, queued events and RNG state. Other pre-intervention state is unchanged. Future congestion, routes, honest messages and outcomes may differ as causal consequences. Every random attack in the branches' shared time interval is checked for equality. Controlled FIR rejects reactive attacks/targeted spoofing because their schedules are endogenous to routing. Policy-level comparison scripts are historical and are not used as event-level attribution.

For factual-minus-suppressed receiver outcomes, the original route-based failure condition is `delta_surprise_blocked_encounters >= 0 and delta_route_surv <= 0`. A separate delivery-based condition is `delta_blocked_encounters >= 0 and delta_delivery <= 0`. Denominators count the processed messages actually replayed, including rejected packets (whose realized effect may be zero). Zero-message FIR is undefined. A limited prefix is labeled as a diagnostic subset, not an unbiased estimate. Interventions can also affect other convoys; episode delivery effects are retained separately. Effects are not additive across messages and do not equal a policy-level communication effect.

## Learning and evaluation

All methods use reachable outgoing edges as the hard candidate mask. Believed hazardous edges are not silently deleted from the deep action space. The same mask applies to selection, distributions and value bootstrapping.

DQN uses a two-layer sparse GNN and Double-DQN updates. PPO uses a shared local actor/critic across convoys with pooled rollouts. IPPO independently initializes and optimizes one local actor/critic per convoy slot. MAPPO uses a shared actor and a critic additionally given four privileged aggregates: active-block budget fraction, active-convoy fraction, mean edge load and global service utilization. These aggregates never enter actor logits. All are explicitly specified baseline variants, not claims of equivalence to every published implementation.

For elapsed decision duration dt and incurred nominal cost dc:

`reward = -time_weight*dt - nominal_weight*dc + delivery_reward*delivered - death_penalty*destroyed - timeout_penalty*horizon_failure`.

The discount is `gamma**(dt/discount_time_unit)`. DQN TD and PPO-family GAE use it; GAE masks terminal continuation. Finite-horizon failures close pending transitions. The default reward uses time weight 1, nominal weight 0 and terminal rewards/penalties of 40. Reward weights are saved with checkpoints and are never inserted into reported nominal cost. This revises the submitted reward definition and requires manuscript updates.

The default architecture has hidden width 48, two graph layers, learning rate .001, gamma .99 per unit of simulation time, GAE lambda .95, PPO clip .2, four epochs, minibatches of 64, value coefficient .5, entropy coefficient .01 and gradient norm clipping at 5. DQN uses a 20,000-transition buffer, warmup 256, batch 32, update interval 8 and target sync interval 100 optimizer updates. Smoke mode explicitly lowers warmup/batch and PPO epochs; its results are not final comparisons.

Training/evaluation environments and episode allocations are matched across algorithms, but actual decisions and updates can differ; the runner records both. Evaluation is deterministic greedy inference. Train graph seeds are 1–40; held-out evaluation seeds start at 300. Larger-graph inference does not demonstrate larger-graph training convergence. Full scientific comparison additionally needs validation-only tuning, convergence assessment, more training seeds, confidence-score calibration assumptions and matched clean/adversarial training budgets.

## Metrics and units

Simulation time is in arbitrary model units; measured execution time is in wall-clock seconds. No conversion to operational minutes is assumed. Nominal cost is the sum of traversed `c_e`, including partial routes for non-deliveries. Realized time is departure-to-target arrival, including queue and service; it is undefined for non-deliveries. Elapsed time and accrued travel/service/wait at the horizon are separately available for censored convoys. Delivery rate, route prior-survival proxy and actual destruction are distinct concepts.

All-convoy and delivered-only nominal averages have explicit names and denominators. Every delivered route is checked against the shortest nominal cost for its identical depot/target. Different survivor subsets can have different average costs without violating Dijkstra optimality; paired common-delivery comparison is provided for that reason. Counts are integers per convoy; episode totals and per-convoy means are separate. Delivered-subset makespan is not mission completion when any convoy fails. Raw records identify graph, episode, method and training seed.
