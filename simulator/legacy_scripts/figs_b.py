import glob, os, numpy as np, pandas as pd
from figstyle import *
setup()
LEARN = ["DQN", "IPPO", "MAPPO"]

# ============ Fig 2: training curves ============
def fig2():
    fs = glob.glob("out/curve_*.csv")
    if not fs: print("no curves yet"); return
    d = pd.concat([pd.read_csv(f) for f in fs]); fig, axs = plt.subplots(1, 3, figsize=(7.16, 2.5), sharey=True)
    for ax, a in zip(axs, ["dqn", "ippo", "mappo"]):
        for comm, col, lab in [("none", C["blue"], "no gate"), ("gate", C["violet"], "gate")]:
            x = d[(d.algo == a) & (d.comm == comm)]
            if x.empty: continue
            p = x.pivot_table(index="ep", columns="seed", values="surv").rolling(20, min_periods=5).mean()
            mu, sd = p.mean(1), p.std(1).fillna(0)
            ax.plot(mu.index, mu.values, color=col, label=f"{lab} ({p.shape[1]} seeds)"); ax.fill_between(mu.index, mu - sd, mu + sd, color=col, alpha=0.18, lw=0)
        ax.set_title(a.upper() if a != "dqn" else "DQN (GNN)", fontsize=8); ax.set_xlabel("training episode"); ax.legend(loc="lower right", fontsize=6.5)
        ax.axvline(0.7 * 300, color=MUTED, ls=":", lw=0.8)
    axs[0].set_ylabel("training survivability\n(20-episode mean, $\\pm$1 sd over seeds)")
    axs[1].text(212, 0.55, "exploration\nends", fontsize=6, color=MUTED, ha="left")
    fig.tight_layout(w_pad=0.5); save(fig, "fig2_training_curves")

# ============ Fig 3: final comparison with all KPIs ============
def fig3():
    if not os.path.exists("out/table3_full.csv"): print("no table3 yet"); return
    d = pd.read_csv("out/table3_full.csv")
    groups = [("Classical", ["B1", "B2", "B3"]), ("Heuristic + messages", ["NC", "COMM-ALL", "GATE", "GATE-SC", "ORACLE"]),
              ("Learned (GNN)", ["PPO-NONE", "DQN-NONE", "IPPO-NONE", "MAPPO-NONE", "DQN-GATE", "IPPO-GATE", "MAPPO-GATE", "DQN-ALL"])]
    names = {"B1": "B1 least-cost", "B2": "B2 threat-aware", "B3": "B3 replan", "NC": "NC", "COMM-ALL": "share all", "GATE": "gate (static)", "GATE-SC": "gate (scaled)", "ORACLE": "oracle"}
    kp = [("surv", "survivability (higher better)"), ("realized", "realized time, delivered (lower better)"), ("enc_per_convoy", "blocked-edge entries / convoy (lower better)")]
    rows = [m for _, ms in groups for m in ms if m in set(d.method)]
    fig, axs = plt.subplots(1, 3, figsize=(7.16, 3.6), sharey=True)
    for ax, (k, lab) in zip(axs, kp):
        for i, m in enumerate(rows):
            x = d[d.method == m][k].values; mu, lo, hi = boot_ci(x); y = len(rows) - 1 - i; base = m.split("-")[0] if m.split("-")[0] in M else m
            col, mk = M.get(m, M.get(base, (INK2, "o")))
            if m.endswith("-GATE"): col = M[base][0]
            ax.plot([lo, hi], [y, y], color=col, lw=1.4); ax.plot(mu, y, marker=mk if not m.endswith("-GATE") else "D", ms=5, color=col, mfc="white" if m.endswith("-NONE") else col, mew=1.2)
        ax.set_xlabel(lab, fontsize=7)
    yl = []
    for m in rows: yl.append(names.get(m, m.replace("-NONE", " (no gate)").replace("-GATE", " + gate").replace("-ALL", " + share all")))
    axs[0].set_yticks(range(len(rows))); axs[0].set_yticklabels(yl[::-1]);
    for ax in axs: ax.grid(axis="y", visible=False)
    # group separators
    n = 0
    for gname, ms in groups[:-1]:
        n += len([m for m in ms if m in rows]);
        for ax in axs: ax.axhline(len(rows) - n - 0.5, color=GRID, lw=1.0)
    fig.tight_layout(w_pad=0.4); save(fig, "fig3_final_comparison")

# ============ Fig 8: scaling ============
def fig8():
    d = pd.read_csv("out/scaling.csv"); fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.7), sharey=True); sizes = sorted(d["size"].unique())
    nl = [0, 0]
    def line(ax, m, key, ls="-", lab=None):
        ys = [boot_ci(d[(d["size"] == s) & (d.method == m)].surv.values) for s in sizes]; ys = np.array(ys); col, mk = M[key]
        k = nl[0] if ax is axs[0] else nl[1]; nl[0 if ax is axs[0] else 1] += 1; xs = np.array(sizes) * (1.0 + 0.035 * (k - 2))  # dodge so error bars do not overlap
        ax.errorbar(xs, ys[:, 0], yerr=[ys[:, 0] - ys[:, 1], ys[:, 2] - ys[:, 0]], color=col, marker=mk, ms=4.5, ls=ls, capsize=1.5, lw=1.2, label=lab or m, alpha=0.95)
    for m, key, lab in [("B3", "B3", "B3 replan"), ("NC", "NC", "no messages"), ("COMM-ALL", "COMM-ALL", "share all"), ("GATE-SC", "GATE-SC", "gate (scaled)"), ("ORACLE", "ORACLE", "oracle")]: line(axs[0], m, key, "--" if m == "ORACLE" else "-", lab)
    axs[0].set_title("heuristic routers", fontsize=8); nl[1] = 0
    line(axs[1], "NC", "NC", ":", "NC heuristic (reference)")
    for m, key, ls in [("DQN-NONE", "DQN", "-"), ("DQN-GATE", "DQN", "--"), ("IPPO-NONE", "IPPO", "-"), ("IPPO-GATE", "IPPO", "--")]: line(axs[1], m, key, ls, m.replace("-NONE", " (no gate)").replace("-GATE", " + gate"))
    axs[1].set_title("GNN agents, trained on 39 nodes only", fontsize=8)
    for ax in axs: ax.set_xscale("log"); ax.set_xticks(sizes); ax.set_xticklabels([str(s) for s in sizes]); ax.minorticks_off(); ax.set_xlabel("number of nodes"); ax.legend(fontsize=6, loc="lower right", ncol=1)
    axs[0].set_ylabel("survivability"); fig.tight_layout(w_pad=0.5); save(fig, "fig8_scaling")

# ============ Fig 9: reactive adversary and route diversification ============
def fig9():
    d = pd.read_csv("out/reactive_heur.csv"); fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.7), gridspec_kw=dict(width_ratios=[1.35, 1]))
    conds = [("random", 0.0, "random adversary"), ("reactive", 0.0, "reactive adversary"), ("reactive", 8.0, "reactive + spoofing")]
    meths = [("B3", "B3", "B3 replan"), ("NC", "NC", "no messages"), ("ALL", "COMM-ALL", "share all"), ("GATE-SC", "GATE-SC", "gate (scaled)"), ("ORACLE", "ORACLE", "oracle")]
    ax = axs[0]; w = 0.16
    for j, (m, key, lab) in enumerate(meths):
        ys = np.array([boot_ci(d[(d.adv == a) & (d.spoof == s) & (d.method == m)].surv.values) for a, s, _ in conds]); x = np.arange(3) + (j - 2) * (w + 0.015)
        ax.bar(x, ys[:, 0], w, color=M[key][0], label=lab, edgecolor=SURF, lw=0.6); ax.errorbar(x, ys[:, 0], yerr=[ys[:, 0] - ys[:, 1], ys[:, 2] - ys[:, 0]], fmt="none", ecolor=INK, lw=0.7, capsize=1)
    ax.set_xticks(range(3)); ax.set_xticklabels([c[2] for c in conds]); ax.set_ylim(0.6, 1.0); ax.set_ylabel("survivability"); ax.legend(ncol=3, fontsize=6, loc="upper right"); ax.grid(axis="x", visible=False)
    ax.set_title("no scheme beats the reactive adversary", fontsize=8)
    v = pd.read_csv("out/diversify.csv"); ax = axs[1]
    for comm, key, lab, ls in [("none", "NC", "no messages", "-"), ("all", "COMM-ALL", "share all", "--")]:
        sg = sorted(v.sigma.unique()); ys = np.array([boot_ci(v[(v.sigma == s) & (v.comm == comm)].surv.values) for s in sg])
        ax.errorbar(range(len(sg)), ys[:, 0], yerr=[ys[:, 0] - ys[:, 1], ys[:, 2] - ys[:, 0]], color=M[key][0], marker=M[key][1], ms=4.5, ls=ls, capsize=1.5, label=lab)
    ax.set_xticks(range(len(sg))); ax.set_xticklabels([f"{s:g}" for s in sg]); ax.set_xlabel(r"route-weight noise $\sigma$ (diversification)"); ax.set_title("randomising routes helps", fontsize=8); ax.legend(fontsize=6.5, loc="upper left")
    fig.tight_layout(w_pad=0.8); save(fig, "fig9_reactive_adversary")

# ============ Fig 10: FIR with common random numbers ============
def fig10():
    d = pd.read_csv("out/fir.csv"); d = d.rename(columns={"FIR_changed_per_info_decision": "fir"}); fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.7))
    conds = [(0.0, 1.0), (0.0, 4.0), (8.0, 1.0), (8.0, 4.0)]; labs = ["no spoof\ndelay 1", "no spoof\ndelay 4", "spoof 8\ndelay 1", "spoof 8\ndelay 4"]
    mm = [("COMM-ALL", "COMM-ALL", "share all"), ("GATE(static)", "GATE", "gate (static)"), ("GATE(conf only)", "NC", "confidence only")]
    ax = axs[0]; w = 0.26
    for j, (m, key, lab) in enumerate(mm):
        ys = []
        for sp, tm in conds:
            r = d[(d.spoof == sp) & (d.tau_msg == tm) & (d.method == m)].iloc[0]; ys.append(r.precision if (r.saved + r.lost) > 0 else np.nan)
        col = {"COMM-ALL": C["orange"], "GATE(static)": C["aqua"], "GATE(conf only)": C["blue"]}[m]
        ax.bar(np.arange(4) + (j - 1) * (w + 0.02), ys, w, color=col, label=lab, edgecolor=SURF, lw=0.6)
    ax.text(1.0 + 0.0, 0.03, "static gate admits\nnothing at delay 4", fontsize=5.5, color=INK2, ha="center", rotation=90, va="bottom")
    ax.set_xticks(range(4)); ax.set_xticklabels(labs, fontsize=6.5); ax.set_ylim(0, 1.18); ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0]); ax.set_ylabel("precision = saved / (saved + lost)"); ax.legend(fontsize=6, loc="upper center", ncol=3); ax.grid(axis="x", visible=False)
    ax.set_title("share of changed outcomes that were saves", fontsize=8)
    ax = axs[1]
    for j, (m, key, lab) in enumerate(mm):
        sv, ls_ = [], []
        for sp, tm in conds:
            r = d[(d.spoof == sp) & (d.tau_msg == tm) & (d.method == m)].iloc[0]; sv.append(r.saved); ls_.append(r.lost)
        x = np.arange(4) + (j - 1) * (w + 0.02); col = {"COMM-ALL": C["orange"], "GATE(static)": C["aqua"], "GATE(conf only)": C["blue"]}[m]
        ax.bar(x, sv, w, color=col, edgecolor=SURF, lw=0.6); ax.bar(x, [-v for v in ls_], w, color=col, edgecolor=SURF, lw=0.6, hatch="////", alpha=0.6)
    ax.axhline(0, color=INK, lw=0.8); ax.set_xticks(range(4)); ax.set_xticklabels(labs, fontsize=6.5); ax.set_ylabel("convoys (up = saved, down = lost)"); ax.grid(axis="x", visible=False)
    ax.set_title("counterfactual outcome changes (60 episodes)", fontsize=8)
    fig.tight_layout(w_pad=0.8); save(fig, "fig10_fir_counterfactual")

# ============ Fig 11: learned agents, gate effect under hostile conditions ============
def fig11():
    fs = glob.glob("out/rob_*.csv"); d = pd.concat([pd.read_csv(f).assign(src=f) for f in fs]); d["method"] = d.method.str.replace("_ADV", "")
    d["trained"] = np.where(d.src.str.contains("_adv_"), "trained with spoofing + reactive mix", np.where(d.src.str.contains("heuristics"), "heur", "trained on clean random adversary"))
    conds = ["random+spoof8", "reactive", "reactive+spoof8"]; fig, axs = plt.subplots(1, 2, figsize=(7.16, 2.7), sharey=True)
    for ax, tr in zip(axs, ["trained on clean random adversary", "trained with spoofing + reactive mix"]):
        i = 0; yl = []; ypos = []
        for a in LEARN:
            for c in conds:
                x = d[(d.trained == tr) & d.method.str.startswith(a + "-") & d.method.str.contains("GATE|NONE") & (d.cond == c)].copy(); x["comm"] = x.method.str.split("-").str[-1]
                p = x.pivot_table(index=["seed", "g", "ep"], columns="comm", values="surv"); mu, lo, hi = paired_ci(p["GATE"], p["NONE"]); y = -i; sig = lo > 0 or hi < 0
                col = M[a][0]; ax.plot([lo * 100, hi * 100], [y, y], color=col, lw=1.4, alpha=1 if sig else 0.5); ax.plot(mu * 100, y, marker=M[a][1], ms=5, color=col, mfc=col if sig else "white", mew=1.1)
                yl.append(f"{a} | {c.replace('+spoof8', ' + spoof')}"); ypos.append(y); i += 1
            i += 0.4
        ax.axvline(0, color=INK, lw=0.8); ax.set_xlabel("gate effect on survival (pts, GATE $-$ no gate)"); ax.set_title(tr, fontsize=7.5); ax.set_yticks(ypos); ax.set_yticklabels(yl, fontsize=6.5); ax.grid(axis="y", visible=False)
    fig.tight_layout(w_pad=0.6); save(fig, "fig11_learned_gate_robustness")


def fig14():
    d = pd.read_csv("out/dynamics.csv"); fig, axs = plt.subplots(1, 4, figsize=(7.16, 2.3), sharex=True)
    spec = [("delivered", "convoys delivered (fraction)"), ("destroyed", "convoys destroyed (fraction)"),
            ("blocked_entries", "blocked-edge entries per convoy"), ("queued", "convoys waiting at hubs")]
    lab = {"B1": "B1 least-cost", "NC": "no messages", "COMM-ALL": "share all", "GATE-SC": "gate (scaled)", "ORACLE": "oracle"}
    for ax, (col, yl) in zip(axs, spec):
        for m in ("B1", "NC", "COMM-ALL", "GATE-SC", "ORACLE"):
            q = d[d.method == m].pivot_table(index=["g", "ep"], columns="t", values=col); t = q.columns.values
            mu = q.mean(0).values; r = np.random.default_rng(0); idx = r.integers(0, len(q), (400, len(q)))
            bs = np.array([q.values[i].mean(0) for i in idx]); lo, hi = np.percentile(bs, [2.5, 97.5], 0)
            ax.plot(t, mu, color=M[m][0], lw=1.3, label=lab[m]); ax.fill_between(t, lo, hi, color=M[m][0], alpha=0.15, lw=0)
        ax.set_xlabel("simulation time"); ax.set_title(yl, fontsize=7.5)
    axs[3].legend(loc="upper right", fontsize=6, handlelength=1.4); fig.tight_layout(w_pad=0.5); save(fig, "fig14_time_dynamics")

if __name__ == "__main__":
    for f in (fig2, fig3, fig8, fig9, fig10, fig11): f(); print("ok", f.__name__)
