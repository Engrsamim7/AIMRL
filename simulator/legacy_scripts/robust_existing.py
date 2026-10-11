import torch, pandas as pd, glob, os
from ammarl2.learn import LearnedPolicy
from ammarl2.policies import standard_methods
from robust_eval import robust_rows
rows = []
for f in sorted(glob.glob("out/*_s[0-2].pt")):
    b = os.path.basename(f)[:-3]; a, c, s = b.split("_")[0], b.split("_")[1], int(b[-1])
    if "adv" in b: continue
    p = LearnedPolicy(name=f"{a}-{c}", weights="threat", use_obs=True, comm=c, algo=a); p.net.load_state_dict(torch.load(__import__("wfind").wpath(__import__("os").path.basename(f))))
    rows += robust_rows(p, a, c, s); print(b, flush=True)
pd.DataFrame(rows).to_csv("out/rob_clean_trained.csv", index=False)
