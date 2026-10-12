# Protocol for testing the manuscript's gate claim

Status: specification based on the supplied manuscript and current source; the new experiments below have not been executed. Existing complete-model-v1 results remain unchanged.

## Question

Does freshness/relevance/confidence filtering improve outcomes over accepting peer reports when the routing learner and response rule are held constant? A favorable answer in a defined regime supports a conditional claim, not universal superiority or necessary-and-sufficient language.

## Mechanism differences that must be explicit

| Component | Submitted manuscript | Current reconstruction |
|---|---|---|
| Learned routing | Per-convoy hub-indexed tabular Q | Belief-feature GNN DQN/PPO/IPPO/MAPPO; heuristic communication comparator is separate |
| Freshness | Age <= 0.40 * 8 = 3.2 time units | Default corridor-traversal-based limit; static rule available |
| Relevance | Current threat-divergent fork, available next hop, matching reported corridor | Reported blocked edge on own-information heuristic route |
| Hazard scoring | At forks: Q minus local penalty 8 or accepted-peer penalty 12; outside forks Q alone | Heuristics use matched additive response strength; deep policies use belief features |
| Main setup | 19 nodes, approximately 60 edges, three simultaneous convoys, hub capacity two | Seeded synthetic graphs, twelve staggered convoys, hub capacity one in delivered suite |
| Primary outcome | Reported survivability; route-threat proxy and actual success need separate definitions | Actual delivery/destruction/censoring separated from route-prior survival proxy |

The current suite is not an exact reproduction of submitted numbers. Exact original topology, edge attributes, threat generation and complete original experiment configuration must be recoverable before labeling any run an exact reproduction. A synthetic manuscript-mechanism variant must be labeled accordingly. The hub-only state may be retained as a historical mechanism comparator, without claiming it is Markov under partial observability.

## Experiment A: isolate filtering before retraining

Use one frozen routing learner per seed for all communication modes. Define a base local-information learner trained without peer inputs, then freeze its Q values for manuscript-style score interventions. Keep local observations, action masks, targets, environment distributions, reward, exploration/evaluation rules and handling of reports identical across variants. Use independent training and validation/test schedules.

Compare NC (own reports), ALL (peer reports subject to the common outer validity and timestamp rules), and FRC (peer reports subject also to all three gate conditions). Explicitly document validity filters that remain active in ALL. Evaluate both matched local/peer response weights (8/8 and 12/12) and the manuscript's asymmetric 8/12 rule. Add zero-response and all eight F/R/C masks as controls. Recheck buffered gate conditions at decision time. Specify deterministic precedence for equally timestamped reports.

Matched-response contrasts identify the gate policy effect without changing response strength. Frozen learner contrasts isolate the immediate scoring mechanism; they do not establish the effect of end-to-end training. In a second separately reported experiment, train each mode with identical budgets and independently initialized matched seeds to evaluate adaptation, including learning uncertainty.

## Experiment B: test message usefulness and failure cases

Build deterministic scout/follower fixtures with alternative routes. Include fresh accurate relevant warnings, stale warnings after hazards clear, off-corridor reports, and incorrect reports with low and high confidence. Include both short and long detours, delayed reports after service, and non-fork decisions. Fix report availability independently of receiver actions in these mechanism fixtures, record selected edges, and verify expected score calculations. These are implementation checks, not statistical evidence of superiority.

For broader evaluation, honest transmissions remain outcomes of each policy and may differ. Match exogenous environment randomness, not outcomes or all future packets. Report packet counts, admission/rejection reasons, accepted genuine/spoofed reports, decision changes and routing outcomes. Receiving less information is not itself proof of communication savings: separately count sent, delivered, processed and accepted packets. A receiver gate does not reduce transmission bandwidth unless a sending protocol does so.

## Experiment C: generalization

Use separately frozen random-exogenous and reactive/targeted scenario definitions. Tune gate thresholds only on validation scenarios; lock them before evaluating new graph/episode seeds. Use at least five independent training seeds for the follow-up learned comparison; report uncertainty at graph and training-seed levels. Predeclare scenario families and primary contrasts, and disclose all tested settings rather than selecting favorable cases.

Keep delivered nominal cost, delivered elapsed time, actual delivery and route-prior survival proxy separate. Include common-survivor time/cost comparisons and failure/censoring counts. Single-message controlled replay is restricted to exogenous attack/spoof schedules; reactive policy comparisons estimate total policy effects with endogenous adversary responses.

## Evidence already available

The completed matched heuristic suite and 12,500-run filtering/response ablation already provide relevant evidence; inspect them before adding runs. In the current reactive scenario, GATE minus COMM-ALL is -16.50 percentage points (paired graph-bootstrap interval -21.00 to -12.17). This refutes general delivery superiority for that tested implementation and regime. MAPPO gate minus all is positive in random and disrupted exogenous scenarios, but negative in reactive scenarios. These are different mechanisms from the submitted tabular score intervention.

## Decision rule for the paper

If matched filtering improves delivery in prespecified regimes, state those regimes and effect intervals. If it only reduces accepted/processed information at comparable delivery, report that narrower result and use a prespecified practical noninferiority margin; do not invent a communication cost absent from the model. If it harms performance, analyze the rejection mechanism and evaluate a revised gate on fresh test scenarios. Preserve the original gate as a comparator. Do not tune to recover the submitted percentages or claim universal superiority, causal benefit from an unmatched baseline, theoretical necessity/sufficiency, or a global parameter optimum from a finite grid.
