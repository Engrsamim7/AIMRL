# Delivery-primary learned routing and causal gate

Read ../delivery-learning-findings.md for the supported claim and limitations. No bandwidth savings are substituted for delivery.

| method       |   episodes |   routing_models |   on_time_pct |   delivery_pct |   elapsed |   mean_rejections |   rejections |   routing_calls |
|:-------------|-----------:|-----------------:|--------------:|---------------:|----------:|------------------:|-------------:|----------------:|
| NONE         | 3456.00000 |          8.00000 |      64.59057 |       96.72309 |  46.26569 |           0.00000 |      0.00000 |    378408.00000 |
| ALL          | 3456.00000 |          8.00000 |      67.27792 |       97.14627 |  45.14665 |           0.00000 |      0.00000 |    367252.00000 |
| FIXED_RX     | 3456.00000 |          8.00000 |      64.95949 |       96.74117 |  46.19686 |         239.08218 | 826268.00000 |    377662.00000 |
| KEEP_ONE     | 3456.00000 |          8.00000 |      67.27792 |       97.14988 |  45.14463 |           0.75694 |   2616.00000 |    367244.00000 |
| KEEP         | 3456.00000 |          8.00000 |      67.33218 |       97.07755 |  45.23114 |          14.43663 |  49893.00000 |    368511.00000 |
| LEARN        | 3456.00000 |          8.00000 |      67.15133 |       97.11733 |  45.20771 |           0.45341 |   1567.00000 |    367967.00000 |
| PLANNER_WARN |  432.00000 |          0.00000 |      64.93056 |       96.81713 |  45.73697 |           0.00000 |      0.00000 |     46755.00000 |
| PLANNER_RAW  |  432.00000 |          0.00000 |      64.78588 |       96.81713 |  46.19112 |           0.00000 |      0.00000 |     46727.00000 |

| method   | baseline    |   difference_pp |   lower_pp |   upper_pp | corrected_positive   | mean_reaches_1pp   |   draws |   correction |
|:---------|:------------|----------------:|-----------:|-----------:|:---------------------|:-------------------|--------:|-------------:|
| LEARN    | ALL         |        -0.12659 |   -0.50275 |    0.22786 | False                | False              |   20000 |            3 |
| LEARN    | KEEP        |        -0.18084 |   -0.71615 |    0.36531 | False                | False              |   20000 |            3 |
| LEARN    | PLANNER_RAW |         2.36545 |   -1.18996 |    6.32719 | False                | True               |   20000 |            3 |

## Reproduce

Install the base environment with `bash setup_local.sh`, then `.venv/bin/python -m pip install -r requirements-actor-aware.txt` for gate fitting. From root run `.venv/bin/python simulator/run_delivery_learning.py --output simulator/out/delivery-learning-reproduction --workers 4`; then `.venv/bin/python simulator/report_delivery_learning.py --run simulator/out/delivery-learning-reproduction`. A fresh run folder is required. Use `MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`.

The runner uses the preserved timed-network calibration file, included in the ZIP. Models are inference checkpoints, not complete optimizer/replay resumes. Eight routing seeds and gates are stored separately. One selected initial actor, if present, is explicit in selected_routing_models.csv. Source and training records of both stopped development passes are archived; neither reached held-out testing. The final comparison uses the corrected v3physics and retrained actors only.

Run `.venv/bin/python -m pytest -q simulator/tests_*.py` for the complete test suite.

Open delivery_learning_report.pdf or index.html for seven figures. Raw training, checkpoint validation, causal labels with both fleet branches, gate validation, held-out convoy outcomes and gate decisions are included. test_environment_manifest.json reconstructs and hash-checks every held-out closure schedule, weighted graph and convoy departure/deadline. sampled_training_opportunity.csv is a hindsight diagnostic over sampled training interventions only, not a deployable oracle or an upper bound over unobserved packets. Identified packet effects use the one-rejection-per-fleet constraint; their denominator is actual rejected packets, not all transmissions.
