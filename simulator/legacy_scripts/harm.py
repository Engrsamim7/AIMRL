import numpy as np, pandas as pd, itertools
from ammarl2.sim import Cfg
from ammarl2.run import run_episode, paired_bootstrap
from ammarl2.policies import Policy
V = {"NC": Policy("NC", weights="threat", use_obs=True), "ALL": Policy("ALL", weights="threat", use_obs=True, comm="all"),
     "GATE": Policy("GATE", weights="threat", use_obs=True, comm="gate", scaling="scaled", eta=1.0),
     "C": Policy("C", weights="threat", use_obs=True, comm="gate", gate_fresh=False, gate_rel=False)}
base = dict(budget=10, attack_rate=0.9, p_kill=0.7, stagger=1.0, n_convoys=30, hub_cap=1, hub_service=2.0)
for dur, tm, ts in [((60,120),1,8), ((10,20),2,8), ((10,20),4,16), ((6,12),4,30), ((6,12),6,30)]:
    cfg = Cfg(**{**base, "attack_dur": dur, "tau_msg": tm, "tau_stale": ts}); r = {k: [] for k in V}
    for gs in range(900, 908):
        for e in range(5):
            for k, p in V.items():
                r[k].append(run_episode(p, gs, 23 * gs + e, cfg, layers=6, width=6)[0].survived.mean())
    print(dur, "tau_msg", tm, "tau_stale", ts, {k: round(float(np.mean(v)), 3) for k, v in r.items()}, "ALL-NC %+.3f[%+.3f,%+.3f]" % paired_bootstrap(r["ALL"], r["NC"]), flush=True)
