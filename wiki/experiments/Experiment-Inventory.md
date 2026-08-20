---
title: Experiment Inventory
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Experiment Inventory

## Active entry points

<!-- trace: C-EXP-001 C-EXP-002 C-DATA-002 E-EXP-001 E-DATA-001 -->

| Entry point | Declared design | Mutable output | Current status |
|---|---|---|---|
| `experiments/07_confirmatory_benchmark.py` | Canonical KAIROS, GRU, and MLP on the frozen benchmark-v1 configuration | Reference runner output is `runs/benchmark-v1/`; new wrapper outputs use `runs/reproductions/benchmark-v1/<run-id>/` | Reference execution complete and validated; future reproductions remain new, unadmitted evidence |

The runner imports canonical KAIROS, verifies the tracked raw-data checksum,
applies the same five seeds to every model, estimates the pseudo-label threshold
from training data only, purges target horizons at temporal boundaries, and
records each declared attempt. [Trace: `C-EXP-001`, `C-EXP-002`, `C-DATA-002`
→ `E-EXP-001`, `E-DATA-001`]

## Superseded design conflicts

<!-- trace: C-EXP-002 C-IMPL-002 E-EXP-001 E-IMPL-001 -->

- The archived comparison used unequal seed registries and a local
  three-feature KAIROS copy.
- The archived scale runner downloaded mutable data and embedded its protocol
  in Python.
- Archived runners are historical inputs and cannot write current evidence.

## Reproduction and admission

The design gates are encoded in `protocols/benchmark-v1.md` and
`configs/benchmark-v1.json`. The frozen release completed and passed those
technical gates. A new reproduction must enter through the locked wrapper and
portable scheduler definition, retain a unique run ID, and independently pass
complete-execution, artifact-finalization, uncertainty, and scoped-wording
review before admission. [Trace: `C-EXP-002`, `C-PERF-001` → `E-EXP-001`,
`E-BENCH-001`]
