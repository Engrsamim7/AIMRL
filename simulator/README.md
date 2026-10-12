# Latest adaptive gate study

Use `run_adaptive_experiments.py`, `run_clearance_stress.py`, `run_adaptive_actor_eval.py`, then `report_adaptive_results.py`. Read [adaptive methods](../revision/adaptive-gate-methods.md) and [results](../revision/adaptive-gate-results/README.md). The packaged baseline weights are reused; no new offline training is claimed. Adaptive sender agreement updates within each episode.

# Current reviewer follow-up

Use `run_reviewer_revision.py` for the original-topology, declared-sensor experiments and `report_reviewer_revision.py` for audited raw-data plots. See [changes and protocol](../revision/reviewer-code-changes.md), [current results](../revision/reviewer-revision-results/README.md), and `tests_reviewer_model.py`. Prior checkpoints are incompatible with the new sensor contract; their archived packages remain historical artifacts.

# Reconstructed AMMARL simulator

## Complete current delivery

The completed 300-episode suite includes 36 fitted models, 10,800 training
episodes, all matched evaluations, full replay and nine generated figures.
Use [the complete model guide](../revision/complete-model.md),
[executed protocol](../revision/complete-protocol.md) and
[current results](../revision/complete-visualisations/README.md).
The downloaded complete package contains the current suite; earlier diagnostic
result references below describe historical runs rather than extra packaged data.

Portable setup and the complete workflow:

```bash
# From the repository/package root:
bash setup_local.sh
source .venv/bin/activate
cd simulator
python -m pytest -q tests_core.py tests_revision.py
python validate_results.py out/complete-model-v1
python run_complete.py --output out/my-new-run --figures ../revision/my-new-figures
```

Open the downloaded `revision/complete-visualisations/index.html` in a browser
for the offline report. The original source archive and earlier outputs remain
preserved in the cloud workspace and repository history.

## Reconstruction details and earlier diagnostic workflows

This source reconstructs the simulator in response to the reviews of IoT-66126-2026. It is a new experimental version, not a reproduction of the submitted paper's numerical claims. The original ZIP, unpacked legacy results and trained weights remain untouched outside this directory.

Run commands from `/workspace/AIMRL/simulator`:

```bash
source /workspace/aimrl-venv/bin/activate
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
python -m pytest -q tests_core.py tests_revision.py
```

The seven dependencies in `requirements.txt` are already installed in that environment. For another machine, use Python 3.12 and install those dependencies in a virtual environment; CPU PyTorch is sufficient. No external service or credential is required. Output directories are ignored by Git; preserve experiment artifacts separately when sharing results.

## What changed

- Deep actors consume local hazard summaries, report age/confidence, unknown-vs-open indicators, local congestion and elapsed time. Public topology/cost/prior threat are known; remote live queues/flow and true attacks are hidden from actors.
- All deep baselines use the same multi-convoy simulator, observation schema, reachable outgoing-edge mask and configurable reward. Shared PPO, independent per-convoy IPPO, and shared MAPPO with a centralized critic are explicitly distinct. DQN uses masked Double-DQN bootstrapping. Semi-Markov discounting uses elapsed time between decisions.
- The default freshness limit is `min(tau_stale, eta * estimated corridor traversal time)`. Local flow updates traversal estimates; remote flow is unknown and uses nominal estimates. Retained reports are rechecked after waiting/service. Static and historical ETA-based rules remain explicit comparators.
- Filtering and hazard response are separate. Heuristics use the same additive blocked-edge cost for own/peer beliefs; strength zero disables this response. Learned actors receive beliefs as features and do not inherit that heuristic penalty.
- Individual message effects use deterministic shadow continuation from the receiver's decision, with exactly one packet suppressed. Full shared-time attack sequences are checked. Controlled FIR uses random attacks and exogenous spoofing; reactive/targeted threats are evaluated separately.
- Nominal path cost, realized elapsed time, queue wait, service, delivery, destruction, censoring, all blocked entries and unexpected blocked entries are separate fields. Per-convoy counts are integers. Delivered paths must respect the nominal Dijkstra lower bound for the identical depot/target.
- Sparse graph message passing supports the 39/51/203/483-node synthetic networks without dense adjacency allocation. These are synthetic benchmarks, not validated military maps.

See [METHODS.md](METHODS.md) for the mathematical contract and [reviewer coverage](../revision/simulator-reviewer-coverage.md) for remaining publication work.

## Reproducible experiments

Every command requires a **new** output directory, writes raw records and a manifest with source hash, configuration and library versions, and preserves failures in the manifest. Existing outputs are never overwritten. Checkpoints from the old archive are incompatible and must be retrained. Checkpoints also require the current source hash, so code changes require a new training run.

Quick functional validation (short training is **not** convergence evidence):

```bash
python run_experiments.py train --output out/my-smoke/train --smoke --convoys 8 --episodes 4 --seeds 0 1
python run_experiments.py evaluate --output out/my-smoke/evaluate --smoke --convoys 8 --graphs 300 301 --eval-episodes 1 --sizes 39 51 203 483 --checkpoints out/my-smoke/train
python run_experiments.py ablate --output out/my-smoke/ablate --smoke --convoys 8 --graphs 300 301 --eval-episodes 1 --strengths 0 12 24 --etas .4 1 --spoof 2 --delay 2
python run_experiments.py fir --output out/my-smoke/fir --smoke --convoys 8 --graphs 300 301 --eval-episodes 1 --spoof 2 --max-messages 12
```

A full initial protocol (expensive; tune only on separate validation graphs, inspect convergence before finalizing training budgets):

```bash
python run_experiments.py train --output out/main/train --episodes 300 --seeds 0 1 2
python run_experiments.py evaluate --output out/main/evaluate --checkpoints out/main/train --sizes 39 51 203 483
python run_experiments.py evaluate --output out/main/reactive --checkpoints out/main/train --sizes 39 203 483 --adversary reactive --spoof 8 --spoof-mode targeted
python run_experiments.py ablate --output out/main/ablate --spoof 8 --delay 4 --loss .4
python run_experiments.py fir --output out/main/fir --spoof 2
```

Training graphs are seeds 1–40; evaluation graph seeds must be at least 300. IPPO has an independent trained network per convoy slot: keep the evaluation population at the trained size. Graph-size transfer retains that population; scaling convoy population requires a separately trained IPPO population and an explicitly documented protocol. Record actual decisions and optimizer updates, since equal episodes do not imply equal update counts across algorithms. Other populations, training against reactive threats and matched clean/adversarial training are configurable, but cannot be inferred from clean-trained tests alone.

`--max-messages` reports FIR for a deterministic diagnostic prefix only. Omit it to evaluate every processed message; full replay can be expensive. FIR is undefined with zero messages. Route-based FIR matching the original metric and delivery-based FIR are separate outputs. They measure realized single-message interventions, not an expectation over unseen random futures.

The evaluation runner reports paired graph-cluster bootstrap intervals for delivery differences against NC, after averaging episodes and training seeds within graphs. These intervals describe sampled graph uncertainty conditional on the trained models; they do not quantify retraining uncertainty. Per-seed/raw outcomes are retained for further analysis. Python allocation peak and process-wide RSS high-water mark are named separately; neither is presented as isolated per-model native tensor allocation.

## Files

- `ammarl2/sim.py`: event queue, queueing, threats, packets, outcomes.
- `ammarl2/policies.py`: local reports, filtering, departure-time expiry and heuristic response.
- `ammarl2/learn.py`: observation contract, sparse GNNs, independent/shared actors, training.
- `ammarl2/counterfactual.py`: single-message shadow replay.
- `ammarl2/metrics.py`: denominators, nominal lower bounds and paired survivor comparisons.
- `run_experiments.py`: training, held-out evaluation/scaling, factorial gate/strength ablations and FIR.
- `tests_revision.py`: reviewer-focused correctness and optimizer-update tests.
- `legacy_scripts/`: historical scripts/documentation retained for reference. Their original assumptions and numerical claims do not describe this reconstruction; use the new runner for results.

## Validated reconstruction

The current reconstruction passed 28 tests, trained 24 diagnostic checkpoints,
and completed multi-size, reactive, factorial-ablation and full-message replay
checks. See [the validation report](../revision/simulator-validation.md).
Audit the generated artifacts with:

```bash
python validate_results.py out/reviewer-validation
```

## Updated exploratory rerun

The later `out/reviewer-rerun-v2` run uses 60 episodes per model with standard
optimizer settings, three training seeds, and 12 convoys. See the
[protocol](../revision/rerun-protocol.md),
[result interpretation](../revision/updated-results.md), and
[updated figures](../revision/updated-visualisations/README.md).
These results replace the earlier smoke figures for exploratory comparisons;
they do not establish convergence or a general gate advantage.

```bash
python validate_results.py out/reviewer-rerun-v2
python plot_updated_results.py --run-root out/reviewer-rerun-v2 --output ../revision/updated-visualisations
```
