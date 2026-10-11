import numpy as np, pandas as pd
from ammarl2.policies import standard_methods
from ammarl2.run import run_episode
from ammarl2.sim import Cfg
P = standard_methods()
def go(label, cfg, **gk):
    r = {n: [] for n in ("NC", "COMM-ALL", "GATE", "ORACLE")}
    for gs in range(200, 206):
        for ep in range(8):
            for n in r:
                r[n].append(run_episode(P[n], gs, 77 * gs + ep, cfg, **gk)[0].survived.mean())
    print(label, {n: round(np.mean(v), 3) for n, v in r.items()})
go("base", Cfg())
go("reveal10", Cfg(tau_reveal=10, attack_dur=(30, 60)))
go("long dur, layers5", Cfg(attack_dur=(40, 80), budget=5, attack_rate=0.5), layers=5)
go("layers5 w6 r1 stagger.5", Cfg(attack_dur=(40, 80), budget=6, attack_rate=0.5, stagger=0.5, n_convoys=24, tau_msg=1.0), layers=5, width=6)
go("same + radius2 off, long", Cfg(attack_dur=(60, 120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0), layers=6, width=6)
