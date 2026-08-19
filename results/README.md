# Results lifecycle

Historical artifacts from the earlier KAIROS workspace are isolated under
`historical/legacy-bundle/`. They are parseable outputs, not a frozen evidence
release. Their bytes are inventoried by the checksum manifest in that bundle;
known provenance and interpretation gaps are recorded in the wiki evidence
ledger. Local caches are not evidence and clean-checkout tests do not depend on
them.

`CURRENT` selects `kairos-benchmark-v1`, the current validated frozen evidence
release. Any correction or successor must be written to a new immutable
`frozen/<release-id>/` directory and selected only after schema, seed coverage,
data identity, configuration, source closure, failure accounting, and claim
review pass.
