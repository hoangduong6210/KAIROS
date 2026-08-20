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

## External benchmark staging

The public repository does not distribute benchmark CSV bytes. The exact input
identity and minimal schema are declared in
[`benchmark-v1-input.json`](benchmark-v1-input.json). Given a lawfully obtained
copy, verify it without writing anything:

```bash
python scripts/stage_benchmark_input.py /path/to/raw_prices.csv --json
```

Add `--stage` to copy a verified file to the canonical local path. Staging uses
exclusive creation and refuses to replace an existing file. See
[`reproducibility/README.md`](../reproducibility/README.md) for the complete
environment and scheduler workflow.
