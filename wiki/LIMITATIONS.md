---
title: Project Limitations
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Project Limitations

<!-- trace: C-DATA-001 C-PERF-001 C-LEAD-001 C-XDOMAIN-001 C-CAUSAL-001 C-EXP-002 H-CAUSAL-001 E-DATA-001 E-EXP-001 E-LEGACY-ARTIFACTS-001 E-PAPER-001 -->

- Historical market inputs were downloaded from mutable external services and
  do not yet have a complete frozen acquisition record or redistributable license record.
- Pseudo-label prediction is not causal identification. State-machine constraints
  and structural masking do not establish real-world interventions or unique causes.
- Historical lead-time results depend on split, threshold, smoothing, index,
  and seed choices that are not yet reconciled under one protocol.
- Benchmark v1 reports descriptive seed means and sample standard deviations but
  prespecified no pairwise inferential test; it supports neither statistical
  superiority nor non-inferiority. [Trace: `C-PERF-001` → `E-BENCH-001`]
- Single-seed and unequal-seed historical comparisons cannot support general
  performance claims.
- Cross-domain epidemiology artifacts do not by themselves establish transfer,
  outbreak detection, or physical/clinical validity.
- Historical papers, slides, reports, and release metadata contain conflicting
  counts and claim language; none overrides the current claim registry.
- The canonical implementation lacks focused numerical tests for transition
  semantics, stochastic TIP inference, pseudo-label behavior, and loss terms.
- The final conference artifact is preserved faithfully, but its finality as a
  conference file does not make its claims current evidence.
- The normalized conference source reconstruction compiles, but it is not the
  exact historical source closure and does not reproduce the canonical PDF's
  bytes, pagination, or layout. [Trace: `C-PAPER-001` → `E-PAPER-001`]
- Named-author consent for the identified conference PDF, source, and figures
  does not resolve provider rights for market data or any separate third-party,
  employer, venue, publisher, or template rights.
