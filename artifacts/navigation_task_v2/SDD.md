# System Design Document — NavigationTaskExtended (v2)

## 1. Specification Summary
- Scheduler: RMS with 1 mutex resource (CPU)
- Tasks:
  - T_High — T=30 ms, C=8 ms, D=30 ms, priority 1
  - T_Medium — T=100 ms, C=30 ms, D=100 ms, priority 2
  - T_Low — T=150 ms, C=20 ms, D=150 ms, priority 3
  - T_Backup — T=400 ms, C=8 ms, D=400 ms, priority 4
  - T_Diagnostic — T=800 ms, C=10 ms, D=800 ms, priority 5

## 2. Priority Validation
- RMS ordering already respected; no corrections were required.

## 3. Schedulability Analysis
- Utilization contributions: 0.2667 + 0.30 + 0.1333 + 0.02 + 0.0125 = **0.7325**
- Liu–Layland bound for n=5: **0.7435** → PASS
- Response-Time results (worst-case R):
  - T_High: 8 ms
  - T_Medium: 46 ms
  - T_Low: 74 ms
  - T_Backup: 82 ms
  - T_Diagnostic: 100 ms
- All R_i ≤ corresponding deadlines.

## 4. TCTL Properties
- See `stage4_tctl_properties.json` (P1–P14) covering safety, per-task deadlines, liveness, and CPU mutual exclusion.

## 5. UPPAAL Model
- File: `uppaal_model.xml`
- Five templates with shared `cpu_owner` guard enforcing mutual exclusion.
- System instantiates all tasks (`T_*_inst`).

## 6. Verification Results
- `verifyta` (Windows 5.0.0) satisfied all 14 queries; log captured in `verifyta_stdout.txt`.

## 7. Repairs
- Not required for v2 (mutual exclusion already enforced from v1 fix).

## 8. Verified Haskell Code
- File: `VerifiedScheduler.hs`
- Extends task set with backup and diagnostic tasks; `allTasksSafe` ensures timing guard holds.

## 9. Traceability Matrix
| Stage | Artifact |
|-------|----------|
| 1 | `spec.json`, `stage1_input_validation.json` |
| 2 | `stage2_priority_validation.json` |
| 3 | `stage3_schedulability.json` |
| 4 | `stage4_tctl_properties.json` |
| 5 | `uppaal_model.xml` |
| 6 | `stage6_verifyta_results.json`, `verifyta_stdout.txt` |
| 7 | `stage7_failure_analysis.json` |
| 8 | `VerifiedScheduler.hs` |
| 9 | `SDD.md` |
