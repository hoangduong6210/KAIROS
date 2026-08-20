# Historical claim boundary

The conference PDF and its normalized reconstruction preserve historical
scientific wording. They do not make that wording current, validated, or
paper-eligible.

`claim-disposition.json` is the machine-readable disposition inventory for
`main.tex`. It binds each extracted unit to an exact source hash and line span.
The inventory intentionally covers a superset of claim-bearing material:

| Unit type | Count |
|---|---:|
| Captions | 29 |
| Tables | 13 |
| Theorem-like environments | 10 |
| Algorithms | 1 |
| Substantive or short claim-bearing prose blocks | 118 |
| **Total** | **171** |

Every unit has `admitted: false` and one of two dispositions:

- `QUARANTINED_ARTIFACT_ONLY`: the wording belongs to one or more existing
  historical `H-*` claim families. Its `E-*` references prove only where the
  historical wording occurs; they do not support its truth.
- `UNSUPPORTED_QUARANTINED`: the prose is preserved for provenance but has no
  truth-supporting claim record and must not be reused as a current statement.

The inventory never maps conference wording to a current `C-*` claim. Current
permitted wording remains exclusively in the wiki claim registry and frozen
evidence ledger.

Run the fail-closed audit from the repository root:

```bash
python scripts/audit_historical_paper_claims.py
```

The audit re-extracts every caption, table, theorem-like environment,
algorithm, and substantive or short claim-bearing prose block. It rejects source drift, missing or
stale units, hash/line mismatches, unknown identifiers, empty reasons, and any
entry that does not explicitly remain unadmitted.
