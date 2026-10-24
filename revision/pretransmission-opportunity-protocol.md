# Pre-transmission delivery opportunity: development protocol

This implements the first step of the mathematical redesign: a radio decision
boundary and actual paired fleet continuations, with routing fixed. No new
controller is fitted and no superiority confirmation is claimed at this stage.
All previous source, checkpoints, results and archives remain unchanged.

The original inline radio start becomes a reversible reservation at zero
elapsed airtime. It is exposed only after the enclosing physical event has
completed, so no routing/sensing function is suspended halfway. Sending the
reserved packet preserves the original heap entries, tie order and statistics.
Alternatives undo only its unspent reservation before modifying service:

- Drop removes that one offer; a later duplicate observation may still be sent.
- Defer makes that packet ineligible for one service interval. Other ready or
  newly arriving packets may transmit immediately. This does not idle the whole
  channel unconditionally and is not receiver-side quarantine.
- Swap serves the next reference-priority ready packet, retaining/coalescing the
  original packet as appropriate. It requires an available alternative.

All continuations use the same frozen actor, VALUE priority with zero sender
threshold, ALL receiver, complete closure schedule and keyed sensor/loss fields.
Semantic loss IDs can recur across duplicate offers; offer numbers identify the
specific reservation. The send branch must reproduce the uninterrupted outcome
exactly. Twenty-four predetermined pilot cases also compare the full reference
outcome against the untouched original event engine.

One preselected reservation per episode is captured at index 1/3/8/16, rotated
deterministically by actor, graph, case, capacity and episode. Its selection
does not inspect a future outcome. Each feasible action is continued through
fleet completion/horizon, retaining all eight convoy records and elapsed-time
components. Defer is omitted when service time is zero. Swap is omitted when no
ready alternative exists. Both helpful and harmful outcomes are retained.

The design uses all eight original routing actors, including the explicitly
selected initial policy, and three new weighted graph instances at 19/51/131
nodes. Adjacency families are fixed; one instance per size does not support
topology-generalization inference. All twelve prior conditions are retained.
Each non-unlimited condition is run at packet_time 0.25 and 1; the unlimited case
uses 0. Each cell has two exogenous schedules. There are 1,104 factual episodes
plus 1,104 full-episode batched-priority reference episodes, and a variable number
of isolated alternative continuations. New development namespace 860000000+
is independent of the earlier study. This is a mechanism pilot, not a sufficient
sample-size justification for a final performance claim.

The stronger batched reference reselects the highest VALUE-priority ready packet
after every atomic event, without learning, discarding or intentional deferral.
It tests whether simple batching already accounts for opportunity exposed at
the new boundary. Later learned-controller comparisons must include this arm,
other strong priorities and a matched learned-priority/no-filter ablation.

The decision features contain offered payload metadata, queue summaries, public
route demand/detour, channel service time and elapsed phase. This is a shared-MAC
queue model, consistent with the existing global queue. It is not claimed fully
decentralized. Remote live unit positions, private inboxes, live flow and hidden
closure/future events do not enter the features. No new telemetry is added.

Report all-action gain/loss rates and magnitudes, captured opportunities, all
physical conditions, capacity/size breakdowns and batching effects. The best
sampled action chosen with hindsight is a diagnostic only: not a deployed
algorithm, an upper bound over unsampled actions, or a learned-policy result.
An unlimited channel does not make packet removal semantically irrelevant:
dropping still changes information, so its effects need not be zero.

Only after this pilot should training proceed, conditional on sufficient useful
signal. The next stage needs separate value/risk estimation, more independent
consequential examples, complete admission/history probes and fresh validation.
The deadline-return critic and a trained pre-transmission controller are not
implemented by this mechanism experiment. Any confirmation needs a new frozen
design and untouched test schedules.
