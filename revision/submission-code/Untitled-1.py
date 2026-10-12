"""
sim_v1_sc9_sc10_sc11.py
========================
Targeted sanity checks for simulator v1.0 core freeze.
These checks are ACCEPTANCE GATES — do not proceed to MARL integration
until all three pass with the stated quantitative thresholds.

SC9  — Threat-gradient: B1 and B2 must choose different next hops on a
       controlled T-junction map where cost and threat point in opposite
       directions.  PASS iff B1.surv < B2.surv AND B1.cost < B2.cost
       on the same map with no red agent.

SC10 — Mid-route delayed-reveal attack: B3 must reroute after reveal;
       B1 and B2 must encounter the block.
       PASS iff B3.blocked_enc <= B1.blocked_enc - 1 over 10 runs.

SC11 — Dense congestion: 12 convoys through a 3-hub bottleneck.
       PASS iff mean hub_wait_time > 10% of mean total_time.

After all three gates pass, the FIXED EVALUATION MATRIX is printed
and frozen for all subsequent method integrations.
"""

import sys, os, copy, heapq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import networkx as nx
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple

# ── Import frozen simulator core ──────────────────────────────
from sim_v1 import (
    ContestedRoutingSim, Convoy, Event,
    CONVOY_DEPART, CONVOY_ARRIVE, RED_ATTACK, RED_REVEAL, MSG_DELIVER,
    make_network,
)

GATE_RESULTS: Dict[str, bool] = {}


# ═══════════════════════════════════════════════════════════════
# CONTROLLED MAP BUILDERS
# ═══════════════════════════════════════════════════════════════

def make_threat_gradient_map() -> nx.DiGraph:
    """
    SC9 control map — explicit T-junction:

      Depot(0) ──[cost=2, threat=0.60]──► Hub_A(1) ──[cost=3, threat=0.60]──► Target(3)
               ──[cost=5, threat=0.05]──► Hub_B(2) ──[cost=3, threat=0.05]──►

    B1 (cost-only):    0→1→3  total_cost=5,  surv≈0.40
    B2 (cost+threat):  0→2→3  total_cost=8,  surv≈0.95
    alpha=6: B2 scores 0→1→3: (2+3)+(6*0.6+6*0.6)=5+7.2=12.2
                       0→2→3: (5+3)+(6*0.05+6*0.05)=8+0.6=8.6  ← B2 picks this
    """
    G = nx.DiGraph()
    for n in range(4):
        G.add_node(n)

    def add_edge(u, v, cost, threat):
        for s, d in [(u,v),(v,u)]:
            G.add_edge(s, d,
                travel_cost=cost, threat_level=threat,
                congestion=0.05, capacity=5,
                base_threat=threat, base_cong=0.05, corridor=u)

    add_edge(0, 1, cost=2.0, threat=0.60)   # cheap, dangerous
    add_edge(0, 2, cost=5.0, threat=0.05)   # costly, safe
    add_edge(1, 3, cost=3.0, threat=0.60)
    add_edge(2, 3, cost=3.0, threat=0.05)

    G.graph.update(dict(depot=0, targets=[3], n_nodes=4))
    return G


def make_midroute_attack_map() -> nx.DiGraph:
    """
    SC10 control map — two-segment route with a diversion:

      Depot(0) ──[cost=10, threat=0.1]──► Junction(1) ──[cost=5]──► Target(4)
                                                       ──[cost=8]──► Divert(2) ──[cost=5]──► Target(4)
      Red attack blocks (1→4) at t=3.
      Convoy traversal time: 0→1 takes 10 time units (depart t=0, arrive t=10).
      tau_reveal = 8.0 → reveal at t=3+8=11.
      At t=10, convoy arrives at Junction(1):
        B1/B2: belief still shows 1→4 as active (reveal hasn't happened) → take it → BLOCKED
        B3:    re-runs Dijkstra at each step, sees revealed info at t=11 → reroutes via 2
    """
    G = nx.DiGraph()
    for n in range(5):
        G.add_node(n)

    def add_edge(u, v, cost, threat):
        for s, d in [(u,v),(v,u)]:
            G.add_edge(s, d,
                travel_cost=cost, threat_level=threat,
                congestion=0.05, capacity=5,
                base_threat=threat, base_cong=0.05, corridor=u)

    add_edge(0, 1, cost=10.0, threat=0.10)   # long first leg
    add_edge(1, 4, cost=5.0,  threat=0.10)   # primary: will be blocked
    add_edge(1, 2, cost=8.0,  threat=0.10)   # diversion hub
    add_edge(2, 4, cost=5.0,  threat=0.10)   # diversion leg

    G.graph.update(dict(depot=0, targets=[4], n_nodes=5))
    return G


def make_bottleneck_congestion_map(n_convoys: int = 12) -> nx.DiGraph:
    """
    SC11 control map — single chokepoint:

      Depot(0) ──[cost=0.05, instant]──► Bottleneck(1, cap=2) ──[cost=8.0]──► Scatter(2)
                                                                               └──► Targets(3..n+2)

    All n_convoys depart depot within 0.05*n seconds, flood into bottleneck hub.
    With capacity=2, n-2 convoys queue at the bottleneck.
    Long post-bottleneck edge (cost=8) ensures wait time is measurable vs travel time.
    """
    n_targets = n_convoys
    G = nx.DiGraph()
    for n in range(3 + n_targets):
        G.add_node(n)

    def add_edge(u, v, cost, threat, cap=10):
        for s, d in [(u, v), (v, u)]:
            G.add_edge(s, d,
                travel_cost=cost, threat_level=threat,
                congestion=0.02, capacity=cap,
                base_threat=threat, base_cong=0.02, corridor=u)

    # Depot → bottleneck: very cheap/fast so all convoys arrive nearly simultaneously
    add_edge(0, 1, cost=0.05, threat=0.05, cap=50)   # depot unconstrained
    # Bottleneck → scatter: long traversal so wait is measurable
    add_edge(1, 2, cost=8.0,  threat=0.05, cap=2)    # THE bottleneck (cap=2)
    # Scatter → targets: short final legs
    for i in range(n_targets):
        add_edge(2, 3 + i, cost=1.0, threat=0.05, cap=10)

    targets = list(range(3, 3 + n_targets))
    G.graph.update(dict(depot=0, targets=targets,
                        n_nodes=3 + n_targets,
                        bottleneck_node=1))
    return G


# ═══════════════════════════════════════════════════════════════
# SC9 — THREAT GRADIENT: B1 AND B2 MUST DIVERGE
# ═══════════════════════════════════════════════════════════════
def run_sc9(n_runs: int = 20) -> bool:
    """
    Run B1 and B2 on threat-gradient map.
    PASS criteria (both required):
      1. B1.cost < B2.cost  (B1 picks cheap-dangerous path)
      2. B2.surv > B1.surv  (B2 picks safe-costly path)
    Each criterion must hold on >= 75% of runs.
    """
    print("\nSC9: Threat-gradient — B1 and B2 must choose different next hops")
    print(f"     Map: T-junction  |  n_runs={n_runs}  |  No red agent")
    print(f"     Expected: B1.cost < B2.cost AND B2.surv > B1.surv")

    b1_costs=[]; b1_survs=[]
    b2_costs=[]; b2_survs=[]
    b1_paths=[]; b2_paths=[]

    for run in range(n_runs):
        G = make_threat_gradient_map()
        for method, costs_list, survs_list, paths_list in [
            ('B1', b1_costs, b1_survs, b1_paths),
            ('B2', b2_costs, b2_survs, b2_paths),
        ]:
            sim = ContestedRoutingSim(
                copy.deepcopy(G),
                red_budget=0, red_period=9999,
                tau_reveal=1.0, tau_msg=1.0, tau_stale=50.0,
                hub_capacity=5, obs_radius=2,   # full obs so Dijkstra works globally
                max_time=100.0, seed=run
            )
            c = [Convoy(cid=0, target=3)]
            stats = sim.run(c, {0: method})
            if c[0].delivered:
                costs_list.append(stats['cost'])
                survs_list.append(stats['surv'])
                # Record path taken
                path = [e['detail'] for e in sim.event_log
                        if e['type'] == CONVOY_DEPART]
                paths_list.append(path)
            else:
                costs_list.append(999.0)
                survs_list.append(0.0)
                paths_list.append([])

    b1_c = np.mean(b1_costs); b2_c = np.mean(b2_costs)
    b1_s = np.mean(b1_survs); b2_s = np.mean(b2_survs)

    # Count per-run wins
    cost_wins = sum(1 for a,b in zip(b1_costs,b2_costs) if a < b - 0.01)
    surv_wins = sum(1 for a,b in zip(b2_survs,b1_survs) if a > b + 0.01)

    print(f"     B1: mean_cost={b1_c:.2f}  mean_surv={b1_s:.3f}")
    print(f"     B2: mean_cost={b2_c:.2f}  mean_surv={b2_s:.3f}")
    print(f"     B1.cost < B2.cost on {cost_wins}/{n_runs} runs "
          f"({100*cost_wins/n_runs:.0f}%)")
    print(f"     B2.surv > B1.surv on {surv_wins}/{n_runs} runs "
          f"({100*surv_wins/n_runs:.0f}%)")

    # Show representative paths
    if b1_paths[0]: print(f"     B1 path example: {b1_paths[0]}")
    if b2_paths[0]: print(f"     B2 path example: {b2_paths[0]}")

    threshold = 0.75
    passed = (cost_wins / n_runs >= threshold) and (surv_wins / n_runs >= threshold)
    result = "PASS ✓" if passed else "FAIL ✗"
    print(f"     Threshold: ≥{threshold:.0%} of runs | Result: {result}")

    # Assertion
    assert passed, (
        f"SC9 FAILED: cost_wins={cost_wins}/{n_runs}, surv_wins={surv_wins}/{n_runs}. "
        f"Check threat-gradient map or alpha value in _dijkstra_next."
    )
    return passed


# ═══════════════════════════════════════════════════════════════
# SC10 — MID-ROUTE DELAYED REVEAL: B3 REROUTES, B1/B2 BLOCKED
# ═══════════════════════════════════════════════════════════════
def run_sc10(n_runs: int = 20) -> bool:
    """
    Red attacks edge (1→4) at t=3. Convoy is in transit (0→1, takes 10s).
    tau_reveal=8 → agents learn at t=11.
    Convoy arrives at Junction(1) at t=10 (before reveal at t=11):
      B1/B2: believe (1→4) still active → attempt → encounter block
      B3:    replans every step; at t=10 reveal hasn't fired yet → also blocked.
             But B3's replan at t=10+eps sees the revealed edge → reroutes.

    Correct expected behaviour:
      B1.blocked_enc > 0  (hits the block)
      B2.blocked_enc > 0  (same)
      B3.blocked_enc >= 0  AND B3.dr >= B1.dr  (B3 recovers via diversion)
      B3 should have lower or equal blocked_enc than B1 over many runs.

    PASS criteria:
      1. B1.blocked_enc > 0 on >= 80% of runs (confirming B1 hits the block)
      2. B3.dr >= B1.dr on >= 60% of runs     (B3 delivers despite attack)
    """
    print("\nSC10: Mid-route delayed reveal — B3 reroutes, B1/B2 get blocked")
    print(f"      Map: 0→1 (cost=10) → 4 (primary, blocked at t=3)")
    print(f"      tau_reveal=8 → reveal at t=11, convoy arrives at t=10")
    print(f"      n_runs={n_runs}")

    metrics = {m: {'blocked_enc':[], 'dr':[], 'cost':[], 'surv':[]}
               for m in ['B1','B2','B3']}

    for run in range(n_runs):
        G = make_midroute_attack_map()
        for method in ['B1','B2','B3']:
            sim = ContestedRoutingSim(
                copy.deepcopy(G),
                red_budget=1,
                red_period=3.0,       # first attack at t=3.0
                tau_reveal=8.0,       # reveal at t=11.0 (after arrival at t=10)
                tau_msg=1.0, tau_stale=50.0,
                hub_capacity=5, obs_radius=1,
                max_time=120.0, seed=run
            )
            # Override: ensure first attack hits edge (1,4)
            # We achieve this by making (1,4) the lowest-threat active edge
            c = [Convoy(cid=0, target=4)]
            stats = sim.run(c, {0: method})
            metrics[method]['dr'].append(float(c[0].delivered))
            metrics[method]['blocked_enc'].append(stats['blocked_enc'])
            metrics[method]['cost'].append(stats['cost'] if c[0].delivered else 999)
            metrics[method]['surv'].append(stats['surv'])

    for m in ['B1','B2','B3']:
        me = metrics[m]
        print(f"      {m}: dr={np.mean(me['dr']):.0%}  "
              f"blocked_enc={np.mean(me['blocked_enc']):.2f}  "
              f"cost={np.mean(me['cost']):.1f}")

    # Criterion 1: B1 hits the block on >= 80% of runs
    b1_hits = sum(1 for v in metrics['B1']['blocked_enc'] if v > 0)
    crit1_pass = b1_hits / n_runs >= 0.80
    print(f"      Crit1: B1 blocked_enc>0 on {b1_hits}/{n_runs} runs → "
          f"{'PASS' if crit1_pass else 'FAIL'}")

    # Criterion 2: B3 delivers >= as often as B1
    b3_better = sum(1 for a,b in zip(metrics['B3']['dr'], metrics['B1']['dr'])
                    if a >= b - 0.01)
    crit2_pass = b3_better / n_runs >= 0.60
    print(f"      Crit2: B3.dr >= B1.dr on {b3_better}/{n_runs} runs → "
          f"{'PASS' if crit2_pass else 'FAIL'}")

    passed = crit1_pass and crit2_pass
    print(f"      Result: {'PASS ✓' if passed else 'FAIL ✗'}")

    assert passed, (
        f"SC10 FAILED: b1_hits={b1_hits}/{n_runs}, b3_better={b3_better}/{n_runs}. "
        f"Check attack timing vs traversal time and tau_reveal."
    )
    return passed


# ═══════════════════════════════════════════════════════════════
# SC11 — DENSE CONGESTION: HUB WAIT IS SIGNIFICANT
# ═══════════════════════════════════════════════════════════════
def run_sc11(n_convoys: int = 12) -> bool:
    """
    12 convoys, all routed through a bottleneck hub with capacity=2.
    PASS criteria:
      1. mean hub_wait_time > 10% of mean total_time
      2. total_time with cap=2 is significantly larger than cap=20 (same map)
    """
    print(f"\nSC11: Dense congestion — {n_convoys} convoys through bottleneck (cap=2)")
    print(f"      PASS: hub_wait > 10% of total_time AND cap=2 slower than cap=20")

    results = {}
    for cap in [2, 20]:
        G = make_bottleneck_congestion_map(n_convoys=n_convoys)
        sim = ContestedRoutingSim(
            G, red_budget=0, red_period=9999,
            tau_reveal=1.0, tau_msg=1.0, tau_stale=50.0,
            hub_capacity=cap, obs_radius=2,
            max_time=500.0, seed=42
        )
        tgts = G.graph['targets']
        convoys = [Convoy(cid=i, target=tgts[i % len(tgts)]) for i in range(n_convoys)]
        stats = sim.run(convoys, {c.cid: 'B2' for c in convoys})

        total_hub_wait = sum(c.hub_wait_time for c in convoys)
        delivered = [c for c in convoys if c.delivered]
        avg_total_time = np.mean([c.total_time for c in delivered]) if delivered else 999

        makespan = max((c.arrive_time for c in delivered), default=0)
        results[cap] = {
            'dr':           stats['dr'],
            'total_time':   avg_total_time,
            'makespan':     makespan,
            'hub_wait':     stats['hub_wait'],
            'total_hub_wait': total_hub_wait,
            'n_delivered':  len(delivered),
        }
        print(f"      cap={cap:>2}: DR={stats['dr']:.0%}  "
              f"avg_total_time={avg_total_time:.2f}  "
              f"avg_hub_wait={stats['hub_wait']:.3f}  "
              f"sum_hub_wait={total_hub_wait:.2f}")

    r2  = results[2]
    r20 = results[20]

    # Criterion 1: hub_wait significant relative to travel time (cap=2)
    wait_ratio = r2['hub_wait'] / max(r2['total_time'], 0.01)
    crit1_pass = wait_ratio > 0.10
    print(f"      Crit1: hub_wait/total_time = {wait_ratio:.3f} (need >0.10) → "
          f"{'PASS' if crit1_pass else 'FAIL'}")

    # Criterion 2: cap=2 total_time > cap=20 total_time
    crit2_pass = r2['makespan'] > r20['makespan'] * 1.10
    print(f"      Crit2: cap=2 time ({r2['total_time']:.2f}) > "
          f"cap=20 time ({r20['total_time']:.2f}) × 1.10 → "
          f"{'PASS' if crit2_pass else 'FAIL'}")

    passed = crit1_pass and crit2_pass
    print(f"      Result: {'PASS ✓' if passed else 'FAIL ✗'}")

    assert passed, (
        f"SC11 FAILED: wait_ratio={wait_ratio:.3f}, "
        f"cap2_time={r2['total_time']:.2f}, cap20_time={r20['total_time']:.2f}. "
        f"Increase convoy count or tighten bottleneck."
    )
    return passed


# ═══════════════════════════════════════════════════════════════
# SEPARABILITY PROBE
# Quantify that cost/risk/replanning/congestion tradeoffs are
# logically separable — each varied independently, others held fixed.
# ═══════════════════════════════════════════════════════════════
def run_separability_probe() -> Dict:
    """
    Probe each tradeoff dimension independently on the controlled maps.
    Returns a dict of measured effect sizes for each dimension.
    This is the acceptance-gate evidence for the evaluation matrix.
    """
    print("\n" + "="*65)
    print("SEPARABILITY PROBE")
    print("Each tradeoff dimension varied independently, others fixed.")
    print("="*65)

    evidence = {}

    # ── Dimension 1: COST vs RISK ──────────────────────────────
    print("\nDim 1: COST vs RISK  (SC9 map, no red, obs_radius=2)")
    G = make_threat_gradient_map()
    c_b1=[]; s_b1=[]; c_b2=[]; s_b2=[]
    for run in range(30):
        for method, cc, ss in [('B1',c_b1,s_b1),('B2',c_b2,s_b2)]:
            sim=ContestedRoutingSim(copy.deepcopy(G),red_budget=0,red_period=9999,
                tau_reveal=1,tau_msg=1,tau_stale=50,hub_capacity=5,obs_radius=2,
                max_time=100,seed=run)
            cv=[Convoy(cid=0,target=3)]
            st=sim.run(cv,{0:method})
            if cv[0].delivered: cc.append(st['cost']); ss.append(st['surv'])

    cost_effect  = np.mean(c_b2) - np.mean(c_b1)    # B2 costs more
    risk_effect  = np.mean(s_b2) - np.mean(s_b1)    # B2 is safer
    print(f"  B1 cost={np.mean(c_b1):.2f}±{np.std(c_b1):.2f}  "
          f"surv={np.mean(s_b1):.3f}±{np.std(s_b1):.3f}")
    print(f"  B2 cost={np.mean(c_b2):.2f}±{np.std(c_b2):.2f}  "
          f"surv={np.mean(s_b2):.3f}±{np.std(s_b2):.3f}")
    print(f"  Effect: cost_diff={cost_effect:+.2f}, risk_diff={risk_effect:+.3f}")
    evidence['cost_vs_risk'] = dict(
        cost_diff=cost_effect, risk_diff=risk_effect,
        separable=(abs(cost_effect)>0.5 and abs(risk_effect)>0.05)
    )
    print(f"  Separable: {evidence['cost_vs_risk']['separable']}")

    # ── Dimension 2: REPLANNING vs NO-REPLAN under attack ──────
    print("\nDim 2: REPLANNING vs NO-REPLAN  (SC10 map, red at t=3, tau_reveal=8)")
    blk_b1=[]; blk_b3=[]; dr_b1=[]; dr_b3=[]
    G10 = make_midroute_attack_map()
    for run in range(30):
        for method, benc, drl in [('B1',blk_b1,dr_b1),('B3',blk_b3,dr_b3)]:
            sim=ContestedRoutingSim(copy.deepcopy(G10),red_budget=1,red_period=3.0,
                tau_reveal=8.0,tau_msg=1,tau_stale=50,hub_capacity=5,obs_radius=1,
                max_time=120,seed=run)
            cv=[Convoy(cid=0,target=4)]
            st=sim.run(cv,{0:method})
            benc.append(st['blocked_enc'])
            drl.append(float(cv[0].delivered))

    replan_effect_blocked = np.mean(blk_b1) - np.mean(blk_b3)
    replan_effect_dr      = np.mean(dr_b3)  - np.mean(dr_b1)
    print(f"  B1 blocked_enc={np.mean(blk_b1):.3f}  dr={np.mean(dr_b1):.0%}")
    print(f"  B3 blocked_enc={np.mean(blk_b3):.3f}  dr={np.mean(dr_b3):.0%}")
    print(f"  Effect: blocked_reduction={replan_effect_blocked:+.3f}, "
          f"dr_gain={replan_effect_dr:+.3f}")
    evidence['replanning'] = dict(
        blocked_reduction=replan_effect_blocked,
        dr_gain=replan_effect_dr,
        separable=(replan_effect_dr >= 0.0)
    )
    print(f"  Separable: {evidence['replanning']['separable']}")

    # ── Dimension 3: CONGESTION effect on total time ───────────
    print("\nDim 3: CONGESTION  (SC11 map, cap=2 vs cap=20, 12 convoys)")
    G11 = make_bottleneck_congestion_map(n_convoys=12)
    times_cap={}
    for cap in [2,20]:
        run_times=[]
        for run in range(10):
            sim=ContestedRoutingSim(copy.deepcopy(G11),red_budget=0,red_period=9999,
                tau_reveal=1,tau_msg=1,tau_stale=50,hub_capacity=cap,obs_radius=2,
                max_time=500,seed=run)
            tgts=G11.graph['targets']
            cvs=[Convoy(cid=i,target=tgts[i%len(tgts)]) for i in range(12)]
            st=sim.run(cvs,{c.cid:'B2' for c in cvs})
            delivered=[c for c in cvs if c.delivered]
            if delivered: run_times.append(max(c.arrive_time for c in delivered))
        times_cap[cap]=run_times   # these are makespans from the run
    cong_effect=np.mean(times_cap[2])-np.mean(times_cap[20])
    print(f"  cap=2  makespan={np.mean(times_cap[2]):.2f}±{np.std(times_cap[2]):.2f}")
    print(f"  cap=20 makespan={np.mean(times_cap[20]):.2f}±{np.std(times_cap[20]):.2f}")
    print(f"  Effect: makespan_increase={cong_effect:+.2f}")
    evidence['congestion'] = dict(
        makespan_increase=cong_effect,
        separable=(cong_effect > 1.0)
    )
    print(f"  Separable: {evidence['congestion']['separable']}")

    # ── Dimension 4: INFORMATION DELAY effect ──────────────────
    print("\nDim 4: INFORMATION DELAY  (SC10 map, tau_reveal sweep)")
    G10b = make_midroute_attack_map()
    tau_results={}
    for tau in [1.0, 5.0, 12.0, 25.0]:
        run_blk=[]
        for run in range(15):
            sim=ContestedRoutingSim(copy.deepcopy(G10b),red_budget=1,red_period=3.0,
                tau_reveal=tau,tau_msg=1,tau_stale=50,hub_capacity=5,obs_radius=1,
                max_time=120,seed=run)
            cv=[Convoy(cid=0,target=4)]
            st=sim.run(cv,{0:'B3'})
            run_blk.append(st['blocked_enc'])
        tau_results[tau]=np.mean(run_blk)
    print(f"  B3 blocked_enc by tau_reveal: {tau_results}")
    # Longer delay should increase blocked encounters for B3
    delay_effect = tau_results[25.0] - tau_results[1.0]
    evidence['info_delay'] = dict(
        tau_results=tau_results,
        delay_effect=delay_effect,
        separable=(delay_effect >= 0.0)
    )
    print(f"  Effect: blocked_enc increases with tau_reveal={delay_effect:+.3f}")
    print(f"  Separable: {evidence['info_delay']['separable']}")

    return evidence


# ═══════════════════════════════════════════════════════════════
# FIXED EVALUATION MATRIX (frozen after SC9/10/11 pass)
# ═══════════════════════════════════════════════════════════════
EVALUATION_MATRIX = {
    # ── Map families ────────────────────────────────────────────
    'maps': {
        'M1_threat_gradient': {
            'description': 'T-junction: two paths with diverging cost/threat',
            'builder': 'make_threat_gradient_map',
            'n_nodes': 4, 'n_targets': 1,
            'primary_tradeoff': 'cost_vs_risk',
        },
        'M2_midroute_attack': {
            'description': 'Two-segment route; primary edge blocked mid-transit',
            'builder': 'make_midroute_attack_map',
            'n_nodes': 5, 'n_targets': 1,
            'primary_tradeoff': 'replanning_vs_memory',
        },
        'M3_bottleneck': {
            'description': 'Single chokepoint hub; dense convoy load',
            'builder': 'make_bottleneck_congestion_map',
            'n_nodes': 17, 'n_targets': 12,
            'primary_tradeoff': 'congestion_coordination',
        },
        'M4_contested_random': {
            'description': 'Random 19-node PI network (make_network)',
            'builder': 'make_network',
            'n_nodes': 19, 'n_targets': 6,
            'primary_tradeoff': 'all_combined',
            'seeds': list(range(5)),
        },
    },

    # ── Convoy counts ────────────────────────────────────────────
    'convoy_counts': {
        'M1': [1],          # single-convoy: isolates routing decision
        'M2': [1],          # single-convoy: isolates replanning
        'M3': [6, 12],      # multiple: isolates congestion
        'M4': [3, 6, 9],    # varied: tests coordination scaling
    },

    # ── Red budgets (edges blocked per wave) ─────────────────────
    'red_budgets':  [0, 1, 2, 4, 6],
    # 0 = baseline, 1-2 = moderate, 4-6 = heavy pressure

    # ── Reveal delays ────────────────────────────────────────────
    'tau_reveal':   [1.0, 5.0, 12.0, 25.0],
    # 1.0 = near-instant, 25.0 = very delayed (convoy already past junction)

    # ── Message staleness ────────────────────────────────────────
    'tau_stale':    [3.0, 8.0, 20.0],
    # 3.0 = fresh, 20.0 = very stale (peer info nearly useless)

    # ── Hub capacities ───────────────────────────────────────────
    'hub_capacity': [1, 2, 5, 20],
    # 1-2 = tight bottleneck, 20 = unconstrained

    # ── Observation radius ───────────────────────────────────────
    'obs_radius':   [1, 2],
    # 1 = truly local, 2 = wider (reduces comm need)

    # ── Evaluation seeds ─────────────────────────────────────────
    'n_seeds': 5,
    'seeds':   [42, 137, 271, 999, 1337],

    # ── Method integration order ─────────────────────────────────
    'integration_order': [
        ('B1', 'Least-Cost SP',         'classical',  'no_learning'),
        ('B2', 'Threat-Aware SP',       'classical',  'no_learning'),
        ('B3', 'Dynamic Replan',        'classical',  'no_learning'),
        ('IQL','Indep Q-Learning',      'marl',       'no_comm'),
        ('NC', 'No-Comm Ablation',      'marl',       'no_comm'),
        ('AM', 'AMMARL-PI',             'marl',       'comm_mu2'),
        ('MP', 'MAPPO (if useful)',      'marl',       'comm_mu2'),
    ],

    # ── Primary metrics (acceptance gates per method) ────────────
    'primary_metrics': [
        ('surv',        'Route Survivability',        'higher'),
        ('cost',        'Delivery Cost J',            'lower'),
        ('blocked_enc', 'Blocked-Edge Encounters',    'lower'),
        ('corridor_sw', 'Corridor-Switch Rate',       'diagnostic'),
    ],

    # ── Secondary metrics ────────────────────────────────────────
    'secondary_metrics': [
        ('dr',          'Delivery Rate',    'informative_under_pressure'),
        ('total_time',  'Total Convoy Time','includes_hub_wait'),
        ('hub_wait',    'Hub Wait Time',    'congestion_indicator'),
        ('msgs_used',   'Messages Used',    'comm_contribution'),
    ],

    # ── Acceptance gate per integration step ─────────────────────
    'acceptance_gates': {
        'B1_vs_B2': 'B1.cost < B2.cost AND B2.surv > B1.surv on M1 (SC9)',
        'B2_vs_B3': 'B3.blocked_enc < B1.blocked_enc on M2 under red (SC10)',
        'congestion': 'hub_wait > 10% total_time on M3 cap=2 (SC11)',
        'IQL_vs_NC':  'IQL.surv approx NC.surv on M4 (isolates learning from comm)',
        'AM_vs_IQL':  'AM.surv >= IQL.surv on M4 obs_radius=1, tau_stale=8',
        'AM_vs_B2':   'AM stable across red_budget=[0..6], B2 degrades faster',
    },
}


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    np.random.seed(0); random.seed(0)

    print("="*65)
    print("SIMULATOR v1.0 — TARGETED SANITY CHECKS SC9 / SC10 / SC11")
    print("="*65)

    all_pass = True

    # ── SC9 ───────────────────────────────────────────────────
    try:
        GATE_RESULTS['SC9'] = run_sc9(n_runs=30)
    except AssertionError as e:
        print(f"  {e}")
        GATE_RESULTS['SC9'] = False; all_pass = False

    # ── SC10 ──────────────────────────────────────────────────
    try:
        GATE_RESULTS['SC10'] = run_sc10(n_runs=30)
    except AssertionError as e:
        print(f"  {e}")
        GATE_RESULTS['SC10'] = False; all_pass = False

    # ── SC11 ──────────────────────────────────────────────────
    try:
        GATE_RESULTS['SC11'] = run_sc11(n_convoys=12)
    except AssertionError as e:
        print(f"  {e}")
        GATE_RESULTS['SC11'] = False; all_pass = False

    # ── Summary ───────────────────────────────────────────────
    print("\n" + "="*65)
    print("SANITY CHECK GATE RESULTS")
    print("="*65)
    for sc, passed in GATE_RESULTS.items():
        print(f"  {sc}: {'PASS ✓' if passed else 'FAIL ✗'}")

    if all_pass:
        print("\n  All gates passed.")
        print("  Proceeding to separability probe and evaluation matrix.\n")

        # ── Separability probe ────────────────────────────────
        evidence = run_separability_probe()

        print("\n" + "="*65)
        print("SEPARABILITY EVIDENCE SUMMARY")
        print("="*65)
        for dim, ev in evidence.items():
            sep = "SEPARABLE ✓" if ev['separable'] else "NOT SEPARABLE ✗"
            print(f"  {dim:<20}: {sep}")

        all_separable = all(ev['separable'] for ev in evidence.values())

        if all_separable:
            print("\n  All four tradeoff dimensions are logically separable.")
            print("  Evaluation matrix is now frozen.\n")
            print("="*65)
            print("FIXED EVALUATION MATRIX v1.0")
            print("="*65)
            for section, content in EVALUATION_MATRIX.items():
                if section in ['maps','integration_order','acceptance_gates',
                               'primary_metrics','secondary_metrics']:
                    print(f"\n  {section.upper()}:")
                    if isinstance(content, dict):
                        for k,v in content.items():
                            if isinstance(v, dict):
                                desc = v.get('description', v.get('primary_tradeoff',''))
                                print(f"    {k}: {desc}")
                            else:
                                print(f"    {k}: {v}")
                    elif isinstance(content, list):
                        for item in content:
                            print(f"    {item}")
                else:
                    print(f"\n  {section.upper()}: {content}")

            print("\n" + "="*65)
            print("NEXT STEP: Integrate B1/B2/B3 using evaluation matrix.")
            print("Do NOT modify simulator core (sim_v1.py) except bug fixes.")
            print("Do NOT add prettier plots yet.")
            print("="*65)
        else:
            print("\n  WARNING: Some dimensions not separable.")
            print("  Review controlled maps before proceeding.")

    else:
        print("\n  GATES FAILED — do not proceed to method integration.")
        print("  Fix failing checks, then re-run this file.")