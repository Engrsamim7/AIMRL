import json, numpy as np, pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle
from figstyle import *
from ammarl2.graph import make_graph
setup()

# ============ Fig 1: architecture, panels A-D match Sec. III-A..D ============
def fig1():
    fig, axs = plt.subplots(2, 2, figsize=(7.16, 5.3)); axs = axs.ravel()
    for ax in axs: ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off"); ax.grid(False)
    def box(ax, x, y, w, h, txt, fc="#ffffff", ec=INK2, fs=7, bold=False, lw=0.8):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=fc, ec=ec, lw=lw))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")
    def arrow(ax, p, q, c=INK2, ls="-", lw=1.0): ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=8, color=c, lw=lw, ls=ls))
    # A ---- network model
    ax = axs[0]; ax.set_title("(A) Contested PI network model  [Sec. III-A]", loc="left", fontweight="bold")
    g = make_graph(5, layers=3, width=4, n_targets=2)
    pos = {0: (0.8, 5)}
    for l in range(3):
        for i in range(4): pos[1 + l * 4 + i] = (2.9 + l * 2.2, 8.3 - i * 2.2)
    for k, t in enumerate(g.targets): pos[t] = (9.3, 6.3 - k * 2.6)
    for e in range(g.m):
        u, v = pos[int(g.src[e])], pos[int(g.dst[e])]; hot = g.rho[e] > 0.3
        ax.plot([u[0], v[0]], [u[1], v[1]], color=C["orange"] if hot else "#c9c8c2", lw=1.6 if hot else 0.7, zorder=1)
    for n, (x, y) in pos.items():
        kind = "depot" if n == 0 else ("base" if n in g.targets else "hub")
        ax.add_patch(Circle((x, y), 0.32, fc={"depot": INK, "base": C["aqua"], "hub": "white"}[kind], ec=INK2, lw=0.8, zorder=3))
    ax.text(0.8, 3.9, "depot $v_0$", ha="center", fontsize=7); ax.text(9.3, 9.0, "bases $B$", ha="center", fontsize=7); ax.text(5.1, 0.55, "hubs $H$", ha="center", fontsize=7)
    ax.plot([], [], color=C["orange"], lw=1.6, label=r"high-threat corridor ($\rho_e>0.3$)"); ax.plot([], [], color="#c9c8c2", lw=0.8, label="low-threat edge")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, -0.02), fontsize=6.5)
    ax.text(5, 9.6, r"edge $e$: $(c_e,\rho_e,q_e,\psi_e)$   $\tau_e=c_e(1+\beta f_e/q_e)$", ha="center", fontsize=7, color=INK2)
    # B ---- convoy dynamics & hubs
    ax = axs[1]; ax.set_title("(B) Convoy dynamics and hub queueing  [Sec. III-B]", loc="left", fontweight="bold")
    for k in range(4): ax.add_patch(Circle((1.0 + k * 0.9, 7.6), 0.3, fc=C["blue"], ec=INK2, lw=0.6))
    ax.text(2.7, 8.5, "convoys arrive (ARRIVE)", ha="center", fontsize=7)
    box(ax, 5.0, 6.0, 2.6, 3.2, "", fc="#f3f2ee"); ax.text(6.3, 8.85, "hub, capacity $c_h$", ha="center", fontsize=7, fontweight="bold")
    for k in range(2): ax.add_patch(Rectangle((5.35 + k * 1.1, 6.35), 0.9, 1.4, fc=C["blue"], ec=INK2, lw=0.6));
    ax.text(6.3, 7.95, "in service", ha="center", fontsize=6.5, color=INK2)
    arrow(ax, (3.7, 7.6), (4.95, 7.6)); arrow(ax, (7.65, 7.6), (9.6, 7.6)); ax.text(8.4, 6.6, "SERVE_END:\nchoose next hop", ha="center", fontsize=6.5)
    for k in range(3): ax.add_patch(Rectangle((1.0 + k * 1.1, 4.0), 0.9, 0.9, fc="white", ec=INK2, lw=0.6, hatch="////"))
    ax.text(2.6, 5.15, "FIFO queue (waiting)", ha="center", fontsize=6.5, color=INK2); arrow(ax, (4.3, 4.45), (5.0, 6.3), ls="--")
    box(ax, 0.6, 0.6, 8.8, 2.4, "Belief age keeps growing while a convoy waits:\n$\\xi(t)=t-t_{obs}$ at the decision (service end), not at arrival\n$\\Rightarrow$ queueing and freshness are coupled", fs=7, fc="#fff7ef", ec=C["orange"])
    # C ---- threat model
    ax = axs[2]; ax.set_title("(C) Threat model, delayed reveal, local belief  [Sec. III-C]", loc="left", fontweight="bold")
    ax.plot([0.8, 9.4], [6.2, 6.2], color=INK2, lw=0.8); arrow(ax, (9.2, 6.2), (9.6, 6.2))
    ax.add_patch(Rectangle((2.2, 5.7), 2.9, 1.0, fc="#fbd9cb", ec="none")); ax.add_patch(Rectangle((5.1, 5.7), 2.9, 1.0, fc="#cde2fb", ec="none"))
    for x, lab in [(2.2, "attack\n$t_0$"), (5.1, "revealed\n$t_0+\\tau_{reveal}$"), (8.0, "block\nends")]:
        ax.plot([x, x], [5.5, 6.9], color=INK, lw=1.0); ax.text(x, 7.15, lab, ha="center", fontsize=7)
    ax.text(3.65, 5.0, "invisible: any entry is\nan encounter (destroyed\nw.p. $p_{kill}$)", ha="center", va="top", fontsize=6.5, color=C["red"])
    ax.text(6.55, 5.0, "visible: scouts\nobserve and report", ha="center", va="top", fontsize=6.5, color=C["blue"])
    box(ax, 0.5, 0.5, 4.3, 2.4, "Adversary: budgeted ($K$ blocks)\n random, or reactive\n (targets recently used edges)", fs=6.8)
    box(ax, 5.1, 0.5, 4.4, 2.4, "Convoy belief per edge $e$:\n (blocked?, $t_{obs}$, confidence $\\kappa$)\n radius $r_{obs}=1$ hop;\n expires after $\\tau_{stale}$", fs=6.8)
    # D ---- communication model
    ax = axs[3]; ax.set_title("(D) Communication model and gate  [Sec. III-D, IV-D]", loc="left", fontweight="bold")
    box(ax, 0.3, 6.6, 2.3, 2.2, "sender $j$\nobserves a\nblocked edge", fs=6.8); box(ax, 7.4, 6.6, 2.4, 2.2, "receiver $i$\nbelief map", fs=6.8, fc="#eaf2fc")
    arrow(ax, (2.7, 7.7), (7.3, 7.7)); ax.text(3.9, 8.3, "$m=(e,\\,blocked,\\,t_{obs},\\,\\kappa)$", ha="center", fontsize=7)
    ax.text(3.9, 7.15, "delay $\\tau_{msg}$, loss $p_{loss}$", ha="center", fontsize=6.5, color=INK2)
    box(ax, 5.3, 9.0, 2.4, 0.8, "spoofing adversary", fs=6.5, fc="#fde8e7", ec=C["red"]); arrow(ax, (6.5, 9.0), (6.5, 7.8), c=C["red"], ls="--")
    for k, (t, s) in enumerate([("F  fresh", "age $\\leq$ min($\\tau_{stale}$,\n$\\eta\\,(ETA_e+\\tau_{msg})$)"), ("R  relevant", "edge $e$ lies on the\ncurrent planned route"), ("C  confident", "$\\kappa \\geq \\kappa_{min}$")]):
        x = 0.5 + k * 3.1; box(ax, x, 2.9, 2.8, 2.7, "", fc="#f3f2ee"); ax.text(x + 1.4, 5.15, t, ha="center", fontsize=7.2, fontweight="bold"); ax.text(x + 1.4, 3.8, s, ha="center", va="center", fontsize=6.4)
    ax.text(5.0, 6.15, "gate: admit the message only if the checked conditions hold", ha="center", fontsize=6.8, color=INK2)
    arrow(ax, (5.0, 2.8), (8.0, 1.6)); box(ax, 6.2, 0.4, 3.5, 1.2, "update belief", fs=7, fc="#eaf2fc")
    ax.text(2.3, 1.3, "each condition can be switched\noff separately (ablation)", ha="center", fontsize=6.5, color=INK2)
    fig.tight_layout(h_pad=1.0, w_pad=1.0); save(fig, "fig1_architecture")

# ============ Fig 4: gate ablation ============
def fig4():
    d = pd.read_csv("out/ablate.csv"); q = d.pivot_table(index=["loss", "tau_msg", "spoof", "g", "ep"], columns="method", values="surv")
    order = [("C", "Confidence (C)"), ("F", "Freshness (F)"), ("R", "Relevance (R)"), ("F+C", "F + C"), ("F+R", "F + R"), ("R+C", "R + C"), ("F+R+C", "F + R + C (scaled)"), ("static F+R+C", "F + R + C (static)")]
    scen = [((0.0, 1.0, 0.0), "delay 1, no spoofing"), ((0.0, 1.0, 8.0), "delay 1, spoof rate 8"), ((0.0, 4.0, 8.0), "delay 4, spoof rate 8"), ((0.4, 4.0, 20.0), "delay 4, loss 0.4, spoof 20")]
    fig, axs = plt.subplots(1, 4, figsize=(7.16, 2.7), sharey=True)
    for ax, (k, ttl) in zip(axs, scen):
        grp = q.xs(k, level=(0, 1, 2))
        for i, (m, lab) in enumerate(order):
            mu, lo, hi = paired_ci(grp[m], grp["ALL"]); y = len(order) - 1 - i
            sig = lo > 0 or hi < 0; col = C["blue"] if mu >= 0 else C["orange"]
            ax.plot([lo * 100, hi * 100], [y, y], color=col, lw=1.4, alpha=1 if sig else 0.55); ax.plot(mu * 100, y, "o", ms=4.5, color=col, mfc=col if sig else "white", mew=1.1)
        ax.axvline(0, color=INK, lw=0.8); ax.set_title(ttl, fontsize=7.5); ax.set_xlabel("survival vs share-all (pts)")
    axs[0].set_yticks(range(len(order))); axs[0].set_yticklabels([l for _, l in order][::-1]); axs[0].grid(axis="y", visible=False)
    for ax in axs[1:]: ax.grid(axis="y", visible=False)
    axs[0].plot([], [], "o", color=INK2, label="95% CI excludes 0 (filled)"); axs[0].plot([], [], "o", mfc="white", color=INK2, label="95% CI includes 0 (hollow)")
    fig.legend(loc="lower center", ncol=2, bbox_to_anchor=(0.55, -0.1), fontsize=7)
    fig.tight_layout(w_pad=0.6); save(fig, "fig4_gate_ablation")

# ============ Fig 5: communication conditions (replaces CC2 figure) ============
def fig5():
    d = pd.read_csv("out/harsh2.csv"); grid = [(0.0, 1.0), (0.0, 4.0), (0.4, 1.0), (0.4, 4.0)]
    meth = [("NC", "NC", "no messages"), ("COMM-ALL", "COMM-ALL", "share all"), ("GATE", "GATE", "gate, static"), ("GATE-SC", "GATE-SC", "gate, scaled"), ("ORACLE", "ORACLE", "oracle")]
    fig, axs = plt.subplots(1, 4, figsize=(7.16, 2.5), sharey=True)
    for ax, (loss, tm) in zip(axs, grid):
        for m, key, lab in meth:
            s = d[(d.loss == loss) & (d.tau_msg == tm) & (d.method == m)].groupby("spoof").surv.mean()
            col, mk = M[key]; ax.plot(s.index, s.values, marker=mk, ms=4.5, color=col, ls="--" if m == "ORACLE" else "-", label=lab)
        ax.set_title(f"loss {loss:g}, delay {tm:g}", fontsize=7.5); ax.set_xlabel("spoof rate"); ax.set_xticks([0, 8, 20]); ax.set_ylim(0.88, 1.0)
    axs[0].set_ylabel("survivability"); h, l = axs[0].get_legend_handles_labels(); fig.legend(h, l, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.08), fontsize=7)
    fig.tight_layout(w_pad=0.5); save(fig, "fig5_communication_conditions")

# ============ Fig 6: route case study ============
def fig6():
    cs = json.load(open("out/casestudy.json")); g = make_graph(cs["gs"], layers=6, width=6)
    pos = {0: (0, 3)}
    for l in range(6):
        for i in range(6): pos[1 + l * 6 + i] = (1 + l, 5.5 - i)
    for k, t in enumerate(g.targets): pos[t] = (7.6, 3.5 - k * 1.0 - 0.0)
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.9));
    def base(ax, title, rho=False):
        ax.set_title(title, fontsize=8); ax.axis("off"); ax.grid(False); ax.set_xlim(-0.4, 8.0); ax.set_ylim(-0.7, 6.0)
        ramp = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
        for e in range(g.m):
            u, v = pos[int(g.src[e])], pos[int(g.dst[e])]
            if rho: c = ramp[min(4, int(g.rho[e] / 0.12))]; lw = 0.7 + 3.2 * g.rho[e]
            else: c, lw = "#d4d3cd", 0.6
            ax.plot([u[0], v[0]], [u[1], v[1]], color=c, lw=lw, zorder=1, solid_capstyle="round")
        for n, (x, y) in pos.items(): ax.add_patch(Circle((x, y), 0.09, fc=INK if n == 0 else (C["aqua"] if n in g.targets else "white"), ec=INK2, lw=0.5, zorder=3))
    def route(ax, entries, col, ls):
        for t, e, bl in entries:
            u, v = pos[int(g.src[e])], pos[int(g.dst[e])]
            ax.plot([u[0], v[0]], [u[1], v[1]], color=col, lw=2.4, ls=ls, zorder=4, solid_capstyle="round")
            if bl: ax.plot((u[0] + v[0]) / 2, (u[1] + v[1]) / 2, "X", color=C["red"], ms=9, mec="white", mew=0.8, zorder=6)
    base(axs[0], "NC (own observations only)"); route(axs[0], cs["nc"], C["blue"], "-")
    axs[0].text(4, -0.55, "convoy destroyed on a blocked edge" if not cs["nc_survived"] else "blocked-edge encounter", ha="center", fontsize=7, color=C["red"])
    base(axs[1], "Gate (scaled freshness)"); route(axs[1], cs["gate"], C["violet"], "-"); axs[1].text(4, -0.55, "peer report admitted: detour, no encounter", ha="center", fontsize=7, color=C["violet"])
    base(axs[2], r"Edge threat level $\rho_e$", rho=True)
    axs[2].text(4, -0.55, "darker / thicker = higher $\\rho_e$", ha="center", fontsize=7, color=INK2)
    axs[0].plot([], [], "X", color=C["red"], label="blocked-edge entry"); axs[0].legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), fontsize=6.5)
    fig.tight_layout(w_pad=0.5); save(fig, "fig6_route_case_study")

# ============ Fig 7: gate-parameter sensitivity ============
def fig7():
    d = pd.read_csv("out/sweep_gate.csv"); fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.6))
    q = d.pivot_table(index=["conf_sd", "g", "ep"], columns="method", values="surv"); ks = [0.4, 0.6, 0.75, 0.9]
    ax = axs[0]
    for sd, lab, col, mk, off in [(0.0, "perfectly informative $\\kappa$", C["blue"], "o", -0.012), (0.1, "noisy genuine $\\kappa\\sim N(0.85,0.1)$", C["orange"], "s", 0.012)]:
        ys = np.array([paired_ci(q.loc[sd][f"conf k={k}"], q.loc[sd]["ALL"]) for k in ks]) * 100
        ax.errorbar(np.array(ks) + off, ys[:, 0], yerr=[ys[:, 0] - ys[:, 1], ys[:, 2] - ys[:, 0]], marker=mk, ms=4.5, color=col, capsize=2, label=lab)
    ax.axhline(0, color=INK, lw=0.8); ax.set_xlabel(r"confidence threshold $\kappa_{min}$"); ax.set_ylabel("survival vs share-all (pts)"); ax.set_title("confidence threshold", fontsize=8); ax.legend(fontsize=6, loc="upper left")
    ax = axs[1]; dd = d[d.conf_sd == 0.1]; allm = dd[dd.method == "ALL"]
    gen = [dd[dd.method == f"conf k={k}"].true_acc.mean() / allm.true_acc.mean() * 100 for k in ks]; sp = [dd[dd.method == f"conf k={k}"].spoof_acc.mean() / allm.spoof_acc.mean() * 100 for k in ks]
    ax.plot(ks, gen, "o-", color=C["aqua"], label="genuine admissions"); ax.plot(ks, sp, "s-", color=C["red"], label="spoofed admissions")
    ax.set_xlabel(r"confidence threshold $\kappa_{min}$"); ax.set_ylabel("% of share-all admissions"); ax.set_title("what the threshold removes (noisy $\\kappa$)", fontsize=8); ax.legend(fontsize=6.5, loc="lower left"); ax.set_ylim(0, 110)
    ax = axs[2]; es = [0.5, 1.0, 2.0, 4.0]; ys = np.array([paired_ci(q.loc[0.0][f"fresh eta={e}"], q.loc[0.0]["ALL"]) for e in es]) * 100
    ax.errorbar(range(4), ys[:, 0], yerr=[ys[:, 0] - ys[:, 1], ys[:, 2] - ys[:, 0]], marker="D", ms=4.5, color=C["violet"], capsize=2); ax.set_xticks(range(4)); ax.set_xticklabels(["0.5", "1", "2", "4"])
    ax.axhline(0, color=INK, lw=0.8); ax.set_xlabel(r"freshness scale $\eta$"); ax.set_ylabel("survival vs share-all (pts)"); ax.set_title(r"freshness limit $\eta\,(ETA_e+\tau_{msg})$", fontsize=8)
    fig.tight_layout(w_pad=0.8); save(fig, "fig7_gate_parameters")

if __name__ == "__main__":
    for f in (fig1, fig4, fig5, fig6, fig7): f(); print("ok", f.__name__)
