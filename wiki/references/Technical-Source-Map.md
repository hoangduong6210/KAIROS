---
title: Technical Source Map
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Technical Source Map

## Repository source hierarchy

<!-- trace: C-REPO-001 C-IMPL-001 C-EXP-001 C-PAPER-001 C-RESULT-001 E-REPO-001 E-IMPL-001 E-EXP-001 E-PAPER-001 E-LEGACY-ARTIFACTS-001 -->

| Source | Authority |
|---|---|
| `src/kairos/model.py` | Canonical implementation behavior |
| `experiments/` | Active benchmark-v1 runner |
| `datasets/` | Public rights/checksum metadata; staged data bytes remain local |
| `results/historical/legacy-bundle/` | Public checksum inventory plus local-only historical records |
| `paper/snapshots/kairos-conference-final/` | Final conference artifact identity, not current scientific truth |
| `docs/ALGORITHM.md` | Historical technical specification; conflicts with canonical code |
| `docs/reports/` | Local generated explanatory reports, excluded from public Git |
| `archive/` | Local superseded code/workspaces; only boundary README is public |
| `releases/` | Boundary documentation; the prior historical bundle is not distributed |

## External literature status

The historical manuscript bibliography requires a primary-source verification
pass. Citation ownership should be organized by temporal graph learning,
state-space/neuro-symbolic methods, information bottlenecks, causal inference,
early-warning evaluation, market-data provenance, and epidemiology data.

Do not add a citation until authorship, title, venue, year, DOI/URL, and the
specific supported sentence are verified. Placeholder DOI values in preserved
release metadata are not valid references and must not enter a new snapshot.

No external bibliography has completed that verification pass. Consequently no
method novelty, literature-superiority, or attribution statement is currently
paper-eligible.
