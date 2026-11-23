# Agent Skills Library

Stewarded collection of portable [Agent Skills](https://agentskills.io)
(`SKILL.md`) for curating repository-local knowledge bases (`README.md`) and
authoritative platform maps. Designed for **GitHub Copilot** and compatible
with Claude Code, Codex, and Cursor.

## Available Skills

| Skill | Access Mode | Intended Audience | Purpose |
| --- | --- | --- | --- |
| [`repo-kb-lint`](skills/repo-kb-lint/SKILL.md) | `read-only` | Research orchestrator, CI, auditors | Audits standardized product `README.md` files (deterministic schema/link/freshness checks + semantic drift) and emits draft `KnowledgeDebt`. |
| [`repo-kb-author`](skills/repo-kb-author/SKILL.md) | `draft-write` | Product & delivery teams | Bootstraps or non-destructively revises product root `README.md` files (preserving non-standard sections) and syncs PR diffs. |
| [`platform-map-author`](skills/platform-map-author/SKILL.md) | `draft-write` | Domain, product, architecture & data owners | Conversationally drafts/updates one-file-per-entity authoritative map YAML files in the owner's preferred vocabulary (DDD or non-DDD). |

---

## Installing Skills (Least-Privilege by Consumer)

Replace `<org>/<repo>` with your published GitHub repository path.

### GitHub Copilot (via GitHub CLI)
```bash
# Delivery teams (into product repo .github/skills/)
gh skills install --agent github-copilot --scope project <org>/<repo> repo-kb-author

# Read-only auditors / research orchestrator
gh skills install --agent github-copilot --scope project <org>/<repo> repo-kb-lint

# Authoritative platform-maps repo
gh skills install --agent github-copilot --scope project <org>/<repo> platform-map-author
```

### Cross-Client CLI (`skills.sh`)
```bash
npx skills add <org>/<repo> --skill repo-kb-author
npx skills add <org>/<repo> --skill repo-kb-lint
npx skills add <org>/<repo> --skill platform-map-author
```

---

## Contributing & Maintaining Shared Assets

Each folder under `skills/<name>/` is **100% self-contained** so consumers can
install a single skill without cross-folder dependencies.

When editing shared files in `shared/` (`validate_kb.py` or
`knowledge-debt-contract.md`), sync them into the skill folders and run tests
before opening a PR:

```bash
python3 scripts/sync_shared.py
python3 -m unittest discover -s tests -v
```

GitHub Actions (`.github/workflows/ci.yml`) automatically verifies frontmatter
validity, shared-file parity, and deterministic validator behavior on every PR.

> **Before publishing internally:** Replace placeholder team handles in
> [`.github/CODEOWNERS`](.github/CODEOWNERS) and swap [`LICENSE`](LICENSE) if
> publishing as a private internal repository.
