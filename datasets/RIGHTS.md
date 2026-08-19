# Dataset rights and staging policy

No dataset in this directory is licensed by the repository-level software
license.

`raw/raw_prices.csv` and the derived CSV files are retained locally for
scientific traceability and checksum verification. Their acquisition records
and provider redistribution permissions are incomplete. They must not be
included in a public repository, source distribution, wheel, release archive,
or mirrored dataset until those rights are closed.

Public material may retain file identities, schemas, checksums, and an
acquisition recipe that does not reproduce provider content. A user who stages
the files locally must verify their digests against `checksums.sha256` before
running benchmark v1. Derived files do not automatically become
redistributable merely because the project transformed upstream values.

