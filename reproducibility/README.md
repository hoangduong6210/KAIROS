# Benchmark-v1 reproduction

This directory records the portable execution contract for the frozen
benchmark. It does not make the private input redistributable, and it does not
change the admission status of the frozen result.

## 1. Stage a lawful input copy

Obtain the CSV from a source you are permitted to use, then verify and stage it:

```bash
python scripts/stage_benchmark_input.py /path/to/raw_prices.csv --stage --json
```

The verifier requires the exact size, SHA-256, header, shape, and date bounds in
[`datasets/benchmark-v1-input.json`](../datasets/benchmark-v1-input.json). It
never replaces an existing `datasets/raw/raw_prices.csv`. The dataset bytes are
excluded from Git and from the container build context.

## 2. Recreate the software environment

The reproducibility closure consists of:

- [`environment.lock.json`](environment.lock.json): Python, CUDA, base-image
  digest, and deterministic runtime settings;
- [`benchmark-v1-cu128.lock.txt`](../requirements/benchmark-v1-cu128.lock.txt):
  exact Python package versions, including transitive dependencies;
- [`sbom.cdx.json`](sbom.cdx.json): CycloneDX 1.5 inventory of the base
  container and locked packages;
- [`Dockerfile`](Dockerfile): a digest-pinned Linux/amd64 container definition.

Build the image on a build host or allocated compute node, not on a shared
login node:

```bash
docker build -f reproducibility/Dockerfile -t kairos-benchmark-v1 .
```

The build intentionally contains no input CSV. At runtime, bind a verified
input directory read-only and a separate output directory read-write:

```bash
docker run --rm --gpus all \
  --user "$(id -u):$(id -g)" \
  --volume "$PWD/datasets/raw:/workspace/datasets/raw:ro" \
  --volume "$PWD/runs:/workspace/runs" \
  kairos-benchmark-v1
```

## 3. Run through the scheduler

Do not execute the benchmark on a login node. Submit the portable Slurm job
from the repository root:

```bash
sbatch reproducibility/slurm/benchmark-v1.sbatch
```

The job deliberately declares no site-specific account, partition, module, or
absolute path. Configure those through your site's normal submission options.
If an Apptainer image is available, supply its path at submission time:

```bash
sbatch --export=ALL,KAIROS_APPTAINER_IMAGE=/path/to/kairos-benchmark-v1.sif \
  reproducibility/slurm/benchmark-v1.sbatch
```

Without `KAIROS_APPTAINER_IMAGE`, the job uses the Python environment active in
the allocation and refuses to proceed if it differs from the lock.

Each run writes to a new
`runs/reproductions/benchmark-v1/<run-id>/` directory. Existing run IDs are
never overwritten. `invocation.json` captures hashes for the frozen runner,
configuration, input contract, environment contract, SBOM, and reference
result; `comparison.json` reports a descriptive comparison to the frozen
aggregate.

For a lightweight metadata check that does not run the benchmark:

```bash
bash scripts/run_benchmark_v1.sh --preflight-only --allow-cpu-preflight
```

Exact software and deterministic settings improve repeatability, but cannot
guarantee bit-identical CUDA results across GPU architectures, drivers, and
kernels. A reproduction remains new evidence and does not rewrite the frozen
record.
