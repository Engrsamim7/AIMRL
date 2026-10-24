# Pre-transmission prototype: implemented and executed mechanism pilot

The first implementation stage is complete: a radio intervention boundary,
paired complete-fleet continuations and a frozen-router development pilot.
There is measured opportunity, but **no trained pre-transmission controller or
new superiority result**. The deadline-return critic is also still proposed.

## Implemented behavior

The radio now exposes a reversible reservation at zero elapsed airtime after
the enclosing physical event completes. Sending it preserves the original
event sequence exactly. Alternatives drop that unsent offer, defer only that
packet by one service time, or serve another ready packet first. Deferral leaves
the channel available to other ready/new packets. It is not a receiver quarantine.
Future transmissions and convoy behavior remain endogenous consequences.

The original routing actors, closure/sensing physics and old study sources are
unchanged. All eight selected actor checkpoints are reused; one is the disclosed
initial-policy selection. No routing updates or controller fitting occur here.
Runtime features use existing payload metadata, shared-MAC queue summaries,
public route demand/detour and channel/time information. They do not use live
remote positions, private inboxes, live flow, future events or closure truth.

The shared-MAC queue is an explicit abstraction inherited from the previous
engine. This does not demonstrate a fully decentralized communication protocol.
No new free telemetry is added. More detailed decentralized coordination would
need its own traffic, delay and overhead model.

## Executed pilot and accounting

The run covers all twelve prior physical conditions, at service-time settings
0.25 and 1 for non-unlimited cases and 0 for the unlimited case. Three new weighted
graph instances have 19/51/131 nodes. Two schedules per cell and eight frozen
actors produce 1,104 factual reference episodes plus 1,104 full batched-priority
reference episodes. Capturing one predetermined reservation per episode yields
1,023 captured episodes and 3,017 feasible isolated alternative continuations.
There are 41,800 saved convoy outcome records.

The sample index is chosen from 1/3/8/16 before seeing an outcome, rotated across
actor/graph/case/capacity/episode. Since the index also varies with actor seed,
per-seed opportunity variation is not a pure measure of routing-policy variation.
Missing/ineligible actions retain the factual outcome in all-episode averages.
Conditional-on-availability averages are reported separately.

Every send continuation exactly reproduces its uninterrupted factual outcome.
Twenty-four predetermined original-engine comparisons also match exactly.
The full suite passes **170 tests**, including exact no-op packet/event behavior,
real timely-warning delivery benefit, unsent-offer removal, packet-only deferral,
future urgent offers using the free channel, feature isolation, branch-copy
independence, batched priority and noisy zero-inspection termination.

The reporter checks all elapsed-time decompositions, legal continuous paths,
nominal path sums, convoy/episode aggregates, integer blocked-entry totals,
paired outcomes, common schedule hashes and completed/partial radio-airtime
accounting. Semantic loss IDs may recur for duplicate observations; offer
numbers identify specific reservations, preventing a duplicate from being
misclassified as a ghost transmission.

## Results and their interpretation

| Arm / diagnostic | On-time delivery |
|---|---:|
| Original VALUE priority, ALL receiver | 69.79167% |
| Full-episode batched VALUE priority, ALL receiver | 69.63315% |
| Best sampled action selected with hindsight | 70.42572% |

The full batched arm loses 0.15851 percentage points, corresponding to 14 fewer
on-time arrivals among 8,832 convoy outcomes. It uses only public priority rules,
not learned filtering. This guards against attributing a possible future gain
to learning when simple same-event queue reselection could explain it. Batching
does not improve the pooled observed result in this pilot; no inferiority test
or generalization claim is made.

The sampled hindsight diagnostic gains 0.63406 points, corresponding to 56 recovered
on-time arrivals, in 44 episodes with a helpful sampled alternative. It chooses
after observing outcomes. **It cannot be presented as a deployable controller,
an achievable learned result, or an upper bound over unsampled decision points.**
It is the exact best gain for the actions actually measured at these sampled
points. That restricted action set falls short of the one-point target even
with hindsight on this cohort; this is not a global impossibility result.

| Sampled action | Interventions | Helpful | Harmful | No delivery effect | Mean change over all 1,104 episodes |
|---|---:|---:|---:|---:|---:|
| Defer selected packet | 975 | 18 | 17 | 940 | -0.01132 pp |
| Drop selected offer | 1,023 | 42 | 47 | 934 | -0.16984 pp |
| Serve next ready packet | 1,019 | 18 | 17 | 984 | -0.01132 pp |

These are single-action continuations at the preselected sample point, not
full policies applying the action at every reservation. They show why blindly
changing radio service is inadequate. The availability sets differ: deferral
is omitted for a zero-time channel and swapping requires an alternative.

All size, condition and service-rate cells are retained. The pooled statistics
weight the declared size/case/capacity cells equally; the unlimited case has one
capacity cell and other cases have two. One weighted instance per size cannot
support topology-generalization inference. No confirmatory confidence interval
or learned-policy superiority test is reported.

## What should follow

The prototype establishes that pre-transmission actions can affect deadline
delivery through actual channel timing and information changes. It does not
show that the present queue features can predict the beneficial actions, or
that the limited sampled opportunities are sufficient for the intended target.

The next development work should expand decision-point coverage, estimate
message usefulness before a receiver's routing commitment/deadline, and retain
full evidence/history effects. Any receiver progress estimate must come from
public manifests or actual communicated information; it cannot read simulator
truth. If telemetry is added, charge its airtime and expose it equally to strong
baselines. Directly fit fleet delivery value separately from calibrated harm
prediction, with more independent consequential continuations and declared
sampling weights. Do not simply deploy the hindsight choices or sum isolated
effects along different trajectories.

A controller with several deviations needs consistent remaining-resource and
continuation-policy labels and state-distribution coverage. Joint routing
training and a deadline-return critic should then be assessed under matched
budgets. Keep batched/age/warning/learned priority without filtering as controls.
Freeze the eventual design before a fresh test. The manuscript superiority
claim remains unsupported by this development pilot.

## Code and delivery

- [Three-figure PDF](../deliverables/AIMRL-pretransmission-opportunity-figures.pdf).
- [Complete prototype, actor checkpoints, raw results and figures ZIP](../deliverables/AIMRL-pretransmission-opportunity.zip).
- [Tables and reproduction commands](pretransmission-opportunity-results/README.md), [offline figures](pretransmission-opportunity-results/index.html).
- [Prospective development protocol](pretransmission-opportunity-protocol.md), [mathematical rationale](delivery-mathematical-analysis.md).

Historical simulator/results archives are preserved separately. Artifact hashes,
extracted-package tests and report regeneration are recorded in the delivery
validation JSON; publication status must be read from that record.
