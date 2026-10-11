"""Find an episode where one convoy meets a blocked edge under NC but is routed around it by GATE-SC (same seed => same attacks)."""
import numpy as np, json
from ammarl2.graph import make_graph
from ammarl2.sim import Sim, Cfg
from ammarl2.policies import Policy
cfg = Cfg(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=12, tau_msg=1.0, hub_cap=1, hub_service=2.0)
NC = Policy("NC", weights="threat", use_obs=True); G = Policy("GATE", weights="threat", use_obs=True, comm="gate", scaling="scaled")
best = None
for gs in range(300, 340):
    for e in range(8):
        seed = 5 * gs + e; g = make_graph(gs, layers=6, width=6)
        a = Sim(g, cfg, NC, seed); a.run(); b = Sim(g, cfg, G, seed); b.run()
        for i in range(cfg.n_convoys):
            ca, cb = a.cv[i], b.cv[i]
            if ca.enc >= 1 and cb.enc == 0 and cb.delivered and ca.target == cb.target and ca.path != cb.path:
                score = (ca.depart_t > 8) * 1 + (not ca.delivered) * 2 - abs(len(ca.path) - len(cb.path)) * 0.1
                if best is None or score > best[0]:
                    best = (score, gs, e, i, [(float(t), int(x), bool(bl)) for t, x, bl in ca.entries], [(float(t), int(x), bool(bl)) for t, x, bl in cb.entries],
                            [(float(t), int(x)) for t, x in a.attack_log], ca.delivered)
print(best[:4], best[-1])
json.dump(dict(gs=best[1], ep=best[2], convoy=best[3], nc=best[4], gate=best[5], attacks=best[6], nc_survived=bool(best[7])), open("out/casestudy.json", "w"))
