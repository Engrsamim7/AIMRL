# Balanced cover-traffic stress: frozen-model results

Completed **28,000 new evaluation episodes**, **140,000 convoy records**, and all four declared stress conditions with unchanged routing actors, value models and inherited numeric settings. **15 of 36 comparisons supported delivery superiority** after a conservative 198-test correction; **0 supported a disadvantage**. The correction accounts for 162 earlier and 36 current comparisons.

The earlier attacker preferentially sent clear statements about active blocks. Strong neural actors could exploit report presence as a clue even when the statement was false. This stress distributes forged targets uniformly over public potential hazard corridors and draws block/open payloads with a fair coin, independently of live truth and receiver plans. Forged reports may be correct by coincidence; forged origin is not equivalent to false content. Confidence matches honest reports. Ninety percent of forged packets claim a convoy identity. Rates 2/6 and delays 1/4 are crossed; loss is 0.1 and physical scout lead is 4.

This is a **frozen-model corruption-shift robustness test** on new layouts and tapes. Models were not retrained on cover traffic. It establishes only the named stress conditions and baselines; it does not establish superiority after every baseline retrains on this new attacker. Costs, sensors, targets, departures, exogenous blocks and environment tapes are matched across methods. All four conditions are published. No forged origin, simulator attack state or future outcome enters the gate.

Loss 0.1 applies to honest broadcasts. Forged packets model receiver-side injection and do not undergo stochastic transport loss; this assumption is common to every method.

## Supported comparisons

| algo    | case               | baseline   |   difference_pp |   lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:--------|:-------------------|:-----------|----------------:|-----------:|-----------:|:------------------------|:-------------------------|
| planner | cover-rate2-delay1 | ALL        |         8.1     |   4.2      |   12.3     | True                    | False                    |
| planner | cover-rate2-delay1 | FRC        |         8.1     |   4.1      |   12.3     | True                    | False                    |
| planner | cover-rate6-delay1 | ALL        |        13.3     |   6.72524  |   19.7     | True                    | False                    |
| planner | cover-rate6-delay1 | FRC        |        13.3     |   7        |   19.7748  | True                    | False                    |
| planner | cover-rate6-delay1 | SAFE-ALL   |         2.8     |   0.2      |    5.8     | True                    | False                    |
| planner | cover-rate2-delay4 | ALL        |         5.2     |   1.8      |   10.1     | True                    | False                    |
| planner | cover-rate2-delay4 | FRC        |         5.2     |   1.8      |   10.1     | True                    | False                    |
| planner | cover-rate6-delay4 | ALL        |         8.4     |   3.5      |   13.7     | True                    | False                    |
| planner | cover-rate6-delay4 | FRC        |         8.4     |   3.3      |   13.7     | True                    | False                    |
| dqn     | cover-rate6-delay1 | ALL        |         8.03333 |   0.841747 |   16.1     | True                    | False                    |
| dqn     | cover-rate6-delay1 | FRC        |         8.03333 |   0.833333 |   16.0916  | True                    | False                    |
| mappo   | cover-rate2-delay1 | ALL        |         4.26667 |   1        |    7.86667 | True                    | False                    |
| mappo   | cover-rate2-delay1 | FRC        |         4.26667 |   1        |    7.96667 | True                    | False                    |
| mappo   | cover-rate6-delay1 | ALL        |         7.13333 |   0.741747 |   16.4     | True                    | False                    |
| mappo   | cover-rate6-delay1 | FRC        |         7.13333 |   0.8      |   16.2748  | True                    | False                    |

## All performance results

| algo    | case               | method   |   episodes |   delivery_pct |   follower_delivery_pct |   utility |    time |
|:--------|:-------------------|:---------|-----------:|---------------:|------------------------:|----------:|--------:|
| dqn     | cover-rate2-delay1 | ALL      |        600 |        89.3333 |                 82.2222 |  17.9224  | 14.0568 |
| dqn     | cover-rate2-delay1 | FRC      |        600 |        89.3333 |                 82.2222 |  17.9224  | 14.0568 |
| dqn     | cover-rate2-delay1 | NC       |        600 |        60.2333 |                 33.7222 |  -2.60856 | 13.6972 |
| dqn     | cover-rate2-delay1 | SAFE-ALL |        600 |        93.1    |                 88.5    |  20.4463  | 14.1627 |
| dqn     | cover-rate2-delay1 | VALUE    |        600 |        93      |                 88.3333 |  20.3655  | 14.1559 |
| dqn     | cover-rate2-delay4 | ALL      |        600 |        94.6667 |                 91.1111 |  21.8773  | 14.0149 |
| dqn     | cover-rate2-delay4 | FRC      |        600 |        94.6667 |                 91.1111 |  21.8773  | 14.0149 |
| dqn     | cover-rate2-delay4 | NC       |        600 |        58.9667 |                 31.6111 |  -3.36261 | 13.7126 |
| dqn     | cover-rate2-delay4 | SAFE-ALL |        600 |        95.4333 |                 92.3889 |  22.3891  | 14.0448 |
| dqn     | cover-rate2-delay4 | VALUE    |        600 |        95.6667 |                 92.7778 |  22.5741  | 14.0445 |
| dqn     | cover-rate6-delay1 | ALL      |        600 |        77.1667 |                 61.9444 |   8.55828 | 14.3981 |
| dqn     | cover-rate6-delay1 | FRC      |        600 |        77.1667 |                 61.9444 |   8.55828 | 14.3981 |
| dqn     | cover-rate6-delay1 | NC       |        600 |        58.0333 |                 30.0556 |  -3.97204 | 13.7461 |
| dqn     | cover-rate6-delay1 | SAFE-ALL |        600 |        84.0667 |                 73.4444 |  12.9809  | 14.7926 |
| dqn     | cover-rate6-delay1 | VALUE    |        600 |        85.2    |                 75.3333 |  13.7416  | 14.8363 |
| dqn     | cover-rate6-delay4 | ALL      |        600 |        85.2    |                 75.3333 |  14.4444  | 14.4409 |
| dqn     | cover-rate6-delay4 | FRC      |        600 |        85.2    |                 75.3333 |  14.4444  | 14.4409 |
| dqn     | cover-rate6-delay4 | NC       |        600 |        54.5667 |                 24.2778 |  -6.39162 | 13.7211 |
| dqn     | cover-rate6-delay4 | SAFE-ALL |        600 |        87.9333 |                 79.8889 |  16.1426  | 14.5546 |
| dqn     | cover-rate6-delay4 | VALUE    |        600 |        87.7333 |                 79.5556 |  15.9787  | 14.5434 |
| mappo   | cover-rate2-delay1 | ALL      |        600 |        88.2667 |                 80.4444 |  17.6294  | 13.7443 |
| mappo   | cover-rate2-delay1 | FRC      |        600 |        88.2667 |                 80.4444 |  17.6294  | 13.7443 |
| mappo   | cover-rate2-delay1 | NC       |        600 |        61.3667 |                 35.6111 |  -1.72681 | 13.6991 |
| mappo   | cover-rate2-delay1 | SAFE-ALL |        600 |        92.6    |                 87.6667 |  20.6835  | 13.7841 |
| mappo   | cover-rate2-delay1 | VALUE    |        600 |        92.5333 |                 87.5556 |  20.629   | 13.7837 |
| mappo   | cover-rate2-delay4 | ALL      |        600 |        93.4667 |                 89.1111 |  21.4101  | 13.7695 |
| mappo   | cover-rate2-delay4 | FRC      |        600 |        93.4667 |                 89.1111 |  21.4101  | 13.7695 |
| mappo   | cover-rate2-delay4 | NC       |        600 |        58.2333 |                 30.3889 |  -3.91577 | 13.7188 |
| mappo   | cover-rate2-delay4 | SAFE-ALL |        600 |        94.1    |                 90.1667 |  21.8494  | 13.7846 |
| mappo   | cover-rate2-delay4 | VALUE    |        600 |        94.1    |                 90.1667 |  21.8497  | 13.7826 |
| mappo   | cover-rate6-delay1 | ALL      |        600 |        71.6333 |                 52.7222 |   5.20222 | 13.8467 |
| mappo   | cover-rate6-delay1 | FRC      |        600 |        71.6333 |                 52.7222 |   5.20222 | 13.8467 |
| mappo   | cover-rate6-delay1 | NC       |        600 |        56      |                 26.6667 |  -5.57181 | 13.7439 |
| mappo   | cover-rate6-delay1 | SAFE-ALL |        600 |        77.8    |                 63      |   9.52787 | 13.9856 |
| mappo   | cover-rate6-delay1 | VALUE    |        600 |        78.7667 |                 64.6111 |  10.1997  | 14.0136 |
| mappo   | cover-rate6-delay4 | ALL      |        600 |        81.3333 |                 68.8889 |  12.3956  | 13.8834 |
| mappo   | cover-rate6-delay4 | FRC      |        600 |        81.3333 |                 68.8889 |  12.3956  | 13.8834 |
| mappo   | cover-rate6-delay4 | NC       |        600 |        56.2667 |                 27.1111 |  -5.08831 | 13.7201 |
| mappo   | cover-rate6-delay4 | SAFE-ALL |        600 |        84.9333 |                 74.8889 |  14.8855  | 13.9484 |
| mappo   | cover-rate6-delay4 | VALUE    |        600 |        84.9667 |                 74.9444 |  14.9088  | 13.9495 |
| planner | cover-rate2-delay1 | ALL      |        200 |        86.1    |                 76.8333 |  15.6861  | 14.0011 |
| planner | cover-rate2-delay1 | FRC      |        200 |        86.1    |                 76.8333 |  15.6861  | 14.0011 |
| planner | cover-rate2-delay1 | NC       |        200 |        60.9    |                 34.8333 |  -2.08535 | 13.7024 |
| planner | cover-rate2-delay1 | SAFE-ALL |        200 |        93.7    |                 89.5    |  20.975   | 14.1176 |
| planner | cover-rate2-delay1 | VALUE    |        200 |        94.2    |                 90.3333 |  21.3295  | 14.1273 |
| planner | cover-rate2-delay4 | ALL      |        200 |        90.8    |                 84.6667 |  19.1385  | 13.9283 |
| planner | cover-rate2-delay4 | FRC      |        200 |        90.8    |                 84.6667 |  19.1385  | 13.9283 |
| planner | cover-rate2-delay4 | NC       |        200 |        57.3    |                 28.8333 |  -4.67745 | 13.7114 |
| planner | cover-rate2-delay4 | SAFE-ALL |        200 |        95.9    |                 93.1667 |  22.8236  | 13.9728 |
| planner | cover-rate2-delay4 | VALUE    |        200 |        96      |                 93.3333 |  22.8915  | 13.9766 |
| planner | cover-rate6-delay1 | ALL      |        200 |        74.2    |                 57      |   6.65292 | 14.2784 |
| planner | cover-rate6-delay1 | FRC      |        200 |        74.2    |                 57      |   6.65292 | 14.2784 |
| planner | cover-rate6-delay1 | NC       |        200 |        57.1    |                 28.5    |  -4.70025 | 13.7324 |
| planner | cover-rate6-delay1 | SAFE-ALL |        200 |        84.7    |                 74.5    |  13.5237  | 14.7412 |
| planner | cover-rate6-delay1 | VALUE    |        200 |        87.5    |                 79.1667 |  15.3864  | 14.917  |
| planner | cover-rate6-delay4 | ALL      |        200 |        80.8    |                 68      |  11.4535  | 14.2201 |
| planner | cover-rate6-delay4 | FRC      |        200 |        80.8    |                 68      |  11.4535  | 14.2201 |
| planner | cover-rate6-delay4 | NC       |        200 |        54.9    |                 24.8333 |  -6.12189 | 13.7212 |
| planner | cover-rate6-delay4 | SAFE-ALL |        200 |        88.3    |                 80.5    |  16.576   | 14.3973 |
| planner | cover-rate6-delay4 | VALUE    |        200 |        89.2    |                 82      |  17.2001  | 14.4264 |

## All paired comparisons

| algo    | case               | baseline   |   difference_pp |     lower_pp |   upper_pp | superiority_supported   | disadvantage_supported   |
|:--------|:-------------------|:-----------|----------------:|-------------:|-----------:|:------------------------|:-------------------------|
| planner | cover-rate2-delay1 | ALL        |       8.1       |  4.2         |   12.3     | True                    | False                    |
| planner | cover-rate2-delay1 | FRC        |       8.1       |  4.1         |   12.3     | True                    | False                    |
| planner | cover-rate2-delay1 | SAFE-ALL   |       0.5       |  0           |    1.8     | False                   | False                    |
| planner | cover-rate6-delay1 | ALL        |      13.3       |  6.72524     |   19.7     | True                    | False                    |
| planner | cover-rate6-delay1 | FRC        |      13.3       |  7           |   19.7748  | True                    | False                    |
| planner | cover-rate6-delay1 | SAFE-ALL   |       2.8       |  0.2         |    5.8     | True                    | False                    |
| planner | cover-rate2-delay4 | ALL        |       5.2       |  1.8         |   10.1     | True                    | False                    |
| planner | cover-rate2-delay4 | FRC        |       5.2       |  1.8         |   10.1     | True                    | False                    |
| planner | cover-rate2-delay4 | SAFE-ALL   |       0.1       |  0           |    1       | False                   | False                    |
| planner | cover-rate6-delay4 | ALL        |       8.4       |  3.5         |   13.7     | True                    | False                    |
| planner | cover-rate6-delay4 | FRC        |       8.4       |  3.3         |   13.7     | True                    | False                    |
| planner | cover-rate6-delay4 | SAFE-ALL   |       0.9       | -0.5         |    2.9     | False                   | False                    |
| dqn     | cover-rate2-delay1 | ALL        |       3.66667   | -4.25408e-16 |    7.8     | False                   | False                    |
| dqn     | cover-rate2-delay1 | FRC        |       3.66667   | -0.1         |    7.93333 | False                   | False                    |
| dqn     | cover-rate2-delay1 | SAFE-ALL   |      -0.1       | -1.93333     |    1.24984 | False                   | False                    |
| dqn     | cover-rate6-delay1 | ALL        |       8.03333   |  0.841747    |   16.1     | True                    | False                    |
| dqn     | cover-rate6-delay1 | FRC        |       8.03333   |  0.833333    |   16.0916  | True                    | False                    |
| dqn     | cover-rate6-delay1 | SAFE-ALL   |       1.13333   | -0.7         |    4.9     | False                   | False                    |
| dqn     | cover-rate2-delay4 | ALL        |       1         | -1.5         |    3.8     | False                   | False                    |
| dqn     | cover-rate2-delay4 | FRC        |       1         | -1.4         |    3.9     | False                   | False                    |
| dqn     | cover-rate2-delay4 | SAFE-ALL   |       0.233333  | -1.03333     |    2.1     | False                   | False                    |
| dqn     | cover-rate6-delay4 | ALL        |       2.53333   | -1.93333     |    8.89159 | False                   | False                    |
| dqn     | cover-rate6-delay4 | FRC        |       2.53333   | -1.89159     |    9       | False                   | False                    |
| dqn     | cover-rate6-delay4 | SAFE-ALL   |      -0.2       | -2.6         |    2       | False                   | False                    |
| mappo   | cover-rate2-delay1 | ALL        |       4.26667   |  1           |    7.86667 | True                    | False                    |
| mappo   | cover-rate2-delay1 | FRC        |       4.26667   |  1           |    7.96667 | True                    | False                    |
| mappo   | cover-rate2-delay1 | SAFE-ALL   |      -0.0666667 | -1           |    0.8     | False                   | False                    |
| mappo   | cover-rate6-delay1 | ALL        |       7.13333   |  0.741747    |   16.4     | True                    | False                    |
| mappo   | cover-rate6-delay1 | FRC        |       7.13333   |  0.8         |   16.2748  | True                    | False                    |
| mappo   | cover-rate6-delay1 | SAFE-ALL   |       0.966667  | -1.2         |    4.8     | False                   | False                    |
| mappo   | cover-rate2-delay4 | ALL        |       0.633333  | -1.03333     |    3.06667 | False                   | False                    |
| mappo   | cover-rate2-delay4 | FRC        |       0.633333  | -1           |    3.02492 | False                   | False                    |
| mappo   | cover-rate2-delay4 | SAFE-ALL   |       0         | -0.9         |    0.9     | False                   | False                    |
| mappo   | cover-rate6-delay4 | ALL        |       3.63333   | -0.5         |    8.53333 | False                   | False                    |
| mappo   | cover-rate6-delay4 | FRC        |       3.63333   | -0.42492     |    8.5     | False                   | False                    |
| mappo   | cover-rate6-delay4 | SAFE-ALL   |       0.0333333 | -1.4         |    1.53333 | False                   | False                    |

The shared interpreter and guarded actor-specific value model are unchanged from the guarded study. NC, ALL, tuned FRC, SAFE-ALL and VALUE use identical weights within each actor/seed. Two scouts and three followers count in full delivery; follower-only rates use the three followers. Claims of gate-specific utility beyond simple conservative filtering require the SAFE-ALL comparison, not just ALL/FRC. A high-confidence forged block can induce detours under warning preservation; common-survivor cost/time effects are retained in common_survivors.csv. This is an explicit safety/efficiency tradeoff, not superiority on every KPI.

Intervals use 200,000 graph/episode clustered, training-seed-crossed paired bootstrap draws and two-sided Bonferroni tails over 198 tests. Higher draw count improves resolution in the extreme corrected tails. Three training seeds and ten small structured layouts limit extrapolation. The original-topology transfer and initial unconstrained failures remain in the earlier reports. Packet communication counts are retained per episode; individual cover packet logs are not exported. Receiver-side admission does not reduce transmission bandwidth.

## Reproduce

Run the first and guarded studies using the commands in ../guarded-research-results/README.md, then:

```bash
cd simulator
../.venv/bin/python run_cover_traffic_stress.py --parent out/guarded-research-study-new --output out/cover-traffic-stress-new --workers 3
cd ..
MPLCONFIGDIR=/tmp/aimrl-mpl .venv/bin/python simulator/report_cover_stress.py --run simulator/out/cover-traffic-stress-new --output revision/cover-traffic-results-new
```
