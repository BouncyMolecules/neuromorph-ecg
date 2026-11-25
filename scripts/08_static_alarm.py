import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

df = pd.read_csv("data/ecgrdvq_clinical.csv")
df = df[df["EXTRT"].isin(["Dofetilide", "Placebo"])].copy()
df["QTcF"] = df["QT"] / (df["RR"] / 1000) ** (1/3)

# one value per subject, drug, time point (average the triplicate)
d = df.groupby(["RANDID", "EXTRT", "TPT"])["QTcF"].mean().reset_index()

# wearable noise: SD 35 ms
d["QTcF_noisy"] = d["QTcF"] + rng.normal(0, 35, len(d))

# baseline = time point -0.5 for each subject and drug
base = d[d["TPT"] == -0.5].set_index(["RANDID", "EXTRT"])["QTcF_noisy"]
d["delta"] = d["QTcF_noisy"] - d.set_index(["RANDID", "EXTRT"]).index.map(base)

# fixed rule: alarm if delta > 60 ms
d["alarm"] = (d["TPT"] > 0) & (d["delta"] > 60)

per_subject = d.groupby(["EXTRT", "RANDID"])["alarm"].any()
print(per_subject.groupby("EXTRT").mean().round(2))

d = d.sort_values(["RANDID", "EXTRT", "TPT"])
d["alarm2"] = d["alarm"] & d.groupby(["RANDID", "EXTRT"])["alarm"].shift(1, fill_value=False)

per_subject2 = d.groupby(["EXTRT", "RANDID"])["alarm2"].any()
print("2 in a row:")
print(per_subject2.groupby("EXTRT").mean().round(2))