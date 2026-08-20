---
title: Current Claim Language
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Current Claim Language

## Validated repository statements

<!-- trace: C-IMPL-001 C-IMPL-002 C-IMPL-003 C-EXP-001 C-EXP-002 C-DATA-001 C-DATA-002 C-PERF-001 C-PAPER-001 C-RESULT-001 C-REPO-001 E-IMPL-001 E-EXP-001 E-DATA-001 E-BENCH-001 E-PAPER-001 E-LEGACY-ARTIFACTS-001 E-REPO-001 -->

| Claim ID | Lifecycle | Exact permitted statement | Scope and qualifier | Evidence | Paper eligible |
|---|---|---|---|---|---|
| `C-IMPL-001` | VALIDATED | The canonical repository contains a four-stage implementation with RSE, a five-state CSM, RMP/TIP, and SCP components. | Static implementation inventory only; not numerical correctness, causal identification, or performance. | `E-IMPL-001` | No |
| `C-IMPL-002` | VALIDATED | The canonical source declares 28 unique tickers, seven risk-on clusters, five risk-off clusters, 35 directed cluster pairs, eight edge features, sequence length 20, hidden width 48, latent width 24, and default seed 42. | Static defaults in `src/kairos/model.py`; not a frozen experiment protocol. | `E-IMPL-001` | No |
| `C-IMPL-003` | VALIDATED | The canonical source samples the TIP latent in every forward pass and initializes CSM probability in DEATH; statements of deterministic inference or a different initial state are not current implementation facts. | Static code-path inspection; runtime distributional behavior is not validated. | `E-IMPL-001` | No |
| `C-EXP-001` | VALIDATED | The active experiment surface contains one benchmark-v1 runner configured to write mutable output under `runs/benchmark-v1/`. | Entry-point inventory only; execution or scientific validity is not implied. | `E-EXP-001` | No |
| `C-EXP-002` | VALIDATED | Benchmark v1 binds canonical KAIROS and two declared baselines to the same frozen data, temporal partitions, training budget, and five-seed registry. | Static protocol and implementation closure; result admission requires a complete execution record. | `E-EXP-001` | No |
| `C-DATA-001` | VALIDATED | The locally staged legacy dataset bundle has the row, column, date-boundary, and checksum identities recorded in the dataset registry. | Byte/schema inventory only; provider provenance and redistribution rights remain open; public distributions retain metadata rather than CSV bytes. | `E-DATA-001` | No |
| `C-DATA-002` | VALIDATED | Benchmark v1 binds `datasets/raw/raw_prices.csv` by checksum and declares its feature, target, split, purge, and seed contracts. | Internal benchmark eligibility only; acquisition provenance and redistribution rights remain outside this claim. | `E-DATA-001`, `E-EXP-001` | No |
| `C-PERF-001` | VALIDATED | Under frozen benchmark v1, mean test balanced accuracy across the five declared seeds was 0.8123 ± 0.0127 for KAIROS, 0.8297 ± 0.0219 for GRU, and 0.6663 ± 0.0100 for MLP. KAIROS's observed mean was lower than GRU's and higher than MLP's. | Mean ± sample SD; the same 350 held-out test windows for every model/seed attempt; one market dataset with training-derived pseudo-labels. No pairwise inferential test was prespecified, so this is descriptive and does not establish superiority or non-inferiority. | `E-BENCH-001` | No; formal publication admission remains |
| `C-PAPER-001` | VALIDATED | `KAIROS_FINAL.pdf` is the preserved 34-page conference artifact with SHA-256 `184f40f4e6c4a22555f7ae568bbeb5f7d2105a80e495c71b09bc9e8e90eea9e0`. | Artifact identity only; its scientific claims are not admitted. | `E-PAPER-001` | No |
| `C-RESULT-001` | VALIDATED | The legacy result bundle contains 12 JSON records and one TeX table, all quarantined and checksummed. | Artifact inventory only; values are not admitted results. | `E-LEGACY-ARTIFACTS-001` | No |
| `C-REPO-001` | VALIDATED | Canonical, historical, frozen-release, and paper-snapshot material occupy separate repository lifecycle areas documented by the knowledge map. | Repository organization only. | `E-REPO-001` | No |

## Proposed and rejected research claims

<!-- trace: C-PERF-001 C-LEAD-001 C-XDOMAIN-001 C-CAUSAL-001 C-EXP-002 C-DATA-002 E-LEGACY-ARTIFACTS-001 E-EXP-001 E-DATA-001 E-IMPL-001 -->

| Claim ID | Lifecycle | Permitted status statement | Existing evidence | What remains |
|---|---|---|---|---|
| `C-LEAD-001` | PROPOSED | No current early-warning lead-time claim is admitted. | `E-LEGACY-ARTIFACTS-001` contains conflicting historical counts. | A separately preregistered external-index protocol; not a benchmark-v1 gate. |
| `C-XDOMAIN-001` | PROPOSED | No current cross-domain generalization claim is admitted. | `E-LEGACY-ARTIFACTS-001` is single-run/legacy evidence. | A separately preregistered target domain; not a benchmark-v1 gate. |
| `C-CAUSAL-001` | REJECTED | The current observational benchmark does not identify intervention effects and supports no causal-effect wording. | Structural code and `E-LEGACY-ARTIFACTS-001` do not provide an identification design. | A future causal claim requires a new estimand, assumptions, design/data, and falsification protocol. |

Prohibited wording includes “ground-truth cause,” “100% causal compliance,”
“unique causal trace,” “validated early detection,” or an unqualified numerical
headline derived from the historical artifacts.
