# ammarl2 — AMMARL-PI rebuilt simulator, experiments and figures

Code, raw results and figure scripts for the resubmission of *"Gated Multi-Agent Reinforcement Learning for Contested Military Logistics Routing in Physical Internet Networks"* (previously IoT-66126-2026, IEEE Internet of Things Journal).
Everything in the manuscript's tables and figures is computed from the raw per-episode CSV files in `out/` by the scripts listed below. Nothing is typed in by hand.

---------------------------------------------------------------------------------------------------

## 1. Quick start (you only want the figures)

The results are already saved in `out/*.csv`, so **no experiment needs to be rerun**.

    pip install numpy scipy pandas matplotlib torch tabulate pytest
    python make_figures.py          # writes figs/*.png and figs/*.pdf

Windows / VS Code: open the project folder in VS Code (File > Open Folder), open a terminal (Terminal > New Terminal; it opens in that folder) and run the line above. If `python` is not found, use the full path of your interpreter, e.g.
`& C:\Users\<you>\AppData\Local\Programs\Python\Python313\python.exe make_figures.py`.

`make_figures.py` prints `ok` for each figure it built and `[skip]` for any figure whose input data is missing (for example Fig. 2 until the training-curve runs exist). A skip is not an error.

## 2. What the simulator models

A **discrete-event simulation** of several convoys routing from one depot to one of several target bases over a contested network.

* **Network**: layered random graph (`ammarl2/graph.py`, `make_graph(seed, layers, width, n_targets)`). Each edge has nominal cost `c_e`, threat level `rho_e`, flow capacity `q_e`. Half of the columns are "hot corridors" with high threat. This is a *synthetic benchmark topology*, not a real map.
* **Traversal time** `T_e = c_e (1 + 0.2 flow_e / q_e)` (congestion).
* **Hubs** have finite service capacity and a FIFO queue. The routing decision is taken at the **end of service**, so the age of a convoy's information keeps growing while it waits (information age is coupled to queueing).
* **Adversary** (`ammarl2/sim.py`): budgeted stochastic blocks (at most K at a time, random duration), three variants: `random` (edge chosen by threat level), `reactive` (targets recently used edges, with random exploration) and **spoofing** (injects false hazard messages about edges on the victim's own planned route).
* **Delayed reveal**: a block is observable only `tau_reveal` (5) time units after it starts. Entering a blocked edge is an *encounter*: the convoy is destroyed with probability `p_kill` (drawn in advance per convoy and hop), otherwise it crosses 2x slower.
* **Communication**: messages `(edge, blocked, t_obs, confidence)` have delay `tau_msg`, loss `p_loss`, and optionally a spoofed stream. Belief entries expire after `tau_stale`.
* **Gate** (`ammarl2/policies.py`): a message is admitted only if it is **F**resh (age below a limit; `static` = eta*tau_stale, or `scaled` = min(tau_stale, max(1, eta*(ETA_e + tau_msg)))), **R**elevant (the edge lies on the receiver's current planned route) and **C**onfident (kappa >= kappa_min). Each component can be switched on/off separately for ablations.
* **Metrics** per convoy: delivered or destroyed (survivability), nominal cost (sum of `c_e` on the path), realized time (includes queueing), integer count of blocked-edge entries, hub waiting time, plus the old-paper metrics (route survivability = mean `1 - rho_e` on the traversed edges; MaxThr = max `rho_e`) so old and new numbers can be compared.
* **Common random numbers**: the graph, convoy schedule, attack schedule, destruction draws and spoof stream are fixed by the episode seed, so two methods on the same seed see exactly the same world; only their decisions/information differ.

## 3. Methods compared

| Name | What it is |
|---|---|
| B1 | least-cost Dijkstra (ignores threat) |
| B2 | threat-weighted Dijkstra, weight `c(1 + 6 rho)` |
| B3 | least-cost with replanning on own observations |
| NC | threat-weighted routing, own observations only (no messages) |
| COMM-ALL | NC + admits every peer message (expires after `tau_stale`) |
| GATE / GATE-SC | NC + the three-condition gate (static / scaled freshness) |
| ORACLE | true state, zero delay (upper bound) |
| DQN, PPO, IPPO, MAPPO | learned graph-neural-network agents (2-layer GNN edge scorer + value head) with a **hard action mask** (only out-edges whose head can still reach the target). Each trained with `none`, `gate` or `all` communication, and an `_adv` variant trained against spoofing/reactive adversaries. PPO is trained on single-convoy episodes, IPPO shares parameters with local critics, MAPPO has a centralised critic. Reward: -(time between decisions), -40 on destruction. |

## 4. Experiments, scripts, outputs, figures

| Script | Question | Output | Used by |
|---|---|---|---|
| `table3.py` | final held-out comparison of all methods (graphs 300-309 x 5 episodes; learned agents x 3 seeds) | `out/table3_full.csv` | Fig. 3, Table III |
| `ablate.py` | which gate component matters (8 variants x 4 comm. conditions) | `out/ablate.csv` | Fig. 4 |
| `harsh2.py` (older: `harsh.py`) | loss / delay / spoofing sweep, incl. static-gate collapse | `out/harsh2.csv` | Fig. 5 |
| `casestudy.py` | find one convoy saved by an admitted peer report | `out/casestudy.json` | Fig. 6 |
| `sweep_gate.py` | confidence threshold, informative vs noisy score, freshness eta | `out/sweep_gate.csv` | Fig. 7 |
| `scaling.py` | 39 / 51 / 203 / 483 nodes (agents trained on 39 only) | `out/scaling.csv` | Fig. 8 |
| `reactive_heur.py`, `diversify.py` | reactive adversary and route randomisation | `out/reactive_heur.csv`, `out/diversify.csv` | Fig. 9 |
| `fir.py` | counterfactual influence of messages (common random numbers) | `out/fir.csv` | Fig. 10 |
| `run_train.py` | train + evaluate learned agents; robustness evaluation | `out/*.pt`, `out/eval_*.csv`, `out/rob_*.csv` | Fig. 3, 11 |
| `robust_existing.py`, `robust_eval.py` | robustness of already trained agents | `out/rob_*.csv` | Fig. 11 |
| `curves.py`, `run_curves.py` | training curves (18 runs: 3 seeds x DQN/IPPO/MAPPO x none/gate) | `out/curve_*.csv` | Fig. 2 |
| `dynamics.py` | time-resolved episode dynamics | `out/dynamics.csv` | Fig. 14 |
| `fig_trace.py` | per-convoy trace of one episode (NC vs gate) | (reads simulator directly) | Fig. 12 |
| `fig_snapshots.py` | live network snapshots at three times | (reads simulator directly) | Fig. 13 |
| `exp1.py`, `harm.py`, `heur_heldout.py`, `headroom.py`, `spoof.py`, `quick_learn.py` | earlier exploratory / diagnostic experiments (benchmark, "is sharing harmful", headroom, spoof effect) | `out/eval_heuristics.csv`, logs | text of the response letter |
| `final_tables.py`, `robust_tables.py` | markdown tables with paired bootstrap CIs | `out/final_tables.md` | manuscript tables |

Figure code: `figstyle.py` (palette, one colour per method in every figure, bootstrap helpers), `figs_a.py` (Figs. 1, 4-7), `figs_b.py` (Figs. 2, 3, 8-11, 14). Fig. 1 is a **model schematic drawn by hand** (it contains no results). Figs. 12 and 13 are drawn directly from running simulator objects. All other figures are computed from the CSVs above. Statistics: paired bootstrap 95% CIs over graph x episode (x seed).

## 5. Reproducing the experiments (optional)

    pytest tests_core.py                     # 5 invariants: realised cost >= shortest path, integer blocked counts,
                                             # hub capacity never exceeded, deterministic replay, oracle >= B1
    python table3.py                         # needs the trained agents (out/*.pt)
    python run_train.py dqn gate 300 0       # args: algo comm episodes seed [scenario=clean|adv]
    python run_curves.py                     # the 18 training-curve runs (slow; skips finished ones)

Run all commands from the project folder (paths such as `out/...` are relative). Scripts that load trained agents (`scaling.py`, `table3.py`, `robust_existing.py`) look for `out/<algo>_<comm>_s<seed>.pt` and, if missing, search nearby folders and print where they looked (`wfind.py`). Weights are shipped separately (`trained_weights.zip`) to keep the code package small.

**Reproducibility**: heuristic results are bit-exact across machines (fixed seeds, common random numbers). Learned-agent training is *not* bit-identical across machines/PyTorch versions; retraining gives slightly different numbers. Use the shipped weights and CSVs to reproduce the manuscript values exactly.

## 6. Main results (held-out graphs, 30 convoys, 8 simultaneous blocks)

| Method | Survivability | Realised time | Hub wait |
|---|---|---|---|
| B1 least-cost | 0.589 | 46.5 | 9.5 |
| B3 replan | 0.909 | 47.2 | 10.4 |
| NC (no messages) | 0.957 | 47.1 | 9.9 |
| share all | 0.981 | 46.8 | 9.5 |
| gate (scaled) | 0.972 | 46.8 | 9.5 |
| oracle | 0.989 | 46.8 | 9.4 |
| DQN / IPPO / MAPPO (no gate) | 0.895 / 0.901 / 0.901 | 36.7 / 37.4 / 37.1 | 1.0 / 1.7 / 1.4 |
| DQN / IPPO / MAPPO + gate | 0.905 / 0.913 / 0.913 | 36.7 / 36.9 / 37.4 | 1.1 / 1.2 / 1.7 |

Paired differences (95% CI): share-all vs no messages +2.4 [+0.5, +4.7] points; oracle vs share-all +0.8 [+0.1, +1.7]; scaled gate vs share-all -0.9 [-1.8, -0.1].

What the data supports, and what it does not:
* Peer hazard information helps modestly; most of the gap to the oracle is closed by simply sharing everything that has not expired.
* The three-condition gate is **not** a clear win for heuristic routers. The relevance filter and a static freshness limit cost survivability (a static limit can disable the gate entirely at delay >= 4); the confidence filter helps only if the confidence score is informative. It gives learned agents about one point in clean tests; the sign varies under hostile conditions.
* Against a traffic-reactive adversary no tested scheme, including the oracle, exceeds about 0.7; route randomisation helps.
* Learned agents trail the best heuristics in survival (0.90 vs 0.96-0.98) but cut realised time by about 22% and hub waiting by roughly 83-90%, because they observe queue information. At 203 / 483 nodes (trained on 39 nodes only) they reach 0.94-0.96, equal to the no-message heuristic.
* Earlier claims that "ungated communication is harmful" and that the gate is "necessary and sufficient" are **withdrawn** (not supported by the controlled experiments).

## 7. Known limitations / open items

* The topology is a synthetic layered graph. A geometric (map-like) generator would make the benchmark look more realistic but changes every number (all experiments and all training would have to be rerun).
* Learned agents are trained for 300 episodes only.
* The confidence score is simulated, not tied to a physical-layer authentication scheme.
* The scout-follower scenario (CC2) of the previous submission is not rebuilt; Fig. 5 replaces it.
* Fig. 2 (training curves) needs `python run_curves.py` (18 runs, hours on CPU).
* Fig. 10 (FIR) summarises 60 episode pairs per setting; Fig. 8 has 12 episodes per cell, so its intervals are wide.

## 8. File map

    ammarl2/graph.py      graph generator, Dijkstra
    ammarl2/sim.py        event-driven simulator (Sim, Cfg, Convoy); Sim.run(until=T) pauses for inspection
    ammarl2/policies.py   heuristic policies, gate, standard_methods()
    ammarl2/learn.py      GNN network, LearnedPolicy (dqn / ppo / ippo / mappo)
    ammarl2/train.py      training loop (clean and adversarial scenarios)
    ammarl2/run.py        run_episode helper, paired bootstrap
    tests_core.py         invariant tests
    out/                  raw results (csv/json/logs); *.pt trained agents are shipped separately
    figs/                 generated figures (png + pdf)
    make_figures.py       one command to rebuild all figures
