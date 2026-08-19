---
title: Market Data and Target Contract
status: VALIDATED
last_updated: 2026-08-19
paper_source: false
---

# Market Data and Target Contract

## Canonical defaults and benchmark binding

<!-- trace: C-IMPL-002 C-DATA-001 C-DATA-002 E-IMPL-001 E-DATA-001 -->

The canonical module requests adjusted closing prices from a mutable yfinance
endpoint, then forward-fills and backward-fills missing values. It derives log
returns, rolling z-scores with a 20-observation window and minimum history of
five observations, clips z-scores to the interval from -5 to 5, and uses median
price as a rough cluster-weight proxy. These are implementation facts, not
approved data semantics.

The canonical defaults request 2014-01-01 through 2025-04-30 and split after
2020-12-31 and 2022-12-31. The tracked raw CSV instead records 3578 rows and 48
columns including the date field, from 2014-01-01 through 2023-12-31. Benchmark
v1 explicitly binds this tracked file by checksum rather than assuming it is
the output of the mutable downloader. [Trace: `C-DATA-002` → `E-DATA-001`,
`E-EXP-001`]

The pseudo-target uses future information by construction: a smoothed risk-on
series is compared with a future minimum over a 15-step horizon, with a base
threshold of 0.7. Benchmark v1 estimates the adaptive threshold from training
data only and excludes samples whose target horizon crosses a temporal
partition. It remains a supervised pseudo-label, not observed causal ground
truth. [Trace: `C-IMPL-002`, `C-DATA-002` → `E-IMPL-001`, `E-EXP-001`]

## Contract boundary

Benchmark v1 freezes:

- ticker universe, adjustment policy, calendar, timezone, and query interval;
- source/version/license, raw response hashes, missingness, delisting, and failure rules;
- feature formulas, rolling-window warm-up, units, clipping, and normalization scope;
- regime target, forecast horizon, intervention-day handling, and class threshold;
- train/validation/test dates and proof that fitting, selection, and smoothing do not cross boundaries;
- seed registry and one immutable row identity per observation.

Acquisition provenance and redistribution rights remain unresolved, so the
dataset is eligible for this benchmark but not automatically eligible for
redistribution.
