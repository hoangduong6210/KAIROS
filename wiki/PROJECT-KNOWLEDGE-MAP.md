---
title: Project Knowledge Map
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Project Knowledge Map

This page is the coverage contract between repository state and the living
wiki. A path may store artifacts, but the listed wiki owner controls its current
interpretation. [Trace: `C-REPO-001` → `E-REPO-001`]

## Active and governance surfaces

<!-- trace: C-REPO-001 C-IMPL-001 C-EXP-001 C-DATA-001 E-REPO-001 E-IMPL-001 E-EXP-001 E-DATA-001 -->

| Repository surface | Role | Lifecycle | Wiki owner |
|---|---|---|---|
| `.gitignore` | Generated, cache, mutable-run, and local-data exclusions | Canonical support | [Reproducibility](REPRODUCIBILITY.md) |
| `.dockerignore` | Container-context exclusion of data, archives, generated outputs, and private material | Canonical support | [Reproducibility](REPRODUCIBILITY.md) |
| `.github/` | Public repository integrity workflow | Canonical support | [Research Workflow](operations/Research-Workflow.md) |
| `LICENSE` | Full AGPL software license text | Canonical legal metadata | [License and Data Assets](governance/License-and-Data-Assets.md) |
| `LICENSE_SCOPE.md` | Software-license inclusions and exclusions | Canonical legal metadata | [License and Data Assets](governance/License-and-Data-Assets.md) |
| `NOTICE` | Copyright, historical-release, and no-advice notices | Canonical legal metadata | [License and Data Assets](governance/License-and-Data-Assets.md) |
| `COPYRIGHT` | Current software copyright notice | Canonical legal metadata | [License and Data Assets](governance/License-and-Data-Assets.md) |
| `THIRD_PARTY_NOTICES.md` | External dependency, data, template, and asset boundary | Canonical legal metadata | [License and Data Assets](governance/License-and-Data-Assets.md) |
| `MANIFEST.in` | Source-distribution allowlist and restricted-material exclusions | Canonical support | [License and Data Assets](governance/License-and-Data-Assets.md) |
| `PROJECT.toml` | Project stage and pointers | Canonical | [Project Status](status/Project-Status.md) |
| `SOURCE.toml` | Canonical source hash and notice-only predecessor transition | Canonical evidence metadata | [Evidence Ledger](evidence/Evidence-Ledger.md) |
| `README.md` | Repository navigation | Presentation only | [Wiki Home](README.md) |
| `pyproject.toml` | Python package and test configuration | Canonical support | [Research System Map](architecture/Research-System-Map.md) |
| `requirements/` | Exact benchmark-v1 Python dependency lock | Frozen reproduction support | [Reproducibility](REPRODUCIBILITY.md) |
| `reproducibility/` | Environment lock, digest-pinned container definition, SBOM, and portable scheduler job | Frozen reproduction support | [Reproducibility](REPRODUCIBILITY.md) |
| `src/` | Package source root; `src/kairos/` is the reusable implementation | Active | [RS-GNN and CFI](methods/RS-GNN-and-CFI.md) |
| `experiments/` | Active research entry points | Benchmark v1 active | [Experiment Inventory](experiments/Experiment-Inventory.md) |
| `configs/` | Reviewed experiment configurations | Benchmark v1 frozen | [Evaluation Protocol](methods/Evaluation-Protocol.md) |
| `protocols/` | Confirmatory protocol definitions | Benchmark v1 frozen | [Evaluation Protocol](methods/Evaluation-Protocol.md) |
| `datasets/` | Public rights/checksum metadata plus locally staged legacy data | Quarantined bytes; validated identity | [Dataset Registry](datasets/Dataset-Registry.md) |
| `results/` | Evidence pointer and result lifecycle | Benchmark v1 validated | [Evidence Ledger](evidence/Evidence-Ledger.md) |
| `runs/` | Ignored mutable execution outputs | Ephemeral | [Reproducibility](REPRODUCIBILITY.md) |
| `paper/` | Living manuscript staging plus pointers, canonical conference PDF, and normalized reconstruction | Current state mutable; conference snapshot immutable; current paper unreleased | [Paper Export Contract](manuscript/Paper-Export-Contract.md) |
| `wiki/` | Living scientific interpretation | Canonical | [Wiki Home](README.md) |
| `docs/` | Public technical references and reports | Reference | [Technical Source Map](references/Technical-Source-Map.md) |
| `scripts/` | Repository/reporting validators and utilities | Active support | [Research Workflow](operations/Research-Workflow.md) |
| `tests/` | Repository, evidence, and wiki contracts | Active support | [Traceability Policy](evidence/Traceability-Policy.md) |

## Preserved and external-facing surfaces

<!-- trace: C-REPO-001 C-RESULT-001 C-PAPER-001 E-REPO-001 E-LEGACY-ARTIFACTS-001 E-PAPER-001 -->

| Repository surface | Role | Lifecycle | Wiki owner |
|---|---|---|---|
| `archive/` | Legacy code, paper workspaces, prototypes, and workbenches | Local archive; only boundary README is public | [Historical Artifact Catalog](results/Historical-Artifact-Catalog.md) |
| `releases/` | Historical-release boundary documentation | Public placeholder; prior bundle excluded | [License and Data Assets](governance/License-and-Data-Assets.md) |
| `assets/` | Rights-cleared distributable assets | Policy only | [License and Data Assets](governance/License-and-Data-Assets.md) |

## Coverage rule

Any change that adds a top-level project surface, changes a lifecycle boundary,
or changes an authoritative path must update this map and its semantic owner in
the same change. [Trace: `C-REPO-001` → `E-REPO-001`]
