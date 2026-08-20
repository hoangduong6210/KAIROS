"""Fail-closed contracts for the public benchmark-v1 reproduction package."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts import stage_benchmark_input as staging
from scripts import verify_reproduction_environment as environment_verifier


ROOT = Path(__file__).resolve().parents[1]


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _locked_packages() -> dict[str, str]:
    lock = ROOT / "requirements/benchmark-v1-cu128.lock.txt"
    packages: dict[str, str] = {}
    for line in lock.read_text(encoding="utf-8").splitlines():
        row = line.strip()
        if not row or row.startswith(("#", "--")):
            continue
        name, separator, version = row.partition("==")
        assert separator and name and version, f"invalid dependency row: {row}"
        normalized = name.casefold().replace("_", "-")
        assert normalized not in packages, f"duplicate dependency: {normalized}"
        packages[normalized] = version
    return packages


def test_input_manifest_matches_config_release_and_public_rights_boundary() -> None:
    manifest = json.loads(
        (ROOT / "datasets/benchmark-v1-input.json").read_text(encoding="utf-8")
    )
    config = json.loads((ROOT / "configs/benchmark-v1.json").read_text(encoding="utf-8"))
    release = json.loads(
        (ROOT / "results/frozen/kairos-benchmark-v1/release.json").read_text(
            encoding="utf-8"
        )
    )
    result = json.loads(
        (ROOT / "results/frozen/kairos-benchmark-v1/result.json").read_text(
            encoding="utf-8"
        )
    )
    artifact = manifest["artifact"]

    assert manifest["distribution"] == {
        "bytes_included": False,
        "redistribution_grant": False,
        "staging_responsibility": "user-supplied-lawful-copy",
    }
    assert artifact["canonical_path"] == config["study"]["data_file"]
    assert artifact["sha256"] == config["study"]["data_sha256"]
    assert artifact["sha256"] == release["closure"]["data"]["sha256"]
    assert artifact["sha256"] == result["dataset"]["data_sha256"]
    assert artifact["row_count"] == result["dataset"]["rows"]
    assert artifact["data_column_count"] == result["dataset"]["columns"]
    assert artifact["date_start"] == result["dataset"]["date_start"]
    assert artifact["date_end"] == result["dataset"]["date_end"]

    tracked_csv = subprocess.run(
        ["git", "ls-files", "*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert tracked_csv == []


def test_stager_verifies_then_publishes_atomically_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"Date,A,B\n2014-01-01,1,2\n2014-01-02,3,4\n"
    source = tmp_path / "lawful-copy.csv"
    source.write_bytes(payload)
    manifest = {
        "schema_version": "1.0",
        "dataset_id": "D-TEST-001",
        "benchmark_id": "test",
        "artifact": {
            "canonical_path": "datasets/raw/input.csv",
            "sha256": _sha256_bytes(payload),
            "size_bytes": len(payload),
            "header_sha256": _sha256_bytes(b"Date,A,B\n"),
            "row_count": 2,
            "data_column_count": 2,
            "index_column": "Date",
            "date_start": "2014-01-01",
            "date_end": "2014-01-02",
        },
    }
    repository = tmp_path / "repository"
    repository.mkdir()
    monkeypatch.setattr(staging, "ROOT", repository)

    destination, report, action = staging.stage(source, manifest)
    assert action == "staged"
    assert report.status == "verified"
    assert destination.read_bytes() == payload
    assert not list(destination.parent.glob("*.partial"))

    source.write_bytes(payload.replace(b"3,4", b"9,9"))
    with pytest.raises(staging.InputContractError, match="sha256 mismatch"):
        staging.stage(source, manifest)
    assert destination.read_bytes() == payload

    unsafe = {**manifest, "artifact": {**manifest["artifact"], "canonical_path": "../escape.csv"}}
    with pytest.raises(staging.InputContractError, match="repository-relative"):
        staging._canonical_destination(unsafe)


def test_dependency_lock_container_and_sbom_form_one_exact_inventory() -> None:
    packages = _locked_packages()
    assert len(packages) == 49
    assert packages["torch"] == "2.8.0+cu128"
    assert packages["numpy"] == "2.0.2"
    assert packages["pandas"] == "2.3.3"

    sbom = json.loads(
        (ROOT / "reproducibility/sbom.cdx.json").read_text(encoding="utf-8")
    )
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    sbom_packages = {
        component["name"].casefold().replace("_", "-"): component["version"]
        for component in sbom["components"]
        if component["type"] == "library"
    }
    assert sbom_packages == packages

    environment = json.loads(
        (ROOT / "reproducibility/environment.lock.json").read_text(encoding="utf-8")
    )
    base_digest = environment["reproduction_environment"]["base_image_digest"]
    dockerfile = (ROOT / "reproducibility/Dockerfile").read_text(encoding="utf-8")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    assert f"@{base_digest}" in dockerfile
    assert "requirements/benchmark-v1-cu128.lock.txt" in dockerfile
    assert "PYTHONHASHSEED=0" in dockerfile
    assert "CUBLAS_WORKSPACE_CONFIG=:4096:8" in dockerfile
    assert "datasets/raw" in dockerignore
    assert "datasets/processed" in dockerignore
    assert "*.csv" in dockerignore


def test_environment_verifier_fails_if_any_locked_distribution_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_version = environment_verifier.metadata.version

    def version_with_missing_distribution(name: str) -> str:
        if name == "charset-normalizer":
            raise environment_verifier.metadata.PackageNotFoundError(name)
        return real_version(name)

    monkeypatch.setattr(environment_verifier.metadata, "version", version_with_missing_distribution)
    with pytest.raises(
        environment_verifier.EnvironmentContractError,
        match=r"charset-normalizer: missing \(expected 3\.4\.4\)",
    ):
        environment_verifier.verify(require_cuda=False)


def test_public_slurm_job_is_deterministic_portable_and_non_overwriting() -> None:
    job = (ROOT / "reproducibility/slurm/benchmark-v1.sbatch").read_text(
        encoding="utf-8"
    )
    wrapper = (ROOT / "scripts/reproduce_benchmark_v1.py").read_text(
        encoding="utf-8"
    )

    assert "#SBATCH --gpus=1" in job
    assert "export PYTHONHASHSEED=0" in job
    assert "export CUBLAS_WORKSPACE_CONFIG=:4096:8" in job
    assert "SLURM_SUBMIT_DIR" in job
    assert "KAIROS_PROJECT_ROOT" in job
    assert "scripts/run_benchmark_v1.sh" in job
    assert "KAIROS_APPTAINER_IMAGE" in job
    assert not any(
        directive in job.casefold()
        for directive in ("#SBATCH --account", "#SBATCH --partition", "#SBATCH --qos", "#SBATCH --reservation")
    )
    assert not any(path in job for path in ("/users/", "/home/", "/scratch/"))
    assert "mkdir(parents=True, exist_ok=False)" in wrapper
    assert 'ROOT / "results/frozen/kairos-benchmark-v1/result.json"' in wrapper
    assert "_atomic_json(output_dir / \"result.json\", result)" in wrapper
