# Third-party and external-material boundary

The root `LICENSE` covers original KAIROS software only, as limited by
`LICENSE_SCOPE.md`. It does not relicense third-party software, data, templates,
or assets.

## Python dependencies

Dependencies named in `pyproject.toml` are obtained separately and retain
their upstream licenses. They are not vendored by the canonical package.

## Market data

The benchmark CSV files originated from mutable market-data services. Their
exact bytes are identified by checksum for scientific traceability, but
acquisition provenance and redistribution permission are not closed. The
license of a download client does not grant rights in provider data. See
`datasets/RIGHTS.md`.

## Conference and publication material

`paper/snapshots/kairos-conference-final/` contains the canonical conference
PDF plus a generic, normalized reconstruction made from retained manuscript
text and 15 retained figures. No venue-specific template is distributed. The
PDF, manuscript text, and figures are not covered by the software license and
retain their respective rights. Preservation for provenance and future
authoring does not imply permission to republish or adapt them.

## Historical and archived material

The local, non-distributed `archive/` payload may contain scripts, media, cached
outputs, or other material with incomplete provenance. Archived material is
excluded from the public Git tree except for its boundary README and does not
inherit a new license from the repository root.

Users who redistribute excluded material are responsible for obtaining the
necessary permissions and carrying all applicable notices.
