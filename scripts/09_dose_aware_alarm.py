import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

df = pd.read_csv("data/ecgrdvq_clinical.csv")
df = df[df["EXTRT"] == "Dofetilide"].copy()
df["QTcF"] = df["QT"] / (df["RR"] / 1000) ** (1/3)

d = df.groupby(["RANDID", "TPT"])[["QTcF", "PCSTRESN"]].mean().reset_index()
d["PCSTRESN"] = d["PCSTRESN"].fillna(0)

# true change (no noise) vs own baseline
base_true = d[d["TPT"] == -0.5].set_index("RANDID")["QTcF"]
d["delta_true"] = d["QTcF"] - d["RANDID"].map(base_true)

truth = d[d["TPT"] > 0].groupby("RANDID")["delta_true"].max() > 60
print("Real cases:", truth.sum(), "of", len(truth))

# noisy wearable readings
d["noisy"] = d["QTcF"] + rng.normal(0, 35, len(d))
base_noisy = d[d["TPT"] == -0.5].set_index("RANDID")["noisy"]
d["delta"] = d["noisy"] - d["RANDID"].map(base_noisy)
post = d[d["TPT"] > 0].copy()

# expected change per concentration, learned WITHOUT this person
expected = []
for _, row in post.iterrows():
    others = post[post["RANDID"] != row["RANDID"]]
    slope = (others["delta"] * others["PCSTRESN"]).sum() / (others["PCSTRESN"] ** 2).sum()
    expected.append(slope * row["PCSTRESN"])
post["expected"] = expected

# dose-aware estimate: half measurement, half expectation
post["estimate"] = 0.5 * post["delta"] + 0.5 * post["expected"]

def score(col):
    alarm = post.groupby("RANDID")[col].max() > 60
    sens = (alarm & truth).sum() / truth.sum()
    fa = (alarm & ~truth).sum() / (~truth).sum()
    return round(sens, 2), round(fa, 2)

print("Fixed rule      (sens, false alarm):", score("delta"))
print("Dose-aware rule (sens, false alarm):", score("estimate"))

# personal slope from the first 3 readings after dose (0.5, 1.0, 1.5 h)
early = post[post["TPT"] <= 1.5]
slope_pers = early.groupby("RANDID").apply(
    lambda g: (g["delta"] * g["PCSTRESN"]).sum() / (g["PCSTRESN"] ** 2).sum()
)

# predicted peak change = personal slope x own highest concentration
cmax = post.groupby("RANDID")["PCSTRESN"].max()
pred_peak = slope_pers * cmax

# alarm: prediction > 60 AND at least one measurement > 60
measured = post.groupby("RANDID")["delta"].max() > 60
alarm_pers = (pred_peak > 60) & measured

sens = (alarm_pers & truth).sum() / truth.sum()
fa = (alarm_pers & ~truth).sum() / (~truth).sum()
print("Personal rule   (sens, false alarm):", round(sens, 2), round(fa, 2))