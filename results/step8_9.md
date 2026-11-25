# Steps 8–9: QTc alarm, dofetilide (ECGRDVQ), noise SD 35 ms, seed 42

## Step 8: dofetilide vs placebo (per subject)
| Rule | Sensitivity | False alarms (placebo) |
|---|---|---|
| Fixed >60 ms, 1 reading | 91% | 41% |
| Fixed >60 ms, 2 in a row | 77% | 14% |

## Step 9: ground truth = true ΔQTcF >60 ms (17 of 22 real cases)
| Rule | Sensitivity | False alarms (5 non-cases) |
|---|---|---|
| Fixed >60 ms | 94% (16/17) | 60% (3/5) |
| Dose-aware, population slope | 94% (16/17) | 60% (3/5) |

Learned: a population expectation can't tell individuals apart -> needs a personal slope.
Caveat: one noise draw only, 5 non-cases -> large jumps.

## Step 10: beat averaging (fixed rule >60 ms)
| Averaged beats | Noise SD | Sensitivity | False alarms |
|---|---|---|---|
| 1 | 35 ms | 94% | 60% |
| 5 | 16 ms | 94% | 40% |
| 20 | 8 ms | 100% | 20% |
Learned: measurement quality (averaging) beats model complexity. Assumption: random noise only.

## Step 11: two-stage alarm (noise SD 8 ms, seed 42)
| Stage | Sensitivity | False alarms |
|---|---|---|
| Flag (1 reading >60) | 100% | 20% |
| Alarm (2 in a row >60) | 88% | 0% |
| Model gate (linear slope, peak >60) | 76% | 0% |
Learned: flag + alarm together miss nobody; linear model underestimates strong responders.
To test: flag AND model >55 ms (first check: 94% / 0%).

## Safety rule (fixed)
- Primary: sensitivity of Stage 1 (flag) must be ~100% of real cases; no case may get zero signals.
- Secondary: reduce false alarms only within that constraint.
- Bad signal or missing data -> "no reliable reading", never silence.

## Step 12: 200 repeats (kill test)
| Scenario | Flag sens / FA | Alarm sens / FA | Combo sens / FA | Runs flag missed ≥1 case |
|---|---|---|---|---|
| SD 35, no dropout | 90% / 78% | 69% / 47% | 61% / 39% | 84% |
| SD 8, no dropout | 96% / 32% | 78% / 8% | 76% / 10% | 55% |
| SD 8, 20% dropout | 92% / 30% | 68% / 7% | 74% / 11% | 77% |
Verdict: seed 42 was lucky. Safety rule FAILS. Linear dose model adds nothing (combo ≈ alarm).
Suspected causes: threshold = danger line (borderline cases), single noisy baseline, dropout.
Next: flag threshold 45–50 ms + 5-reading baseline, then retest dose model.

## Step 13: safety margin + early warning (SD 8 ms, 200 runs)
| Setup | Sens | False | Runs missing a case |
|---|---|---|---|
| Baseline 1, flag >60 | 96% | 30% | 52% |
| Baseline 1, flag >50 | 99% | 68% | 10% |
| Baseline 5, flag >60 | 98% | 25% | 31% |
| Baseline 5, flag >50 | 100% | 72% | 0% ✅ safety rule met |

Early warning at 1.5 h (peak 2.5 h), threshold 50:
| Method | Sens | False |
|---|---|---|
| Seen so far (threshold) | 41% | 1% |
| Personal forecast (curve-shape scaling) | 83% | 26% |
Finding: the dose-aware model's value is EARLY warning (~1 h lead), not better whole-day detection.
Caveats: single dose, healthy volunteers, random noise only, shape learned leave-one-out within same study.
Next: external test on ECGDMMLD (repeated dofetilide dosing).

## Step 14: QTDB caveat 1 (101 records, cardiologist reference)
QT T-end: 65% records bias >20 ms, drift 23 ms vs 16 ms random-expected (1.5x)
R-Tpeak: 38% records bias >20 ms, drift 19 ms vs 12 ms (1.5x)
-> Caveat 1 CONFIRMED: error partly systematic; averaging does not reach 8 ms.
-> Bias cancels via personal baseline (same device + lead). Drift does not.
-> Realistic averaged noise: 15-20 ms, not 8 ms. Rerun step 13 with this.

## Step 16: KILL TEST (pre-registered: <8 lives, 8-12 narrow, >12 kill)
Ella's run, 101 QTDB records: best method (median beat + gate + T peak) drift 20.3 ms, 95% CI 5.3-33.8
Verdict: KILL. Wearable home QTc alarm claim dropped.
Exploratory note (not a rescue): error driven by a few records with gross T-peak jumps (30-200 ms).