"""Contracts for the quarantined conference-paper claim inventory."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts/audit_historical_paper_claims.py"
SOURCE = ROOT / "paper/snapshots/kairos-conference-final/main.tex"
MANIFEST = ROOT / "paper/snapshots/kairos-conference-final/claim-disposition.json"

SPEC = importlib.util.spec_from_file_location("historical_claim_audit", AUDIT_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


def test_every_extracted_historical_unit_has_a_quarantined_disposition() -> None:
    issues, stats = AUDIT.audit()

    assert issues == []
    assert stats == {
        "caption": 29,
        "table": 13,
        "theorem": 10,
        "algorithm": 1,
        "prose": 118,
        "total": 171,
        "mapped": 171,
        "issues": 0,
    }

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["lifecycle"] == "QUARANTINED"
    assert manifest["paper_current"] is False
    assert manifest["claim_eligible"] is False
    assert len(manifest["units"]) == stats["total"]
    assert all(entry["admitted"] is False for entry in manifest["units"])
    assert not any(
        claim_id.startswith("C-")
        for entry in manifest["units"]
        for claim_id in entry["claim_ids"]
    )


def test_manifest_covers_every_historical_claim_family() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mapped_claims = {
        claim_id
        for entry in manifest["units"]
        for claim_id in entry["claim_ids"]
    }
    assert mapped_claims == AUDIT.ALLOWED_HISTORICAL_CLAIMS
    assert {entry["disposition"] for entry in manifest["units"]} == {
        "QUARANTINED_ARTIFACT_ONLY",
        "UNSUPPORTED_QUARANTINED",
    }


def test_audit_fails_closed_on_source_or_admission_drift(tmp_path: Path) -> None:
    changed_source = tmp_path / "main.tex"
    changed_source.write_text(
        SOURCE.read_text(encoding="utf-8")
        + "\nA newly inserted unreviewed scientific statement claims broad empirical superiority without evidence.\n",
        encoding="utf-8",
    )
    source_issues, _ = AUDIT.audit(source=changed_source, manifest_path=MANIFEST)
    assert {issue.code for issue in source_issues} >= {"source-hash", "unmapped"}

    changed_manifest = tmp_path / "claim-disposition.json"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["units"][0]["admitted"] = True
    changed_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    admission_issues, _ = AUDIT.audit(source=SOURCE, manifest_path=changed_manifest)
    assert any(issue.code == "admission" for issue in admission_issues)
