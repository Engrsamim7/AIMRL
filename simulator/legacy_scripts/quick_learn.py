import numpy as np, time
from ammarl2.sim import Cfg
from ammarl2.train import train_policy
from ammarl2.run import run_episode
from ammarl2.policies import standard_methods
cfg = Cfg(attack_dur=(60,120), budget=8, attack_rate=0.6, stagger=1.0, n_convoys=30, tau_msg=1.0, hub_cap=1, hub_service=2.0)
kw = dict(layers=6, width=6)
t0 = time.time()
pol = train_policy("dqn", "none", cfg, list(range(1, 21)), 60, seed=0, log=True, **kw)
print("train time", time.time() - t0)
P = standard_methods()
for name, p in [("DQN-NC", pol), ("NC", P["NC"]), ("B1", P["B1"])]:
    v = [run_episode(p, gs, 5 * gs + e, cfg, **kw)[0].survived.mean() for gs in range(300, 306) for e in range(4)]
    print(name, round(float(np.mean(v)), 3))
