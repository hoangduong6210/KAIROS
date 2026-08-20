#!/usr/bin/env bash
#SBATCH --job-name=kairos-benchmark-v1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gpus=1
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=kairos-benchmark-v1-%j.out
#SBATCH --error=kairos-benchmark-v1-%j.err

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -n "${KAIROS_PROJECT_ROOT:-}" ]]; then
    PROJECT_ROOT="$(cd -- "${KAIROS_PROJECT_ROOT}" && pwd)"
elif [[ -n "${SLURM_SUBMIT_DIR:-}" ]]; then
    # Slurm normally executes a spooled copy of this file, so BASH_SOURCE no
    # longer identifies the checkout. The submission directory does.
    PROJECT_ROOT="$(cd -- "${SLURM_SUBMIT_DIR}" && pwd)"
else
    PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
fi
if [[ ! -f "${PROJECT_ROOT}/scripts/run_benchmark_v1.sh" ]]; then
    echo "KAIROS checkout not found; submit from its root or set KAIROS_PROJECT_ROOT." >&2
    exit 2
fi
cd "${PROJECT_ROOT}"

export PYTHONHASHSEED=0
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/kairos-matplotlib-${SLURM_JOB_ID:-manual}"
mkdir -p "${MPLCONFIGDIR}"

JOB_ID="${SLURM_JOB_ID:-manual-$$}"
RUN_ID="${KAIROS_RUN_ID:-slurm-${JOB_ID}}"
if [[ -n "${KAIROS_APPTAINER_IMAGE:-}" ]]; then
    command -v apptainer >/dev/null
    apptainer exec --nv \
        --bind "${PROJECT_ROOT}:${PROJECT_ROOT}" \
        --pwd "${PROJECT_ROOT}" \
        "${KAIROS_APPTAINER_IMAGE}" \
        bash scripts/run_benchmark_v1.sh --run-id "${RUN_ID}"
else
    bash scripts/run_benchmark_v1.sh --run-id "${RUN_ID}"
fi
