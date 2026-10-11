import numpy as np, pandas as pd, torch, time, sys
from ammarl2.sim import Cfg
from ammarl2.run import run_episode
from ammarl2.policies import standard_methods, Policy
from ammarl2.learn import LearnedPolicy
SIZES = {"39": (6, 6), "51": (4, 12), "203": (10, 20), "483": (20, 24)}
P = standard_methods()
P["GATE-SC"] = Policy("GATE-SC", weights="threat", use_obs=True, comm="gate", scaling="scaled", eta=1.0)
learned = {}
for algo in ("dqn", "ippo"):
    for comm in ("none", "gate"):
        p = LearnedPolicy(name=f"{algo.upper()}-{comm.upper()}", weights="threat", use_obs=True, comm=comm, algo=algo)
        p.net.load_state_dict(torch.load(__import__("wfind").wpath(f"{algo}_{comm}_s0.pt"))); learned[p.name] = p
rows = []
for sz, (L, W) in SIZES.items():
    cfg = Cfg(attack_dur=(60,120), budget=int(1.3*W+2), attack_rate=0.1*W+0.3, p_kill=0.7, stagger=1.0, n_convoys=5*W,
              hub_cap=1, hub_service=2.0, tau_msg=1.0, horizon=5000)
    for n, p in list(P.items()) + list(learned.items()):
        if n in ("B2",): continue
        t0 = time.time(); neps = 0
        for gs in range(700, 704):
            for e in range(3):
                df, o = run_episode(p, gs, 17 * gs + e, cfg, layers=L, width=W)
                rows.append(dict(size=sz, method=n, g=gs, ep=e, surv=df.survived.mean(), enc=df.blocked_enc.sum(),
                                 real=df.realized.mean())); neps += 1
        print(sz, n, round((time.time() - t0) / neps, 2), "s/ep", flush=True)
    pd.DataFrame(rows).to_csv("out/scaling.csv", index=False)
print("DONE")
