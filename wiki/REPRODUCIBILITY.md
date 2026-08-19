---
title: Reproducibility Contract
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Reproducibility Contract

A claim-bearing run must record the source commit, exact configuration and
environment, immutable data identity and checksums, task/seed coverage, every
failed or excluded attempt, raw and finalized artifact paths, aggregation
procedure, and claim/figure mapping.

Mutable runs must use a new run ID and must never overwrite a frozen release.
Finalization fails closed on missing, duplicate, non-finite, unexpected, or
hash-drifted records. `PROJECT.toml`, `results/CURRENT`, wiki evidence metadata,
`paper/CURRENT`, and the paper results lock must agree.

The current historical checksum inventory protects bytes only. It does not
close source, data, environment, checkpoint, or execution provenance.

