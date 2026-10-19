# Actor-aware development results

This is an algorithm-development audit on new training-distribution layouts and tapes. It uses16 existing frozen SAFE-trained routing actors, not new routing-training seeds or a matched-retraining confirmation. The prior null recovery study is unchanged.

## Paired exploratory differences

| algo   | endpoint   | baseline   |   difference |   exploratory_lower |   exploratory_upper | interpretation                                   |
|:-------|:-----------|:-----------|-------------:|--------------------:|--------------------:|:-------------------------------------------------|
| dqn    | utility    | SAFE       |       0.0115 |             -0.7327 |              0.7940 | development only; no corrected superiority claim |
| dqn    | utility    | TREE_BASE  |       0.1810 |             -0.0900 |              0.6092 | development only; no corrected superiority claim |
| dqn    | delivery   | SAFE       |       0.0781 |             -0.8984 |              1.1328 | development only; no corrected superiority claim |
| dqn    | delivery   | TREE_BASE  |       0.2734 |             -0.1172 |              0.8594 | development only; no corrected superiority claim |
| mappo  | utility    | SAFE       |       0.4464 |             -0.0359 |              1.0423 | development only; no corrected superiority claim |
| mappo  | utility    | TREE_BASE  |       0.2418 |             -0.0524 |              0.8439 | development only; no corrected superiority claim |
| mappo  | delivery   | SAFE       |       0.6641 |              0.0000 |              1.4453 | development only; no corrected superiority claim |
| mappo  | delivery   | TREE_BASE  |       0.3516 |              0.0000 |              1.1719 | development only; no corrected superiority claim |

Intervals are exploratory95% crossed seed/layout bootstrap intervals,20,000 draws; no multiplicity-adjusted superiority conclusion is made. All methods share the same frozen routing actor per seed. The old-feature forest has the same fitting data, estimator family, override rule/budget and setting grid as the actor-aware forest.

## All pooled means

| algo   | method      |   delivery_pct |   utility |   overrides |   accept_overrides |   reject_overrides |
|:-------|:------------|---------------:|----------:|------------:|-------------------:|-------------------:|
| dqn    | ACTOR_AWARE |        93.1250 |   21.5219 |         139 |                  0 |                139 |
| dqn    | AGE         |        93.0469 |   21.5104 |           0 |                  0 |                  0 |
| dqn    | ALL         |        92.0703 |   20.8292 |           0 |                  0 |                  0 |
| dqn    | KEEP        |        92.7344 |   21.2533 |           0 |                  0 |                  0 |
| dqn    | SAFE        |        93.0469 |   21.5104 |           0 |                  0 |                  0 |
| dqn    | TREE_BASE   |        92.8516 |   21.3409 |         187 |                  3 |                184 |
| mappo  | ACTOR_AWARE |        93.7500 |   21.9742 |         103 |                  0 |                103 |
| mappo  | AGE         |        93.3984 |   21.7726 |           0 |                  0 |                  0 |
| mappo  | ALL         |        92.0313 |   20.7761 |           0 |                  0 |                  0 |
| mappo  | KEEP        |        92.9688 |   21.4276 |           0 |                  0 |                  0 |
| mappo  | SAFE        |        93.0859 |   21.5278 |           0 |                  0 |                  0 |
| mappo  | TREE_BASE   |        93.3984 |   21.7324 |         187 |                  2 |                185 |

## Labels and opportunities

| algo   | split       |   labels |   relevant |   consequential |   positive |   negative |
|:-------|:------------|---------:|-----------:|----------------:|-----------:|-----------:|
| dqn    | audit       |     1314 |        418 |             230 |        261 |        209 |
| dqn    | calibration |     1222 |        326 |             162 |        199 |        169 |
| dqn    | fit         |     5214 |       1630 |             707 |        922 |        822 |
| mappo  | audit       |     1313 |        417 |             228 |        256 |        201 |
| mappo  | calibration |     1188 |        292 |             167 |        167 |        164 |
| mappo  | fit         |     5146 |       1562 |             701 |        866 |        824 |

The sampled hindsight reference selects at most one privileged best flip from sampled packets per episode. It is not deployable or a global bound. Its delivery tradeoff is in sampled_opportunity.csv. Zero immediate action change does not prove zero future effect. Tree dispersion is heuristic, not calibrated safety.

## Locked settings

```json
{
  "dqn": {
    "TREE_BASE": {
      "beta": 0.0,
      "margin": 0.0,
      "delivery_tolerance": 0.0
    },
    "ACTOR_AWARE": {
      "beta": 0.0,
      "margin": 0.0,
      "delivery_tolerance": 0.0
    }
  },
  "mappo": {
    "TREE_BASE": {
      "beta": 0.0,
      "margin": 0.0,
      "delivery_tolerance": 0.0
    },
    "ACTOR_AWARE": {
      "beta": 0.0,
      "margin": 0.5,
      "delivery_tolerance": 0.0
    }
  }
}
```

## Reproduce

Run `bash setup_local.sh`, then `.venv/bin/python -m pip install -r requirements-actor-aware.txt`. Use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache`. From `simulator/`, run `../.venv/bin/python run_actor_aware_development.py --output out/actor-aware-reproduction --workers 4` (parent recovery SAFE checkpoints must be available). From root regenerate with `.venv/bin/python simulator/report_actor_aware_development.py --run simulator/out/actor-aware-reproduction`. Existing study directories are never overwritten.

Open actor_aware_development.pdf or index.html for six figures. All tables, selected paired branch labels, factual baseline outcomes, estimator arrays and locked settings accompany the full source ZIP. No new general or bounded superiority claim follows from these exploratory comparisons. See ../actor-aware-development-findings.md for the research decision.
