# Scripts

Repository and reporting utilities belong here. `generate_report_vi.py` writes
local explanatory reports under `docs/reports/`; generated report files are
excluded from public Git and are not evidence authority.

Repository tests invoke the documentation and public-disclosure checks used to
keep maintained pages consistent with project state.

`audit_historical_paper_claims.py` re-extracts claim-bearing units from the
normalized conference source and requires exact, unadmitted dispositions in
its snapshot manifest.

Benchmark reproduction utilities are intentionally split by responsibility:

- `stage_benchmark_input.py` verifies a user-supplied lawful input copy and can
  stage it without overwriting an existing file;
- `verify_reproduction_environment.py` checks Python, every locked package,
  CUDA, and deterministic-runtime identity against the public lock;
- `reproduce_benchmark_v1.py` performs preflight, invokes the frozen runner, and
  writes a new run directory plus provenance and comparison records;
- `run_benchmark_v1.sh` sets deterministic environment variables before
  entering the Python wrapper.

Submit the full workload with
`reproducibility/slurm/benchmark-v1.sbatch`; the login-node-safe preflight is
documented in [`reproducibility/README.md`](../reproducibility/README.md).
