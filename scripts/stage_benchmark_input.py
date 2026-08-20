#!/usr/bin/env python3
"""Verify, and optionally stage, a lawful local copy of benchmark-v1 input."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "datasets/benchmark-v1-input.json"


class InputContractError(ValueError):
    """Raised when an input or manifest violates the staging contract."""


@dataclass(frozen=True)
class VerificationReport:
    dataset_id: str
    benchmark_id: str
    status: str
    sha256: str
    size_bytes: int
    row_count: int
    data_column_count: int
    date_start: str
    date_end: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputContractError(f"cannot read input manifest: {exc}") from exc

    if manifest.get("schema_version") != "1.0":
        raise InputContractError("unsupported input-manifest schema_version")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        raise InputContractError("input manifest is missing artifact metadata")
    required = {
        "canonical_path",
        "sha256",
        "size_bytes",
        "header_sha256",
        "row_count",
        "data_column_count",
        "index_column",
        "date_start",
        "date_end",
    }
    missing = sorted(required - artifact.keys())
    if missing:
        raise InputContractError(f"input manifest is missing fields: {missing}")
    return manifest


def _canonical_destination(manifest: dict[str, Any]) -> Path:
    relative = Path(str(manifest["artifact"]["canonical_path"]))
    if relative.is_absolute() or ".." in relative.parts:
        raise InputContractError("canonical_path must be repository-relative")
    destination = (ROOT / relative).resolve()
    try:
        destination.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise InputContractError("canonical_path escapes the repository") from exc
    return destination


def verify(path: Path, manifest: dict[str, Any]) -> VerificationReport:
    """Validate byte identity and the minimal public CSV schema contract."""
    artifact = manifest["artifact"]
    if not path.is_file():
        raise InputContractError("benchmark input is not a regular file")
    observed_size = path.stat().st_size
    if observed_size != int(artifact["size_bytes"]):
        raise InputContractError(
            f"size mismatch: expected {artifact['size_bytes']}, observed {observed_size}"
        )
    observed_hash = _sha256(path)
    if observed_hash != artifact["sha256"]:
        raise InputContractError(
            f"sha256 mismatch: expected {artifact['sha256']}, observed {observed_hash}"
        )

    with path.open("rb") as stream:
        header_bytes = stream.readline()
    if hashlib.sha256(header_bytes).hexdigest() != artifact["header_sha256"]:
        raise InputContractError("CSV header checksum mismatch")

    row_count = 0
    first_date: str | None = None
    last_date: str | None = None
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise InputContractError("benchmark input is empty") from exc
        if not header or header[0] != artifact["index_column"]:
            raise InputContractError("unexpected CSV index column")
        if len(header) - 1 != int(artifact["data_column_count"]):
            raise InputContractError("unexpected CSV data-column count")
        for row in reader:
            if len(row) != len(header):
                raise InputContractError(f"row {row_count + 2} has the wrong width")
            if row_count == 0:
                first_date = row[0]
            last_date = row[0]
            row_count += 1

    if row_count != int(artifact["row_count"]):
        raise InputContractError(
            f"row-count mismatch: expected {artifact['row_count']}, observed {row_count}"
        )
    if first_date != artifact["date_start"] or last_date != artifact["date_end"]:
        raise InputContractError("CSV date boundary mismatch")
    return VerificationReport(
        dataset_id=str(manifest["dataset_id"]),
        benchmark_id=str(manifest["benchmark_id"]),
        status="verified",
        sha256=observed_hash,
        size_bytes=observed_size,
        row_count=row_count,
        data_column_count=len(header) - 1,
        date_start=first_date or "",
        date_end=last_date or "",
    )


def stage(source: Path, manifest: dict[str, Any]) -> tuple[Path, VerificationReport, str]:
    """Atomically stage a verified source without replacing the destination."""
    source_report = verify(source, manifest)
    destination = _canonical_destination(manifest)
    if source.resolve() == destination:
        return destination, source_report, "already-staged"
    if destination.exists():
        destination_report = verify(destination, manifest)
        return destination, destination_report, "already-staged"

    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".partial",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as output_stream, source.open("rb") as input_stream:
            shutil.copyfileobj(input_stream, output_stream, length=1024 * 1024)
            output_stream.flush()
            os.fsync(output_stream.fileno())
        staged_report = verify(temporary, manifest)
        try:
            # A same-filesystem hard link publishes the fully verified bytes in
            # one operation and fails rather than replacing an existing path.
            os.link(temporary, destination)
        except FileExistsError:
            destination_report = verify(destination, manifest)
            return destination, destination_report, "already-staged"
    finally:
        temporary.unlink(missing_ok=True)
    return destination, staged_report, "staged"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="lawfully obtained CSV to verify; defaults to the canonical staged path",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--stage",
        action="store_true",
        help="copy a verified external input to the canonical path; never overwrite",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
        manifest = _load_manifest(manifest_path)
        source = args.input or _canonical_destination(manifest)
        if args.stage:
            if args.input is None:
                raise InputContractError("--stage requires an explicit source path")
            destination, report, action = stage(source, manifest)
            payload = {
                **asdict(report),
                "action": action,
                "destination": destination.relative_to(ROOT).as_posix(),
            }
        else:
            report = verify(source, manifest)
            payload = {**asdict(report), "action": "verified"}
    except (InputContractError, OSError) as exc:
        print(f"benchmark input verification failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"benchmark input {payload['action']}: {payload['sha256']} "
            f"({payload['row_count']} rows, {payload['data_column_count']} data columns)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
