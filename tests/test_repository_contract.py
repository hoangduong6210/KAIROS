"""Integrity checks for the restructured KAIROS research repository."""

from __future__ import annotations

import ast
import configparser
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from scripts.audit_wiki import audit as audit_wiki
from scripts.check_public_disclosure import scan as scan_public_disclosure


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
FRONT_MATTER = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
LATEX_FIGURE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
MODEL_LICENSE_HEADER = (
    "# SPDX-FileCopyrightText: 2026 Duong Viet Hoang\n"
    "# SPDX-FileCopyrightText: 2026 Lun-Min Shih\n"
    "# SPDX-FileCopyrightText: 2026 Yi-Hao Lai\n"
    "# SPDX-License-Identifier: AGPL-3.0-or-later\n"
    "#\n"
    "# Modified from the previously distributed KAIROS source.\n"
    "# Modification date: 2026-08-19. See NOTICE for provenance and license scope.\n"
).encode("utf-8")


def _front_matter(path: Path) -> dict[str, str]:
    match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    assert match, f"missing YAML front matter: {path.relative_to(ROOT)}"
    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            assert key not in fields, f"duplicate front-matter key {key}: {path.relative_to(ROOT)}"
            fields[key] = value.strip()
    return fields


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _benchmark_execution_model_bytes() -> bytes:
    current = (ROOT / "src/kairos/model.py").read_bytes()
    shebang, separator, remainder = current.partition(b"\n")
    assert separator == b"\n"
    assert shebang == b"#!/usr/bin/env python3"
    assert remainder.startswith(MODEL_LICENSE_HEADER)
    assert current.count(MODEL_LICENSE_HEADER) == 1
    header_lines = MODEL_LICENSE_HEADER.splitlines()
    assert len(header_lines) == 7
    assert all(line == b"#" or line.startswith(b"# ") for line in header_lines)
    return shebang + separator + remainder[len(MODEL_LICENSE_HEADER) :]


def test_required_repository_layout() -> None:
    required = [
        "LICENSE",
        "LICENSE_SCOPE.md",
        "NOTICE",
        "COPYRIGHT",
        "THIRD_PARTY_NOTICES.md",
        "MANIFEST.in",
        "README.md",
        "PROJECT.toml",
        "SOURCE.toml",
        "pyproject.toml",
        "src/kairos/__init__.py",
        "src/kairos/model.py",
        "src/kairos/NOTICE",
        "experiments",
        "datasets/README.md",
        "datasets/RIGHTS.md",
        "datasets/checksums.sha256",
        "results/CURRENT",
        "results/historical/legacy-bundle/README.md",
        "paper/CURRENT",
        "paper/CONFERENCE_CURRENT",
        "paper/current-state/README.md",
        "paper/RIGHTS.md",
        "paper/snapshots/kairos-conference-final/KAIROS_FINAL.pdf",
        "paper/snapshots/kairos-conference-final/main.tex",
        "paper/snapshots/kairos-conference-final/figures",
        "paper/snapshots/kairos-conference-final/RIGHTS.md",
        "paper/snapshots/kairos-conference-final/artifact.toml",
        "paper/snapshots/kairos-conference-final/checksums.sha256",
        "paper/snapshots/kairos-conference-final/source-checksums.sha256",
        "configs/README.md",
        "protocols/README.md",
        "wiki/START-HERE.md",
        "datasets/RIGHTS.md",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    assert not missing, f"missing required paths: {missing}"


def test_repository_name_and_conference_snapshot_boundary() -> None:
    assert (ROOT / "paper/snapshots/kairos-conference-final").is_dir()
    assert (ROOT / "paper/current-state").is_dir()
    assert (ROOT / "archive/README.md").is_file()
    assert not (ROOT / "paper/conference_snapshot").exists()
    assert not (ROOT / "paper/edition1").exists()
    assert not (ROOT / "paper/figures").exists()


def test_vendor_specific_agent_instructions_are_not_distributed() -> None:
    assert not (ROOT / "CLAUDE.md").exists()
    assert not (ROOT / ".claude").exists()
    assert not list(ROOT.glob("**/CLAUDE.md"))


def test_project_and_release_pointers_agree() -> None:
    project = configparser.ConfigParser()
    project.read(ROOT / "PROJECT.toml", encoding="utf-8")
    results_pointer = (ROOT / "results/CURRENT").read_text(encoding="utf-8").strip()
    paper_pointer = (ROOT / "paper/CURRENT").read_text(encoding="utf-8").strip()
    conference_pointer = (ROOT / "paper/CONFERENCE_CURRENT").read_text(encoding="utf-8").strip()
    assert project["pointers"]["evidence_release"].strip('"') == results_pointer
    assert project["pointers"]["paper_snapshot"].strip('"') == paper_pointer
    assert project["pointers"]["conference_artifact"].strip('"') == conference_pointer
    assert project["canonical"]["implementation"].strip('"') == "src/kairos/model.py"
    assert project["canonical"]["source_manifest"].strip('"') == "SOURCE.toml"
    assert project["canonical"]["paper_working_state"].strip('"') == "paper/current-state"
    assert (ROOT / project["canonical"]["knowledge_map"].strip('"')).is_file()
    conference_path = project["canonical"]["conference_snapshot"].strip('"')
    assert conference_path == f"paper/snapshots/{conference_pointer}"
    assert (ROOT / conference_path).is_dir()
    conference_source = project["canonical"]["conference_reconstruction"].strip('"')
    assert conference_source == f"{conference_path}/main.tex"
    assert (ROOT / conference_source).is_file()
    for pointer in ("status", "claims", "evidence"):
        assert (ROOT / project["pointers"][pointer].strip('"')).is_file()
    evidence_metadata = _front_matter(WIKI / "evidence/Evidence-Ledger.md")
    assert evidence_metadata["evidence_release"] == results_pointer
    if results_pointer != "UNRELEASED":
        assert (ROOT / "results" / "frozen" / results_pointer).is_dir()
    if paper_pointer != "UNRELEASED":
        assert results_pointer != "UNRELEASED"
        snapshot = ROOT / "paper" / "snapshots" / paper_pointer
        assert snapshot.is_dir()
        assert results_pointer in (snapshot / "results.lock.yaml").read_text(encoding="utf-8")


def test_license_and_distribution_boundaries() -> None:
    project = configparser.ConfigParser()
    project.read(ROOT / "PROJECT.toml", encoding="utf-8")
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    scope = (ROOT / "LICENSE_SCOPE.md").read_text(encoding="utf-8")
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    source_notice = (ROOT / "src/kairos/NOTICE").read_text(encoding="utf-8")
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text
    assert project["rights"]["software_license"].strip('"') == "AGPL-3.0-or-later"
    assert 'software_license = "AGPL-3.0-or-later"' in pyproject
    assert "datasets/" in scope and "paper/" in scope and "archive/" in scope
    assert "do not create a current offer" in notice
    assert "MODIFIED-FILE NOTICE" in notice
    assert "`src/kairos/model.py` is a modified version" in notice
    assert "Duong Viet Hoang" in notice
    assert "Lun-Min Shih" in notice
    assert "Yi-Hao Lai" in notice
    assert "seven registered header lines" in notice
    assert "model.py is a modified version" in source_notice
    assert "Copyright (C) 2026 Duong Viet Hoang, Lun-Min Shih, and" in source_notice
    assert "recursive-include src NOTICE" in manifest
    assert "include SOURCE.toml" in manifest
    assert 'kairos = ["NOTICE"]' in pyproject
    for restricted in ("archive", "datasets", "paper", "releases", "results", ".internal"):
        assert f"prune {restricted}" in manifest
    assert "global-exclude *.csv *.pdf" in manifest
    assert "datasets/raw/*.csv" in ignore
    assert "datasets/processed/*.csv" in ignore


def test_canonical_source_notice_transition_is_registered_exactly() -> None:
    project = configparser.ConfigParser()
    project.read(ROOT / "PROJECT.toml", encoding="utf-8")
    source = configparser.ConfigParser()
    source.read(ROOT / "SOURCE.toml", encoding="utf-8")

    model = ROOT / source["canonical"]["path"].strip('"')
    current_bytes = model.read_bytes()
    execution_bytes = _benchmark_execution_model_bytes()
    current_hash = _sha256_bytes(current_bytes)
    execution_hash = _sha256_bytes(execution_bytes)

    assert current_hash == "bd9c108c448ca747ba6031c42251fa9856d00c6da99c9da18ca0a511ee1e3a2f"
    assert execution_hash == "b9dbbcb36bac125a10912b87033ec46814c4b0a2ffe70ef8e55a01f1919d32da"
    assert source["canonical"]["sha256"].strip('"') == current_hash
    assert project["canonical"]["implementation_sha256"].strip('"') == current_hash
    assert source["predecessor"]["sha256"].strip('"') == execution_hash
    assert source["predecessor"]["transition"].strip('"') == "license-notice-only"
    assert source["predecessor"]["removed_line_range_for_verification"].strip('"') == "2-8"
    assert source["verification"].getboolean("frozen_release_mutated") is False
    assert source["verification"].getboolean("benchmark_rerun") is False
    assert source["verification"].getboolean("result_reinterpreted") is False
    assert ast.dump(ast.parse(current_bytes), include_attributes=False) == ast.dump(
        ast.parse(execution_bytes), include_attributes=False
    )


def test_current_state_and_historical_snapshot_prose_agree_with_pointers() -> None:
    results_pointer = (ROOT / "results/CURRENT").read_text(encoding="utf-8").strip()
    results_readme = (ROOT / "results/README.md").read_text(encoding="utf-8")
    paper_readme = (ROOT / "paper/README.md").read_text(encoding="utf-8")
    conference_record = (WIKI / "manuscript/Conference-Artifact-Record.md").read_text(
        encoding="utf-8"
    )

    assert results_pointer in results_readme
    assert results_pointer in paper_readme
    assert results_pointer in conference_record
    assert "paper/current-state/" in conference_record
    assert "Do not modify this snapshot in place" in (
        ROOT / "paper/snapshots/kairos-conference-final/README.md"
    ).read_text(encoding="utf-8")


def test_all_wiki_pages_have_valid_front_matter() -> None:
    allowed_statuses = {
        "canonical",
        "PROPOSED",
        "RUNNING",
        "VALIDATED",
        "ADMITTED",
        "ADMITTED NEGATIVE",
        "REJECTED",
        "BLOCKED",
        "QUARANTINED",
        "SUPERSEDED",
        "ARCHIVED",
    }
    for page in WIKI.rglob("*.md"):
        fields = _front_matter(page)
        assert fields.get("title")
        assert fields.get("status") in allowed_statuses
        assert ("last_updated" in fields) ^ ("date" in fields)
        date.fromisoformat(fields.get("last_updated", fields.get("date", "")))
        assert fields.get("paper_source") in {"true", "false"}
        if fields["paper_source"] == "true":
            assert fields.get("prose_reviewed") == "true"
            assert fields.get("claim_ids")


def test_wiki_index_covers_every_page() -> None:
    index = (WIKI / "INDEX.md").read_text(encoding="utf-8")
    missing = []
    for page in WIKI.rglob("*.md"):
        if page.name == "INDEX.md":
            continue
        relative = page.relative_to(WIKI).as_posix()
        if f"({relative})" not in index:
            missing.append(relative)
    assert not missing, f"wiki pages absent from INDEX.md: {missing}"


def test_wiki_relative_links_resolve() -> None:
    broken: list[str] = []
    for page in WIKI.rglob("*.md"):
        for target in MARKDOWN_LINK.findall(page.read_text(encoding="utf-8")):
            clean = target.split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            if not (page.parent / clean).resolve().exists():
                broken.append(f"{page.relative_to(WIKI)} -> {target}")
    assert not broken, f"broken wiki links: {broken}"


def test_wiki_ai_and_traceability_audit_passes() -> None:
    issues, _stats = audit_wiki()
    assert not issues, "\n".join(
        f"{issue.path}:{issue.line}: {issue.code}: {issue.message}" for issue in issues
    )


def test_public_documents_do_not_expose_operational_material() -> None:
    issues, _stats = scan_public_disclosure()
    assert not issues, "\n".join(
        f"{issue.path}:{issue.location}: {issue.rule}" for issue in issues
    )


def test_claim_evidence_and_dataset_identifiers_resolve() -> None:
    current_claims = (WIKI / "claims/Current-Claim-Language.md").read_text(encoding="utf-8")
    historical_claims = (WIKI / "claims/Historical-Claim-Ledger.md").read_text(encoding="utf-8")
    evidence = (WIKI / "evidence/Evidence-Ledger.md").read_text(encoding="utf-8")
    datasets = (WIKI / "datasets/Dataset-Registry.md").read_text(encoding="utf-8")

    evidence_id_list = re.findall(r"^## (E-[A-Z0-9-]+)$", evidence, re.MULTILINE)
    dataset_id_list = re.findall(r"^## (D-[A-Z0-9-]+)$", datasets, re.MULTILINE)
    current_id_list = re.findall(r"^\| `(C-[A-Z0-9-]+)` \|", current_claims, re.MULTILINE)
    historical_id_list = re.findall(r"^\| `(H-[A-Z0-9-]+)` \|", historical_claims, re.MULTILINE)
    assert len(evidence_id_list) == len(set(evidence_id_list))
    assert len(dataset_id_list) == len(set(dataset_id_list))
    assert len(current_id_list) == len(set(current_id_list))
    assert len(historical_id_list) == len(set(historical_id_list))

    evidence_ids = set(evidence_id_list)
    dataset_ids = set(dataset_id_list)
    current_ids = set(current_id_list)
    historical_ids = set(historical_id_list)

    referenced_evidence = set(re.findall(r"`(E-[A-Z0-9-]+)`", current_claims))
    referenced_datasets = set(re.findall(r"`(D-[A-Z0-9-]+)`", evidence))
    evidence_current_claims = set(re.findall(r"`(C-[A-Z0-9-]+)`", evidence))
    evidence_historical_claims = set(re.findall(r"`(H-[A-Z0-9-]+)`", evidence))

    assert referenced_evidence <= evidence_ids
    assert referenced_datasets <= dataset_ids
    assert evidence_current_claims <= current_ids
    assert evidence_historical_claims <= historical_ids


def test_tracked_artifact_checksums_match() -> None:
    manifests = [
        ROOT / "results/historical/legacy-bundle/checksums.sha256",
        ROOT / "datasets/checksums.sha256",
        ROOT / "paper/snapshots/kairos-conference-final/checksums.sha256",
        ROOT / "paper/snapshots/kairos-conference-final/source-checksums.sha256",
        ROOT / "results/frozen/kairos-benchmark-v1/checksums.sha256",
    ]
    for manifest in manifests:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            expected, filename = line.split(maxsplit=1)
            artifact = manifest.parent / filename
            if manifest.parent in {
                ROOT / "datasets",
                ROOT / "results/historical/legacy-bundle",
            } and not artifact.is_file():
                # Provider-controlled data and quarantined historical outputs
                # are intentionally local-only. Public Git retains identity
                # manifests without redistributing those bytes.
                continue
            assert artifact.is_file(), f"missing tracked artifact: {filename}"
            assert _sha256(artifact) == expected, f"checksum drift: {filename}"


def test_evidence_manifests_cover_their_artifact_sets() -> None:
    legacy = ROOT / "results/historical/legacy-bundle"
    legacy_manifest = {
        line.split(maxsplit=1)[1]
        for line in (legacy / "checksums.sha256").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    legacy_artifacts = {
        path.name for pattern in ("*.json", "*.tex") for path in legacy.glob(pattern)
    }
    assert len(legacy_manifest) == 13
    if legacy_artifacts:
        assert legacy_manifest == legacy_artifacts

    datasets = ROOT / "datasets"
    dataset_manifest = {
        line.split(maxsplit=1)[1]
        for line in (datasets / "checksums.sha256").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    staged_dataset_artifacts = {
        path.relative_to(datasets).as_posix()
        for directory in (datasets / "raw", datasets / "processed")
        for path in directory.glob("*.csv")
    }
    assert dataset_manifest == {
        "raw/raw_prices.csv",
        "processed/pooled_z_scores.csv",
        "processed/z_scores.csv",
    }
    assert staged_dataset_artifacts <= dataset_manifest

    snapshot = ROOT / "paper/snapshots/kairos-conference-final"
    snapshot_manifest = {
        line.split(maxsplit=1)[1]
        for line in (snapshot / "checksums.sha256").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert snapshot_manifest == {"KAIROS_FINAL.pdf"}

    benchmark = ROOT / "results/frozen/kairos-benchmark-v1"
    benchmark_manifest = {
        line.split(maxsplit=1)[1]
        for line in (benchmark / "checksums.sha256").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    benchmark_artifacts = {
        path.name for path in benchmark.iterdir() if path.is_file() and path.name != "checksums.sha256"
    }
    assert benchmark_manifest == benchmark_artifacts


def test_historical_json_artifacts_parse() -> None:
    for artifact in (ROOT / "results/historical/legacy-bundle").glob("*.json"):
        with artifact.open(encoding="utf-8") as stream:
            json.load(stream)


def test_current_evidence_release_is_complete_and_self_consistent() -> None:
    release_dir = ROOT / "results/frozen/kairos-benchmark-v1"
    result = json.loads((release_dir / "result.json").read_text(encoding="utf-8"))
    release = json.loads((release_dir / "release.json").read_text(encoding="utf-8"))
    attempts = result["attempts"]
    declared = {
        (model, seed)
        for model in ("KAIROS", "GRU", "MLP")
        for seed in (42, 123, 456, 789, 1024)
    }

    assert result["status"] == "complete"
    assert result["expected_attempts"] == len(declared)
    assert {(attempt["model"], attempt["seed"]) for attempt in attempts} == declared
    assert all(attempt["status"] == "success" for attempt in attempts)
    assert release["result"]["sha256"] == _sha256(release_dir / "result.json")
    assert release["closure"]["runner"]["sha256"] == _sha256(
        ROOT / release["closure"]["runner"]["path"]
    )
    source = configparser.ConfigParser()
    source.read(ROOT / "SOURCE.toml", encoding="utf-8")
    execution_source_hash = source["predecessor"]["sha256"].strip('"')
    assert release["closure"]["model"]["sha256"] == result["source_sha256"]
    assert release["closure"]["model"]["sha256"] == execution_source_hash
    assert _sha256_bytes(_benchmark_execution_model_bytes()) == execution_source_hash
    assert release["closure"]["config"]["sha256"] == _sha256(
        ROOT / release["closure"]["config"]["path"]
    )
    assert release["closure"]["protocol"]["sha256"] == _sha256(
        ROOT / release["closure"]["protocol"]["path"]
    )
    assert _sha256(release_dir / "result.json") == (
        "4ad144a070cd406e7c92ccd8effe0fb7cb881dc8adbac2a83a9187f0bcd0d1c1"
    )
    assert _sha256(release_dir / "release.json") == (
        "606be33d38e8f10f388555a48e44f0c97506711ce40eb677cc3da2d8da6aaba8"
    )
    assert _sha256(release_dir / "README.md") == (
        "d66f159ff31669de1f85388eea8549e37b2bfc3b68964ca39913f4bb331514cd"
    )
    assert _sha256(release_dir / "checksums.sha256") == (
        "3d7f3454af567d83f86b2f6fed5947325fb42f6d46528c97593e6520067f6db8"
    )
    data_path = ROOT / release["closure"]["data"]["path"]
    if data_path.is_file():
        assert release["closure"]["data"]["sha256"] == _sha256(data_path)
    else:
        dataset_checksums = {
            filename: checksum
            for checksum, filename in (
                line.split(maxsplit=1)
                for line in (ROOT / "datasets/checksums.sha256").read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            )
        }
        assert release["closure"]["data"]["sha256"] == dataset_checksums[
            release["closure"]["data"]["path"].removeprefix("datasets/")
        ]


def test_final_conference_artifact_and_reconstruction_are_separate() -> None:
    snapshot = ROOT / "paper/snapshots/kairos-conference-final"
    assert not (snapshot / "source").exists()
    artifact_metadata = (snapshot / "artifact.toml").read_text(encoding="utf-8")
    assert 'evidence_release = "UNRELEASED"' in artifact_metadata
    assert 'source_status = "normalized-overleaf-reconstruction-included"' in artifact_metadata
    assert 'source_entrypoint = "main.tex"' in artifact_metadata
    assert 'source_build_engine = "pdflatex"' in artifact_metadata
    assert "source_venue_template_included = false" in artifact_metadata
    assert "source_exact_historical_build = false" in artifact_metadata
    assert 'source_expected_pdf_equivalence = "none"' in artifact_metadata
    assert "source_claim_eligible = false" in artifact_metadata
    assert 'source_license = "rights-retained"' in artifact_metadata
    assert "184f40f4e6c4a22555f7ae568bbeb5f7d2105a80e495c71b09bc9e8e90eea9e0" in artifact_metadata
    pdf_manifest_rows = [
        line.split(maxsplit=1)
        for line in (snapshot / "checksums.sha256").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert pdf_manifest_rows == [
        [_sha256(snapshot / "KAIROS_FINAL.pdf"), "KAIROS_FINAL.pdf"]
    ]

    source_manifest = {
        filename: expected
        for expected, filename in (
            line.split(maxsplit=1)
            for line in (snapshot / "source-checksums.sha256").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        )
    }
    figures = {
        path.relative_to(snapshot).as_posix()
        for path in (snapshot / "figures").glob("*.png")
    }
    assert len(figures) == 15
    assert set(source_manifest) == {"main.tex"} | figures
    for filename, expected in source_manifest.items():
        assert _sha256(snapshot / filename) == expected

    source = (snapshot / "main.tex").read_text(encoding="utf-8")
    figure_references = set(LATEX_FIGURE.findall(source))
    assert figure_references == figures
    assert r"\documentclass[11pt]{article}" in source
    assert r"\usepackage[hidelinks]{hyperref}" in source
    assert r"\begin{thebibliography}" in source
    assert not re.search(r"\\(?:input|include)\s*\{", source)
    assert not list(snapshot.glob("*.bib"))
    bibliography_keys = set(
        re.findall(r"\\bibitem(?:\[[^\]]+\])?\{([^}]+)\}", source)
    )
    citation_keys = {
        key.strip()
        for group in re.findall(r"\\cite[a-zA-Z]*\{([^}]+)\}", source)
        for key in group.split(",")
    }
    assert len(bibliography_keys) == 70
    assert citation_keys == bibliography_keys

    snapshot_readme = (snapshot / "README.md").read_text(encoding="utf-8")
    rights = (snapshot / "RIGHTS.md").read_text(encoding="utf-8")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "not the original submitted or camera-ready source package" in snapshot_readme
    assert "Do not modify this snapshot in place" in snapshot_readme
    assert "AGPL-3.0-or-later" in rights
    assert "license does not apply" in rights
    assert "/paper/snapshots/kairos-conference-final/main.pdf" in ignore


def test_public_tree_has_no_removed_venue_year_template_or_branding() -> None:
    markers = (
        "neur" + "ips_2024",
        "neur" + "ips 2024",
        "neur" + "ips v8",
        "neur" + "ips oral",
    )
    roots = ("assets", "configs", "datasets", "docs", "experiments", "paper", "protocols", "releases", "results", "scripts", "src", "tests", "wiki")
    offenders: list[str] = []
    for root_name in roots:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            relative = path.relative_to(ROOT).as_posix().lower()
            if any(marker in relative for marker in markers):
                offenders.append(relative)
                continue
            if not path.is_file() or path.suffix.lower() not in {"", ".in", ".md", ".py", ".rst", ".tex", ".toml", ".txt", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if any(marker in text for marker in markers):
                offenders.append(relative)
    assert not offenders, f"removed venue/year material reintroduced: {sorted(set(offenders))}"


def test_canonical_python_sources_parse() -> None:
    source_roots = [ROOT / "src", ROOT / "experiments", ROOT / "scripts"]
    for source_root in source_roots:
        for source in source_root.rglob("*.py"):
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))


def test_canonical_experiments_do_not_depend_on_archive() -> None:
    for source in (ROOT / "experiments").glob("*.py"):
        text = source.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(source))
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
        )
        assert "cmi_ctgc" not in imported_modules
        assert all(not module.startswith("archive") for module in imported_modules)


def test_active_runners_do_not_overwrite_quarantined_results() -> None:
    writers = [
        ROOT / "experiments/07_confirmatory_benchmark.py",
    ]
    for source in writers:
        text = source.read_text(encoding="utf-8")
        assert 'ROOT / "results"' not in text
        assert 'PROJECT_DIR, "results"' not in text
        assert "os.makedirs('data'" not in text


def test_benchmark_v1_closes_static_comparison_gates() -> None:
    config_path = ROOT / "configs/benchmark-v1.json"
    with config_path.open(encoding="utf-8") as stream:
        config = json.load(stream)
    runner = (ROOT / "experiments/07_confirmatory_benchmark.py").read_text(encoding="utf-8")
    protocol = (ROOT / "protocols/benchmark-v1.md").read_text(encoding="utf-8")

    assert config["training"]["seeds"] == [42, 123, 456, 789, 1024]
    assert config["evaluation"]["models"] == ["KAIROS", "GRU", "MLP"]
    data_path = ROOT / config["study"]["data_file"]
    if data_path.is_file():
        assert _sha256(data_path) == config["study"]["data_sha256"]
    else:
        dataset_manifest = {
            f"datasets/{filename}": checksum
            for checksum, filename in (
                line.split(maxsplit=1)
                for line in (ROOT / "datasets/checksums.sha256").read_text(
                    encoding="utf-8"
                ).splitlines()
                if line.strip()
            )
        }
        assert dataset_manifest[config["study"]["data_file"]] == config["study"]["data_sha256"]
    assert "canonical.SRGNN" in runner
    assert "yfinance" not in runner
    assert "requests" not in runner
    assert "results[" not in runner
    assert "training partition only" in protocol
    assert "Every model/seed pair" in protocol


def test_canonical_model_exposes_expected_components() -> None:
    tree = ast.parse((ROOT / "src/kairos/model.py").read_text(encoding="utf-8"))
    classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    assert {"RSE", "CSMCell", "RMP_TIP", "SCP", "SRGNN"} <= classes
