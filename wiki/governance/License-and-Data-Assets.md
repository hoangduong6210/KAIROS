---
title: License and Data Assets
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# License and Data Assets

<!-- trace: C-REPO-001 C-DATA-001 E-REPO-001 E-DATA-001 -->

The repository now declares `AGPL-3.0-or-later` for original KAIROS software.
The authoritative boundary is the root `LICENSE`, `LICENSE_SCOPE.md`, `NOTICE`,
and `THIRD_PARTY_NOTICES.md`. This closes the current software-license choice;
it does not convert every repository artifact into AGPL material.

| Surface | Current rights boundary |
|---|---|
| `src/`, active experiment and support software | `AGPL-3.0-or-later`, unless a file states otherwise |
| `configs/`, tests | Covered only to the extent they are original copyrightable software; embedded third-party material remains excluded |
| Protocols, wiki, and public documentation prose | Rights retained by respective authors pending a separate documentation-license decision |
| `datasets/` | No redistribution grant; local bytes are excluded from future Git adds and distributions |
| `results/frozen/` | Evidence records may be reviewed; no upstream-data rights are granted |
| `paper/`, PDFs, figures, slides, styles | Excluded from the software license; author, venue, and third-party terms control |
| `archive/` | Per-file notices control; unclear provenance means no redistribution grant |
| `releases/` | Public placeholder only; the historical distribution is excluded from the current public tree |
| `assets/` | Admit only assets with recorded source, holder, license, attribution, and redistribution permission |

The existing code lineage was previously distributed under AGPL, so switching
the current derivative implementation to MIT or BSD would require written
relicensing authorization from all applicable rights holders. Former
commercial-license and CLA material is not distributed and does not constitute
a current offer.

The canonical model now embeds its SPDX, retained copyright, and dated
modification notice. `SOURCE.toml` registers its new canonical hash and the
prior benchmark execution-source hash as a license-notice-only transition. The
frozen evidence release remains byte-identical and is not described as rerun.

Market-data client licensing does not grant rights in data-provider content.
The benchmark CSVs remain checksum-identified local staging inputs until their
acquisition provenance and redistribution permissions are closed. Public
packages must exclude their bytes, as enforced by `MANIFEST.in` and repository
ignore rules.

`KAIROS_FINAL.pdf` remains the canonical conference artifact. A generic,
normalized reconstruction (`main.tex` plus 15 manifested figures) is preserved
beside it; the venue-specific template is not distributed. The project owner
confirms all named authors approved distribution of those identified files as
provided, while the root AGPL grant does not apply to them and third-party,
employer, venue, and publisher terms remain controlling. Preservation does not
grant republication or adaptation rights. A future snapshot must carry both an
evidence lock and a rights manifest.

These boundaries reduce accidental over-licensing and redistribution; they do
not replace review by the applicable rights holders or qualified counsel when a
public release is prepared.
