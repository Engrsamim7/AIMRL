# Adaptive gate: executed results

An adaptive model-based gate estimates routing regret and evidence innovation, combines independent sender reports with aging, and learns local sender agreement. It uses only public topology, declared sensor observations and packet contents. Probabilities and agreement scores are approximate model quantities, not calibrated confidence guarantees.

Settings were selected on separate validation episodes and three validation topologies, then frozen. Held-out graphs and episode schedules are new. Existing deep baseline models are reused with frozen weights; no new offline model training is claimed. Soft-fusion ALL uses the same risk estimator without value filtering, so an advantage over old binary ALL alone cannot establish a gate-specific benefit. Sender identity is unauthenticated; impersonation defeats the independent-source assumption. No general superiority, convergence or operational validity is claimed.

## Verification

| status   |   heldout_episodes |   convoy_records |   processed_packets |   validation_episodes |   controlled_episodes |   network_interventions |   controlled_interventions |   superiority_supported |   primary_tests |
|:---------|-------------------:|-----------------:|--------------------:|----------------------:|----------------------:|------------------------:|---------------------------:|------------------------:|----------------:|
| passed   |              21680 |            65040 |              995237 |                  3240 |                  5600 |                     293 |                        150 |                       0 |              24 |

## Locked settings

```json
{
  "parameters": {
    "risk_aversion": 0.25,
    "age_scale": 2.0,
    "min_value": 0.02
  },
  "selection": "highest mean delivery, then shorter delivered elapsed time, then fewer accepted packets; >=5% genuine admission; deterministic parameter tie order",
  "validation_genuine_admission": 0.07142857142857142,
  "unknown_block_prior": 0.05,
  "source_hash": "b293fa951ccb53b657093753aa54e89542fdc4bfbdcf7793dbe2826bb9b213c1"
}
```

## Primary contrasts

| family       | regime         | baseline   |   difference_pp |   simultaneous_lower_pp |   simultaneous_upper_pp | superiority_supported   |
|:-------------|:---------------|:-----------|----------------:|------------------------:|------------------------:|:------------------------|
| original-19  | reliable       | COMM-ALL   |    -1.66667     |                -8.33333 |                 0       | False                   |
| original-19  | reliable       | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| original-19  | delayed-spoof  | COMM-ALL   |     1.66667     |                 0       |                 8.33333 | False                   |
| original-19  | delayed-spoof  | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| original-19  | heavy-spoof    | COMM-ALL   |     0           |                 0       |                 0       | False                   |
| original-19  | heavy-spoof    | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| original-19  | reactive-spoof | COMM-ALL   |     5           |                 0       |                15       | False                   |
| original-19  | reactive-spoof | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-39 | reliable       | COMM-ALL   |    -1           |                -4       |                 0       | False                   |
| synthetic-39 | reliable       | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-39 | delayed-spoof  | COMM-ALL   |     0           |                -1.16667 |                 1.33333 | False                   |
| synthetic-39 | delayed-spoof  | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-39 | heavy-spoof    | COMM-ALL   |     8.32667e-17 |                -2.83333 |                 2.5     | False                   |
| synthetic-39 | heavy-spoof    | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-39 | reactive-spoof | COMM-ALL   |    -0.166667    |                -2.33333 |                 1.5974  | False                   |
| synthetic-39 | reactive-spoof | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-51 | reliable       | COMM-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-51 | reliable       | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-51 | delayed-spoof  | COMM-ALL   |     0.5         |                 0       |                 2.33333 | False                   |
| synthetic-51 | delayed-spoof  | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-51 | heavy-spoof    | COMM-ALL   |     0           |                -2.26406 |                 2       | False                   |
| synthetic-51 | heavy-spoof    | SOFT-ALL   |     0           |                 0       |                 0       | False                   |
| synthetic-51 | reactive-spoof | COMM-ALL   |    -0.333333    |                -2.83333 |                 1.16667 | False                   |
| synthetic-51 | reactive-spoof | SOFT-ALL   |     0           |                 0       |                 0       | False                   |

## Controlled probes: delay 1, no packet loss

| case               |   delay |   loss | method     |   delivery_rate |
|:-------------------|--------:|-------:|:-----------|----------------:|
| accurate           |       1 |      0 | COMM-ALL   |        1        |
| accurate           |       1 |      0 | FRC        |        1        |
| accurate           |       1 |      0 | NC         |        0.666667 |
| accurate           |       1 |      0 | SOFT-ALL   |        1        |
| accurate           |       1 |      0 | SOFT-FRC   |        1        |
| accurate           |       1 |      0 | SOFT-NC    |        0.666667 |
| accurate           |       1 |      0 | VALUE-GATE |        1        |
| high-clear         |       1 |      0 | COMM-ALL   |        0.666667 |
| high-clear         |       1 |      0 | FRC        |        0.666667 |
| high-clear         |       1 |      0 | NC         |        0.666667 |
| high-clear         |       1 |      0 | SOFT-ALL   |        1        |
| high-clear         |       1 |      0 | SOFT-FRC   |        1        |
| high-clear         |       1 |      0 | SOFT-NC    |        0.666667 |
| high-clear         |       1 |      0 | VALUE-GATE |        1        |
| impersonated-clear |       1 |      0 | COMM-ALL   |        0.666667 |
| impersonated-clear |       1 |      0 | FRC        |        0.666667 |
| impersonated-clear |       1 |      0 | NC         |        0.666667 |
| impersonated-clear |       1 |      0 | SOFT-ALL   |        0.333333 |
| impersonated-clear |       1 |      0 | SOFT-FRC   |        0.333333 |
| impersonated-clear |       1 |      0 | SOFT-NC    |        0.666667 |
| impersonated-clear |       1 |      0 | VALUE-GATE |        0.333333 |
| low-clear          |       1 |      0 | COMM-ALL   |        0.666667 |
| low-clear          |       1 |      0 | FRC        |        1        |
| low-clear          |       1 |      0 | NC         |        0.666667 |
| low-clear          |       1 |      0 | SOFT-ALL   |        1        |
| low-clear          |       1 |      0 | SOFT-FRC   |        1        |
| low-clear          |       1 |      0 | SOFT-NC    |        0.666667 |
| low-clear          |       1 |      0 | VALUE-GATE |        1        |

## Fresh held-out delivery; soft comparators isolate the estimator from admission

![Fresh held-out delivery; soft comparators isolate the estimator from admission](01_delivery.png)

## Bonferroni-adjusted paired bootstrap intervals for 24 prespecified contrasts

![Bonferroni-adjusted paired bootstrap intervals for 24 prespecified contrasts](02_primary_contrasts.png)

## Constructed truthful/false/impersonated reports: benefits and identity failure boundary

![Constructed truthful/false/impersonated reports: benefits and identity failure boundary](03_controlled.png)

## Selective admission is not transmission bandwidth reduction

![Selective admission is not transmission bandwidth reduction](04_admission.png)

## Component effects and implementation overhead; measured on shared machine

![Component effects and implementation overhead; measured on shared machine](05_ablation_runtime.png)

## Complete packet suppression: conditional realized effects, not additive policy benefit

![Complete packet suppression: conditional realized effects, not additive policy benefit](06_packet_replay.png)
