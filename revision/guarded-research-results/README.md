# Fresh actor-specific value gate: executed results

Completed **92,610 frozen-test episodes** and **463,050 convoy records**. The guarded study reuses the first study’s 3,600 fresh DQN/MAPPO training episodes and 700 causal-label-generation episodes; no additional actor or utility fitting is claimed. Value regressors fit episodes 0–79 of each 100-episode label study; 80–99 are internal held-out diagnostics. All nine declared cases and the original-topology transfer check are retained.

Across 81 primary delivery comparisons with a **198-test correction**, **7 supported superiority** and **0 supported a disadvantage**. These are actor/baseline/case-specific results on constructed physical scout/follower benchmarks, not general superiority.

The unconstrained learned version is retained in ../research-opportunity-results. It sometimes discarded useful warnings. This guarded version preserves fresh confident public-reachable hazard reports and requires two claimed clear sources before erasing a warning; learned utility filters the remaining reports. Actual model predictions and admission overrides are recorded separately. Its layouts, validation tapes and final test tapes are new. Final combined reporting accounts for 81 initial, 81 guarded and 36 cover-stress comparisons when correction=198. Claimed sources remain unauthenticated.

## Frozen settings

```json
{
  "status": "locked_before_test",
  "source_hash": "3fe6d2f8443a469956015b086990139a4c6b52315d83893357a75f4b1cd61852",
  "strength": 12.0,
  "gate": {
    "value_threshold": -1.0,
    "uncertainty_weight": 0.5
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
| planner | timely-misleading      | ALL        |             9.9 |    5.05251 |   15.2     | True                    | False                    |
| planner | timely-misleading      | FRC        |             9.9 |    5.5     |   15.3475  | True                    | False                    |
| planner | delayed-misleading     | ALL        |             3.5 |    1.3     |    6.44749 | True                    | False                    |
| planner | delayed-misleading     | FRC        |             3.4 |    1.15251 |    6.3     | True                    | False                    |
| planner | multiple-impersonation | ALL        |            20.1 |   14.105   |   26.0475  | True                    | False                    |
| planner | multiple-impersonation | FRC        |            20.1 |   14.405   |   26.2475  | True                    | False                    |
| planner | multiple-impersonation | SAFE-ALL   |             5.1 |    1.7     |    8.94749 | True                    | False                    |

## Supported adverse comparisons

None after correction; lack of detected disadvantage is not proof of noninferiority.

## All delivery results

| family            | algo    | case                   | method   |   episodes |   delivery_pct |   follower_delivery_pct |   utility |   censored |
|:------------------|:--------|:-----------------------|:---------|-----------:|---------------:|------------------------:|----------:|-----------:|
| constructed-forks | dqn     | delayed-misleading     | ALL      |        600 |        97.8    |                 96.3333 |  24.3452  |          0 |
| constructed-forks | dqn     | delayed-misleading     | FRC      |        600 |        97.8    |                 96.3333 |  24.3452  |          0 |
| constructed-forks | dqn     | delayed-misleading     | NC       |        600 |        57.9    |                 29.8333 |  -4.35247 |          0 |
| constructed-forks | dqn     | delayed-misleading     | SAFE-ALL |        600 |        97.7333 |                 96.2222 |  24.2934  |          0 |
| constructed-forks | dqn     | delayed-misleading     | VALUE    |        600 |        97.6667 |                 96.1111 |  24.2429  |          0 |
| constructed-forks | dqn     | late-warning           | ALL      |        600 |        55.5    |                 25.8333 |  -6.22006 |          0 |
| constructed-forks | dqn     | late-warning           | FRC      |        600 |        55.5    |                 25.8333 |  -6.22006 |          0 |
| constructed-forks | dqn     | late-warning           | NC       |        600 |        55.5    |                 25.8333 |  -6.22006 |          0 |
| constructed-forks | dqn     | late-warning           | SAFE-ALL |        600 |        55.5    |                 25.8333 |  -6.22006 |          0 |
| constructed-forks | dqn     | late-warning           | VALUE    |        600 |        55.5    |                 25.8333 |  -6.22006 |          0 |
| constructed-forks | dqn     | multiple-impersonation | ALL      |        600 |        95.8333 |                 93.0556 |  22.8006  |          0 |
| constructed-forks | dqn     | multiple-impersonation | FRC      |        600 |        95.8333 |                 93.0556 |  22.8006  |          0 |
| constructed-forks | dqn     | multiple-impersonation | NC       |        600 |        56.2333 |                 27.0556 |  -5.63508 |          0 |
| constructed-forks | dqn     | multiple-impersonation | SAFE-ALL |        600 |        97.4    |                 95.6667 |  23.8351  |          0 |
| constructed-forks | dqn     | multiple-impersonation | VALUE    |        600 |        97.2667 |                 95.4444 |  23.7283  |          0 |
| constructed-forks | dqn     | no-hazards             | ALL      |        600 |       100      |                100      |  26.4597  |          0 |
| constructed-forks | dqn     | no-hazards             | FRC      |        600 |       100      |                100      |  26.4597  |          0 |
| constructed-forks | dqn     | no-hazards             | NC       |        600 |       100      |                100      |  26.4874  |          0 |
| constructed-forks | dqn     | no-hazards             | SAFE-ALL |        600 |       100      |                100      |  26.4603  |          0 |
| constructed-forks | dqn     | no-hazards             | VALUE    |        600 |       100      |                100      |  26.4649  |          0 |
| constructed-forks | dqn     | redundant-sensing      | ALL      |        600 |       100      |                100      |  26.0108  |          0 |
| constructed-forks | dqn     | redundant-sensing      | FRC      |        600 |       100      |                100      |  26.0108  |          0 |
| constructed-forks | dqn     | redundant-sensing      | NC       |        600 |       100      |                100      |  26.0116  |          0 |
| constructed-forks | dqn     | redundant-sensing      | SAFE-ALL |        600 |       100      |                100      |  26.0108  |          0 |
| constructed-forks | dqn     | redundant-sensing      | VALUE    |        600 |       100      |                100      |  26.0108  |          0 |
| constructed-forks | dqn     | short-lived-honest     | ALL      |        600 |       100      |                100      |  26.3688  |          0 |
| constructed-forks | dqn     | short-lived-honest     | FRC      |        600 |       100      |                100      |  26.3688  |          0 |
| constructed-forks | dqn     | short-lived-honest     | NC       |        600 |       100      |                100      |  26.4814  |          0 |
| constructed-forks | dqn     | short-lived-honest     | SAFE-ALL |        600 |       100      |                100      |  26.3688  |          0 |
| constructed-forks | dqn     | short-lived-honest     | VALUE    |        600 |       100      |                100      |  26.3688  |          0 |
| constructed-forks | dqn     | short-lived-misleading | ALL      |        600 |       100      |                100      |  26.377   |          0 |
| constructed-forks | dqn     | short-lived-misleading | FRC      |        600 |       100      |                100      |  26.377   |          0 |
| constructed-forks | dqn     | short-lived-misleading | NC       |        600 |       100      |                100      |  26.4868  |          0 |
| constructed-forks | dqn     | short-lived-misleading | SAFE-ALL |        600 |       100      |                100      |  26.3749  |          0 |
| constructed-forks | dqn     | short-lived-misleading | VALUE    |        600 |       100      |                100      |  26.3675  |          0 |
| constructed-forks | dqn     | timely-honest          | ALL      |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | dqn     | timely-honest          | FRC      |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | dqn     | timely-honest          | NC       |        600 |        56.8    |                 28      |  -5.14487 |          0 |
| constructed-forks | dqn     | timely-honest          | SAFE-ALL |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | dqn     | timely-honest          | VALUE    |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | dqn     | timely-misleading      | ALL      |        600 |        98.4    |                 97.3333 |  24.7091  |          0 |
| constructed-forks | dqn     | timely-misleading      | FRC      |        600 |        98.4    |                 97.3333 |  24.7091  |          0 |
| constructed-forks | dqn     | timely-misleading      | NC       |        600 |        56.5333 |                 27.5556 |  -5.21927 |          0 |
| constructed-forks | dqn     | timely-misleading      | SAFE-ALL |        600 |        98.5333 |                 97.5556 |  24.7953  |          0 |
| constructed-forks | dqn     | timely-misleading      | VALUE    |        600 |        98.3    |                 97.1667 |  24.6211  |          0 |
| constructed-forks | mappo   | delayed-misleading     | ALL      |        600 |        97.3333 |                 95.5556 |  24.0191  |          0 |
| constructed-forks | mappo   | delayed-misleading     | FRC      |        600 |        97.3333 |                 95.5556 |  24.0191  |          0 |
| constructed-forks | mappo   | delayed-misleading     | NC       |        600 |        57.8667 |                 29.7778 |  -4.35627 |          0 |
| constructed-forks | mappo   | delayed-misleading     | SAFE-ALL |        600 |        97.3667 |                 95.6111 |  24.0366  |          0 |
| constructed-forks | mappo   | delayed-misleading     | VALUE    |        600 |        97.3333 |                 95.5556 |  24.0124  |          0 |
| constructed-forks | mappo   | late-warning           | ALL      |        600 |        55.4667 |                 25.7778 |  -6.22942 |          0 |
| constructed-forks | mappo   | late-warning           | FRC      |        600 |        55.4667 |                 25.7778 |  -6.22942 |          0 |
| constructed-forks | mappo   | late-warning           | NC       |        600 |        55.4667 |                 25.7778 |  -6.22942 |          0 |
| constructed-forks | mappo   | late-warning           | SAFE-ALL |        600 |        55.4667 |                 25.7778 |  -6.22942 |          0 |
| constructed-forks | mappo   | late-warning           | VALUE    |        600 |        55.4667 |                 25.7778 |  -6.22942 |          0 |
| constructed-forks | mappo   | multiple-impersonation | ALL      |        600 |        94.9333 |                 91.5556 |  22.2431  |          0 |
| constructed-forks | mappo   | multiple-impersonation | FRC      |        600 |        94.9333 |                 91.5556 |  22.2431  |          0 |
| constructed-forks | mappo   | multiple-impersonation | NC       |        600 |        56.5    |                 27.5    |  -5.38893 |          0 |
| constructed-forks | mappo   | multiple-impersonation | SAFE-ALL |        600 |        96.6667 |                 94.4444 |  23.4963  |          0 |
| constructed-forks | mappo   | multiple-impersonation | VALUE    |        600 |        96.7667 |                 94.6111 |  23.568   |          0 |
| constructed-forks | mappo   | no-hazards             | ALL      |        600 |       100      |                100      |  26.4562  |          0 |
| constructed-forks | mappo   | no-hazards             | FRC      |        600 |       100      |                100      |  26.4562  |          0 |
| constructed-forks | mappo   | no-hazards             | NC       |        600 |       100      |                100      |  26.4918  |          0 |
| constructed-forks | mappo   | no-hazards             | SAFE-ALL |        600 |       100      |                100      |  26.4568  |          0 |
| constructed-forks | mappo   | no-hazards             | VALUE    |        600 |       100      |                100      |  26.4663  |          0 |
| constructed-forks | mappo   | redundant-sensing      | ALL      |        600 |        98.8    |                 98      |  25.1122  |          0 |
| constructed-forks | mappo   | redundant-sensing      | FRC      |        600 |        98.8    |                 98      |  25.1122  |          0 |
| constructed-forks | mappo   | redundant-sensing      | NC       |        600 |       100      |                100      |  26.0116  |          0 |
| constructed-forks | mappo   | redundant-sensing      | SAFE-ALL |        600 |        98.8    |                 98      |  25.1122  |          0 |
| constructed-forks | mappo   | redundant-sensing      | VALUE    |        600 |        98.8    |                 98      |  25.1122  |          0 |
| constructed-forks | mappo   | short-lived-honest     | ALL      |        600 |       100      |                100      |  26.3696  |          0 |
| constructed-forks | mappo   | short-lived-honest     | FRC      |        600 |       100      |                100      |  26.3696  |          0 |
| constructed-forks | mappo   | short-lived-honest     | NC       |        600 |       100      |                100      |  26.4841  |          0 |
| constructed-forks | mappo   | short-lived-honest     | SAFE-ALL |        600 |       100      |                100      |  26.3696  |          0 |
| constructed-forks | mappo   | short-lived-honest     | VALUE    |        600 |       100      |                100      |  26.3696  |          0 |
| constructed-forks | mappo   | short-lived-misleading | ALL      |        600 |       100      |                100      |  26.3776  |          0 |
| constructed-forks | mappo   | short-lived-misleading | FRC      |        600 |       100      |                100      |  26.3776  |          0 |
| constructed-forks | mappo   | short-lived-misleading | NC       |        600 |       100      |                100      |  26.4903  |          0 |
| constructed-forks | mappo   | short-lived-misleading | SAFE-ALL |        600 |       100      |                100      |  26.3756  |          0 |
| constructed-forks | mappo   | short-lived-misleading | VALUE    |        600 |       100      |                100      |  26.3758  |          0 |
| constructed-forks | mappo   | timely-honest          | ALL      |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | mappo   | timely-honest          | FRC      |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | mappo   | timely-honest          | NC       |        600 |        57.1667 |                 28.6111 |  -4.89779 |          0 |
| constructed-forks | mappo   | timely-honest          | SAFE-ALL |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | mappo   | timely-honest          | VALUE    |        600 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | mappo   | timely-misleading      | ALL      |        600 |        98.2    |                 97      |  24.6565  |          0 |
| constructed-forks | mappo   | timely-misleading      | FRC      |        600 |        98.2    |                 97      |  24.6565  |          0 |
| constructed-forks | mappo   | timely-misleading      | NC       |        600 |        57.4    |                 29      |  -4.59057 |          0 |
| constructed-forks | mappo   | timely-misleading      | SAFE-ALL |        600 |        98.5    |                 97.5    |  24.8731  |          0 |
| constructed-forks | mappo   | timely-misleading      | VALUE    |        600 |        98.2667 |                 97.1111 |  24.7019  |          0 |
| constructed-forks | planner | delayed-misleading     | ALL      |        200 |        94.3    |                 90.5    |  21.7619  |          0 |
| constructed-forks | planner | delayed-misleading     | FRC      |        200 |        94.4    |                 90.6667 |  21.8414  |          0 |
| constructed-forks | planner | delayed-misleading     | NC       |        200 |        57.6    |                 29.3333 |  -4.57226 |          0 |
| constructed-forks | planner | delayed-misleading     | SAFE-ALL |        200 |        97.8    |                 96.3333 |  24.3224  |          0 |
| constructed-forks | planner | delayed-misleading     | VALUE    |        200 |        97.8    |                 96.3333 |  24.3224  |          0 |
| constructed-forks | planner | late-warning           | ALL      |        200 |        55.5    |                 25.8333 |  -6.1846  |          0 |
| constructed-forks | planner | late-warning           | FRC      |        200 |        55.5    |                 25.8333 |  -6.1846  |          0 |
| constructed-forks | planner | late-warning           | NC       |        200 |        55.5    |                 25.8333 |  -6.1846  |          0 |
| constructed-forks | planner | late-warning           | SAFE-ALL |        200 |        55.5    |                 25.8333 |  -6.1846  |          0 |
| constructed-forks | planner | late-warning           | VALUE    |        200 |        55.5    |                 25.8333 |  -6.1846  |          0 |
| constructed-forks | planner | multiple-impersonation | ALL      |        200 |        75      |                 58.3333 |   7.5804  |          0 |
| constructed-forks | planner | multiple-impersonation | FRC      |        200 |        75      |                 58.3333 |   7.5804  |          0 |
| constructed-forks | planner | multiple-impersonation | NC       |        200 |        55.6    |                 26      |  -6.06941 |          0 |
| constructed-forks | planner | multiple-impersonation | SAFE-ALL |        200 |        90      |                 83.3333 |  18.2438  |          0 |
| constructed-forks | planner | multiple-impersonation | VALUE    |        200 |        95.1    |                 91.8333 |  21.9509  |          0 |
| constructed-forks | planner | no-hazards             | ALL      |        200 |       100      |                100      |  26.4778  |          0 |
| constructed-forks | planner | no-hazards             | FRC      |        200 |       100      |                100      |  26.4778  |          0 |
| constructed-forks | planner | no-hazards             | NC       |        200 |       100      |                100      |  26.5082  |          0 |
| constructed-forks | planner | no-hazards             | SAFE-ALL |        200 |       100      |                100      |  26.4769  |          0 |
| constructed-forks | planner | no-hazards             | VALUE    |        200 |       100      |                100      |  26.4769  |          0 |
| constructed-forks | planner | redundant-sensing      | ALL      |        200 |       100      |                100      |  25.9493  |          0 |
| constructed-forks | planner | redundant-sensing      | FRC      |        200 |       100      |                100      |  25.9493  |          0 |
| constructed-forks | planner | redundant-sensing      | NC       |        200 |       100      |                100      |  26.0116  |          0 |
| constructed-forks | planner | redundant-sensing      | SAFE-ALL |        200 |       100      |                100      |  25.9493  |          0 |
| constructed-forks | planner | redundant-sensing      | VALUE    |        200 |       100      |                100      |  25.9493  |          0 |
| constructed-forks | planner | short-lived-honest     | ALL      |        200 |       100      |                100      |  26.4954  |          0 |
| constructed-forks | planner | short-lived-honest     | FRC      |        200 |       100      |                100      |  26.4954  |          0 |
| constructed-forks | planner | short-lived-honest     | NC       |        200 |       100      |                100      |  26.5018  |          0 |
| constructed-forks | planner | short-lived-honest     | SAFE-ALL |        200 |       100      |                100      |  26.4831  |          0 |
| constructed-forks | planner | short-lived-honest     | VALUE    |        200 |       100      |                100      |  26.3848  |          0 |
| constructed-forks | planner | short-lived-misleading | ALL      |        200 |       100      |                100      |  26.4841  |          0 |
| constructed-forks | planner | short-lived-misleading | FRC      |        200 |       100      |                100      |  26.4841  |          0 |
| constructed-forks | planner | short-lived-misleading | NC       |        200 |       100      |                100      |  26.5069  |          0 |
| constructed-forks | planner | short-lived-misleading | SAFE-ALL |        200 |       100      |                100      |  26.4705  |          0 |
| constructed-forks | planner | short-lived-misleading | VALUE    |        200 |       100      |                100      |  26.3597  |          0 |
| constructed-forks | planner | timely-honest          | ALL      |        200 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | planner | timely-honest          | FRC      |        200 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | planner | timely-honest          | NC       |        200 |        57      |                 28.3333 |  -5.02189 |          0 |
| constructed-forks | planner | timely-honest          | SAFE-ALL |        200 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | planner | timely-honest          | VALUE    |        200 |       100      |                100      |  26.0041  |          0 |
| constructed-forks | planner | timely-misleading      | ALL      |        200 |        87.4    |                 79      |  16.6562  |          0 |
| constructed-forks | planner | timely-misleading      | FRC      |        200 |        87.4    |                 79      |  16.6562  |          0 |
| constructed-forks | planner | timely-misleading      | NC       |        200 |        57.1    |                 28.5    |  -4.78062 |          0 |
| constructed-forks | planner | timely-misleading      | SAFE-ALL |        200 |        96.8    |                 94.6667 |  23.451   |          0 |
| constructed-forks | planner | timely-misleading      | VALUE    |        200 |        97.3    |                 95.5    |  23.8184  |          0 |
| original-topology | dqn     | delayed-misleading     | ALL      |         30 |        88      |                 86.6667 |  16.6233  |          0 |
| original-topology | dqn     | delayed-misleading     | FRC      |         30 |        88      |                 86.6667 |  16.6233  |          0 |
| original-topology | dqn     | delayed-misleading     | NC       |         30 |        87.3333 |                 85.5556 |  16.2082  |          0 |
| original-topology | dqn     | delayed-misleading     | SAFE-ALL |         30 |        88      |                 86.6667 |  16.6233  |          0 |
| original-topology | dqn     | delayed-misleading     | VALUE    |         30 |        88      |                 86.6667 |  16.6233  |          0 |
| original-topology | dqn     | late-warning           | ALL      |         30 |        99.3333 |                 98.8889 |  25.1089  |          0 |
| original-topology | dqn     | late-warning           | FRC      |         30 |        99.3333 |                 98.8889 |  25.1089  |          0 |
| original-topology | dqn     | late-warning           | NC       |         30 |        99.3333 |                 98.8889 |  25.1089  |          0 |
| original-topology | dqn     | late-warning           | SAFE-ALL |         30 |        99.3333 |                 98.8889 |  25.1089  |          0 |
| original-topology | dqn     | late-warning           | VALUE    |         30 |        99.3333 |                 98.8889 |  25.1089  |          0 |
| original-topology | dqn     | multiple-impersonation | ALL      |         30 |        91.3333 |                 91.1111 |  19.804   |          0 |
| original-topology | dqn     | multiple-impersonation | FRC      |         30 |        91.3333 |                 91.1111 |  19.804   |          0 |
| original-topology | dqn     | multiple-impersonation | NC       |         30 |        92      |                 92.2222 |  20.3622  |          0 |
| original-topology | dqn     | multiple-impersonation | SAFE-ALL |         30 |        91.3333 |                 91.1111 |  19.804   |          0 |
| original-topology | dqn     | multiple-impersonation | VALUE    |         30 |        91.3333 |                 91.1111 |  19.7981  |          0 |
| original-topology | dqn     | no-hazards             | ALL      |         30 |       100      |                100      |  25.9964  |          0 |
| original-topology | dqn     | no-hazards             | FRC      |         30 |       100      |                100      |  25.9964  |          0 |
| original-topology | dqn     | no-hazards             | NC       |         30 |       100      |                100      |  25.9949  |          0 |
| original-topology | dqn     | no-hazards             | SAFE-ALL |         30 |       100      |                100      |  25.9964  |          0 |
| original-topology | dqn     | no-hazards             | VALUE    |         30 |       100      |                100      |  25.9968  |          0 |
| original-topology | dqn     | redundant-sensing      | ALL      |         30 |        92.6667 |                 93.3333 |  20.0901  |          0 |
| original-topology | dqn     | redundant-sensing      | FRC      |         30 |        92.6667 |                 93.3333 |  20.0901  |          0 |
| original-topology | dqn     | redundant-sensing      | NC       |         30 |        92.6667 |                 93.3333 |  20.0759  |          0 |
| original-topology | dqn     | redundant-sensing      | SAFE-ALL |         30 |        92.6667 |                 93.3333 |  20.0901  |          0 |
| original-topology | dqn     | redundant-sensing      | VALUE    |         30 |        92.6667 |                 93.3333 |  20.0901  |          0 |
| original-topology | dqn     | short-lived-honest     | ALL      |         30 |        86      |                 87.7778 |  15.0097  |          0 |
| original-topology | dqn     | short-lived-honest     | FRC      |         30 |        86      |                 87.7778 |  15.0097  |          0 |
| original-topology | dqn     | short-lived-honest     | NC       |         30 |        86      |                 87.7778 |  15.0319  |          0 |
| original-topology | dqn     | short-lived-honest     | SAFE-ALL |         30 |        86      |                 87.7778 |  15.0097  |          0 |
| original-topology | dqn     | short-lived-honest     | VALUE    |         30 |        86      |                 87.7778 |  15.0097  |          0 |
| original-topology | dqn     | short-lived-misleading | ALL      |         30 |        89.3333 |                 90      |  17.5066  |          0 |
| original-topology | dqn     | short-lived-misleading | FRC      |         30 |        89.3333 |                 90      |  17.5066  |          0 |
| original-topology | dqn     | short-lived-misleading | NC       |         30 |        89.3333 |                 90      |  17.5431  |          0 |
| original-topology | dqn     | short-lived-misleading | SAFE-ALL |         30 |        89.3333 |                 90      |  17.5066  |          0 |
| original-topology | dqn     | short-lived-misleading | VALUE    |         30 |        89.3333 |                 90      |  17.5206  |          0 |
| original-topology | dqn     | timely-honest          | ALL      |         30 |        91.3333 |                 93.3333 |  19.1603  |          0 |
| original-topology | dqn     | timely-honest          | FRC      |         30 |        91.3333 |                 93.3333 |  19.1603  |          0 |
| original-topology | dqn     | timely-honest          | NC       |         30 |        88      |                 87.7778 |  16.7062  |          0 |
| original-topology | dqn     | timely-honest          | SAFE-ALL |         30 |        91.3333 |                 93.3333 |  19.1603  |          0 |
| original-topology | dqn     | timely-honest          | VALUE    |         30 |        91.3333 |                 93.3333 |  19.1603  |          0 |
| original-topology | dqn     | timely-misleading      | ALL      |         30 |        84      |                 85.5556 |  13.8655  |          0 |
| original-topology | dqn     | timely-misleading      | FRC      |         30 |        84      |                 85.5556 |  13.8655  |          0 |
| original-topology | dqn     | timely-misleading      | NC       |         30 |        82.6667 |                 83.3333 |  12.9769  |          0 |
| original-topology | dqn     | timely-misleading      | SAFE-ALL |         30 |        84      |                 85.5556 |  13.8655  |          0 |
| original-topology | dqn     | timely-misleading      | VALUE    |         30 |        82.6667 |                 83.3333 |  12.9951  |          0 |
| original-topology | mappo   | delayed-misleading     | ALL      |         30 |        66.6667 |                 61.1111 | -10.8287  |          0 |
| original-topology | mappo   | delayed-misleading     | FRC      |         30 |        66.6667 |                 61.1111 | -10.8287  |          0 |
| original-topology | mappo   | delayed-misleading     | NC       |         30 |        68.6667 |                 65.5556 |  -9.4041  |          0 |
| original-topology | mappo   | delayed-misleading     | SAFE-ALL |         30 |        66.6667 |                 61.1111 | -10.8287  |          0 |
| original-topology | mappo   | delayed-misleading     | VALUE    |         30 |        66      |                 60      | -13.4992  |          0 |
| original-topology | mappo   | late-warning           | ALL      |         30 |        84      |                 76.6667 |   8.78796 |          3 |
| original-topology | mappo   | late-warning           | FRC      |         30 |        84      |                 76.6667 |   8.78796 |          3 |
| original-topology | mappo   | late-warning           | NC       |         30 |        84      |                 76.6667 |   8.78796 |          3 |
| original-topology | mappo   | late-warning           | SAFE-ALL |         30 |        84      |                 76.6667 |   8.78796 |          3 |
| original-topology | mappo   | late-warning           | VALUE    |         30 |        84      |                 76.6667 |   8.78796 |          3 |
| original-topology | mappo   | multiple-impersonation | ALL      |         30 |        84.6667 |                 84.4444 |  10.9101  |          2 |
| original-topology | mappo   | multiple-impersonation | FRC      |         30 |        84.6667 |                 84.4444 |  10.9101  |          2 |
| original-topology | mappo   | multiple-impersonation | NC       |         30 |        82.6667 |                 81.1111 |   5.36863 |          6 |
| original-topology | mappo   | multiple-impersonation | SAFE-ALL |         30 |        84.6667 |                 84.4444 |  10.9101  |          2 |
| original-topology | mappo   | multiple-impersonation | VALUE    |         30 |        84.6667 |                 84.4444 |  10.9783  |          2 |
| original-topology | mappo   | no-hazards             | ALL      |         30 |        90      |                 83.3333 |  -7.60563 |         15 |
| original-topology | mappo   | no-hazards             | FRC      |         30 |        90      |                 83.3333 |  -7.60563 |         15 |
| original-topology | mappo   | no-hazards             | NC       |         30 |        80      |                 66.6667 | -26.5106  |         30 |
| original-topology | mappo   | no-hazards             | SAFE-ALL |         30 |        90      |                 83.3333 |  -7.60563 |         15 |
| original-topology | mappo   | no-hazards             | VALUE    |         30 |        85.3333 |                 75.5556 | -16.5163  |         22 |
| original-topology | mappo   | redundant-sensing      | ALL      |         30 |        88      |                 86.6667 |  17.294   |          0 |
| original-topology | mappo   | redundant-sensing      | FRC      |         30 |        88      |                 86.6667 |  17.294   |          0 |
| original-topology | mappo   | redundant-sensing      | NC       |         30 |        88      |                 86.6667 |  17.1528  |          0 |
| original-topology | mappo   | redundant-sensing      | SAFE-ALL |         30 |        88      |                 86.6667 |  17.294   |          0 |
| original-topology | mappo   | redundant-sensing      | VALUE    |         30 |        88      |                 86.6667 |  17.294   |          0 |
| original-topology | mappo   | short-lived-honest     | ALL      |         30 |        81.3333 |                 72.2222 |   2.47039 |          6 |
| original-topology | mappo   | short-lived-honest     | FRC      |         30 |        81.3333 |                 72.2222 |   2.47039 |          6 |
| original-topology | mappo   | short-lived-honest     | NC       |         30 |        83.3333 |                 75.5556 |   7.69698 |          3 |
| original-topology | mappo   | short-lived-honest     | SAFE-ALL |         30 |        81.3333 |                 72.2222 |   2.47039 |          6 |
| original-topology | mappo   | short-lived-honest     | VALUE    |         30 |        81.3333 |                 72.2222 |   2.47039 |          6 |
| original-topology | mappo   | short-lived-misleading | ALL      |         30 |        82.6667 |                 77.7778 |  -5.04021 |          7 |
| original-topology | mappo   | short-lived-misleading | FRC      |         30 |        82.6667 |                 77.7778 |  -5.04021 |          7 |
| original-topology | mappo   | short-lived-misleading | NC       |         30 |        80.6667 |                 74.4444 |  -7.12798 |         10 |
| original-topology | mappo   | short-lived-misleading | SAFE-ALL |         30 |        82.6667 |                 77.7778 |  -5.04021 |          7 |
| original-topology | mappo   | short-lived-misleading | VALUE    |         30 |        82.6667 |                 77.7778 |  -5.04021 |          7 |
| original-topology | mappo   | timely-honest          | ALL      |         30 |        72.6667 |                 64.4444 | -10.9976  |          5 |
| original-topology | mappo   | timely-honest          | FRC      |         30 |        72.6667 |                 64.4444 | -10.9976  |          5 |
| original-topology | mappo   | timely-honest          | NC       |         30 |        71.3333 |                 62.2222 | -13.0677  |          6 |
| original-topology | mappo   | timely-honest          | SAFE-ALL |         30 |        72.6667 |                 64.4444 | -10.9976  |          5 |
| original-topology | mappo   | timely-honest          | VALUE    |         30 |        72.6667 |                 64.4444 | -10.9976  |          5 |
| original-topology | mappo   | timely-misleading      | ALL      |         30 |        72.6667 |                 61.1111 | -19.3612  |         12 |
| original-topology | mappo   | timely-misleading      | FRC      |         30 |        72.6667 |                 61.1111 | -19.3612  |         12 |
| original-topology | mappo   | timely-misleading      | NC       |         30 |        69.3333 |                 55.5556 | -24.878   |         12 |
| original-topology | mappo   | timely-misleading      | SAFE-ALL |         30 |        72.6667 |                 61.1111 | -19.3612  |         12 |
| original-topology | mappo   | timely-misleading      | VALUE    |         30 |        71.3333 |                 58.8889 | -20.4043  |         12 |
| original-topology | planner | delayed-misleading     | ALL      |         10 |        92      |                 93.3333 |  19.068   |          0 |
| original-topology | planner | delayed-misleading     | FRC      |         10 |        92      |                 93.3333 |  19.068   |          0 |
| original-topology | planner | delayed-misleading     | NC       |         10 |        92      |                 93.3333 |  19.068   |          0 |
| original-topology | planner | delayed-misleading     | SAFE-ALL |         10 |        92      |                 93.3333 |  19.068   |          0 |
| original-topology | planner | delayed-misleading     | VALUE    |         10 |        92      |                 93.3333 |  19.068   |          0 |
| original-topology | planner | late-warning           | ALL      |         10 |        92      |                 93.3333 |  18.6631  |          0 |
| original-topology | planner | late-warning           | FRC      |         10 |        92      |                 93.3333 |  18.6631  |          0 |
| original-topology | planner | late-warning           | NC       |         10 |        92      |                 93.3333 |  18.6631  |          0 |
| original-topology | planner | late-warning           | SAFE-ALL |         10 |        92      |                 93.3333 |  18.6631  |          0 |
| original-topology | planner | late-warning           | VALUE    |         10 |        92      |                 93.3333 |  18.6631  |          0 |
| original-topology | planner | multiple-impersonation | ALL      |         10 |        92      |                 93.3333 |  20.3555  |          0 |
| original-topology | planner | multiple-impersonation | FRC      |         10 |        92      |                 93.3333 |  20.3555  |          0 |
| original-topology | planner | multiple-impersonation | NC       |         10 |        92      |                 93.3333 |  20.3555  |          0 |
| original-topology | planner | multiple-impersonation | SAFE-ALL |         10 |        92      |                 93.3333 |  20.3555  |          0 |
| original-topology | planner | multiple-impersonation | VALUE    |         10 |        92      |                 93.3333 |  20.3555  |          0 |
| original-topology | planner | no-hazards             | ALL      |         10 |       100      |                100      |  26.0264  |          0 |
| original-topology | planner | no-hazards             | FRC      |         10 |       100      |                100      |  26.0264  |          0 |
| original-topology | planner | no-hazards             | NC       |         10 |       100      |                100      |  26.0264  |          0 |
| original-topology | planner | no-hazards             | SAFE-ALL |         10 |       100      |                100      |  26.0264  |          0 |
| original-topology | planner | no-hazards             | VALUE    |         10 |       100      |                100      |  26.0264  |          0 |
| original-topology | planner | redundant-sensing      | ALL      |         10 |        90      |                 90      |  17.5447  |          0 |
| original-topology | planner | redundant-sensing      | FRC      |         10 |        90      |                 90      |  17.5447  |          0 |
| original-topology | planner | redundant-sensing      | NC       |         10 |        90      |                 90      |  17.5649  |          0 |
| original-topology | planner | redundant-sensing      | SAFE-ALL |         10 |        90      |                 90      |  17.5447  |          0 |
| original-topology | planner | redundant-sensing      | VALUE    |         10 |        90      |                 90      |  17.5447  |          0 |
| original-topology | planner | short-lived-honest     | ALL      |         10 |        96      |                 93.3333 |  22.0283  |          0 |
| original-topology | planner | short-lived-honest     | FRC      |         10 |        96      |                 93.3333 |  22.0283  |          0 |
| original-topology | planner | short-lived-honest     | NC       |         10 |        94      |                 90      |  20.303   |          0 |
| original-topology | planner | short-lived-honest     | SAFE-ALL |         10 |        96      |                 93.3333 |  22.0283  |          0 |
| original-topology | planner | short-lived-honest     | VALUE    |         10 |        96      |                 93.3333 |  22.0283  |          0 |
| original-topology | planner | short-lived-misleading | ALL      |         10 |       100      |                100      |  25.4458  |          0 |
| original-topology | planner | short-lived-misleading | FRC      |         10 |       100      |                100      |  25.4458  |          0 |
| original-topology | planner | short-lived-misleading | NC       |         10 |       100      |                100      |  25.5701  |          0 |
| original-topology | planner | short-lived-misleading | SAFE-ALL |         10 |       100      |                100      |  25.4458  |          0 |
| original-topology | planner | short-lived-misleading | VALUE    |         10 |       100      |                100      |  25.4458  |          0 |
| original-topology | planner | timely-honest          | ALL      |         10 |        96      |                 93.3333 |  22.902   |          0 |
| original-topology | planner | timely-honest          | FRC      |         10 |        96      |                 93.3333 |  22.902   |          0 |
| original-topology | planner | timely-honest          | NC       |         10 |        96      |                 93.3333 |  22.902   |          0 |
| original-topology | planner | timely-honest          | SAFE-ALL |         10 |        96      |                 93.3333 |  22.902   |          0 |
| original-topology | planner | timely-honest          | VALUE    |         10 |        96      |                 93.3333 |  22.902   |          0 |
| original-topology | planner | timely-misleading      | ALL      |         10 |       100      |                100      |  25.2993  |          0 |
| original-topology | planner | timely-misleading      | FRC      |         10 |       100      |                100      |  25.2993  |          0 |
| original-topology | planner | timely-misleading      | NC       |         10 |       100      |                100      |  25.2993  |          0 |
| original-topology | planner | timely-misleading      | SAFE-ALL |         10 |       100      |                100      |  25.2993  |          0 |
| original-topology | planner | timely-misleading      | VALUE    |         10 |       100      |                100      |  25.2993  |          0 |

## All corrected comparisons

| algo    | case                   | baseline   |   difference_pp |   lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:--------|:-----------------------|:-----------|----------------:|-----------:|-----------:|:------------------------|:-------------------------|
| planner | timely-honest          | ALL        |       0         |   0        |   0        | False                   | False                    |
| planner | timely-honest          | FRC        |       0         |   0        |   0        | False                   | False                    |
| planner | timely-honest          | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| planner | timely-misleading      | ALL        |       9.9       |   5.05251  |  15.2      | True                    | False                    |
| planner | timely-misleading      | FRC        |       9.9       |   5.5      |  15.3475   | True                    | False                    |
| planner | timely-misleading      | SAFE-ALL   |       0.5       |   0        |   2.2      | False                   | False                    |
| planner | delayed-misleading     | ALL        |       3.5       |   1.3      |   6.44749  | True                    | False                    |
| planner | delayed-misleading     | FRC        |       3.4       |   1.15251  |   6.3      | True                    | False                    |
| planner | delayed-misleading     | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| planner | late-warning           | ALL        |       0         |   0        |   0        | False                   | False                    |
| planner | late-warning           | FRC        |       0         |   0        |   0        | False                   | False                    |
| planner | late-warning           | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| planner | redundant-sensing      | ALL        |       0         |   0        |   0        | False                   | False                    |
| planner | redundant-sensing      | FRC        |       0         |   0        |   0        | False                   | False                    |
| planner | redundant-sensing      | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| planner | short-lived-honest     | ALL        |       0         |   0        |   0        | False                   | False                    |
| planner | short-lived-honest     | FRC        |       0         |   0        |   0        | False                   | False                    |
| planner | short-lived-honest     | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| planner | short-lived-misleading | ALL        |       0         |   0        |   0        | False                   | False                    |
| planner | short-lived-misleading | FRC        |       0         |   0        |   0        | False                   | False                    |
| planner | short-lived-misleading | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| planner | multiple-impersonation | ALL        |      20.1       |  14.105    |  26.0475   | True                    | False                    |
| planner | multiple-impersonation | FRC        |      20.1       |  14.405    |  26.2475   | True                    | False                    |
| planner | multiple-impersonation | SAFE-ALL   |       5.1       |   1.7      |   8.94749  | True                    | False                    |
| planner | no-hazards             | ALL        |       0         |   0        |   0        | False                   | False                    |
| planner | no-hazards             | FRC        |       0         |   0        |   0        | False                   | False                    |
| planner | no-hazards             | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| dqn     | timely-honest          | ALL        |       0         |   0        |   0        | False                   | False                    |
| dqn     | timely-honest          | FRC        |       0         |   0        |   0        | False                   | False                    |
| dqn     | timely-honest          | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| dqn     | timely-misleading      | ALL        |      -0.1       |  -1.36667  |   1.36499  | False                   | False                    |
| dqn     | timely-misleading      | FRC        |      -0.1       |  -1.4      |   1.54246  | False                   | False                    |
| dqn     | timely-misleading      | SAFE-ALL   |      -0.233333  |  -1.23166  |   0        | False                   | False                    |
| dqn     | delayed-misleading     | ALL        |      -0.133333  |  -1.5      |   0        | False                   | False                    |
| dqn     | delayed-misleading     | FRC        |      -0.133333  |  -1.4      |   0        | False                   | False                    |
| dqn     | delayed-misleading     | SAFE-ALL   |      -0.0666667 |  -0.8      |   0        | False                   | False                    |
| dqn     | late-warning           | ALL        |       0         |   0        |   0        | False                   | False                    |
| dqn     | late-warning           | FRC        |       0         |   0        |   0        | False                   | False                    |
| dqn     | late-warning           | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| dqn     | redundant-sensing      | ALL        |       0         |   0        |   0        | False                   | False                    |
| dqn     | redundant-sensing      | FRC        |       0         |   0        |   0        | False                   | False                    |
| dqn     | redundant-sensing      | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| dqn     | short-lived-honest     | ALL        |       0         |   0        |   0        | False                   | False                    |
| dqn     | short-lived-honest     | FRC        |       0         |   0        |   0        | False                   | False                    |
| dqn     | short-lived-honest     | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| dqn     | short-lived-misleading | ALL        |       0         |   0        |   0        | False                   | False                    |
| dqn     | short-lived-misleading | FRC        |       0         |   0        |   0        | False                   | False                    |
| dqn     | short-lived-misleading | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| dqn     | multiple-impersonation | ALL        |       1.43333   |  -0.849162 |   4.36499  | False                   | False                    |
| dqn     | multiple-impersonation | FRC        |       1.43333   |  -0.847487 |   4.3108   | False                   | False                    |
| dqn     | multiple-impersonation | SAFE-ALL   |      -0.133333  |  -1.6      |   0.6      | False                   | False                    |
| dqn     | no-hazards             | ALL        |       0         |   0        |   0        | False                   | False                    |
| dqn     | no-hazards             | FRC        |       0         |   0        |   0        | False                   | False                    |
| dqn     | no-hazards             | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| mappo   | timely-honest          | ALL        |       0         |   0        |   0        | False                   | False                    |
| mappo   | timely-honest          | FRC        |       0         |   0        |   0        | False                   | False                    |
| mappo   | timely-honest          | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| mappo   | timely-misleading      | ALL        |       0.0666667 |  -1.2      |   1.79665  | False                   | False                    |
| mappo   | timely-misleading      | FRC        |       0.0666667 |  -1.2825   |   1.81583  | False                   | False                    |
| mappo   | timely-misleading      | SAFE-ALL   |      -0.233333  |  -1.6      |   0        | False                   | False                    |
| mappo   | delayed-misleading     | ALL        |       0         |  -1.2      |   0.847487 | False                   | False                    |
| mappo   | delayed-misleading     | FRC        |       0         |  -1        |   0.8      | False                   | False                    |
| mappo   | delayed-misleading     | SAFE-ALL   |      -0.0333333 |  -0.7      |   0        | False                   | False                    |
| mappo   | late-warning           | ALL        |       0         |   0        |   0        | False                   | False                    |
| mappo   | late-warning           | FRC        |       0         |   0        |   0        | False                   | False                    |
| mappo   | late-warning           | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| mappo   | redundant-sensing      | ALL        |       0         |   0        |   0        | False                   | False                    |
| mappo   | redundant-sensing      | FRC        |       0         |   0        |   0        | False                   | False                    |
| mappo   | redundant-sensing      | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| mappo   | short-lived-honest     | ALL        |       0         |   0        |   0        | False                   | False                    |
| mappo   | short-lived-honest     | FRC        |       0         |   0        |   0        | False                   | False                    |
| mappo   | short-lived-honest     | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| mappo   | short-lived-misleading | ALL        |       0         |   0        |   0        | False                   | False                    |
| mappo   | short-lived-misleading | FRC        |       0         |   0        |   0        | False                   | False                    |
| mappo   | short-lived-misleading | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |
| mappo   | multiple-impersonation | ALL        |       1.83333   |  -0.147487 |   4.54749  | False                   | False                    |
| mappo   | multiple-impersonation | FRC        |       1.83333   |  -0.2      |   4.56499  | False                   | False                    |
| mappo   | multiple-impersonation | SAFE-ALL   |       0.1       |   0        |   1.2      | False                   | False                    |
| mappo   | no-hazards             | ALL        |       0         |   0        |   0        | False                   | False                    |
| mappo   | no-hazards             | FRC        |       0         |   0        |   0        | False                   | False                    |
| mappo   | no-hazards             | SAFE-ALL   |       0         |   0        |   0        | False                   | False                    |

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

After the first run, generate the guarded study and report:

```bash
cd simulator
../.venv/bin/python run_guarded_research_study.py --parent out/research-opportunity-study-new --output out/guarded-research-study-new --workers 3
cd ..
MPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_research_study.py --guarded --correction 198 --run simulator/out/guarded-research-study-new --output revision/guarded-research-results-new
```
