---
title: Traceability Policy
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Traceability Policy

## Required chain

A scientific or quantitative statement in the wiki must resolve through this
chain:

```text
statement -> C-* or H-* claim -> E-* evidence -> exact artifact/manifest
          -> lifecycle and scientific-use boundary
```

Current admitted wording uses a `C-*` identifier. Historical wording uses an
`H-*` identifier and cannot become current merely by being cited. Dataset
identity uses `D-*`; research questions use `RQ-*`.

## Trace annotations

Claim-bearing sections declare an HTML comment of the form:

```text
<!-- trace: C-EXAMPLE-001 E-EXAMPLE-001 -->
```

The annotation applies until the next heading at the same or higher level.
Inline `[Trace: ...]` markers may be used for short standalone statements. A
number in prose or a table is rejected by the wiki audit unless its section has
both a claim identifier and an evidence identifier. Dates in front matter,
hashes, paths, versions, code, and list ordinals are metadata rather than
scientific quantities.

## Evidence quality

Evidence records must identify lifecycle, exact artifacts, validation actually
performed, supported claims, and the scientific-use boundary. Hash validation
establishes byte identity only. Static code inspection establishes
implementation presence only. Neither establishes numerical correctness,
external validity, or causal identification.

## Publication boundary

Public pages may describe scientific methods, data scope, results, limitations,
and the evidence needed to reproduce them. Operational reports, private paths,
scheduler metadata, editorial notes, and authorship-analysis material are not
publication content. Repository checks enforce this separation; scientific
review remains a human responsibility.
