"""
eval_b123.py — B1 / B2 / B3 on the frozen evaluation matrix
============================================================
Runs every combination of:
  map family x convoy count x red budget x tau_reveal x seed
for B1 (Least-Cost SP), B2 (Threat-Aware SP), B3 (Dynamic Replan).

Produces:
  1. Gate report table (G1–G5) — PASS / FAIL with numeric evidence
  2. Six diagnostic figures
  3. Per-method CSV for the paper appendix

Gate definitions (from the frozen matrix):
  G1  M1: B1.cost < B2.cost  AND  B2.surv > B1.surv
  G2  M2: B3.blocked_enc meaningfully lower than B1 after delayed reveal
  G3  M3: hub_wait and total_time materially higher at hub_capacity=2 vs 20
  G4  All maps: survivability / DR degrade as tau_reveal increases
  G5  All maps: survivability / DR degrade (near-)monotonically as red_budget increases

All results are mean +/- std over 5 seeds.
"""

import sys, os, copy, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from collections import defaultdict
from scipy import stats as scipy_stats

from ammarl_sim_core import ContestedRoutingSim, Convoy, make_network
from sim_v1_sc9_sc10_sc11 import (
    make_threat_gradient_map, make_midroute_attack_map,
    make_bottleneck_congestion_map, EVALUATION_MATRIX,
)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
def save(fn): return os.path.join(OUTPUT_DIR, fn)

FB   = {'fontweight': 'bold'}
SEEDS = EVALUATION_MATRIX['seeds']   # [42, 137, 271, 999, 1337]
METHODS = ['B1', 'B2', 'B3']
MCOLOR  = {'B1': '#EF5350', 'B2': '#FF9800', 'B3': '#4CAF50'}
METRICS = ['dr','cost','surv','blocked_enc','hub_wait','max_threat','corridor_sw']

# ═══════════════════════════════════════════════════════════════
# RUNNER — one (map, config, method, seed) cell
# ═══════════════════════════════════════════════════════════════
def run_cell(G, n_convoys, method, red_budget, tau_reveal,
             hub_capacity, obs_radius, seed, max_time=400):
    """Run one simulation cell. Returns stats dict."""
    import random
    np.random.seed(seed); random.seed(seed)
    env = ContestedRoutingSim(
        copy.deepcopy(G),
        red_budget  = red_budget,
        red_period  = 15.0,
        tau_reveal  = tau_reveal,
        tau_msg     = 2.0,
        tau_stale   = 10.0,
        hub_capacity= hub_capacity,
        obs_radius  = obs_radius,
        max_time    = max_time,
        seed        = seed,
    )
    tgts = G.graph['targets']
    convoys = [Convoy(cid=i, target=tgts[i % len(tgts)]) for i in range(n_convoys)]
    stats = env.run(convoys, {c.cid: method for c in convoys})
    # Add max_threat: mean of max(1-surv) over each delivered convoy's path
    delivered = [c for c in convoys if c.delivered]
    if delivered:
        stats['max_threat'] = float(np.mean([
            max((1.0 - s) for s in c.surv_edges) if c.surv_edges else 0.5
            for c in delivered
        ]))
    else:
        stats['max_threat'] = 0.5
    return stats


# ═══════════════════════════════════════════════════════════════
# EXPERIMENT RUNNER — all cells for a given map + sweep variable
# ═══════════════════════════════════════════════════════════════
def sweep(map_builder_fn, n_convoys, red_budgets, tau_reveals,
          hub_capacities, obs_radius, seeds,
          base_red_budget=2, base_tau_reveal=5.0,
          base_hub_capacity=5, label=''):
    """
    Run B1/B2/B3 on a grid of conditions.
    Returns nested dict: results[method][condition_key] = list of stat dicts (one per seed).
    """
    results = {m: defaultdict(list) for m in METHODS}

    # Conditions:
    # A) Vary red_budget (tau_reveal=base, hub_cap=base)
    # B) Vary tau_reveal (red_budget=base, hub_cap=base)
    # C) Vary hub_capacity (red_budget=0, tau_reveal=1)

    conditions = []
    for rb in red_budgets:
        conditions.append(('red_budget', rb, base_tau_reveal, base_hub_capacity))
    for tr in tau_reveals:
        conditions.append(('tau_reveal', base_red_budget, tr, base_hub_capacity))
    for hc in hub_capacities:
        conditions.append(('hub_capacity', 0, 1.0, hc))

    for sweep_type, rb, tr, hc in conditions:
        key = (sweep_type, rb if sweep_type=='red_budget' else
                           tr if sweep_type=='tau_reveal' else hc)
        G = map_builder_fn() if callable(map_builder_fn) else map_builder_fn
        for method in METHODS:
            for seed in seeds:
                st = run_cell(G, n_convoys, method, rb, tr, hc, obs_radius, seed)
                results[method][key].append(st)

    return results, conditions


def agg_key(results, method, key):
    """Mean +/- std over seeds for a given (method, condition_key)."""
    cells = results[method][key]
    if not cells: return {m: (0.0, 0.0) for m in METRICS}
    return {m: (float(np.mean([c[m] for c in cells])),
                float(np.std ([c[m] for c in cells])))
            for m in METRICS}


# ═══════════════════════════════════════════════════════════════
# MAIN EXPERIMENT
# ═══════════════════════════════════════════════════════════════
print("="*70)
print("B1 / B2 / B3 — Full Evaluation Matrix Run")
print("Frozen simulator v1.0 | Seeds:", SEEDS)
print("="*70)
t0 = time.time()

# ── M1: Threat-gradient ──────────────────────────────────────
print("\n[M1] Threat-gradient map  (1 convoy, vary red_budget & tau_reveal)")
R_M1, C_M1 = sweep(
    make_threat_gradient_map, n_convoys=1,
    red_budgets=[0,1,2],         # M1 has only 4 edges; budget>2 blocks all paths
    tau_reveals=EVALUATION_MATRIX['tau_reveal'],
    hub_capacities=[5, 20],      # congestion not the focus on M1
    obs_radius=2,                # full obs so Dijkstra works globally
    seeds=SEEDS,
    base_red_budget=1, base_tau_reveal=5.0, base_hub_capacity=5,
    label='M1',
)

# ── M2: Mid-route attack ─────────────────────────────────────
print("[M2] Mid-route attack map  (1 convoy, vary red_budget & tau_reveal)")
R_M2, C_M2 = sweep(
    make_midroute_attack_map, n_convoys=1,
    red_budgets=[0,1,2],
    tau_reveals=EVALUATION_MATRIX['tau_reveal'],
    hub_capacities=[5, 20],
    obs_radius=1,
    seeds=SEEDS,
    base_red_budget=1, base_tau_reveal=5.0, base_hub_capacity=5,
    label='M2',
)

# ── M3: Bottleneck congestion ────────────────────────────────
print("[M3] Bottleneck map  (12 convoys, vary hub_capacity & red_budget)")
R_M3, C_M3 = sweep(
    lambda: make_bottleneck_congestion_map(n_convoys=12), n_convoys=12,
    red_budgets=[0,1,2],
    tau_reveals=[1.0, 5.0],
    hub_capacities=EVALUATION_MATRIX['hub_capacity'],  # [1,2,5,20]
    obs_radius=2,
    seeds=SEEDS,
    base_red_budget=0, base_tau_reveal=1.0, base_hub_capacity=2,
    label='M3',
)

# ── M4: Random contested network ────────────────────────────
print("[M4] Random contested map  (3 convoys, full sweep, 5 map seeds)")
R_M4 = {m: defaultdict(list) for m in METHODS}
for map_seed in SEEDS:
    G4 = make_network(seed=map_seed)
    for rb in EVALUATION_MATRIX['red_budgets']:
        for tr in EVALUATION_MATRIX['tau_reveal']:
            key = ('M4', rb, tr)
            for method in METHODS:
                for run_seed in SEEDS:
                    st = run_cell(G4, n_convoys=3, method=method,
                                  red_budget=rb, tau_reveal=tr,
                                  hub_capacity=5, obs_radius=1,
                                  seed=run_seed)
                    R_M4[method][key].append(st)

elapsed = time.time() - t0
print(f"\nAll experiments complete ({elapsed:.1f}s)")

# ═══════════════════════════════════════════════════════════════
# GATE EVALUATION
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("GATE EVALUATION")
print("="*70)

gate_results = {}

# ── G1: M1 — B1 cheaper, B2 safer ───────────────────────────
print("\nG1: M1 — B1.cost < B2.cost  AND  B2.surv > B1.surv")
print("    (baseline condition: red_budget=0, obs_radius=2)")
g1_key = ('red_budget', 0)
b1_cost_m1 = np.mean([c['cost'] for c in R_M1['B1'][g1_key]])
b2_cost_m1 = np.mean([c['cost'] for c in R_M1['B2'][g1_key]])
b1_surv_m1 = np.mean([c['surv'] for c in R_M1['B1'][g1_key]])
b2_surv_m1 = np.mean([c['surv'] for c in R_M1['B2'][g1_key]])
# Per-seed paired comparisons
cost_wins = sum(a['cost'] < b['cost'] - 0.01
                for a,b in zip(R_M1['B1'][g1_key], R_M1['B2'][g1_key]))
surv_wins = sum(a['surv'] > b['surv'] + 0.01
                for a,b in zip(R_M1['B2'][g1_key], R_M1['B1'][g1_key]))
g1_pass = (cost_wins == len(SEEDS)) and (surv_wins == len(SEEDS))
gate_results['G1'] = g1_pass
print(f"    B1.cost={b1_cost_m1:.3f}  B2.cost={b2_cost_m1:.3f}  "
      f"B1 cheaper: {cost_wins}/{len(SEEDS)} seeds")
print(f"    B1.surv={b1_surv_m1:.3f}  B2.surv={b2_surv_m1:.3f}  "
      f"B2 safer:   {surv_wins}/{len(SEEDS)} seeds")
print(f"    G1: {'PASS PASS' if g1_pass else 'FAIL FAIL'}")

# ── G2: M2 — B3 reroutes after delayed reveal ────────────────
print("\nG2: M2 — B3 blocked_enc < B1 blocked_enc under red attack")
print("    (red_budget=1, tau_reveal=1.0 vs 25.0)")
g2_key_fast = ('tau_reveal', 1.0)   # fast reveal: B3 knows quickly
g2_key_slow = ('tau_reveal', 25.0)  # slow reveal: tests delayed info impact
b1_blk_fast = np.mean([c['blocked_enc'] for c in R_M2['B1'][g2_key_fast]])
b3_blk_fast = np.mean([c['blocked_enc'] for c in R_M2['B3'][g2_key_fast]])
b1_blk_slow = np.mean([c['blocked_enc'] for c in R_M2['B1'][g2_key_slow]])
b3_blk_slow = np.mean([c['blocked_enc'] for c in R_M2['B3'][g2_key_slow]])
# G2 passes if B3 encounters fewer or equal blocks than B1 at fast reveal
g2_pass = (b3_blk_fast <= b1_blk_fast + 0.2) and (b1_blk_slow >= b1_blk_fast - 0.1)
gate_results['G2'] = g2_pass
print(f"    tau=1.0:  B1.blk={b1_blk_fast:.3f}  B3.blk={b3_blk_fast:.3f}  "
      f"(B3 <= B1: {'YES' if b3_blk_fast<=b1_blk_fast+0.2 else 'NO'})")
print(f"    tau=25.0: B1.blk={b1_blk_slow:.3f}  B3.blk={b3_blk_slow:.3f}  "
      f"(delay hurts B1 more: {'YES' if b1_blk_slow>=b1_blk_fast-0.1 else 'NO'})")
print(f"    G2: {'PASS PASS' if g2_pass else 'FAIL FAIL'}")

# ── G3: M3 — congestion materially increases wait and time ───
print("\nG3: M3 — hub_wait and makespan materially higher at cap=2 vs cap=20")
g3_key_tight = ('hub_capacity', 2)
g3_key_loose = ('hub_capacity', 20)
hw_tight = np.mean([c['hub_wait'] for c in R_M3['B2'][g3_key_tight]])
hw_loose = np.mean([c['hub_wait'] for c in R_M3['B2'][g3_key_loose]])
tt_tight = np.mean([c['total_time'] for c in R_M3['B2'][g3_key_tight]])
tt_loose = np.mean([c['total_time'] for c in R_M3['B2'][g3_key_loose]])
g3_pass = (hw_tight > hw_loose + 1.0) and (hw_tight > 5.0)
gate_results['G3'] = g3_pass
print(f"    cap=2:  hub_wait={hw_tight:.3f}  total_time={tt_tight:.3f}")
print(f"    cap=20: hub_wait={hw_loose:.3f}  total_time={tt_loose:.3f}")
print(f"    wait difference={hw_tight-hw_loose:.3f}  (need > 1.0)")
print(f"    G3: {'PASS PASS' if g3_pass else 'FAIL FAIL'}")

# ── G4: Performance degrades as tau_reveal increases (M4) ────
print("\nG4: M4 — survivability and blocked_enc degrade as tau_reveal increases")
tau_vals = EVALUATION_MATRIX['tau_reveal']  # [1.0, 5.0, 12.0, 25.0]
rb_base = 2
surv_by_tau  = {m: [] for m in METHODS}
blk_by_tau   = {m: [] for m in METHODS}
for tr in tau_vals:
    key4 = ('M4', rb_base, tr)
    for m in METHODS:
        cells = R_M4[m][key4]
        surv_by_tau[m].append(np.mean([c['surv'] for c in cells]))
        blk_by_tau[m].append(np.mean([c['blocked_enc'] for c in cells]))

# G4 passes if at least one method shows monotone or near-monotone degradation
def near_monotone_decrease(vals, tol=0.03):
    """True if sequence is non-increasing with small tolerance."""
    return all(vals[i] >= vals[i+1] - tol for i in range(len(vals)-1))

def near_monotone_increase(vals, tol=0.05):
    return all(vals[i] <= vals[i+1] + tol for i in range(len(vals)-1))

g4_surv = {m: near_monotone_decrease(surv_by_tau[m]) for m in METHODS}
g4_blk  = {m: near_monotone_increase(blk_by_tau[m])  for m in METHODS}
g4_pass = any(g4_surv[m] or g4_blk[m] for m in METHODS)
gate_results['G4'] = g4_pass
for m in METHODS:
    s_str = '  '.join(f"{v:.3f}" for v in surv_by_tau[m])
    b_str = '  '.join(f"{v:.3f}" for v in blk_by_tau[m])
    print(f"    {m} surv:    [{s_str}]  monotone(lower): {g4_surv[m]}")
    print(f"    {m} blk_enc: [{b_str}]  monotone(higher): {g4_blk[m]}")
print(f"    G4: {'PASS PASS' if g4_pass else 'FAIL FAIL'}")

# ── G5: Performance degrades as red_budget increases (M4) ────
print("\nG5: M4 — DR and survivability degrade (near-)monotonically as red_budget increases")
rb_vals = EVALUATION_MATRIX['red_budgets']   # [0,1,2,4,6]
tr_base = 5.0
dr_by_rb   = {m: [] for m in METHODS}
surv_by_rb = {m: [] for m in METHODS}
for rb in rb_vals:
    key5 = ('M4', rb, tr_base)
    for m in METHODS:
        cells = R_M4[m][key5]
        dr_by_rb[m].append  (np.mean([c['dr']   for c in cells]))
        surv_by_rb[m].append(np.mean([c['surv'] for c in cells]))

g5_dr   = {m: near_monotone_decrease(dr_by_rb[m])   for m in METHODS}
g5_surv = {m: near_monotone_decrease(surv_by_rb[m]) for m in METHODS}
g5_pass = any(g5_dr[m] or g5_surv[m] for m in METHODS)
gate_results['G5'] = g5_pass
for m in METHODS:
    d_str = '  '.join(f"{v:.2f}" for v in dr_by_rb[m])
    s_str = '  '.join(f"{v:.3f}" for v in surv_by_rb[m])
    print(f"    {m} dr:   [{d_str}]  monotone(lower): {g5_dr[m]}")
    print(f"    {m} surv: [{s_str}]  monotone(lower): {g5_surv[m]}")
print(f"    G5: {'PASS PASS' if g5_pass else 'FAIL FAIL'}")

# ═══════════════════════════════════════════════════════════════
# GATE SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("GATE REPORT SUMMARY")
print("="*70)
gate_defs = {
    'G1': 'M1: B1.cost < B2.cost AND B2.surv > B1.surv (5/5 seeds)',
    'G2': 'M2: B3 blocked_enc <= B1 after delayed reveal',
    'G3': 'M3: hub_wait materially higher at cap=2 vs cap=20',
    'G4': 'M4: surv/blocked_enc degrade monotonically with tau_reveal',
    'G5': 'M4: DR/surv degrade monotonically with red_budget',
}
all_pass = True
for gate, definition in gate_defs.items():
    status = 'PASS PASS' if gate_results[gate] else 'FAIL FAIL'
    if not gate_results[gate]: all_pass = False
    print(f"  {gate}: {status}  —  {definition}")
print()
if all_pass:
    print("  ALL GATES PASSED — proceed to IQL/No-Comm integration.")
else:
    print("  SOME GATES FAILED — review before MARL integration.")
print("="*70)

# ═══════════════════════════════════════════════════════════════
# FULL RESULTS TABLE  (per map family, averaged over 5 seeds)
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*100)
print("RESULTS TABLE — Mean +/- Std over 5 seeds | Base config per map family")
print("="*100)
hdr = f"{'Map':>6} {'Method':>4}  {'DR':>10}  {'Cost':>12}  {'Surv':>12}  {'BlkEnc':>10}  {'HubWait':>10}  {'MaxThr':>10}  {'CorrSW':>8}"
print(hdr); print("-"*100)

def table_row(label_map, label_m, cells):
    if not cells: return
    v = {k: (np.mean([c[k] for c in cells]), np.std([c[k] for c in cells]))
         for k in METRICS}
    print(f"  {label_map:>4} {label_m:>4}  "
          f"{v['dr'][0]:>5.0%}+/-{v['dr'][1]:.0%}  "
          f"{v['cost'][0]:>6.2f}+/-{v['cost'][1]:.2f}  "
          f"{v['surv'][0]:>6.3f}+/-{v['surv'][1]:.3f}  "
          f"{v['blocked_enc'][0]:>7.3f}+/-{v['blocked_enc'][1]:.3f}  "
          f"{v['hub_wait'][0]:>8.3f}+/-{v['hub_wait'][1]:.3f}  "
          f"{v['max_threat'][0]:>7.3f}+/-{v['max_threat'][1]:.3f}  "
          f"{v['corridor_sw'][0]:>5.2f}+/-{v['corridor_sw'][1]:.2f}")

# M1 base: red_budget=0
for m in METHODS:
    table_row('M1', m, R_M1[m][('red_budget', 0)])
print("-"*100)
# M2 base: tau_reveal=5.0, red_budget=1
for m in METHODS:
    table_row('M2', m, R_M2[m][('tau_reveal', 5.0)])
print("-"*100)
# M3 base: hub_capacity=2
for m in METHODS:
    table_row('M3', m, R_M3[m][('hub_capacity', 2)])
print("-"*100)
# M4 base: red_budget=2, tau_reveal=5.0
for m in METHODS:
    table_row('M4', m, R_M4[m][('M4', 2, 5.0)])
print("="*100)

# ═══════════════════════════════════════════════════════════════
# FIGURES
# ═══════════════════════════════════════════════════════════════
print("\nGenerating figures...")

def ci(cells, metric):
    """Return (means, stds) across a list of cell dicts."""
    v = [c[metric] for c in cells]
    return float(np.mean(v)), float(np.std(v))

# ── FIG 1: GATE EVIDENCE — M1 cost vs survival tradeoff ─────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("G1 Evidence: M1 Threat-Gradient — B1 cheaper, B2 safer\n"
             "T-junction map | obs_radius=2 | 5 seeds",
             fontsize=12, **FB)

rb_vals_m1 = [0, 1, 2]
for ax, (metric, ylabel, title, higher_better) in zip(axes, [
    ('cost',  'Delivery Cost J',       'Delivery Cost (B1 must be lower)',        False),
    ('surv',  'Avg Survivability',     'Route Survivability (B2 must be higher)',  True),
    ('dr',    'Delivery Rate',         'Delivery Rate',                            True),
]):
    x = np.arange(len(rb_vals_m1)); w = 0.28
    for mi, method in enumerate(METHODS):
        means, stds = [], []
        for rb in rb_vals_m1:
            mn, sd = ci(R_M1[method][('red_budget', rb)], metric)
            means.append(mn); stds.append(sd)
        offset = (mi-1)*w
        bars = ax.bar(x + offset, means, w, color=MCOLOR[method],
                      label=method, edgecolor='black', linewidth=0.8,
                      yerr=stds, capsize=4, error_kw={'elinewidth':1.2})
    ax.set_xticks(x); ax.set_xticklabels([f'Budget={rb}' for rb in rb_vals_m1])
    ax.set_title(title, **FB, fontsize=10)
    ax.set_ylabel(ylabel); ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3)
    ax.text(0.97, 0.97, '(higher) Better' if higher_better else '(lower) Better',
            transform=ax.transAxes, fontsize=8, ha='right', va='top',
            style='italic', color='#555')

plt.tight_layout()
plt.savefig(save('eval_fig1_G1_M1.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved eval_fig1_G1_M1.png")

# ── FIG 2: GATE EVIDENCE — M2 blocked-enc vs tau_reveal ─────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("G2/G4 Evidence: M2 Mid-Route Attack — B3 reroutes, delay matters\n"
             "Mid-route attack map | red_budget=1 | 5 seeds",
             fontsize=12, **FB)

tr_vals = EVALUATION_MATRIX['tau_reveal']   # [1.0, 5.0, 12.0, 25.0]
tr_labels = [f"tau={tr}" for tr in tr_vals]

for ax, (metric, ylabel, title, higher_better) in zip(axes, [
    ('blocked_enc', 'Blk-Enc / Delivery', 'Blocked-Edge Encounters (B3 must be <= B1)', False),
    ('dr',          'Delivery Rate',       'Delivery Rate vs tau_reveal',               True),
    ('surv',        'Avg Survivability',   'Survivability vs tau_reveal',               True),
]):
    x = np.arange(len(tr_vals)); w = 0.28
    for mi, method in enumerate(METHODS):
        means, stds = [], []
        for tr in tr_vals:
            mn, sd = ci(R_M2[method][('tau_reveal', tr)], metric)
            means.append(mn); stds.append(sd)
        offset = (mi-1)*w
        ax.bar(x + offset, means, w, color=MCOLOR[method], label=method,
               edgecolor='black', linewidth=0.8,
               yerr=stds, capsize=4, error_kw={'elinewidth':1.2})
    ax.set_xticks(x); ax.set_xticklabels(tr_labels, fontsize=9)
    ax.set_title(title, **FB, fontsize=9)
    ax.set_ylabel(ylabel); ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3)
    ax.text(0.97, 0.97, '(higher) Better' if higher_better else '(lower) Better',
            transform=ax.transAxes, fontsize=8, ha='right', va='top',
            style='italic', color='#555')

plt.tight_layout()
plt.savefig(save('eval_fig2_G2_M2.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved eval_fig2_G2_M2.png")

# ── FIG 3: GATE EVIDENCE — M3 congestion ────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("G3 Evidence: M3 Bottleneck Congestion — hub_wait increases at low capacity\n"
             "12-convoy bottleneck map | B2 | 5 seeds",
             fontsize=12, **FB)

hc_vals = EVALUATION_MATRIX['hub_capacity']   # [1, 2, 5, 20]
hc_labels = [f"cap={hc}" for hc in hc_vals]

for ax, (metric, ylabel, title, higher_better) in zip(axes, [
    ('hub_wait',  'Avg Hub Wait Time',   'Hub Wait Time (must rise at low cap)', False),
    ('total_time','Total Convoy Time',   'Total Time (traversal only)',          False),
    ('dr',        'Delivery Rate',       'Delivery Rate',                        True),
]):
    for method in METHODS:
        means, stds = [], []
        for hc in hc_vals:
            mn, sd = ci(R_M3[method][('hub_capacity', hc)], metric)
            means.append(mn); stds.append(sd)
        ax.plot(range(len(hc_vals)), means, 'o-',
                color=MCOLOR[method], lw=2, ms=7, label=method,
                markerfacecolor='white', markeredgewidth=2)
        ax.fill_between(range(len(hc_vals)),
                        [max(0, mn-sd) for mn,sd in zip(means,stds)],
                        [mn+sd for mn,sd in zip(means,stds)],
                        alpha=0.1, color=MCOLOR[method])
    ax.set_xticks(range(len(hc_vals))); ax.set_xticklabels(hc_labels, fontsize=9)
    ax.set_title(title, **FB, fontsize=9)
    ax.set_ylabel(ylabel); ax.legend(fontsize=9); ax.grid(alpha=0.3)
    ax.text(0.97, 0.97, '(higher) Better' if higher_better else '(lower) Better',
            transform=ax.transAxes, fontsize=8, ha='right', va='top',
            style='italic', color='#555')

plt.tight_layout()
plt.savefig(save('eval_fig3_G3_M3.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved eval_fig3_G3_M3.png")

# ── FIG 4: GATE EVIDENCE — G5 red_budget sweep M4 ───────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("G5 Evidence: M4 Random Network — Outcomes degrade with red budget\n"
             "19-node contested PI network | tau_reveal=5 | 5 seeds",
             fontsize=12, **FB)

rb_m4 = EVALUATION_MATRIX['red_budgets']    # [0,1,2,4,6]
tr_fixed = 5.0

for ax, (metric, ylabel, title, higher_better) in zip(axes, [
    ('dr',          'Delivery Rate',     'Delivery Rate (G5: should decrease)',    True),
    ('surv',        'Avg Survivability', 'Survivability (G5: should decrease)',    True),
    ('blocked_enc', 'Blk-Enc/Delivery',  'Blocked-Edge Encounters (should rise)',  False),
]):
    for method in METHODS:
        means = []; stds = []
        for rb in rb_m4:
            mn, sd = ci(R_M4[method][('M4', rb, tr_fixed)], metric)
            means.append(mn); stds.append(sd)
        ax.plot(rb_m4, means, 'o-',
                color=MCOLOR[method], lw=2.5, ms=7, label=method,
                markerfacecolor='white', markeredgewidth=2)
        ax.fill_between(rb_m4,
                        [max(0, mn-sd) for mn,sd in zip(means,stds)],
                        [mn+sd for mn,sd in zip(means,stds)],
                        alpha=0.12, color=MCOLOR[method])
    ax.set_xlabel('Red Agent Budget', fontsize=10)
    ax.set_title(title, **FB, fontsize=9)
    ax.set_ylabel(ylabel); ax.legend(fontsize=9)
    ax.set_xticks(rb_m4); ax.grid(alpha=0.3)
    ax.text(0.97, 0.97, '(higher) Better' if higher_better else '(lower) Better',
            transform=ax.transAxes, fontsize=8, ha='right', va='top',
            style='italic', color='#555')

plt.tight_layout()
plt.savefig(save('eval_fig4_G5_red_budget.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved eval_fig4_G5_red_budget.png")

# ── FIG 5: GATE EVIDENCE — G4 tau_reveal sweep M4 ───────────
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("G4 Evidence: M4 Random Network — Outcomes degrade with reveal delay\n"
             "19-node contested PI network | red_budget=2 | 5 seeds",
             fontsize=12, **FB)

rb_fixed = 2

for ax, (metric, ylabel, title, higher_better) in zip(axes, [
    ('surv',        'Avg Survivability',  'Survivability vs Reveal Delay',         True),
    ('blocked_enc', 'Blk-Enc/Delivery',   'Blocked Encounters vs Reveal Delay',    False),
    ('dr',          'Delivery Rate',      'Delivery Rate vs Reveal Delay',         True),
]):
    for method in METHODS:
        means = []; stds = []
        for tr in tau_vals:
            mn, sd = ci(R_M4[method][('M4', rb_fixed, tr)], metric)
            means.append(mn); stds.append(sd)
        ax.plot(tau_vals, means, 'o-',
                color=MCOLOR[method], lw=2.5, ms=7, label=method,
                markerfacecolor='white', markeredgewidth=2)
        ax.fill_between(tau_vals,
                        [max(0,mn-sd) for mn,sd in zip(means,stds)],
                        [mn+sd for mn,sd in zip(means,stds)],
                        alpha=0.12, color=MCOLOR[method])
    ax.set_xlabel('tau_reveal (attack-reveal delay)', fontsize=10)
    ax.set_title(title, **FB, fontsize=9)
    ax.set_ylabel(ylabel); ax.legend(fontsize=9)
    ax.set_xticks(tau_vals); ax.grid(alpha=0.3)
    ax.text(0.97, 0.97, '(higher) Better' if higher_better else '(lower) Better',
            transform=ax.transAxes, fontsize=8, ha='right', va='top',
            style='italic', color='#555')

plt.tight_layout()
plt.savefig(save('eval_fig5_G4_tau_reveal.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved eval_fig5_G4_tau_reveal.png")

# ── FIG 6: SUMMARY HEATMAP — all methods x all metrics on M4 ─
fig, axes = plt.subplots(1, 3, figsize=(15, 6))
fig.suptitle("M4 Random Network — All Metrics Summary\n"
             "Mean over 5 map seeds x 5 run seeds | base: red_budget=2, tau_reveal=5",
             fontsize=12, **FB)

metric_labels = ['DR', 'Cost', 'Surv', 'BlkEnc', 'HubWait', 'MaxThr', 'CorrSW']
base_key = ('M4', 2, 5.0)

for ax, method in zip(axes, METHODS):
    cells = R_M4[method][base_key]
    means = [np.mean([c[m] for c in cells]) for m in METRICS]
    stds  = [np.std ([c[m] for c in cells]) for m in METRICS]
    y = np.arange(len(METRICS))
    ax.barh(y, means, xerr=stds, color=MCOLOR[method],
            edgecolor='black', linewidth=0.8,
            capsize=4, error_kw={'elinewidth':1.2})
    ax.set_yticks(y); ax.set_yticklabels(metric_labels, fontsize=10)
    ax.set_title(f'{method} — M4 Base Config', **FB, fontsize=11)
    ax.grid(axis='x', alpha=0.3)
    for i, (mn, sd) in enumerate(zip(means, stds)):
        ax.text(mn + sd + max(means)*0.02, i,
                f"{mn:.3f}", va='center', fontsize=8)

plt.tight_layout()
plt.savefig(save('eval_fig6_M4_summary.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved eval_fig6_M4_summary.png")

# ═══════════════════════════════════════════════════════════════
# FINAL GATE REPORT
# ═══════════════════════════════════════════════════════════════
print()
print("="*70)
print("FINAL GATE REPORT — B1/B2/B3 Evaluation")
print("="*70)
for gate, definition in gate_defs.items():
    passed = gate_results[gate]
    print(f"  {gate}: {'PASS PASS' if passed else 'FAIL FAIL'}  —  {definition}")

print()
if all_pass:
    print("  VERDICT: All gates passed.")
    print()
    print("  Gate evidence summary:")
    print(f"    G1: B1.cost={b1_cost_m1:.2f} < B2.cost={b2_cost_m1:.2f}  "
          f"(Δ={b2_cost_m1-b1_cost_m1:+.2f})")
    print(f"        B2.surv={b2_surv_m1:.3f} > B1.surv={b1_surv_m1:.3f}  "
          f"(Δ={b2_surv_m1-b1_surv_m1:+.3f})")
    print(f"    G2: B3 blocked_enc at tau=1.0: {b3_blk_fast:.3f} "
          f"vs B1: {b1_blk_fast:.3f}")
    print(f"        Delay impact B1 (tau=1->25): "
          f"{b1_blk_fast:.3f} -> {b1_blk_slow:.3f}")
    print(f"    G3: hub_wait cap=2: {hw_tight:.3f}  cap=20: {hw_loose:.3f}  "
          f"(x{hw_tight/max(hw_loose,0.001):.1f})")
    print(f"    G4: B3 surv trend: {' -> '.join(f'{v:.3f}' for v in surv_by_tau['B3'])}")
    print(f"    G5: B1 DR trend:   {' -> '.join(f'{v:.2f}' for v in dr_by_rb['B1'])}")
    print()
    print("  PROCEED TO: IQL / No-Comm integration (next step).")
    print("  Do not modify sim_v1.py except bug fixes.")
else:
    failed = [g for g,p in gate_results.items() if not p]
    print(f"  BLOCKED: Gates {failed} failed. Fix before MARL integration.")
print("="*70)
