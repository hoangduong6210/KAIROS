---
title: Project Status
status: VALIDATED
last_updated: 2026-08-19
paper_source: false
---

# Project Status

## Current state

<!-- trace: C-REPO-001 C-PAPER-001 C-RESULT-001 C-PERF-001 C-LEAD-001 C-XDOMAIN-001 C-CAUSAL-001 E-REPO-001 E-BENCH-001 E-PAPER-001 E-LEGACY-ARTIFACTS-001 -->

The repository layout and governance scaffolding are in place. The canonical
implementation is `src/kairos/model.py`; V1/V2 code remains in the local archive,
and the previous public bundle is excluded from the public tree.

The repository root is `KAIROS/`. `KAIROS_FINAL.pdf` is preserved as a
PDF-only artifact at `paper/snapshots/kairos-conference-final/` and is selected
by `paper/CONFERENCE_CURRENT`. Its former venue-specific source/template bundle
was removed from public surfaces on explicit project-owner authorization;
`artifact.toml` records the exception. Superseded drafts, slides, generated
exports, and paper scripts are excluded from the public tree under the archive
boundary.

Legacy code, prototypes, and workbenches are categorized in the local archive.
Public Git retains only archive boundary documentation and the checksum
inventory for local historical outputs.

The wiki now has repository coverage, experiment/artifact inventories,
conference-claim disposition, and claim/evidence traceability.

The current evidence release is `kairos-benchmark-v1`; the current
evidence-locked paper snapshot remains `UNRELEASED`. Benchmark v1 completed all
fifteen declared model/seed attempts without failures. KAIROS's observed mean
balanced accuracy was lower than GRU's and higher than MLP's. Because no
pairwise inferential test was prespecified, the finding is descriptive and does
not establish superiority or non-inferiority. Legacy result bytes remain
quarantined and are not merged into the current release. [Trace: `C-PERF-001`
→ `E-BENCH-001`]

The canonical model now embeds its SPDX, retained copyright, and dated
modification notice. `SOURCE.toml` registers the new canonical hash and proves
that removing exactly the seven header lines reconstructs the benchmark-v1
execution-source hash. The frozen benchmark was not changed or represented as
rerun. [Trace: `C-IMPL-001`, `C-REPO-001` → `E-IMPL-001`, `E-BENCH-001`]

## Remaining publication gates

1. Record the canonical implementation and PDF-only artifact closure in a durable commit.
2. Formally admit `C-PERF-001` before making any benchmark page a paper source.
3. Keep the declared software license separate from unresolved data, template,
   figure, manuscript, and archived-material redistribution rights before any
   new paper-source distribution.
4. Develop manuscript updates in `paper/current-state/` and create a new
   evidence-locked snapshot only when publication is requested.
5. Treat lead-time and cross-domain questions as separate future protocols; the
   current observational design rejects causal-effect wording.

## Next stage

The project is in evidence-release review. Benchmark v1 is technically
validated; publication admission requires the remaining gates above and must
preserve its negative and limited-scope result.
