# Timed-network development protocol

Specified before the development campaign on 19 October 2026. This is a new network revision following the inactive-gate diagnosis. It is a development/feasibility study, not an independent confirmation of the old manuscript claim. Original files and previous results remain unchanged.

## Physical model

Use one event-driven engine for the original 19-node topology (fresh cost attributes) and independently generated 51/131-node layered networks. Eight convoys have assigned targets, a leading scout, service-only FIFO hub capacity, flow-dependent edge travel times and deadlines fixed at 1.75 times their public free-flow path cost plus service. Time is in abstract model units, not minutes. The original topology is a continuity case; the larger generators are synthetic scale cases, not operational maps.

Closure and static route risk are separate. Exactly round(closure_fraction * directed edge count) distinct edges receive one exogenous closure each; no policy changes that schedule or budget. Half start at zero and half within half a median free-flow mission duration; the late-onset control begins after 1.5 such durations. Recovery follows declared durations. There is no destruction probability. A closed edge cannot be entered; a failed attempt consumes inspection time, records an actual observation and then reroutes or holds. Open entries already in transit complete even if a closure starts later. Waiting and all partial segments at the horizon enter elapsed accounting.

Sensors are position-based: the scout observes radius two, others radius one with seed-fixed coverage masks. Reports record the observation time, binary state and claimed confidence. Sender/receiver identity and packet identifiers are not learned predictor features. Noise and loss use independently keyed deterministic streams, so actor randomness cannot alter closure schedules. Remote active closures and remote live convoy states are absent from actor inputs. Truth is used offline for calibration labels and evaluator diagnostics only.

## Shared interpretation and real communication capacity

Fit one empirical report-validity model from 76,800 synthetic training sensor/query labels on eight graph instances at sizes 19/51, eight fitting cases and three schedules per case. Tables condition on normalized report age, public mission phase, confidence bin and observed state, with declared count backoff and smoothing. The miscalibrated-sensor case is excluded from fitting. Evaluate on-policy Brier scores rather than assuming field calibration. The model is shared by all relevant planning methods. It does not know the test case name, closure schedule, true current state or future recovery.

A common receding-horizon planner uses public topology/cost, locally visible flow, available timestamped observations and expected failed-inspection delay. Public free-flow distances approximate time until a remote edge is traversed. It is an approximate expected-time planner, not a MARL learner, optimal on-time controller or proof of optimality. A belief-conditioned learned actor remains later work.

A single finite broadcast channel serializes actual 64-byte packets. Transmission takes packet_time * median nominal edge cost; propagation takes delay * median edge cost. Queue waiting contributes to report age. Packets are generated from actual source observations and periodic re-advertisement; initial clear-state advertisements are explicit traffic. Each transmission broadcasts one packet to the fleet, with per-recipient keyed losses. Bytes measure actual completed transmissions before fleet completion/horizon, not receiver admission counts.

Compare seven methods:

- NONE: local sensing, zero radio transmissions, age-aware own interpretation.
- RAW_ALL: FIFO transmission, age-ignorant report interpretation.
- FRC: FIFO transmission, fixed receiver freshness 3.2/confidence 0.6; does not save transmitted bandwidth.
- AGE_ALL: FIFO transmission with the fitted age-aware interpreter.
- LATEST: AGE_ALL plus coalescing queued updates from the same source/edge.
- WARN_PRIORITY: LATEST plus warning-first/static public-route-demand priority.
- VALUE: sender admission and priority using calibrated belief changes times public detour/demand relevance. Both warnings and clearances can be sent. No live receiver state is used. This is a new heuristic transmission-value rule, not the original FRC, a trained causal value predictor, or a theorem of improvement.

## Fixed development grid and selection

Nine cases: clean-covered/perfect-sensor, clean-partial, persistent, transient, rapid recovery, late onset, late reports, 20% loss and confidence miscalibration. Channel packet times are 0, 0.25 and 1 median-edge time units. The zero-duration channel is an unlimited-rate control. Full case objects are saved before execution in design.json.

Use separate namespaces: training 710000000+, validation 711000000+, development evaluation 712000000+. Validation uses four graphs at sizes 19/51, every case/channel setting, two schedules and VALUE thresholds 0/0.05/0.2. Select pooled on-time delivery, then fewer bytes, then lower threshold; lock calibration and settings before development evaluation. Zero is a legitimate candidate, so selection may favor prioritization without admission filtering.

Development evaluation uses six new graphs: two each at 19, 51 and 131 nodes; nine cases; three channel rates; six exogenous schedules; seven methods: 6,804 method episodes and 54,432 convoy records. The larger size is not included in calibration fitting. Graph/episode pairs share closure schedule, sensor mask, assigned targets and departures. Different closed-loop decisions may change encountered observations and transmitted traffic; this is a policy comparison, not single-packet causal FIR.

## Evidence and limits

Primary development outcome is on-time delivery; whole-horizon delivery, time, nominal cost, integer encounters, actual transmitted bytes, radio queue age, peer-induced next-hop changes and calibration Brier remain separate. Keep every case, including clean and late controls. Report all methods against both AGE_ALL and WARN_PRIORITY. Do not describe improvement over RAW_ALL alone as strong-baseline superiority.

Intervals, if reported, are descriptive paired graph/episode resampling, not a fresh corrected significance test. There are only two graphs per size and one fitted interpreter; no independent routing-training replication, convergence claim or adequate power is implied. Future confirmation needs an untouched test set, independent learned-model seeds and a fixed scientific effect-size criterion.

Mechanism tests verify an actual scout warning changes a follower route and avoids a blocked attempt; no closed edge is traversed; time/path sums balance; closure schedules match across methods; hidden remote truth does not change an actor with fixed visible inputs; sender decisions ignore live receiver positions; real packet serialization adds age; queue waiting expires retained reports; old persistent and obsolete reports are distinguished; coalescing and clearance transmission work; and zero inspection delay still advances time.

The implementation, protocol and settings are fingerprinted. Do not alter physical settings, method rules or the declared grid after inspecting development results while retaining them as an independent confirmation. This phase resolves key model-validity gaps; it does not by itself satisfy every reviewer concern or make the original manuscript ready.
