# Step 15: does the safety rule survive realistic measurement noise (from step 14)?
import numpy as np
import pandas as pd

df = pd.read_csv("data/ecgrdvq_clinical.csv")
df = df[df["EXTRT"] == "Dofetilide"].copy()
df["QTcF"] = df["QT"] / (df["RR"] / 1000) ** (1/3)
d = df.groupby(["RANDID", "TPT"])["QTcF"].mean().reset_index()
base_true = d[d["TPT"] == -0.5].set_index("RANDID")["QTcF"]
d["delta_true"] = d["QTcF"] - d["RANDID"].map(base_true)
true_delta = d[d["TPT"] > 0].pivot(index="RANDID", columns="TPT", values="delta_true").values
truth = true_delta.max(axis=1) > 60

def run_once(rng, sd, threshold, persist, n_base=5):
    noise = rng.normal(0, sd, true_delta.shape)
    base_noise = rng.normal(0, sd / np.sqrt(n_base), len(truth))
    delta = true_delta + noise - base_noise[:, None]
    if persist:   # two readings in a row above threshold
        above = delta > threshold
        flag = (above[:, 1:] & above[:, :-1]).any(axis=1)
    else:
        flag = delta.max(axis=1) > threshold
    sens = (flag & truth).sum() / truth.sum()
    false = (flag & ~truth).sum() / (~truth).sum()
    missed = (truth & ~flag).sum() > 0
    return sens, false, missed

rng = np.random.default_rng(1)
print(f"Real cases: {truth.sum()} of {len(truth)} | baseline 5 readings | 200 runs each\n")
print("noise  flag>  rule        sens   false  runs missing a case")
for sd in [8, 15, 20]:
    for threshold in [50, 40]:
        for persist in [False, True]:
            r = np.array([run_once(rng, sd, threshold, persist) for _ in range(200)], dtype=float)
            rule = "2 in a row" if persist else "any 1"
            print(f"{sd:4d}  {threshold:5d}  {rule:10s}  {r[:,0].mean():.2f}   "
                  f"{r[:,1].mean():.2f}   {r[:,2].mean():.0%}")