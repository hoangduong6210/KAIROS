---
title: Dataset Registry
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Dataset Registry

## D-MARKET-LEGACY-001

<!-- trace: C-DATA-001 E-DATA-001 -->

| Field | Value |
|---|---|
| Lifecycle | QUARANTINED |
| Locally staged files | `datasets/raw/raw_prices.csv`, `datasets/processed/pooled_z_scores.csv`, `datasets/processed/z_scores.csv` |
| Byte inventory | `datasets/checksums.sha256` |
| Domain | Historical market-price-derived features |
| Known gaps | Acquisition request/response provenance, stable vendor snapshot, license, missing-ticker accounting, schema version, and split registry |
| Compatible current claims | File identity (`C-DATA-001`) and benchmark input binding (`C-DATA-002`) only |

### Locally staged file inventory

<!-- trace: C-DATA-001 E-DATA-001 -->

| File | Data rows | Columns including `Date` | First recorded date | Last recorded date | SHA-256 |
|---|---:|---:|---|---|---|
| `datasets/raw/raw_prices.csv` | 3578 | 48 | 2014-01-01 | 2023-12-31 | `e66b2bd0312712428745f0d8cfcd2ee63857b1518f12ebc6d5443cc9bd491587` |
| `datasets/processed/pooled_z_scores.csv` | 2243 | 13 | 2017-11-10 | 2023-12-31 | `a27f902497a1c52abc3269b694985741cdf2fca9936ae5c64c537b718dbb9b83` |
| `datasets/processed/z_scores.csv` | 2244 | 13 | 2015-02-02 | 2023-12-29 | `caacab9d7436834b0c076f6605b77c7501c949a55fc97cf4d5f51ecfad027e40` |

These counts are file-schema observations, not claims about independent trading
days, data quality, market coverage, or suitability. The raw table contains
calendar-dated rows and forward-filled-looking repeated values; acquisition and
imputation provenance is not closed. [Trace: `C-DATA-001` → `E-DATA-001`]

No untracked cache is part of the current dataset identity or supports a claim.
The benchmark binds the raw CSV by checksum; a future dataset whose content,
source, coverage, or target semantics differ requires a new identity. [Trace:
`C-DATA-002` → `E-DATA-001`, `E-BENCH-001`]

The CSV bytes are intentionally excluded from future Git adds and software
distributions. A clean public checkout may contain only this registry,
`datasets/checksums.sha256`, and staging instructions; benchmark execution
requires users to stage checksum-matching inputs under their applicable access
terms. [Trace: `C-DATA-002` → `E-DATA-001`, `E-BENCH-001`]
