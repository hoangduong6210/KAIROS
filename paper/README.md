# Manuscript states

| Area | Role | Mutable? |
|---|---|---:|
| [`current-state/`](current-state/) | Living staging area for post-conference manuscript updates | Yes |
| [`snapshots/kairos-conference-final/`](snapshots/kairos-conference-final/) | PDF-only final conference artifact and integrity metadata | No |

`CONFERENCE_CURRENT` selects the final conference artifact. Superseded drafts,
slide exports, figure-generation scripts, and Edition 1 work are excluded from
the public tree under the archive boundary.

The project's current evidence release is `kairos-benchmark-v1`; the preserved
conference artifact itself has no evidence lock and is not the current paper.
`CURRENT` therefore reads `UNRELEASED`. The project owner explicitly authorized
removal of the former venue-specific source/template bundle; the final PDF was
not changed. Current updates belong in the wiki and, when a
manuscript is being prepared, `current-state/`. A future immutable paper
snapshot must lock an admitted claim set and frozen evidence release as
described by the wiki paper-export contract. Manuscript and template rights are
defined separately in [`RIGHTS.md`](RIGHTS.md).
