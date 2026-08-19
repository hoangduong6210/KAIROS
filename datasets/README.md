# Data boundary

`raw/raw_prices.csv` is the preserved raw-price table currently staged locally.
`processed/` contains derived z-score tables. These files were moved without
content changes during repository restructuring.

Their current bytes are inventoried in `checksums.sha256`. They do not constitute
a redistributable dataset release: source query identity, download response
metadata, licensing, and coverage failures remain incomplete. The CSV bytes are
local staging inputs and are excluded from source distributions and future Git
adds; public material retains only metadata and checksums. See [`RIGHTS.md`](RIGHTS.md).
New downloads must not overwrite these files; create a versioned run artifact
instead.

`cache/` is an ignored local-only area. Cache contents are not evidence and are
not required by repository contract tests.
