---
title: Evidence Ledger
status: canonical
last_updated: 2026-08-19
paper_source: false
evidence_release: kairos-benchmark-v1
---

# Evidence Ledger

## E-IMPL-001

<!-- trace: C-IMPL-001 C-IMPL-002 C-IMPL-003 E-IMPL-001 -->

| Field | Value |
|---|---|
| Lifecycle | VALIDATED |
| Scientific purpose | Verify only the named canonical implementation structure and repository contracts |
| Source identity | `src/kairos/model.py`, SHA-256 `bd9c108c448ca747ba6031c42251fa9856d00c6da99c9da18ca0a511ee1e3a2f`; registered by `SOURCE.toml` and preserved in commit `5401c46804302e7095ef7cce57b4e6ea0ca9424e` |
| Artifact path | `src/kairos/model.py` |
| Validation | Repository contract tests, including Python syntax and required class inventory |
| Supported claims | `C-IMPL-001`, `C-IMPL-002`, `C-IMPL-003` |
| Scientific-use boundary | Static implementation inventory only; no numerical, performance, or causal conclusion |

## E-LEGACY-ARTIFACTS-001

<!-- trace: C-RESULT-001 C-PERF-001 C-LEAD-001 C-XDOMAIN-001 C-CAUSAL-001 H-PERF-001 H-LEAD-001 H-XDOMAIN-001 H-MODEL-001 H-CAUSAL-001 E-LEGACY-ARTIFACTS-001 -->

| Field | Value |
|---|---|
| Lifecycle | QUARANTINED |
| Scientific purpose | Preserve and audit the historical KAIROS result bundle |
| Artifact directory | `results/historical/legacy-bundle/`; artifact bytes are local and not distributed in public Git |
| Public byte inventory | `results/historical/legacy-bundle/checksums.sha256` |
| Nearest containing source commit | `d6d7ab6e4701ab3eb87de83ec52672d7171fb693` |
| Protocol/configuration identity | Incomplete; parameters are distributed across scripts and artifacts |
| Data identity | `D-MARKET-LEGACY-001`, incomplete provenance |
| Execution identity | Mixed experiments and dates; no complete immutable attempt ledger |
| Coverage/failures | Not consistently recorded |
| Supported current claims | None |
| Historical claim links | `H-PERF-001`, `H-LEAD-001`, `H-XDOMAIN-001`, `H-MODEL-001`, `H-CAUSAL-001` |
| Scientific-use boundary | Audit and historical reconstruction only |

The checksum inventory detects subsequent drift from the restructuring audit
state. For tracked files, preservation was also checked against the prior Git
blobs. The ignored legacy cache had no Git baseline. These checks do not
validate schema, computation, interpretation, or claim eligibility.

## E-EXP-001

<!-- trace: C-EXP-001 C-EXP-002 C-DATA-002 E-EXP-001 -->

| Field | Value |
|---|---|
| Lifecycle | VALIDATED |
| Artifact paths | `experiments/07_confirmatory_benchmark.py`, `configs/benchmark-v1.json`, `protocols/benchmark-v1.md` |
| SHA-256 | `171e937c5ebfa8de759ef5b3d6089035ec49757613f0504cd9b14d1c38edeba8`, `b11035996800de90b2c9e4f2e273277fbbddac1b6b82a916fdfb97d4383826e2`, `05e6bad173282434264eb63fdf9da155c7531b64e72196985f392b8806dfe8c7` |
| Validation | Static protocol, checksum, seed-registry, canonical-import, output, and failure-record inspection |
| Supported claims | `C-EXP-001`, `C-EXP-002`, `C-DATA-002` |
| Scientific-use boundary | Protocol and runner closure only; numerical claims require a finalized execution release |

## E-DATA-001

<!-- trace: C-DATA-001 C-DATA-002 E-DATA-001 E-IMPL-001 -->

| Field | Value |
|---|---|
| Lifecycle | VALIDATED |
| Dataset identity | `D-MARKET-LEGACY-001` |
| Artifact paths | `datasets/raw/raw_prices.csv`, `datasets/processed/pooled_z_scores.csv`, `datasets/processed/z_scores.csv` |
| Byte inventory | `datasets/checksums.sha256` |
| Validation | CSV header, row count, column count, date-boundary, and checksum checks |
| Supported claims | `C-DATA-001`, together with `E-EXP-001` for `C-DATA-002` |
| Scientific-use boundary | File identity and schema only; no acquisition provenance, license closure, or target validity |

## E-PAPER-001

<!-- trace: C-PAPER-001 H-PERF-001 H-LEAD-001 H-XDOMAIN-001 H-MODEL-001 H-CAUSAL-001 E-PAPER-001 -->

| Field | Value |
|---|---|
| Lifecycle | VALIDATED |
| Artifact path | `paper/snapshots/kairos-conference-final/KAIROS_FINAL.pdf` |
| Manifests | Canonical PDF inventory in `paper/snapshots/kairos-conference-final/checksums.sha256`; reconstruction inventory in `paper/snapshots/kairos-conference-final/source-checksums.sha256`; exhaustive historical wording disposition in `paper/snapshots/kairos-conference-final/claim-disposition.json`; boundary metadata in `artifact.toml` |
| Identity | 34 pages; SHA-256 `184f40f4e6c4a22555f7ae568bbeb5f7d2105a80e495c71b09bc9e8e90eea9e0` |
| Validation | Canonical PDF parsing, text extraction, first/last-page rendering, and exact SHA-256 verification; reconstruction checksum closure, 15-of-15 figure-reference closure, and successful pdfLaTeX compilation; 171-of-171 caption/table/theorem/algorithm/substantive-or-short-claim-prose disposition coverage with every unit unadmitted; contract check that no venue-specific template is present |
| Supported claim | Artifact-identity claim `C-PAPER-001`; direct source for quarantined historical claim records |
| Scientific-use boundary | Artifact identity and reconstruction closure only; the normalized source is not the exact historical build closure, is not expected to reproduce the canonical PDF, and does not admit paper values or causal wording as current evidence |

## E-REPO-001

<!-- trace: C-REPO-001 E-REPO-001 -->

| Field | Value |
|---|---|
| Lifecycle | VALIDATED |
| Artifact paths | `PROJECT.toml`, `README.md`, `wiki/PROJECT-KNOWLEDGE-MAP.md` |
| Validation | Repository layout and pointer contract tests |
| Supported claim | `C-REPO-001` |
| Scientific-use boundary | Organization and lifecycle boundaries only |

## E-BENCH-001

<!-- trace: C-PERF-001 C-EXP-002 C-DATA-002 E-BENCH-001 -->

| Field | Value |
|---|---|
| Lifecycle | VALIDATED |
| Scientific purpose | Evaluate KAIROS against GRU and MLP under the frozen benchmark-v1 within-dataset pseudo-label protocol |
| Artifact path | `results/frozen/kairos-benchmark-v1/result.json` |
| Artifact checksum | SHA-256 `4ad144a070cd406e7c92ccd8effe0fb7cb881dc8adbac2a83a9187f0bcd0d1c1` |
| Release manifest | `results/frozen/kairos-benchmark-v1/release.json` and `results/frozen/kairos-benchmark-v1/checksums.sha256` |
| Source identity | Benchmark execution source `src/kairos/model.py` SHA-256 `b9dbbcb36bac125a10912b87033ec46814c4b0a2ffe70ef8e55a01f1919d32da`; current canonical source SHA-256 `bd9c108c448ca747ba6031c42251fa9856d00c6da99c9da18ca0a511ee1e3a2f` is registered in `SOURCE.toml` as a seven-line license-notice-only successor and preserved in commit `5401c46804302e7095ef7cce57b4e6ea0ca9424e`; benchmark not rerun |
| Protocol/configuration identity | `protocols/benchmark-v1.md` SHA-256 `05e6bad173282434264eb63fdf9da155c7531b64e72196985f392b8806dfe8c7`; `configs/benchmark-v1.json` SHA-256 `b11035996800de90b2c9e4f2e273277fbbddac1b6b82a916fdfb97d4383826e2` |
| Data identity | `datasets/raw/raw_prices.csv` SHA-256 `e66b2bd0312712428745f0d8cfcd2ee63857b1518f12ebc6d5443cc9bd491587` |
| Coverage/failures | Fifteen declared attempts, fifteen successes, zero failures; five seeds for each of three models |
| Acceptance-gate outcome | Complete, finite, deterministic GPU execution; aggregate metrics replicated exactly across two compute executions |
| Supported claims | `C-PERF-001`, `C-EXP-002`, `C-DATA-002` |
| Scientific-use boundary | Descriptive within-dataset pseudo-label comparison only; no prespecified pairwise inferential test and no superiority, non-inferiority, causal, cross-domain, physical-validation, or external early-warning conclusion |
