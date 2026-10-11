# Updated experiment protocol

This rerun replaces four-episode smoke training with 60 episodes per model and standard optimizer settings (not smoke mode). All four algorithms, three communication modes and three training seeds are retained: 36 models and 2,160 training episodes, with 12 convoys. This budget is exploratory; inspect curves rather than assuming convergence.

Training graphs: 1–40. Scenario selection uses validation graphs 100–104 only. Fresh held-out evaluation graphs: 400–409, five episodes each. Every method sees matching schedules and configuration within each scenario. Scaling uses graphs 500–502, two episodes each, at 39/51/203/483 nodes, with population and attack budget held fixed; this is a size-transfer check, not constant threat density. Exact FIR uses random threats with exogenous spoofing, graphs 600–604, two episodes each; reactive/targeted attacks are excluded from controlled FIR.

Shared congested settings: hub capacity 1, service time 2, 12 convoys staggered by .5. Threat pressure: attack rate .9, duration 40–80, budget 12, destruction probability .7. Genuine confidence has mean .85 and SD .1; it remains a simulated score, not authentication. Training uses random attacks, exogenous spoof rate 4, message delay 2 and loss .2.

Held-out scenarios:

1. Random attacks, no spoof/loss, message delay 1.
2. Random attacks, exogenous spoof rate 8, loss .2, delay 4.
3. Reactive attacks and targeted spoof rate 8, loss .2, delay 4.

Matching graph/episode seeds fixes schedules and random initialization. In the reactive scenario, attack and spoof targets respond to policy behavior, so their realized sequences may differ between methods; this is part of the measured closed-loop effect. Only the random/exogenous message-replay experiment enforces identical exogenous attack traces over each branch's shared time interval.

The spoofing ablation independently varies heuristic response strength 0/4/8/12/24, static/travel freshness, eta .4/1/2, and every freshness/relevance/confidence switch combination. It does not add that heuristic penalty to deep action scores.

CPU quota is four cores. Training runs in four independent processes, each with one PyTorch thread. Python memory profiling is opt-in: updated wall times exclude allocation instrumentation, unlike the old smoke timing figures. Manifests record the source version and all parameters; model-level intermediate curves and checkpoints are saved as training progresses.

The scaling and message-replay runs use the disrupted/exogenous-spoof configuration (delay 4, loss .2, spoof rate 8). Scaling runs alongside the heuristic ablation and replay workers, each limited to one CPU thread, within the four-core quota. Runtime is a descriptive measurement on this shared cloud machine, not a controlled hardware benchmark.

Artifacts are stored under `simulator/out/reviewer-rerun-v2/`. Independent `train-dqn`, `train-ppo`, `train-ippo` and `train-mappo` directories retain each worker's manifest and curves. `train/` is a documented aggregation of those same 36 checkpoints and 2,160 episodes, not an additional training run. Evaluation directories are `random`, `spoof`, `reactive` and `scaling`; the remaining experiments are `ablate` and `fir`.

Each executed command is saved in its manifest's `argv`, along with its complete configuration. To reproduce, run those commands from `simulator/` using fresh output directories and the newly trained checkpoint path. Final artifact audit and figure generation:

```bash
python validate_results.py out/reviewer-rerun-v2
python plot_updated_results.py --run-root out/reviewer-rerun-v2 --output ../revision/updated-visualisations
```

Delivery uncertainty is reported using paired graph-cluster bootstrap intervals. Training-seed variability is shown separately; graph-only intervals are conditional on the trained models. Stronger results are not a guarantee of gate superiority. All original data and visualisations remain preserved.
