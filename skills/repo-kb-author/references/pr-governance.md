# PR Knowledge Governance Reference

> **Purpose:** Guide `repo-kb-author` (`sync` and `bootstrap` modes) on mapping
> PR diffs to `README.md` sections, documenting explicit no-impact rationales,
> and optionally wiring lightweight PR-sync habits into a product repository.

---

## 1. Change-to-Section Impact Matrix

Use this matrix during `sync` mode as a prompt (not a mechanical checklist) to
identify which `README.md` sections a PR diff may affect:

| Change detected in PR diff | Sections to check and update |
| --- | --- |
| Public API, event, message, or data schema | `## 4. Interfaces`, `## 6. Data responsibilities`, `## 7. Dependencies` |
| Business rule, state transition, eligibility, or domain term | `## 2. Supported business activities` (including *Decisions owned*), `## 5. Domain terms` |
| New capability, revised responsibility, or scope change | `## 1. Product purpose`, `## 2. Supported business activities`, `## 3. System boundaries` |
| Team, maintainer, decision authority, or `CODEOWNERS` change | `## 8. Owner references`, frontmatter `maintainer` (note: `CODEOWNERS` proves technical maintenance only) |
| System boundary, storage, or integration change | `## 3. System boundaries`, `## 4. Interfaces`, `## 6. Data responsibilities`, `## 7. Dependencies` |
| Upstream or downstream product dependency change | `## 7. Dependencies` + note cross-repo follow-up for affected teams |
| Local setup, build/test, env vars, deploy, observability, or SLO change | `## Additional repository documentation` |
| Behavior-preserving internal refactor or formatting | Usually no `README.md` edit; record a specific no-impact rationale |

---

## 2. Structured `sync` Review Output

Every `sync` run must conclude with an explicit, reviewable decision rather than
silently skipping documentation:

```text
Knowledge impact: Updated | No impact | Needs owner decision
Files reviewed: <paths or diff range>
Evidence: <linked source/schema/contract paths @ commit-sha>
README sections changed: <sections updated, or "None">
Rationale (required when No impact): <specific reason this diff does not alter product knowledge; never "N/A">
Cross-product follow-ups: <downstream/upstream repos that may need updates, or "None">
Open questions / KnowledgeDebt: <draft IDs or "None">
```

---

## 3. Opt-In Repository Hooks (`bootstrap` Mode)

Only add or merge these snippets when requested or confirmed by the user, and
never overwrite existing repository instructions or PR template content.

### `AGENTS.md` snippet (merge into existing `AGENTS.md`)

```markdown
## Product knowledge maintenance

The root `README.md` is part of the product contract for both humans and
agentic workflows. Before changing product behavior, interfaces, data roles,
boundaries, or dependencies, review `README.md`.

For every PR, run `repo-kb-author` in `sync` mode: update impacted sections of
`README.md` in the same PR, or record a specific, reviewable no-impact
rationale in the PR description (never `"N/A"`). Do not fabricate ownership,
domain terms, or business accountability from `CODEOWNERS` or code structure.
```

### Pull request template snippet (merge into `.github/pull_request_template.md`)

```markdown
## Knowledge impact (check one)

- [ ] Updated root `README.md` in this PR
- [ ] No `README.md` update required (specific rationale below)

**Knowledge impact rationale:**
<!-- Briefly explain what changed in README.md, or why this PR does not affect product knowledge. Do not write "N/A". -->

**Affected upstream/downstream products or contracts (if any):**
<!-- Name affected boundaries or dependencies, or write "None" with a brief reason. -->
```
