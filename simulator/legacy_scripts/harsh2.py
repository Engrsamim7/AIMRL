import numpy as np, pandas as pd, itertools
from ammarl2.sim import Cfg
from ammarl2.run import run_episode
from ammarl2.policies import standard_methods, Policy
P = standard_methods()
P["GATE-SC"] = Policy("GATE-SC", weights="threat", use_obs=True, comm="gate", scaling="scaled")
base = dict(attack_dur=(60,120), budget=10, attack_rate=0.9, p_kill=0.7, stagger=1.0, n_convoys=30, hub_cap=1, hub_service=2.0)
rows = []
for loss, tm, sp in itertools.product((0.0, 0.4), (1.0, 4.0), (0.0, 8.0, 20.0)):
    cfg = Cfg(**{**base, "p_loss": loss, "tau_msg": tm, "spoof_rate": sp})
    for n in ("B3", "NC", "COMM-ALL", "GATE", "GATE-SC", "ORACLE"):
        for gs in range(500, 510):
            for e in range(6):
                df, o = run_episode(P[n], gs, 11 * gs + e, cfg, layers=6, width=6)
                rows.append(dict(loss=loss, tau_msg=tm, spoof=sp, method=n, g=gs, ep=e, surv=df.survived.mean(),
                                 enc=df.blocked_enc.sum(), spoof_acc=o["stats"]["spoof_accepted"]))
    pd.DataFrame(rows).to_csv("out/harsh2.csv", index=False)
print("DONE")
