import wfdb
import numpy as np

ann = wfdb.rdann("data/mitdb/232", "atr")

for sample, sym, note in zip(ann.sample, ann.symbol, ann.aux_note):
    if note:
        print(f"{sample / 360:8.1f}s  {sym}  {note}")