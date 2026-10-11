import numpy as np, pandas as pd, itertools
from ammarl2.sim import Cfg
from ammarl2.run import run_episode, paired_bootstrap
from ammarl2.policies import Policy
def G(n, f=1, r=1, c=1, sc="scaled", eta=1.0, k=0.6): return Policy(n, weights="threat", use_obs=True, comm="gate", gate_fresh=f, gate_rel=r, gate_conf=c, scaling=sc, eta=eta, kappa_min=k)
V = {"B3": Policy("B3", use_obs=True), "NC": Policy("NC", weights="threat", use_obs=True), "ALL": Policy("ALL", weights="threat", use_obs=True, comm="all"),
     "GATE-SC": G("GATE-SC"), "C": G("C", 0, 0, 1), "ORACLE": Policy("ORACLE", weights="threat", use_obs=True, comm="oracle")}
base = dict(attack_dur=(60,120), budget=10, attack_rate=0.9, p_kill=0.7, stagger=1.0, n_convoys=30, hub_cap=1, hub_service=2.0, tau_msg=1.0)
rows = []
for adv, sp in itertools.product(("random", "reactive"), (0.0, 8.0)):
    cfg = Cfg(**{**base, "adv": adv, "spoof_rate": sp})
    for n, p in V.items():
        for gs in range(1000, 1010):
            for e in range(6):
                df, o = run_episode(p, gs, 29 * gs + e, cfg, layers=6, width=6)
                rows.append(dict(adv=adv, spoof=sp, method=n, g=gs, ep=e, surv=df.survived.mean(), enc=df.blocked_enc.sum()))
d = pd.DataFrame(rows); d.to_csv("out/reactive_heur.csv", index=False)
print(d.pivot_table(index="method", columns=["adv", "spoof"], values="surv").round(3).to_string())
q = d.pivot_table(index=["adv", "spoof", "g", "ep"], columns="method", values="surv")
for k, grp in q.groupby(level=[0, 1]):
    print(k, "ALL-NC %+.3f[%+.3f,%+.3f]" % paired_bootstrap(grp["ALL"], grp["NC"]), "| GATE-SC-ALL %+.3f[%+.3f,%+.3f]" % paired_bootstrap(grp["GATE-SC"], grp["ALL"]),
          "| C-ALL %+.3f[%+.3f,%+.3f]" % paired_bootstrap(grp["C"], grp["ALL"]), "| NC-B3 %+.3f[%+.3f,%+.3f]" % paired_bootstrap(grp["NC"], grp["B3"]))
