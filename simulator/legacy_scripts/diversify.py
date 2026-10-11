import numpy as np, pandas as pd
from ammarl2.sim import Cfg
from ammarl2.run import run_episode, paired_bootstrap
from ammarl2.policies import Policy
base = dict(attack_dur=(60,120), budget=10, attack_rate=0.9, p_kill=0.7, stagger=1.0, n_convoys=30, hub_cap=1, hub_service=2.0, tau_msg=1.0, adv="reactive")
rows = []
for sg in (0.0, 0.2, 0.4, 0.8):
    for comm in ("none", "all"):
        p = Policy(f"noise{sg}-{comm}", weights="threat", use_obs=True, comm=comm, noise=sg)
        for gs in range(1100, 1110):
            for e in range(6):
                df, o = run_episode(p, gs, 31 * gs + e, Cfg(**base), layers=6, width=6)
                rows.append(dict(sigma=sg, comm=comm, g=gs, ep=e, surv=df.survived.mean(), enc=df.blocked_enc.sum()))
d = pd.DataFrame(rows); d.to_csv("out/diversify.csv", index=False)
print(d.pivot_table(index="sigma", columns="comm", values="surv").round(3))
q = d[d.comm == "none"].pivot_table(index=["g", "ep"], columns="sigma", values="surv")
for s_ in (0.2, 0.4, 0.8): print(f"sigma {s_} vs 0: %+.3f[%+.3f,%+.3f]" % paired_bootstrap(q[s_], q[0.0]))
