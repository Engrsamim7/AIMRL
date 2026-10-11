import pandas as pd, glob, numpy as np

def _md(df):
    """to_markdown needs the optional 'tabulate' package; fall back to plain text if it is not installed."""
    try:
        return df.to_markdown()
    except ImportError:
        return df.to_string()
from ammarl2.run import paired_bootstrap
d = pd.concat([pd.read_csv(f).assign(src=f) for f in glob.glob("out/rob_*.csv")])
d["method"] = d.method.str.replace("_ADV", "")
d["trained"] = np.where(d.src.str.contains("_adv_"), "adv-trained", np.where(d.src.str.contains("heuristics"), "heuristic", "clean-trained"))
out = []
def P(s): out.append(s); print(s)
P("## Robustness: survival under spoofing and the reactive adversary (held-out graphs 300-309)")
P(_md(d.groupby(["trained", "method", "cond"]).surv.mean().unstack("cond").round(3)))
P("\n## Gate effect (GATE minus NONE), paired over seed x graph x episode")
for tr in ("clean-trained", "adv-trained"):
    for a in ("DQN", "IPPO", "MAPPO"):
        for c in d.cond.unique():
            x = d[(d.trained == tr) & d.method.str.startswith(a + "-")& d.method.str.contains("GATE|NONE")]
            x = x[x.cond == c]; x = x.assign(comm=x.method.str.split("-").str[-1]).pivot_table(index=["seed", "g", "ep"], columns="comm", values="surv")
            if {"GATE", "NONE"} <= set(x.columns) and len(x) > 5:
                P(f"{tr} {a} {c}: GATE-NONE %+.3f [%+.3f,%+.3f] (n={len(x)})" % paired_bootstrap(x["GATE"], x["NONE"]))
open("out/robust_tables.md", "w").write("\n".join(out))
