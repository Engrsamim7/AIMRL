"""FIR with common random numbers: same graph, convoys, attack schedule, kill draws, spoof stream.
Only the information flow differs, so per-convoy outcome differences are causal effects of communication."""
import numpy as np, pandas as pd
from ammarl2.graph import make_graph
from ammarl2.sim import Sim, Cfg
from ammarl2.policies import Policy
from ammarl2.run import paired_bootstrap

NC = Policy("NC", weights="threat", use_obs=True)
base = dict(attack_dur=(60,120), budget=10, attack_rate=0.9, p_kill=0.7, stagger=1.0, n_convoys=30, hub_cap=1, hub_service=2.0)

def run(pol, gs, seed, cfg):
    s = Sim(make_graph(gs, layers=6, width=6), cfg, pol, seed); out = s.run(); return s, out

def fir(pol, cfg, graphs=range(800, 815), eps=range(4)):
    rows = []
    for gs in graphs:
        for e in eps:
            seed = 19 * gs + e
            s0, o0 = run(NC, gs, seed, cfg); s1, o1 = run(pol, gs, seed, cfg)
            k = min(len(s0.attack_log), len(s1.attack_log), 5)
            assert s0.attack_log[:k] == s1.attack_log[:k], "CRN broken: attack schedules differ"
            a = np.array([r["survived"] for r in o0["rows"]]); b = np.array([r["survived"] for r in o1["rows"]])
            tr = [t for t in o1["trace"] if t[6] > 0]            # decisions that received accepted info
            ch = [t for t in tr if t[3] != t[4]]                  # ... and acted differently from own-info-only
            rows.append(dict(g=gs, ep=e, dec=len(o1["trace"]), dec_info=len(tr), dec_changed=len(ch),
                             saved=int(((b == 1) & (a == 0)).sum()), lost=int(((b == 0) & (a == 1)).sum()),
                             surv_nc=a.mean(), surv_x=b.mean()))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    out = []
    pols = {"COMM-ALL": Policy("ALL", weights="threat", use_obs=True, comm="all"),
            "GATE(static)": Policy("GATE", weights="threat", use_obs=True, comm="gate"),
            "GATE(conf only)": Policy("C", weights="threat", use_obs=True, comm="gate", gate_fresh=False, gate_rel=False)}
    for sp in (0.0, 8.0):
        for tm in (1.0, 4.0):
            cfg = Cfg(**{**base, "tau_msg": tm, "spoof_rate": sp})
            for n, p in pols.items():
                d = fir(p, cfg)
                di = d.dec_info.sum()
                m, lo, hi = paired_bootstrap(d.surv_x, d.surv_nc)
                out.append(dict(spoof=sp, tau_msg=tm, method=n, FIR_changed_per_info_decision=round(d.dec_changed.sum() / max(1, di), 3),
                                info_decision_share=round(di / d.dec.sum(), 3), saved=d.saved.sum(), lost=d.lost.sum(),
                                precision=round(d.saved.sum() / max(1, d.saved.sum() + d.lost.sum()), 3),
                                dsurv=f"{m:+.3f} [{lo:+.3f},{hi:+.3f}]"))
                print(out[-1], flush=True)
    pd.DataFrame(out).to_csv("out/fir.csv", index=False)
