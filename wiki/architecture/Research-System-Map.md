---
title: Research System Map
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Research System Map

The repository surface and semantic owners are enumerated in the
[project knowledge map](../PROJECT-KNOWLEDGE-MAP.md). This page describes the
scientific state transition rather than the directory tree.

```text
research question
  -> versioned data identity and target contract
  -> frozen configuration, splits, seeds, and gates
  -> src/kairos implementation + experiments entry point
  -> immutable atomic attempts with failure accounting
  -> validated release + checksums
  -> evidence ledger
  -> scoped claim review
  -> paper-source eligibility
  -> immutable paper snapshot
```

Benchmark v1 has passed the validated-release and scoped wording-review stages.
Its descriptive negative/mixed performance claim remains `VALIDATED`, not
`ADMITTED`: durable source closure is complete, and the flow currently stops
before publication admission. Post-conference manuscript work belongs in `paper/current-state/`;
the conference snapshot remains outside this flow and immutable. [Trace:
`C-REPO-001`, `C-PERF-001` → `E-REPO-001`, `E-BENCH-001`]
