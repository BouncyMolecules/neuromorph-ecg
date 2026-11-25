# Neuromorphic ECG QTc Alarm Experiment

## Overview

This experiment evaluates whether ECG-based QTc measurements can reliably detect clinically meaningful QTcF prolongation after dofetilide exposure.

The central question is not merely whether a drug-effect model can fit the data. It asks whether a practical ECG alarm can:

1. detect real QTcF prolongation,
2. avoid excessive false alarms,
3. remain reliable across repeated noisy measurements, and
4. provide adequate measurement stability in real ECG recordings.

The original wearable/home-monitoring claim was treated as a safety hypothesis. It was killed when independent QT measurement testing showed too much drift.

## Data

The experiment uses three kinds of data:

- `data/ecgrdvq_clinical.csv`: a clinical ECG dataset for dofetilide and placebo exposure.
- `data/qtdb/`: PhysioNet QTDB records with cardiologist annotations.
- `data/mitdb/`: MIT-BIH Arrhythmia Database records for ECG/rhythm checks.

## Objective

Dofetilide can prolong the QT interval. The experiment tests whether changes in Fridericia-corrected QT (QTcF) can be converted into a dependable alarm for an individual subject.

The ground-truth drug effect is based on each subject's measured dofetilide minus placebo or personal-baseline change. A case is considered a true positive when the subject's true peak change in QTcF is greater than 60 ms.

## Safety Rule

The pre-registered safety priority is sensitivity:

- **Primary:** real cases must not be missed.
- **Secondary:** false alarms should be reduced only after sensitivity is protected.
- **Missing or unreliable data:** report “no reliable reading”; never silently suppress a possible alarm.

In the repeated-testing framework, the main safety requirement is that no real case is missed across a run.

## Experiment Steps

The numbered scripts form a progressive test of the alarm concept:

| Step | Script | Purpose |
|---|---|---|
| 1-4 | `01_load_record.py` through `04_episodes.py` | Load ECG data, calculate RR intervals, apply RR rules, and detect episodes |
| 5-6 | `05_check_rhythm.py`, `06_state_alarm.py` | Check rhythm and evaluate alarm state behavior |
| 7 | `07_load_ecgrdvq.py` | Load and inspect the dofetilide clinical dataset |
| 8-9 | `08_static_alarm.py`, `09_dose_aware_alarm.py` | Compare fixed and dose-aware alarm rules |
| 10 | `10_noise_averaging.py` | Measure the effect of averaging multiple beats |
| 11 | `11_two_stage_alarm.py` | Compare a sensitive flag, confirmed alarm, and model gate |
| 12 | `12_repeat_test.py` | Repeat tests across many noise seeds |
| 13 | `13_early_warning.py` | Test safety thresholds and early forecasting |
| 14 | `14_qtdb_check.py` | Compare automatic QT measurements with cardiologist references |
| 15 | `15_realistic_noise.py` | Incorporate realistic measurement noise |
| 16 | `16_kill_test.py` | Run the final pre-registered measurement kill test |

## Main Findings

### Fixed alarms

A fixed threshold of greater than 60 ms can identify many true cases, but measurement noise creates too many false alarms. Requiring two readings in a row reduces false alarms but also misses cases.

### Beat averaging

The `10_noise_averaging.py` simulation shows that measurement quality can matter more than alarm-model complexity:

| Averaged beats | Effective random noise | Sensitivity | False alarms |
|---:|---:|---:|---:|
| 1 | 35 ms | 94% | 60% |
| 5 | 16 ms | 94% | 40% |
| 20 | 8 ms | 100% | 20% |

This result assumes only independent random noise.

### Two-stage alarms

The two-stage approach separates:

- a sensitive **flag** that catches a possible event, and
- a stricter **alarm** that requires confirmation.

In the low-noise seed-42 run:

| Stage | Sensitivity | False alarms |
|---|---:|---:|
| Flag: 1 reading greater than 60 ms | 100% | 20% |
| Alarm: 2 readings in a row greater than 60 ms | 88% | 0% |
| Linear model gate | 76% | 0% |

A flag plus confirmation missed no case in that seed, while the linear model missed strong responders.

### Repeated noise testing

Running 200 repetitions showed that seed 42 was optimistic:

| Scenario | Flag sensitivity / false alarms | Alarm sensitivity / false alarms |
|---|---:|---:|
| 35 ms noise, no dropout | 90% / 78% | 69% / 47% |
| 8 ms noise, no dropout | 96% / 32% | 78% / 8% |
| 8 ms noise, 20% dropout | 92% / 30% | 68% / 7% |

The fixed safety rule therefore failed under repeated testing. A population dose model did not improve whole-day detection enough to justify it.

### Safety margin and early warning

In repeated low-noise tests, a 50 ms flag combined with a five-reading baseline met the safety rule:

| Baseline | Flag threshold | Sensitivity | False alarms | Runs missing a case |
|---:|---:|---:|---:|---:|
| 1 reading | 60 ms | 96% | 30% | 52% |
| 1 reading | 50 ms | 99% | 68% | 10% |
| 5 readings | 60 ms | 98% | 25% | 31% |
| 5 readings | 50 ms | 100% | 72% | 0% |

A personal dose/shape forecast could provide earlier warning at 1.5 hours, roughly one hour before the 2.5-hour peak:

| Method | Sensitivity | False alarms |
|---|---:|---:|
| Observed readings so far | 41% | 1% |
| Personal curve-shape forecast | 83% | 26% |

The model's potential value was early warning, not necessarily better whole-day alarm detection.

## QTDB Validation

Automatic QT measurements were compared with 101 QTDB records annotated by cardiologists.

Key results:

- QT T-end: 65% of records had bias greater than 20 ms.
- QT T-end drift was 23 ms versus 16 ms expected for random noise.
- R-to-T-peak: 38% of records had bias greater than 20 ms.
- R-to-T-peak drift was 19 ms versus 12 ms expected for random noise.

The comparison confirmed that measurement error is partly systematic. A personal baseline can cancel bias for the same device and lead, but drift remains.

This made 8 ms averaged random noise an unrealistic target: 15-20 ms is a more credible range for the realistic measurement scenario.

## Final Kill Test

The final test used the following pre-registered rule:

- Drift below 8 ms: live claim
- Drift of 8-12 ms: narrow, clinic-ECG-only claim
- Drift above 12 ms: kill the claim

Across 101 QTDB records, the best tested method—median beat, quality gate, and T peak—produced:

- Drift: **20.3 ms**
- 95% confidence interval: **5.3-33.8 ms**

### Verdict

**KILL.**

The wearable/home QTc alarm claim is not supported. The strong sensitivity findings in ideal and simulated settings were not enough to overcome real-measurement drift.

A few QTDB records contained gross T-peak jumps of approximately 30-200 ms. These outliers explain part of the poor stability but do not rescue the claim.

## Interpretation

The experiment found three distinct conclusions:

- Averaging helps random-noise reduction, but it does not remove systematic bias or drift.
- A personal five-reading baseline and a 50 ms safety flag can protect sensitivity in controlled simulations, but it produces many false alarms.
- Real QT measurement drift is too large for an unsupported wearable alarm claim.

The ECG measurement may still be useful in a supervised or clinic-based workflow, and missing measurements should remain explicit rather than being converted into an alarm guess.

## Reproducibility

Run the scripts from the repository root in step order. For example:

```powershell
python scripts\07_load_ecgrdvq.py
python scripts\14_qtdb_check.py
python scripts\16_kill_test.py
```

The numbered scripts are intended to be read as an evidence-building sequence. Results in `results/` should be interpreted as the output of that sequence, including failed alarm designs and the final kill decision.

## Caveats

- The clinical PK/PD signal is based on single-dose dofetilide data in healthy volunteers.
- The early-warning model uses a curve shape learned with leave-one-out validation within the same study.
- Final real-world generalization was not established.
- QTDB is a retrospective measurement-validation source, not a dofetilide trial.
- Some records may lack enough reliable readings for comparison.
