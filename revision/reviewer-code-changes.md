# Implemented reviewer follow-up using the supplied submission code

This revision modifies the executable reconstruction, preserves the supplied originals, and uses the recovered `make_network(seed=42)` graph (19 nodes, 64 directed edges, original costs, priors, capacities and corridor IDs). It does not reuse the presentation pipeline's fixed numbers, simulated learning curves or significance calculations.

## Implementation changes

- `Sim.observation_edges(convoy)` is now the common sensor-coverage API for local report updates, travel estimates and actor features. The default keeps the previous uniform coverage. `ReviewerSim` adds declared scout/follower coverage without reading hidden hazards to choose the mask. Missing sensor coverage leaves a report unknown; it does not fabricate a fresh clear reading.
- The general model broadcasts genuine blocked/cleared reports through actual latency/loss events. Mixed-coverage M4 masks are deterministic functions of topology, independently of attacks. Scouts have two-hop sensing, followers one-hop sensing with documented static gaps. Uniform-coverage cases remain separate comparators.
- Relevance can use the historical own-information route or public reachability to retain warnings about alternative routes a learned actor might choose. The conservative reachable rule is intentionally broad on strongly connected graphs; its benefit and admission rate must be measured, not presumed.
- All compared heuristic modes use identical own/peer response strength. Eight F/R/C masks at strengths 0/8/12 separate filtering from hazard response; zero-strength equality is checked every episode.
- Actor visibility masks and belief features reflect the same sensing contract. Deep algorithms use documented Double DQN/PPO/IPPO/MAPPO implementations rather than the supplied custom tabular softmax baseline labeled MAPPO. The observation version is now `local-belief-v3-declared-sensors`; older checkpoints are rejected and freshly trained weights are delivered.
- The bidirectional original network permits transit through other base nodes. Only arrival at the assigned target terminates a convoy. This is an explicit configuration (`allow_base_transit`) and is identical across compared policies.
- Exact single-message replay accepts a simulator factory and copies the complete role/sensor configuration. Controlled replay remains limited to exogenous hazards/spoofs; reactive cases are policy comparisons.
- Episode state resides in new convoy objects; reports/inboxes do not persist across episodes. Future-dated packets are rejected. Departure-time expiry includes hub wait/service.
- Raw CSVs drive every report. Nominal cost, elapsed travel/wait/service, actual delivery/destruction/censoring, and route-prior survival proxy remain separate. Matched common-survivor costs/times, integer counts, Dijkstra bounds and timing decompositions are audited.

## Executed protocol

The active runner is `simulator/run_reviewer_revision.py`. Twenty all-communication models (four algorithms, five training seeds) each train for 300 episodes on the recovered original topology under alternating clean/disrupted and uniform/mixed/reactive configurations: 6,000 training episodes per executed version. At evaluation the same fitted weights are frozen and used with none/all/gate communication. This isolates the inference-time information effect, not separately trained communication strategies.

Gate validation uses 10 independent episode schedules across four scenario families and a nine-setting eta/confidence grid. In v1, unconstrained delivery selection chose eta=.4/confidence=.4 and admitted no warnings on disrupted held-out episodes. This result is preserved, not relabeled as superiority. V2 requires at least 5% aggregate genuine-report admission during validation before ranking delivery; ties use smaller eta then smaller confidence threshold. This is an explicit mechanism-activity requirement, not a theoretical guarantee. It was added after the v1 diagnosis, so v2 uses new training, validation, evaluation and replay schedules.

V2 seeds are training `1100000 + seed*10000 + episode`, validation `2100000 + episode`, held-out `3100000 + episode`, CC2 `4100000 + episode`, M4 replay `5100000 + episode`. The selected thresholds and admission counts are saved. Each held-out scenario has 50 schedules, five heuristic configurations and 60 fitted model/mode instances: 13,000 evaluation episodes, 39,000 convoy records. Uncertainty resamples paired episodes and training seeds on a fixed topology, not independent graph samples.

The response/filter ablation has 2,400 episodes. CC2 has 900 episodes across 1/4/8-unit delays and 0/20% packet loss, plus 40 packet interventions. CC2 explicitly gives scouts observation links to two hidden fork corridors and fixed public priors; it measures actual blocked-edge losses with a persistent exogenous block, not the original route-threat-only score. It is a controlled communication-critical fixture, not operational validation. M4 replay covers all processed packets in four independently seeded episodes per tested mode. Scaling covers 39/51/203/483-node synthetic graphs with two schedules and five heuristic policies; it is descriptive inference scaling with fixed population/attack budget.

## Reproduce

From repository root, use `bash setup_local.sh` and activate `.venv`, then:

```bash
cd simulator
python -m pytest -q tests_core.py tests_revision.py tests_manuscript_gate.py tests_reviewer_model.py
python run_reviewer_revision.py --output out/my-reviewer-run
python run_gate_fixtures.py --output out/my-reviewer-run/gate-fixtures
python report_reviewer_revision.py --input out/my-reviewer-run --output ../revision/my-reviewer-results
```

Each run requires a fresh output directory. The runner records source/network hashes, optimizer counts, parameters, raw schedules and executed outcomes. Tests and report audits establish implementation consistency, not superiority or convergence.

## Remaining scientific/manuscript work

Assess convergence and validation-only algorithm hyperparameter sensitivity; separately train each communication mode if claiming total training benefit; expand independent graph/topology and operational-data coverage; calibrate confidence assumptions; broaden scenario sensitivity. The current results must determine claim wording. Rewrite manuscript equations, units, comparator descriptions, figures/tables and point-by-point reviewer response. Original presentation constants remain unverified without their raw logs; do not carry them into the new paper as evidence.

## Controlled filtering probes

`run_gate_fixtures.py` adds 450 independent fixture episodes and 80 complete packet interventions. It compares accurate reports alone, a fresh low-confidence false clear report, and a fresh high-confidence false clear report. The gate uses the manuscript confidence threshold .6 for these probes, separate from the M4-selected threshold. Packet labels are evaluation-only. These deliberately constructed cases expose a filtering benefit and its failure boundary; they are not general performance evidence.

```bash
python run_gate_fixtures.py --output out/my-reviewer-run/gate-fixtures
python report_reviewer_revision.py --input out/my-reviewer-run --output ../revision/my-reviewer-results
```

Run the fixture command before building the complete report. Rejected misleading packets are replayed as well as accepted packets. A high confidence score is not authentication or proof of truth.
