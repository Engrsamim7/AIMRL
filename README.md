# AIMRL

## Matched-training gate study — 19 October 2026

This follow-up tests whether learned message filtering adds benefit beyond
identical conservative safeguards when the routing actors adapt under each
method. It uses eight paired seeds per algorithm, four factorial arms, new
layouts and corruption settings, and a predeclared pooled delivery endpoint.
Read the actual primary result before interpreting case-specific improvements.
The earlier frozen-model experiments remain separately available below.

- [New results, primary intervals and all conditions](revision/matched-gate-results/README.md).
- [Eight new figures in one PDF](deliverables/AIMRL-matched-gate-figures.pdf).
- [Complete new code, 64 checkpoints and raw data ZIP](deliverables/AIMRL-matched-gate-study.zip).
- [Offline visual report](revision/matched-gate-results/index.html).
- [Protocol published before testing](revision/matched-gate-protocol.md).
- [Figure interpretation guide](revision/matched-gate-figure-guide.md).
- [Updated bounded manuscript claim](revision/matched-gate-claim-draft.md).

## Fresh study: physical communication opportunities and learned message value

This study introduces randomized multi-fork layouts with physically leading
scouts, fresh DQN/MAPPO training, and actor-specific utility models learned from
complete-episode message interventions. ALL and FRC use the same actor weights
and shared report interpreter as VALUE; FRC is tuned on validation data. Nine
predeclared cases include favorable conditions and counterexamples, alongside an
original-topology transfer check. Results support only the named conditions and
baselines shown in the corrected comparisons.

- [Latest frozen neural cover-traffic stress and four figures](revision/cover-traffic-results/README.md).
- [Latest neural stress PDF](revision/cover-traffic-results/cover_traffic_report.pdf).
- [All 20 research figures in one PDF](deliverables/AIMRL-research-figures.pdf).
- [Guarded gate results and eight visualizations](revision/guarded-research-results/README.md).
- [Download combined figure PDF](revision/guarded-research-results/research_opportunity_report.pdf).
- [Offline figure report](revision/guarded-research-results/index.html).
- [Preserved unconstrained learned gate and its failures](revision/research-opportunity-results/README.md).
- [Complete fresh-study code, weights, data and figures ZIP](deliverables/AIMRL-research-opportunity-study.zip).
- [Mechanisms, physical cases, assumptions and reproducibility](revision/research-opportunity-methods.md).
- [Draft replacement manuscript claim and evidence limits](revision/research-manuscript-claim-draft.md).

## Earlier audit: why the adaptive results were equivalent

The communication opportunity audit replays the existing frozen schedules with
diagnostic logging, isolated decision probes and complete-episode interventions.
It checks when warnings are novel, concern the proposed route, and could support
a feasible detour. The original evaluated simulator and gate source are unchanged;
this is diagnosis, not new training or a fresh superiority claim.

- [Audit findings and six figures](revision/communication-opportunity-audit/README.md).
- [Combined audit PDF](revision/communication-opportunity-audit/communication_opportunity_report.pdf).
- [Offline audit visualization report](revision/communication-opportunity-audit/index.html).
- [Complete code, weights, prior results and audit data ZIP](deliverables/AIMRL-communication-audit.zip).
- [Proposed fresh experiments](revision/communication-audit-next-experiments.md).

## Adaptive gate: latest implementation and fresh tests

The adaptive gate estimates routing sensitivity, combines uncertain sender evidence,
learns local agreement, and protects warnings against uncorroborated clear reports.
It also has an adapter for the existing frozen DQN/PPO/IPPO/MAPPO actors.

- [Download complete adaptive code, data and baseline weights](deliverables/AIMRL-adaptive-gate.zip).
- [Latest results and eight figures](revision/adaptive-gate-results/README.md).
- [Combined PDF](revision/adaptive-gate-results/adaptive_gate_report.pdf).
- [Offline HTML report](revision/adaptive-gate-results/index.html).
- [Method, baselines, limitations and reproduction](revision/adaptive-gate-methods.md).
- [Preserved negative prototype](revision/adaptive-gate-v1-results/README.md).

The controlled single-impersonation fixture improves delivery over fixed and
soft-fusion baselines. Broader network and frozen-actor comparisons do not establish
statistical superiority. Multiple forged identities can defeat the quorum; legitimate
clearance can incur a detour. These outcomes are retained in the report.

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
