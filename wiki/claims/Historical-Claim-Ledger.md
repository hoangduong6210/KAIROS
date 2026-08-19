---
title: Historical Claim Ledger
status: QUARANTINED
last_updated: 2026-08-19
paper_source: false
---

# Historical Claim Ledger

<!-- trace: H-PERF-001 H-LEAD-001 H-XDOMAIN-001 H-MODEL-001 H-CAUSAL-001 E-PAPER-001 E-LEGACY-ARTIFACTS-001 -->

| Claim ID | Observed historical wording or value | Direct source | Evidence | Reason quarantined |
|---|---|---|---|---|
| `H-PERF-001` | The final conference abstract reports 72.3% balanced accuracy and describes comparative advantages; legacy JSON files report additional, non-identical aggregates. | `KAIROS_FINAL.pdf`, page 1; legacy result bundle | `E-PAPER-001`, `E-LEGACY-ARTIFACTS-001` | Conflicting model identities, feature sets, seed counts, and aggregates; no frozen release closure. |
| `H-LEAD-001` | The final conference abstract reports 25 days; `priority1_walkforward.json` records 52 days and separately records the paper value as 25 days. | `KAIROS_FINAL.pdf`, page 1; `priority1_walkforward.json` | `E-PAPER-001`, `E-LEGACY-ARTIFACTS-001` | Split, crossing rule, threshold, smoothing, and single-seed identities are not reconciled. |
| `H-XDOMAIN-001` | The final conference abstract reports a 21-point epidemiology improvement with zero architecture changes. | `KAIROS_FINAL.pdf`, page 1; epidemiology JSON artifacts | `E-PAPER-001`, `E-LEGACY-ARTIFACTS-001` | Legacy/single-run transfer setup, weak state-recovery records, and no frozen external-validity protocol. |
| `H-MODEL-001` | The final conference abstract describes 28 assets, 35 macro edges, and 11 years; code and artifacts contain other universes, feature counts, and periods. | `KAIROS_FINAL.pdf`, page 1; canonical and archived sources | `E-PAPER-001`, `E-IMPL-001`, `E-LEGACY-ARTIFACTS-001` | Artifact-specific model/data identity cannot be generalized to the current implementation. |
| `H-CAUSAL-001` | Historical paper and metadata use wording such as unique causal trace, ground-truth cause, causal compliance, and native counterfactual reasoning. | Final conference artifact and legacy sources | `E-PAPER-001`, `E-LEGACY-ARTIFACTS-001` | Structural decomposition and masks do not establish causal identification or intervention effects. |

These records preserve history; they are not permitted current wording.
