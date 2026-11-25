# Knowledge Debt & Lint Output Contract

> **Purpose:** Standardize read-only `lint` reports and draft `KnowledgeDebt`
> records emitted by `repo-kb-lint` and `repo-kb-author` for human routing.
> Agents **never** publish these directly to teams or issue trackers without
> separate human authorization.

---

## 1. Lint Report Summary Structure

Include this header at the top of every `lint` run:

```yaml
lint_report:
  skill_version: "repo-kb-lint@0.1.0"
  repository: "<org/repo>"
  branch: "<branch>"
  commit_sha: "<short-sha>"
  observed_at: "YYYY-MM-DD"
  kb_entry_point: "<README.md | monorepo-index | missing>"
  last_reviewed: "<YYYY-MM-DD | missing>"
  freshness_status: "<Fresh | Stale | Missing>"
  preserved_section_present: "<true | false>"
  visibility_limits:
    - "<e.g., Authoritative domain/data maps not provided in read scope>"
    - "<e.g., Runtime Datadog telemetry not inspected>"
  section_coverage:
    metadata_header: "<Pass | Partial | Missing>"
    product_purpose: "<Pass | Partial | Missing>"
    supported_business_activities: "<Pass | Partial | Missing>"
    system_boundaries: "<Pass | Partial | Missing>"
    interfaces: "<Pass | Partial | Missing>"
    domain_terms: "<Pass | Partial | Missing>"
    data_responsibilities: "<Pass | Partial | Missing>"
    dependencies_and_owners: "<Pass | Partial | Missing>"
```

---

## 2. Draft `KnowledgeDebt` Item Schema

Emit one entry per missing section, stale review date, broken source link,
unmapped owner, or unresolved conflict.

```yaml
knowledge_debt:
  - id: "KD-DRAFT-001"
    category: "<missing_section | stale_review | broken_link | code_doc_conflict | unmapped_owner | map_conflict | sensitive_data_exposure>"
    severity: "<High | Medium | Low>"
    gap: "<Concise description of what is missing, stale, or contradictory>"
    source_evidence:
      - location: "<relative/path/or/map-id>"
        version: "<commit-sha-or-map-version>"
        observed_at: "YYYY-MM-DD"
        provenance: "<Declared | Implemented | Intended | Observed | Inferred>"
    affected_conclusion: "<Which KB section or downstream participation finding is weakened>"
    confidence_impact: "<e.g., Lowers Quote Service participation confidence from High to Medium>"
    proposed_owner: "<Named maintainer or 'Unconfirmed — route via Initiative Lead'>"
    ownership_status: "<Confirmed per map | Proposed — unconfirmed>"
    next_action: "<Concrete human review or routing step>"
    publication_state: "Draft — human routing required (not published)"
```

---

## 3. Severity Guidance (Starter Proposal — Confirm with Knowledge Steward)

| Severity | Criteria |
| --- | --- |
| **High** | Missing KB entry point, undocumented public/external interface, unmapped data/error-state or decision-authority owner, exposed credentials/PII/restricted operational data (`sensitive_data_exposure`), or active conflict between code and contract affecting participation accuracy. |
| **Medium** | `last_reviewed` exceeds review cadence (`> 180` days), broken internal file reference, `CODEOWNERS` conflated with business/product ownership without Domain Map confirmation, or missing system boundary / domain term definition. |
| **Low** | Minor formatting drift, missing optional metadata, or prose clarity issue that does not affect dependency or ownership conclusions. |
