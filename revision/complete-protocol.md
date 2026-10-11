# Complete model experiment protocol

This protocol extends the earlier 60-episode exploratory run to 300 episodes per model with standard optimization. It does not alter simulator dynamics, actor information or gate semantics to manufacture better outcomes. It uses all four algorithms (DQN/PPO/IPPO/MAPPO), three communication modes (none/all/gate), and three training seeds: 36 models and 10,800 training episodes. Population is 12 convoys in both training and inference; IPPO retains the independently trained convoy slots.

Training uses graph seeds 1–40. Previous validation graphs 100–104 were used only to select threat pressure. The new held-out comparison uses graphs 700–709, five episode seeds per graph. Graph-size transfer uses graphs 800–802, two episodes each at 39/51/203/483 nodes. Exact message replay uses graphs 900–904, two episodes each for all/gate, with every processed packet replayed. These graph sets are disjoint from the earlier held-out runs; no parameter is tuned on their outcomes.

Shared settings: hub capacity 1, service time 2, departure staggering .5; attack rate .9, simultaneous budget 12, durations 40–80, destruction probability .7; genuine confidence mean .85/SD .1. Training uses random attacks with exogenous spoof rate 4, report delay 2 and loss .2. Confidence is a simulated score, not authentication.

The three matched held-out scenarios are random attacks with delay 1/no loss/no spoof; random attacks with delay 4/loss .2/exogenous spoof rate 8; and reactive attacks with delay 4/loss .2/targeted spoof rate 8. Matching graph/episode seeds fixes schedules and initialization. Realized reactive/targeted attack traces depend on policy behavior, as part of the closed-loop outcome. They are not claimed to be fixed exogenous attack tapes.

Scaling, ablation and exact message replay use the disrupted/exogenous-spoof scenario. Scaling retains fixed population and attack budget, so larger graphs have changing threat density. It tests graph-size transfer, not larger-network training or robustness at constant density. The ablation evaluates all freshness/relevance/confidence switch combinations, static/travel freshness, eta .4/1/2, and response strengths 0/4/8/12/24. It changes the heuristic response factor independently of gate filtering, not deep action scores.

Controlled replay suppresses exactly one delivered packet before its receiver decision, retaining the complete copied state and verifying all exogenous attacks over the shared time interval. Rejected packets remain in the intervention denominator. Receiver and total-episode effects are kept separately; message effects need not add up. Reactive/targeted threats are excluded from this controlled intervention.

`simulator/run_complete.py` runs four one-thread workers within the four-core CPU quota, preserves every command/log/manifest, aggregates copies of the same 36 checkpoints, executes the six experiment stages, audits the raw/summary results and builds seven comparison figures plus a self-contained HTML report. The report also records the first fixed held-out disrupted episode for DQN-GATE training seed 0, with a network/route figure and exact travel/wait/service/packet timing. Instrumented convoy outcomes must match the existing evaluation rows, and phase durations must sum to the recorded totals. This single episode is illustrative and is not used as a comparative performance estimate. Runtime excludes allocation instrumentation and describes a shared cloud machine. Equal episode budgets do not imply equal decision or optimizer-update counts; both are recorded.

Delivery intervals resample graph clusters conditional on fitted models; learned gate-versus-all intervals resample matched graph and training-seed clusters. Three training seeds give limited retraining uncertainty. All intervals are exploratory and unadjusted for multiple comparisons. Training curves and final-window diagnostics are descriptive; convergence is not presumed from a fixed 300-episode budget. Positive, negative and inconclusive gate effects must all be reported.

The implementation and local package are complete executable research artifacts. Realistic geographic/operational data, exact reconstruction of the submitted topology, hyperparameter sensitivity, manuscript rewriting and final publication claims remain distinct work.

Run from `simulator/` with Python 3.12/CPU PyTorch:

```bash
python run_complete.py --episodes 300 --output out/complete-model-v1 --figures ../revision/complete-visualisations
```

Existing output directories are refused. Use new directory names for reproduction. See `METHODS.md` for the mathematical contract and the run manifests for exact parameters and versions.
