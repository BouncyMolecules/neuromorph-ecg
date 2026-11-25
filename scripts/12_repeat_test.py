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

def run_once(rng, sd, dropout):
    x = d.copy()
    x["noisy"] = x["QTcF"] + rng.normal(0, sd, len(x))
    base = x[x["TPT"] == -0.5].set_index("RANDID")["noisy"]
    x["delta"] = x["noisy"] - x["RANDID"].map(base)
    post = x[x["TPT"] > 0]
    post = post[rng.random(len(post)) > dropout].sort_values(["RANDID", "TPT"]).copy()

    post["above"] = post["delta"] > 60
    flag = post.groupby("RANDID")["above"].any().reindex(truth.index, fill_value=False)
    post["two"] = post["above"] & post.groupby("RANDID")["above"].shift(1, fill_value=False)
    alarm = post.groupby("RANDID")["two"].any().reindex(truth.index, fill_value=False)

    post["dc"] = post["delta"] * post["PCSTRESN"]
    post["cc"] = post["PCSTRESN"] ** 2
    g = post.groupby("RANDID")
    pred_peak = (g["dc"].sum() / g["cc"].sum() * g["PCSTRESN"].max()).reindex(truth.index, fill_value=0)
    combo = flag & (pred_peak > 55)

    out = {}
    for name, a in [("flag", flag), ("alarm", alarm), ("combo", combo)]:
        out[name + "_sens"] = (a & truth).sum() / truth.sum()
        out[name + "_fa"] = (a & ~truth).sum() / (~truth).sum()
    out["missed_by_flag"] = (truth & ~flag).sum()
    return out

rng = np.random.default_rng(1)
for sd, dropout in [(35, 0.0), (8, 0.0), (8, 0.2)]:
    res = pd.DataFrame([run_once(rng, sd, dropout) for _ in range(200)])
    print(f"\nnoise SD={sd} ms, dropout={dropout:.0%}")
    for name in ["flag", "alarm", "combo"]:
        s, f = res[name + "_sens"], res[name + "_fa"]
        print(f"  {name:5s}  sens {s.mean():.2f} (5-95%: {s.quantile(.05):.2f}-{s.quantile(.95):.2f})"
              f"  false {f.mean():.2f} ({f.quantile(.05):.2f}-{f.quantile(.95):.2f})")
    print(f"  runs where flag missed >=1 real case: {(res['missed_by_flag'] > 0).mean():.0%}")