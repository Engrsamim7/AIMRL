import sys, json, numpy as np, pandas as pd, torch
from ammarl2.sim import Cfg
from ammarl2.train import train_policy
from ammarl2.run import run_episode
USAGE = "usage: python run_train.py [algo: dqn|ppo|ippo|mappo] [comm: none|all|gate] [episodes=300] [seed=0]"
algo = sys.argv[1] if len(sys.argv) > 1 else "dqn"      # no arguments (e.g. the editor's Run button) -> train DQN with the gate
comm = sys.argv[2] if len(sys.argv) > 2 else "gate"
if algo not in ("dqn", "ppo", "ippo", "mappo") or comm not in ("none", "all", "gate"):
    sys.exit(USAGE)
eps = int(sys.argv[3]) if len(sys.argv) > 3 else 300
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 0
scenario = sys.argv[5] if len(sys.argv) > 5 else "clean"   # clean | adv (spoofing + random/reactive adversary mix)
print(f"training algo={algo} comm={comm} episodes={eps} seed={seed}  (about 7 minutes; progress prints every 25 episodes)", flush=True)
import os; os.makedirs("out", exist_ok=True)
cfg = Cfg(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
kw = dict(layers=6, width=6)
pol = train_policy(algo, comm, cfg, list(range(1, 41)), eps, seed=seed, log=True, scenario=scenario, **kw)
tag = "" if scenario == "clean" else "_adv"
torch.save(pol.net.state_dict(), f"out/{algo}_{comm}{tag}_s{seed}.pt")
rows = []
for gs in range(300, 310):          # held-out graphs (never seen in training)
    for e in range(5):
        df, o = run_episode(pol, gs, 5 * gs + e, cfg, **kw)
        rows.append(dict(method=pol.name, seed=seed, g=gs, ep=e, surv=df.survived.mean(), enc=df.blocked_enc.sum()))
if scenario == "clean":
    pd.DataFrame(rows).to_csv(f"out/eval_{algo}_{comm}_s{seed}.csv", index=False)
from robust_eval import robust_rows
pd.DataFrame(robust_rows(pol, f"{algo}{tag}", comm, seed)).to_csv(f"out/rob_{algo}_{comm}{tag}_s{seed}.csv", index=False)
print("DONE", algo, comm, np.mean([r["surv"] for r in rows]))
