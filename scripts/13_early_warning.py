import numpy as np
import pandas as pd

df = pd.read_csv("data/ecgrdvq_clinical.csv")
df = df[df["EXTRT"] == "Dofetilide"].copy()
df["QTcF"] = df["QT"] / (df["RR"] / 1000) ** (1/3)
d = df.groupby(["RANDID", "TPT"])["QTcF"].mean().reset_index()

base_true = d[d["TPT"] == -0.5].set_index("RANDID")["QTcF"]
d["delta_true"] = d["QTcF"] - d["RANDID"].map(base_true)

# table: one row per person, one column per time point after dose
table = d[d["TPT"] > 0].pivot(index="RANDID", columns="TPT", values="delta_true")
true_delta = table.values
times = np.array(table.columns)
truth = true_delta.max(axis=1) > 60

def score(alarm):
    sens = (alarm & truth).sum() / truth.sum()
    fa = (alarm & ~truth).sum() / (~truth).sum()
    missed = (truth & ~alarm).sum() > 0
    return sens, fa, missed

def run_once(rng, threshold, n_base, upto):
    sd = 8
    noise = rng.normal(0, sd, true_delta.shape)
    base_noise = rng.normal(0, sd / np.sqrt(n_base), len(truth))
    delta = true_delta + noise - base_noise[:, None]

    # A) safety-margin flag over the whole day
    flag = delta.max(axis=1) > threshold

    # B) early forecast: only readings up to 'upto' hours
    early = times <= upto
    seen = delta[:, early].max(axis=1) > threshold
    forecast = np.zeros(len(truth))
    for i in range(len(truth)):
        others = np.delete(np.arange(len(truth)), i)
        shape = delta[others].mean(axis=0)          # typical curve, learned without person i
        scale = (delta[i, early] * shape[early]).sum() / (shape[early] ** 2).sum()
        forecast[i] = scale * shape.max()           # predicted personal peak
    return score(flag) + score(seen) + score(forecast > threshold)

rng = np.random.default_rng(1)

print("A) Whole-day flag, 200 runs")
for n_base in [1, 5]:
    for threshold in [60, 50]:
        r = np.array([run_once(rng, threshold, n_base, 24)[:3] for _ in range(200)], dtype=float)
        print(f"  baseline {n_base} reading(s), flag >{threshold}: sens {r[:,0].mean():.2f}  "
              f"false {r[:,1].mean():.2f}  runs missing a case {r[:,2].mean():.0%}")

print("\nB) Early warning at 1.5 h (peak is at 2.5 h), threshold 50, baseline 5")
r = np.array([run_once(rng, 50, 5, 1.5)[3:] for _ in range(200)], dtype=float)
print(f"  seen so far:      sens {r[:,0].mean():.2f}  false {r[:,1].mean():.2f}")
print(f"  personal forecast: sens {r[:,3].mean():.2f}  false {r[:,4].mean():.2f}")