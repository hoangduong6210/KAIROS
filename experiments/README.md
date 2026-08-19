# Experiments

The active entry point is `07_confirmatory_benchmark.py`. It imports the
canonical KAIROS model, reads the frozen benchmark configuration, verifies the
input checksum, and writes atomic attempt records under `runs/`.

Earlier runners, including the scale and unmatched-seed comparison scripts,
remain under `archive/code/legacy-experiments/`. They are preserved for history
and are not active scientific entry points.
