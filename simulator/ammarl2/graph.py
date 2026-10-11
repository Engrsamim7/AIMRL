"""Graph generation and shortest paths (no networkx dependency, deterministic)."""
import heapq
from dataclasses import dataclass
import numpy as np

INF = float("inf")


@dataclass
class Graph:
    n: int
    depot: int
    targets: list
    src: np.ndarray
    dst: np.ndarray
    c: np.ndarray        # nominal traversal cost c_e  (paper Eq. 1)
    rho: np.ndarray      # adversarial threat level rho_e
    q: np.ndarray        # link flow capacity q_e
    corridor: np.ndarray # corridor index psi_e
    out: list            # out[u] -> list of edge ids

    @property
    def m(self):
        return len(self.src)


def make_graph(seed, layers=3, width=4, n_targets=2):
    """Layered contested network. Half of the columns ('corridors') are hot."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, 7919]))
    node = lambda l, i: 1 + l * width + i
    targets = [1 + layers * width + k for k in range(n_targets)]
    n = 1 + layers * width + n_targets
    hot = set(rng.choice(width, size=max(1, width // 2), replace=False).tolist())
    E = []  # (u, v, c, rho, q, corridor)

    def add(u, v, c, rho, corr):
        E.append((u, v, float(c), float(rho), int(rng.integers(2, 5)), corr))

    for i in range(width):
        h = i in hot
        add(0, node(0, i), rng.uniform(2, 4), rng.uniform(0.40, 0.55) if h else rng.uniform(0.05, 0.10), i)
    for l in range(layers - 1):
        for i in range(width):
            h = i in hot
            add(node(l, i), node(l + 1, i), rng.uniform(2.5, 5),
                rng.uniform(0.35, 0.55) if h else rng.uniform(0.04, 0.12), i)
            add(node(l, i), node(l + 1, (i + 1) % width), rng.uniform(3, 6), rng.uniform(0.20, 0.30), i)
    for i in range(width):
        for k in {i % n_targets, (i + 1) % n_targets}:
            add(node(layers - 1, i), targets[k], rng.uniform(1.5, 3.5), rng.uniform(0.08, 0.20), i)

    src = np.array([e[0] for e in E]); dst = np.array([e[1] for e in E])
    out = [[] for _ in range(n)]
    for eid, u in enumerate(src):
        out[u].append(eid)
    return Graph(n, 0, targets, src, dst,
                 np.array([e[2] for e in E]), np.array([e[3] for e in E]),
                 np.array([e[4] for e in E]), np.array([e[5] for e in E]), out)


def dijkstra(g, src, tgt, w, banned=()):
    """Edge-id path src->tgt minimising sum of w over non-banned edges, or None."""
    if src == tgt:
        return []
    dist = {src: 0.0}
    prev = {}
    h = [(0.0, src)]
    while h:
        d, u = heapq.heappop(h)
        if d > dist.get(u, INF):
            continue
        if u == tgt:
            break
        for e in g.out[u]:
            if e in banned:
                continue
            v = int(g.dst[e])
            nd = d + w[e]
            if nd < dist.get(v, INF):
                dist[v] = nd
                prev[v] = (u, e)
                heapq.heappush(h, (nd, v))
    if tgt not in dist:
        return None
    path = []
    v = tgt
    while v != src:
        u, e = prev[v]
        path.append(e)
        v = u
    return path[::-1]


def optimal_nominal_cost(g, src, tgt):
    p = dijkstra(g, src, tgt, g.c)
    return float(sum(g.c[e] for e in p)) if p is not None else INF


def dists(g, src, w):
    """Single-source shortest distances (array, INF if unreachable)."""
    d = np.full(g.n, INF)
    d[src] = 0.0
    h = [(0.0, src)]
    while h:
        du, u = heapq.heappop(h)
        if du > d[u]:
            continue
        for e in g.out[u]:
            v = int(g.dst[e])
            nd = du + w[e]
            if nd < d[v]:
                d[v] = nd
                heapq.heappush(h, (nd, v))
    return d
