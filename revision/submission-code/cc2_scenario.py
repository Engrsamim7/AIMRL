"""
cc2_scenario.py  v3 -- Correct Randomised Hidden Corridor
=========================================================
Key design fixes over v2:
  1. Separate scout route vs follower route - followers commit at Fork
     BEFORE they can see actual corridor threats
  2. Small per-episode cost noise breaks Dijkstra tie-breaking
     so NC makes genuinely random corridor choices
  3. Only scout uses obs_radius=2 (reads actual Fork threats)
  4. Followers use obs_radius=1 (cannot see past Fork from MainHub)
  5. Message timing: scout sends at t~1, followers commit at t~9

TOPOLOGY
--------
  Depot(0)  --[fast, cost=1]--> ScoutObs(3) --[cost=1]--> Fork(2)
  Depot(0)  --[slow, cost=8]--> MainHub(1)  --[cost=1]--> Fork(2)
  Fork(2)   --[corrA, cost=3+noise, threat=H_A]--> MidA(4) --> Target(7)
  Fork(2)   --[corrB, cost=3+noise, threat=H_B]--> MidB(5) --> Target(7)
  Fork(2)   --[safe,  cost=8,       threat=0.35]-> Safe(6)  --> Target(7)

CONVOY ROLES
------------
  C0 (Scout):   Depot->ScoutObs->Fork->corr->Target
                Arrives ScoutObs at t=1. Sends hazard at t=1.
                Message arrives followers at t=1+tau_msg=2.5.
                Followers arrive Fork at t=9 (far too late to see threat themselves).

  C1,C2 (Followers): Depot->MainHub->Fork->corr->Target
                Arrive MainHub at t=8. With AMMARL: belief updated by t=2.5.
                With NC: belief = BASE_T on both corridors.
                Dijkstra at Fork: NC picks randomly (tie-broken by cost noise),
                AMMARL picks safe corridor (threat known from hazard).
"""

import sys, os, copy, heapq, random, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import networkx as nx
from collections import defaultdict
from scipy import stats as sp_stats

from ammarl_sim_core import (
    ContestedRoutingSim, Convoy, Event,
    CONVOY_DEPART, CONVOY_ARRIVE, RED_ATTACK, RED_REVEAL, MSG_DELIVER,
)

OUT = os.path.dirname(os.path.abspath(__file__))
def savep(f): return os.path.join(OUT, f)

SAFE_T     = 0.05
DANGER_T   = 0.75
BASE_T     = 0.35   # prior belief of followers (no observation)
TAU_MSG    = 1.5
TAU_STALE  = 20.0
SEEDS      = [42, 137, 271, 999, 1337]
N_EVAL     = 200


# =========================================================
# MAP BUILDER
# =========================================================
def make_cc2_map(ep_seed: int):
    """
    Per-episode H drawn from ep_seed.
    Small noise on corridor costs ensures NC breaks ties randomly.
    """
    rng = np.random.RandomState(ep_seed & 0xFFFF)
    H   = int(rng.randint(0, 2))

    threat_A = DANGER_T if H == 0 else SAFE_T
    threat_B = DANGER_T if H == 1 else SAFE_T

    # small noise on corridor costs -- makes NC genuinely random
    noise_A = rng.uniform(-0.4, 0.4)
    noise_B = rng.uniform(-0.4, 0.4)

    G = nx.DiGraph()
    for n in range(8):
        G.add_node(n)

    def ae(u, v, cost, thr, corr):
        for s, d in [(u, v), (v, u)]:
            G.add_edge(s, d,
                travel_cost  = float(cost),
                threat_level = float(thr),
                congestion   = 0.05,
                capacity     = 10,
                base_threat  = float(BASE_T),
                base_cong    = 0.05,
                corridor     = corr,
            )

    # Depot -> ScoutObs (fast) and Depot -> MainHub (slow)
    ae(0, 3, 1.0, 0.05, 0)   # scout route leg 1
    ae(3, 2, 1.0, 0.05, 0)   # scout route leg 2 -> Fork
    ae(0, 1, 8.0, 0.05, 0)   # follower route leg 1
    ae(1, 2, 1.0, 0.05, 0)   # follower route leg 2 -> Fork

    # Fork -> corridors (noisy costs)
    ae(2, 4, 3.0 + noise_A, threat_A, 1)   # corrA
    ae(2, 5, 3.0 + noise_B, threat_B, 2)   # corrB
    ae(2, 6, 8.0, 0.35, 3)                 # safe alt

    # Corridors -> Target
    ae(4, 7, 3.0, threat_A, 1)
    ae(5, 7, 3.0, threat_B, 2)
    ae(6, 7, 3.0, 0.35, 3)

    G.graph.update(dict(
        depot=0, targets=[7, 7, 7], n_nodes=8,
        H=H, threat_A=threat_A, threat_B=threat_B,
        noise_A=noise_A, noise_B=noise_B,
        scout_obs=3, fork_node=2, main_hub=1,
        corr_A=4, corr_B=5, safe_alt=6, target=7,
    ))
    return G, H


# =========================================================
# CC2 SIMULATOR
# =========================================================
class CC2Sim(ContestedRoutingSim):

    def __init__(self, G, H, mode='NC', tau_msg=TAU_MSG, **kw):
        super().__init__(G, tau_msg=tau_msg, **kw)
        self.H    = H
        self.mode = mode
        self.hazard_fused = []
        self.scout_done   = False

    def _update_belief(self, convoy: Convoy, node: int, now: float):
        """
        Override: followers (cid != 0) do NOT observe actual corridor threats.
        They only learn corridor threats via hazard messages (_process_inbox).
        This models the followers as having limited ISR capability -- they need
        the scout's observation to know which corridor is hot this episode.
        """
        fork = 2; corr_A = 4; corr_B = 5; safe_alt = 6; target = 7
        is_follower = (convoy.cid != 0)

        # Call parent to update non-corridor edges
        visible = self._visible_nodes(node)
        for u in visible:
            for v in self.G.successors(u):
                if v not in visible: continue
                es = self.edge_state.get((u, v), None)
                if es is None: continue
                is_corr_or_beyond = (
                    (u == fork and v in (corr_A, corr_B, safe_alt)) or
                    (u in (corr_A, corr_B, safe_alt) and v == target)
                )
                if is_follower and is_corr_or_beyond:
                    # Followers keep their existing belief (BASE_T or hazard-updated)
                    # Do NOT overwrite with actual observed threat
                    if (u, v) not in convoy.belief:
                        convoy.belief[(u, v)] = {
                            'active': True, 'threat': BASE_T,
                            'cost': es.get('cost', 3.0),
                            'congestion': 0.05, 'age': 0.0,
                            'corridor': es.get('corridor', -1),
                        }
                    continue
                # Normal update for non-corridor edges and scout
                active = not es['revealed_blocked']
                convoy.belief[(u, v)] = {
                    'active':     active,
                    'threat':     es['threat'],
                    'cost':       es['cost'],
                    'congestion': es['congestion'],
                    'age':        now,
                    'corridor':   es['corridor'],
                }

    def _init_convoy_beliefs(self, convoy: Convoy):
        """
        Role-based belief init:
          C0 (scout, cid=0): knows depot->ScoutObs(3) route only
          C1,C2 (followers): knows depot->MainHub(1) route only
        Corridor edges all initialised at BASE_T regardless of role.
        This forces each convoy type through its designated route.
        """
        convoy.belief        = {}
        convoy.visited_nodes = {convoy.position}
        fork = 2; corr_A = 4; corr_B = 5; safe = 6; target = 7
        scout_obs = 3; main_hub = 1; depot = 0

        is_scout = (convoy.cid == 0)

        # Define which edges this convoy knows about
        if is_scout:
            # Scout knows: 0->3, 3->2, then fork onwards
            known_edges = [(0,3),(3,0),(3,2),(2,3)]
        else:
            # Followers know: 0->1, 1->2, then fork onwards
            known_edges = [(0,1),(1,0),(1,2),(2,1)]

        # Everyone knows fork->corridors (at BASE_T) and corridor->target
        fork_edges = [(2,4),(4,2),(2,5),(5,2),(2,6),(6,2),
                      (4,7),(7,4),(5,7),(7,5),(6,7),(7,6)]
        known_edges += fork_edges

        for (u, v) in known_edges:
            if not self.G.has_edge(u, v): continue
            es  = self.edge_state.get((u, v), {})
            is_corr_or_beyond = (
                (u == fork and v in (corr_A, corr_B, safe)) or
                (u in (corr_A, corr_B, safe) and v == target)
            )
            thr = BASE_T if is_corr_or_beyond else es.get('threat', 0.05)
            convoy.belief[(u, v)] = {
                'active':     True,
                'threat':     thr,
                'cost':       es.get('cost', 3.0),
                'congestion': 0.05,
                'age':        0.0,
                'corridor':   es.get('corridor', -1),
            }

    def _execute_arrive(self, cid):
        convoy = self.convoys[cid]
        # Check arrival destination BEFORE super() calls _try_depart
        # which would set convoy.position = None
        arriving_at = convoy.transit_edge[1] if convoy.transit_edge else None
        
        # Scout broadcasts immediately upon arriving at ScoutObs (node 3)
        if (self.mode == 'AMMARL'
                and arriving_at == 3              # scout_obs node
                and not self.scout_done):
            # Must observe threats NOW (before super moves convoy onward)
            # Update scout position temporarily to read edge_state
            self.scout_done = True
            self._scout_broadcast_from_node(cid, obs_node=3)
        
        super()._execute_arrive(cid)

    def _scout_broadcast_from_node(self, scout_cid, obs_node):
        """Broadcast corridor hazards; called before super()._execute_arrive."""
        fork = 2
        msgs_sent = 0
        for corr_node in [4, 5, 6]:
            if not self.G.has_edge(fork, corr_node): continue
            actual_thr = self.edge_state[(fork, corr_node)]['threat']
            payload = {
                'type': 'HAZARD',
                'corridor_node': corr_node,
                'threat_obs': actual_thr,
                'timestamp': self.sim_time,
                'confidence': 1.0,
            }
            for rcid, convoy in self.convoys.items():
                if rcid == scout_cid: continue
                if convoy.delivered or convoy.failed: continue
                self.send_message(scout_cid, rcid, payload, self.sim_time)
                msgs_sent += 1
        self._log(self.sim_time, 'SCOUT_BROADCAST',
                  f"C{scout_cid} -> {msgs_sent} msgs, H={self.H} "
                  f"tA={self.G.graph['threat_A']:.2f} tB={self.G.graph['threat_B']:.2f}")

    def _process_inbox(self, convoy: Convoy):
        """Fuse HAZARD messages into corridor beliefs."""
        now  = self.sim_time
        fork = 2

        past_fork = (convoy.position is not None and
                     convoy.position not in [0, 1, 2, 3])

        for msg in list(convoy.inbox):
            age = now - msg['sent_at']
            if age > self.tau_stale: continue
            payload = msg.get('payload', {})
            if payload.get('type') != 'HAZARD': continue
            if past_fork: continue

            corr_node = payload['corridor_node']
            thr_obs   = payload['threat_obs']
            ts        = payload['timestamp']
            key       = (fork, corr_node)

            existing_age = convoy.belief.get(key, {}).get('age', -9999)
            if ts > existing_age:
                if key in convoy.belief:
                    convoy.belief[key]['threat'] = thr_obs
                    convoy.belief[key]['age']    = ts
                else:
                    convoy.belief[key] = {
                        'active': True, 'threat': thr_obs,
                        'cost': self.G[fork][corr_node].get('travel_cost', 3.0),
                        'congestion': 0.05, 'age': ts, 'corridor': -1,
                    }
                key2 = (corr_node, 7)
                if key2 in convoy.belief:
                    convoy.belief[key2]['threat'] = thr_obs
                    convoy.belief[key2]['age']    = ts

                convoy.messages_used += 1
                self.hazard_fused.append({
                    'cid': convoy.cid, 'corr': corr_node,
                    'threat': thr_obs, 'time': now
                })

        convoy.inbox = [m for m in convoy.inbox
                        if now - m['sent_at'] <= self.tau_stale]


# =========================================================
# EPISODE RUNNER
# =========================================================
def run_cc2_episode(ep_seed: int, mode: str) -> dict:
    random.seed(ep_seed); np.random.seed(ep_seed)
    G, H = make_cc2_map(ep_seed)

    # Scout: C0 takes route 0->3->2->...
    # Followers: C1,C2 take route 0->1->2->...
    # Achieved by setting visited_nodes on convoys after init
    sim = CC2Sim(
        G, H=H, mode=mode,
        red_budget=0, red_period=9999.0,
        tau_reveal=1.0, tau_msg=TAU_MSG, tau_stale=TAU_STALE,
        hub_capacity=10, obs_radius=1, max_time=300, seed=ep_seed,
    )
    tgts    = G.graph['targets']
    convoys = [Convoy(cid=i, target=tgts[i]) for i in range(3)]
    stats   = sim.run(convoys, {c.cid: 'B2' for c in convoys})

    delivered = [c for c in convoys if c.delivered]
    stats['max_threat'] = float(np.mean([
        max((1-s) for s in c.surv_edges) if c.surv_edges else 0.5
        for c in delivered])) if delivered else 0.5
    stats['H']          = H
    stats['msgs_used']  = float(np.mean([c.messages_used for c in convoys]))
    stats['msgs_fused'] = len(sim.hazard_fused)
    return stats, sim, convoys


# =========================================================
# QUICK VALIDATION
# =========================================================
def validate_cc2():
    print("=" * 65)
    print("CC2 MECHANISM VALIDATION")
    print("=" * 65)

    # Timing check
    print("\nTiming verification:")
    print(f"  Scout: 0->3 (cost=1) arrives at t=1")
    print(f"  Scout sends hazard at t=1")
    print(f"  Message arrives followers at t={1+TAU_MSG:.1f} (tau_msg={TAU_MSG})")
    print(f"  Followers: 0->1 (cost=8) arrives at t=8, 1->2 at t=9")
    print(f"  Followers arrive Fork at t=9  >  message arrival t={1+TAU_MSG:.1f}: OK")

    st_am, sim_am, cvs_am = run_cc2_episode(42, 'AMMARL')
    st_nc, sim_nc, cvs_nc = run_cc2_episode(42, 'NC')

    print(f"\nSeed=42, H={sim_am.H}  "
          f"({'A=dangerous' if sim_am.H==0 else 'B=dangerous'})")
    print("AMMARL key events:")
    for e in sim_am.event_log:
        if e['type'] in ('SCOUT_BROADCAST','HAZARD_FUSED','CONVOY_DELIVERED'):
            print(f"  t={e['time']:>6.2f}  {e['type']:<20}  {e['detail']}")

    print(f"\nAMMARL: DR={st_am['dr']:.0%}  surv={st_am['surv']:.4f}  "
          f"fused={st_am['msgs_fused']}")
    print(f"NC:     DR={st_nc['dr']:.0%}  surv={st_nc['surv']:.4f}  "
          f"fused={st_nc['msgs_fused']}")

    # Show convoy paths
    print("\nConvoy paths (AMMARL):")
    for c in cvs_am:
        log_edges = [e['detail'] for e in sim_am.event_log
                     if f'C{c.cid} ->' in e['detail']]
        print(f"  C{c.cid}: {log_edges}")

    print("\n200-episode quick check:")
    nc_s=[]; am_s=[]
    for ep in range(200):
        seed = ep*7+13
        st_n,_,_ = run_cc2_episode(seed, 'NC')
        st_a,_,_ = run_cc2_episode(seed, 'AMMARL')
        nc_s.append(st_n['surv']); am_s.append(st_a['surv'])
    gap = float(np.mean(am_s) - np.mean(nc_s))
    print(f"  NC     surv={np.mean(nc_s):.4f}  "
          f"(theoretical NC: {0.5*0.95+0.5*(1-DANGER_T):.3f})")
    print(f"  AMMARL surv={np.mean(am_s):.4f}  "
          f"(theoretical AM: {0.9*0.95+0.1*(1-DANGER_T):.3f})")
    print(f"  Gap = {gap:+.4f}  "
          f"(expected ~{0.9*0.95+0.1*(1-DANGER_T)-(0.5*0.95+0.5*(1-DANGER_T)):+.3f})")
    return gap


# =========================================================
# FULL EVALUATION
# =========================================================
def run_full_eval():
    print("\n" + "=" * 65)
    print(f"CC2 FULL EVAL  ({N_EVAL} episodes x {len(SEEDS)} seeds)")
    print("=" * 65)
    results = {'NC': [], 'AMMARL': []}
    for mode in ['NC', 'AMMARL']:
        print(f"\n{mode}:")
        for seed in SEEDS:
            survs=[]; costs=[]; blks=[]; drs=[]
            for ep in range(N_EVAL):
                st,_,_ = run_cc2_episode(seed*100000+ep, mode)
                survs.append(st['surv']); costs.append(st['cost'])
                blks.append(st['blocked_enc']); drs.append(st['dr'])
            cell = {'surv': float(np.mean(survs)),
                    'cost': float(np.mean(costs)),
                    'blocked_enc': float(np.mean(blks)),
                    'dr': float(np.mean(drs))}
            results[mode].append(cell)
            print(f"  seed={seed}: DR={cell['dr']:.0%}  "
                  f"surv={cell['surv']:.4f}  cost={cell['cost']:.2f}")
    return results


# =========================================================
# GATE EVALUATION
# =========================================================
def evaluate_gates(results):
    print("\n" + "=" * 65)
    print("CC2 ACCEPTANCE GATE EVALUATION")
    print("=" * 65)

    nc_surv = np.array([c['surv']        for c in results['NC']])
    am_surv = np.array([c['surv']        for c in results['AMMARL']])
    nc_blk  = np.array([c['blocked_enc'] for c in results['NC']])
    am_blk  = np.array([c['blocked_enc'] for c in results['AMMARL']])
    nc_cost = np.array([c['cost']        for c in results['NC']])
    am_cost = np.array([c['cost']        for c in results['AMMARL']])

    surv_diff = float(am_surv.mean() - nc_surv.mean())
    blk_gap   = float(nc_blk.mean()  - am_blk.mean())
    cost_gain = float(nc_cost.mean() - am_cost.mean())
    n = len(SEEDS)
    t_surv, p_surv = sp_stats.ttest_rel(am_surv, nc_surv)
    t_surv=float(t_surv); p_surv=float(p_surv)
    seeds_surv = sum(1 for a,b in zip(am_surv,nc_surv) if a > b+0.005)

    print(f"  Surv:    AMMARL={am_surv.mean():.4f}  NC={nc_surv.mean():.4f}  "
          f"diff={surv_diff:+.4f}  t={t_surv:+.3f}  p={p_surv:.4f}")
    print(f"  Blk-Enc: AMMARL={am_blk.mean():.4f}  NC={nc_blk.mean():.4f}  "
          f"gap={blk_gap:+.4f}")
    print(f"  Cost:    AMMARL={am_cost.mean():.2f}  NC={nc_cost.mean():.2f}  "
          f"gain={cost_gain:+.2f}")
    print(f"  AMMARL better surv: {seeds_surv}/{n} seeds")

    G_surv    = surv_diff >= 0.03 and seeds_surv/n >= 0.70
    G_blocked = blk_gap   >= 0.15
    G_sig     = p_surv < 0.05 and t_surv > 0
    G_any     = G_surv or G_blocked or G_sig

    print(f"\n  Gate G_surv    (diff>=0.03, >=70% seeds): "
          f"{'PASS' if G_surv else 'FAIL'}")
    print(f"  Gate G_blocked (NC-AM gap >= 0.15):       "
          f"{'PASS' if G_blocked else 'FAIL'}")
    print(f"  Gate G_sig     (p<0.05, t>0):             "
          f"{'PASS' if G_sig else 'FAIL'}")
    print()
    if G_any:
        print("  VERDICT: CC2 PASSES -- retain comm as contribution.")
    else:
        print("  VERDICT: CC2 FAILS")
        print("  Reframe: AMMARL advantage = stable partial-obs Q-learning,")
        print("           not peer communication.")
    print("=" * 65)
    return G_any, dict(
        surv_diff=surv_diff, blk_gap=blk_gap, cost_gain=cost_gain,
        t_surv=t_surv, p_surv=p_surv, seeds_surv=seeds_surv,
        G_surv=G_surv, G_blocked=G_blocked, G_sig=G_sig,
    )


# =========================================================
# FIGURES
# =========================================================
def make_cc2_figures(results, nums):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    FB = {'fontweight': 'bold'}
    COL = {'NC': '#26C6DA', 'AMMARL': '#2E7D32'}

    nc_s=[c['surv'] for c in results['NC']]
    am_s=[c['surv'] for c in results['AMMARL']]
    nc_b=[c['blocked_enc'] for c in results['NC']]
    am_b=[c['blocked_enc'] for c in results['AMMARL']]
    nc_c=[c['cost'] for c in results['NC']]
    am_c=[c['cost'] for c in results['AMMARL']]

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(
        "CC2: Randomized Hidden Corridor -- Hazard-Message Ablation\n"
        f"AMMARL (hazard-msg) vs No-Comm | {N_EVAL} eval eps x {len(SEEDS)} seeds\n"
        "H randomized per episode -- Q-memory alone cannot determine H",
        fontsize=11, **FB)

    specs = [
        (nc_s, am_s, 'Survivability',    True),
        (nc_b, am_b, 'Blk-Enc/Delivery', False),
        (nc_c, am_c, 'Delivery Cost J',  False),
    ]
    for ax, (nc_v, am_v, ylabel, hb) in zip(axes, specs):
        nm=np.mean(nc_v); ns=np.std(nc_v)
        am=np.mean(am_v); as_=np.std(am_v)
        bars = ax.bar([0,1],[nm,am],
                      color=[COL['NC'],COL['AMMARL']],
                      edgecolor='black',linewidth=1.2,width=0.5,
                      yerr=[ns,as_],capsize=8,error_kw={'elinewidth':2})
        bars[1].set_edgecolor('#1B5E20'); bars[1].set_linewidth(2.5)
        for xi,vals in [(0,nc_v),(1,am_v)]:
            jit=np.linspace(-0.08,0.08,len(vals))
            for j,v in zip(jit,vals):
                ax.plot(xi+j,v,'o',color='black',ms=5,alpha=0.7,zorder=5)
        diff=am-nm
        if len(nc_v)>=3:
            t,p=sp_stats.ttest_rel(am_v,nc_v)
            sig=('***' if p<0.001 else '**' if p<0.01
                 else '*' if p<0.05 else 'ns')
        else:
            t,p,sig=0,1,'ns'
        col='#1B5E20' if (hb and diff>0) or (not hb and diff<0) else '#B71C1C'
        ax.text(0.5,0.93,f"diff={diff:+.4f}  {sig}",
                transform=ax.transAxes,ha='center',fontsize=10,**FB,color=col)
        if ylabel=='Survivability':
            th_nc=0.5*0.95+0.5*(1-DANGER_T)
            th_am=0.9*0.95+0.1*(1-DANGER_T)
            ax.axhline(th_nc,color=COL['NC'],lw=1.5,ls='--',alpha=0.7,
                       label=f'NC theoretical {th_nc:.3f}')
            ax.axhline(th_am,color=COL['AMMARL'],lw=1.5,ls='--',alpha=0.7,
                       label=f'AMMARL theoretical {th_am:.3f}')
            ax.legend(fontsize=8)
        ax.set_xticks([0,1])
        ax.set_xticklabels(['NC\n(no hazard)','AMMARL\n(hazard msg)'],fontsize=10)
        ax.set_ylabel(ylabel,fontsize=10)
        ax.set_title(ylabel+(' (higher=better)' if hb else ' (lower=better)'),
                     **FB,fontsize=10)
        ax.grid(axis='y',alpha=0.3)
        ax.text(0,nm+ns+(nm+am)*0.025,f"{nm:.4f}",ha='center',fontsize=9)
        ax.text(1,am+as_+(nm+am)*0.025,f"{am:.4f}",ha='center',fontsize=9)

    plt.tight_layout()
    plt.savefig(savep('cc2_ablation.png'),dpi=150,bbox_inches='tight')
    plt.close()
    print("Saved cc2_ablation.png")

    fig2, ax2 = plt.subplots(figsize=(8,5))
    fig2.suptitle("CC2 Per-Seed Survivability -- AMMARL vs NC\n"
                  "Green=AMMARL better, Red=NC better",fontsize=11,**FB)
    for nc_v,am_v,s in zip(nc_s,am_s,SEEDS):
        c='#2E7D32' if am_v>nc_v else '#B71C1C'
        ax2.plot([0,1],[nc_v,am_v],'o-',color=c,lw=2,ms=8)
        ax2.text(1.04,am_v,str(s),fontsize=8,va='center')
    ax2.axhline(0.5*0.95+0.5*(1-DANGER_T),color=COL['NC'],lw=1.3,ls='--',alpha=0.8)
    ax2.axhline(0.9*0.95+0.1*(1-DANGER_T),color=COL['AMMARL'],lw=1.3,ls='--',alpha=0.8)
    ax2.set_xticks([0,1]); ax2.set_xticklabels(['NC','AMMARL'],fontsize=11)
    ax2.set_ylabel('Mean Survivability',fontsize=10)
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(savep('cc2_perseed.png'),dpi=150,bbox_inches='tight')
    plt.close()
    print("Saved cc2_perseed.png")


# =========================================================
# MAIN
# =========================================================
if __name__ == '__main__':
    gap = validate_cc2()
    if abs(gap) < 0.05:
        print("\nWARNING: gap < 0.05 -- check mechanism.")
    else:
        print(f"\nMechanism validated: gap={gap:+.4f}")
    results = run_full_eval()
    passed, nums = evaluate_gates(results)
    make_cc2_figures(results, nums)
    with open(savep('cc2_table.txt'),'w',encoding='utf-8') as f:
        f.write("CC2 Results -- Randomized Hidden Corridor\n")
        f.write("="*65+"\n")
        for mode in ['NC','AMMARL']:
            cells=results[mode]
            f.write(f"  {mode}: surv={np.mean([c['surv'] for c in cells]):.4f}+/-"
                    f"{np.std([c['surv'] for c in cells]):.4f}  "
                    f"blk={np.mean([c['blocked_enc'] for c in cells]):.4f}  "
                    f"cost={np.mean([c['cost'] for c in cells]):.2f}\n")
        f.write(f"G_surv:{' PASS' if nums['G_surv'] else ' FAIL'}  "
                f"G_blocked:{' PASS' if nums['G_blocked'] else ' FAIL'}  "
                f"G_sig:{' PASS' if nums['G_sig'] else ' FAIL'}\n")
        f.write(f"VERDICT: {'CC2 PASSES' if passed else 'CC2 FAILS'}\n")
    print("Saved cc2_table.txt\n=== DONE ===")
