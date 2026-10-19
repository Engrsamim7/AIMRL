# Dynamic-recovery gate results

No primary comparison met both predeclared requirements. These results do not establish the learned gate as superior to a conservative baseline.

This new study follows earlier negative results; it does not replace them. All 8 cases are reported. These are constructed logistics graphs, not operational validation. Filtering at the receiver does not save transmitted bandwidth.

## Primary decisions

| algo   | baseline   |   utility_difference |   utility_lower |   utility_upper |   delivery_difference_pp |   delivery_lower_pp |   delivery_upper_pp | utility_superiority   | delivery_noninferiority   | joint_success   |
|:-------|:-----------|---------------------:|----------------:|----------------:|-------------------------:|--------------------:|--------------------:|:----------------------|:--------------------------|:----------------|
| dqn    | AGE        |               -0.024 |          -1.758 |           1.537 |                   -0.059 |              -2.594 |               2.223 | False                 | False                     | False           |
| dqn    | KEEP       |                0.591 |          -1.255 |           3.068 |                    0.811 |              -1.926 |               4.398 | False                 | False                     | False           |
| dqn    | SAFE       |                0.135 |          -1.857 |           2.277 |                    0.184 |              -2.753 |               3.305 | False                 | False                     | False           |
| mappo  | AGE        |                0.333 |          -0.510 |           1.293 |                    0.471 |              -0.717 |               1.843 | False                 | True                      | False           |
| mappo  | KEEP       |                0.170 |          -0.655 |           0.958 |                    0.266 |              -0.897 |               1.383 | False                 | True                      | False           |
| mappo  | SAFE       |                0.360 |          -0.529 |           1.295 |                    0.516 |              -0.777 |               1.846 | False                 | True                      | False           |

Success requires corrected utility lower bound >0 and delivery lower bound >−1 percentage point. Delivery noninferiority alone is not superiority. Two-sided Bonferroni correction388, 200,000 crossed paired bootstrap draws,8 independent paired training seeds per algorithm. Historical intervals unchanged.

## All means

| algo   | case              | method   |   delivery_pct |   utility |
|:-------|:------------------|:---------|---------------:|----------:|
| dqn    | late-control      | AGE      |         64.828 |    -3.897 |
| dqn    | late-control      | ALL      |         64.969 |    -3.795 |
| dqn    | late-control      | KEEP     |         64.594 |    -4.063 |
| dqn    | late-control      | LEARN    |         64.703 |    -3.985 |
| dqn    | late-control      | SAFE     |         65.062 |    -3.725 |
| dqn    | mixed-recovery    | AGE      |         91.500 |    14.843 |
| dqn    | mixed-recovery    | ALL      |         90.281 |    14.043 |
| dqn    | mixed-recovery    | KEEP     |         90.594 |    14.173 |
| dqn    | mixed-recovery    | LEARN    |         91.406 |    14.794 |
| dqn    | mixed-recovery    | SAFE     |         91.344 |    14.746 |
| dqn    | no-hazard-control | AGE      |        100.000 |    21.145 |
| dqn    | no-hazard-control | ALL      |        100.000 |    21.152 |
| dqn    | no-hazard-control | KEEP     |        100.000 |    21.148 |
| dqn    | no-hazard-control | LEARN    |        100.000 |    21.158 |
| dqn    | no-hazard-control | SAFE     |        100.000 |    21.145 |
| dqn    | persistent        | AGE      |         82.734 |     8.229 |
| dqn    | persistent        | ALL      |         79.203 |     5.749 |
| dqn    | persistent        | KEEP     |         80.422 |     6.622 |
| dqn    | persistent        | LEARN    |         82.844 |     8.376 |
| dqn    | persistent        | SAFE     |         81.984 |     7.734 |
| dqn    | rapid-recovery    | AGE      |         99.844 |    20.937 |
| dqn    | rapid-recovery    | ALL      |         99.969 |    21.047 |
| dqn    | rapid-recovery    | KEEP     |         99.719 |    20.796 |
| dqn    | rapid-recovery    | LEARN    |         99.906 |    20.979 |
| dqn    | rapid-recovery    | SAFE     |         99.812 |    20.919 |
| dqn    | unseen-corruption | AGE      |         87.281 |    11.848 |
| dqn    | unseen-corruption | ALL      |         84.844 |    10.139 |
| dqn    | unseen-corruption | KEEP     |         86.516 |    11.332 |
| dqn    | unseen-corruption | LEARN    |         87.453 |    11.991 |
| dqn    | unseen-corruption | SAFE     |         86.750 |    11.476 |
| dqn    | unseen-delay      | AGE      |         95.047 |    17.442 |
| dqn    | unseen-delay      | ALL      |         94.047 |    16.709 |
| dqn    | unseen-delay      | KEEP     |         93.625 |    16.427 |
| dqn    | unseen-delay      | LEARN    |         94.672 |    17.177 |
| dqn    | unseen-delay      | SAFE     |         94.641 |    17.168 |
| dqn    | unseen-loss       | AGE      |         85.250 |    10.297 |
| dqn    | unseen-loss       | ALL      |         83.953 |     9.362 |
| dqn    | unseen-loss       | KEEP     |         84.062 |     9.484 |
| dqn    | unseen-loss       | LEARN    |         85.031 |    10.162 |
| dqn    | unseen-loss       | SAFE     |         84.953 |    10.104 |
| mappo  | late-control      | AGE      |         63.109 |    -5.150 |
| mappo  | late-control      | ALL      |         62.766 |    -5.413 |
| mappo  | late-control      | KEEP     |         63.625 |    -4.744 |
| mappo  | late-control      | LEARN    |         63.469 |    -4.899 |
| mappo  | late-control      | SAFE     |         63.391 |    -4.955 |
| mappo  | mixed-recovery    | AGE      |         91.484 |    14.789 |
| mappo  | mixed-recovery    | ALL      |         90.922 |    14.389 |
| mappo  | mixed-recovery    | KEEP     |         91.516 |    14.796 |
| mappo  | mixed-recovery    | LEARN    |         92.656 |    15.582 |
| mappo  | mixed-recovery    | SAFE     |         91.531 |    14.827 |
| mappo  | no-hazard-control | AGE      |        100.000 |    21.061 |
| mappo  | no-hazard-control | ALL      |        100.000 |    21.054 |
| mappo  | no-hazard-control | KEEP     |        100.000 |    21.077 |
| mappo  | no-hazard-control | LEARN    |        100.000 |    21.089 |
| mappo  | no-hazard-control | SAFE     |        100.000 |    21.069 |
| mappo  | persistent        | AGE      |         85.469 |    10.162 |
| mappo  | persistent        | ALL      |         83.687 |     8.838 |
| mappo  | persistent        | KEEP     |         85.484 |    10.208 |
| mappo  | persistent        | LEARN    |         87.016 |    11.292 |
| mappo  | persistent        | SAFE     |         84.891 |     9.742 |
| mappo  | rapid-recovery    | AGE      |        100.000 |    20.937 |
| mappo  | rapid-recovery    | ALL      |        100.000 |    20.938 |
| mappo  | rapid-recovery    | KEEP     |        100.000 |    20.924 |
| mappo  | rapid-recovery    | LEARN    |        100.000 |    20.931 |
| mappo  | rapid-recovery    | SAFE     |        100.000 |    20.946 |
| mappo  | unseen-corruption | AGE      |         87.078 |    11.621 |
| mappo  | unseen-corruption | ALL      |         85.609 |    10.566 |
| mappo  | unseen-corruption | KEEP     |         87.656 |    12.074 |
| mappo  | unseen-corruption | LEARN    |         88.422 |    12.567 |
| mappo  | unseen-corruption | SAFE     |         86.969 |    11.556 |
| mappo  | unseen-delay      | AGE      |         95.156 |    17.404 |
| mappo  | unseen-delay      | ALL      |         94.500 |    16.892 |
| mappo  | unseen-delay      | KEEP     |         95.359 |    17.559 |
| mappo  | unseen-delay      | LEARN    |         94.781 |    17.109 |
| mappo  | unseen-delay      | SAFE     |         95.063 |    17.342 |
| mappo  | unseen-loss       | AGE      |         85.703 |    10.528 |
| mappo  | unseen-loss       | ALL      |         84.953 |    10.001 |
| mappo  | unseen-loss       | KEEP     |         86.000 |    10.769 |
| mappo  | unseen-loss       | LEARN    |         85.422 |    10.347 |
| mappo  | unseen-loss       | SAFE     |         85.797 |    10.613 |

## Gate use and genuine clearances

| algo   | case              |   genuine_clears |   genuine_warning_clears |   accept_overrides |   reject_overrides |
|:-------|:------------------|-----------------:|-------------------------:|-------------------:|-------------------:|
| dqn    | late-control      |                0 |                        0 |                  0 |                  0 |
| dqn    | mixed-recovery    |             6889 |                     5372 |                945 |               2934 |
| dqn    | no-hazard-control |                0 |                        0 |                273 |               1424 |
| dqn    | persistent        |                0 |                        0 |                389 |               3181 |
| dqn    | rapid-recovery    |            12870 |                    10020 |               1322 |               2824 |
| dqn    | unseen-corruption |             5480 |                     3983 |               1505 |               3058 |
| dqn    | unseen-delay      |             6043 |                     4765 |                447 |               3290 |
| dqn    | unseen-loss       |             4174 |                     2886 |                866 |               2447 |
| mappo  | late-control      |                0 |                        0 |                  0 |                  0 |
| mappo  | mixed-recovery    |             6895 |                     5434 |                433 |               3847 |
| mappo  | no-hazard-control |                0 |                        0 |                123 |               2812 |
| mappo  | persistent        |                0 |                        0 |                150 |               3623 |
| mappo  | rapid-recovery    |            12793 |                    10107 |                607 |               3903 |
| mappo  | unseen-corruption |             5564 |                     4136 |                585 |               4546 |
| mappo  | unseen-delay      |             6106 |                     4822 |                240 |               4146 |
| mappo  | unseen-loss       |             4203 |                     2867 |                357 |               3607 |

## Locked validation settings

```json
{
  "dqn": {
    "LEARN": {
      "risk_limit": 0.3,
      "margin": 1.0
    },
    "AGE": {
      "age_limit": 8.0,
      "confidence": 0.4
    }
  },
  "mappo": {
    "LEARN": {
      "risk_limit": 0.3,
      "margin": 1.0
    },
    "AGE": {
      "age_limit": 8.0,
      "confidence": 0.6
    }
  }
}
```

## Reproduce

Use Linux/Python3.12; set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache` for this CPU workflow. From repository root, `bash setup_local.sh`, then `cd simulator` and `../.venv/bin/python run_recovery_gate_study.py --output out/recovery-gate-reproduction --workers 4`. From root regenerate this report with `.venv/bin/python simulator/report_recovery_gate_study.py --run simulator/out/recovery-gate-reproduction`. The runner refuses to overwrite an existing study directory. Model/checkpoint hashes, paired physical schedules and convoy accounting are checked during reporting.

Open `recovery_gate_report.pdf` or `index.html` for8 figures. `contrasts.csv` contains all140 intervals, `primary_decisions.csv` the co-required decisions, `summary.csv` every mean, `validation_selection.csv` all selection options, `prediction_diagnostics.csv` internal error, and `fixed_actor_ablation.csv` descriptive swaps. Raw CSV.gz, all80 final neural routing checkpoints, initial/refreshed gate estimators and training/causal labels are in the complete ZIP. No after-test retuning.
