import numpy as np
from ammarl2.policies import standard_methods
from ammarl2.run import run_episode, paired_bootstrap
from ammarl2.sim import Cfg
P = standard_methods()
base = dict(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
for sr in (0.0, 0.5, 1.5, 4.0):
    cfg = Cfg(spoof_rate=sr, **base); r = {n: [] for n in ("NC", "COMM-ALL", "GATE")}
    for gs in range(300, 308):
        for ep in range(8):
            for n in r:
                r[n].append(run_episode(P[n], gs, 91*gs+ep, cfg, layers=6, width=6)[0].survived.mean())
    m = {n: round(float(np.mean(v)), 3) for n, v in r.items()}
    d = paired_bootstrap(r["GATE"], r["COMM-ALL"])
    print(f"spoof_rate={sr}", m, "GATE-ALL %+.3f [%+.3f,%+.3f]" % d)
