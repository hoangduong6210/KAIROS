# KAIROS final conference artifact

`KAIROS_FINAL.pdf` is the canonical preserved conference paper. Its SHA-256 is
`184f40f4e6c4a22555f7ae568bbeb5f7d2105a80e495c71b09bc9e8e90eea9e0`,
recorded separately in `checksums.sha256`.

## Overleaf reconstruction bundle

`main.tex` and `figures/` form a self-contained, preservation-oriented
reconstruction bundle. They can be uploaded directly to Overleaf with
`main.tex` selected as the root document. The source uses a generic `article`
layout and contains no venue-specific template.

This bundle is not the original submitted or camera-ready source package and
is not an exact historical build closure. A successful compilation is not
expected to reproduce the bytes, pagination, or layout of `KAIROS_FINAL.pdf`.
`checksums.sha256` inventories only the canonical PDF;
`source-checksums.sha256` independently inventories `main.tex` and all 15
reconstruction figures.

The reconstruction preserves historical manuscript wording and claim-bearing
figures for editability and audit. It does not admit those statements as
current evidence, does not change `paper/CURRENT` from `UNRELEASED`, and does
not supersede the wiki or frozen evidence release. Conference-era numerical,
causal, early-warning, and cross-domain statements remain quarantined.

### Build

On Overleaf, select pdfLaTeX and `main.tex`. Locally, from this directory, run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The bibliography is inline, so no `.bib` file or separate BibTeX step is
required. Build success verifies LaTeX closure only; it does not verify
historical PDF equivalence or scientific claims.

### Change boundary

Do not modify this snapshot in place for new scientific work. Copy the bundle to
`paper/current-state/`, update it from admitted wiki content, and create a new
evidence-locked snapshot under the paper-export contract. Rights for the PDF,
source, and figures are defined in `RIGHTS.md` and the repository-level
`paper/RIGHTS.md`.
