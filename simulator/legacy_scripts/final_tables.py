import pandas as pd, numpy as np, glob

def _md(df):
    """to_markdown needs the optional 'tabulate' package; fall back to plain text if it is not installed."""
    try:
        return df.to_markdown()
    except ImportError:
        return df.to_string()
from ammarl2.run import paired_bootstrap
out = []
def P(s): out.append(s); print(s)
# --- scaling
sc = pd.read_csv("out/scaling.csv")
P("## Scaling (survival, mean over 12 episodes per cell)")
P(_md(sc.pivot_table(index="method", columns="size", values="surv").round(3).reindex(columns=[39, 51, 203, 483])))
P("\n## Blocked-edge encounters per episode")
P(_md(sc.pivot_table(index="method", columns="size", values="enc").round(1).reindex(columns=[39, 51, 203, 483])))
# --- ablation CIs
ab = pd.read_csv("out/ablate.csv")
q = ab.pivot_table(index=["loss", "tau_msg", "spoof", "g", "ep"], columns="method", values="surv")
P("\n## Ablation: paired difference vs ALL (sharing everything), [95% bootstrap CI]")
rows = []
for k, grp in q.groupby(level=[0, 1, 2]):
    for m in ("C", "F", "R", "F+R+C", "scaled eta=2.0 F+R+C", "static F+R+C"):
        d, lo, hi = paired_bootstrap(grp[m], grp["ALL"]); rows.append(dict(loss=k[0], tau_msg=k[1], spoof=k[2], variant=m, diff=f"{d:+.3f} [{lo:+.3f},{hi:+.3f}]"))
P(_md(pd.DataFrame(rows).pivot_table(index="variant", columns=["loss", "tau_msg", "spoof"], values="diff", aggfunc="first")))
# --- multi-seed learned
ev = pd.concat([pd.read_csv(f) for f in glob.glob("out/eval_*_s*.csv")])
ev["algo"] = ev.method.str.split("-").str[0]; ev["comm"] = ev.method.str.split("-").str[1]
P("\n## Learned agents, held-out graphs, mean over training seeds (+/- sd across seeds)")
ps = ev.groupby(["method", "seed"]).surv.mean().reset_index()
P(_md(ps.groupby("method").surv.agg(["mean", "std", "count"]).round(3)))
P("\n## Gate effect for learned agents (paired over seed x graph x episode)")
for a in ("DQN", "IPPO", "MAPPO"):
    x = ev[ev.algo == a].pivot_table(index=["seed", "g", "ep"], columns="comm", values="surv")
    if {"GATE", "NONE"} <= set(x.columns):
        P(f"{a}: GATE-NONE %+.3f [%+.3f,%+.3f]" % paired_bootstrap(x["GATE"], x["NONE"]))
open("out/final_tables.md", "w").write("\n".join(out))
