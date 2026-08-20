#!/usr/bin/env python3
"""Audit claim-disposition coverage for the quarantined conference source.

The reconstruction is historical material, not current scientific evidence.
This audit intentionally extracts a superset of claim-bearing material: every
caption, table, theorem-like environment, algorithm, and substantive or short
claim-bearing prose block outside those structures.  Each extracted unit must have an exact,
hash-bound disposition in ``claim-disposition.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "paper/snapshots/kairos-conference-final"
SOURCE = SNAPSHOT / "main.tex"
MANIFEST = SNAPSHOT / "claim-disposition.json"

EXCLUDED_PROSE_ENVIRONMENTS = (
    "figure",
    "figure*",
    "table",
    "table*",
    "algorithm",
    "theorem",
    "proposition",
    "corollary",
    "lemma",
    "definition",
    "remark",
    "assumption",
    "equation",
    "equation*",
    "align",
    "align*",
    "gather",
    "gather*",
    "displaymath",
    "thebibliography",
    "verbatim",
)
THEOREM_ENVIRONMENTS = (
    "theorem",
    "proposition",
    "corollary",
    "lemma",
    "definition",
    "remark",
    "assumption",
)
ALLOWED_DISPOSITIONS = {
    "QUARANTINED_ARTIFACT_ONLY",
    "UNSUPPORTED_QUARANTINED",
}
ALLOWED_HISTORICAL_CLAIMS = {
    "H-PERF-001",
    "H-LEAD-001",
    "H-XDOMAIN-001",
    "H-MODEL-001",
    "H-CAUSAL-001",
}
ALLOWED_EVIDENCE = {"E-PAPER-001", "E-LEGACY-ARTIFACTS-001"}
SHORT_CLAIM_SIGNAL = re.compile(
    r"\b(?:causal|accuracy|performance|predicts?|demonstrates?|proves?|"
    r"validates?|significant|outperforms?|superior|improvement|detects?|"
    r"generalizes?|ensures?|results?|theorem|unique|compliance|lead[- ]?time|"
    r"early warning|reduces?|increases?|underperforms?|correlation|novel|"
    r"contribution)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ClaimUnit:
    unit_id: str
    unit_type: str
    start_line: int
    end_line: int
    sha256: str
    preview: str


@dataclass(frozen=True)
class AuditIssue:
    code: str
    unit_id: str
    message: str


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _preview(text: str, limit: int = 150) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[: limit - 1] + "…"


def _environment_spans(text: str, names: Sequence[str]) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for name in names:
        pattern = re.compile(
            rf"\\begin\{{{re.escape(name)}\}}.*?\\end\{{{re.escape(name)}\}}",
            re.DOTALL,
        )
        spans.extend((match.start(), match.end(), name) for match in pattern.finditer(text))
    return sorted(spans)


def _balanced_command_spans(text: str, command: str) -> list[tuple[int, int]]:
    pattern = re.compile(rf"\\{re.escape(command)}(?:\[[^\]]*\])?\s*\{{")
    spans: list[tuple[int, int]] = []
    for match in pattern.finditer(text):
        depth = 1
        cursor = match.end()
        while cursor < len(text) and depth:
            char = text[cursor]
            escaped = cursor > 0 and text[cursor - 1] == "\\"
            if not escaped:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
            cursor += 1
        if depth:
            raise ValueError(f"unbalanced \\{command} beginning at line {_line_number(text, match.start())}")
        spans.append((match.start(), cursor))
    return spans


def _make_units(text: str, unit_type: str, spans: Iterable[tuple[int, int]]) -> list[ClaimUnit]:
    units: list[ClaimUnit] = []
    for index, (start, end) in enumerate(sorted(spans), start=1):
        payload = text[start:end]
        units.append(
            ClaimUnit(
                unit_id=f"{unit_type.upper()}-{index:03d}",
                unit_type=unit_type,
                start_line=_line_number(text, start),
                end_line=_line_number(text, max(start, end - 1)),
                sha256=_sha256_text(payload),
                preview=_preview(payload),
            )
        )
    return units


def _substantive_prose(text: str) -> bool:
    without_comments = re.sub(r"(?m)^\s*%.*$", " ", text)
    without_commands = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", without_comments)
    without_markup = re.sub(r"[{}$^_~&\\]", " ", without_commands)
    words = re.findall(r"[A-Za-z][A-Za-z'-]+", without_markup)
    has_numeric_claim = len(words) >= 3 and bool(re.search(r"\d", without_markup))
    return len(words) >= 8 or bool(SHORT_CLAIM_SIGNAL.search(without_markup)) or has_numeric_claim


def _prose_spans(text: str, excluded: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    lines = text.splitlines(keepends=True)
    offsets: list[int] = []
    cursor = 0
    for line in lines:
        offsets.append(cursor)
        cursor += len(line)

    def line_excluded(start: int, end: int) -> bool:
        return any(start < blocked_end and end > blocked_start for blocked_start, blocked_end in excluded)

    spans: list[tuple[int, int]] = []
    block_start: int | None = None
    block_end: int | None = None

    def flush() -> None:
        nonlocal block_start, block_end
        if block_start is not None and block_end is not None:
            payload = text[block_start:block_end]
            if _substantive_prose(payload):
                spans.append((block_start, block_end))
        block_start = None
        block_end = None

    structural = re.compile(
        r"^\s*\\(?:begin|end|section|subsection|subsubsection|bibliographystyle|newcommand|newtheorem|label|centering|toprule|midrule|bottomrule|documentclass|usepackage|date|maketitle)\b"
    )
    for index, line in enumerate(lines):
        start = offsets[index]
        end = start + len(line)
        stripped = line.strip()
        if line_excluded(start, end) or not stripped or stripped.startswith("%") or structural.match(line):
            flush()
            continue
        if stripped.startswith(r"\item") or stripped.startswith(r"\paragraph{"):
            flush()
        if block_start is None:
            block_start = start
        block_end = end
    flush()
    return spans


def extract_units(source: Path = SOURCE) -> list[ClaimUnit]:
    text = source.read_text(encoding="utf-8")
    captions = _make_units(text, "caption", _balanced_command_spans(text, "caption"))
    tables = _make_units(
        text,
        "table",
        ((start, end) for start, end, _ in _environment_spans(text, ("table", "table*"))),
    )
    theorems = _make_units(
        text,
        "theorem",
        ((start, end) for start, end, _ in _environment_spans(text, THEOREM_ENVIRONMENTS)),
    )
    algorithms = _make_units(
        text,
        "algorithm",
        ((start, end) for start, end, _ in _environment_spans(text, ("algorithm",))),
    )

    excluded_envs = _environment_spans(text, EXCLUDED_PROSE_ENVIRONMENTS)
    excluded = [(start, end) for start, end, _ in excluded_envs]
    excluded.extend(_balanced_command_spans(text, "caption"))
    prose = _make_units(text, "prose", _prose_spans(text, excluded))

    order = {"caption": 0, "table": 1, "theorem": 2, "algorithm": 3, "prose": 4}
    return sorted(
        captions + tables + theorems + algorithms + prose,
        key=lambda unit: (unit.start_line, order[unit.unit_type], unit.unit_id),
    )


def _load_manifest(path: Path = MANIFEST) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(source: Path = SOURCE, manifest_path: Path = MANIFEST) -> tuple[list[AuditIssue], dict[str, int]]:
    units = extract_units(source)
    manifest = _load_manifest(manifest_path)
    issues: list[AuditIssue] = []

    required_header = {
        "schema_version": 1,
        "source": "paper/snapshots/kairos-conference-final/main.tex",
        "lifecycle": "QUARANTINED",
        "paper_current": False,
        "claim_eligible": False,
    }
    for field, expected in required_header.items():
        if manifest.get(field) != expected:
            issues.append(
                AuditIssue(
                    "header",
                    "MANIFEST",
                    f"{field} must equal {expected!r}",
                )
            )
    if not isinstance(manifest.get("interpretation"), str) or not str(
        manifest.get("interpretation")
    ).strip():
        issues.append(AuditIssue("header", "MANIFEST", "interpretation is required"))

    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if manifest.get("source_sha256") != source_hash:
        issues.append(AuditIssue("source-hash", "MANIFEST", "source_sha256 does not match main.tex"))

    manifest_units = manifest.get("units")
    if not isinstance(manifest_units, list):
        return [AuditIssue("schema", "MANIFEST", "units must be a list")], {"units": len(units), "issues": 1}

    indexed: dict[str, dict[str, object]] = {}
    for raw in manifest_units:
        if not isinstance(raw, dict) or not isinstance(raw.get("unit_id"), str):
            issues.append(AuditIssue("schema", "MANIFEST", "every unit requires a string unit_id"))
            continue
        unit_id = str(raw["unit_id"])
        if unit_id in indexed:
            issues.append(AuditIssue("duplicate", unit_id, "duplicate manifest unit"))
        indexed[unit_id] = raw

    extracted = {unit.unit_id: unit for unit in units}
    for unit_id in sorted(extracted.keys() - indexed.keys()):
        issues.append(AuditIssue("unmapped", unit_id, extracted[unit_id].preview))
    for unit_id in sorted(indexed.keys() - extracted.keys()):
        issues.append(AuditIssue("stale", unit_id, "manifest unit is no longer extracted"))

    for unit_id in sorted(extracted.keys() & indexed.keys()):
        unit = extracted[unit_id]
        entry = indexed[unit_id]
        for field in ("unit_type", "start_line", "end_line", "sha256"):
            if entry.get(field) != getattr(unit, field):
                issues.append(AuditIssue("identity", unit_id, f"{field} does not match source"))
        disposition = entry.get("disposition")
        claim_ids = entry.get("claim_ids")
        evidence_ids = entry.get("evidence_ids")
        if disposition not in ALLOWED_DISPOSITIONS:
            issues.append(AuditIssue("disposition", unit_id, f"invalid disposition: {disposition}"))
        if entry.get("admitted") is not False:
            issues.append(AuditIssue("admission", unit_id, "historical source unit must set admitted=false"))
        if not isinstance(claim_ids, list) or not set(claim_ids).issubset(ALLOWED_HISTORICAL_CLAIMS):
            issues.append(AuditIssue("claim-id", unit_id, f"invalid historical claim IDs: {claim_ids}"))
        if not isinstance(evidence_ids, list) or "E-PAPER-001" not in evidence_ids or not set(evidence_ids).issubset(ALLOWED_EVIDENCE):
            issues.append(AuditIssue("evidence-id", unit_id, f"invalid evidence IDs: {evidence_ids}"))
        if disposition == "QUARANTINED_ARTIFACT_ONLY" and not claim_ids:
            issues.append(AuditIssue("claim-id", unit_id, "artifact-only disposition requires an H-* family"))
        if disposition == "UNSUPPORTED_QUARANTINED" and claim_ids:
            issues.append(AuditIssue("claim-id", unit_id, "unsupported disposition must not imply an H-* admission"))
        if not isinstance(entry.get("reason"), str) or not str(entry.get("reason")).strip():
            issues.append(AuditIssue("reason", unit_id, "non-empty reason is required"))

    expected_counts = manifest.get("expected_counts")
    actual_counts = {
        kind: sum(unit.unit_type == kind for unit in units)
        for kind in ("caption", "table", "theorem", "algorithm", "prose")
    }
    actual_counts["total"] = len(units)
    if expected_counts != actual_counts:
        issues.append(AuditIssue("count", "MANIFEST", f"expected_counts != {actual_counts}"))

    stats = dict(actual_counts)
    stats["mapped"] = len(extracted.keys() & indexed.keys())
    stats["issues"] = len(issues)
    return issues, stats


def inventory() -> dict[str, object]:
    units = extract_units()
    counts = {
        kind: sum(unit.unit_type == kind for unit in units)
        for kind in ("caption", "table", "theorem", "algorithm", "prose")
    }
    counts["total"] = len(units)
    return {
        "schema_version": 1,
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "lifecycle": "QUARANTINED",
        "paper_current": False,
        "claim_eligible": False,
        "extraction_policy": "All captions, tables, theorem-like environments, algorithms, and substantive or short claim-bearing prose blocks outside those structures.",
        "expected_counts": counts,
        "units": [asdict(unit) for unit in units],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-json", action="store_true", help="print extracted units before disposition")
    parser.add_argument("--json", action="store_true", help="print audit result as JSON")
    args = parser.parse_args()

    if args.inventory_json:
        print(json.dumps(inventory(), indent=2, ensure_ascii=False))
        return 0

    issues, stats = audit()
    if args.json:
        print(json.dumps({"stats": stats, "issues": [asdict(issue) for issue in issues]}, indent=2))
    else:
        for issue in issues:
            print(f"{issue.code}: {issue.unit_id}: {issue.message}")
        print(
            "historical paper claim audit: "
            f"{stats['total']} units, {stats['mapped']} mapped, {stats['issues']} issues"
        )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
