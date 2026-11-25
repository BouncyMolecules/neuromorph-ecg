import wfdb
import numpy as np

ann = wfdb.rdann("data/mitdb/232", "atr")
beat_symbols = ["N", "L", "R", "A", "V", "F", "j", "e", "a", "J", "E", "/", "f", "Q"]
beats = ann.sample[np.isin(ann.symbol, beat_symbols)]
rr = np.diff(beats) / 360
pause_times = beats[np.where(rr > 2.0)[0]] / 360

quiet = 120
alarms = []
for t in pause_times:
    if alarms and t - alarms[-1][1] <= quiet:
        alarms[-1][1] = t
    else:
        alarms.append([t, t])

print("Alarms:", len(alarms))
for start, end in alarms:
    print(f"Alarm active {start:.1f}s to {end:.1f}s")