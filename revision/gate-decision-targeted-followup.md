# Exploratory follow-up to the decision diagnosis

The initial diagnosis showed that the chronological disagreement sample usually changed no route. Inspecting the complete public candidate records then identified a sampling limitation: early irrelevant reports can fill the per-episode cap before a later consequential clearance.

Before the additional replay outcomes are inspected, add the following **exploratory targeted follow-up**. Reuse the same 512 COMBINED trajectories and replay every disagreement satisfying either public-state condition: the actor's action probe changes when the packet is included, or the packet concerns an existing peer warning on a publicly reachable edge. Do not select using origin, current truth, future delivery or utility. The initial all-candidate records identify 106 DQN and 48 MAPPO candidates under this predicate on these bounded-size graphs; the rerun must recover the same set.

Each selected packet receives the original full-inbox accept/reject intervention, with unchanged actor/value weights and all future messages. The branch using the actual decision must reproduce the factual convoy outcomes. Preserve the initial capped diagnosis separately. Identify overlap between the initial and targeted replay samples and do not count them as independent replicates. This improves coverage of consequential disagreements **within this diagnostic subset**, not population coverage or confirmation of a redesigned gate.

```bash
cd simulator
MPLCONFIGDIR=/tmp/aimrl-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 ../.venv/bin/python audit_gate_relevant_disagreements.py --parent out/matched-gate-study --output out/gate-decision-targeted-audit --workers 4
```
