#!/usr/bin/env python3
"""Reject operational or machine-private material in public project documents."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    "",
    ".in",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".sbatch",
    ".sh",
    ".tex",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
PUBLIC_ROOTS = (
    ".dockerignore",
    ".github",
    "COPYRIGHT",
    "LICENSE",
    "LICENSE_SCOPE.md",
    "MANIFEST.in",
    "NOTICE",
    "README.md",
    "PROJECT.toml",
    "SOURCE.toml",
    "THIRD_PARTY_NOTICES.md",
    "assets",
    "configs",
    "datasets",
    "docs",
    "experiments",
    "paper",
    "protocols",
    "releases",
    "results",
    "requirements",
    "reproducibility",
    "scripts",
    "src",
    "wiki",
    "pyproject.toml",
)
EXCLUDED_PREFIXES = (
    ".internal/",
    "archive/",
    "results/historical/",
    "runs/",
)
PDF_ROOTS = ("docs", "paper/snapshots", "releases")

FORBIDDEN = {
    "private-machine-path": re.compile(
        r"(?:^|[\s`'\"])/(?:users|home|scratch|gpfs|lustre)/", re.IGNORECASE
    ),
    "private-area-reference": re.compile(r"(?:^|[\s`'\"])(?:\.internal)(?:/|\b)"),
    "private-scheduler-directive": re.compile(
        r"^\s*#SBATCH\s+--(?:account|partition|qos|reservation)(?:=|\s+)\S+",
        re.IGNORECASE,
    ),
    "operational-audit-id": re.compile(r"\b(?:C-WIKI-001|E-WIKI-AUDIT-001)\b"),
    "operational-report-path": re.compile(r"\bdocs/audits/", re.IGNORECASE),
    "host-state-note": re.compile(
        r"\b(?:audit host|current worktree|commit remains pending)\b", re.IGNORECASE
    ),
}


@dataclass(frozen=True)
class DisclosureIssue:
    path: str
    location: str
    rule: str


def _is_excluded(path: Path) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    public_boundary_files = {
        "archive/README.md",
        "results/historical/legacy-bundle/README.md",
    }
    if relative in public_boundary_files:
        return False
    return any(relative == prefix.rstrip("/") or relative.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def iter_public_text() -> Iterable[Path]:
    """Yield text documents that form part of the distributable repository."""
    seen: set[Path] = set()
    for entry in PUBLIC_ROOTS:
        root = ROOT / entry
        candidates = (root,) if root.is_file() else root.rglob("*") if root.is_dir() else ()
        for path in candidates:
            if path == Path(__file__).resolve():
                # This scanner necessarily contains the forbidden expressions
                # as policy definitions; scanning itself would be recursive.
                continue
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and not _is_excluded(path):
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield path


def _scan_text(path: Path, text: str, *, page: int | None = None) -> list[DisclosureIssue]:
    issues: list[DisclosureIssue] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in FORBIDDEN.items():
            if pattern.search(line):
                if rule == "private-area-reference":
                    relative = path.relative_to(ROOT).as_posix()
                    stripped = line.strip()
                    denylist_entry = path.name in {
                        ".dockerignore",
                        ".gitignore",
                        "MANIFEST.in",
                    } and (stripped == ".internal" or stripped.startswith("prune "))
                    audit_exclusion = (
                        relative == "scripts/audit_wiki.py"
                        and '".internal"' in stripped
                    )
                    if denylist_entry or audit_exclusion:
                        # Distribution deny-lists and repository-coverage code
                        # must name the excluded area as policy. Neither case
                        # publishes its contents or an operational path.
                        continue
                location = f"page {page}, line {line_number}" if page is not None else f"line {line_number}"
                issues.append(
                    DisclosureIssue(path.relative_to(ROOT).as_posix(), location, rule)
                )
    return issues


def scan_text_documents() -> tuple[list[DisclosureIssue], int]:
    issues: list[DisclosureIssue] = []
    count = 0
    for path in iter_public_text():
        count += 1
        issues.extend(_scan_text(path, path.read_text(encoding="utf-8", errors="replace")))
    return issues, count


def scan_pdf_documents() -> tuple[list[DisclosureIssue], int]:
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - exercised only by the optional CLI mode
        raise RuntimeError("PDF disclosure scanning requires the project 'paper' dependencies") from exc

    issues: list[DisclosureIssue] = []
    count = 0
    for entry in PDF_ROOTS:
        root = ROOT / entry
        if not root.exists():
            continue
        for path in root.rglob("*.pdf"):
            if _is_excluded(path):
                continue
            count += 1
            with fitz.open(path) as document:
                for page_number, page in enumerate(document, start=1):
                    issues.extend(_scan_text(path, page.get_text(), page=page_number))
    return issues, count


def scan(*, include_pdf: bool = False) -> tuple[list[DisclosureIssue], dict[str, int]]:
    issues, text_count = scan_text_documents()
    pdf_count = 0
    if include_pdf:
        pdf_issues, pdf_count = scan_pdf_documents()
        issues.extend(pdf_issues)
    return issues, {
        "text_documents": text_count,
        "pdf_documents": pdf_count,
        "issues": len(issues),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-pdf", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        issues, stats = scan(include_pdf=args.include_pdf)
    except RuntimeError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps({"stats": stats, "issues": [asdict(issue) for issue in issues]}, indent=2))
    else:
        for issue in issues:
            print(f"{issue.path}:{issue.location}: {issue.rule}")
        print(
            f"public disclosure check: {stats['text_documents']} text documents, "
            f"{stats['pdf_documents']} PDFs, {stats['issues']} issues"
        )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
