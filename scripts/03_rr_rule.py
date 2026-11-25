import wfdb
import numpy as np

wfdb.dl_database("mitdb", dl_dir="data/mitdb", records=["232"])

ann = wfdb.rdann("data/mitdb/232", "atr")
beat_symbols = ["N", "L", "R", "A", "V", "F", "j", "e", "a", "J", "E", "/", "f", "Q"]
beats = ann.sample[np.isin(ann.symbol, beat_symbols)]
rr = np.diff(beats) / 360

fast = rr < 0.4
pause = rr > 2.0

print("Fast alarms:", fast.sum())
print("Pause alarms:", pause.sum())
print("Longest RR (s):", round(rr.max(), 2))