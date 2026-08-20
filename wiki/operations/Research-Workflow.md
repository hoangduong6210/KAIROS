---
title: Research Workflow
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Research Workflow

1. Define the question, population, estimand, endpoint, and limitations.
2. Freeze data identity, configuration, splits, seeds, comparators, resources, and gates.
3. Review source/protocol hashes before confirmatory execution.
4. Preserve every atomic attempt; retries receive new attempt IDs.
5. Fail finalization on incomplete coverage, duplicates, failures, non-finite values, or drift.
6. Register the finalized immutable release and recomputable checksums.
7. Review exact wording in the claim registry, including negative results.
8. Update the owning method/result page and only then consider paper-source eligibility.
9. Export an immutable paper snapshot locked to claim and evidence IDs.

Exploratory work must remain visibly separate from confirmatory work. Failed and
unfavorable outcomes remain part of the record.

## Wiki co-change matrix

| Changed surface | Required wiki review |
|---|---|
| `src/kairos/` | Method page, implementation claims, evidence source hash, tests |
| `experiments/`, `configs/`, `protocols/` | Experiment inventory, evaluation protocol, reproducibility contract |
| `datasets/` | Dataset registry, target contract, checksums, licensing |
| `requirements/`, `reproducibility/`, scheduler wrappers | Reproducibility contract, environment identity, data boundary |
| `results/`, `runs/` finalization | Evidence ledger, benchmark status, claim registry, project status |
| `paper/` | Conference/paper record, pointer consistency, paper export contract |
| `archive/`, `releases/` | Knowledge map, artifact catalog, rights/provenance review |
| Repository root layout | Project knowledge map, START-HERE, status, contract tests |

Automated checks enforce structural consistency; the reviewer remains
responsible for scientific meaning, disclosure boundaries, and citation
support. [Trace: `C-REPO-001` → `E-REPO-001`]
