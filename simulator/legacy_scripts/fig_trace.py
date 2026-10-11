"""Fig. 12: a raw trace of ONE simulated episode (same attacks, NC vs GATE-SC), drawn directly from Sim objects."""
import numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from ammarl2.graph import make_graph
from ammarl2.sim import Sim, Cfg
from ammarl2.policies import Policy
from figstyle import setup, save, C, INK, INK2, MUTED
setup()
gs, ep = 301, 3; seed = 5 * gs + ep
cfg = Cfg(attack_dur=(60, 120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=12, tau_msg=1.0, hub_cap=1, hub_service=2.0)
g = make_graph(gs, layers=6, width=6)
runs = {}
for name, p in (("NC (own observations)", Policy("NC", weights="threat", use_obs=True)),
                ("GATE-SC (gated peer messages)", Policy("GATE-SC", weights="threat", use_obs=True, comm="gate", scaling="scaled", eta=1.0))):
    s = Sim(g, cfg, p, seed); s.run(); runs[name] = s
fig, axs = plt.subplots(1, 3, figsize=(7.16, 3.0), gridspec_kw=dict(width_ratios=[1.15, 1, 1]))
# (A) graph with realised attack counts
a = runs["NC (own observations)"]; cnt = np.zeros(g.m)
for t, e in a.attack_log: cnt[e] += 1
layer = {0: 0};
for n in range(1, g.n): layer[n] = 1 + (n - 1) // 6 if n < g.n - 2 else 7
pos = {}
for n in range(g.n):
    l = layer[n]; k = 0 if n == 0 else ((n - 1) % 6 if n < g.n - 2 else n - (g.n - 2))
    cnt_l = 1 if n == 0 else (6 if n < g.n - 2 else 2); pos[n] = (l, (k - (cnt_l - 1) / 2) * (1 if cnt_l == 6 else 2.5))
ax = axs[0]; ax.grid(False); ax.axis("off")
mx = max(1, cnt.max())
for e in range(g.m):
    u, v = int(g.src[e]), int(g.dst[e]); c = cnt[e] / mx
    ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color=plt.cm.Reds(0.15 + 0.85 * c) if cnt[e] else "#cfcec8", lw=0.5 + 2.2 * c, zorder=1)
ax.scatter(*zip(*pos.values()), s=9, color=INK2, zorder=2)
ax.set_title("(A) network and attacks that occurred", loc="left");
ax.text(0.0, -0.04, f"graph seed {gs}, {g.n} nodes, {g.m} edges; {len(a.attack_log)} attacks\nedge width/darkness = number of attacks on that edge", transform=ax.transAxes, fontsize=6.5, color=INK2, va="top")
# (B,C) space-time per convoy
for ax, (name, s) in zip(axs[1:], runs.items()):
    ax.grid(False)
    for i, cv in enumerate(s.cv):
        t_end = cv.finished_t if not np.isnan(cv.finished_t) else s.t
        col = C["aqua"] if cv.delivered else C["red"]
        ax.plot([cv.depart_t, t_end], [i, i], color=col, lw=2.2, solid_capstyle="butt", alpha=.85)
        for t, e, bl in cv.entries:
            if bl: ax.plot(t, i, marker="x", color=INK, ms=4.5, mew=1.2)
        if not cv.delivered: ax.plot(t_end, i, marker="o", mfc="white", mec=C["red"], ms=5, mew=1.3)
    for t, e in s.attack_log: ax.axvline(t, color=C["orange"], lw=0.5, alpha=.5, zorder=0)
    ax.set_yticks(range(0, len(s.cv), 2)); ax.set_xlabel("simulation time"); ax.set_ylim(-0.8, len(s.cv) - 0.2)
    ax.set_title(("(B) " if "NC" in name.split()[0] else "(C) ") + name, loc="left", fontsize=7.5)
    ns = sum(c.delivered for c in s.cv); ax.text(0.98, 0.02, f"{ns}/{len(s.cv)} delivered", transform=ax.transAxes, ha="right", fontsize=7, color=INK2)
axs[1].set_ylabel("convoy")
h = [Line2D([], [], color=C["aqua"], lw=2.2, label="delivered"), Line2D([], [], color=C["red"], lw=2.2, label="destroyed"),
     Line2D([], [], marker="x", color=INK, ls="", label="entered blocked edge"), Line2D([], [], color=C["orange"], lw=0.8, label="attack onset")]
fig.legend(handles=h, loc="lower center", ncol=4, bbox_to_anchor=(0.55, -0.06), fontsize=7)
fig.tight_layout(w_pad=0.8); save(fig, "fig12_simulator_trace")
