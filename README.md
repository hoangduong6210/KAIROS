# KAIROS — Stateful Temporal Graph Modeling for Market-Regime Research

> **CURRENT EVIDENCE STATUS.** Under the frozen benchmark-v1 protocol,
> KAIROS's observed mean balanced accuracy was lower than GRU's and higher than
> MLP's. This is a descriptive result on one frozen market dataset with
> training-derived pseudo-labels. It does not establish statistical
> superiority, non-inferiority, causal identification, cross-domain
> generalization, or external early-warning utility.

KAIROS is a research codebase for compiling temporal market events into
stateful graph representations with the RS-GNN pipeline. The repository is in
the `evidence-release` stage: `kairos-benchmark-v1` is the current validated
evidence release, while no evidence-locked current paper has been released.

The implementation uses PyTorch. Original KAIROS software is licensed under
`AGPL-3.0-or-later`; datasets, manuscript material, conference assets,
archives, and third-party content are governed separately by
[`LICENSE_SCOPE.md`](LICENSE_SCOPE.md), [`NOTICE`](NOTICE), and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

Research status: the current result is an auditable within-dataset pseudo-label
comparison, not a causal study, external validation, or financial or investment
advice. The version-controlled [wiki](wiki/README.md) is authoritative for
project status, protocols, permitted claim language, evidence, and limitations.
New contributors should begin with [`wiki/START-HERE.md`](wiki/START-HERE.md).

## Manuscript packages

The repository separates the mutable post-conference manuscript state from the
immutable conference artifact:

| Package | Purpose | Status |
|---|---|---|
| [`paper/current-state/`](paper/current-state/) | Living staging area for post-conference updates | Mutable; currently no claim-bearing manuscript |
| [`paper/snapshots/kairos-conference-final/`](paper/snapshots/kairos-conference-final/) | Canonical conference PDF plus a separately manifested Overleaf reconstruction | Immutable historical snapshot; reconstruction is not exact source closure |

`paper/CONFERENCE_CURRENT` identifies `kairos-conference-final`, while
`paper/CURRENT` remains `UNRELEASED`. The conference artifact predates the
current evidence-lock contract, so its claims do not override the wiki. Its
venue-specific template is not part of the public tree. A generic, normalized
`main.tex` reconstruction and its 15 retained figures are included beside the
PDF for preservation and future editing; they are not the original submitted
or camera-ready source and are not expected to reproduce the canonical PDF.
Future manuscript revisions must be developed in `paper/current-state/` from
admitted wiki content and locked to a frozen evidence release before snapshot
publication.

## Current evidence status

Benchmark v1 completed all 15 declared model/seed attempts without failures on
the same 350 held-out test windows.

| Model | Balanced accuracy | F1 | ROC AUC |
|---|---:|---:|---:|
| KAIROS | 0.8123 ± 0.0127 | 0.5074 ± 0.0311 | 0.8951 ± 0.0266 |
| GRU | 0.8297 ± 0.0219 | 0.5474 ± 0.0171 | 0.9094 ± 0.0021 |
| MLP | 0.6663 ± 0.0100 | 0.3561 ± 0.0183 | 0.7477 ± 0.0079 |

Values are means ± sample standard deviations across the five declared seeds.
KAIROS's observed mean balanced accuracy was lower than GRU's and higher than
MLP's. No pairwise inferential test was prespecified, so the comparison
supports neither statistical superiority nor non-inferiority. The exact
permitted wording is claim
[`C-PERF-001`](wiki/claims/Current-Claim-Language.md), backed by
[`E-BENCH-001`](wiki/evidence/Evidence-Ledger.md), the
[current benchmark page](wiki/results/Current-Benchmark-Status.md), and the
[frozen release](results/frozen/kairos-benchmark-v1/).

Conference-era headline values and legacy outputs are not current evidence and
must not be merged into the benchmark-v1 result. The superseded historical
release bundle is not part of the public distribution.

## Layout

```text
src/kairos/       canonical reusable implementation
experiments/      active benchmark entry point
configs/          frozen machine-readable configuration
protocols/        versioned experiment and admission contract
datasets/         public rights/checksum metadata; inputs are staged locally
results/          current frozen evidence plus legacy quarantine metadata
runs/             mutable execution outputs; never authoritative evidence
paper/            current manuscript staging and immutable conference snapshot
wiki/             canonical status, methods, claims, evidence, and limitations
docs/             technical reference material
scripts/          integrity, disclosure, and reporting utilities
tests/            repository, evidence, and import contract checks
archive/          public boundary documentation; legacy contents are excluded
releases/         public boundary documentation; historical bundle is excluded
assets/           rights-cleared public assets only
```

## Benchmark-v1 protocol

The frozen protocol binds KAIROS, GRU, and MLP to the same data checksum,
temporal partitions, forward-horizon exclusions, training budget, primary
metric, and five-seed registry. The target threshold is estimated from the
training partition only. Every model/seed pair must produce either a success
record or an explicit failure record, and aggregation fails closed if coverage
is incomplete or reported values are non-finite.

The authoritative design is in
[`protocols/benchmark-v1.md`](protocols/benchmark-v1.md) and
[`configs/benchmark-v1.json`](configs/benchmark-v1.json). Heavy training must
run inside a scheduled compute allocation, never on a shared login node.

## Install

Python 3.9 or newer is supported.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest
```

A lightweight import check is:

```bash
python -c 'from kairos import model; print(model.N_EDGES)'
```

## Data

The benchmark configuration expects `datasets/raw/raw_prices.csv` with the
checksum recorded in `configs/benchmark-v1.json`. The CSV bytes are local-only
staging inputs and are intentionally excluded from source distributions. Public
material retains identity metadata and checksums, not a redistribution grant.

Do not replace or overwrite the staged file. New acquisitions must be recorded
as versioned artifacts with source, query, response metadata, license, schema,
and checksum closure. See [`datasets/README.md`](datasets/README.md) and
[`datasets/RIGHTS.md`](datasets/RIGHTS.md).

## Reproducing a result

Do not overwrite `results/frozen/`. From a checkout with the exact input
checksum, execute the runner only inside an allocated compute environment:

```bash
python experiments/07_confirmatory_benchmark.py \
  --config configs/benchmark-v1.json
```

The mutable result is written atomically to `runs/benchmark-v1/result.json`.
Before scientific use, verify complete model/seed coverage, all
source/configuration/protocol/data hashes, explicit failures, finite metrics,
and the frozen-release admission record. Environment and timing fields can vary
across platforms; reproduction does not mean rewriting the immutable release.

### Provenance

[`PROJECT.toml`](PROJECT.toml), [`results/CURRENT`](results/CURRENT),
[`paper/CURRENT`](paper/CURRENT), and
[`paper/CONFERENCE_CURRENT`](paper/CONFERENCE_CURRENT) define the active
evidence and manuscript pointers. Exact benchmark identities are recorded in
[`release.json`](results/frozen/kairos-benchmark-v1/release.json) and
[`checksums.sha256`](results/frozen/kairos-benchmark-v1/checksums.sha256);
permitted interpretation is controlled by the wiki evidence ledger and claim
registry. [`SOURCE.toml`](SOURCE.toml) registers the current canonical source
hash and its license-notice-only transition from the benchmark execution
source.

## Known limitations

1. The target is a training-derived pseudo-label from one market dataset.
2. Benchmark v1 is descriptive and prespecified no pairwise inferential test.
3. KAIROS did not lead the primary metric: its observed mean balanced accuracy
   was lower than GRU's.
4. The benchmark supports no causal-effect, external early-warning,
   cross-domain, or physical-validation claim.
5. Market-data acquisition provenance and redistribution permission are not
   closed; public distributions exclude CSV bytes.
6. Focused numerical tests for transition semantics, stochastic TIP inference,
   pseudo-label behavior, and loss terms remain incomplete.
7. The final conference artifact is immutable historical provenance; its
   claims are not current evidence.

See the complete [project limitations](wiki/LIMITATIONS.md).

## License

Original KAIROS software is licensed under
[`AGPL-3.0-or-later`](LICENSE). [`LICENSE_SCOPE.md`](LICENSE_SCOPE.md) and
[`NOTICE`](NOTICE) define the grant and exclusions. Datasets, manuscript text,
PDFs, figures, conference materials, archives, and third-party content do not
automatically inherit the root software license; their own notices and upstream
terms control. The project owner confirms that all named authors approved
repository distribution of the final conference PDF and the identified
reconstruction source and figures as provided; this closes only the
author-consent gate and does not alter any third-party terms.
See [`paper/RIGHTS.md`](paper/RIGHTS.md) and
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
