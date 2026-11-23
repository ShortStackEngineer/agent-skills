# Platform Maps Invariant Kernel Specification (`v0.1`)

> **Design rule:** Keep the kernel tiny and invariant so the read-only MCP,
> skills (`repo-kb-lint`, `repo-kb-author`), and deterministic validator work
> uniformly across every team. Keep `extensions:` **completely freeform**.

---

## 1. File Placement (One File Per Entity / Context)

| `map_role` | Directory | ID Prefix Convention | Examples |
| --- | --- | --- | --- |
| `boundary` | `boundaries/<slug>.yaml` | `ctx:` or `sys:` | `ctx:quote-retrieval`, `sys:channel-web` |
| `ownership` | `domains/<slug>.yaml` | `dom:` or `cap:` | `dom:quoting`, `cap:digital-channels` |
| `data` | `data/<slug>.yaml` | `data:` | `data:quote-status` |

## 2. Required Invariant Kernel Fields

```yaml
schema_version: "0.1"             # Required
vocabulary_profile: "ddd"         # Required: ddd | product-system | c4 | custom
map_role: "boundary"              # Required: boundary | ownership | data

id: "ctx:quote-retrieval"         # Required: globally unique slug across all maps
name: "Quote Retrieval"           # Required: human-readable display name
native_kind: "Bounded Context"    # Required: team's own noun (free text)
summary: "Short 1-2 sentence purpose." # Optional but strongly recommended

governance:                       # Required
  owner: "Named Role or Person"   # Required: authoritative approver (or TBD)
  steward: "Optional maintainer"  # Optional
  last_reviewed: "YYYY-MM-DD"     # Required: ISO date
  review_cadence_days: 180        # Optional (default: 180)

repos:                            # Optional: GitHub org/repo refs
  - "org/quote-service"

relationships:                    # Optional list of graph edges
  - target_id: "dom:quoting"      # Must resolve to an existing map id
    relation: "belongs_to"        # Must be in canonical enum below
    native_relation: "Subdomain Of" # Optional: team's own nuance

extensions: {}                    # Completely freeform (never schema-rejected)
```

## 3. Canonical `relation` Enum

| Relation | Meaning |
| --- | --- |
| `belongs_to` | Entity sits inside an ownership domain or parent boundary |
| `contains` | Domain or parent boundary contains child entity |
| `owns` | Authoritative ownership relationship |
| `depends_on` | Calls or relies on target to fulfill its function |
| `integrates_with` | Bidirectional or peer integration (e.g., Partnership, Shared Kernel) |
| `produces` | Emits, publishes, or writes target data/event |
| `consumes` | Reads or subscribes to target data/event |
| `produced_by` | Inverse of `produces` (useful on `data` map files) |
| `consumed_by` | Inverse of `consumes` (useful on `data` map files) |
| `maps_to` | Equivalent or bridging alignment across vocabularies |
