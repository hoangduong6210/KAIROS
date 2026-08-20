---
title: Start Here
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Start Here

## Objective and stage

KAIROS studies whether a state-constrained temporal graph model can provide
useful, inspectable representations of market-regime transitions. The current
stage is `evidence-release`: benchmark v1 is the current validated evidence
release, while no evidence-locked paper snapshot is current.

The repository is named `KAIROS`. The final conference artifact is preserved at
`paper/snapshots/kairos-conference-final/` together with a generic, normalized
Overleaf reconstruction; superseded paper work and the venue-specific template
are excluded under the archive boundary. Post-conference manuscript updates
belong in `paper/current-state/`, after the wiki is updated. The conference
artifact and reconstruction are not a current evidence-locked paper release.

## Current pointers

| Pointer | Value |
|---|---|
| Evidence release | `kairos-benchmark-v1` |
| Paper snapshot | `UNRELEASED` |
| Final conference artifact | `kairos-conference-final` |
| Conference artifact path | `paper/snapshots/kairos-conference-final/` |
| Canonical implementation | `src/kairos/model.py` |

## Supported and unresolved statements

The repository supports descriptive implementation statements and one scoped
benchmark finding: under frozen benchmark v1, KAIROS's observed mean balanced
accuracy was lower than GRU's and higher than MLP's. No pairwise inferential
test was prespecified, so this does not establish statistical superiority or
non-inferiority. No lead-time or cross-domain claim is current, and the
observational benchmark supports no causal-effect wording. [Trace:
`C-PERF-001`, `C-CAUSAL-001` → `E-BENCH-001`]

## Remaining limitations

- The validated input is frozen by checksum, but acquisition provenance and
  redistribution rights remain unresolved; its bytes are local-only staging.
- The target is training-derived and limited to one market dataset.
- The current paper pointer remains unreleased; the conference artifact is a
  preserved historical snapshot.

## Next actions

1. Formally review `C-PERF-001` for publication admission without changing its
   negative and limited-scope wording.
2. Close data-provider and any separate third-party, employer, venue, or
   publisher rights; the software license and named-author consent are recorded separately.
3. Develop post-conference wording in `paper/current-state/`, then create a new
   snapshot only from admitted, evidence-linked wiki content.

Safe first check: `python -m pytest`. Read [Project Status](status/Project-Status.md),
[Current Claim Language](claims/Current-Claim-Language.md), [Evidence Ledger](evidence/Evidence-Ledger.md),
and [Reproducibility](REPRODUCIBILITY.md) before claim-bearing work.
