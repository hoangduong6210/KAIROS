---
title: Current Benchmark Status
status: VALIDATED
last_updated: 2026-08-19
paper_source: false
---

# Current Benchmark Status

<!-- trace: C-PERF-001 C-LEAD-001 C-XDOMAIN-001 C-EXP-002 E-BENCH-001 E-LEGACY-ARTIFACTS-001 E-EXP-001 -->

Benchmark v1 is the current validated evidence release. It contains five seeds
for each of KAIROS, GRU, and MLP, with fifteen successful attempts and no failed
attempts on 350 held-out test windows.

| Model | Balanced accuracy | F1 | ROC AUC |
|---|---:|---:|---:|
| KAIROS | 0.8123 ± 0.0127 | 0.5074 ± 0.0311 | 0.8951 ± 0.0266 |
| GRU | 0.8297 ± 0.0219 | 0.5474 ± 0.0171 | 0.9094 ± 0.0021 |
| MLP | 0.6663 ± 0.0100 | 0.3561 ± 0.0183 | 0.7477 ± 0.0079 |

Values are means ± sample standard deviations across the five declared seeds;
each model/seed attempt used the same 350 held-out test windows. KAIROS's
observed mean balanced accuracy was lower than GRU's and higher than MLP's.
Benchmark v1 prespecified no pairwise inferential test, so this is a descriptive
within-dataset comparison: it supports neither statistical superiority nor
non-inferiority. The target is a training-derived pseudo-label on one frozen
market dataset; the result does not establish broad generalization, causal
identification, physical validation, or external early-warning utility.
[Trace: `C-PERF-001` → `E-BENCH-001`]

Known audit conflicts include unequal seed counts, multiple reported model
sizes and feature counts, inconsistent test denominators, differing lead-time
definitions, and cross-domain failures omitted from some narrative summaries.
Historical values remain quarantined and are not merged into benchmark v1.

The complete file-level inventory is in the
[historical artifact catalog](Historical-Artifact-Catalog.md); major published
wording is in the [historical claim ledger](../claims/Historical-Claim-Ledger.md).
