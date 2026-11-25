import pandas as pd

df = pd.read_csv("data/ecgrdvq_clinical.csv")

print("Rows:", len(df))
print("Subjects:", df["RANDID"].nunique())
print("Drugs:", df["EXTRT"].unique())
print("Time points:", sorted(df["TPT"].unique()))

dof = df[df["EXTRT"] == "Dofetilide"]
print(dof[["RANDID", "TPT", "PCSTRESN", "QT", "JTPEAK", "RR"]].head(10))

dof = dof.copy()
dof["QTcF"] = dof["QT"] / (dof["RR"] / 1000) ** (1/3)

mean_dof = dof.groupby("TPT")[["PCSTRESN", "QTcF", "JTPEAK"]].mean()
print(mean_dof.round(1))

pla = df[df["EXTRT"] == "Placebo"].copy()
pla["QTcF"] = pla["QT"] / (pla["RR"] / 1000) ** (1/3)
mean_pla = pla.groupby("TPT")[["QTcF", "JTPEAK"]].mean()

diff = mean_dof[["QTcF", "JTPEAK"]] - mean_pla
print("Dofetilide minus placebo:")
print(diff.round(1))