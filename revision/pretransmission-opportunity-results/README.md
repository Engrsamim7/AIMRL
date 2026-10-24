# Pre-transmission mechanism pilot

Development opportunity measurement with frozen routing, not learned-controller superiority. Hindsight chooses after seeing future outcomes and is not deployable.

| arm                                            |   on_time_pct |
|:-----------------------------------------------|--------------:|
| Original VALUE priority / ALL receiver         |      69.79167 |
| Batched VALUE priority / ALL receiver          |      69.63315 |
| Sampled hindsight best action (not deployable) |      70.42572 |

| action   |   interventions |   helpful |   harmful |   no_delivery_effect |   mean_gain_when_available_pp |   gain_sum |   mean_gain_over_all_episodes_pp |
|:---------|----------------:|----------:|----------:|---------------------:|------------------------------:|-----------:|---------------------------------:|
| defer    |       975.00000 |  18.00000 |  17.00000 |            940.00000 |                      -0.01282 |   -0.12500 |                         -0.01132 |
| drop     |      1023.00000 |  42.00000 |  47.00000 |            934.00000 |                      -0.18328 |   -1.87500 |                         -0.16984 |
| swap     |      1019.00000 |  18.00000 |  17.00000 |            984.00000 |                      -0.01227 |   -0.12500 |                         -0.01132 |

Read ../pretransmission-opportunity-findings.md and ../pretransmission-opportunity-protocol.md for assumptions and limitations. Open pretransmission_report.pdf or index.html for three figures.

Rerun from root with `.venv/bin/python simulator/run_pretransmission_opportunity.py --output simulator/out/pretransmission-reproduction`; then `.venv/bin/python simulator/report_pretransmission_opportunity.py --run simulator/out/pretransmission-reproduction`. Install using setup_local.sh plus requirements-actor-aware.txt for the historical full test suite. Use MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1.
