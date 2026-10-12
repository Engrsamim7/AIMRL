# Communication opportunity audit

Replayed **7,560 network episodes** and **2,400 controlled episodes** with the original parameters and schedules. All checked physical metrics, packet admission counts and network convoy records reproduced the archived experiment. No training or parameter selection was performed.

## What the audit found

- **SOFT-ALL:** 2,440 genuine blocked-edge reports; 1,554 fresh reports not superseded by own sensing; 33 concerned the proposed route; 20 met the current-hazard opportunity definition. All peer history changed the next edge in 0/44,143 decisions; new inboxes changed it in 0 decisions.
- **VALUE-GATE:** 2,440 genuine blocked-edge reports; 1,554 fresh reports not superseded by own sensing; 33 concerned the proposed route; 20 met the current-hazard opportunity definition. All peer history changed the next edge in 0/44,143 decisions; new inboxes changed it in 0 decisions.
- **Whole-inbox causal replay:** 704 interventions, 0 changed receiver paths, 0 helpful and 0 harmful receiver delivery effects. This is a declared subset, not every episode.

- **Warning-driven action intervention:** 21 structural warning opportunities in exogenous regimes; taking one public-weight next hop that avoids the warned edge changed 16 receiver paths, helped receiver delivery in 10 cases and harmed it in 1 cases. This targeted mechanism probe is not an algorithm comparison.

## Why warnings can fail to change routes

With the declared 0.05 block prior and initial sender agreement 2/3, even a confidence-1 warning with no age or distance decay gives a single-report probability of only **0.2006**. Decay reduces its increment. The chosen risk-aversion parameter is 0.0; the edge penalty is 12 times the estimated risk. This is a model assumption, not calibrated hazard probability. A warning therefore need not overcome the reference cost of a detour. The figure compares the observed innovation penalty and detour cost in currently blocked cases; other simultaneous evidence can also affect a decision.

The next model should be tested for whether it responds to useful observations before testing whether filtering adds value. Calibrate report interpretation and predicted decision benefit on new training data; evaluate a stronger matched ALL estimator as well as the gate. Predefine a sweep of scout lead time, sensing overlap, warning delay and hazard persistence, including cases where communication is redundant or late. Do not train on this diagnostic test set or select only favorable scenarios.

## Definitions and limits

The warning funnel counts packets, not independent episodes. A structural warning opportunity requires a genuine blocked report within the common TTL, no equally new or newer fresh own observation, membership in the reference route without the current inbox, and an alternative route avoiding that edge. A current-hazard opportunity additionally requires that the reported edge is actually blocked at decision time. The separate clear-alternative count requires the alternative to avoid all currently active blocks. These last two labels use evaluator-only state; the actor never receives them. This is an instantaneous diagnostic, not a promise that the warning or alternative stays valid until traversal.

The without-inbox probe retains old admitted reports. The local-only probe removes peer reports, warning anchors, agreement feedback and sender reputation, while preserving factual previous movement and own observations. These are isolated one-decision probes, not complete no-communication trajectories. Complete SOFT-NC trajectories are also reproduced.

Whole-inbox causal replay removes all packets waiting at one routing decision, retains earlier reports, and runs both futures to completion. Exact simulator/event/RNG state is copied, and the entire shared-time attack schedule is checked. It covers all nonempty inboxes in the first five episodes on the original graph and first graph of each synthetic family, in the three exogenous regimes, for SOFT-ALL and VALUE-GATE. Reactive/targeted cases appear only in observational and one-step diagnostics.

The warning-response probe selects every structural warning opportunity for SOFT-ALL in exogenous network regimes, collapsing duplicate warnings for the same decision and edge. It changes only the next hop to the public-weight shortest route avoiding the reported edge, then resumes the original policy. It does not force continued avoidance after later decisions. Genuine labels define the diagnostic population; this is not a deployable perfect-message selector. Gain values are intervention minus factual, whereas batch delta values are factual minus suppression. Exogenous attack schedules are checked in both probes.

Envelope logs cover scheduled packets; lost packets are excluded. Packets scheduled after episode completion, arriving after receiver completion, or never consumed at a decision are retained separately. The timing table counts reported-edge entry before arrival on the factual path; a report about an untraversed edge is not classified as late. Admission does not save transmission bandwidth: both communicating methods broadcast before filtering.

This audit reuses previously inspected test schedules for diagnosis. It must not be used as training data for a later claimed fresh test. A subsequent design needs new training/validation/test schedules and a preregistered range of conditions. Genuine reports describe revealed observations; they are not perfect ground truth.

## Warning funnel by network family and regime

| family       | regime         | method     |   processed |   genuine_warnings |   fresh_warnings |   not_locally_superseded |   on_route |   structural_opportunities |   current_hazard_opportunities |   clear_alternative_opportunities |
|:-------------|:---------------|:-----------|------------:|-------------------:|-----------------:|-------------------------:|-----------:|---------------------------:|-------------------------------:|----------------------------------:|
| original-19  | delayed-spoof  | SOFT-ALL   |         572 |                 28 |               28 |                       24 |          0 |                          0 |                              0 |                                 0 |
| original-19  | delayed-spoof  | SOFT-NC    |         544 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| original-19  | delayed-spoof  | VALUE-GATE |         572 |                 28 |               28 |                       24 |          0 |                          0 |                              0 |                                 0 |
| original-19  | heavy-spoof    | SOFT-ALL   |        2433 |                 24 |               24 |                       22 |          0 |                          0 |                              0 |                                 0 |
| original-19  | heavy-spoof    | SOFT-NC    |        2409 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| original-19  | heavy-spoof    | VALUE-GATE |        2433 |                 24 |               24 |                       22 |          0 |                          0 |                              0 |                                 0 |
| original-19  | reactive-spoof | SOFT-ALL   |         633 |                 15 |               14 |                       13 |          0 |                          0 |                              0 |                                 0 |
| original-19  | reactive-spoof | SOFT-NC    |         618 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| original-19  | reactive-spoof | VALUE-GATE |         633 |                 15 |               14 |                       13 |          0 |                          0 |                              0 |                                 0 |
| original-19  | reliable       | SOFT-ALL   |          37 |                 37 |               37 |                       29 |          0 |                          0 |                              0 |                                 0 |
| original-19  | reliable       | VALUE-GATE |          37 |                 37 |               37 |                       29 |          0 |                          0 |                              0 |                                 0 |
| synthetic-39 | delayed-spoof  | SOFT-ALL   |       14477 |                484 |              427 |                      259 |          7 |                          4 |                              4 |                                 3 |
| synthetic-39 | delayed-spoof  | SOFT-NC    |       13988 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| synthetic-39 | delayed-spoof  | VALUE-GATE |       14477 |                484 |              427 |                      259 |          7 |                          4 |                              4 |                                 3 |
| synthetic-39 | heavy-spoof    | SOFT-ALL   |       56311 |                427 |              372 |                      267 |          2 |                          0 |                              0 |                                 0 |
| synthetic-39 | heavy-spoof    | SOFT-NC    |       55880 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| synthetic-39 | heavy-spoof    | VALUE-GATE |       56311 |                427 |              372 |                      267 |          2 |                          0 |                              0 |                                 0 |
| synthetic-39 | reactive-spoof | SOFT-ALL   |       14009 |                108 |               88 |                       64 |          0 |                          0 |                              0 |                                 0 |
| synthetic-39 | reactive-spoof | SOFT-NC    |       13901 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| synthetic-39 | reactive-spoof | VALUE-GATE |       14009 |                108 |               88 |                       64 |          0 |                          0 |                              0 |                                 0 |
| synthetic-39 | reliable       | SOFT-ALL   |         829 |                814 |              810 |                      522 |         17 |                         15 |                             14 |                                12 |
| synthetic-39 | reliable       | VALUE-GATE |         829 |                814 |              810 |                      522 |         17 |                         15 |                             14 |                                12 |
| synthetic-51 | delayed-spoof  | SOFT-ALL   |        8441 |                122 |              115 |                       89 |          3 |                          1 |                              1 |                                 1 |
| synthetic-51 | delayed-spoof  | SOFT-NC    |        8319 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| synthetic-51 | delayed-spoof  | VALUE-GATE |        8441 |                122 |              115 |                       89 |          3 |                          1 |                              1 |                                 1 |
| synthetic-51 | heavy-spoof    | SOFT-ALL   |       32876 |                 96 |               84 |                       64 |          3 |                          0 |                              0 |                                 0 |
| synthetic-51 | heavy-spoof    | SOFT-NC    |       32780 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| synthetic-51 | heavy-spoof    | VALUE-GATE |       32876 |                 96 |               84 |                       64 |          3 |                          0 |                              0 |                                 0 |
| synthetic-51 | reactive-spoof | SOFT-ALL   |        8305 |                 55 |               55 |                       48 |          0 |                          0 |                              0 |                                 0 |
| synthetic-51 | reactive-spoof | SOFT-NC    |        8250 |                  0 |                0 |                        0 |          0 |                          0 |                              0 |                                 0 |
| synthetic-51 | reactive-spoof | VALUE-GATE |        8305 |                 55 |               55 |                       48 |          0 |                          0 |                              0 |                                 0 |
| synthetic-51 | reliable       | SOFT-ALL   |         230 |                230 |              230 |                      153 |          1 |                          1 |                              1 |                                 1 |
| synthetic-51 | reliable       | VALUE-GATE |         230 |                230 |              230 |                      153 |          1 |                          1 |                              1 |                                 1 |

## Action influence

| scope      | family             | regime             | method     |   decisions |   decisions_with_inbox |   next_edge_changes_from_new_inbox |   next_edge_changes_from_all_history |   selected_active_edges |
|:-----------|:-------------------|:-------------------|:-----------|------------:|-----------------------:|-----------------------------------:|-------------------------------------:|------------------------:|
| controlled | accurate           | delay=1.0,loss=0.0 | SOFT-ALL   |         600 |                    100 |                                 50 |                                   50 |                       0 |
| controlled | accurate           | delay=1.0,loss=0.0 | SOFT-NC    |         550 |                      0 |                                  0 |                                    0 |                      50 |
| controlled | accurate           | delay=1.0,loss=0.0 | VALUE-GATE |         600 |                    100 |                                 50 |                                   50 |                       0 |
| controlled | accurate           | delay=1.0,loss=0.2 | SOFT-ALL   |         590 |                     81 |                                 40 |                                   40 |                      10 |
| controlled | accurate           | delay=1.0,loss=0.2 | SOFT-NC    |         550 |                      0 |                                  0 |                                    0 |                      50 |
| controlled | accurate           | delay=1.0,loss=0.2 | VALUE-GATE |         590 |                     81 |                                 40 |                                   40 |                      10 |
| controlled | accurate           | delay=4.0,loss=0.0 | SOFT-ALL   |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | accurate           | delay=4.0,loss=0.0 | SOFT-NC    |         550 |                      0 |                                  0 |                                    0 |                      50 |
| controlled | accurate           | delay=4.0,loss=0.0 | VALUE-GATE |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | accurate           | delay=4.0,loss=0.2 | SOFT-ALL   |         550 |                     41 |                                  0 |                                    0 |                      50 |
| controlled | accurate           | delay=4.0,loss=0.2 | SOFT-NC    |         550 |                      0 |                                  0 |                                    0 |                      50 |
| controlled | accurate           | delay=4.0,loss=0.2 | VALUE-GATE |         550 |                     41 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=1.0,loss=0.0 | SOFT-ALL   |         600 |                    100 |                                 50 |                                   50 |                       0 |
| controlled | high-clear         | delay=1.0,loss=0.0 | SOFT-NC    |         550 |                    100 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=1.0,loss=0.0 | VALUE-GATE |         600 |                    100 |                                 50 |                                   50 |                       0 |
| controlled | high-clear         | delay=1.0,loss=0.2 | SOFT-ALL   |         581 |                    100 |                                 49 |                                   49 |                      19 |
| controlled | high-clear         | delay=1.0,loss=0.2 | SOFT-NC    |         550 |                    100 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=1.0,loss=0.2 | VALUE-GATE |         590 |                    100 |                                 40 |                                   40 |                      10 |
| controlled | high-clear         | delay=4.0,loss=0.0 | SOFT-ALL   |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=4.0,loss=0.0 | SOFT-NC    |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=4.0,loss=0.0 | VALUE-GATE |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=4.0,loss=0.2 | SOFT-ALL   |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=4.0,loss=0.2 | SOFT-NC    |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | high-clear         | delay=4.0,loss=0.2 | VALUE-GATE |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=1.0,loss=0.0 | SOFT-ALL   |         500 |                    100 |                                 50 |                                   50 |                     100 |
| controlled | impersonated-clear | delay=1.0,loss=0.0 | SOFT-NC    |         550 |                    100 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=1.0,loss=0.0 | VALUE-GATE |         600 |                    100 |                                 50 |                                   50 |                       0 |
| controlled | impersonated-clear | delay=1.0,loss=0.2 | SOFT-ALL   |         500 |                    100 |                                 50 |                                   50 |                     100 |
| controlled | impersonated-clear | delay=1.0,loss=0.2 | SOFT-NC    |         550 |                    100 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=1.0,loss=0.2 | VALUE-GATE |         590 |                    100 |                                 40 |                                   40 |                      10 |
| controlled | impersonated-clear | delay=4.0,loss=0.0 | SOFT-ALL   |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=4.0,loss=0.0 | SOFT-NC    |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=4.0,loss=0.0 | VALUE-GATE |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=4.0,loss=0.2 | SOFT-ALL   |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=4.0,loss=0.2 | SOFT-NC    |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | impersonated-clear | delay=4.0,loss=0.2 | VALUE-GATE |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=1.0,loss=0.0 | SOFT-ALL   |         600 |                    100 |                                 50 |                                   50 |                       0 |
| controlled | low-clear          | delay=1.0,loss=0.0 | SOFT-NC    |         550 |                    100 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=1.0,loss=0.0 | VALUE-GATE |         600 |                    100 |                                 50 |                                   50 |                       0 |
| controlled | low-clear          | delay=1.0,loss=0.2 | SOFT-ALL   |         581 |                    100 |                                 49 |                                   49 |                      19 |
| controlled | low-clear          | delay=1.0,loss=0.2 | SOFT-NC    |         550 |                    100 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=1.0,loss=0.2 | VALUE-GATE |         590 |                    100 |                                 40 |                                   40 |                      10 |
| controlled | low-clear          | delay=4.0,loss=0.0 | SOFT-ALL   |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=4.0,loss=0.0 | SOFT-NC    |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=4.0,loss=0.0 | VALUE-GATE |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=4.0,loss=0.2 | SOFT-ALL   |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=4.0,loss=0.2 | SOFT-NC    |         550 |                     50 |                                  0 |                                    0 |                      50 |
| controlled | low-clear          | delay=4.0,loss=0.2 | VALUE-GATE |         550 |                     50 |                                  0 |                                    0 |                      50 |
| network    | original-19        | delayed-spoof      | SOFT-ALL   |         359 |                    211 |                                  0 |                                    0 |                       8 |
| network    | original-19        | delayed-spoof      | SOFT-NC    |         359 |                    211 |                                  0 |                                    0 |                       8 |
| network    | original-19        | delayed-spoof      | VALUE-GATE |         359 |                    211 |                                  0 |                                    0 |                       8 |
| network    | original-19        | heavy-spoof        | SOFT-ALL   |         362 |                    258 |                                  0 |                                    0 |                       6 |
| network    | original-19        | heavy-spoof        | SOFT-NC    |         362 |                    258 |                                  0 |                                    0 |                       6 |
| network    | original-19        | heavy-spoof        | VALUE-GATE |         362 |                    258 |                                  0 |                                    0 |                       6 |
| network    | original-19        | reactive-spoof     | SOFT-ALL   |         360 |                    214 |                                  0 |                                    0 |                       1 |
| network    | original-19        | reactive-spoof     | SOFT-NC    |         360 |                    214 |                                  0 |                                    0 |                       1 |
| network    | original-19        | reactive-spoof     | VALUE-GATE |         360 |                    214 |                                  0 |                                    0 |                       1 |
| network    | original-19        | reliable           | SOFT-ALL   |         357 |                     28 |                                  0 |                                    0 |                       8 |
| network    | original-19        | reliable           | SOFT-NC    |         357 |                      0 |                                  0 |                                    0 |                       8 |
| network    | original-19        | reliable           | VALUE-GATE |         357 |                     28 |                                  0 |                                    0 |                       8 |
| network    | synthetic-39       | delayed-spoof      | SOFT-ALL   |        6185 |                   4500 |                                  0 |                                    0 |                      70 |
| network    | synthetic-39       | delayed-spoof      | SOFT-NC    |        6185 |                   4481 |                                  0 |                                    0 |                      70 |
| network    | synthetic-39       | delayed-spoof      | VALUE-GATE |        6185 |                   4500 |                                  0 |                                    0 |                      70 |
| network    | synthetic-39       | heavy-spoof        | SOFT-ALL   |        6221 |                   4961 |                                  0 |                                    0 |                      55 |
| network    | synthetic-39       | heavy-spoof        | SOFT-NC    |        6221 |                   4961 |                                  0 |                                    0 |                      55 |
| network    | synthetic-39       | heavy-spoof        | VALUE-GATE |        6221 |                   4961 |                                  0 |                                    0 |                      55 |
| network    | synthetic-39       | reactive-spoof     | SOFT-ALL   |        6210 |                   4470 |                                  0 |                                    0 |                      37 |
| network    | synthetic-39       | reactive-spoof     | SOFT-NC    |        6210 |                   4467 |                                  0 |                                    0 |                      37 |
| network    | synthetic-39       | reactive-spoof     | VALUE-GATE |        6210 |                   4470 |                                  0 |                                    0 |                      37 |
| network    | synthetic-39       | reliable           | SOFT-ALL   |        6221 |                    658 |                                  0 |                                    0 |                      63 |
| network    | synthetic-39       | reliable           | SOFT-NC    |        6221 |                      0 |                                  0 |                                    0 |                      63 |
| network    | synthetic-39       | reliable           | VALUE-GATE |        6221 |                    658 |                                  0 |                                    0 |                      63 |
| network    | synthetic-51       | delayed-spoof      | SOFT-ALL   |        4475 |                   2773 |                                  0 |                                    0 |                      36 |
| network    | synthetic-51       | delayed-spoof      | SOFT-NC    |        4475 |                   2762 |                                  0 |                                    0 |                      36 |
| network    | synthetic-51       | delayed-spoof      | VALUE-GATE |        4475 |                   2773 |                                  0 |                                    0 |                      36 |
| network    | synthetic-51       | heavy-spoof        | SOFT-ALL   |        4463 |                   3174 |                                  0 |                                    0 |                      53 |
| network    | synthetic-51       | heavy-spoof        | SOFT-NC    |        4463 |                   3174 |                                  0 |                                    0 |                      53 |
| network    | synthetic-51       | heavy-spoof        | VALUE-GATE |        4463 |                   3174 |                                  0 |                                    0 |                      53 |
| network    | synthetic-51       | reactive-spoof     | SOFT-ALL   |        4487 |                   2780 |                                  0 |                                    0 |                      10 |
| network    | synthetic-51       | reactive-spoof     | SOFT-NC    |        4487 |                   2777 |                                  0 |                                    0 |                      10 |
| network    | synthetic-51       | reactive-spoof     | VALUE-GATE |        4487 |                   2780 |                                  0 |                                    0 |                      10 |
| network    | synthetic-51       | reliable           | SOFT-ALL   |        4443 |                    186 |                                  0 |                                    0 |                      48 |
| network    | synthetic-51       | reliable           | SOFT-NC    |        4443 |                      0 |                                  0 |                                    0 |                      48 |
| network    | synthetic-51       | reliable           | VALUE-GATE |        4443 |                    186 |                                  0 |                                    0 |                      48 |

## Batch causal effects

| family       | regime        | method     |   interventions |   changed_paths |   helpful_receiver_delivery |   harmful_receiver_delivery |   changes_episode_delivery |   changes_nominal_cost |
|:-------------|:--------------|:-----------|----------------:|----------------:|----------------------------:|----------------------------:|---------------------------:|-----------------------:|
| original-19  | delayed-spoof | SOFT-ALL   |              34 |               0 |                           0 |                           0 |                          0 |                      0 |
| original-19  | delayed-spoof | VALUE-GATE |              34 |               0 |                           0 |                           0 |                          0 |                      0 |
| original-19  | heavy-spoof   | SOFT-ALL   |              45 |               0 |                           0 |                           0 |                          0 |                      0 |
| original-19  | heavy-spoof   | VALUE-GATE |              45 |               0 |                           0 |                           0 |                          0 |                      0 |
| original-19  | reliable      | SOFT-ALL   |               7 |               0 |                           0 |                           0 |                          0 |                      0 |
| original-19  | reliable      | VALUE-GATE |               7 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-39 | delayed-spoof | SOFT-ALL   |              76 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-39 | delayed-spoof | VALUE-GATE |              76 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-39 | heavy-spoof   | SOFT-ALL   |              80 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-39 | heavy-spoof   | VALUE-GATE |              80 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-39 | reliable      | SOFT-ALL   |              10 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-39 | reliable      | VALUE-GATE |              10 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-51 | delayed-spoof | SOFT-ALL   |              45 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-51 | delayed-spoof | VALUE-GATE |              45 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-51 | heavy-spoof   | SOFT-ALL   |              50 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-51 | heavy-spoof   | VALUE-GATE |              50 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-51 | reliable      | SOFT-ALL   |               5 |               0 |                           0 |                           0 |                          0 |                      0 |
| synthetic-51 | reliable      | VALUE-GATE |               5 |               0 |                           0 |                           0 |                          0 |                      0 |

## Warning-driven action effects

| family       | regime        |   interventions |   currently_blocked |   changed_paths |   helpful_delivery |   harmful_delivery |   fewer_blocked_encounters |
|:-------------|:--------------|----------------:|--------------------:|----------------:|-------------------:|-------------------:|---------------------------:|
| synthetic-39 | delayed-spoof |               4 |                   4 |               4 |                  3 |                  0 |                          4 |
| synthetic-39 | reliable      |              15 |                  14 |              10 |                  5 |                  1 |                          6 |
| synthetic-51 | delayed-spoof |               1 |                   1 |               1 |                  1 |                  0 |                          1 |
| synthetic-51 | reliable      |               1 |                   1 |               1 |                  1 |                  0 |                          1 |

## Packet timing

| scope      | family             | regime             | method     |   scheduled_packets |   processed |   receiver_finished_by_arrival |   after_episode_end |   enters_reported_edge_before_arrival |
|:-----------|:-------------------|:-------------------|:-----------|--------------------:|------------:|-------------------------------:|--------------------:|--------------------------------------:|
| controlled | accurate           | delay=1.0,loss=0.0 | SOFT-ALL   |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | accurate           | delay=1.0,loss=0.0 | VALUE-GATE |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | accurate           | delay=1.0,loss=0.2 | SOFT-ALL   |                  81 |          81 |                              0 |                   0 |                                     0 |
| controlled | accurate           | delay=1.0,loss=0.2 | VALUE-GATE |                  81 |          81 |                              0 |                   0 |                                     0 |
| controlled | accurate           | delay=4.0,loss=0.0 | SOFT-ALL   |                 100 |          50 |                             25 |                   0 |                                    50 |
| controlled | accurate           | delay=4.0,loss=0.0 | VALUE-GATE |                 100 |          50 |                             25 |                   0 |                                    50 |
| controlled | accurate           | delay=4.0,loss=0.2 | SOFT-ALL   |                  81 |          41 |                             20 |                   0 |                                    40 |
| controlled | accurate           | delay=4.0,loss=0.2 | VALUE-GATE |                  81 |          41 |                             20 |                   0 |                                    40 |
| controlled | high-clear         | delay=1.0,loss=0.0 | SOFT-ALL   |                 200 |         200 |                              0 |                   0 |                                     0 |
| controlled | high-clear         | delay=1.0,loss=0.0 | SOFT-NC    |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | high-clear         | delay=1.0,loss=0.0 | VALUE-GATE |                 200 |         200 |                              0 |                   0 |                                     0 |
| controlled | high-clear         | delay=1.0,loss=0.2 | SOFT-ALL   |                 181 |         181 |                              0 |                   0 |                                     0 |
| controlled | high-clear         | delay=1.0,loss=0.2 | SOFT-NC    |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | high-clear         | delay=1.0,loss=0.2 | VALUE-GATE |                 181 |         181 |                              0 |                   0 |                                     0 |
| controlled | high-clear         | delay=4.0,loss=0.0 | SOFT-ALL   |                 200 |         100 |                             75 |                   0 |                                   100 |
| controlled | high-clear         | delay=4.0,loss=0.0 | SOFT-NC    |                 100 |          50 |                             50 |                   0 |                                    50 |
| controlled | high-clear         | delay=4.0,loss=0.0 | VALUE-GATE |                 200 |         100 |                             75 |                   0 |                                   100 |
| controlled | high-clear         | delay=4.0,loss=0.2 | SOFT-ALL   |                 181 |          91 |                             70 |                   0 |                                    90 |
| controlled | high-clear         | delay=4.0,loss=0.2 | SOFT-NC    |                 100 |          50 |                             50 |                   0 |                                    50 |
| controlled | high-clear         | delay=4.0,loss=0.2 | VALUE-GATE |                 181 |          91 |                             70 |                   0 |                                    90 |
| controlled | impersonated-clear | delay=1.0,loss=0.0 | SOFT-ALL   |                 200 |         200 |                              0 |                   0 |                                     0 |
| controlled | impersonated-clear | delay=1.0,loss=0.0 | SOFT-NC    |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | impersonated-clear | delay=1.0,loss=0.0 | VALUE-GATE |                 200 |         200 |                              0 |                   0 |                                     0 |
| controlled | impersonated-clear | delay=1.0,loss=0.2 | SOFT-ALL   |                 181 |         181 |                              0 |                   0 |                                     0 |
| controlled | impersonated-clear | delay=1.0,loss=0.2 | SOFT-NC    |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | impersonated-clear | delay=1.0,loss=0.2 | VALUE-GATE |                 181 |         181 |                              0 |                   0 |                                     0 |
| controlled | impersonated-clear | delay=4.0,loss=0.0 | SOFT-ALL   |                 200 |         100 |                             75 |                   0 |                                   100 |
| controlled | impersonated-clear | delay=4.0,loss=0.0 | SOFT-NC    |                 100 |          50 |                             50 |                   0 |                                    50 |
| controlled | impersonated-clear | delay=4.0,loss=0.0 | VALUE-GATE |                 200 |         100 |                             75 |                   0 |                                   100 |
| controlled | impersonated-clear | delay=4.0,loss=0.2 | SOFT-ALL   |                 181 |          91 |                             70 |                   0 |                                    90 |
| controlled | impersonated-clear | delay=4.0,loss=0.2 | SOFT-NC    |                 100 |          50 |                             50 |                   0 |                                    50 |
| controlled | impersonated-clear | delay=4.0,loss=0.2 | VALUE-GATE |                 181 |          91 |                             70 |                   0 |                                    90 |
| controlled | low-clear          | delay=1.0,loss=0.0 | SOFT-ALL   |                 200 |         200 |                              0 |                   0 |                                     0 |
| controlled | low-clear          | delay=1.0,loss=0.0 | SOFT-NC    |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | low-clear          | delay=1.0,loss=0.0 | VALUE-GATE |                 200 |         200 |                              0 |                   0 |                                     0 |
| controlled | low-clear          | delay=1.0,loss=0.2 | SOFT-ALL   |                 181 |         181 |                              0 |                   0 |                                     0 |
| controlled | low-clear          | delay=1.0,loss=0.2 | SOFT-NC    |                 100 |         100 |                              0 |                   0 |                                     0 |
| controlled | low-clear          | delay=1.0,loss=0.2 | VALUE-GATE |                 181 |         181 |                              0 |                   0 |                                     0 |
| controlled | low-clear          | delay=4.0,loss=0.0 | SOFT-ALL   |                 200 |         100 |                             75 |                   0 |                                   100 |
| controlled | low-clear          | delay=4.0,loss=0.0 | SOFT-NC    |                 100 |          50 |                             50 |                   0 |                                    50 |
| controlled | low-clear          | delay=4.0,loss=0.0 | VALUE-GATE |                 200 |         100 |                             75 |                   0 |                                   100 |
| controlled | low-clear          | delay=4.0,loss=0.2 | SOFT-ALL   |                 181 |          91 |                             70 |                   0 |                                    90 |
| controlled | low-clear          | delay=4.0,loss=0.2 | SOFT-NC    |                 100 |          50 |                             50 |                   0 |                                    50 |
| controlled | low-clear          | delay=4.0,loss=0.2 | VALUE-GATE |                 181 |          91 |                             70 |                   0 |                                    90 |
| network    | original-19        | delayed-spoof      | SOFT-ALL   |                1092 |         572 |                            337 |                 259 |                                    14 |
| network    | original-19        | delayed-spoof      | SOFT-NC    |                 999 |         544 |                            293 |                 231 |                                    11 |
| network    | original-19        | delayed-spoof      | VALUE-GATE |                1092 |         572 |                            337 |                 259 |                                    14 |
| network    | original-19        | heavy-spoof        | SOFT-ALL   |                4392 |        2433 |                           1337 |                1055 |                                    34 |
| network    | original-19        | heavy-spoof        | SOFT-NC    |                4307 |        2409 |                           1281 |                1003 |                                    33 |
| network    | original-19        | heavy-spoof        | VALUE-GATE |                4392 |        2433 |                           1337 |                1055 |                                    34 |
| network    | original-19        | reactive-spoof     | SOFT-ALL   |                1143 |         633 |                            339 |                 260 |                                    32 |
| network    | original-19        | reactive-spoof     | SOFT-NC    |                1099 |         618 |                            317 |                 241 |                                    32 |
| network    | original-19        | reactive-spoof     | VALUE-GATE |                1143 |         633 |                            339 |                 260 |                                    32 |
| network    | original-19        | reliable           | SOFT-ALL   |                  88 |          37 |                             16 |                   0 |                                     2 |
| network    | original-19        | reliable           | VALUE-GATE |                  88 |          37 |                             16 |                   0 |                                     2 |
| network    | synthetic-39       | delayed-spoof      | SOFT-ALL   |               19413 |       14477 |                           3505 |                2407 |                                   160 |
| network    | synthetic-39       | delayed-spoof      | SOFT-NC    |               18830 |       13988 |                           3452 |                2384 |                                   140 |
| network    | synthetic-39       | delayed-spoof      | VALUE-GATE |               19413 |       14477 |                           3505 |                2407 |                                   160 |
| network    | synthetic-39       | heavy-spoof        | SOFT-ALL   |               75974 |       56311 |                          13822 |                9650 |                                   522 |
| network    | synthetic-39       | heavy-spoof        | SOFT-NC    |               75437 |       55880 |                          13772 |                9627 |                                   500 |
| network    | synthetic-39       | heavy-spoof        | VALUE-GATE |               75974 |       56311 |                          13822 |                9650 |                                   522 |
| network    | synthetic-39       | reactive-spoof     | SOFT-ALL   |               18807 |       14009 |                           3303 |                2479 |                                   223 |
| network    | synthetic-39       | reactive-spoof     | SOFT-NC    |               18670 |       13901 |                           3282 |                2465 |                                   216 |
| network    | synthetic-39       | reactive-spoof     | VALUE-GATE |               18807 |       14009 |                           3303 |                2479 |                                   223 |
| network    | synthetic-39       | reliable           | SOFT-ALL   |                 874 |         829 |                             30 |                   0 |                                     3 |
| network    | synthetic-39       | reliable           | VALUE-GATE |                 874 |         829 |                             30 |                   0 |                                     3 |
| network    | synthetic-51       | delayed-spoof      | SOFT-ALL   |               13067 |        8441 |                           3213 |                2474 |                                    65 |
| network    | synthetic-51       | delayed-spoof      | SOFT-NC    |               12882 |        8319 |                           3190 |                2463 |                                    62 |
| network    | synthetic-51       | delayed-spoof      | VALUE-GATE |               13067 |        8441 |                           3213 |                2474 |                                    65 |
| network    | synthetic-51       | heavy-spoof        | SOFT-ALL   |               51060 |       32876 |                          12636 |                9727 |                                   274 |
| network    | synthetic-51       | heavy-spoof        | SOFT-NC    |               50884 |       32780 |                          12585 |                9691 |                                   261 |
| network    | synthetic-51       | heavy-spoof        | VALUE-GATE |               51060 |       32876 |                          12636 |                9727 |                                   274 |
| network    | synthetic-51       | reactive-spoof     | SOFT-ALL   |               12843 |        8305 |                           3132 |                2453 |                                   231 |
| network    | synthetic-51       | reactive-spoof     | SOFT-NC    |               12771 |        8250 |                           3124 |                2448 |                                   230 |
| network    | synthetic-51       | reactive-spoof     | VALUE-GATE |               12843 |        8305 |                           3132 |                2453 |                                   231 |
| network    | synthetic-51       | reliable           | SOFT-ALL   |                 272 |         230 |                             20 |                   0 |                                     4 |
| network    | synthetic-51       | reliable           | VALUE-GATE |                 272 |         230 |                             20 |                   0 |                                     4 |

## Reproduce

```bash
bash setup_local.sh
cd simulator
../.venv/bin/python audit_communication_opportunities.py --output out/communication-opportunity-audit-new
../.venv/bin/python audit_warning_response.py --run out/communication-opportunity-audit-new
cd ..
MPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_communication_audit.py --run simulator/out/communication-opportunity-audit-new --output revision/communication-opportunity-audit-new
```

Original experiment source hash: `4da5ccebf13143b860c2705362bb1263e1e4906c45190a4fc8260629fe405c6c`. Audit script SHA256: `fc1689b406e42c60ec4134fa1c3acbf22f9870ec172bc0174b6a3de5259bb6a9`.
