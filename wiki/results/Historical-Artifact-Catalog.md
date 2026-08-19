---
title: Historical Artifact Catalog
status: QUARANTINED
last_updated: 2026-08-19
paper_source: false
---

# Historical Artifact Catalog

<!-- trace: C-RESULT-001 E-LEGACY-ARTIFACTS-001 -->

The locally retained legacy bundle contains 12 JSON records and one TeX table.
Public Git carries their checksum inventory, not the artifact bytes. None is a
current result. [Trace: `C-RESULT-001` → `E-LEGACY-ARTIFACTS-001`]

## Bundle inventory

<!-- trace: C-RESULT-001 H-PERF-001 H-LEAD-001 H-XDOMAIN-001 H-CAUSAL-001 E-LEGACY-ARTIFACTS-001 -->

| Artifact | Recorded subject | Claim family |
|---|---|---|
| `critique5_intervention_aware.json` | Standard versus walk-forward TGN diagnostic | `H-PERF-001` |
| `fair_comparison.json` | KAIROS and baseline aggregate records | `H-PERF-001` |
| `multiseed_edition1.json` | Per-seed KAIROS/TGN records | `H-PERF-001` |
| `priority1_walkforward.json` | Walk-forward split and lead-time crossings | `H-LEAD-001` |
| `priority2_scp_ablation.json` | SCP ablation record | `H-PERF-001` |
| `real_epidemiology_results.json` | Historical COVID-domain run | `H-XDOMAIN-001` |
| `scale_results.json` | Historical scale variants | `H-PERF-001`, `H-MODEL-001` |
| `t2a_synthetic_results.json` | Synthetic state-recovery diagnostics | `H-PERF-001` |
| `t2c_epidemiology_results.json` | Synthetic/epidemiology transfer diagnostics | `H-XDOMAIN-001` |
| `table1b.json` | Natural/intervention subset table | `H-PERF-001`, `H-CAUSAL-001` |
| `table1b_predictions.json` | Per-observation prediction dump | `H-PERF-001` |
| `walkforward_cfi_series.json` | Historical CFI time series | `H-LEAD-001` |
| `table1b.tex` | Generated historical table | `H-PERF-001` |

## Use boundary

The bundle can support reconstruction and discrepancy analysis only. A value
inside a parseable JSON file is not admitted merely because its byte identity
is known. The required missing chain is source commit, exact environment,
frozen data identity, reviewed configuration/protocol, complete attempts,
aggregation, and claim review. [Trace: `C-RESULT-001` →
`E-LEGACY-ARTIFACTS-001`]
