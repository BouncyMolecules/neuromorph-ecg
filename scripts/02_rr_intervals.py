import wfdb
import numpy as np

ann = wfdb.rdann("data/mitdb/100", "atr")

beat_symbols = ["N", "L", "R", "A", "V", "F", "j", "e", "a", "J", "E", "/", "f", "Q"]
is_beat = np.isin(ann.symbol, beat_symbols)
beats = ann.sample[is_beat]

rr = np.diff(beats) / 360

print("Number of beats:", len(beats))
print("Mean RR (s):", round(rr.mean(), 3))
print("Mean heart rate (bpm):", round(60 / rr.mean(), 1))
print("Shortest RR (s):", round(rr.min(), 3))
print("Longest RR (s):", round(rr.max(), 3))