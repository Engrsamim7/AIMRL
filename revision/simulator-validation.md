# Reconstruction validation

This report records functional smoke validation of the rebuilt simulator, not final scientific performance results.

- Source SHA-256: `21843a345b3e23aa5b94bfa75aacf35252ed05e8d60cab79372ed1ea109a0046`.
- Tests: **28 passed** (`tests_core.py` and `tests_revision.py`), with no failed or skipped tests.
- Training: **24 checkpoints**, four algorithms × three communication modes × two seeds; four episodes per checkpoint, **96 training episodes**. Every model performed optimizer updates. Smoke settings reduce DQN warmup/batch and PPO epochs.
- Held-out graph-size inference: **248 episode runs** across 39, 51, 203 and 483 nodes on graph seeds 300/301; 8 convoys per run. Models loaded from newly trained versioned checkpoints.
- Reactive attacks / targeted spoofing: **62 episode runs**, graph seeds 302/303, with every baseline and new checkpoint evaluated.
- Gate/response-strength ablation: **204 episode runs**, static/travel freshness, eight gate-component combinations, two eta values and strengths 0/12/24. At strength zero, communication/filter variants produced identical routing outcomes.
- Full-message replay: **413 single-message interventions** across two held-out graphs and all/gate communication; every decision-processed message replayed, including rejected ones. **3 receiver paths changed**. The complete random-attack sequence matched over the shared time interval in every branch. A separate controlled test proves that one report can prevent destruction.
- Artifact audit: completed manifests, identical source versions, expected record counts, positive optimizer updates, finite losses, matched convoy schedules, nominal shortest-path bounds, integer encounter counts, successful time decompositions and full replay denominators passed.

## Reproduce the artifact audit

From `/workspace/AIMRL/simulator`:

```bash
/workspace/aimrl-venv/bin/python validate_results.py out/reviewer-validation
```

The run manifests, raw convoy records, training curves, checkpoints and audit JSON are in `simulator/out/reviewer-validation/` (ignored generated outputs). Methods and reviewer coverage are saved in ordinary source files. Earlier diagnostic directories are not the validated result set; source-version checks reject their superseded checkpoints.

## Limits

Four-episode training establishes working optimization and serialization only. It cannot establish convergence, comparative superiority, real-world military applicability or robustness guarantees. The two-graph smoke intervals are not adequate manuscript evidence. Full training, validation-only tuning and adequately replicated experiments remain necessary before replacing the manuscript's tables and claims. The existing ZIP/manuscript results were not reused or described as validation of the new semantics.
