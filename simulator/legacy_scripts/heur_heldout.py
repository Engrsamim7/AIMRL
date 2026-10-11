import numpy as np, pandas as pd
from ammarl2.sim import Cfg
from ammarl2.run import run_episode
from ammarl2.policies import standard_methods
cfg = Cfg(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
kw = dict(layers=6, width=6); P = standard_methods(); rows = []
for n, p in P.items():
    for gs in range(300, 310):
        for e in range(5):
            df, o = run_episode(p, gs, 5 * gs + e, cfg, **kw)
            rows.append(dict(method=n, seed=0, g=gs, ep=e, surv=df.survived.mean(), enc=df.blocked_enc.sum()))
d = pd.DataFrame(rows); d.to_csv("out/eval_heuristics.csv", index=False)
print(d.groupby("method").surv.mean().round(3))
