# System Design Document — NavigationTask (v1)

## 1. Specification Summary
- Scheduler: RMS
- Mutexes: 1
- Tasks:
  - T_High — T=30 ms, C=8 ms, D=30 ms, priority 1
  - T_Medium — T=100 ms, C=30 ms, D=100 ms, priority 2
  - T_Low — T=150 ms, C=20 ms, D=150 ms, priority 3

## 2. Priority Validation
- RMS rule satisfied out-of-the-box (shorter periods already mapped to higher priorities).

## 3. Schedulability Analysis
- Utilization: 0.2667 + 0.30 + 0.1333 = **0.70**
- Liu–Layland bound (n=3): **0.7798** → PASS
- Response-Time Results:
  - T_High: R = 8 ms ≤ 30 ms
  - T_Medium: R = 46 ms ≤ 100 ms
  - T_Low: R = 74 ms ≤ 150 ms

## 4. TCTL Properties
See `stage4_tctl_properties.json` (P1–P9) capturing safety, deadlines, liveness, and mutual exclusion.

## 5. UPPAAL Model
- File: `uppaal_model.xml`
- Three templates (one per task) with clock invariants, deterministic transitions, sanitized identifiers, and instantiations `T_*_inst`.

## 6. Verification Results
- Simulated verifyta: PASS for all properties.
- Awaiting execution by physical verifyta binary (see Stage 6 notes).

## 7. Repairs
- None required; pipeline converged immediately.

## 8. Verified Haskell Code
- File: `VerifiedScheduler.hs`
- Pure schedule predicate + utilization guard ensures second-layer safety.

## 9. Traceability Matrix
| Stage | Artifact |
|-------|----------|
| 1 | `spec.json`, `stage1_input_validation.json` |
| 2 | `stage2_priority_validation.json` |
| 3 | `stage3_schedulability.json` |
| 4 | `stage4_tctl_properties.json` |
| 5 | `uppaal_model.xml` |
| 6 | `stage6_verifyta_results.json` |
| 8 | `VerifiedScheduler.hs` |
| 9 | `SDD.md` |
