---
title: Reproducibility Contract
status: canonical
last_updated: 2026-08-19
paper_source: false
---

# Reproducibility Contract

A claim-bearing run must record the source commit, exact configuration and
environment, immutable data identity and checksums, task/seed coverage, every
failed or excluded attempt, raw and finalized artifact paths, aggregation
procedure, and claim/figure mapping.

Mutable runs must use a new run ID and must never overwrite a frozen release.
Finalization fails closed on missing, duplicate, non-finite, unexpected, or
hash-drifted records. `PROJECT.toml`, `results/CURRENT`, wiki evidence metadata,
`paper/CURRENT`, and the paper results lock must agree.

For benchmark v1, the public reproduction closure is:

<!-- trace: C-EXP-001 C-DATA-002 E-EXP-001 E-DATA-001 E-BENCH-001 -->

- `datasets/benchmark-v1-input.json`, which identifies but does not distribute
  the rights-restricted input bytes;
- `requirements/benchmark-v1-cu128.lock.txt` and
  `reproducibility/environment.lock.json`, which freeze the Python, package,
  CUDA, base-image, and deterministic-runtime identities;
- `reproducibility/Dockerfile` and `reproducibility/sbom.cdx.json`, which bind
  the container base by digest and inventory the 49 locked Python packages;
- `reproducibility/slurm/benchmark-v1.sbatch`, which requests allocated compute,
  sets `PYTHONHASHSEED=0` and `CUBLAS_WORKSPACE_CONFIG=:4096:8`, and writes each
  reproduction to a new run ID.

The public repository cannot supply the raw CSV under the current rights
boundary. A reproducer must lawfully obtain checksum-identical bytes and stage
them with `scripts/stage_benchmark_input.py`. The staging operation verifies
size, checksum, header, shape, and date bounds before atomically publishing a
new local file; it never overwrites an existing path.

Dependency and environment locking improves repeatability but does not imply
bit-identical CUDA behavior across GPU architectures, drivers, or kernels. A
new run is candidate evidence and remains unadmitted until the normal evidence
and claim review completes. [Trace: `C-EXP-001`, `C-DATA-002` → `E-EXP-001`,
`E-DATA-001`, `E-BENCH-001`]
