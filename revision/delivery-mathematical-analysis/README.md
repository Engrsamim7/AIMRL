# Delivery gap: a retrospective mathematical audit

This supplement audits existing v3 test results and includes a controlled
development ablation on saved validation contexts. It runs no new held-out
test. Read the
[mathematical diagnosis and proposed design](../delivery-mathematical-analysis.md)
for the equations, assumptions, limits and next implementation sequence.

| Contribution across 3,456 paired method episodes | On-time convoy change | Delivery change |
|---|---:|---:|
| Helpful rejections | +147 | +0.531684 percentage points |
| Harmful rejections | -182 | -0.658275 percentage points |
| Net effect | -35 | -0.126591 percentage points |

Among 1,567 selected rejections, average predicted harm frequency was 2.1456%
and observed harm frequency was 9.7639%. This selected-case discrepancy is not
a global false-rejection rate or a conditional coverage guarantee.

- `analysis.json`: numeric decomposition and exact input hashes.
- `training_signal_by_seed.csv`: the rare-effect training evidence available to each gate.
- `multioutput_target_scale.csv`: the delivery target supplies 1.60–2.56% of total target variance in the current equally averaged multi-output criterion; this is a hypothesis for ablation, not a demonstrated cause.
- `selected_rejection_predictions_by_seed.csv`: predicted versus realized selected effects.
- `validation_pairing_and_spread.csv`: 192 actor rows per setting share only 24 physical validation contexts; the spread is descriptive, not a new confidence interval.
- `delivery_gap_decomposition.pdf` / `.png`: a two-panel explanatory figure.
- `simulator/analyze_delivery_gap.py`: reruns the audit from the repository root.

The separate controlled **development** ablation fits the value target in convoy
counts, converts predictions back and evaluates identical validation contexts.
At fixed setting 1, delivery changes from 57.2266% to 57.0313%; no observed gain.
This is not a new held-out test or a demonstrated cause of the original failure.
See `value_scale_development_ablation.csv`, its paired rows and verification JSON.
The script `simulator/run_delivery_value_scale_ablation.py` reproduces it in a
fresh output folder. Original frozen actors, gates, labels and the development
ablation models are included in the supplement for that purpose.

The supplemental ZIP includes the audit script, mathematical note, outputs and
input table snapshots, including the small saved validation table. It does not
replace the complete simulator/model/data ZIP from the earlier study. The
audit needs NumPy, pandas and matplotlib, already present in the project
environment. Run:

```bash
MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
python simulator/analyze_delivery_gap.py
```
