# Caveat 1: does QT measurement error average out, or is it systematic?
# Compares my automatic QT with cardiologist annotations in PhysioNet QTDB.
import urllib.request
from pathlib import Path
import numpy as np, pandas as pd, wfdb, neurokit2 as nk
from scipy.signal import butter, filtfilt

URL = "https://physionet.org/files/qtdb/1.0.0/"
DATA = Path("data/qtdb")
DATA.mkdir(parents=True, exist_ok=True)

# 1. Download (skips files you already have)
if not (DATA / "RECORDS").exists():
    urllib.request.urlretrieve(URL + "RECORDS", DATA / "RECORDS")
records = (DATA / "RECORDS").read_text().split()
for rec in records:
    for ext in ["hea", "dat", "q1c"]:
        f = DATA / f"{rec}.{ext}"
        if not f.exists():
            try:
                urllib.request.urlretrieve(URL + f.name, f)
            except Exception:
                pass
print("Records downloaded:", len(records))

# 2. Cardiologist beats: (R peak, QRS onset, T peak, T end)
def manual_beats(ann):
    s, sym = ann.sample, ann.symbol
    beats = []
    for i, x in enumerate(sym):
        if x != "N" or i == 0 or sym[i-1] != "(":
            continue
        for j in range(i+1, min(i+8, len(sym)-1)):
            if sym[j] == "N":
                break
            if sym[j] == "t" and sym[j+1] == ")":
                beats.append((s[i], s[i-1], s[j], s[j+1]))
                break
    return beats

# 3. My measurement: QRS onset, T peak, T end (tangent method)
def measure(x, r, rr, fs):
    ms = lambda v: int(v * fs / 1000)
    d = np.gradient(x)
    thr = 0.1 * np.abs(d[r-ms(60):r]).max()
    q = r - ms(20)
    while q > r - ms(120) and abs(d[q]) > thr:
        q -= 1
    base = x[q]
    lo, hi = r + ms(150), r + min(ms(550), int(0.6 * rr))
    tp = lo + np.argmax(np.abs(x[lo:hi] - base))
    w = d[tp:tp+ms(150)]
    k = tp + (np.argmin(w) if x[tp] > base else np.argmax(w))
    t_end = k - (x[k] - base) / d[k]
    if not (k <= t_end <= k + ms(120)):
        return np.nan, np.nan          # no reliable reading, never a guess
    return (t_end - q) / fs * 1000, (tp - r) / fs * 1000

rows = []
for rec in records:
    try:
        ann = wfdb.rdann(str(DATA / rec), "q1c")
        sig, info = wfdb.rdsamp(str(DATA / rec), channels=[0])
    except Exception:
        continue
    fs = info["fs"]
    beats = manual_beats(ann)
    if len(beats) < 5:
        continue
    b, a = butter(2, [0.5, 40], btype="band", fs=fs)
    x = filtfilt(b, a, sig[:, 0])
    _, r = nk.ecg_peaks(x, sampling_rate=fs)
    rp = np.array(r["ECG_R_Peaks"])
    for n, q, tpk, t in beats:
        k = np.argmin(abs(rp - n))
        if abs(rp[k] - n) > 0.1 * fs or k + 1 >= len(rp):
            continue
        qt, rt = measure(x, rp[k], rp[k+1] - rp[k], fs)
        rows.append(dict(record=rec, beat=n,
                         qt_err=qt - (t - q) / fs * 1000,
                         rt_err=rt - (tpk - n) / fs * 1000))

df = pd.DataFrame(rows)
print(f"No reliable reading: {df.qt_err.isna().mean():.0%} of beats")
df = df.dropna()
print(f"Beats compared: {len(df)} | records: {df.record.nunique()}")

# 4. Report: overall error, error vs own baseline, does it average out?
def halves(g, col):
    g = g.sort_values("beat"); h = len(g) // 2
    return g[col].iloc[h:].mean() - g[col].iloc[:h].mean()

n_half = df.groupby("record").size().median() / 2
for col, name in [("qt_err", "QT (to T END)"), ("rt_err", "R to T PEAK")]:
    per = df.groupby("record")[col].median()
    own = df[col] - df.groupby("record")[col].transform("median")
    drift = df.groupby("record").apply(lambda g: halves(g, col))
    print(f"\n{name}")
    print(f"  Records with bias > 20 ms:      {(per.abs() > 20).mean():.0%}")
    print(f"  Error vs own bias, SD:          {own.std():.1f} ms")
    print(f"  Drift between halves, SD:       {drift.std():.1f} ms")
    print(f"  If pure random noise, expected: {np.sqrt(2) * own.std() / np.sqrt(n_half):.1f} ms")