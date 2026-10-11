import numpy as np, matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e5e4e0", "#fcfcfb"
C = dict(blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", magenta="#e87ba4", green="#008300", violet="#6250d6", red="#e34948")
# one colour per ENTITY, identical in every figure
M = {"B1": ("#b9b8b2", "o"), "B2": ("#8a8984", "s"), "B3": ("#52514e", "^"), "NC": (C["blue"], "o"), "COMM-ALL": (C["orange"], "s"),
     "GATE": (C["aqua"], "D"), "GATE-SC": (C["violet"], "D"), "ORACLE": (INK, "*"),
     "DQN": (C["green"], "o"), "IPPO": (C["yellow"], "s"), "MAPPO": (C["magenta"], "^"), "PPO": ("#8a8984", "v")}
def setup():
    mpl.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
        "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7, "axes.edgecolor": INK2, "axes.linewidth": 0.6, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2, "axes.facecolor": SURF, "figure.facecolor": "white", "savefig.facecolor": "white", "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.4,
        "legend.frameon": False, "pdf.fonttype": 42, "savefig.dpi": 300})
def save(fig, name):
    fig.savefig(f"figs/{name}.pdf", bbox_inches="tight"); fig.savefig(f"figs/{name}.png", bbox_inches="tight", dpi=200); plt.close(fig)
def boot_ci(x, n=2000, seed=0):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    r = np.random.default_rng(seed); b = r.choice(x, size=(n, len(x))).mean(1)
    return x.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)
def paired_ci(a, b, n=2000, seed=0):
    d = np.asarray(a, float) - np.asarray(b, float); return boot_ci(d, n, seed)
def panel_tag(ax, t): ax.text(-0.02, 1.07, t, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")
