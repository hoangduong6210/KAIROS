---
title: Paper Export Contract
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Paper Export Contract

A paper snapshot is eligible only when every quantitative statement resolves
to an admitted claim and exact frozen evidence artifact. Its manifest must lock
the snapshot ID, source wiki commit, claim IDs/versions, evidence release and
hashes, figure/table sources, bibliography hash, manuscript/PDF hashes,
toolchain identity, and review dates.

The paper must also include `results.lock.yaml`; its release must match
`PROJECT.toml`, `results/CURRENT`, wiki evidence metadata, and `paper/CURRENT`.
Submitted and accepted snapshots are immutable. The current paper pointer is
`UNRELEASED`. `paper/CONFERENCE_CURRENT` separately identifies
`kairos-conference-final`, the preserved final conference artifact under
`paper/snapshots/`. It predates this evidence-lock contract and is retained for
provenance, not admitted as a current claim-bearing release. The superseded
venue-specific build workspace is not distributed in the public tree. A
normalized generic reconstruction is preserved directly in the conference
snapshot for editability, but it predates the evidence-lock contract and is not
current paper source. Living post-conference manuscript work belongs in
`paper/current-state/`; it is not a snapshot and cannot be selected by
`paper/CURRENT` until it has passed this export contract.
