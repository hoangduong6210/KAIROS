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
`source-checksums.sha256` independently inventories `main.tex`, the locked TeX
toolchain declaration, and all 15 reconstruction figures. The canonical PDF is
never generated or overwritten by the reconstruction build.

Historical wording in the reconstruction is dispositioned unit by unit in
[`claim-disposition.json`](claim-disposition.json). The human-readable
boundary and audit contract are summarized in [`CLAIMS.md`](CLAIMS.md). This
inventory records where wording occurs and why it remains quarantined; it is
not evidence that any historical statement is true.

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

### Locked CI toolchain

[`tex-toolchain.lock.toml`](tex-toolchain.lock.toml) records the root document,
compiler arguments, immutable GitHub Action commit, and immutable TeX Live
container manifest digest used by repository CI. The date-like image tag in the
lock is provenance evidence only; CI resolves the image by digest.

To reproduce the CI toolchain locally with Docker, run from this directory:

```bash
docker run --rm \
  --volume "$PWD:/work" \
  --workdir /work \
  --entrypoint latexmk \
  ghcr.io/xu-cheng/texlive-full@sha256:c2fc32a343b5b351a3401f3e1083ebe3774c06d0ab746ac8377029acb1daf47f \
  -pdf -file-line-error -halt-on-error -interaction=nonstopmode main.tex
```

The locked generic build currently produces 36 pages. The preserved canonical
`KAIROS_FINAL.pdf` has 34 pages; this difference is expected because the
venue-specific layout is intentionally absent. Generated `main.pdf` bytes,
pagination, and layout are not evidence and must not be substituted for the
canonical PDF.

### Figure provenance and rights

[`figure-rights.toml`](figure-rights.toml) identifies every one of the 15 PNG
files by relative path and SHA-256 and records its repository-distribution,
adaptation, underlying-data, trademark, and claim-status boundaries. It is a
public status record, not a substitute for private authorization records and
not a license grant.

### Change boundary

Do not modify this snapshot in place for new scientific work. Copy the bundle
to `paper/current-state/`, update it from admitted wiki content, and create a
new evidence-locked snapshot under the paper-export contract. Rights for the
PDF, source, and figures are defined in `RIGHTS.md`, `figure-rights.toml`, and
the repository-level `paper/RIGHTS.md`.
