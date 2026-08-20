#!/usr/bin/env python3
"""Run benchmark-v1 into a new, immutable-by-convention reproduction directory."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/benchmark-v1.json"
RUNNER = ROOT / "experiments/07_confirmatory_benchmark.py"
INPUT_MANIFEST = ROOT / "datasets/benchmark-v1-input.json"
ENVIRONMENT_LOCK = ROOT / "reproducibility/environment.lock.json"
SBOM = ROOT / "reproducibility/sbom.cdx.json"
REFERENCE_RESULT = ROOT / "results/frozen/kairos-benchmark-v1/result.json"
RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")

sys.path.insert(0, str(ROOT))
from scripts.stage_benchmark_input import _canonical_destination, _load_manifest, verify as verify_input  # noqa: E402
from scripts.verify_reproduction_environment import verify as verify_environment  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    partial = path.with_suffix(path.suffix + ".partial")
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(partial, path)


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("kairos_frozen_benchmark_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load benchmark runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def _new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def preflight(*, require_cuda: bool) -> dict[str, Any]:
    manifest = _load_manifest(INPUT_MANIFEST)
    input_report = verify_input(_canonical_destination(manifest), manifest)
    environment_report = verify_environment(ENVIRONMENT_LOCK, require_cuda=require_cuda)
    return {
        "status": "verified",
        "input": input_report.__dict__,
        "environment": environment_report,
        "closure": {
            "config_sha256": _sha256(CONFIG),
            "runner_sha256": _sha256(RUNNER),
            "input_manifest_sha256": _sha256(INPUT_MANIFEST),
            "environment_lock_sha256": _sha256(ENVIRONMENT_LOCK),
            "sbom_sha256": _sha256(SBOM),
            "reference_result_sha256": _sha256(REFERENCE_RESULT),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", help="unique output identifier; generated when omitted")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--allow-cpu-preflight",
        action="store_true",
        help="permit a metadata-only preflight without an allocated GPU",
    )
    args = parser.parse_args()
    if args.allow_cpu_preflight and not args.preflight_only:
        parser.error("--allow-cpu-preflight is valid only with --preflight-only")

    try:
        preflight_report = preflight(require_cuda=not args.allow_cpu_preflight)
    except Exception as exc:
        print(f"reproduction preflight failed: {exc}", file=sys.stderr)
        return 1
    if args.preflight_only:
        print(json.dumps(preflight_report, indent=2, sort_keys=True))
        return 0

    run_id = args.run_id or _new_run_id()
    if not RUN_ID.fullmatch(run_id):
        parser.error("run ID must match [A-Za-z0-9][A-Za-z0-9._-]{0,95}")
    output_dir = ROOT / "runs/reproductions/benchmark-v1" / run_id
    try:
        output_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f"refusing to overwrite existing run ID: {run_id}", file=sys.stderr)
        return 1

    invocation = {
        "schema_version": "1.0",
        "benchmark_id": "kairos-benchmark-v1",
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "determinism": {
            name: os.environ.get(name)
            for name in ("PYTHONHASHSEED", "CUBLAS_WORKSPACE_CONFIG", "CUDA_DEVICE_ORDER")
        },
        "preflight": preflight_report,
    }
    _atomic_json(output_dir / "invocation.json", invocation)

    try:
        result = _load_runner().run(CONFIG)
        _atomic_json(output_dir / "result.json", result)
        reference = json.loads(REFERENCE_RESULT.read_text(encoding="utf-8"))
        comparison = {
            "reference_result_sha256": _sha256(REFERENCE_RESULT),
            "reproduction_result_sha256": _sha256(output_dir / "result.json"),
            "status_complete": result.get("status") == "complete",
            "attempt_coverage_match": result.get("expected_attempts")
            == reference.get("expected_attempts"),
            "aggregate_exact_match": result.get("summary") == reference.get("summary"),
            "interpretation": "descriptive comparison only; scientific admission is unchanged",
        }
        _atomic_json(output_dir / "comparison.json", comparison)
    except Exception as exc:
        _atomic_json(
            output_dir / "failure.json",
            {
                "status": "failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
        )
        print(f"reproduction failed; record retained under {output_dir.relative_to(ROOT)}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": result["status"],
                "run_id": run_id,
                "output": output_dir.relative_to(ROOT).as_posix(),
                "aggregate_exact_match": comparison["aggregate_exact_match"],
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
