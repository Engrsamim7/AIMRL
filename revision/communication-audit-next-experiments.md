# Proposed experiments after the communication opportunity audit

This is a prospective design, **not executed results**. The completed audit diagnoses existing test schedules. It is not additional training data or a fresh test of superiority. The original source and experiment settings remain unchanged.

## Establish a useful observation response first

The model-based gate currently changes a reference planner's heuristic block penalty. The declared block prior is 0.05, initial sender agreement is 2/3, and the selected risk-aversion coefficient is zero. Even an instantaneous confidence-1 warning from a new sender produces a probability near 0.20 before age/distance decay. Such a warning can leave the route unchanged when an alternative costs several units more. This is not an empirical calibration of report accuracy or expected delivery loss.

Build a shared report interpreter for both communication-ALL and gated policies before testing a gate-specific improvement. Estimate how report age, observation coverage, clearance evidence, disagreement and sender history predict a block at expected traversal time. Train on newly generated episodes, including honest hazard transitions and misleading packets. Simulator truth can be used for offline training labels and evaluator diagnostics; deployed actors and gates must use public packets and declared observations only. Measure calibration on validation data and account for biased confirmation opportunities. Do not equate agreement with honesty, and do not treat reported confidence as a calibrated likelihood.

Choose the survival-versus-detour objective explicitly and report its units. A delivery failure penalty should not be silently replaced by an arbitrary edge-cost increment. Retain measured detour cost, realized time, destruction, censoring, and actual delivery separately. A conservative warning response is also a baseline, with its costs measured.

## Define when communication can matter

Use the original topology plus separate randomly generated topologies. Declare topology, traffic and sensing assumptions before testing. Sweep the following ranges; these are study dimensions, not a plan to select a favorable outcome:

| Dimension | Proposed levels | Why it matters |
|---|---|---|
| Scout departure lead | 0, 3, 6 time units | A scout must observe before followers commit |
| Follower coverage gaps | 0%, 20%, 50% of eligible edges | Communication can be redundant or fill unknown regions |
| Message delay | 1, 4, 8 time units | Delays can consume the warning's actionable lifetime |
| Attack reveal delay | 0, 5 time units | Shared observations can still be late relative to real attacks |
| Block duration | 5–10, 15–30 time units | Warning validity and clearance tradeoffs depend on persistence |
| Loss | 0, 0.2 | Distinguish sending, delivery and use |
| Misleading reports | none, false-block/false-clear mix, single and multiple impersonation | Filtering must address both detours and unsafe clearance |

A scout lead should be applied to actual departure schedules, not privileged warnings. Use the same departures, assigned targets and sensors for all compared policies. Fix coverage masks from topology and a declared sensor seed independently of attacks. For leading scouts, offset follower departures while preserving scout jitter; do not simulate a negative mission clock or add unmodeled observer information to ordinary network experiments.

Define a staged grid before running it to keep computation feasible: first timing/coverage/persistence with honest reports; then delay/loss/misleading-report stress in those **predeclared** cells. Include zero-lead, full-coverage, late-message and no-attack controls. Publish the whole declared grid. Do not remove cells because they do not favor the gate.

## Learn the value of a message for the actual actor

After a shared report interpreter demonstrably supports appropriate routing responses, train an actor-specific value predictor. Generate complete-episode, single-message or inbox-batch interventions on training schedules with frozen actors. Labels should include delivery benefit/harm, extra travel time and cost; account for interacting and redundant messages. Use actor state, public route alternatives, public age/confidence and report features as inputs. Do not expose current active attacks, genuine/spoof labels, critic-only global state, future outcomes or encoded message-ID origins as inputs. Packet identifiers should be opaque and used for bookkeeping, not predictive features.

The existing reference-planner regret proxy is a comparator, not the target actor's learned value. If observation features change, train compatible actors on the new contract instead of mapping untrained probabilities into existing binary features. Evaluate multiple independent training seeds and graph seeds. Keep unauthenticated sender identities explicit: two claimed sources are not proof of independent observers.

## Lock a new study before testing

Use new nonoverlapping random-seed namespaces for training, validation and testing, for example 40,000,000+, 41,000,000+, and 42,000,000+. Record complete schedule identifiers and separately held-out synthetic graph seeds. Avoid reusing any adaptive-v1/v2 or audit episodes for fresh-test claims. Tune the interpreter, objective, gate thresholds and architecture on training/validation only. Archive a signed or hashed design, code fingerprint and selected settings before unlocking test evaluation.

Compare: communication off; old binary ALL/FRC; the new shared interpreter with ALL; the same interpreter with FRC; the model-based gate; and the learned actor-specific value gate. Match actor architecture, training budget, observations, traffic and objective. If gating changes transmitted rather than merely admitted packets, add a separate sending policy and model its communication budget; the current receiver filter does not save transmitted bandwidth.

Primary endpoints should be actual delivery against the matched new ALL and FRC baselines over the declared range, with paired topology/episode inference and a predeclared correction. Report absolute differences and intervals, plus common-survivor travel/cost contrasts, blocked entries, warning opportunity rates and actual decision changes. Derive sample sizes from new training/validation variance and a scientifically meaningful effect size. No general-superiority claim, percentage target or significance promise is justified in advance.

## What would justify proceeding with a gate claim

First show that accurate novel timely warnings can influence consequential decisions in realistic declared conditions. Then establish that value filtering improves outcomes or a explicitly specified cost/budget objective over the matched shared interpreter. If the shared interpreter improves routing but filtering adds no benefit, report an estimator contribution rather than a gate contribution. If useful warning opportunities remain rare, the broad network evaluation cannot support a large delivery superiority claim; report that limitation and the conditions under which the mechanism operates.
