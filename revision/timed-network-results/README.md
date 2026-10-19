# Timed-network development and response surface

Read ../timed-network-findings.md before interpreting performance. This is a new physical/communication revision with a fitted report interpreter and shared planning actor. It is not newly trained MARL or a confirmation of the original manuscript claim.

## pilot

| method         |   episodes |   on_time_pct |   delivery_pct |   attempted_bytes |   completed_bytes |   elapsed |   nominal |   encounters |   peer_changes |   routing_calls |   radio_airtime |
|:---------------|-----------:|--------------:|---------------:|------------------:|------------------:|----------:|----------:|-------------:|---------------:|----------------:|----------------:|
| AGE_ALL        |   972.0000 |       93.3256 |        95.2932 |         4887.6379 |         4844.9712 |   41.9695 |   29.2566 |      22.5957 |      2749.0000 |      94939.0000 |         38.6820 |
| FRC            |   972.0000 |       93.2742 |        95.0360 |         4941.4321 |         4898.7654 |   41.9743 |   29.2186 |      23.2058 |       747.0000 |      95107.0000 |         38.6701 |
| LATEST         |   972.0000 |       93.3385 |        95.3189 |         4884.4774 |         4842.2058 |   41.9470 |   29.2594 |      22.5412 |      2840.0000 |      94898.0000 |         38.6687 |
| NONE           |   972.0000 |       93.0170 |        94.8688 |            0.0000 |            0.0000 |   42.2519 |   29.1299 |      23.8580 |         0.0000 |      96018.0000 |          0.0000 |
| RAW_ALL        |   972.0000 |       94.0458 |        95.7948 |         4741.9918 |         4699.3251 |   41.2895 |   29.5048 |      20.3395 |      3418.0000 |      92708.0000 |         38.6880 |
| VALUE          |   972.0000 |       93.6471 |        95.4090 |         1036.6420 |         1030.3210 |   41.8137 |   29.2299 |      22.0689 |      3654.0000 |      94375.0000 |         19.4984 |
| VALUE_PRIORITY |   972.0000 |       93.5700 |        95.4990 |         4891.1276 |         4848.6584 |   41.8120 |   29.2930 |      21.7963 |      4653.0000 |      94196.0000 |         38.7751 |
| WARN_PRIORITY  |   972.0000 |       93.5571 |        95.5247 |         4891.6543 |         4848.9877 |   41.7752 |   29.2688 |      21.8169 |      5129.0000 |      94146.0000 |         38.7381 |

| method   | baseline       | endpoint           |   difference |      lower |      upper | scope                                                                      |
|:---------|:---------------|:-------------------|-------------:|-----------:|-----------:|:---------------------------------------------------------------------------|
| VALUE    | RAW_ALL        | on_time            |      -0.3987 |    -0.9902 |     0.1543 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | AGE_ALL        | on_time            |       0.3215 |     0.0514 |     0.6687 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | LATEST         | on_time            |       0.3086 |     0.0386 |     0.6687 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | WARN_PRIORITY  | on_time            |       0.0900 |    -0.2058 |     0.3987 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | VALUE_PRIORITY | on_time            |       0.0772 |    -0.1029 |     0.2958 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | RAW_ALL        | attempted_tx_bytes |   -3705.3498 | -4777.9572 | -2754.4198 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | AGE_ALL        | attempted_tx_bytes |   -3850.9959 | -5008.4741 | -2789.3251 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | LATEST         | attempted_tx_bytes |   -3847.8354 | -5010.5811 | -2781.9358 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | WARN_PRIORITY  | attempted_tx_bytes |   -3855.0123 | -5016.1053 | -2790.7819 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | VALUE_PRIORITY | attempted_tx_bytes |   -3854.4856 | -5017.6230 | -2788.9366 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |

## surface

| method         |   episodes |   on_time_pct |   delivery_pct |   attempted_bytes |   completed_bytes |   elapsed |   nominal |   encounters |   peer_changes |   routing_calls |   radio_airtime |
|:---------------|-----------:|--------------:|---------------:|------------------:|------------------:|----------:|----------:|-------------:|---------------:|----------------:|----------------:|
| AGE_ALL        |  6912.0000 |       68.2346 |        87.9991 |         6151.5093 |         6108.8426 |   53.1901 |   28.5597 |      71.7902 |     11405.0000 |    1223240.0000 |         46.0283 |
| FRC            |  6912.0000 |       68.2219 |        87.8074 |         6180.1481 |         6137.4815 |   53.2367 |   28.4231 |      72.9831 |      3866.0000 |    1225818.0000 |         45.9984 |
| LATEST         |  6912.0000 |       68.2418 |        87.9991 |         6134.6852 |         6092.5926 |   53.1727 |   28.5750 |      71.5813 |     12382.0000 |    1222004.0000 |         45.9317 |
| NONE           |  6912.0000 |       67.5673 |        87.4837 |            0.0000 |            0.0000 |   53.7622 |   28.2929 |      74.5221 |         0.0000 |    1238490.0000 |          0.0000 |
| RAW_ALL        |  6912.0000 |       68.9091 |        88.3898 |         6005.7870 |         5963.1296 |   52.4248 |   28.7266 |      69.6869 |     18484.0000 |    1206545.0000 |         45.9499 |
| VALUE          |  6912.0000 |       68.3919 |        88.0588 |         1477.0185 |         1467.7130 |   53.0472 |   28.5797 |      70.8579 |     13829.0000 |    1216712.0000 |         22.8572 |
| VALUE_PRIORITY |  6912.0000 |       68.6343 |        88.2017 |         6132.1481 |         6089.7870 |   52.8606 |   28.6459 |      70.3387 |     18256.0000 |    1214105.0000 |         45.8634 |
| WARN_PRIORITY  |  6912.0000 |       68.6578 |        88.1637 |         6134.9259 |         6092.3796 |   52.8753 |   28.6421 |      70.4339 |     20858.0000 |    1214887.0000 |         45.9038 |

| method   | baseline       | endpoint           |   difference |      lower |      upper | scope                                                                      |
|:---------|:---------------|:-------------------|-------------:|-----------:|-----------:|:---------------------------------------------------------------------------|
| VALUE    | RAW_ALL        | on_time            |      -0.5172 |    -0.9115 |    -0.1465 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | AGE_ALL        | on_time            |       0.1573 |    -0.0289 |     0.3979 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | LATEST         | on_time            |       0.1501 |    -0.0289 |     0.3780 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | WARN_PRIORITY  | on_time            |      -0.2658 |    -0.4069 |    -0.1429 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | VALUE_PRIORITY | on_time            |      -0.2423 |    -0.3581 |    -0.1284 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | RAW_ALL        | attempted_tx_bytes |   -4528.7685 | -6204.3618 | -3019.3424 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | AGE_ALL        | attempted_tx_bytes |   -4674.4907 | -6431.6315 | -3064.5208 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | LATEST         | attempted_tx_bytes |   -4657.6667 | -6414.5039 | -3049.5331 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | WARN_PRIORITY  | attempted_tx_bytes |   -4657.9074 | -6412.1801 | -3051.3938 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |
| VALUE    | VALUE_PRIORITY | attempted_tx_bytes |   -4655.1296 | -6409.3900 | -3049.3921 | descriptive paired graph/environment bootstrap;10000draws;not confirmatory |

## Reproduce

From extracted root: `bash setup_local.sh`; use `.venv/bin/python simulator/run_timed_network_development.py --output simulator/out/timed-network-reproduction --workers 4`, then `.venv/bin/python simulator/run_timed_network_surface.py --parent simulator/out/timed-network-reproduction --output simulator/out/timed-network-surface-reproduction --workers 4`, then `.venv/bin/python simulator/run_timed_network_ablation.py --parent simulator/out/timed-network-reproduction --output simulator/out/timed-network-ablation-reproduction --workers 4`; then `.venv/bin/python simulator/report_timed_network.py --pilot simulator/out/timed-network-reproduction --surface simulator/out/timed-network-surface-reproduction --ablation simulator/out/timed-network-ablation-reproduction`. Use fresh run directories and `MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Default report output is revision/timed-network-results.

Open timed_network_report.pdf or index.html for eight figures. All condition tables, factor tables, contrasts, common-probe calibration data and full surface graphs/closure schedules are retained. ZIP includes raw calibration, validation, episodes, convoys, routing decisions and completed packet records. Attempted bytes charge 64 bytes for every started frame; completed bytes and actual partial-frame airtime are separate. The model uses abstract time units, no destruction, and one fitted interpreter; no independent routing-training seeds or convergence evidence are supplied.
