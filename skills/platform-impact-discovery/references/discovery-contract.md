# Platform Impact Discovery Output Contract (`v0.1`)

> **Purpose:** Standardize the read-only consultation records, Contribution
> Matrix, Conceptual Flow, and confidence rubric produced by
> `platform-impact-discovery` for human owner alignment.
>
> All YAML/JSON blocks below are vendor-neutral logical schemas. They do not
> assume a specific MCP server, orchestrator runtime, or issue tracker.

---

## 1. Pinned Repo Consultation Record

Capture one record per consulted repository so every claim remains traceable to
an exact revision and provenance level:

```yaml
consultation:
  initiative_id: "INIT-EXAMPLE"
  map_id: "ctx:quote-retrieval"        # Authoritative map ID, or "unmapped"
  repository: "org/quote-service"
  pinned_commit: "<short-sha>"
  observed_at: "YYYY-MM-DD"
  kb_health:
    freshness_status: "Fresh | Stale | Missing"
    broken_links_count: 0
    unresolved_marker_count: 0
  current_state:
    - claim: "Retrieves active quotes via POST /v2/quotes/retrieve"
      evidence: "src/routes/quotes.ts @ <short-sha>"
      provenance: "Implemented"        # Declared | Intended | Implemented | Inferred
  decisions_owned:
    - decision: "Quote expiration eligibility"
      authority: "Confirmed per dom:quoting | Unconfirmed"
      evidence: "src/quotes/eligibility.ts @ <short-sha>"
  data_roles:
    - data_map_ref: "data:quote-status"
      role: "Producer"                 # Producer | Consumer | Store
      authoritative_owner: "Quoting Data Owner (per data:quote-status)"
  proposed_changes:
    - change: "Expose quote-modification eligibility flag"
      status: "proposed"               # Never present as approved or implemented
  discovered_dependencies:
    - target: "sys:channel-web"
      reason: "Upstream caller of quote retrieval API"
      status: "consulted | needs_consultation"
  open_questions:
    - "Who owns decision authority if a quote is already bound?"
  knowledge_debt_refs:
    - "KD-DRAFT-001"
```

---

## 2. Contribution Matrix (Present in Finding Summary)

| Product / Boundary (`map_id`) | Authoritative Domain & Data Owner | Current Responsibility | Proposed Contribution | Dependencies | Confidence | Owner Decision |
| --- | --- | --- | --- | --- | --- | --- |
| `<Quote Retrieval (ctx:quote-retrieval)>` | `<Quoting Domain Owner / Quoting Data Owner>` | `<Retrieves unexpired quotes>` | `<Proposed: return modification eligibility>` | `<Upstream: sys:channel-web>` | `High` / `Medium` / `Low` | `Pending review` |

---

## 3. Conceptual Flow Representation

Keep current-state and proposed-state nodes distinct, and flag every cross-team
edge that lacks a verified contract:

```yaml
conceptual_flow:
  schema_version: "0.1"
  initiative_id: "INIT-EXAMPLE"
  flow_id: "FLOW-EXAMPLE"
  version: 1
  status: "proposed"                   # proposed | owner_reviewed | baseline_approved
  objective: "<1-2 sentence initiative goal>"
  nodes:
    - id: "step-1"
      map_id: "sys:channel-web"
      responsibility: "Capture customer modification request"
      decision_authority: null
      input_data: ["data:quote-id"]
      output_data: ["data:quote-change-request (unmapped)"]
      status: "proposed"               # current | proposed
      evidence:
        - "org/channel-web/README.md @ <short-sha>"
    - id: "step-2"
      map_id: "ctx:quote-retrieval"
      responsibility: "Evaluate eligibility and apply state transition"
      decision_authority: "ctx:quote-retrieval"
      input_data: ["data:quote-change-request (unmapped)", "data:quote-status"]
      output_data: ["data:quote-status"]
      status: "proposed"
      evidence:
        - "org/quote-service/README.md @ <short-sha>"
  edges:
    - from: "step-1"
      to: "step-2"
      contract: null
      status: "requires_contract_review" # verified | requires_contract_review
  source_snapshots:
    - repository: "org/quote-service"
      pinned_commit: "<short-sha>"
      observed_at: "YYYY-MM-DD"
  open_questions:
    - "Does data:quote-change-request require a new authoritative Data Map entry?"
  approvals: []                        # Populated only by human approval records
```

---

## 4. Participation Confidence Rubric

| Confidence | Criteria |
| --- | --- |
| **High** | Confirmed in authoritative platform maps (`domains/`, `boundaries/`, `data/`), `README.md` is `Fresh`, technical claims verified against linked code/contracts at a pinned commit, and zero `High`-severity `KnowledgeDebt` items affect the finding. |
| **Medium** | Mapped or partially mapped, but `README.md` is `Stale`, relies on `Inferred` claims, has `TBD` markers, or has `Medium`-severity `KnowledgeDebt` / `requires_contract_review` edges. |
| **Low** | Unmapped in authoritative platform maps, `README.md` is missing or contradicts code/maps (`High`-severity `KnowledgeDebt`), owner is `Unconfirmed`, or repository was inaccessible (`visibility_limits`). |
