# Fresh actor-specific value gate: executed results

Completed **92,610 frozen-test episodes** and **463,050 convoy records**. The study includes 3,600 fresh DQN/MAPPO training episodes and 700 separate causal-label-generation episodes. Value regressors fit episodes 0–79 of each 100-episode label study; 80–99 are internal held-out diagnostics. All nine declared cases and the original-topology transfer check are retained.

Across 81 primary delivery comparisons with a **198-test correction**, **4 supported superiority** and **3 supported a disadvantage**. These are actor/baseline/case-specific results on constructed physical scout/follower benchmarks, not general superiority.

## Frozen settings

```json
{
  "status": "locked_before_test",
  "source_hash": "48515b25f8c781ecdf4bd037a4885935ad2ec0acef1f6c34f8de12776b54158f",
  "strength": 12.0,
  "gate": {
    "value_threshold": -1.0,
    "uncertainty_weight": 0.0
  },
  "frc": {
    "eta": 8.0,
    "kappa_min": 0.4
  },
  "test_results_inspected": false
}
```

## Supported positive comparisons

| algo    | case                   | baseline   |   difference_pp |   lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:--------|:-----------------------|:-----------|----------------:|-----------:|-----------:|:------------------------|:-------------------------|
| planner | timely-misleading      | ALL        |             4.2 |    1.15251 |    7.74749 | True                    | False                    |
| planner | timely-misleading      | FRC        |             4.2 |    1.1     |    7.7     | True                    | False                    |
| planner | multiple-impersonation | ALL        |             8   |    4.35251 |   11.9475  | True                    | False                    |
| planner | multiple-impersonation | FRC        |             8   |    4.25754 |   12.3     | True                    | False                    |

## Supported adverse comparisons

| algo    | case                   | baseline   |   difference_pp |   lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:--------|:-----------------------|:-----------|----------------:|-----------:|-----------:|:------------------------|:-------------------------|
| planner | timely-misleading      | SAFE-ALL   |            -5   |   -8.84749 |  -1.9      | False                   | True                     |
| planner | delayed-misleading     | SAFE-ALL   |            -3.8 |   -8.24749 |  -0.9      | False                   | True                     |
| planner | multiple-impersonation | SAFE-ALL   |            -6.6 |  -12.7     |  -0.952513 | False                   | True                     |

## All delivery results

| family            | algo    | case                   | method   |   episodes |   delivery_pct |   follower_delivery_pct |   utility |   censored |
|:------------------|:--------|:-----------------------|:---------|-----------:|---------------:|------------------------:|----------:|-----------:|
| constructed-forks | dqn     | delayed-misleading     | ALL      |        600 |        97.2    |                 95.3333 |  24.3782  |          0 |
| constructed-forks | dqn     | delayed-misleading     | FRC      |        600 |        97.2    |                 95.3333 |  24.3782  |          0 |
| constructed-forks | dqn     | delayed-misleading     | NC       |        600 |        57.7    |                 29.5    |  -4.25776 |          0 |
| constructed-forks | dqn     | delayed-misleading     | SAFE-ALL |        600 |        97.1333 |                 95.2222 |  24.3243  |          0 |
| constructed-forks | dqn     | delayed-misleading     | VALUE    |        600 |        92.9    |                 88.1667 |  21.2582  |          0 |
| constructed-forks | dqn     | late-warning           | ALL      |        600 |        58.3333 |                 30.5556 |  -3.7231  |          0 |
| constructed-forks | dqn     | late-warning           | FRC      |        600 |        58.3333 |                 30.5556 |  -3.7231  |          0 |
| constructed-forks | dqn     | late-warning           | NC       |        600 |        58.3333 |                 30.5556 |  -3.7231  |          0 |
| constructed-forks | dqn     | late-warning           | SAFE-ALL |        600 |        58.3333 |                 30.5556 |  -3.7231  |          0 |
| constructed-forks | dqn     | late-warning           | VALUE    |        600 |        58.3333 |                 30.5556 |  -3.7231  |          0 |
| constructed-forks | dqn     | multiple-impersonation | ALL      |        600 |        97.0333 |                 95.0556 |  24.1844  |          0 |
| constructed-forks | dqn     | multiple-impersonation | FRC      |        600 |        97.0333 |                 95.0556 |  24.1844  |          0 |
| constructed-forks | dqn     | multiple-impersonation | NC       |        600 |        57.0667 |                 28.4444 |  -4.44032 |          0 |
| constructed-forks | dqn     | multiple-impersonation | SAFE-ALL |        600 |        98.1667 |                 96.9444 |  24.9762  |          0 |
| constructed-forks | dqn     | multiple-impersonation | VALUE    |        600 |        97      |                 95      |  24.1277  |          0 |
| constructed-forks | dqn     | no-hazards             | ALL      |        600 |       100      |                100      |  26.8917  |          0 |
| constructed-forks | dqn     | no-hazards             | FRC      |        600 |       100      |                100      |  26.8917  |          0 |
| constructed-forks | dqn     | no-hazards             | NC       |        600 |       100      |                100      |  26.9193  |          0 |
| constructed-forks | dqn     | no-hazards             | SAFE-ALL |        600 |       100      |                100      |  26.8918  |          0 |
| constructed-forks | dqn     | no-hazards             | VALUE    |        600 |       100      |                100      |  26.8985  |          0 |
| constructed-forks | dqn     | redundant-sensing      | ALL      |        600 |       100      |                100      |  26.5214  |          0 |
| constructed-forks | dqn     | redundant-sensing      | FRC      |        600 |       100      |                100      |  26.5214  |          0 |
| constructed-forks | dqn     | redundant-sensing      | NC       |        600 |       100      |                100      |  26.5214  |          0 |
| constructed-forks | dqn     | redundant-sensing      | SAFE-ALL |        600 |       100      |                100      |  26.5214  |          0 |
| constructed-forks | dqn     | redundant-sensing      | VALUE    |        600 |       100      |                100      |  26.5214  |          0 |
| constructed-forks | dqn     | short-lived-honest     | ALL      |        600 |       100      |                100      |  26.8278  |          0 |
| constructed-forks | dqn     | short-lived-honest     | FRC      |        600 |       100      |                100      |  26.8278  |          0 |
| constructed-forks | dqn     | short-lived-honest     | NC       |        600 |       100      |                100      |  26.9126  |          0 |
| constructed-forks | dqn     | short-lived-honest     | SAFE-ALL |        600 |       100      |                100      |  26.8278  |          0 |
| constructed-forks | dqn     | short-lived-honest     | VALUE    |        600 |       100      |                100      |  26.8278  |          0 |
| constructed-forks | dqn     | short-lived-misleading | ALL      |        600 |       100      |                100      |  26.7978  |          0 |
| constructed-forks | dqn     | short-lived-misleading | FRC      |        600 |       100      |                100      |  26.7978  |          0 |
| constructed-forks | dqn     | short-lived-misleading | NC       |        600 |       100      |                100      |  26.9127  |          0 |
| constructed-forks | dqn     | short-lived-misleading | SAFE-ALL |        600 |       100      |                100      |  26.7952  |          0 |
| constructed-forks | dqn     | short-lived-misleading | VALUE    |        600 |       100      |                100      |  26.799   |          0 |
| constructed-forks | dqn     | timely-honest          | ALL      |        600 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | dqn     | timely-honest          | FRC      |        600 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | dqn     | timely-honest          | NC       |        600 |        55.5333 |                 25.8889 |  -5.65233 |          0 |
| constructed-forks | dqn     | timely-honest          | SAFE-ALL |        600 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | dqn     | timely-honest          | VALUE    |        600 |        98.5    |                 97.5    |  25.3511  |          0 |
| constructed-forks | dqn     | timely-misleading      | ALL      |        600 |        98.2333 |                 97.0556 |  25.1536  |          0 |
| constructed-forks | dqn     | timely-misleading      | FRC      |        600 |        98.2333 |                 97.0556 |  25.1536  |          0 |
| constructed-forks | dqn     | timely-misleading      | NC       |        600 |        57.7333 |                 29.5556 |  -4.1114  |          0 |
| constructed-forks | dqn     | timely-misleading      | SAFE-ALL |        600 |        98.5    |                 97.5    |  25.3243  |          0 |
| constructed-forks | dqn     | timely-misleading      | VALUE    |        600 |        96.8667 |                 94.7778 |  24.0834  |          0 |
| constructed-forks | mappo   | delayed-misleading     | ALL      |        600 |        96.8667 |                 94.7778 |  24.1725  |          0 |
| constructed-forks | mappo   | delayed-misleading     | FRC      |        600 |        96.8667 |                 94.7778 |  24.1725  |          0 |
| constructed-forks | mappo   | delayed-misleading     | NC       |        600 |        58.0667 |                 30.1111 |  -3.98205 |          0 |
| constructed-forks | mappo   | delayed-misleading     | SAFE-ALL |        600 |        96.9    |                 94.8333 |  24.1948  |          0 |
| constructed-forks | mappo   | delayed-misleading     | VALUE    |        600 |        96.7333 |                 94.5556 |  24.0702  |          0 |
| constructed-forks | mappo   | late-warning           | ALL      |        600 |        58.3333 |                 30.5556 |  -3.72865 |          0 |
| constructed-forks | mappo   | late-warning           | FRC      |        600 |        58.3333 |                 30.5556 |  -3.72865 |          0 |
| constructed-forks | mappo   | late-warning           | NC       |        600 |        58.3333 |                 30.5556 |  -3.72865 |          0 |
| constructed-forks | mappo   | late-warning           | SAFE-ALL |        600 |        58.3333 |                 30.5556 |  -3.72865 |          0 |
| constructed-forks | mappo   | late-warning           | VALUE    |        600 |        58.3333 |                 30.5556 |  -3.72865 |          0 |
| constructed-forks | mappo   | multiple-impersonation | ALL      |        600 |        95.5333 |                 92.5556 |  23.1806  |          0 |
| constructed-forks | mappo   | multiple-impersonation | FRC      |        600 |        95.5333 |                 92.5556 |  23.1806  |          0 |
| constructed-forks | mappo   | multiple-impersonation | NC       |        600 |        56.3    |                 27.1667 |  -5.04938 |          0 |
| constructed-forks | mappo   | multiple-impersonation | SAFE-ALL |        600 |        97.3    |                 95.5    |  24.4733  |          0 |
| constructed-forks | mappo   | multiple-impersonation | VALUE    |        600 |        93.7    |                 89.5    |  21.7217  |          0 |
| constructed-forks | mappo   | no-hazards             | ALL      |        600 |       100      |                100      |  26.8788  |          0 |
| constructed-forks | mappo   | no-hazards             | FRC      |        600 |       100      |                100      |  26.879   |          0 |
| constructed-forks | mappo   | no-hazards             | NC       |        600 |       100      |                100      |  26.9141  |          0 |
| constructed-forks | mappo   | no-hazards             | SAFE-ALL |        600 |       100      |                100      |  26.879   |          0 |
| constructed-forks | mappo   | no-hazards             | VALUE    |        600 |       100      |                100      |  26.8896  |          0 |
| constructed-forks | mappo   | redundant-sensing      | ALL      |        600 |        98.6333 |                 97.7222 |  25.4695  |          0 |
| constructed-forks | mappo   | redundant-sensing      | FRC      |        600 |        98.6333 |                 97.7222 |  25.4695  |          0 |
| constructed-forks | mappo   | redundant-sensing      | NC       |        600 |       100      |                100      |  26.5214  |          0 |
| constructed-forks | mappo   | redundant-sensing      | SAFE-ALL |        600 |        98.6333 |                 97.7222 |  25.4695  |          0 |
| constructed-forks | mappo   | redundant-sensing      | VALUE    |        600 |        99.4333 |                 99.0556 |  26.1031  |          0 |
| constructed-forks | mappo   | short-lived-honest     | ALL      |        600 |       100      |                100      |  26.8187  |          0 |
| constructed-forks | mappo   | short-lived-honest     | FRC      |        600 |       100      |                100      |  26.8187  |          0 |
| constructed-forks | mappo   | short-lived-honest     | NC       |        600 |       100      |                100      |  26.9035  |          0 |
| constructed-forks | mappo   | short-lived-honest     | SAFE-ALL |        600 |       100      |                100      |  26.8187  |          0 |
| constructed-forks | mappo   | short-lived-honest     | VALUE    |        600 |       100      |                100      |  26.8187  |          0 |
| constructed-forks | mappo   | short-lived-misleading | ALL      |        600 |       100      |                100      |  26.79    |          0 |
| constructed-forks | mappo   | short-lived-misleading | FRC      |        600 |       100      |                100      |  26.79    |          0 |
| constructed-forks | mappo   | short-lived-misleading | NC       |        600 |       100      |                100      |  26.9016  |          0 |
| constructed-forks | mappo   | short-lived-misleading | SAFE-ALL |        600 |       100      |                100      |  26.7885  |          0 |
| constructed-forks | mappo   | short-lived-misleading | VALUE    |        600 |       100      |                100      |  26.7938  |          0 |
| constructed-forks | mappo   | timely-honest          | ALL      |        600 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | mappo   | timely-honest          | FRC      |        600 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | mappo   | timely-honest          | NC       |        600 |        55.4667 |                 25.7778 |  -5.71041 |          0 |
| constructed-forks | mappo   | timely-honest          | SAFE-ALL |        600 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | mappo   | timely-honest          | VALUE    |        600 |        96.6333 |                 94.3889 |  23.891   |          0 |
| constructed-forks | mappo   | timely-misleading      | ALL      |        600 |        98      |                 96.6667 |  25.0427  |          0 |
| constructed-forks | mappo   | timely-misleading      | FRC      |        600 |        98      |                 96.6667 |  25.0427  |          0 |
| constructed-forks | mappo   | timely-misleading      | NC       |        600 |        58.6333 |                 31.0556 |  -3.41639 |          0 |
| constructed-forks | mappo   | timely-misleading      | SAFE-ALL |        600 |        98.6    |                 97.6667 |  25.4838  |          0 |
| constructed-forks | mappo   | timely-misleading      | VALUE    |        600 |        95.0667 |                 91.7778 |  22.7563  |          0 |
| constructed-forks | planner | delayed-misleading     | ALL      |        200 |        92.4    |                 87.3333 |  20.7874  |          0 |
| constructed-forks | planner | delayed-misleading     | FRC      |        200 |        92.5    |                 87.5    |  20.8748  |          0 |
| constructed-forks | planner | delayed-misleading     | NC       |        200 |        58      |                 30      |  -4.02437 |          0 |
| constructed-forks | planner | delayed-misleading     | SAFE-ALL |        200 |        96.3    |                 93.8333 |  23.6302  |          0 |
| constructed-forks | planner | delayed-misleading     | VALUE    |        200 |        92.5    |                 87.5    |  20.8655  |          0 |
| constructed-forks | planner | late-warning           | ALL      |        200 |        58.6    |                 31      |  -3.51455 |          0 |
| constructed-forks | planner | late-warning           | FRC      |        200 |        58.6    |                 31      |  -3.51455 |          0 |
| constructed-forks | planner | late-warning           | NC       |        200 |        58.6    |                 31      |  -3.51455 |          0 |
| constructed-forks | planner | late-warning           | SAFE-ALL |        200 |        58.6    |                 31      |  -3.51455 |          0 |
| constructed-forks | planner | late-warning           | VALUE    |        200 |        58.6    |                 31      |  -3.51455 |          0 |
| constructed-forks | planner | multiple-impersonation | ALL      |        200 |        76.9    |                 61.5    |   9.42589 |          0 |
| constructed-forks | planner | multiple-impersonation | FRC      |        200 |        76.9    |                 61.5    |   9.42589 |          0 |
| constructed-forks | planner | multiple-impersonation | NC       |        200 |        57      |                 28.3333 |  -4.49263 |          0 |
| constructed-forks | planner | multiple-impersonation | SAFE-ALL |        200 |        91.5    |                 85.8333 |  19.8893  |          0 |
| constructed-forks | planner | multiple-impersonation | VALUE    |        200 |        84.9    |                 74.8333 |  15.1936  |          0 |
| constructed-forks | planner | no-hazards             | ALL      |        200 |       100      |                100      |  26.9091  |          0 |
| constructed-forks | planner | no-hazards             | FRC      |        200 |       100      |                100      |  26.9091  |          0 |
| constructed-forks | planner | no-hazards             | NC       |        200 |       100      |                100      |  26.9281  |          0 |
| constructed-forks | planner | no-hazards             | SAFE-ALL |        200 |       100      |                100      |  26.9087  |          0 |
| constructed-forks | planner | no-hazards             | VALUE    |        200 |       100      |                100      |  26.9091  |          0 |
| constructed-forks | planner | redundant-sensing      | ALL      |        200 |       100      |                100      |  26.4506  |          0 |
| constructed-forks | planner | redundant-sensing      | FRC      |        200 |       100      |                100      |  26.4506  |          0 |
| constructed-forks | planner | redundant-sensing      | NC       |        200 |       100      |                100      |  26.5214  |          0 |
| constructed-forks | planner | redundant-sensing      | SAFE-ALL |        200 |       100      |                100      |  26.4506  |          0 |
| constructed-forks | planner | redundant-sensing      | VALUE    |        200 |       100      |                100      |  26.4506  |          0 |
| constructed-forks | planner | short-lived-honest     | ALL      |        200 |       100      |                100      |  26.9155  |          0 |
| constructed-forks | planner | short-lived-honest     | FRC      |        200 |       100      |                100      |  26.9155  |          0 |
| constructed-forks | planner | short-lived-honest     | NC       |        200 |       100      |                100      |  26.9203  |          0 |
| constructed-forks | planner | short-lived-honest     | SAFE-ALL |        200 |       100      |                100      |  26.9002  |          0 |
| constructed-forks | planner | short-lived-honest     | VALUE    |        200 |       100      |                100      |  26.8624  |          0 |
| constructed-forks | planner | short-lived-misleading | ALL      |        200 |       100      |                100      |  26.8976  |          0 |
| constructed-forks | planner | short-lived-misleading | FRC      |        200 |       100      |                100      |  26.8976  |          0 |
| constructed-forks | planner | short-lived-misleading | NC       |        200 |       100      |                100      |  26.9197  |          0 |
| constructed-forks | planner | short-lived-misleading | SAFE-ALL |        200 |       100      |                100      |  26.873   |          0 |
| constructed-forks | planner | short-lived-misleading | VALUE    |        200 |       100      |                100      |  26.8034  |          0 |
| constructed-forks | planner | timely-honest          | ALL      |        200 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | planner | timely-honest          | FRC      |        200 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | planner | timely-honest          | NC       |        200 |        55      |                 25      |  -6.06735 |          0 |
| constructed-forks | planner | timely-honest          | SAFE-ALL |        200 |       100      |                100      |  26.5212  |          0 |
| constructed-forks | planner | timely-honest          | VALUE    |        200 |        99.2    |                 98.6667 |  25.8974  |          0 |
| constructed-forks | planner | timely-misleading      | ALL      |        200 |        87.7    |                 79.5    |  17.3219  |          0 |
| constructed-forks | planner | timely-misleading      | FRC      |        200 |        87.7    |                 79.5    |  17.3219  |          0 |
| constructed-forks | planner | timely-misleading      | NC       |        200 |        58      |                 30      |  -3.90315 |          0 |
| constructed-forks | planner | timely-misleading      | SAFE-ALL |        200 |        96.9    |                 94.8333 |  24.0491  |          0 |
| constructed-forks | planner | timely-misleading      | VALUE    |        200 |        91.9    |                 86.5    |  20.34    |          0 |
| original-topology | dqn     | delayed-misleading     | ALL      |         30 |        89.3333 |                 84.4444 |  18.1191  |          0 |
| original-topology | dqn     | delayed-misleading     | FRC      |         30 |        89.3333 |                 84.4444 |  18.1191  |          0 |
| original-topology | dqn     | delayed-misleading     | NC       |         30 |        90      |                 85.5556 |  18.6614  |          0 |
| original-topology | dqn     | delayed-misleading     | SAFE-ALL |         30 |        89.3333 |                 84.4444 |  18.1191  |          0 |
| original-topology | dqn     | delayed-misleading     | VALUE    |         30 |        89.3333 |                 84.4444 |  18.1318  |          0 |
| original-topology | dqn     | late-warning           | ALL      |         30 |        84      |                 87.7778 |  14.1579  |          0 |
| original-topology | dqn     | late-warning           | FRC      |         30 |        84      |                 87.7778 |  14.1579  |          0 |
| original-topology | dqn     | late-warning           | NC       |         30 |        84      |                 87.7778 |  14.1579  |          0 |
| original-topology | dqn     | late-warning           | SAFE-ALL |         30 |        84      |                 87.7778 |  14.1579  |          0 |
| original-topology | dqn     | late-warning           | VALUE    |         30 |        84      |                 87.7778 |  14.1579  |          0 |
| original-topology | dqn     | multiple-impersonation | ALL      |         30 |        83.3333 |                 78.8889 |  13.0319  |          0 |
| original-topology | dqn     | multiple-impersonation | FRC      |         30 |        83.3333 |                 78.8889 |  13.0319  |          0 |
| original-topology | dqn     | multiple-impersonation | NC       |         30 |        84      |                 80      |  13.663   |          0 |
| original-topology | dqn     | multiple-impersonation | SAFE-ALL |         30 |        84      |                 80      |  13.4476  |          0 |
| original-topology | dqn     | multiple-impersonation | VALUE    |         30 |        84.6667 |                 81.1111 |  13.9858  |          0 |
| original-topology | dqn     | no-hazards             | ALL      |         30 |       100      |                100      |  25.8466  |          0 |
| original-topology | dqn     | no-hazards             | FRC      |         30 |       100      |                100      |  25.8466  |          0 |
| original-topology | dqn     | no-hazards             | NC       |         30 |       100      |                100      |  25.9075  |          0 |
| original-topology | dqn     | no-hazards             | SAFE-ALL |         30 |       100      |                100      |  25.8466  |          0 |
| original-topology | dqn     | no-hazards             | VALUE    |         30 |       100      |                100      |  25.8928  |          0 |
| original-topology | dqn     | redundant-sensing      | ALL      |         30 |        91.3333 |                 92.2222 |  18.4896  |          0 |
| original-topology | dqn     | redundant-sensing      | FRC      |         30 |        91.3333 |                 92.2222 |  18.4896  |          0 |
| original-topology | dqn     | redundant-sensing      | NC       |         30 |        91.3333 |                 92.2222 |  18.4743  |          0 |
| original-topology | dqn     | redundant-sensing      | SAFE-ALL |         30 |        91.3333 |                 92.2222 |  18.4896  |          0 |
| original-topology | dqn     | redundant-sensing      | VALUE    |         30 |        91.3333 |                 92.2222 |  18.4743  |          0 |
| original-topology | dqn     | short-lived-honest     | ALL      |         30 |        82      |                 77.7778 |  12.6279  |          0 |
| original-topology | dqn     | short-lived-honest     | FRC      |         30 |        82      |                 77.7778 |  12.6279  |          0 |
| original-topology | dqn     | short-lived-honest     | NC       |         30 |        82      |                 77.7778 |  12.6222  |          0 |
| original-topology | dqn     | short-lived-honest     | SAFE-ALL |         30 |        82      |                 77.7778 |  12.6279  |          0 |
| original-topology | dqn     | short-lived-honest     | VALUE    |         30 |        82      |                 77.7778 |  12.6222  |          0 |
| original-topology | dqn     | short-lived-misleading | ALL      |         30 |        86.6667 |                 82.2222 |  16.5493  |          0 |
| original-topology | dqn     | short-lived-misleading | FRC      |         30 |        86.6667 |                 82.2222 |  16.5493  |          0 |
| original-topology | dqn     | short-lived-misleading | NC       |         30 |        86      |                 81.1111 |  16.1462  |          0 |
| original-topology | dqn     | short-lived-misleading | SAFE-ALL |         30 |        86.6667 |                 82.2222 |  16.5493  |          0 |
| original-topology | dqn     | short-lived-misleading | VALUE    |         30 |        86.6667 |                 82.2222 |  16.5525  |          0 |
| original-topology | dqn     | timely-honest          | ALL      |         30 |        72      |                 72.2222 |   5.47916 |          0 |
| original-topology | dqn     | timely-honest          | FRC      |         30 |        72      |                 72.2222 |   5.47916 |          0 |
| original-topology | dqn     | timely-honest          | NC       |         30 |        72      |                 72.2222 |   5.49163 |          0 |
| original-topology | dqn     | timely-honest          | SAFE-ALL |         30 |        72      |                 72.2222 |   5.47916 |          0 |
| original-topology | dqn     | timely-honest          | VALUE    |         30 |        72      |                 72.2222 |   5.49163 |          0 |
| original-topology | dqn     | timely-misleading      | ALL      |         30 |        77.3333 |                 75.5556 |   9.48484 |          0 |
| original-topology | dqn     | timely-misleading      | FRC      |         30 |        77.3333 |                 75.5556 |   9.48484 |          0 |
| original-topology | dqn     | timely-misleading      | NC       |         30 |        77.3333 |                 75.5556 |   9.54687 |          0 |
| original-topology | dqn     | timely-misleading      | SAFE-ALL |         30 |        77.3333 |                 75.5556 |   9.48484 |          0 |
| original-topology | dqn     | timely-misleading      | VALUE    |         30 |        78      |                 76.6667 |  10.0054  |          0 |
| original-topology | mappo   | delayed-misleading     | ALL      |         30 |        64.6667 |                 51.1111 |  -5.31599 |          0 |
| original-topology | mappo   | delayed-misleading     | FRC      |         30 |        64.6667 |                 51.1111 |  -5.31599 |          0 |
| original-topology | mappo   | delayed-misleading     | NC       |         30 |        63.3333 |                 48.8889 |  -7.29405 |          0 |
| original-topology | mappo   | delayed-misleading     | SAFE-ALL |         30 |        64.6667 |                 51.1111 |  -5.31599 |          0 |
| original-topology | mappo   | delayed-misleading     | VALUE    |         30 |        64.6667 |                 51.1111 |  -5.31599 |          0 |
| original-topology | mappo   | late-warning           | ALL      |         30 |        71.3333 |                 65.5556 |  -9.36989 |          9 |
| original-topology | mappo   | late-warning           | FRC      |         30 |        71.3333 |                 65.5556 |  -9.36989 |          9 |
| original-topology | mappo   | late-warning           | NC       |         30 |        71.3333 |                 65.5556 |  -9.36989 |          9 |
| original-topology | mappo   | late-warning           | SAFE-ALL |         30 |        71.3333 |                 65.5556 |  -9.36989 |          9 |
| original-topology | mappo   | late-warning           | VALUE    |         30 |        71.3333 |                 65.5556 |  -9.36989 |          9 |
| original-topology | mappo   | multiple-impersonation | ALL      |         30 |        84      |                 76.6667 |  13.7649  |          0 |
| original-topology | mappo   | multiple-impersonation | FRC      |         30 |        84      |                 76.6667 |  13.7649  |          0 |
| original-topology | mappo   | multiple-impersonation | NC       |         30 |        84      |                 76.6667 |  14.2267  |          0 |
| original-topology | mappo   | multiple-impersonation | SAFE-ALL |         30 |        84      |                 76.6667 |  13.5669  |          0 |
| original-topology | mappo   | multiple-impersonation | VALUE    |         30 |        84      |                 76.6667 |  13.883   |          0 |
| original-topology | mappo   | no-hazards             | ALL      |         30 |        88      |                 80      | -17.0302  |         18 |
| original-topology | mappo   | no-hazards             | FRC      |         30 |        88      |                 80      | -17.0302  |         18 |
| original-topology | mappo   | no-hazards             | NC       |         30 |        76      |                 60      | -36.8464  |         36 |
| original-topology | mappo   | no-hazards             | SAFE-ALL |         30 |        88      |                 80      | -17.0302  |         18 |
| original-topology | mappo   | no-hazards             | VALUE    |         30 |        86      |                 76.6667 | -21.8262  |         21 |
| original-topology | mappo   | redundant-sensing      | ALL      |         30 |        76      |                 76.6667 |   7.25301 |          0 |
| original-topology | mappo   | redundant-sensing      | FRC      |         30 |        76      |                 76.6667 |   7.25301 |          0 |
| original-topology | mappo   | redundant-sensing      | NC       |         30 |        77.3333 |                 78.8889 |   8.02204 |          0 |
| original-topology | mappo   | redundant-sensing      | SAFE-ALL |         30 |        76      |                 76.6667 |   7.25301 |          0 |
| original-topology | mappo   | redundant-sensing      | VALUE    |         30 |        76.6667 |                 77.7778 |   7.55052 |          0 |
| original-topology | mappo   | short-lived-honest     | ALL      |         30 |        71.3333 |                 62.2222 |   5.35987 |          0 |
| original-topology | mappo   | short-lived-honest     | FRC      |         30 |        71.3333 |                 62.2222 |   5.35987 |          0 |
| original-topology | mappo   | short-lived-honest     | NC       |         30 |        71.3333 |                 62.2222 |   5.35987 |          0 |
| original-topology | mappo   | short-lived-honest     | SAFE-ALL |         30 |        71.3333 |                 62.2222 |   5.35987 |          0 |
| original-topology | mappo   | short-lived-honest     | VALUE    |         30 |        71.3333 |                 62.2222 |   5.35987 |          0 |
| original-topology | mappo   | short-lived-misleading | ALL      |         30 |        69.3333 |                 55.5556 |  -6.81049 |          7 |
| original-topology | mappo   | short-lived-misleading | FRC      |         30 |        69.3333 |                 55.5556 |  -6.81049 |          7 |
| original-topology | mappo   | short-lived-misleading | NC       |         30 |        68      |                 53.3333 |  -8.74231 |          9 |
| original-topology | mappo   | short-lived-misleading | SAFE-ALL |         30 |        69.3333 |                 55.5556 |  -6.81049 |          7 |
| original-topology | mappo   | short-lived-misleading | VALUE    |         30 |        68.6667 |                 54.4444 |  -7.77395 |          8 |
| original-topology | mappo   | timely-honest          | ALL      |         30 |        62.6667 |                 56.6667 | -11.4762  |          6 |
| original-topology | mappo   | timely-honest          | FRC      |         30 |        62.6667 |                 56.6667 | -11.4762  |          6 |
| original-topology | mappo   | timely-honest          | NC       |         30 |        62.6667 |                 56.6667 | -11.4762  |          6 |
| original-topology | mappo   | timely-honest          | SAFE-ALL |         30 |        62.6667 |                 56.6667 | -11.4762  |          6 |
| original-topology | mappo   | timely-honest          | VALUE    |         30 |        62.6667 |                 56.6667 | -11.4762  |          6 |
| original-topology | mappo   | timely-misleading      | ALL      |         30 |        54.6667 |                 54.4444 | -20.7848  |          8 |
| original-topology | mappo   | timely-misleading      | FRC      |         30 |        54.6667 |                 54.4444 | -20.7848  |          8 |
| original-topology | mappo   | timely-misleading      | NC       |         30 |        47.3333 |                 42.2222 | -36.0826  |         13 |
| original-topology | mappo   | timely-misleading      | SAFE-ALL |         30 |        54.6667 |                 54.4444 | -20.7848  |          8 |
| original-topology | mappo   | timely-misleading      | VALUE    |         30 |        54      |                 53.3333 | -24.5964  |          9 |
| original-topology | planner | delayed-misleading     | ALL      |         10 |       100      |                100      |  25.5544  |          0 |
| original-topology | planner | delayed-misleading     | FRC      |         10 |       100      |                100      |  25.5544  |          0 |
| original-topology | planner | delayed-misleading     | NC       |         10 |       100      |                100      |  25.5544  |          0 |
| original-topology | planner | delayed-misleading     | SAFE-ALL |         10 |       100      |                100      |  25.5544  |          0 |
| original-topology | planner | delayed-misleading     | VALUE    |         10 |       100      |                100      |  25.5544  |          0 |
| original-topology | planner | late-warning           | ALL      |         10 |       100      |                100      |  24.4327  |          0 |
| original-topology | planner | late-warning           | FRC      |         10 |       100      |                100      |  24.4327  |          0 |
| original-topology | planner | late-warning           | NC       |         10 |       100      |                100      |  24.4327  |          0 |
| original-topology | planner | late-warning           | SAFE-ALL |         10 |       100      |                100      |  24.4327  |          0 |
| original-topology | planner | late-warning           | VALUE    |         10 |       100      |                100      |  24.4327  |          0 |
| original-topology | planner | multiple-impersonation | ALL      |         10 |        94      |                 93.3333 |  20.3672  |          0 |
| original-topology | planner | multiple-impersonation | FRC      |         10 |        94      |                 93.3333 |  20.3672  |          0 |
| original-topology | planner | multiple-impersonation | NC       |         10 |        94      |                 93.3333 |  20.3672  |          0 |
| original-topology | planner | multiple-impersonation | SAFE-ALL |         10 |        94      |                 93.3333 |  20.3672  |          0 |
| original-topology | planner | multiple-impersonation | VALUE    |         10 |        94      |                 93.3333 |  20.3672  |          0 |
| original-topology | planner | no-hazards             | ALL      |         10 |       100      |                100      |  25.5947  |          0 |
| original-topology | planner | no-hazards             | FRC      |         10 |       100      |                100      |  25.5947  |          0 |
| original-topology | planner | no-hazards             | NC       |         10 |       100      |                100      |  25.5947  |          0 |
| original-topology | planner | no-hazards             | SAFE-ALL |         10 |       100      |                100      |  25.5947  |          0 |
| original-topology | planner | no-hazards             | VALUE    |         10 |       100      |                100      |  25.5947  |          0 |
| original-topology | planner | redundant-sensing      | ALL      |         10 |        98      |                100      |  23.2343  |          0 |
| original-topology | planner | redundant-sensing      | FRC      |         10 |        98      |                100      |  23.2343  |          0 |
| original-topology | planner | redundant-sensing      | NC       |         10 |        94      |                 93.3333 |  20.0054  |          0 |
| original-topology | planner | redundant-sensing      | SAFE-ALL |         10 |        98      |                100      |  23.2343  |          0 |
| original-topology | planner | redundant-sensing      | VALUE    |         10 |        98      |                100      |  23.2343  |          0 |
| original-topology | planner | short-lived-honest     | ALL      |         10 |        92      |                 86.6667 |  19.0717  |          0 |
| original-topology | planner | short-lived-honest     | FRC      |         10 |        92      |                 86.6667 |  19.0717  |          0 |
| original-topology | planner | short-lived-honest     | NC       |         10 |        92      |                 86.6667 |  19.0717  |          0 |
| original-topology | planner | short-lived-honest     | SAFE-ALL |         10 |        92      |                 86.6667 |  19.0717  |          0 |
| original-topology | planner | short-lived-honest     | VALUE    |         10 |        92      |                 86.6667 |  19.0717  |          0 |
| original-topology | planner | short-lived-misleading | ALL      |         10 |       100      |                100      |  25.9386  |          0 |
| original-topology | planner | short-lived-misleading | FRC      |         10 |       100      |                100      |  25.9386  |          0 |
| original-topology | planner | short-lived-misleading | NC       |         10 |       100      |                100      |  25.9386  |          0 |
| original-topology | planner | short-lived-misleading | SAFE-ALL |         10 |       100      |                100      |  25.9386  |          0 |
| original-topology | planner | short-lived-misleading | VALUE    |         10 |       100      |                100      |  25.9386  |          0 |
| original-topology | planner | timely-honest          | ALL      |         10 |        88      |                 93.3333 |  15.6305  |          0 |
| original-topology | planner | timely-honest          | FRC      |         10 |        88      |                 93.3333 |  15.6305  |          0 |
| original-topology | planner | timely-honest          | NC       |         10 |        88      |                 93.3333 |  15.6305  |          0 |
| original-topology | planner | timely-honest          | SAFE-ALL |         10 |        88      |                 93.3333 |  15.6305  |          0 |
| original-topology | planner | timely-honest          | VALUE    |         10 |        88      |                 93.3333 |  15.6305  |          0 |
| original-topology | planner | timely-misleading      | ALL      |         10 |        88      |                 86.6667 |  15.3895  |          0 |
| original-topology | planner | timely-misleading      | FRC      |         10 |        88      |                 86.6667 |  15.3895  |          0 |
| original-topology | planner | timely-misleading      | NC       |         10 |        92      |                 93.3333 |  18.45    |          0 |
| original-topology | planner | timely-misleading      | SAFE-ALL |         10 |        88      |                 86.6667 |  15.3895  |          0 |
| original-topology | planner | timely-misleading      | VALUE    |         10 |        90      |                 90      |  17.0272  |          0 |

## All corrected comparisons

| algo    | case                   | baseline   |   difference_pp |   lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:--------|:-----------------------|:-----------|----------------:|-----------:|-----------:|:------------------------|:-------------------------|
| planner | timely-honest          | ALL        |    -0.8         |  -3.4      |   0        | False                   | False                    |
| planner | timely-honest          | FRC        |    -0.8         |  -3.3      |   0        | False                   | False                    |
| planner | timely-honest          | SAFE-ALL   |    -0.8         |  -3.14749  |   0        | False                   | False                    |
| planner | timely-misleading      | ALL        |     4.2         |   1.15251  |   7.74749  | True                    | False                    |
| planner | timely-misleading      | FRC        |     4.2         |   1.1      |   7.7      | True                    | False                    |
| planner | timely-misleading      | SAFE-ALL   |    -5           |  -8.84749  |  -1.9      | False                   | True                     |
| planner | delayed-misleading     | ALL        |     0.1         |   0        |   0.9      | False                   | False                    |
| planner | delayed-misleading     | FRC        |    -5.55112e-17 |  -0.947487 |   0.9      | False                   | False                    |
| planner | delayed-misleading     | SAFE-ALL   |    -3.8         |  -8.24749  |  -0.9      | False                   | True                     |
| planner | late-warning           | ALL        |     0           |   0        |   0        | False                   | False                    |
| planner | late-warning           | FRC        |     0           |   0        |   0        | False                   | False                    |
| planner | late-warning           | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| planner | redundant-sensing      | ALL        |     0           |   0        |   0        | False                   | False                    |
| planner | redundant-sensing      | FRC        |     0           |   0        |   0        | False                   | False                    |
| planner | redundant-sensing      | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| planner | short-lived-honest     | ALL        |     0           |   0        |   0        | False                   | False                    |
| planner | short-lived-honest     | FRC        |     0           |   0        |   0        | False                   | False                    |
| planner | short-lived-honest     | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| planner | short-lived-misleading | ALL        |     0           |   0        |   0        | False                   | False                    |
| planner | short-lived-misleading | FRC        |     0           |   0        |   0        | False                   | False                    |
| planner | short-lived-misleading | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| planner | multiple-impersonation | ALL        |     8           |   4.35251  |  11.9475   | True                    | False                    |
| planner | multiple-impersonation | FRC        |     8           |   4.25754  |  12.3      | True                    | False                    |
| planner | multiple-impersonation | SAFE-ALL   |    -6.6         | -12.7      |  -0.952513 | False                   | True                     |
| planner | no-hazards             | ALL        |     0           |   0        |   0        | False                   | False                    |
| planner | no-hazards             | FRC        |     0           |   0        |   0        | False                   | False                    |
| planner | no-hazards             | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| dqn     | timely-honest          | ALL        |    -1.5         |  -7.68995  |   0        | False                   | False                    |
| dqn     | timely-honest          | FRC        |    -1.5         |  -8.14749  |   0        | False                   | False                    |
| dqn     | timely-honest          | SAFE-ALL   |    -1.5         |  -7.44749  |   0        | False                   | False                    |
| dqn     | timely-misleading      | ALL        |    -1.36667     |  -9.63744  |   1.14749  | False                   | False                    |
| dqn     | timely-misleading      | FRC        |    -1.36667     |  -9.94749  |   1.14749  | False                   | False                    |
| dqn     | timely-misleading      | SAFE-ALL   |    -1.63333     |  -9.16332  |   0.447487 | False                   | False                    |
| dqn     | delayed-misleading     | ALL        |    -4.3         | -17.4324   |   0        | False                   | False                    |
| dqn     | delayed-misleading     | FRC        |    -4.3         | -17.5475   |   0        | False                   | False                    |
| dqn     | delayed-misleading     | SAFE-ALL   |    -4.23333     | -16.3      |   0.7      | False                   | False                    |
| dqn     | late-warning           | ALL        |     0           |   0        |   0        | False                   | False                    |
| dqn     | late-warning           | FRC        |     0           |   0        |   0        | False                   | False                    |
| dqn     | late-warning           | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| dqn     | redundant-sensing      | ALL        |     0           |   0        |   0        | False                   | False                    |
| dqn     | redundant-sensing      | FRC        |     0           |   0        |   0        | False                   | False                    |
| dqn     | redundant-sensing      | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| dqn     | short-lived-honest     | ALL        |     0           |   0        |   0        | False                   | False                    |
| dqn     | short-lived-honest     | FRC        |     0           |   0        |   0        | False                   | False                    |
| dqn     | short-lived-honest     | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| dqn     | short-lived-misleading | ALL        |     0           |   0        |   0        | False                   | False                    |
| dqn     | short-lived-misleading | FRC        |     0           |   0        |   0        | False                   | False                    |
| dqn     | short-lived-misleading | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| dqn     | multiple-impersonation | ALL        |    -0.0333333   |  -3.86499  |   2.74749  | False                   | False                    |
| dqn     | multiple-impersonation | FRC        |    -0.0333333   |  -3.81583  |   2.89497  | False                   | False                    |
| dqn     | multiple-impersonation | SAFE-ALL   |    -1.16667     |  -4.77747  |   1.03333  | False                   | False                    |
| dqn     | no-hazards             | ALL        |     0           |   0        |   0        | False                   | False                    |
| dqn     | no-hazards             | FRC        |     0           |   0        |   0        | False                   | False                    |
| dqn     | no-hazards             | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| mappo   | timely-honest          | ALL        |    -3.36667     | -14.8849   |   0        | False                   | False                    |
| mappo   | timely-honest          | FRC        |    -3.36667     | -14.0749   |   0        | False                   | False                    |
| mappo   | timely-honest          | SAFE-ALL   |    -3.36667     | -13.2475   |   0        | False                   | False                    |
| mappo   | timely-misleading      | ALL        |    -2.93333     | -10.7475   |   0.5      | False                   | False                    |
| mappo   | timely-misleading      | FRC        |    -2.93333     | -10.7      |   0.4      | False                   | False                    |
| mappo   | timely-misleading      | SAFE-ALL   |    -3.53333     | -11.2374   |   0        | False                   | False                    |
| mappo   | delayed-misleading     | ALL        |    -0.133333    |  -1.44749  |   0.5      | False                   | False                    |
| mappo   | delayed-misleading     | FRC        |    -0.133333    |  -1.5      |   0.5      | False                   | False                    |
| mappo   | delayed-misleading     | SAFE-ALL   |    -0.166667    |  -1.6      |   0.8      | False                   | False                    |
| mappo   | late-warning           | ALL        |     0           |   0        |   0        | False                   | False                    |
| mappo   | late-warning           | FRC        |     0           |   0        |   0        | False                   | False                    |
| mappo   | late-warning           | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| mappo   | redundant-sensing      | ALL        |     0.8         |  -0.2      |   3.04749  | False                   | False                    |
| mappo   | redundant-sensing      | FRC        |     0.8         |  -0.266667 |   3        | False                   | False                    |
| mappo   | redundant-sensing      | SAFE-ALL   |     0.8         |  -0.231658 |   2.9      | False                   | False                    |
| mappo   | short-lived-honest     | ALL        |     0           |   0        |   0        | False                   | False                    |
| mappo   | short-lived-honest     | FRC        |     0           |   0        |   0        | False                   | False                    |
| mappo   | short-lived-honest     | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| mappo   | short-lived-misleading | ALL        |     0           |   0        |   0        | False                   | False                    |
| mappo   | short-lived-misleading | FRC        |     0           |   0        |   0        | False                   | False                    |
| mappo   | short-lived-misleading | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |
| mappo   | multiple-impersonation | ALL        |    -1.83333     |  -7.34749  |   1.54749  | False                   | False                    |
| mappo   | multiple-impersonation | FRC        |    -1.83333     |  -7.99497  |   1.6825   | False                   | False                    |
| mappo   | multiple-impersonation | SAFE-ALL   |    -3.6         |  -8.94749  |   0.394975 | False                   | False                    |
| mappo   | no-hazards             | ALL        |     0           |   0        |   0        | False                   | False                    |
| mappo   | no-hazards             | FRC        |     0           |   0        |   0        | False                   | False                    |
| mappo   | no-hazards             | SAFE-ALL   |     0           |   0        |   0        | False                   | False                    |

## Value learning diagnostics

| algo    |   seed |   examples |   fitted_examples |   positive_delivery_labels |   negative_delivery_labels |   holdout_examples |   mean_absolute_error |   mean_squared_error |   holdout_positive_delivery_labels |
|:--------|-------:|-----------:|------------------:|---------------------------:|---------------------------:|-------------------:|----------------------:|---------------------:|-----------------------------------:|
| dqn     |      0 |        444 |               360 |                         30 |                          1 |                 84 |               9.13618 |              295.542 |                                  7 |
| dqn     |      1 |        454 |               354 |                         24 |                          1 |                100 |               7.17645 |              257.432 |                                  5 |
| dqn     |      2 |        462 |               367 |                         39 |                          0 |                 95 |               9.91056 |              286.792 |                                  9 |
| mappo   |      0 |        450 |               350 |                         33 |                          2 |                100 |               9.73793 |              280.833 |                                  8 |
| mappo   |      1 |        459 |               363 |                         27 |                          0 |                 96 |               7.36135 |              174.124 |                                  4 |
| mappo   |      2 |        415 |               324 |                         23 |                          2 |                 91 |               7.58401 |              263.472 |                                  6 |
| planner |     -1 |        421 |               338 |                         33 |                          2 |                 83 |              10.3499  |              350.049 |                                 12 |

## What these results can establish

A positive result must identify the actor, baseline and declared condition shown above. Gains over ALL or tuned FRC that do not persist against SAFE-ALL do not establish a learned-value contribution beyond conservative clearance filtering. Cross-actor, no-hazard, redundant-sensing, late-warning and impersonation cases bound any claim. Original-topology transfer is descriptive, with different sensing/attack timing and no actor retraining on that graph. Constructed layouts randomize costs, stages and hot branches; they remain designed mechanism benchmarks, not representative sampled military networks.

Methods use the same actor weights, sensors, target/departure schedules and exogenous tapes. Training, validation and test namespaces are disjoint. All gates are receiver-side filters: admission counts are not bandwidth savings. Public feature vectors exclude genuine labels, simulator attacks, future outcomes, packet origins and privileged critic state. Sender agreement and ensemble uncertainty remain approximate. Full-episode training labels are conditional on chronological prefixes and may differ from the distribution induced by the learned gate.

Confidence intervals use 20,000 paired bootstrap draws, clustering graph and within-graph episodes while crossing independent training seeds with shared environment tapes. Two-sided Bonferroni tails cover 198 tests. With only three training seeds and ten constructed layouts, uncertainty estimates have limited support; no real-world confidence guarantee or convergence claim follows. Common-survivor time/cost contrasts are in common_survivors.csv and exclude pairs where either method fails delivery. No test outcome was used to fit the utility models or select frozen numeric settings; the guarded architecture responds to the earlier study’s failures and is tested on a new split.

## Reproduce

```bash
bash setup_local.sh
cd simulator
../.venv/bin/python run_research_study.py --workers 3 --output out/research-opportunity-study-new
cd ..
MPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_research_study.py --correction 198 --run simulator/out/research-opportunity-study-new --output revision/research-opportunity-results-new
```

Read ../research-opportunity-methods.md for exact semantics and assumptions. Open index.html locally for the eight-figure offline report, or research_opportunity_report.pdf.
