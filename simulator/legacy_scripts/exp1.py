import numpy as np, pandas as pd, sys
from ammarl2.policies import standard_methods
from ammarl2.run import run_episode, paired_bootstrap
from ammarl2.sim import Cfg
adv = sys.argv[1] if len(sys.argv) > 1 else "random"
cfg = Cfg(adv=adv)
P = standard_methods(); R = []
for gs in range(100, 110):
    for ep in range(10):
        for n, p in P.items():
            df, o = run_episode(p, gs, 1000 * gs + ep, cfg)
            R.append(dict(method=n, g=gs, ep=ep, surv=df.survived.mean(), enc=df.blocked_enc.sum(),
                          real=df.realized.mean(), wait=df.wait.mean(), **{k: v for k, v in o["stats"].items() if k in ("spoof_accepted", "rejected")}))
d = pd.DataFrame(R); d.to_csv(f"exp1_{adv}.csv", index=False)
print(d.groupby("method")[["surv", "enc", "real", "wait"]].mean().round(3))
piv = d.pivot_table(index=["g", "ep"], columns="method", values="surv")
for a, b in [("GATE", "NC"), ("GATE", "COMM-ALL"), ("COMM-ALL", "NC"), ("ORACLE", "GATE")]:
    m, lo, hi = paired_bootstrap(piv[a], piv[b]); print(f"surv {a}-{b}: {m:+.4f} [{lo:+.4f},{hi:+.4f}]")
