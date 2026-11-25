# Pre-registration: PK/PD forecast (written 23 Nov 2026, before running)

Question: Does a PK/PD model forecast the evening QTcF peak (12–13.5 h) on ECGDMMLD
from readings up to 8 h better than carrying the last value forward?

Success (all must hold, 200 noise runs, SD 8 ms, 5-reading baseline):
- Mean absolute error <= 10 ms (carry-forward: 14.6 ms)
- At threshold 40 ms: sensitivity >= 80% AND false alarms <= 20%
Kill: MAE > 12 ms OR sensitivity < 60% -> drop the forecast claim, keep safety flag only.

Caveat gate first: QT measurement on QTDB must show systematic error < 20 ms.