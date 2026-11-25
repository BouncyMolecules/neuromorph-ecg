import numpy as np
import pandas as pd

df = pd.read_csv("data/ecgrdvq_clinical.csv")
df = df[df["EXTRT"] == "Dofetilide"].copy()
df["QTcF"] = df["QT"] / (df["RR"] / 1000) ** (1/3)
d = df.groupby(["RANDID", "TPT"])[["QTcF", "PCSTRESN"]].mean().reset_index()
d["PCSTRESN"] = d["PCSTRESN"].fillna(0)

# ground truth: true change > 60 ms
base_true = d[d["TPT"] == -0.5].set_index("RANDID")["QTcF"]
d["delta_true"] = d["QTcF"] - d["RANDID"].map(base_true)
truth = d[d["TPT"] > 0].groupby("RANDID")["delta_true"].max() > 60

for n_beats in [1, 5, 20]:
    sd = 35 / np.sqrt(n_beats)
    rng = np.random.default_rng(42)
    d["noisy"] = d["QTcF"] + rng.normal(0, sd, len(d))
    base_noisy = d[d["TPT"] == -0.5].set_index("RANDID")["noisy"]
    d["delta"] = d["noisy"] - d["RANDID"].map(base_noisy)
    post = d[d["TPT"] > 0]

    alarm = post.groupby("RANDID")["delta"].max() > 60
    sens = (alarm & truth).sum() / truth.sum()
    fa = (alarm & ~truth).sum() / (~truth).sum()
    print(f"n={n_beats:2d}  noise SD={sd:4.1f} ms  sens={sens:.2f}  false alarm={fa:.2f}")