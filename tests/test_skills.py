"""Zero-dependency test suite for agent-skills packaging and deterministic validators."""

from __future__ import annotations

import datetime as dt
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestSkillPackaging(unittest.TestCase):
    def test_every_skill_has_valid_frontmatter_and_no_parent_traversal(self) -> None:
        skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
        self.assertGreaterEqual(len(skill_dirs), 4)

        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"Missing SKILL.md in {skill_dir.name}")
            text = skill_md.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f"{skill_dir.name}: missing YAML frontmatter")

            end = text.find("\n---\n", 4)
            self.assertGreater(end, 0, f"{skill_dir.name}: unclosed YAML frontmatter")
            fm = text[4:end]

            name_match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", fm, flags=re.MULTILINE)
            self.assertIsNotNone(name_match, f"{skill_dir.name}: invalid or missing 'name:'")
            self.assertEqual(
                name_match.group(1),
                skill_dir.name,
                f"Skill name must match folder name ({skill_dir.name})",
            )
            self.assertRegex(fm, r"(?m)^description:", f"{skill_dir.name}: missing 'description:'")
            self.assertRegex(fm, r'version:\s*"\d+\.\d+\.\d+"', f"{skill_dir.name}: missing SemVer metadata.version")
            self.assertNotIn("../", text, f"{skill_dir.name}: must stay self-contained (no '../' references)")

    def test_shared_files_in_sync(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts/sync_shared.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestValidateKbScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module("validate_kb", REPO_ROOT / "shared/validate_kb.py")

    def test_valid_readme_passes(self) -> None:
        today = dt.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src/service.ts").write_text("export const ok = true;\n")
            readme = root / "README.md"
            readme.write_text(
                f"""---
kb_schema_version: "0.1"
product_name: "Quote Service"
maintainer: "Jane Doe"
last_reviewed: "{today}"
review_cadence_days: 180
verified_commit: "a4f91c"
authoritative_maps:
  context_map_ref: "ctx:quote-retrieval"
  domain_map_ref: "dom:quoting"
  data_map_ref: "data:quote-status"
---

# Quote Service

## 1. Product purpose
Retrieves customer quotes.

## 2. Supported business activities
Quote lookup in [service.ts](src/service.ts).

## 3. System boundaries
In scope: lookup.

## 4. Interfaces
POST /v2/quotes/retrieve

## 5. Domain terms
Active Quote.

## 6. Data responsibilities
Producer of Quote Status.

## 7. Dependencies
Channel Web.

## 8. Owner references
Quote Team.

## Additional repository documentation
### Local setup
Run `npm test`.
""",
                encoding="utf-8",
            )
            res = self.mod.validate_readme(readme)
            self.assertEqual(res["status"], "pass", res)
            self.assertTrue(res["preserved_section_present"])
            self.assertEqual(res["broken_links"], [])

    def test_stale_broken_readme_fails(self) -> None:
        stale = (dt.date.today() - dt.timedelta(days=250)).isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            readme = Path(tmp) / "README.md"
            readme.write_text(
                f"""---
kb_schema_version: "0.1"
product_name: "Quote Service"
maintainer: "TBD"
last_reviewed: "{stale}"
review_cadence_days: 180
verified_commit: "a4f91c"
---

## 1. Product purpose
See [broken](src/missing.ts). Owner is TBD.
""",
                encoding="utf-8",
            )
            res = self.mod.validate_readme(readme)
            self.assertEqual(res["status"], "fail")
            self.assertEqual(res["freshness_status"], "Stale")
            self.assertIn("src/missing.ts", res["broken_links"])
            self.assertEqual(res["unresolved_marker_count"], 1)


class TestValidateMapsScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_module(
            "validate_maps",
            SKILLS_DIR / "platform-map-author/scripts/validate_maps.py",
        )

    def test_cross_vocabulary_valid_maps_pass_with_stdlib_parser(self) -> None:
        today = dt.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "domains").mkdir()
            (root / "boundaries").mkdir()
            (root / "data").mkdir()

            (root / "domains/quoting.yaml").write_text(
                f"""schema_version: "0.1"
vocabulary_profile: "ddd"
map_role: "ownership"
id: "dom:quoting"
name: "Quoting"
native_kind: "Domain"
governance:
  owner: "Quoting Domain Owner"
  last_reviewed: "{today}"
relationships:
  - target_id: "ctx:quote-retrieval"
    relation: "contains"
""",
                encoding="utf-8",
            )
            (root / "boundaries/quote-retrieval.yaml").write_text(
                f"""schema_version: "0.1"
vocabulary_profile: "ddd"
map_role: "boundary"
id: "ctx:quote-retrieval"
name: "Quote Retrieval"
native_kind: "Bounded Context"
governance:
  owner: "Quote PO"
  last_reviewed: "{today}"
relationships:
  - target_id: "dom:quoting"
    relation: "belongs_to"
  - target_id: "data:quote-status"
    relation: "produces"
extensions:
  aggregates:
    - name: "Quote"
      invariants: "Unexpired quotes only"
  domain_events: ["QuoteRetrieved", "QuoteRetrievalFailed"]
""",
                encoding="utf-8",
            )
            (root / "boundaries/channel-web.yaml").write_text(
                f"""schema_version: "0.1"
vocabulary_profile: "product-system"
map_role: "boundary"
id: "sys:channel-web"
name: "Channel Web"
native_kind: "Product"
governance:
  owner: "Channels PO"
  last_reviewed: "{today}"
relationships:
  - target_id: "ctx:quote-retrieval"
    relation: "depends_on"
extensions:
  tier: "tier-1"
""",
                encoding="utf-8",
            )
            (root / "data/quote-status.yaml").write_text(
                f"""schema_version: "0.1"
vocabulary_profile: "ddd"
map_role: "data"
id: "data:quote-status"
name: "Quote Status"
native_kind: "Domain Event"
governance:
  owner: "Quoting Data Owner"
  last_reviewed: "{today}"
relationships:
  - target_id: "ctx:quote-retrieval"
    relation: "produced_by"
""",
                encoding="utf-8",
            )

            orig_yaml = sys.modules.get("yaml")
            sys.modules["yaml"] = None  # force pure-stdlib path
            try:
                res = self.mod.validate_maps(root)
            finally:
                if orig_yaml is None:
                    sys.modules.pop("yaml", None)
                else:
                    sys.modules["yaml"] = orig_yaml

            self.assertEqual(res["status"], "pass", res)
            self.assertEqual(res["file_count"], 4)
            self.assertEqual(res["relationship_count"], 5)

    def test_dangling_target_and_duplicate_id_fail(self) -> None:
        today = dt.date.today().isoformat()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "boundaries").mkdir()
            (root / "boundaries/a.yaml").write_text(
                f"""schema_version: "0.1"
vocabulary_profile: "ddd"
map_role: "boundary"
id: "ctx:dup"
name: "A"
native_kind: "Bounded Context"
governance:
  owner: "TBD"
  last_reviewed: "{today}"
relationships:
  - target_id: "data:missing"
    relation: "produces"
""",
                encoding="utf-8",
            )
            (root / "boundaries/b.yaml").write_text(
                f"""schema_version: "0.1"
vocabulary_profile: "ddd"
map_role: "boundary"
id: "ctx:dup"
name: "B"
native_kind: "Bounded Context"
governance:
  owner: "Owner B"
  last_reviewed: "{today}"
""",
                encoding="utf-8",
            )
            res = self.mod.validate_maps(root)
            self.assertEqual(res["status"], "fail")
            self.assertTrue(any("dangling target_id" in e for e in res["errors"]))
            self.assertTrue(any("duplicate id" in e for e in res["errors"]))
            self.assertTrue(any("unconfirmed" in w for w in res["warnings"]))


if __name__ == "__main__":
    unittest.main()
