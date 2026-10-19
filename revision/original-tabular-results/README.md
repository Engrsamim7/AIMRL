# Original tabular AMMARL-PI: reproduced and repaired

The study returns to hub-indexed independent Q-learning and a fixed FRC gate. Neural/learned-gate extensions are excluded. Source-file hashes are unchanged.

## Executed original-source results

| method       |   delivery_pct |   route_prior_score |   legacy_time_weighted_cost |
|:-------------|---------------:|--------------------:|----------------------------:|
| AMMARL       |     100.000000 |            0.876374 |                   50.703836 |
| AMMARL_NOGAT |     100.000000 |            0.875512 |                   50.504573 |
| B1           |     100.000000 |            0.682633 |                  136.718607 |
| B2           |     100.000000 |            0.682633 |                  136.718607 |
| B3           |     100.000000 |            0.682633 |                  136.718607 |
| IQL          |     100.000000 |            0.857023 |                   55.746522 |
| MAPPO_LABEL  |     100.000000 |            0.839465 |                   56.925910 |
| NC           |     100.000000 |            0.857023 |                   55.746522 |

AMMARL 0.876374 and IQL 0.857023 reproduce the rounded 0.876/0.857 presentation scores, but both deliver 100% and original M4 has zero hazard-buffer entries/uses. The original ungated result does not reproduce 0.851; IQL and NC are identical paths. Matching some numbers cannot attribute a communication effect or authenticate all presentation constants. Costs above are the original cost-times-travel-time metric, not nominal sums.

## Closest repaired pairs

|        seed |   delivery_difference_pp |   route_score_difference |   nominal_difference |   elapsed_difference |
|------------:|-------------------------:|-------------------------:|---------------------:|---------------------:|
|   42.000000 |                 0.000000 |                 0.000000 |             0.000000 |             0.000000 |
|  137.000000 |                 0.000000 |                 0.000000 |             0.000000 |             0.000000 |
|  271.000000 |                 0.000000 |                 0.000000 |             0.000000 |             0.000000 |
|  999.000000 |                 0.000000 |                 0.000000 |             0.000000 |             0.000000 |
| 1337.000000 |                 0.000000 |                 0.000000 |             0.000000 |             0.000000 |

Same original seed ranges/300-episode curriculum/scoring/evaluation epsilon 0.05. This is a bundle-of-repairs comparison, not a single-patch causal effect. Controlled refinements below use fresh independent training streams and greedy evaluation, so cross-layer differences must not be attributed solely to bug fixes.

## Matched tabular refinements

| scope            | weight     | sensing   | mode   |   episodes |   delivery_pct |   route_score |   nominal |   elapsed |   messages_sent |   hazard_score_applications |
|:-----------------|:-----------|:----------|:-------|-----------:|---------------:|--------------:|----------:|----------:|----------------:|----------------------------:|
| fresh-attributes | code       | mixed     | ALL    |       2400 |     100.000000 |      0.725781 | 14.005833 | 14.291758 |       94.700000 |                    4.925000 |
| fresh-attributes | code       | mixed     | FRC    |       2400 |     100.000000 |      0.725781 | 14.005833 | 14.291758 |       94.700000 |                    1.156667 |
| fresh-attributes | code       | mixed     | NONE   |       2400 |     100.000000 |      0.717594 | 13.994583 | 14.303453 |       94.650000 |                    0.000000 |
| fresh-attributes | code       | mixed     | TRAVEL |       2400 |     100.000000 |      0.717594 | 13.994583 | 14.303453 |       94.650000 |                    0.000000 |
| fresh-attributes | code       | uniform   | ALL    |       2400 |     100.000000 |      0.725781 | 14.005833 | 14.291758 |      103.550000 |                    0.000000 |
| fresh-attributes | code       | uniform   | FRC    |       2400 |     100.000000 |      0.725781 | 14.005833 | 14.291758 |      103.550000 |                    0.000000 |
| fresh-attributes | code       | uniform   | NONE   |       2400 |     100.000000 |      0.725781 | 14.005833 | 14.291758 |      103.550000 |                    0.000000 |
| fresh-attributes | code       | uniform   | TRAVEL |       2400 |     100.000000 |      0.725781 | 14.005833 | 14.291758 |      103.550000 |                    0.000000 |
| fresh-attributes | manuscript | mixed     | ALL    |       2400 |     100.000000 |      0.712448 | 13.919167 | 14.189708 |       94.600000 |                    4.820417 |
| fresh-attributes | manuscript | mixed     | FRC    |       2400 |     100.000000 |      0.712448 | 13.919167 | 14.189708 |       94.600000 |                    1.397917 |
| fresh-attributes | manuscript | mixed     | NONE   |       2400 |     100.000000 |      0.712448 | 13.919167 | 14.189708 |       94.600000 |                    0.000000 |
| fresh-attributes | manuscript | mixed     | TRAVEL |       2400 |     100.000000 |      0.712448 | 13.919167 | 14.189708 |       94.600000 |                    0.000000 |
| fresh-attributes | manuscript | uniform   | ALL    |       2400 |     100.000000 |      0.720635 | 13.930417 | 14.178014 |      104.450000 |                    0.000000 |
| fresh-attributes | manuscript | uniform   | FRC    |       2400 |     100.000000 |      0.720635 | 13.930417 | 14.178014 |      104.450000 |                    0.000000 |
| fresh-attributes | manuscript | uniform   | NONE   |       2400 |     100.000000 |      0.720635 | 13.930417 | 14.178014 |      104.450000 |                    0.000000 |
| fresh-attributes | manuscript | uniform   | TRAVEL |       2400 |     100.000000 |      0.720635 | 13.930417 | 14.178014 |      104.450000 |                    0.000000 |
| original-graph   | code       | mixed     | ALL    |        300 |     100.000000 |      0.883083 | 13.462667 | 13.732022 |       96.400000 |                    5.266667 |
| original-graph   | code       | mixed     | FRC    |        300 |     100.000000 |      0.883083 | 13.462667 | 13.732022 |       96.400000 |                    1.406667 |
| original-graph   | code       | mixed     | NONE   |        300 |     100.000000 |      0.883917 | 13.540667 | 13.848378 |       96.000000 |                    0.000000 |
| original-graph   | code       | mixed     | TRAVEL |        300 |     100.000000 |      0.883917 | 13.540667 | 13.848378 |       96.000000 |                    0.000000 |
| original-graph   | code       | uniform   | ALL    |        300 |     100.000000 |      0.883083 | 13.462667 | 13.732022 |       96.400000 |                    0.000000 |
| original-graph   | code       | uniform   | FRC    |        300 |     100.000000 |      0.883083 | 13.462667 | 13.732022 |       96.400000 |                    0.000000 |
| original-graph   | code       | uniform   | NONE   |        300 |     100.000000 |      0.883083 | 13.462667 | 13.732022 |       96.400000 |                    0.000000 |
| original-graph   | code       | uniform   | TRAVEL |        300 |     100.000000 |      0.883083 | 13.462667 | 13.732022 |       96.400000 |                    0.000000 |
| original-graph   | manuscript | mixed     | ALL    |        300 |     100.000000 |      0.890917 | 13.437333 | 13.714289 |       96.800000 |                    4.956667 |
| original-graph   | manuscript | mixed     | FRC    |        300 |     100.000000 |      0.890917 | 13.437333 | 13.714289 |       96.800000 |                    1.570000 |
| original-graph   | manuscript | mixed     | NONE   |        300 |     100.000000 |      0.890917 | 13.437333 | 13.714289 |       96.800000 |                    0.000000 |
| original-graph   | manuscript | mixed     | TRAVEL |        300 |     100.000000 |      0.890917 | 13.437333 | 13.714289 |       96.800000 |                    0.000000 |
| original-graph   | manuscript | uniform   | ALL    |        300 |     100.000000 |      0.890083 | 13.359333 | 13.597933 |       97.200000 |                    0.000000 |
| original-graph   | manuscript | uniform   | FRC    |        300 |     100.000000 |      0.890083 | 13.359333 | 13.597933 |       97.200000 |                    0.000000 |
| original-graph   | manuscript | uniform   | NONE   |        300 |     100.000000 |      0.890083 | 13.359333 | 13.597933 |       97.200000 |                    0.000000 |
| original-graph   | manuscript | uniform   | TRAVEL |        300 |     100.000000 |      0.890083 | 13.359333 | 13.597933 |       97.200000 |                    0.000000 |

Actual delivery is separated from route-prior score, which is not survival probability. The inherited model does not simulate attack-induced killing. Original graph scope conditions on graph 42; fresh graphs change attributes within the same small topology family. Mixed sensing, scoring specification and traversal-scaled freshness are labeled scientific refinements. No general superiority or convergence claim follows.

## Reproduce

Use `bash setup_local.sh`, then from simulator run `../.venv/bin/python run_original_tabular_study.py --output out/original-tabular-reproduction --workers 4`. From root run `.venv/bin/python simulator/report_original_tabular_study.py --run simulator/out/original-tabular-reproduction`. Use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache`. A fresh study directory is required.

Open original_tabular_report.pdf or index.html for eight figures. original_reproduction.csv and presentation_comparison.csv distinguish source outcomes from fixed anchors; closest_repair_pairs.csv gives matched repairs; repaired_summary.csv/all_conditions.csv retain every refinement/regime; contrasts.csv holds all 48 corrected intervals; communication.csv separates activity. Raw original/repaired training, models, validation, test outcomes and all 17 uploaded source files are in the ZIP. The protocol and findings describe unresolved reviewer/manuscript issues.
