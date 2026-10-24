# AIMRL

## Implemented pre-transmission mechanism pilot

A new radio reservation/intervention prototype is implemented and evaluated with
frozen routers: 1,104 factual episodes, 1,104 batched-priority reference episodes
and 3,017 isolated interventions. All 170 tests pass. Hindsight over the sampled
actions finds a 0.634-point delivery opportunity; this is not a deployed or
learned-controller result. The one-point superiority target remains unsupported.

- [Implemented behavior, results and remaining work](revision/pretransmission-opportunity-findings.md).
- [Three-figure PDF](deliverables/AIMRL-pretransmission-opportunity-figures.pdf).
- [Prototype, actor checkpoints and raw-results ZIP](deliverables/AIMRL-pretransmission-opportunity.zip).
- [All tables](revision/pretransmission-opportunity-results/README.md) and [protocol](revision/pretransmission-opportunity-protocol.md).

## Completed delivery-primary learned-routing experiment (v3)

Delivery improvement remains the primary objective. The corrected simulator
trains eight routing runs and causal packet-value gates, then evaluates 21,600
method episodes. LEARN achieves 67.151% on-time delivery versus 67.278% for the
same router accepting all reports. The declared superiority target is unmet;
all three corrected primary intervals include zero. All 153 tests pass.

- [Actual results, implemented changes and remaining gaps](revision/delivery-learning-findings.md).
- [Seven-figure PDF](deliverables/AIMRL-delivery-learning-figures.pdf).
- [Complete code, original uploads, checkpoints and raw-data ZIP](deliverables/AIMRL-delivery-learning-study.zip).
- [All tables and reproduction commands](revision/delivery-learning-results/README.md).
- [Reviewer coverage](revision/delivery-learning-reviewer-map.md) and [protocol](revision/delivery-learning-protocol.md).
- [Mathematical diagnosis and proposed next design](revision/delivery-mathematical-analysis.md): exact gain/loss decomposition, deadline-value control and fair confirmation requirements.

The sections below describe earlier preserved development stages. Their results
and downloadable archives remain historical evidence.

## Implemented timed-network revision and full development surface

The new model includes consequential closures/inspections, deadlines, local noisy
observations, training-fitted report validity and a real finite broadcast channel.
The study executes 63,072 method episodes across 19/51/131-node networks, with
864 response-surface cells and a matched admission ablation. VALUE saves about
76% of transmission bytes but loses on-time delivery to stronger scheduling
baselines. This is a planning development study, not confirmed MARL superiority.

- [Implemented changes, actual findings and remaining research gaps](revision/timed-network-findings.md).
- [Eight-figure PDF](deliverables/AIMRL-timed-network-figures.pdf).
- [Code, fitted interpreter, raw primary results and figures ZIP](deliverables/AIMRL-timed-network-study.zip).
- [All tables and reproduction commands](revision/timed-network-results/README.md).
- Full packet/decision trace archives are listed in the ZIP's TRACE_DOWNLOADS.json; the included fetch helper verifies and extracts them.

## Critical journal-readiness assessment

The present results do **not** support submitting the existing superiority claim.
A read-only audit of 518,400 routing decisions finds zero ALL/FRC/NONE next-hop
changes on the same frozen policies and zero blocked outgoing options offered.
An exact decision reference shows when freshness filtering helps, hurts or ties;
it is model validation, not a new network-performance result.

- [Scientific assessment and reviewer blockers](revision/journal-readiness-assessment.md).
- [Four diagnostic figures](deliverables/AIMRL-journal-readiness-figures.pdf).
- [Complete audit, code, parent models and raw-data ZIP](deliverables/AIMRL-journal-readiness.zip).
- [Tables](revision/journal-readiness/README.md), [protocol](revision/journal-readiness-protocol.md), and [next network acceptance contract](revision/journal-network-acceptance-contract.md).

## Original tabular AMMARL reproduction and repairs

The latest study returns to the submitted tabular Q-learning and fixed FRC gate.
Original AMMARL/IQL route scores reproduce 0.876/0.857, but these are not survival
probabilities: delivery is 100% and original M4 hazard use is zero. The repaired
43,200-episode comparison also finds no FRC advantage over accepting all reports.

- [What reproduced, what changed and the defensible claim](revision/original-tabular-findings.md).
- [Eight-figure PDF](deliverables/AIMRL-original-tabular-figures.pdf).
- [Complete code, original uploads, models and raw-results ZIP](deliverables/AIMRL-original-tabular-study.zip).
- [Tables and reproduction commands](revision/original-tabular-results/README.md).
- [Protocol](revision/original-tabular-protocol.md) and [offline figures](revision/original-tabular-results/index.html).

## Actor-aware fleet-value development

The latest development phase probes the actual frozen routing actor, predicts
fleet effects and permits one learned override per episode. MAPPO shows a small
development mean gain; DQN is weak and useful clearance acceptance remains
unresolved. This is not a new superiority confirmation or new routing training.

- [What changed, measured opportunity and actual findings](revision/actor-aware-development-findings.md).
- [All development tables and reproduction commands](revision/actor-aware-development-results/README.md).
- [Download six-figure PDF](deliverables/AIMRL-actor-aware-development-figures.pdf).
- [Download complete source, models and data ZIP](deliverables/AIMRL-actor-aware-development.zip).
- [Development protocol](revision/actor-aware-development-protocol.md).

## Dynamic-recovery gate redesign — completed experiment

The redesigned gate can accept and reject relative to SAFE, with bounded authority,
complete-inbox causal labels and physical reopening observations. Eight paired
training seeds per algorithm and five matched-trained methods produce 80 models.
The 102,400-episode held-out study does **not establish superiority** under the
predeclared corrected utility and delivery criteria. Read the interpretation
before using the figures as evidence.

- [What changed, actual results and defensible claim](revision/recovery-gate-findings.md).
- [All tables and reproduction commands](revision/recovery-gate-results/README.md).
- [Download eight-figure PDF](deliverables/AIMRL-recovery-gate-figures.pdf).
- [Download complete code, checkpoints and raw-data ZIP](deliverables/AIMRL-recovery-gate-study.zip).
- [Offline visual report](revision/recovery-gate-results/index.html).
- [Prospective protocol](revision/recovery-gate-protocol.md), [exact gate contract](simulator/RECOVERY_GATE_METHODS.md) and [reviewer coverage](revision/recovery-gate-reviewer-map.md).

## Decision-level diagnosis of the learned gate

The follow-up audits actual message decisions, exact accept/reject effects,
prediction transport, a simple warning-retention rule and genuine clearance
opportunities. Its findings are exploratory and preserve the matched study's
null primary result. No deployed gate or original final checkpoint was refitted.

- [What limits the learned gate and what should change next](revision/gate-decision-diagnosis-findings.md).
- [All diagnostic tables and seven figures](revision/gate-decision-diagnosis/README.md).
- [Download diagnostic figure PDF](deliverables/AIMRL-gate-decision-diagnosis-figures.pdf).
- [Complete diagnostic code, models, labels and replay data ZIP](deliverables/AIMRL-gate-decision-diagnosis.zip).
- [Diagnostic protocol](revision/gate-decision-diagnosis-protocol.md) and [targeted follow-up](revision/gate-decision-targeted-followup.md).

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
