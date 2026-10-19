# Decision diagnosis after the matched-training null result

This is exploratory mechanism diagnosis, not a new superiority trial. Preserve every original checkpoint, gate setting and result. No new labels fit a deployed estimator, and no positive outcome is assumed.

The executed design is also saved as `simulator/out/gate-decision-diagnosis/design.json` with source hashes.

## Scope specified before replay

Use both algorithms, all eight training seeds, mechanism layouts 59000/59001 (three/four forks), all eight declared conditions and original mechanism episodes 0/1. These 512 COMBINED trajectories are a deterministic subset of the already published diagnostic study, not fresh confirmation. Reproduce their recorded per-convoy outcomes exactly. Capture every eligible packet's original learned prediction, safeguard rule, final decision and public features without modifying factual actions.

Compare COMBINED admission with the safeguards-only decision **on the same preceding packet interpretation**. This prevents differences in earlier inbox processing being mistaken for direct value-model decisions. Eligible candidates exclude duplicate, superseded, stale and suppressed packets. Retain total processed-message counts as well.

Per episode, select the first two packets where learned filtering changes the safeguards-only decision, the first warning whose rejection the guard overrides, the first clearance whose admission the guard overrides, and the first remaining agreement. Select by public decision category and chronology only, never by true origin or realized effect. Report category totals, selected counts and coverage. These stratified chronological samples are not representative population effect estimates.

For each selected eligible packet, copy the complete state before its routing decision and run two full futures: force final admission versus force final rejection for that packet only. Retain earlier and later inbox packets, all subsequent transmissions, observations and events, and identical initial random-generator states. Preserve the true learned prediction in audit records even when forcing a decision. Check exogenous attack logs over shared time, unchanged departure/target schedules and exactly one intervention hit. Record receiver delivery, elapsed time and utility, team outcomes, next action and complete path differences.

For the first selected disagreement and first selected warning override per episode, also replay a training-style variant: remove later packets from the current inbox in both branches, while preserving future transmissions. Compare these with the corresponding full-inbox effects to diagnose credit masking and message redundancy. Conditional message effects need not add up to the overall gate effect.

Compare a simple static rule on the same COMBINED-trained actors/tapes: never let a peer clearance erase a fresh peer warning, even if two claimed sources corroborate it. Own observations and the existing TTL still apply. This is a fixed-actor diagnostic, not a retrained baseline or a significance claim. Evaluate whether genuine reopening clearances actually occur, rather than assuming the benchmark supplies them.

## Prediction transport after actor learning

Reconstruct each of sixteen original 300-episode ALL warmup actors using the exact published seed, layouts, cases, optimizer settings and tapes. Require its network hash to match the recorded warmup hash before any analysis. Freeze it. Original final checkpoints remain unchanged.

Generate sixteen fresh ALL label episodes each for the recovered warmup actor and its adapted COMBINED actor: new layouts 61000–61015, balanced two/three forks and all eight training conditions; tapes `66000000 + seed*10000 + episode`. Use the original chronological-prefix label routine without modification. Evaluate the **same original fitted estimator**, with no refitting, on each dataset. Report error against a zero-value predictor, target distributions, packet counts and variation across actor/seed pairs.

Warmup and adapted actors may visit different states and receive different useful packets, even on shared physical tapes. An error increase would diagnose failed prediction transport; it would not isolate staleness as the cause of the pooled null result. An error decrease would count against the proposed staleness explanation. Likewise, comparing full-inbox versus prefix credit is a separate check of the training target's relevance to deployment.

## Deliverables and limits

Publish candidate records, selected replay effects, all resulting convoy outcomes, fresh prediction labels, reconstructed warmup weights, original final weights/value models, code, tests, figures and a diagnosis with concrete design implications. Use a ZIP and the existing GitHub branch. No current test-based redesign will be described as independently confirmed. Any improved gate requires a new protocol and untouched confirmation conditions.

```bash
cd simulator
MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ../.venv/bin/python diagnose_gate_decisions.py --parent out/matched-gate-study --output out/gate-decision-diagnosis --workers 4
```
