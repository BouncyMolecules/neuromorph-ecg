# Step 16 KILL TEST: can better measurement push drift below 8 ms?
# Pre-registered rule: best drift < 8 ms -> lives | 8-12 ms -> narrow (clinic ECG only) | > 12 ms -> kill
from pathlib import Path
import numpy as np, pandas as pd, wfdb, neurokit2 as nk
from scipy.signal import butter, filtfilt

DATA = Path("data/qtdb")   # downloaded in step 14
records = (DATA / "RECORDS").read_text().split()

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
        return np.nan, np.nan
    return (t_end - q) / fs * 1000, (tp - r) / fs * 1000

def median_beat(x, peaks, fs, gate):
    pre, post = int(0.25 * fs), int(0.60 * fs)
    seg = np.array([x[p-pre:p+post] for p in peaks if p - pre >= 0 and p + post < len(x)])
    if len(seg) < 3:
        return None, 0
    if gate:   # quality gate: drop beats that don't look like the typical beat
        tmpl = np.median(seg, axis=0)
        corr = np.array([np.corrcoef(s, tmpl)[0, 1] for s in seg])
        seg = seg[corr > 0.95]
        if len(seg) < 3:
            return None, 0
    return np.median(seg, axis=0), pre

rows = []
for rec in records:
    try:
        ann = wfdb.rdann(str(DATA / rec), "q1c")
        sig, info = wfdb.rdsamp(str(DATA / rec), channels=[0])
    except Exception:
        continue
    fs = info["fs"]
    beats = manual_beats(ann)
    if len(beats) < 10:
        continue
    b, a = butter(2, [0.5, 40], btype="band", fs=fs)
    x = filtfilt(b, a, sig[:, 0])
    _, r = nk.ecg_peaks(x, sampling_rate=fs)
    rp = np.array(r["ECG_R_Peaks"])
    rr = np.median(np.diff(rp))
    half = len(beats) // 2
    for h, part in enumerate([beats[:half], beats[half:]]):
        man_qt = np.median([(t - q) / fs * 1000 for n, q, tp, t in part])
        man_rt = np.median([(tp - n) / fs * 1000 for n, q, tp, t in part])
        peaks = [rp[np.argmin(abs(rp - n))] for n, q, tp, t in part]
        # A) measure every beat, then average (= step 14)
        m = np.array([measure(x, p, rr, fs) for p in peaks if p + int(0.6*fs) < len(x)])
        row = dict(record=rec, half=h,
                   A_beats_Tend=np.nanmean(m[:, 0]) - man_qt)
        # B-D) median beat first, then measure once
        for gate in [False, True]:
            tmpl, r0 = median_beat(x, peaks, fs, gate)
            qt, rt = measure(tmpl, r0, rr, fs) if tmpl is not None else (np.nan, np.nan)
            tag = "gate" if gate else "nogate"
            row[f"median_{tag}_Tend"] = qt - man_qt
            row[f"median_{tag}_Tpeak"] = rt - man_rt
        rows.append(row)

df = pd.DataFrame(rows)
methods = [c for c in df.columns if c not in ("record", "half")]

def drift(c, recs=None):
    w = df.pivot(index="record", columns="half", values=c)
    if recs is not None:
        w = w.loc[recs]
    d = (w[1] - w[0]).dropna()
    return d, d.std() / np.sqrt(2)      # SD of one reading's error vs own bias

print(f"Records: {df.record.nunique()} | each record split into 2 halves\n")
print("1) All records")
print(f"{'method':22s} {'no reading':>10s} {'drift/reading':>14s}")
for c in methods:
    miss = df.pivot(index="record", columns="half", values=c).isna().any(axis=1).mean()
    print(f"{c:22s} {miss:10.0%} {drift(c)[1]:11.1f} ms")

# Fair comparison: only records where the quality gate gave a reading
passed = df.pivot(index="record", columns="half", values="median_gate_Tpeak").dropna().index
print(f"\n2) Same {len(passed)} records that passed the quality gate (fair comparison)")
for c in methods:
    print(f"{c:22s} {drift(c, passed)[1]:11.1f} ms")

# Uncertainty of the best method
d, best = drift("median_gate_Tpeak")
rng = np.random.default_rng(0)
boot = [rng.choice(d.values, len(d)).std(ddof=1) / np.sqrt(2) for _ in range(5000)]
lo, hi = np.percentile(boot, [2.5, 97.5])
print(f"\nBest (median beat + gate + T peak): {best:.1f} ms, 95% CI {lo:.1f}-{hi:.1f} ms")
verdict = "LIVES" if hi < 8 else "BORDERLINE (CI crosses 8)" if best < 8 else \
          "NARROW (clinic ECG only)" if best <= 12 else "KILL"
print("Verdict:", verdict)