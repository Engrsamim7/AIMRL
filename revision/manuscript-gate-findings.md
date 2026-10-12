# First manuscript-mechanism diagnostic

Executed 4,500 local-only training episodes (three synthetic graphs, five initialization seeds, 300 episodes each), then 24,000 matched frozen-Q evaluation episodes (two scenario families, 20 test episodes, 40 variants). All 33 tests pass. This is a synthetic mechanism diagnosis, not reproduction of the submitted numerical table.

## Finding

Every evaluated candidate has `peer_used = false`. For each fixed penalty pair, NC, ALL and full FRC therefore have identical routing outcomes. The filtering contrasts and their bootstrap intervals are zero. The zero-response control is also identical for every episode. This is evidence of an inactive communication pathway in this tested formulation, not gate superiority, convergence or equivalence in general.

Local sensing refreshes all outgoing reports at each decision. These updates have the decision timestamp, even when the sensor reports an unrevealed edge as unblocked. Delayed peer reports carry older observation timestamps. The rule that newer own evidence supersedes peer evidence makes all candidate peer reports unusable. Meanwhile, manuscript relevance requires a report to match an immediately available outgoing corridor. Reports about remote future edges cannot affect this score. Those two rules together remove peer influence in this diagnostic. Removing freshness or confidence cannot recover it.

Controlled fixtures confirm that a fresh warning can change the selected edge when no newer local report is present, whereas stale, low-confidence and off-next-hop reports do not. Thus the score/gate implementation has an actionable path; the broad benchmark's sensing and precedence contract never exercises it.

## Reconcile with submission code before changing the mechanism

Check whether unrevealed observations meant unknown rather than known-open; whether observations receive their actual observation time or are refreshed at every decision; whether accepted peer warnings override newer local clear readings; whether scouts possess a different sensing radius or reveal delay; whether corridor-level reports refer to threats beyond the next edge; and whether the CC2 fixture injects communication independently of sensing. These are consequential model choices. Do not change them just to obtain a positive gate result.

The repository's preserved original archive has GNN routing and route-plan-based filtering. It does not establish the manuscript's tabular-Q/fork-scoring experiment. The exact pre-submission source and scenario configurations would resolve this mismatch and the printed reward-sign ambiguity.

## Limits and reproducibility

The diagnostic uses 17-node generated networks, a fixed target, three simultaneous convoy slots, and a per-slot hub/edge Q approximation. Training and test episode schedules are disjoint on the same three graphs; this is not unseen-topology testing. Q learning uses a negative nominal/threat step penalty and explicit death penalty; the manuscript's positive printed threat term and terminal failure handling are ambiguous. Exploration decays with a shared policy decision counter. These choices are explicitly historical/diagnostic, not claims of faithfully reproducing every submitted detail.

`used_candidates` records whether candidate scoring consumed a peer report. General simulator acceptance/rejection counters are not updated by this separate comparator and must not be interpreted as its gate-use statistics. Packet sent/delivered/lost counts remain simulator counts. Receiver filtering alone is not transmission bandwidth reduction.

Run from `simulator/` after installing the existing project dependencies:

```bash
python -m pytest -q tests_core.py tests_revision.py tests_manuscript_gate.py
python run_manuscript_gate.py --output out/my-manuscript-diagnostic
```

Outputs are in `simulator/out/manuscript-gate-diagnostic/`: raw episode/convoy records, fitted Q tables, training records, contrasts, manifest, PNG/PDF and README. Earlier complete-model-v1 outputs and core source are unchanged.
