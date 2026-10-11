"""Held-out evaluation under spoofing + random/reactive adversary (graphs 300-309, same seeds for every method)."""
import numpy as np
from ammarl2.sim import Cfg
from ammarl2.run import run_episode
BASE = dict(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
COND = {"random+spoof8": dict(adv="random", spoof_rate=8.0), "reactive+spoof8": dict(adv="reactive", spoof_rate=8.0), "reactive": dict(adv="reactive")}
def robust_rows(pol, algo, comm, seed):
    rows = []
    for cn, kw in COND.items():
        cfg = Cfg(**{**BASE, **kw})
        for gs in range(300, 310):
            for e in range(3):
                df, o = run_episode(pol, gs, 5 * gs + e, cfg, layers=6, width=6)
                rows.append(dict(method=f"{algo.upper()}-{comm.upper()}", seed=seed, cond=cn, g=gs, ep=e, surv=df.survived.mean(), enc=df.blocked_enc.sum()))
    return rows
