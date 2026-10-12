# AIMRL

## Current reviewer revision using the original submission topology

The supplied pre-submission code has been audited and preserved. The current
revision uses its recovered 19-node, 64-edge network, explicit scout/follower
sensing, genuine delayed hazard reports, matched filtering/response comparisons,
and newly trained DQN/PPO/IPPO/MAPPO models.

- [Download current complete code, models and results](deliverables/AIMRL-reviewer-revision.zip).
- [Current results and nine figures](revision/reviewer-revision-results/README.md).
- [Combined PDF](revision/reviewer-revision-results/reviewer_revision_report.pdf).
- [Offline HTML](revision/reviewer-revision-results/index.html): download and open locally.
- [Changes, protocol and reproduction commands](revision/reviewer-code-changes.md).
- [Original code audit](revision/submission-code-audit/README.md).
- [Current raw CSVs and fresh models](simulator/out/reviewer-revision-v2).

```bash
bash setup_local.sh
source .venv/bin/activate
cd simulator
python -m pytest -q tests_core.py tests_revision.py tests_manuscript_gate.py tests_reviewer_model.py
python run_reviewer_revision.py --output out/my-reviewer-run
python run_gate_fixtures.py --output out/my-reviewer-run/gate-fixtures
python report_reviewer_revision.py --input out/my-reviewer-run --output ../revision/my-reviewer-results
```

Current weights compare communication modes with frozen fitted routing models.
These experiments do not establish universal gate superiority or convergence.
Historical runs below require their archived source and weights; the current
sensor contract has a new source/observation version.

## Historical complete reconstruction

The `reviewer-complete-model-20261012` branch delivers the reconstructed model
and the longer 300-episode-per-model experiment suite together:

- [Download the complete ZIP](deliverables/AIMRL-complete.zip) (use GitHub's **Download raw file** button).
- [Open the results and all nine figures](revision/complete-visualisations/README.md).
- [Combined vector PDF](revision/complete-visualisations/updated_results_report.pdf).
- [Illustrative routes and event timing PDF](revision/complete-visualisations/simulation_episode_report.pdf).
- [Offline HTML report](revision/complete-visualisations/index.html): download it and open it in your browser.
- [Complete model and source map](revision/complete-model.md).
- [Executed experiment protocol](revision/complete-protocol.md).
- [Raw data, checkpoints, logs and manifests](simulator/out/complete-model-v1).

From a downloaded checkout or extracted package, use Python 3.12 on Linux/WSL:

```bash
bash setup_local.sh
source .venv/bin/activate
cd simulator
python -m pytest -q tests_core.py tests_revision.py
python run_complete.py --output out/my-new-run --figures ../revision/my-new-figures
```

The offline report is self-contained and requires no server. Complete source
and artifacts do not establish convergence, real-world applicability or a
consistent gate advantage; the report retains negative and inconclusive results.

## Earlier reconstruction and diagnostics

The reviewer-driven reconstruction is in [simulator/](simulator/README.md).
It provides locally observed deep routing agents, congestion-aware communication
freshness, delayed reactive threats, exact single-message shadow replay, explicit
cost/count metrics, and reproducible training/evaluation commands.

See the [methods contract](simulator/METHODS.md) and
[reviewer coverage](revision/simulator-reviewer-coverage.md). Short validation
runs establish executable behavior, not publication-ready performance claims.

The latest exploratory rerun and regenerated charts are documented in
[updated results](revision/updated-results.md), with its
[matched experiment protocol](revision/rerun-protocol.md) and
[seven-figure report](revision/updated-visualisations/README.md).

The original `ammarl2-pi.zip` and `README (5).md` are preserved as legacy material.
Original checkpoints and numerical results are incompatible with the revised
observation and simulator semantics; retrain and regenerate results.
