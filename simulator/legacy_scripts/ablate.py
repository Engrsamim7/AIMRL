import numpy as np, pandas as pd, itertools
from ammarl2.sim import Cfg
from ammarl2.run import run_episode
from ammarl2.policies import Policy
def G(name, f, r, c, sc="scaled", eta=1.0):
    return Policy(name, weights="threat", use_obs=True, comm="gate", gate_fresh=f, gate_rel=r, gate_conf=c, scaling=sc, eta=eta)
V = {"NC": Policy("NC", weights="threat", use_obs=True),
     "ALL": Policy("ALL", weights="threat", use_obs=True, comm="all"),
     "F": G("F", 1, 0, 0), "R": G("R", 0, 1, 0), "C": G("C", 0, 0, 1),
     "F+R": G("F+R", 1, 1, 0), "F+C": G("F+C", 1, 0, 1), "R+C": G("R+C", 0, 1, 1), "F+R+C": G("F+R+C", 1, 1, 1),
     "static F+R+C": G("static F+R+C", 1, 1, 1, "static", 0.4)}
for eta in (0.5, 2.0, 4.0):
    V[f"scaled eta={eta} F+R+C"] = G(f"scaled eta={eta} F+R+C", 1, 1, 1, "scaled", eta)
base = dict(attack_dur=(60,120), budget=10, attack_rate=0.9, p_kill=0.7, stagger=1.0, n_convoys=30, hub_cap=1, hub_service=2.0)
rows = []
for loss, tm, sp in [(0.0, 1.0, 0.0), (0.0, 1.0, 8.0), (0.0, 4.0, 8.0), (0.4, 4.0, 20.0)]:
    cfg = Cfg(**{**base, "p_loss": loss, "tau_msg": tm, "spoof_rate": sp})
    for n, p in V.items():
        for gs in range(600, 610):
            for e in range(6):
                df, o = run_episode(p, gs, 13 * gs + e, cfg, layers=6, width=6)
                rows.append(dict(loss=loss, tau_msg=tm, spoof=sp, method=n, g=gs, ep=e, surv=df.survived.mean(),
                                 enc=df.blocked_enc.sum(), spoof_acc=o["stats"]["spoof_accepted"], true_acc=o["stats"]["true_accepted"]))
    pd.DataFrame(rows).to_csv("out/ablate.csv", index=False)
print("DONE")
