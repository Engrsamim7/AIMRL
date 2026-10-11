"""Time-resolved simulator dynamics: 10 held-out graphs x 5 episodes, 30 convoys, same attacks for every method. Writes out/dynamics.csv"""
import numpy as np, pandas as pd
from ammarl2.graph import make_graph
from ammarl2.sim import Sim, Cfg
from ammarl2.policies import standard_methods, Policy
cfg = Cfg(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
P = standard_methods(); P["GATE-SC"] = Policy("GATE-SC", weights="threat", use_obs=True, comm="gate", scaling="scaled")
grid = np.arange(0, 121, 2.0); rows = []
for name in ("B1", "NC", "COMM-ALL", "GATE-SC", "ORACLE"):
    for gs in range(300, 310):
        g = make_graph(gs, layers=6, width=6)
        for e in range(5):
            s = Sim(g, cfg, P[name], 5 * gs + e)
            for T in grid:
                s.run(until=T)
                n = len(s.cv)
                rows.append(dict(method=name, g=gs, ep=e, t=T,
                                 delivered=sum(c.delivered for c in s.cv) / n, destroyed=sum((not c.alive) for c in s.cv) / n,
                                 queued=sum(len(q) for q in s.queue), active_attacks=len(s.active),
                                 blocked_entries=sum(c.enc for c in s.cv) / n))
pd.DataFrame(rows).to_csv("out/dynamics.csv", index=False); print("done", len(rows))
