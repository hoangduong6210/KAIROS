# Manuscript states

| Area | Role | Mutable? |
|---|---|---:|
| [`current-state/`](current-state/) | Living staging area for post-conference manuscript updates | Yes |
| [`snapshots/kairos-conference-final/`](snapshots/kairos-conference-final/) | Canonical final PDF plus a normalized, separately manifested Overleaf reconstruction | No |

`CONFERENCE_CURRENT` selects the final conference artifact. Superseded drafts,
slide exports, figure-generation scripts, and Edition 1 work are excluded from
the public tree under the archive boundary.

The project's current evidence release is `kairos-benchmark-v1`; the preserved
conference artifact itself has no evidence lock and is not the current paper.
`CURRENT` therefore reads `UNRELEASED`. The venue-specific template remains
excluded, while `main.tex` and 15 retained figures provide a generic,
preservation-oriented reconstruction directly inside the conference snapshot.
That bundle is neither the original camera-ready source nor an exact build
closure for the canonical PDF. Current updates belong in the wiki and, when a
manuscript is being prepared, `current-state/`. A future immutable paper
snapshot must lock an admitted claim set and frozen evidence release as
described by the wiki paper-export contract. Manuscript and template rights are
defined separately in [`RIGHTS.md`](RIGHTS.md).
