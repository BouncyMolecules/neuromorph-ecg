import wfdb
import numpy as np

ann = wfdb.rdann("data/mitdb/232", "atr")
beat_symbols = ["N", "L", "R", "A", "V", "F", "j", "e", "a", "J", "E", "/", "f", "Q"]
beats = ann.sample[np.isin(ann.symbol, beat_symbols)]
rr = np.diff(beats) / 360

pause_idx = np.where(rr > 2.0)[0]
pause_times = beats[pause_idx] / 360

episodes = []
for t in pause_times:
    if episodes and t - episodes[-1][1] <= 10:
        episodes[-1][1] = t
    else:
        episodes.append([t, t])

hours = (beats[-1] - beats[0]) / 360 / 3600
print("Pause beats:", len(pause_times))
print("Episodes:", len(episodes))
print("Recording length (h):", round(hours, 2))
print("Episodes per hour:", round(len(episodes) / hours, 1))
for start, end in episodes[:5]:
    print(f"Episode {start:.1f}s to {end:.1f}s")