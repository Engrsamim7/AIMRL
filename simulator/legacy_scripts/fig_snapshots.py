"""Fig. 13: live simulator state at three moments of ONE episode (GATE-SC policy). Everything drawn is read from the Sim object
(graph, true active attacks, convoy positions, hub queues); only the 2-D coordinates of the nodes are a drawing choice."""
import numpy as np, matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D
from ammarl2.graph import make_graph
from ammarl2.sim import Sim, Cfg
from ammarl2.policies import Policy
from figstyle import setup, save, C, INK, INK2, MUTED
setup()
gs, ep, L, W = 301, 3, 6, 6; seed = 5 * gs + ep
cfg = Cfg(attack_dur=(60, 120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=12, tau_msg=1.0, hub_cap=1, hub_service=2.0)
g = make_graph(gs, layers=L, width=W)
rng = np.random.default_rng(gs)
pos = {}
for n in range(g.n):
    if n == 0: pos[n] = (0.0, 0.0); continue
    if n < g.n - len(g.targets):
        l, i = (n - 1) // W, (n - 1) % W; pos[n] = (1 + l + rng.uniform(-.28, .28), (i - (W - 1) / 2) * 1.0 + rng.uniform(-.3, .3))
    else:
        k = n - (g.n - len(g.targets)); pos[n] = (L + 1.2 + rng.uniform(-.1, .1), (k - .5) * 2.6)
P = Policy("GATE-SC", weights="threat", use_obs=True, comm="gate", scaling="scaled", eta=1.0)
s = Sim(g, cfg, P, seed)
times = [6, 16, 30]
fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.9), sharex=True, sharey=True)
cmap = plt.cm.Greys
for ax, T in zip(axs, times):
    s.run(until=T); ax.axis("off"); ax.grid(False)
    for e in range(g.m):
        u, v = int(g.src[e]), int(g.dst[e]); r = g.rho[e]
        blocked = e in s.active
        ax.add_patch(FancyArrowPatch(pos[u], pos[v], connectionstyle="arc3,rad=0.06", arrowstyle="-", lw=0.4 + 1.6 * r,
                                     color=C["red"] if blocked else plt.cm.Blues(0.25 + 0.6 * r), alpha=1 if blocked else 0.9, ls=(0, (3, 1.5)) if blocked else "-", zorder=1))
        if blocked:
            m = ((pos[u][0] + pos[v][0]) / 2, (pos[u][1] + pos[v][1]) / 2); ax.plot(*m, marker="x", color=C["red"], ms=5, mew=1.4, zorder=4)
    for n in range(g.n):
        q = len(s.queue[n]) + int(s.busy[n])
        if n in g.targets: ax.scatter(*pos[n], s=30, color=C["aqua"], edgecolor=INK, lw=.6, zorder=3, marker="s")
        elif n == 0: ax.scatter(*pos[n], s=34, color=INK, zorder=3, marker="s")
        else: ax.scatter(*pos[n], s=9, color="white", edgecolor=INK2, lw=.6, zorder=3)
        if q >= 2 and n not in g.targets: ax.text(pos[n][0] + .07, pos[n][1] + .22, str(q), fontsize=6.5, color=C["orange"], fontweight="bold", zorder=5)
    alive = deliv = dead = 0
    for cv in s.cv:
        if cv.delivered: deliv += 1; continue
        if not cv.alive: dead += 1; continue
        if cv.depart_t > T: continue
        alive += 1
        if cv.cur_edge >= 0:
            e = cv.cur_edge; t0 = cv.entries[-1][0]; f = float(np.clip((T - t0) / (g.c[e] * 1.15), 0, 1))
            a, b = pos[int(g.src[e])], pos[int(g.dst[e])]; p = (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]))
        else: p = pos[cv.node]
        ax.scatter(*p, s=16, color=C["blue"] if cv.target == g.targets[0] else C["violet"], edgecolor="white", lw=.6, zorder=6)
    ax.set_title(f"t = {T}", loc="left", fontsize=8.5)
    ax.text(0.0, -0.02, f"in transit/at hubs {alive} · delivered {deliv} · destroyed {dead} · active attacks {len(s.active)}", transform=ax.transAxes, fontsize=6.2, color=INK2, va="top")
    ax.set_aspect("equal")
h = [Line2D([], [], color=C["red"], ls=(0, (3, 1.5)), lw=1.6, label="edge under attack (true state)"), Line2D([], [], marker="x", color=C["red"], ls="", label="attack location"),
     Line2D([], [], marker="o", color=C["blue"], ls="", label="convoy → target 1"), Line2D([], [], marker="o", color=C["violet"], ls="", label="convoy → target 2"),
     Line2D([], [], marker="s", color=C["aqua"], mec=INK, ls="", label="target base"), Line2D([], [], color=plt.cm.Blues(.7), lw=2, label="darker/thicker = higher threat ρ"),
     Line2D([], [], color=C["orange"], marker="$2$", ls="", label="convoys at hub (queue)")]
fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.04), fontsize=6.5)
fig.tight_layout(w_pad=0.2, rect=(0, 0.12, 1, 1)); save(fig, "fig13_simulator_snapshots")
