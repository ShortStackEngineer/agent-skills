# Standardized Product `README.md` Template

> **Usage:** Use this template for the **root `README.md`** of each product
> repository so both **humans** and **agentic workflows** share a single,
> consistent entry point. (For multi-product monorepos, keep a short product
> index in root `README.md` linking to each product's standardized `README.md`.)
>
> **Revising an existing `README.md`:** Map content that belongs in Sections
> 1–8 into the standard layout, preserve any disagreements with code/contracts
> in *Known visibility limits & open conflicts*, and move all remaining
> repo-specific documentation (local setup, testing, runbooks, deployment,
> badges, troubleshooting) intact into **Additional repository documentation**
> below. Every technical claim must link to a verified source file and
> commit/version. Keep prose short, concrete, and unambiguous.

---

```markdown
---
kb_schema_version: "0.1"
product_name: "<Product or Service Name>"
maintainer: "<Named Person or Role — TBD until confirmed>"
last_reviewed: "YYYY-MM-DD"
review_cadence_days: 180
verified_commit: "<short-sha-or-tag>"
authoritative_maps:
  context_map_ref: "<URL or ID — TBD if unmapped>"
  domain_map_ref: "<URL or ID — TBD if unmapped>"
  data_map_ref: "<URL or ID — TBD if unmapped>"
---

# <Product or Service Name>

> **Status:** `Draft` | `Reviewed`  
> **Maintainer:** `<Named Maintainer>` · **Last reviewed:** `YYYY-MM-DD` · **Verified at:** `<commit-sha>`

## 1. Product purpose
<!-- 2–4 concise sentences: what this product/service does and who relies on it. -->

## 2. Supported business activities
<!-- Link each activity to business outcomes or journey stages when known. -->
| Activity | Role of this repo | Evidence / Reference | Status |
| --- | --- | --- | --- |
| `<e.g., Quote retrieval>` | `<Handles quote lookup and timeout fallback>` | `[src/quotes/retrieve.ts](src/quotes/retrieve.ts)` @ `<sha>` | `Implemented` / `Declared` |

## 3. System boundaries
- **In scope:** `<Concrete responsibilities owned by this codebase>`
- **Out of scope:** `<Adjacent capabilities explicitly handled elsewhere>`
- **Context map reference:** `<Link or ID; mark TBD if not yet mapped>`

## 4. Interfaces
<!-- Distinguish intended contracts (OpenAPI/schema) from implemented entry points. -->
| Interface | Direction | Protocol / Contract | Source evidence | Provenance |
| --- | --- | --- | --- | --- |
| `POST /v2/quotes/retrieve` | Inbound | `[api/openapi.yaml](api/openapi.yaml)` | `[src/routes/quotes.ts](src/routes/quotes.ts)` @ `<sha>` | `Intended + Implemented` |

## 5. Domain terms
<!-- Define terms as used inside this boundary; note conflicts with enterprise glossaries. -->
| Term | Local definition | Authoritative source / Conflict note |
| --- | --- | --- |
| `<e.g., Active Quote>` | `<Quote not expired and retrievable by customer>` | `<Domain map ref or TBD>` |

## 6. Data responsibilities
<!-- Do NOT declare authoritative ownership without a verified Data Map reference. -->
| Data entity / state | Role (`Producer` / `Consumer` / `Store`) | Authoritative owner (per Data Map) | Evidence |
| --- | --- | --- | --- |
| `<e.g., Quote Status>` | `Producer` | `<Quote Domain (per Data Map vX)>` | `[schemas/quote-status.json](schemas/quote-status.json)` @ `<sha>` |
| `<e.g., QUOTE_RETRY_TIMEOUT>` | `Producer` | `Unconfirmed — see Knowledge Debt` | `[src/errors/retry.ts](src/errors/retry.ts)` @ `<sha>` |

## 7. Dependencies
| Dependency | Direction (`Upstream` / `Downstream`) | Purpose | Evidence | Provenance |
| --- | --- | --- | --- | --- |
| `<e.g., Channel Web>` | `Upstream` | Calls quote retrieval API | `[api/openapi.yaml](api/openapi.yaml)` | `Intended` |

## 8. Owner references
- **Product owner:** `<Name / Team — per Domain Map>`
- **Delivery team:** `<Team — per Authoritative Map or TBD>`
- **Escalation / routing channel:** `<Agreed human process — no autonomous agent outreach>`

## Known visibility limits & open conflicts
<!-- Preserve unresolved disagreements between existing README claims, code, contracts, telemetry, and maps. -->
- `<None recorded, or list explicit gaps and conflicting sources with commit/date refs>`

---

## Additional repository documentation
<!--
  Dedicated preservation section for existing README content that does not fit
  Sections 1–8 (e.g., Local development setup, Running tests, Environment
  variables, Deployment & release runbooks, Troubleshooting, Contributing).
  Preserve original subheadings and operational details intact. Omit this
  section only for greenfield repos with no extra documentation yet.
-->

### `<Preserved heading, e.g., Local development & testing>`
`<Preserved content from the prior README.md>`
```
