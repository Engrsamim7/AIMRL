import numpy as np, time
from .graph import make_graph
from .sim import Sim, Cfg
from .learn import LearnedPolicy


def train_policy(algo, comm, cfg, graph_seeds, episodes, seed=0, log=False, scenario='clean', **gkw):
    pol = LearnedPolicy(name=f"{algo.upper()}-{comm.upper()}", weights="threat", use_obs=True, comm=comm,
                        algo=algo, train=True, seed=seed)
    rng = np.random.default_rng(seed + 123)
    tcfg = cfg  # all baselines use the same multi-convoy environment/budget
    t0 = time.time()
    for ep in range(episodes):
        pol.eps = max(0.03, 0.4 * (1 - ep / (0.7 * episodes)))
        gs = int(rng.choice(graph_seeds))
        ecfg = tcfg if scenario == 'clean' else Cfg(**{**tcfg.__dict__, 'spoof_rate': 8.0, 'adv': ('reactive' if rng.random() < 0.5 else 'random')})
        s = Sim(make_graph(gs, **gkw), ecfg, pol, seed=10_000 + seed * 100_000 + ep)
        out = s.run(); pol.end_episode()
        if log and ep % 25 == 0:
            sv = np.mean([r["survived"] for r in out["rows"]])
            print(f"  ep {ep} surv={sv:.2f} eps={pol.eps:.2f} t={time.time()-t0:.0f}s", flush=True)
    pol.train = False; pol.eps = 0.0
    return pol
