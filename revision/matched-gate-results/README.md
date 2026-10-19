# Matched-training gate study

Completed 81,920 final method-evaluation episodes (409,600 convoy records), 10,240 fixed-actor diagnostic episodes, 64 adapted checkpoints and eight independent paired training seeds per algorithm. **Primary learned-addition superiority supported for: neither algorithm.**

## Primary question: does learned filtering add benefit beyond safeguards?

| algo   | scope   | case               | baseline   |   difference_pp |   lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:-------|:--------|:-------------------|:-----------|----------------:|-----------:|-----------:|:------------------------|:-------------------------|
| dqn    | primary | equal-case-average | SAFE       |        0.259766 |  -0.427105 |    1.11492 | False                   | False                    |
| mappo  | primary | equal-case-average | SAFE       |       -0.294922 |  -3.73545  |    3.63836 | False                   | False                    |

Positive numerical differences without a positive corrected lower bound are inconclusive. Each new interval uses a conservative 248-test threshold (50 new plus 198 prior comparisons). Earlier published intervals are preserved rather than recomputed here; this is not a claim of revised joint coverage for all historical results. Secondary case wins do not replace the pooled primary endpoint. Eight paired seeds are the training replication, not the number of convoy records.

## All conditions

| algo   | case                | method   |   episodes |   delivery_pct |   follower_delivery_pct |   utility |   elapsed_delivered |
|:-------|:--------------------|:---------|-----------:|---------------:|------------------------:|----------:|--------------------:|
| dqn    | late-control        | ALL      |       1280 |        52.6563 |                 21.0938 | -11.908   |             19.2416 |
| dqn    | late-control        | COMBINED |       1280 |        52.2812 |                 20.4688 | -12.1831  |             19.2412 |
| dqn    | late-control        | SAFE     |       1280 |        52.1719 |                 20.2865 | -12.2575  |             19.2398 |
| dqn    | late-control        | VALUE    |       1280 |        52.2031 |                 20.3385 | -12.2246  |             19.2384 |
| dqn    | no-hazard-control   | ALL      |       1280 |       100      |                100      |  20.8932  |             19.1068 |
| dqn    | no-hazard-control   | COMBINED |       1280 |       100      |                100      |  20.6457  |             19.3543 |
| dqn    | no-hazard-control   | SAFE     |       1280 |       100      |                100      |  20.6385  |             19.3615 |
| dqn    | no-hazard-control   | VALUE    |       1280 |       100      |                100      |  20.8513  |             19.1487 |
| dqn    | seen-r2.0-d1.0      | ALL      |       1280 |        88.2188 |                 80.3646 |  11.9598  |             19.3854 |
| dqn    | seen-r2.0-d1.0      | COMBINED |       1280 |        90.6719 |                 84.4531 |  13.4837  |             19.4607 |
| dqn    | seen-r2.0-d1.0      | SAFE     |       1280 |        90.6719 |                 84.4531 |  13.4762  |             19.4678 |
| dqn    | seen-r2.0-d1.0      | VALUE    |       1280 |        81.6094 |                 69.349  |   7.01323 |             19.3553 |
| dqn    | seen-r2.0-d4.0      | ALL      |       1280 |        94.5156 |                 90.8594 |  16.7882  |             19.1538 |
| dqn    | seen-r2.0-d4.0      | COMBINED |       1280 |        94.2031 |                 90.3385 |  16.5107  |             19.1632 |
| dqn    | seen-r2.0-d4.0      | SAFE     |       1280 |        94.0938 |                 90.1562 |  16.4277  |             19.1627 |
| dqn    | seen-r2.0-d4.0      | VALUE    |       1280 |        94.3594 |                 90.599  |  16.6463  |             19.1629 |
| dqn    | seen-r6.0-d1.0      | ALL      |       1280 |        69.7031 |                 49.5052 |  -1.31248 |             19.5421 |
| dqn    | seen-r6.0-d1.0      | COMBINED |       1280 |        81.125  |                 68.5417 |   5.90262 |             20.0247 |
| dqn    | seen-r6.0-d1.0      | SAFE     |       1280 |        80.8281 |                 68.0469 |   5.70801 |             20.0188 |
| dqn    | seen-r6.0-d1.0      | VALUE    |       1280 |        67.7656 |                 46.276  |  -3.0951  |             19.5977 |
| dqn    | seen-r6.0-d4.0      | ALL      |       1280 |        83.5    |                 72.5    |   8.40908 |             19.44   |
| dqn    | seen-r6.0-d4.0      | COMBINED |       1280 |        86.9062 |                 78.1771 |  10.4806  |             19.5825 |
| dqn    | seen-r6.0-d4.0      | SAFE     |       1280 |        86.7969 |                 77.9948 |  10.3913  |             19.5891 |
| dqn    | seen-r6.0-d4.0      | VALUE    |       1280 |        85.2344 |                 75.3906 |   9.42568 |             19.5271 |
| dqn    | unseen-r4-d2-loss20 | ALL      |       1280 |        81.4531 |                 69.0885 |   7.07819 |             19.4143 |
| dqn    | unseen-r4-d2-loss20 | COMBINED |       1280 |        85.8906 |                 76.4844 |   9.99704 |             19.5351 |
| dqn    | unseen-r4-d2-loss20 | SAFE     |       1280 |        85.6875 |                 76.1458 |   9.83657 |             19.5419 |
| dqn    | unseen-r4-d2-loss20 | VALUE    |       1280 |        80.6406 |                 67.7344 |   6.34218 |             19.4429 |
| dqn    | unseen-r8-d1-loss20 | ALL      |       1280 |        66      |                 43.3333 |  -3.64615 |             19.4764 |
| dqn    | unseen-r8-d1-loss20 | COMBINED |       1280 |        74.8438 |                 58.0729 |   1.14489 |             20.1052 |
| dqn    | unseen-r8-d1-loss20 | SAFE     |       1280 |        73.5938 |                 55.9896 |   0.40286 |             20.058  |
| dqn    | unseen-r8-d1-loss20 | VALUE    |       1280 |        63.8906 |                 39.8177 |  -5.79415 |             19.5789 |
| mappo  | late-control        | ALL      |       1280 |        51.2344 |                 18.724  | -12.6937  |             19.218  |
| mappo  | late-control        | COMBINED |       1280 |        51.4062 |                 19.0104 | -12.5369  |             19.2228 |
| mappo  | late-control        | SAFE     |       1280 |        50.8906 |                 18.1771 | -12.8619  |             19.211  |
| mappo  | late-control        | VALUE    |       1280 |        51.6094 |                 19.349  | -12.4591  |             19.2336 |
| mappo  | no-hazard-control   | ALL      |       1280 |       100      |                100      |  21.3389  |             18.6611 |
| mappo  | no-hazard-control   | COMBINED |       1280 |       100      |                100      |  21.2855  |             18.7145 |
| mappo  | no-hazard-control   | SAFE     |       1280 |       100      |                100      |  21.2412  |             18.7588 |
| mappo  | no-hazard-control   | VALUE    |       1280 |       100      |                100      |  21.0508  |             18.9492 |
| mappo  | seen-r2.0-d1.0      | ALL      |       1280 |        85.1094 |                 75.1823 |  10.4178  |             19.0344 |
| mappo  | seen-r2.0-d1.0      | COMBINED |       1280 |        86.1562 |                 76.9271 |  11.1063  |             19.0544 |
| mappo  | seen-r2.0-d1.0      | SAFE     |       1280 |        86.5156 |                 77.526  |  11.3354  |             19.0842 |
| mappo  | seen-r2.0-d1.0      | VALUE    |       1280 |        79.6562 |                 66.0938 |   5.89592 |             19.2292 |
| mappo  | seen-r2.0-d4.0      | ALL      |       1280 |        92.3438 |                 87.2396 |  15.5079  |             18.9696 |
| mappo  | seen-r2.0-d4.0      | COMBINED |       1280 |        92.5781 |                 87.6302 |  15.7133  |             18.9788 |
| mappo  | seen-r2.0-d4.0      | SAFE     |       1280 |        92.8438 |                 88.0729 |  15.8809  |             18.9915 |
| mappo  | seen-r2.0-d4.0      | VALUE    |       1280 |        94.0312 |                 90.0521 |  16.4907  |             19.1053 |
| mappo  | seen-r6.0-d1.0      | ALL      |       1280 |        67.3594 |                 45.599  |  -1.92025 |             19.0496 |
| mappo  | seen-r6.0-d1.0      | COMBINED |       1280 |        72.3281 |                 53.8802 |   1.42628 |             19.0933 |
| mappo  | seen-r6.0-d1.0      | SAFE     |       1280 |        73.0625 |                 55.1042 |   1.87564 |             19.1553 |
| mappo  | seen-r6.0-d1.0      | VALUE    |       1280 |        65.2344 |                 42.0573 |  -4.23069 |             19.3117 |
| mappo  | seen-r6.0-d4.0      | ALL      |       1280 |        80.0938 |                 66.8229 |   6.81663 |             18.9746 |
| mappo  | seen-r6.0-d4.0      | COMBINED |       1280 |        82.875  |                 71.4583 |   8.77152 |             19.0012 |
| mappo  | seen-r6.0-d4.0      | SAFE     |       1280 |        83.4688 |                 72.4479 |   9.079   |             19.0469 |
| mappo  | seen-r6.0-d4.0      | VALUE    |       1280 |        83.2969 |                 72.1615 |   8.4233  |             19.318  |
| mappo  | unseen-r4-d2-loss20 | ALL      |       1280 |        77.4375 |                 62.3958 |   5.05148 |             18.9494 |
| mappo  | unseen-r4-d2-loss20 | COMBINED |       1280 |        80      |                 66.6667 |   6.85273 |             18.9754 |
| mappo  | unseen-r4-d2-loss20 | SAFE     |       1280 |        80.4375 |                 67.3958 |   7.08629 |             19.0098 |
| mappo  | unseen-r4-d2-loss20 | VALUE    |       1280 |        77.4063 |                 62.3438 |   4.3459  |             19.2434 |
| mappo  | unseen-r8-d1-loss20 | ALL      |       1280 |        60.9219 |                 34.8698 |  -6.34254 |             18.9836 |
| mappo  | unseen-r8-d1-loss20 | COMBINED |       1280 |        65.5312 |                 42.5521 |  -3.2467  |             19.0432 |
| mappo  | unseen-r8-d1-loss20 | SAFE     |       1280 |        66.0156 |                 43.3594 |  -2.95707 |             19.0979 |
| mappo  | unseen-r8-d1-loss20 | VALUE    |       1280 |        60.2656 |                 33.776  |  -7.55196 |             19.2529 |

## All confirmatory comparisons

| algo   | scope   | case                | baseline   |   difference_pp |   lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:-------|:--------|:--------------------|:-----------|----------------:|-----------:|-----------:|:------------------------|:-------------------------|
| dqn    | case    | seen-r2.0-d1.0      | ALL        |     2.45312     | -1.5       |    6.67994 | False                   | False                    |
| dqn    | case    | seen-r2.0-d1.0      | SAFE       |     6.93889e-17 | -1.4375    |    1.1875  | False                   | False                    |
| dqn    | case    | seen-r2.0-d1.0      | VALUE      |     9.0625      |  3.81754   |   15.5444  | True                    | False                    |
| dqn    | case    | seen-r6.0-d1.0      | ALL        |    11.4219      |  5.23689   |   18.0262  | True                    | False                    |
| dqn    | case    | seen-r6.0-d1.0      | SAFE       |     0.296875    | -1.79436   |    2.75    | False                   | False                    |
| dqn    | case    | seen-r6.0-d1.0      | VALUE      |    13.3594      |  7.95564   |   19.8362  | True                    | False                    |
| dqn    | case    | seen-r2.0-d4.0      | ALL        |    -0.3125      | -3.04688   |    1.77873 | False                   | False                    |
| dqn    | case    | seen-r2.0-d4.0      | SAFE       |     0.109375    | -0.859375  |    1.03125 | False                   | False                    |
| dqn    | case    | seen-r2.0-d4.0      | VALUE      |    -0.15625     | -1.96875   |    1.07561 | False                   | False                    |
| dqn    | case    | seen-r6.0-d4.0      | ALL        |     3.40625     | -0.96875   |    8.21875 | False                   | False                    |
| dqn    | case    | seen-r6.0-d4.0      | SAFE       |     0.109375    | -2.27873   |    1.85686 | False                   | False                    |
| dqn    | case    | seen-r6.0-d4.0      | VALUE      |     1.67187     | -1.65373   |    6       | False                   | False                    |
| dqn    | case    | unseen-r4-d2-loss20 | ALL        |     4.4375      | -0.216231  |    8.99748 | False                   | False                    |
| dqn    | case    | unseen-r4-d2-loss20 | SAFE       |     0.203125    | -1.65625   |    1.92188 | False                   | False                    |
| dqn    | case    | unseen-r4-d2-loss20 | VALUE      |     5.25        |  1.4375    |   10.7162  | True                    | False                    |
| dqn    | case    | unseen-r8-d1-loss20 | ALL        |     8.84375     |  3.35938   |   14.625   | True                    | False                    |
| dqn    | case    | unseen-r8-d1-loss20 | SAFE       |     1.25        | -1.10686   |    5.20061 | False                   | False                    |
| dqn    | case    | unseen-r8-d1-loss20 | VALUE      |    10.9531      |  5.73438   |   16.2944  | True                    | False                    |
| dqn    | case    | late-control        | ALL        |    -0.375       | -3.79688   |    1.41936 | False                   | False                    |
| dqn    | case    | late-control        | SAFE       |     0.109375    | -1.40373   |    2.09375 | False                   | False                    |
| dqn    | case    | late-control        | VALUE      |     0.078125    | -1.35686   |    1.57561 | False                   | False                    |
| dqn    | case    | no-hazard-control   | ALL        |     0           |  0         |    0       | False                   | False                    |
| dqn    | case    | no-hazard-control   | SAFE       |     0           |  0         |    0       | False                   | False                    |
| dqn    | case    | no-hazard-control   | VALUE      |     0           |  0         |    0       | False                   | False                    |
| dqn    | primary | equal-case-average  | SAFE       |     0.259766    | -0.427105  |    1.11492 | False                   | False                    |
| mappo  | case    | seen-r2.0-d1.0      | ALL        |     1.04688     | -4.25      |    6.61996 | False                   | False                    |
| mappo  | case    | seen-r2.0-d1.0      | SAFE       |    -0.359375    | -6.95616   |    6.78125 | False                   | False                    |
| mappo  | case    | seen-r2.0-d1.0      | VALUE      |     6.5         |  0.335681  |   12.7162  | True                    | False                    |
| mappo  | case    | seen-r6.0-d1.0      | ALL        |     4.96875     | -1.52873   |   11.9975  | False                   | False                    |
| mappo  | case    | seen-r6.0-d1.0      | SAFE       |    -0.734375    | -8.49496   |    7.68498 | False                   | False                    |
| mappo  | case    | seen-r6.0-d1.0      | VALUE      |     7.09375     |  0.0413243 |   14.8569  | True                    | False                    |
| mappo  | case    | seen-r2.0-d4.0      | ALL        |     0.234375    | -2.40373   |    3.10937 | False                   | False                    |
| mappo  | case    | seen-r2.0-d4.0      | SAFE       |    -0.265625    | -3.24244   |    2.76562 | False                   | False                    |
| mappo  | case    | seen-r2.0-d4.0      | VALUE      |    -1.45312     | -5.68498   |    2.61493 | False                   | False                    |
| mappo  | case    | seen-r6.0-d4.0      | ALL        |     2.78125     | -2.01563   |    7.53125 | False                   | False                    |
| mappo  | case    | seen-r6.0-d4.0      | SAFE       |    -0.59375     | -4.57561   |    3.60937 | False                   | False                    |
| mappo  | case    | seen-r6.0-d4.0      | VALUE      |    -0.421875    | -7.60686   |    6.37248 | False                   | False                    |
| mappo  | case    | unseen-r4-d2-loss20 | ALL        |     2.5625      | -2.39869   |    7.68498 | False                   | False                    |
| mappo  | case    | unseen-r4-d2-loss20 | SAFE       |    -0.4375      | -5.28125   |    5.43246 | False                   | False                    |
| mappo  | case    | unseen-r4-d2-loss20 | VALUE      |     2.59375     | -3.66936   |    8.71371 | False                   | False                    |
| mappo  | case    | unseen-r8-d1-loss20 | ALL        |     4.60938     | -2.62248   |   13.2319  | False                   | False                    |
| mappo  | case    | unseen-r8-d1-loss20 | SAFE       |    -0.484375    | -8.67743   |    8.96371 | False                   | False                    |
| mappo  | case    | unseen-r8-d1-loss20 | VALUE      |     5.26562     | -2.19305   |   12.4375  | False                   | False                    |
| mappo  | case    | late-control        | ALL        |     0.171875    | -5.57561   |    5.28125 | False                   | False                    |
| mappo  | case    | late-control        | SAFE       |     0.515625    | -4.15121   |    5.76311 | False                   | False                    |
| mappo  | case    | late-control        | VALUE      |    -0.203125    | -5.10686   |    4.46623 | False                   | False                    |
| mappo  | case    | no-hazard-control   | ALL        |     0           |  0         |    0       | False                   | False                    |
| mappo  | case    | no-hazard-control   | SAFE       |     0           |  0         |    0       | False                   | False                    |
| mappo  | case    | no-hazard-control   | VALUE      |     0           |  0         |    0       | False                   | False                    |
| mappo  | primary | equal-case-average  | SAFE       |    -0.294922    | -3.73545   |    3.63836 | False                   | False                    |

## Interpretation and limits

Auxiliary training generated 18,518 eligible packet interventions from 2,560 factual episodes, requiring 37,036 replay branches in addition to the routing training episodes. These are training simulations, not independent final evaluation episodes.

Routing actors have equal episode budgets: 300 shared ALL warmup plus 300 arm-specific adaptation episodes. SAFE and COMBINED share exactly the same safeguards; SAFE differs from the previous SAFE-ALL baseline. Learned arms additionally consume auxiliary causal replay labels available to all arms. Total computation is not matched. Updates and runtime are in training_manifest.csv. A value model fitted to the warmup actor stays fixed, so actor adaptation can make its estimates stale. Validation was diagnostic only; settings and checkpoint hashes were locked before tests. No model selection or retuning used final outcomes.

Final layouts/tapes are new; half the layouts have four forks, a size absent from training. Two corruption conditions have unseen parameters. The pooled endpoint includes late/no-hazard controls equally. This tests bounded structured-network generalization, not operational performance. Forged messages use public target edges and independent fair-coin payloads, may be correct by coincidence and claim unauthenticated identities. Loss applies only to honest transmissions; forgery models receiver injection. Admission does not save transmitted bandwidth.

Fixed-actor swaps isolate immediate filtering under the COMBINED-trained actor, whereas primary contrasts include actor adaptation. Those swaps, topology-size breakdowns, training curves, utility, packet counts, prediction errors and common-survivor cost/time are descriptive. Common-survivor comparisons condition on both methods succeeding and are not unconditional cost guarantees. No nonsignificant result establishes equivalence/noninferiority, and training curves do not establish convergence. All earlier failures remain preserved.

## Reproduce

See [the locked protocol](../matched-gate-protocol.md). The package includes the full simulator, all 64 checkpoints, fitted regressors, auxiliary examples, training/validation/episode/convoy records and report code.
