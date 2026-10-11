import numpy as np, pandas as pd, itertools
from ammarl2.sim import Cfg
from ammarl2.run import run_episode, paired_bootstrap
from ammarl2.policies import Policy
def G(n, k, eta=1.0, f=1, r=0, c=1): return Policy(n, weights="threat", use_obs=True, comm="gate", gate_fresh=f, gate_rel=r, gate_conf=c, scaling="scaled", eta=eta, kappa_min=k)
base = dict(attack_dur=(60,120), budget=10, attack_rate=0.9, p_kill=0.7, stagger=1.0, n_convoys=30, hub_cap=1, hub_service=2.0, tau_msg=1.0, spoof_rate=8.0)
V = {"NC": Policy("NC", weights="threat", use_obs=True), "ALL": Policy("ALL", weights="threat", use_obs=True, comm="all")}
for k in (0.4, 0.6, 0.75, 0.9): V[f"conf k={k}"] = G(f"c{k}", k, f=0, c=1)
for eta in (0.5, 1.0, 2.0, 4.0): V[f"fresh eta={eta}"] = G(f"f{eta}", 0.0, eta=eta, f=1, c=0)
rows = []
for conf_sd, conf_mu in [(0.0, 1.0), (0.10, 0.85)]:
    cfg = Cfg(**{**base, "conf_mu": conf_mu, "conf_sd": conf_sd})
    for n, p in V.items():
        for gs in range(1200, 1210):
            for e in range(6):
                df, o = run_episode(p, gs, 37 * gs + e, cfg, layers=6, width=6)
                rows.append(dict(conf_sd=conf_sd, method=n, g=gs, ep=e, surv=df.survived.mean(), spoof_acc=o["stats"]["spoof_accepted"], true_acc=o["stats"]["true_accepted"]))
d = pd.DataFrame(rows); d.to_csv("out/sweep_gate.csv", index=False)
print(d.groupby(["conf_sd", "method"])[["surv", "spoof_acc", "true_acc"]].mean().round(3).to_string())
q = d.pivot_table(index=["conf_sd", "g", "ep"], columns="method", values="surv")
for sd, grp in q.groupby(level=0):
    print("conf_sd", sd, " ".join("%s-ALL %+.3f[%+.3f,%+.3f]" % ((m,) + paired_bootstrap(grp[m], grp["ALL"])) for m in V if m not in ("ALL",)))
