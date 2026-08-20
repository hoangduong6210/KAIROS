#!/usr/bin/env python3
"""Verify the benchmark-v1 Python/CUDA environment against the public lock."""

from __future__ import annotations

import argparse
import importlib
from importlib import metadata
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "reproducibility/environment.lock.json"
class EnvironmentContractError(RuntimeError):
    """Raised when the active environment differs from the declared lock."""


def _read_package_lock(path: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "--")):
            continue
        name, separator, version = stripped.partition("==")
        if not separator or not name or not version:
            raise EnvironmentContractError(f"invalid dependency-lock row: {line}")
        versions[name.lower()] = version
    return versions


def verify(lock_path: Path = DEFAULT_LOCK, *, require_cuda: bool = True) -> dict[str, Any]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "1.0":
        raise EnvironmentContractError("unsupported environment-lock schema")
    reproduction = lock["reproduction_environment"]
    expected_python = str(reproduction["python"])
    observed_python = ".".join(str(value) for value in sys.version_info[:3])
    if observed_python != expected_python:
        raise EnvironmentContractError(
            f"Python mismatch: expected {expected_python}, observed {observed_python}"
        )

    dependency_path = ROOT / str(reproduction["dependency_lock"])
    package_lock = _read_package_lock(dependency_path)
    observed: dict[str, str] = {}
    package_drift: list[str] = []
    for distribution, expected in sorted(package_lock.items()):
        if distribution == "torch":
            # PyTorch's import version carries the CUDA local-version suffix;
            # some site package metadata normalizes it away.
            continue
        try:
            version = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            package_drift.append(f"{distribution}: missing (expected {expected})")
            continue
        observed[distribution] = version
        if version != expected:
            package_drift.append(
                f"{distribution}: observed {version}, expected {expected}"
            )
    if package_drift:
        raise EnvironmentContractError(
            "dependency lock mismatch: " + "; ".join(package_drift)
        )

    torch = importlib.import_module("torch")
    torch_version = str(torch.__version__)
    observed["torch"] = torch_version
    if torch_version != package_lock["torch"]:
        raise EnvironmentContractError(
            f"torch mismatch: expected {package_lock['torch']}, observed {torch_version}"
        )
    expected_cuda = str(lock["historical_execution"]["cuda_runtime_reported_by_torch"])
    observed_cuda = str(torch.version.cuda)
    if observed_cuda != expected_cuda:
        raise EnvironmentContractError(
            f"CUDA runtime mismatch: expected {expected_cuda}, observed {observed_cuda}"
        )
    if require_cuda and not torch.cuda.is_available():
        raise EnvironmentContractError("CUDA is not available to PyTorch")

    for name, expected in lock["determinism"].items():
        if expected == "scheduler-cpu-count":
            continue
        observed_value = os.environ.get(name)
        if observed_value != expected:
            raise EnvironmentContractError(
                f"{name} mismatch: expected {expected!r}, observed {observed_value!r}"
            )
    return {
        "status": "verified",
        "python": observed_python,
        "packages": observed,
        "cuda_runtime_reported_by_torch": observed_cuda,
        "cuda_available": bool(torch.cuda.is_available()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--allow-cpu", action="store_true")
    args = parser.parse_args()
    lock_path = args.lock if args.lock.is_absolute() else ROOT / args.lock
    try:
        report = verify(lock_path, require_cuda=not args.allow_cpu)
    except (EnvironmentContractError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"environment verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
