import numpy as np
import pandas as pd

df = pd.read_csv("data/ecgrdvq_clinical.csv")
df = df[df["EXTRT"] == "Dofetilide"].copy()
df["QTcF"] = df["QT"] / (df["RR"] / 1000) ** (1/3)
d = df.groupby(["RANDID", "TPT"])[["QTcF", "PCSTRESN"]].mean().reset_index()
d["PCSTRESN"] = d["PCSTRESN"].fillna(0)

base_true = d[d["TPT"] == -0.5].set_index("RANDID")["QTcF"]
d["delta_true"] = d["QTcF"] - d["RANDID"].map(base_true)
truth = d[d["TPT"] > 0].groupby("RANDID")["delta_true"].max() > 60

# 20 averaged beats -> noise SD about 8 ms
sd = 35 / np.sqrt(20)
rng = np.random.default_rng(42)
d["noisy"] = d["QTcF"] + rng.normal(0, sd, len(d))
base_noisy = d[d["TPT"] == -0.5].set_index("RANDID")["noisy"]
d["delta"] = d["noisy"] - d["RANDID"].map(base_noisy)
post = d[d["TPT"] > 0].sort_values(["RANDID", "TPT"]).copy()

# Stage 1: flag = one reading above 60 -> "please do a check ECG"
post["above"] = post["delta"] > 60
flag = post.groupby("RANDID")["above"].any()

# Stage 2: alarm = two readings in a row above 60 -> "call the clinic"
post["two"] = post["above"] & post.groupby("RANDID")["above"].shift(1, fill_value=False)
alarm = post.groupby("RANDID")["two"].any()

# Model gate: linear concentration-QTc slope per person, predicted peak > 60
def slope(g):
    return (g["delta"] * g["PCSTRESN"]).sum() / (g["PCSTRESN"] ** 2).sum()
pred_peak = post.groupby("RANDID").apply(slope) * post.groupby("RANDID")["PCSTRESN"].max()
model = pred_peak > 60

def score(a):
    sens = (a & truth).sum() / truth.sum()
    fa = (a & ~truth).sum() / (~truth).sum()
    return round(sens, 2), round(fa, 2)

print("Stage 1 flag      (sens, false):", score(flag))
print("Stage 2 alarm     (sens, false):", score(alarm))
print("Model gate        (sens, false):", score(model))