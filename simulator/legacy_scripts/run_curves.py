"""Train the 18 curve runs (3 seeds x DQN/IPPO/MAPPO x none/gate), skipping finished ones. Then run: python make_figures.py"""
import os, subprocess, sys
for s in (0, 1, 2):
    for a in ("dqn", "ippo", "mappo"):
        for c in ("none", "gate"):
            if os.path.exists(f"out/curve_{a}_{c}_s{s}.csv"): continue
            print("training", a, c, s, flush=True); subprocess.run([sys.executable, "curves.py", a, c, str(s), "300"], check=True)
