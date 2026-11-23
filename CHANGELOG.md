# Changelog

All notable changes to the shared Agent Skills library are documented here.
Skill versions follow [Semantic Versioning](https://semver.org/) so
orchestration audit logs can pin and trace exact skill releases.

## [0.1.0] - 2026-11-23

### Added
- **`repo-kb-lint` (`read-only`):** Deterministic `validate_kb.py` check plus
  semantic drift audit and draft `KnowledgeDebt` reporting for standardized
  product root `README.md` files.
- **`repo-kb-author` (`draft-write`):** Standardized root `README.md`
  bootstrapping, non-destructive revision of existing READMEs (with dedicated
  `## Additional repository documentation` preservation), and PR diff syncing
  without auto-advancing `last_reviewed`.
- **`platform-map-author` (`draft-write`):** Conversational authoring for
  one-file-per-entity authoritative platform maps using a thin invariant kernel
  and freeform `extensions:` (with DDD and Product/System profiles), paired
  with deterministic `validate_maps.py`.
- **Packaging & CI:** `shared/` parity sync script (`scripts/sync_shared.py`),
  zero-dependency `unittest` suite (`tests/test_skills.py`), `CODEOWNERS`, and
  GitHub Actions workflow (`.github/workflows/ci.yml`).
