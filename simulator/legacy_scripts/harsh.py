import numpy as np, pandas as pd, itertools, dataclasses
from ammarl2.sim import Cfg
from ammarl2.run import run_episode
from ammarl2.policies import standard_methods, Policy
P = standard_methods()
P["GATE-SC"] = Policy("GATE-SC", weights="threat", use_obs=True, comm="gate", scaling="scaled")
base = dict(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
rows = []
for loss, tm, sp in itertools.product((0.0, 0.4, 0.8), (1.0, 4.0, 8.0), (0.0, 2.0, 8.0)):
    cfg = Cfg(**{**base, "p_loss": loss, "tau_msg": tm, "spoof_rate": sp})
    for n in ("NC", "COMM-ALL", "GATE", "GATE-SC"):
        for gs in range(400, 406):
            for e in range(4):
                df, o = run_episode(P[n], gs, 7 * gs + e, cfg, layers=6, width=6)
                rows.append(dict(loss=loss, tau_msg=tm, spoof=sp, method=n, g=gs, ep=e, surv=df.survived.mean(),
                                 enc=df.blocked_enc.sum(), spoof_acc=o["stats"]["spoof_accepted"]))
    pd.DataFrame(rows).to_csv("out/harsh.csv", index=False)
print("DONE")
