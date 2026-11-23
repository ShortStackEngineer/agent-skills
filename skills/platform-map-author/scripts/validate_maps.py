#!/usr/bin/env python3
"""Deterministic validator for one-file-per-entity platform map YAML files.

Validates ONLY the thin invariant kernel (IDs, required governance fields,
freshness, valid map_role/relations, and referential integrity across files).
Leaves `extensions:` completely freeform so teams can model in DDD or any
other vocabulary without schema friction.

Zero required external dependencies (uses PyYAML if installed for full syntax
checking, and falls back seamlessly to a pure Python 3 stdlib kernel parser).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

VALID_MAP_ROLES = {"boundary", "ownership", "data"}
VALID_RELATIONS = {
    "belongs_to",
    "contains",
    "owns",
    "depends_on",
    "integrates_with",
    "produces",
    "consumes",
    "produced_by",
    "consumed_by",
    "maps_to",
}
REQUIRED_TOP_KEYS = (
    "schema_version",
    "vocabulary_profile",
    "map_role",
    "id",
    "name",
    "native_kind",
)
MAP_SUBDIRS = ("boundaries", "domains", "data")
PLACEHOLDER_RE = re.compile(r"(<[^>\n]+>|\bTBD\b|\bYYYY-MM-DD\b)", re.IGNORECASE)


def _strip_quotes(val: str) -> str:
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        return val[1:-1]
    return val


def _strip_inline_comment(val: str) -> str:
    in_single = False
    in_double = False
    for idx, ch in enumerate(val):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if idx == 0 or val[idx - 1].isspace():
                return val[:idx].strip()
    return val.strip()


def parse_map_yaml(path: Path) -> tuple[dict[str, object], list[str]]:
    """Parse invariant kernel fields; treat `extensions:` as freeform."""
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            return {}, ["Top-level YAML document must be a mapping"]
        return loaded, []
    except ImportError:
        pass
    except Exception as exc:  # pragma: no cover
        return {}, [f"YAML syntax error: {exc}"]

    # Pure-stdlib kernel parser (ignores freeform `extensions:` subtree)
    data: dict[str, object] = {}
    section: str | None = None
    current_rel: dict[str, str] | None = None

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            errors.append(f"Line {lineno}: tabs are not valid indentation in YAML")
            continue
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if indent == 0:
            current_rel = None
            if ":" not in stripped:
                errors.append(f"Line {lineno}: expected 'key: value'")
                continue
            key, rest = stripped.split(":", 1)
            key = key.strip()
            val = _strip_quotes(_strip_inline_comment(rest))
            if key == "extensions":
                section = "extensions"
                data["extensions"] = {}
            elif key == "governance":
                section = "governance"
                data["governance"] = {}
            elif key == "relationships":
                section = "relationships"
                data["relationships"] = []
            elif key == "repos":
                section = "repos"
                data["repos"] = []
            else:
                section = None
                data[key] = val
            continue

        if section == "extensions":
            continue

        if section == "governance" and isinstance(data.get("governance"), dict):
            if ":" in stripped:
                k, r = stripped.split(":", 1)
                data["governance"][k.strip()] = _strip_quotes(_strip_inline_comment(r))
        elif section == "repos" and isinstance(data.get("repos"), list):
            if stripped.startswith("- "):
                data["repos"].append(_strip_quotes(_strip_inline_comment(stripped[2:])))
        elif section == "relationships" and isinstance(data.get("relationships"), list):
            if stripped.startswith("- "):
                current_rel = {}
                data["relationships"].append(current_rel)
                item_part = stripped[2:].strip()
                if ":" in item_part:
                    k, r = item_part.split(":", 1)
                    current_rel[k.strip()] = _strip_quotes(_strip_inline_comment(r))
            elif current_rel is not None and ":" in stripped:
                k, r = stripped.split(":", 1)
                current_rel[k.strip()] = _strip_quotes(_strip_inline_comment(r))

    return data, errors


def is_placeholder(val: object) -> bool:
    if val is None:
        return True
    s = str(val).strip()
    return not s or bool(PLACEHOLDER_RE.search(s))


def discover_map_files(maps_dir: Path) -> list[Path]:
    files: list[Path] = []
    for sub in MAP_SUBDIRS:
        sub_path = maps_dir / sub
        if sub_path.is_dir():
            files.extend(sorted(sub_path.glob("*.yaml")))
            files.extend(sorted(sub_path.glob("*.yml")))
    return files


def validate_maps(maps_dir: Path, today: dt.date | None = None) -> dict[str, object]:
    today = today or dt.date.today()
    files = discover_map_files(maps_dir)
    if not files:
        return {
            "status": "fail",
            "maps_dir": str(maps_dir),
            "file_count": 0,
            "errors": [f"No map YAML files found under {maps_dir}/{{boundaries,domains,data}}/"],
            "warnings": [],
        }

    parsed: list[tuple[Path, dict[str, object]]] = []
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, Path] = {}

    for path in files:
        rel = str(path.relative_to(maps_dir))
        doc, parse_errs = parse_map_yaml(path)
        for err in parse_errs:
            errors.append(f"{rel}: {err}")
        parsed.append((path, doc))

        for key in REQUIRED_TOP_KEYS:
            if key not in doc or not str(doc.get(key, "")).strip():
                errors.append(f"{rel}: missing required kernel field '{key}'")

        role = str(doc.get("map_role", "")).strip()
        if role and role not in VALID_MAP_ROLES:
            errors.append(f"{rel}: invalid map_role '{role}' (expected one of {sorted(VALID_MAP_ROLES)})")

        entity_id = str(doc.get("id", "")).strip()
        if entity_id:
            if entity_id in seen_ids:
                errors.append(f"{rel}: duplicate id '{entity_id}' (already defined in {seen_ids[entity_id].relative_to(maps_dir)})")
            else:
                seen_ids[entity_id] = path

        gov = doc.get("governance")
        if not isinstance(gov, dict):
            errors.append(f"{rel}: missing required 'governance' block")
        else:
            owner = gov.get("owner")
            if owner is None or not str(owner).strip():
                errors.append(f"{rel}: missing governance.owner")
            elif is_placeholder(owner):
                warnings.append(f"{rel}: governance.owner is unconfirmed ({owner})")

            cadence = 180
            if gov.get("review_cadence_days") is not None and str(gov.get("review_cadence_days")).strip():
                try:
                    cadence = int(str(gov["review_cadence_days"]).strip())
                except ValueError:
                    errors.append(f"{rel}: invalid governance.review_cadence_days ({gov['review_cadence_days']!r})")

            last_rev = gov.get("last_reviewed")
            if is_placeholder(last_rev):
                errors.append(f"{rel}: missing or placeholder governance.last_reviewed")
            else:
                try:
                    rev_date = dt.date.fromisoformat(str(last_rev).strip())
                    age = (today - rev_date).days
                    if age < 0:
                        errors.append(f"{rel}: governance.last_reviewed is in the future ({last_rev})")
                    elif age > cadence:
                        warnings.append(f"{rel}: stale map ({age}d since last_reviewed; cadence {cadence}d)")
                except ValueError:
                    errors.append(f"{rel}: governance.last_reviewed is not ISO YYYY-MM-DD ({last_rev!r})")

    # Second pass: referential integrity & canonical relation checks
    total_edges = 0
    for path, doc in parsed:
        rel = str(path.relative_to(maps_dir))
        rels = doc.get("relationships")
        if rels is None:
            continue
        if not isinstance(rels, list):
            errors.append(f"{rel}: 'relationships' must be a list")
            continue
        for idx, edge in enumerate(rels):
            if not isinstance(edge, dict):
                errors.append(f"{rel}: relationships[{idx}] must be a mapping")
                continue
            total_edges += 1
            target = str(edge.get("target_id", "")).strip()
            relation = str(edge.get("relation", "")).strip()
            if not target:
                errors.append(f"{rel}: relationships[{idx}] missing target_id")
            elif target not in seen_ids:
                errors.append(f"{rel}: dangling target_id '{target}' (no matching map file)")
            if not relation:
                errors.append(f"{rel}: relationships[{idx}] missing canonical relation")
            elif relation not in VALID_RELATIONS:
                errors.append(
                    f"{rel}: invalid canonical relation '{relation}' (expected one of {sorted(VALID_RELATIONS)})"
                )

    status = "fail" if errors else ("warn" if warnings else "pass")
    return {
        "status": status,
        "maps_dir": str(maps_dir),
        "file_count": len(files),
        "entity_ids": sorted(seen_ids.keys()),
        "relationship_count": total_edges,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic validator for one-file-per-entity platform maps."
    )
    parser.add_argument(
        "maps_dir",
        nargs="?",
        default="platform-maps",
        help="Path to platform maps root directory (default: ./platform-maps)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings too")
    args = parser.parse_args()

    result = validate_maps(Path(args.maps_dir))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"Platform Maps Validator [{str(result['status']).upper()}]: "
            f"{result['file_count']} files, {result.get('relationship_count', 0)} edges"
        )
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
