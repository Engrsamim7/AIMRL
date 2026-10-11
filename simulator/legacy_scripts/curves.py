"""Training curves: per-episode training survival (eps-greedy / sampling policy) for the figure. Separate from run_train.py so saved agents/results are not overwritten."""
import sys, numpy as np, pandas as pd
from ammarl2.sim import Cfg, Sim
from ammarl2.graph import make_graph
from ammarl2.learn import LearnedPolicy
algo, comm, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
episodes = int(sys.argv[4]) if len(sys.argv) > 4 else 300
cfg = Cfg(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
pol = LearnedPolicy(name=f"{algo}-{comm}", weights="threat", use_obs=True, comm=comm, algo=algo, train=True, seed=seed)
rng = np.random.default_rng(seed + 123); rows = []
for ep in range(episodes):
    pol.eps = max(0.03, 0.4 * (1 - ep / (0.7 * episodes)))
    gs = int(rng.choice(list(range(1, 41))))
    s = Sim(make_graph(gs, layers=6, width=6), cfg, pol, seed=10_000 + seed * 100_000 + ep)
    out = s.run(); pol.end_episode()
    r = out["rows"]
    rows.append(dict(algo=algo, comm=comm, seed=seed, ep=ep, surv=np.mean([x["survived"] for x in r]), enc=np.sum([x["blocked_enc"] for x in r]),
                     realized=np.nanmean([x["realized"] for x in r])))
pd.DataFrame(rows).to_csv(f"out/curve_{algo}_{comm}_s{seed}.csv", index=False)
