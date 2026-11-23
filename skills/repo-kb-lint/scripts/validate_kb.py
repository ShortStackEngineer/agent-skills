#!/usr/bin/env python3
"""Deterministic validator for standardized product README.md knowledge bases.

Zero external dependencies (Python 3 standard library only). Designed to run
identically inside agent skills (`repo-kb-lint`, `repo-kb-author`) and CI.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REQUIRED_FRONTMATTER_KEYS = (
    "kb_schema_version",
    "product_name",
    "maintainer",
    "last_reviewed",
    "review_cadence_days",
    "verified_commit",
)

REQUIRED_SECTIONS = (
    ("product_purpose", r"product\s+purpose"),
    ("supported_business_activities", r"supported\s+business\s+activities"),
    ("system_boundaries", r"system\s+boundaries"),
    ("interfaces", r"interfaces"),
    ("domain_terms", r"domain\s+terms"),
    ("data_responsibilities", r"data\s+responsibilities"),
    ("dependencies", r"dependencies"),
    ("owner_references", r"owner\s+references"),
)

PLACEHOLDER_PATTERNS = (
    re.compile(r"<[^>\n]+>"),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bYYYY-MM-DD\b"),
)


def parse_frontmatter(text: str) -> tuple[dict[str, object], str, list[str]]:
    """Parse simple YAML frontmatter without external YAML dependencies."""
    errors: list[str] = []
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return {}, text, ["Missing YAML frontmatter block at top of README.md"]

    lines = text.splitlines()
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break

    if end_idx is None:
        return {}, text, ["Unclosed YAML frontmatter block (missing closing '---')"]

    data: dict[str, object] = {}
    current_parent: str | None = None
    for raw_line in lines[1:end_idx]:
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if ":" not in raw_line:
            errors.append(f"Invalid frontmatter line: {raw_line.strip()}")
            continue
        key, val = raw_line.split(":", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")

        if indent == 0:
            if val == "":
                data[key] = {}
                current_parent = key
            else:
                data[key] = val
                current_parent = None
        elif current_parent and isinstance(data.get(current_parent), dict):
            data[current_parent][key] = val

    body = "\n".join(lines[end_idx + 1 :])
    return data, body, errors


def is_placeholder(value: object) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    return any(p.search(text) for p in PLACEHOLDER_PATTERNS)


def check_freshness(
    last_reviewed: object, cadence_raw: object, today: dt.date
) -> tuple[str, int | None, list[str]]:
    issues: list[str] = []
    cadence = 180
    try:
        if cadence_raw is not None and str(cadence_raw).strip():
            cadence = int(str(cadence_raw).strip())
    except ValueError:
        issues.append(f"Invalid review_cadence_days value: {cadence_raw!r}")

    if is_placeholder(last_reviewed):
        return "Missing", None, issues + ["last_reviewed date is missing or placeholder"]

    try:
        reviewed_date = dt.date.fromisoformat(str(last_reviewed).strip())
    except ValueError:
        return (
            "Invalid",
            None,
            issues + [f"last_reviewed is not ISO YYYY-MM-DD: {last_reviewed!r}"],
        )

    age_days = (today - reviewed_date).days
    if age_days < 0:
        return "Invalid", age_days, issues + [f"last_reviewed is in the future ({last_reviewed})"]
    if age_days > cadence:
        return (
            "Stale",
            age_days,
            issues + [f"README is stale: {age_days} days since last_reviewed (cadence: {cadence}d)"],
        )
    return "Fresh", age_days, issues


def check_sections(body: str) -> tuple[dict[str, str], bool]:
    headings = re.findall(r"^##\s+(.+)$", body, flags=re.MULTILINE)
    normalized = [h.strip() for h in headings]

    coverage: dict[str, str] = {}
    for key, pattern in REQUIRED_SECTIONS:
        matched = any(re.search(pattern, h, flags=re.IGNORECASE) for h in normalized)
        coverage[key] = "Pass" if matched else "Missing"

    preserved_present = any(
        re.search(r"additional\s+repository\s+documentation", h, flags=re.IGNORECASE)
        for h in normalized
    )
    return coverage, preserved_present


def strip_fenced_code_blocks(body: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", body)


def check_relative_links(body: str, repo_root: Path) -> list[str]:
    broken: list[str] = []
    clean_body = strip_fenced_code_blocks(body)
    for match in re.finditer(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", clean_body):
        target = match.group(1).strip()
        if (
            not target
            or target.startswith(("http://", "https://", "mailto:", "#"))
            or "<" in target
            or ">" in target
        ):
            continue
        path_only = target.split("#", 1)[0].split("?", 1)[0]
        if not path_only:
            continue
        resolved = (repo_root / path_only).resolve()
        if not resolved.exists():
            broken.append(target)
    return sorted(set(broken))


def count_unresolved_markers(body: str) -> int:
    clean_body = strip_fenced_code_blocks(body)
    return len(re.findall(r"\b(?:TBD|Unconfirmed)\b", clean_body, flags=re.IGNORECASE))


def validate_readme(readme_path: Path, today: dt.date | None = None) -> dict[str, object]:
    today = today or dt.date.today()
    repo_root = readme_path.parent.resolve()

    if not readme_path.exists():
        return {
            "status": "fail",
            "readme": str(readme_path),
            "errors": ["README.md not found"],
            "warnings": [],
        }

    text = readme_path.read_text(encoding="utf-8")
    fm, body, fm_errors = parse_frontmatter(text)
    errors: list[str] = list(fm_errors)
    warnings: list[str] = []

    missing_keys = [k for k in REQUIRED_FRONTMATTER_KEYS if k not in fm]
    placeholder_keys = [k for k in REQUIRED_FRONTMATTER_KEYS if k in fm and is_placeholder(fm[k])]
    if missing_keys:
        errors.append(f"Missing frontmatter keys: {', '.join(missing_keys)}")
    if placeholder_keys:
        warnings.append(f"Unconfirmed placeholder frontmatter keys: {', '.join(placeholder_keys)}")

    freshness_status, age_days, freshness_issues = check_freshness(
        fm.get("last_reviewed"), fm.get("review_cadence_days"), today
    )
    if freshness_status in ("Missing", "Invalid"):
        errors.extend(freshness_issues)
    elif freshness_status == "Stale":
        warnings.extend(freshness_issues)

    section_coverage, preserved_present = check_sections(body)
    missing_sections = [k for k, v in section_coverage.items() if v == "Missing"]
    if missing_sections:
        errors.append(f"Missing required sections: {', '.join(missing_sections)}")

    broken_links = check_relative_links(body, repo_root)
    if broken_links:
        errors.append(f"Broken relative links ({len(broken_links)}): {', '.join(broken_links)}")

    unresolved_count = count_unresolved_markers(body)
    if unresolved_count > 0:
        warnings.append(f"Found {unresolved_count} TBD/Unconfirmed marker(s) requiring human review")

    maps = fm.get("authoritative_maps")
    unmapped_refs: list[str] = []
    if isinstance(maps, dict):
        for map_key in ("context_map_ref", "domain_map_ref", "data_map_ref"):
            if is_placeholder(maps.get(map_key)):
                unmapped_refs.append(map_key)
    else:
        unmapped_refs = ["context_map_ref", "domain_map_ref", "data_map_ref"]
    if unmapped_refs:
        warnings.append(f"Unconfirmed authoritative map refs: {', '.join(unmapped_refs)}")

    status = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "status": status,
        "readme": str(readme_path),
        "kb_schema_version": fm.get("kb_schema_version"),
        "product_name": fm.get("product_name"),
        "maintainer": fm.get("maintainer"),
        "verified_commit": fm.get("verified_commit"),
        "last_reviewed": fm.get("last_reviewed"),
        "freshness_status": freshness_status,
        "review_age_days": age_days,
        "preserved_section_present": preserved_present,
        "section_coverage": section_coverage,
        "broken_links": broken_links,
        "unresolved_marker_count": unresolved_count,
        "unmapped_authoritative_refs": unmapped_refs,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic validator for standardized product README.md files."
    )
    parser.add_argument(
        "readme",
        nargs="?",
        default="README.md",
        help="Path to README.md (default: ./README.md)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on warnings (stale dates, TBD markers) as well as errors",
    )
    args = parser.parse_args()

    result = validate_readme(Path(args.readme))

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"README Validator [{str(result['status']).upper()}]: {result['readme']}")
        print(
            f"  Freshness: {result.get('freshness_status')} "
            f"(last_reviewed={result.get('last_reviewed')}, age={result.get('review_age_days')}d)"
        )
        print(f"  Preserved section present: {result.get('preserved_section_present')}")
        if result["errors"]:
            print("  Errors:")
            for err in result["errors"]:
                print(f"    - {err}")
        if result["warnings"]:
            print("  Warnings:")
            for warn in result["warnings"]:
                print(f"    - {warn}")

    if result["status"] == "fail":
        return 1
    if args.strict and result["status"] == "warn":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
