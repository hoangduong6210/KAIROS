# syntax=docker/dockerfile:1
FROM python:3.9.21-slim-bookworm@sha256:0710396c56abc20fb84a6d9f4cc09b59463418ff842d2753f11707f71099c6a0

LABEL org.opencontainers.image.title="KAIROS benchmark-v1 reproduction"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"
LABEL org.opencontainers.image.source="https://github.com/hoangduong6210/KAIROS"
LABEL org.opencontainers.image.description="KAIROS code is AGPL-3.0-or-later; dependencies retain upstream terms"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0 \
    CUBLAS_WORKSPACE_CONFIG=:4096:8 \
    CUDA_DEVICE_ORDER=PCI_BUS_ID \
    MPLCONFIGDIR=/tmp/kairos-matplotlib

WORKDIR /workspace
COPY requirements/benchmark-v1-cu128.lock.txt /opt/kairos/requirements.lock.txt
RUN python -m pip install --no-cache-dir --no-deps -r /opt/kairos/requirements.lock.txt

COPY . /workspace
ENTRYPOINT ["bash", "scripts/run_benchmark_v1.sh"]
