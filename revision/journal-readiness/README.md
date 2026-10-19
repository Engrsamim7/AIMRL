# Journal-readiness diagnostics

These files do not establish a new network performance claim. Read ../journal-readiness-assessment.md first.

- decision_audit.csv and all_audit_conditions.csv: all 518,400 routing calls from a read-only replay of the original-family study. Existing episode metrics reproduce, Q checkpoints remain fixed, and every factual score probe matches the actual next hop.
- exact_reference_cells.csv: all 432 analytical decision conditions; exact_reference_branches.csv: all 3,456 probability-weighted states. Costs are expected travel loss under a declared two-state closure model with known sensor accuracy and dynamics. They are not MARL training or field observations.
- journal_readiness.pdf and index.html: four diagnostic figures.
- verification.json: counts, scope and code hashes.

From root, with the base pinned environment: python simulator/audit_tabular_decisions.py --parent simulator/out/original-tabular-study --output simulator/out/tabular-decision-audit-reproduction --workers 4; then python simulator/report_journal_readiness.py --audit simulator/out/tabular-decision-audit-reproduction. Use fresh output directories and MPLCONFIGDIR=/tmp/aimrl-mpl XDG_CACHE_HOME=/tmp/aimrl-cache OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1. Original-study parent models and raw episode metrics are included in the diagnosis ZIP. See ../journal-readiness-protocol.md for the prospective grid and diagnostic limitations.
