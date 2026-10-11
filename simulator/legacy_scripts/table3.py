"""New Table III: full KPI set for all methods on held-out graphs 300-309 (5 episodes each), same seeds for every method.
KPIs: survivability (delivered fraction), route survivability (old Eq.5: mean 1-rho on traversed edges), nominal cost (sum c_e, delivered convoys),
realized time (incl. queueing), blocked-edge encounters per convoy (integer per convoy, mean), MaxThr (old Eq.6)."""
import glob, os, numpy as np, pandas as pd, torch
from ammarl2.sim import Cfg
from ammarl2.run import run_episode
from ammarl2.policies import standard_methods, Policy
from ammarl2.learn import LearnedPolicy
cfg = Cfg(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
P = standard_methods(); P["GATE-SC"] = Policy("GATE-SC", weights="threat", use_obs=True, comm="gate", scaling="scaled")
def kpis(df):
    d = df[df.survived == 1]
    return dict(surv=df.survived.mean(), route_surv=df.route_surv.mean(), nominal=d.nominal.mean(), realized=d.realized.mean(), enc_per_convoy=df.blocked_enc.mean(),
                max_thr=df.max_thr.mean(), wait=df.wait.mean())
rows = []
def go(name, pol, seed):
    for gs in range(300, 310):
        for e in range(5):
            df, _ = run_episode(pol, gs, 5 * gs + e, cfg, layers=6, width=6)
            rows.append(dict(method=name, seed=seed, g=gs, ep=e, **kpis(df)))
for n in ("B1", "B2", "B3", "NC", "COMM-ALL", "GATE", "GATE-SC", "ORACLE"): go(n, P[n], 0)
for f in sorted(glob.glob("out/*_s[0-2].pt")):
    b = os.path.basename(f)[:-3]
    if "adv" in b: continue
    a, c, s = b.split("_")[0], b.split("_")[1], int(b[-1])
    p = LearnedPolicy(name=f"{a}-{c}", weights="threat", use_obs=True, comm=c, algo=a); p.net.load_state_dict(torch.load(__import__("wfind").wpath(__import__("os").path.basename(f))))
    go(f"{a.upper()}-{c.upper()}", p, s)
pd.DataFrame(rows).to_csv("out/table3_full.csv", index=False)
print(pd.DataFrame(rows).groupby("method").mean(numeric_only=True).round(3).to_string())
