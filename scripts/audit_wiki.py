#!/usr/bin/env python3
"""Fail-closed structural, traceability, and prose-risk audit for the KAIROS wiki."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
INDEX = WIKI / "INDEX.md"

FRONT_MATTER = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
IDENTIFIER = re.compile(r"\b(?:RQ|C|H|E|D)-[A-Z0-9-]+\b")
TRACE_COMMENT = re.compile(r"<!--\s*trace:\s*(.*?)\s*-->", re.IGNORECASE)
HEADING = re.compile(r"^(#{1,6})\s+")
CODE_SPAN = re.compile(r"`[^`]*`")
HASH = re.compile(r"\b[0-9a-f]{40,64}\b")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
NUMBER = re.compile(r"(?<![A-Za-z])(?:\d+(?:\.\d+)?%?|\d+x\d+)(?![A-Za-z])")

ALLOWED_STATUSES = {
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

REQUIRED_SURFACES = {
    ".gitignore",
    "PROJECT.toml",
    "README.md",
    "pyproject.toml",
    "src/",
    "experiments/",
    "configs/",
    "protocols/",
    "datasets/",
    "results/",
    "runs/",
    "paper/",
    "wiki/",
    "docs/",
    "scripts/",
    "tests/",
    "archive/",
    "releases/",
    "assets/",
}

STALE_ACTIVE_PATHS = {
    "paper/conference_snapshot",
    "archive/legacy-models",
    "archive/legacy-experiments",
    "archive/model-workbench",
    "archive/nscg-prototype",
    "assets/master-files",
    "results/checksums.sha256",
    "results/external-assets.toml",
}

RISKY_PROSE = re.compile(
    r"\b(?:state-of-the-art|groundbreaking|revolutionary|breakthrough|"
    r"game-changing|unprecedented|unique causal|proves?|guarantees?|"
    r"validated early detection|zero architecture changes)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Issue:
    code: str
    path: str
    line: int
    message: str


def _front_matter(path: Path, text: str) -> tuple[dict[str, str], int]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, 0
    fields: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, text[: match.end()].count("\n")


def _without_code_fences(text: str) -> str:
    lines: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def _registered_local_only_paths() -> set[str]:
    """Return artifact paths whose bytes may be absent from public Git."""
    registered: set[str] = set()
    manifests = (
        (ROOT / "datasets/checksums.sha256", "datasets"),
        (ROOT / "results/historical/legacy-bundle/checksums.sha256", "results/historical/legacy-bundle"),
    )
    for manifest, prefix in manifests:
        if not manifest.is_file():
            continue
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                _checksum, filename = line.split(maxsplit=1)
                registered.add(f"{prefix}/{filename}")
    return registered


def _definition_locations(pages: dict[Path, str]) -> dict[str, list[str]]:
    definitions: dict[str, list[str]] = {}
    patterns = (
        re.compile(r"^##\s+((?:E|D|RQ)-[A-Z0-9-]+)\s*$", re.MULTILINE),
        re.compile(r"^\|\s*`((?:C|H)-[A-Z0-9-]+)`\s*\|", re.MULTILINE),
    )
    for path, text in pages.items():
        for pattern in patterns:
            for identifier in pattern.findall(text):
                definitions.setdefault(identifier, []).append(path.relative_to(WIKI).as_posix())
    return definitions


def _trace_ids_by_line(text: str) -> list[set[str]]:
    traces: dict[int, set[str]] = {}
    current_level = 1
    result: list[set[str]] = []
    in_fence = False
    for line in text.splitlines():
        heading = HEADING.match(line)
        if heading and not in_fence:
            current_level = len(heading.group(1))
            for level in list(traces):
                if level >= current_level:
                    del traces[level]
        if line.strip().startswith("```"):
            in_fence = not in_fence
        trace = TRACE_COMMENT.search(line)
        if trace and not in_fence:
            traces[current_level] = set(IDENTIFIER.findall(trace.group(1)))
        active = set().union(*traces.values()) if traces else set()
        active.update(IDENTIFIER.findall(line))
        result.append(active)
    return result


def _has_claim_and_evidence(identifiers: Iterable[str]) -> bool:
    values = set(identifiers)
    return any(item.startswith(("C-", "H-")) for item in values) and any(
        item.startswith("E-") for item in values
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _numeric_payload(line: str) -> str:
    value = CODE_SPAN.sub("", line)
    value = HASH.sub("", value)
    value = ISO_DATE.sub("", value)
    value = IDENTIFIER.sub("", value)
    value = re.sub(r"^\s*\d+[.)]\s+", "", value)
    value = re.sub(r"https?://\S+", "", value)
    return value


def audit() -> tuple[list[Issue], dict[str, int]]:
    issues: list[Issue] = []
    pages = {path: path.read_text(encoding="utf-8") for path in sorted(WIKI.rglob("*.md"))}
    definitions = _definition_locations(pages)
    known_ids = set(definitions)
    index_text = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    numeric_lines = 0
    risky_lines = 0

    registered_local_only = _registered_local_only_paths()
    for identifier, locations in definitions.items():
        if len(locations) > 1:
            issues.append(Issue("duplicate-id", locations[0], 1, f"{identifier}: {locations}"))
        if identifier not in index_text:
            issues.append(Issue("unindexed-id", locations[0], 1, identifier))

    for path, text in pages.items():
        relative = path.relative_to(WIKI).as_posix()
        fields, front_end_line = _front_matter(path, text)
        if not fields:
            issues.append(Issue("front-matter", relative, 1, "missing YAML front matter"))
        else:
            for key in ("title", "status", "paper_source"):
                if not fields.get(key):
                    issues.append(Issue("front-matter", relative, 1, f"missing {key}"))
            if fields.get("status") not in ALLOWED_STATUSES:
                issues.append(Issue("front-matter", relative, 1, f"invalid status {fields.get('status')}"))
            if ("last_updated" in fields) == ("date" in fields):
                issues.append(Issue("front-matter", relative, 1, "require exactly one date field"))
            if fields.get("paper_source") == "true":
                if fields.get("prose_reviewed") != "true" or not fields.get("claim_ids"):
                    issues.append(Issue("paper-source", relative, 1, "missing review or claim_ids"))

        for target in MARKDOWN_LINK.findall(text):
            clean = target.split("#", 1)[0]
            if clean and not clean.startswith(("http://", "https://", "mailto:")):
                if not (path.parent / clean).resolve().exists():
                    issues.append(Issue("broken-link", relative, 1, target))

        for stale in STALE_ACTIVE_PATHS:
            if stale in text:
                line = text[: text.index(stale)].count("\n") + 1
                issues.append(Issue("stale-path", relative, line, stale))

        scan_text = _without_code_fences(text)
        for identifier in IDENTIFIER.findall(scan_text):
            if "EXAMPLE" not in identifier and identifier not in known_ids:
                line = text[: text.find(identifier)].count("\n") + 1
                issues.append(Issue("unknown-id", relative, line, identifier))

        line_traces = _trace_ids_by_line(text)
        in_fence = False
        for number, line in enumerate(text.splitlines(), start=1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or number <= front_end_line or line.lstrip().startswith("#"):
                continue
            trace_ids = line_traces[number - 1]
            payload = _numeric_payload(line)
            if NUMBER.search(payload):
                numeric_lines += 1
                if not _has_claim_and_evidence(trace_ids):
                    issues.append(Issue("untraced-number", relative, number, line.strip()))
            if RISKY_PROSE.search(line):
                risky_lines += 1
                if not _has_claim_and_evidence(trace_ids):
                    issues.append(Issue("risky-prose", relative, number, line.strip()))

        for number, line in enumerate(text.splitlines(), start=1):
            if re.match(r"^\|\s*`(?:C|H)-[A-Z0-9-]+`\s*\|", line):
                if not re.search(r"`E-[A-Z0-9-]+`", line):
                    issues.append(Issue("claim-without-evidence", relative, number, line.strip()))

    for identifier, locations in definitions.items():
        if not identifier.startswith("E-"):
            continue
        ledger = pages[WIKI / "evidence/Evidence-Ledger.md"]
        section_match = re.search(
            rf"^## {re.escape(identifier)}\s*$\n(?P<body>.*?)(?=^## E-|\Z)",
            ledger,
            re.MULTILINE | re.DOTALL,
        )
        if not section_match:
            continue
        body = section_match.group("body")
        required_groups = (
            ("Lifecycle",),
            ("Artifact path", "Artifact paths", "Artifact directory", "Source identity"),
            ("Supported claim", "Supported claims", "Supported current claims"),
            ("Scientific-use boundary",),
        )
        for group in required_groups:
            if not any(token in body for token in group):
                issues.append(Issue("incomplete-evidence", locations[0], 1, f"{identifier}: missing {group}"))

        path_fields = re.findall(
            r"^\|\s*(?:Artifact paths?|Artifact directory|Byte inventory|Manifest|Source identity)\s*\|(?P<value>.*?)\|$",
            body,
            re.MULTILINE,
        )
        for field in path_fields:
            for token in re.findall(r"`([^`]+)`", field):
                if IDENTIFIER.fullmatch(token) or HASH.fullmatch(token):
                    continue
                looks_like_path = "/" in token or token.endswith(
                    (".md", ".py", ".toml", ".yaml", ".json", ".csv", ".sha256", ".pdf")
                )
                if (
                    looks_like_path
                    and not (ROOT / token).exists()
                    and token not in registered_local_only
                ):
                    issues.append(Issue("missing-evidence-artifact", locations[0], 1, f"{identifier}: {token}"))

        identity_fields = re.findall(
            r"^\|\s*(?:Artifact paths?|Source identity)\s*\|(?P<value>.*?)\|$",
            body,
            re.MULTILINE,
        )
        identity_paths = [
            ROOT / token
            for field in identity_fields
            for token in re.findall(r"`([^`]+)`", field)
            if ("/" in token or token.endswith((".py", ".pdf"))) and (ROOT / token).is_file()
        ]
        declared_hashes = re.findall(r"\b[0-9a-f]{64}\b", body)
        if declared_hashes and len(declared_hashes) == len(identity_paths):
            for artifact, expected in zip(identity_paths, declared_hashes):
                if _sha256(artifact) != expected:
                    issues.append(
                        Issue(
                            "evidence-hash-drift",
                            locations[0],
                            1,
                            f"{identifier}: {artifact.relative_to(ROOT)}",
                        )
                    )

    knowledge_map = pages.get(WIKI / "PROJECT-KNOWLEDGE-MAP.md", "")
    actual_surfaces = {
        f"{path.name}/" if path.is_dir() else path.name
        for path in ROOT.iterdir()
        if path.name not in {".git", ".internal", ".pytest_cache"}
    }
    for surface in sorted(REQUIRED_SURFACES | actual_surfaces):
        if f"`{surface}`" not in knowledge_map:
            issues.append(Issue("knowledge-gap", "PROJECT-KNOWLEDGE-MAP.md", 1, surface))

    stats = {
        "pages": len(pages),
        "identifiers": len(known_ids),
        "numeric_lines_checked": numeric_lines,
        "risky_lines_reviewed": risky_lines,
        "issues": len(issues),
    }
    return issues, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args()
    issues, stats = audit()
    if args.json:
        print(json.dumps({"stats": stats, "issues": [issue.__dict__ for issue in issues]}, indent=2))
    else:
        for issue in issues:
            print(f"{issue.path}:{issue.line}: {issue.code}: {issue.message}")
        print(
            "wiki audit: "
            f"{stats['pages']} pages, {stats['identifiers']} identifiers, "
            f"{stats['numeric_lines_checked']} numeric lines, "
            f"{stats['risky_lines_reviewed']} risky-prose lines, "
            f"{stats['issues']} issues"
        )
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
