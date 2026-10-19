# Decision-level gate diagnosis

Exploratory diagnosis following the null matched-training primary result. No fitted gate or final routing checkpoint was changed. All figures and tables are descriptive.

Exactly reproduced **512 original COMBINED trajectories / 2,560 convoy records**. Audited **42,596 eligible packet candidates** and completed **2,041 full-inbox accept/reject replay pairs** plus **828 prefix-context pairs**. All sixteen reconstructed warmup actors matched their recorded network hashes.

## Candidate totals and denominators

| algo   |   eligible |   genuine |   raw_admit |   final_admit |   processed_messages |   routing_decisions |
|:-------|-----------:|----------:|------------:|--------------:|---------------------:|--------------------:|
| dqn    |      22497 |      3366 |        9338 |         10824 |                28224 |               12522 |
| mappo  |      20099 |      3117 |        8625 |          9964 |                25571 |               12092 |

## Candidate coverage and selection

| algo   | category           |   candidates |   selected |   coverage_pct |
|:-------|:-------------------|-------------:|-----------:|---------------:|
| dqn    | agreement          |         9934 |        224 |        2.25488 |
| dqn    | clearance_override |          575 |        131 |       22.7826  |
| dqn    | disagreement       |         9927 |        448 |        4.51294 |
| dqn    | warning_override   |         2061 |        185 |        8.97623 |
| mappo  | agreement          |         8636 |        224 |        2.59379 |
| mappo  | clearance_override |          811 |        186 |       22.9346  |
| mappo  | disagreement       |         8502 |        448 |        5.26935 |
| mappo  | warning_override   |         2150 |        195 |        9.06977 |

## Selected causal packet effects

| algo   | category           |   pairs |   next_action_changes |   path_changes |   actual_delivery_helps |   actual_delivery_harms |   actual_utility_helps |   actual_utility_harms |   utility_unchanged |   mean_actual_utility_gain |   mean_abs_prediction_error |
|:-------|:-------------------|--------:|----------------------:|---------------:|------------------------:|------------------------:|-----------------------:|-----------------------:|--------------------:|---------------------------:|----------------------------:|
| dqn    | agreement          |     224 |                     0 |             16 |                       0 |                       8 |                      8 |                      8 |                 208 |                  -2.4085   |                     6.1278  |
| dqn    | clearance_override |     131 |                    15 |             27 |                       8 |                       5 |                     14 |                     13 |                 104 |                   1.35577  |                     8.76583 |
| dqn    | disagreement       |     448 |                     1 |              1 |                       0 |                       1 |                      0 |                      1 |                 447 |                  -0.178365 |                     4.51393 |
| dqn    | warning_override   |     185 |                     0 |              4 |                       4 |                       0 |                      4 |                      0 |                 181 |                   1.45785  |                     3.67632 |
| mappo  | agreement          |     224 |                     0 |             12 |                       4 |                       2 |                     10 |                      2 |                 212 |                   0.849028 |                     6.42478 |
| mappo  | clearance_override |     186 |                    17 |             29 |                       7 |                       4 |                     18 |                     11 |                 157 |                   1.04505  |                     7.714   |
| mappo  | disagreement       |     448 |                     0 |              0 |                       0 |                       0 |                      0 |                      0 |                 448 |                   0        |                     4.49605 |
| mappo  | warning_override   |     195 |                     0 |              2 |                       2 |                       0 |                      2 |                      0 |                 193 |                   0.718396 |                     3.47313 |

## Exhaustive relevant disagreement follow-up

| algo   |   pairs |   next_action_changes |   path_changes |   actual_delivery_helps |   actual_delivery_harms |   actual_utility_helps |   actual_utility_harms |   utility_unchanged |   mean_actual_utility_gain |
|:-------|--------:|----------------------:|---------------:|------------------------:|------------------------:|-----------------------:|-----------------------:|--------------------:|---------------------------:|
| dqn    |     106 |                    28 |             30 |                       7 |                       4 |                     10 |                     20 |                  76 |                   1.31357  |
| mappo  |      48 |                     9 |              9 |                       2 |                       2 |                      7 |                      2 |                  39 |                   0.291918 |

## Prediction transport: equal weight per actor seed

| algo   | stage   |   seeds |   labels |     mae |   zero_mae |   nonzero_labels |   positive_delivery_labels |
|:-------|:--------|--------:|---------:|--------:|-----------:|-----------------:|---------------------------:|
| dqn    | adapted |       8 |      779 | 6.62621 |    3.98018 |               70 |                         35 |
| dqn    | warmup  |       8 |      801 | 6.45029 |    3.72141 |               62 |                         36 |
| mappo  | adapted |       8 |      779 | 6.50269 |    3.24316 |               60 |                         29 |
| mappo  | warmup  |       8 |      811 | 6.60731 |    3.42232 |               71 |                         34 |

## Same actor, simple static comparison

| algo   | method       |   convoys |   delivery_pct |   utility |
|:-------|:-------------|----------:|---------------:|----------:|
| dqn    | COMBINED     |      1280 |        81.25   |   6.2522  |
| dqn    | KEEP-WARNING |      1280 |        81.25   |   6.20388 |
| dqn    | SAFE         |      1280 |        80.625  |   5.83721 |
| mappo  | COMBINED     |      1280 |        81.875  |   8.09379 |
| mappo  | KEEP-WARNING |      1280 |        81.7188 |   7.96552 |
| mappo  | SAFE         |      1280 |        81.7969 |   8.0381  |

## Actual clearance opportunities

| algo   |   eligible |   genuine_clear |   genuine_clear_against_warning |   correct_clear_against_warning |   clear_against_warning |   false_warnings |   false_warnings_forced_accepted |
|:-------|-----------:|----------------:|--------------------------------:|--------------------------------:|------------------------:|-----------------:|---------------------------------:|
| dqn    |      22497 |               0 |                               0 |                             824 |                    2048 |             5754 |                             3140 |
| mappo  |      20099 |               0 |                               0 |                             760 |                    1903 |             5157 |                             2883 |

## Credit-context comparison

| algo   | category         |   pairs |   prefix_delivery_only |   full_delivery_only |   prefix_utility_only |   full_utility_only |   mean_abs_prefix |   mean_abs_full |
|:-------|:-----------------|--------:|-----------------------:|---------------------:|----------------------:|--------------------:|------------------:|----------------:|
| dqn    | disagreement     |     224 |                      1 |                    0 |                     1 |                   0 |          0.276904 |        0        |
| dqn    | warning_override |     185 |                      1 |                    0 |                     2 |                   0 |          1.82349  |        1.45785  |
| mappo  | disagreement     |     224 |                      3 |                    0 |                     4 |                   0 |          0.993991 |        0        |
| mappo  | warning_override |     195 |                      1 |                    0 |                     2 |                   0 |          1.10368  |        0.718396 |

The relevant-packet follow-up replays all **154** publicly action-changing or reachable peer-warning disagreements in the same subset. **6** overlap the initial capped sample. These are reused trajectories, not fresh independent trials. Selection was added after inspecting the initial mechanism diagnostics; see [the follow-up specification](../gate-decision-targeted-followup.md). Its effects must not be pooled with the initial sample as independent observations.

## How to interpret these diagnostics

The admission comparison holds earlier packet interpretation fixed: a disagreement is the learned gate changing the safeguards-only decision on the same public prefix. Category selection is chronological and capped per episode; replay frequencies are not unbiased population effect estimates. Packet effects are conditional and cannot be summed into the total gate effect. Each full-inbox branch matching the original choice reproduces the complete factual convoy outcomes. All remaining current-inbox packets and future events are retained, except in the separately identified prefix check.

Warmup/adapted prediction errors use new layouts and tapes, the same original estimator, and the original label-generation routine. The two actors can visit different states and create different packets, so error differences do not isolate staleness as a causal explanation of the null. Compare the model with the zero-value predictor as well as with its own earlier errors. A lower adapted error is evidence against a blanket staleness explanation.

KEEP-WARNING has no learned value model: it blocks every peer clearance of a fresh peer warning, including corroborated clearances. Own observations and the common TTL still apply. All three static-comparison methods use the COMBINED-trained actor. This can favor its familiar gate and is not a comparison of separately optimized systems or fresh confirmation. Check actual genuine reopening opportunities before treating a conservative rule as generally preferable. Correct forged payloads are possible; true origin and current truth are evaluator-only annotations.

Delivery is binary and checked against convoy records. Utility includes failure and elapsed-time penalties. An elapsed-time reduction can arise from early destruction and is not an efficiency benefit; inspect accept_rows/reject_rows for paired successful convoy costs. No bandwidth, universal-superiority, equivalence or noninferiority claim follows. Original historical results remain unchanged.

## Reproduce

See [the diagnosis protocol](../gate-decision-diagnosis-protocol.md). After running the diagnostic runner from simulator/, run this report from the repository root:

```bash
MPLCONFIGDIR=/tmp/aimrl-mpl OPENBLAS_NUM_THREADS=1 .venv/bin/python simulator/report_gate_diagnosis.py --run simulator/out/gate-decision-diagnosis --parent simulator/out/matched-gate-study --output revision/gate-decision-diagnosis
```
