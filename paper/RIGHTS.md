# Manuscript and conference-artifact rights

The root software license does not cover manuscript text, PDFs, figures,
slides, publisher or conference templates, or style files under `paper/`.
Copyright and upstream terms for each component remain controlling.

`snapshots/kairos-conference-final/` is a provenance record containing the
canonical PDF and a preservation-oriented normalized reconstruction. Its
presence does not grant permission to republish, adapt, or reuse its contents.
The project owner confirms that all named authors approved repository
distribution of both the final PDF as provided and the reconstruction bundle
(`main.tex` and the 15 figures listed in `source-checksums.sha256`) as provided.
Supporting records are retained privately where applicable. This closes only
the author-consent gate for those identified files; it does not grant rights in
third-party material or apply the root software license. The former
venue-specific template is not distributed.

The snapshot-level `figure-rights.toml` is mandatory for this reconstruction.
It enumerates exactly 15 PNGs by path and SHA-256 and records the narrow
distribution-as-provided status of each file. It grants no adaptation right,
no underlying-data right, no trademark right, and no scientific-claim status.
The separately locked TeX toolchain is build metadata and does not alter these
rights boundaries.

Every future paper snapshot must carry a rights manifest for its source, PDF,
figures, bibliography, and templates in addition to its evidence lock. A
collective statement is insufficient where figures are distributed: every
figure must have a path-stable, checksum-bound entry.

## Current verification status

The artifact names Duong Viet Hoang, Lun-Min Shih, and Yi-Hao Lai as paper
authors. The project owner reports that every named author approved repository
distribution of the final PDF and identified reconstruction source and figures
as provided. This closes the author-consent gate for those files; it does not
grant rights in third-party material or establish that an employer, sponsor,
venue, or publisher has no separate rights.

Before a new paper-source release, record written closure for:

- any university, employer, or sponsor agreement that assigns or restricts
  copyright;
- the conference or publisher agreement, including which of the submitted,
  accepted, and publisher-rendered versions may be self-archived;
- every figure, table, photograph, icon, code excerpt, and bibliography asset,
  including source, rights holder, license or written
  permission, attribution, modification rights, and redistribution rights;
- approval from all applicable rightsholders before applying a new license or
  offering a separate commercial license.

Keep contracts, permission emails, and identity documents outside the public
repository. Public documentation should record only the resulting status,
required attribution, and applicable license or restriction.
