# Experiments

The active entry point is `07_confirmatory_benchmark.py`. It imports the
canonical KAIROS model, reads the frozen benchmark configuration, verifies the
input checksum, and writes atomic attempt records under `runs/`.

Earlier runners, including the scale and unmatched-seed comparison scripts,
remain under `archive/code/legacy-experiments/`. They are preserved for history
and are not active scientific entry points.

For a new benchmark-v1 reproduction, do not call the frozen runner directly.
Use `scripts/reproduce_benchmark_v1.py` through the public Slurm definition in
`reproducibility/slurm/benchmark-v1.sbatch`. The wrapper verifies the complete
input/environment closure and guarantees a new, non-overwriting output path;
it does not modify the frozen runner or reference result.
