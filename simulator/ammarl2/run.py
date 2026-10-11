import numpy as np, pandas as pd
from .graph import make_graph, optimal_nominal_cost
from .sim import Sim, Cfg


def run_episode(policy, graph_seed, ep_seed, cfg=None, **gkw):
    g = make_graph(graph_seed, **gkw)
    cfg = cfg or Cfg()
    s = Sim(g, cfg, policy, ep_seed)
    out = s.run()
    df = pd.DataFrame(out["rows"])
    df["method"] = policy.name; df["graph_seed"] = graph_seed; df["ep_seed"] = ep_seed
    return df, out


def paired_bootstrap(a, b, n=2000, seed=0):
    d = np.asarray(a) - np.asarray(b)
    r = np.random.default_rng(seed)
    bs = r.choice(d, size=(n, len(d))).mean(1)
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
