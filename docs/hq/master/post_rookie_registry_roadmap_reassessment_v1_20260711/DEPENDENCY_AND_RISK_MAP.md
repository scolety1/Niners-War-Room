# Dependency and Risk Map

## Immediate lane boundary

```text
Trading Lab human-entered fields
  -> allowlisted scenario schema
  -> explicit local save
  -> previewed load/import
  -> explicit overwrite confirmation
  -> atomic write + backup + corrupt quarantine
  -> focused lifecycle and isolation tests

Excluded from every arrow:
rank/formula/source/plugin/registry/frozen-comparator effects
derived-value persistence
fairness, winner, package score, or offer generation
Live Draft or Mock Draft state mutation
```

The lane may reuse the lifecycle shape of `src/services/development_lab_state_service.py`, but it must use a distinct storage root, schema, keys, and tests. Reuse means borrowing a proven defensive pattern, not sharing state between products.

## Immediate dependency table

| Dependency | Present state | Lane use | Risk | Required control |
|---|---|---|---|---|
| Trading Lab manual fields | Implemented | Persist an explicit allowlist | Moderate | Schema-versioned serialization; reject unlisted fields |
| Stable player/pick keys | Existing page/service identities | Store keys and human-entered labels | Moderate | Unknown keys remain unresolved; no name fallback |
| Streamlit session state | Current scenario lifetime | Hydrate only after explicit user action | Moderate | No implicit overwrite; deterministic default state |
| Local filesystem | Used elsewhere for manual review state | Dedicated untracked store | Low | Environment override, atomic replace, backup, quarantine |
| Development Lab state pattern | Proven in repository | Pattern reference only | Low | No cross-product files, imports, or shared namespaces |
| Draft state | Separate Live/Mock workflows | Must remain untouched | High if crossed | Isolation assertions and diff review |
| Rankings/formulas/sources/plugins/registry | Protected systems | No dependency | Critical if crossed | Forbidden imports/effects scan and merge-review stop |

## Later-lane dependencies

### Player Compare Compact-Width and Accessibility Hardening V1

- Depends only on the existing Player Compare page, display components, and existing admitted facts.
- Does not depend on the Trading Lab lane.
- Primary risks: accidental copy semantics that imply a winner, layout regressions, and static-only tests.
- Controls: preserve information order and caveats; verify keyboard focus, accessible names, status announcements, and compact widths; add focused rendered checks where feasible.

### Data Health Guardrail Truth and Refresh Receipt Durability V1

- Depends on existing Git diagnostics and refresh status/archive formats.
- Does not depend on product decision logic.
- Primary risks: false green status, breaking existing receipts, or changing refresh execution accidentally.
- Controls: fail closed on diagnostic error; inspect unstaged, staged, and untracked protected changes; atomically replace receipts; recover only from a validated archive; leave source execution untouched.

### Roster Weakness Tracker Admitted-Roster Hydration Design and Readiness V1

- Depends on `fact_rosters`, stable player identity, local-pack behavior, and a human-confirmed league configuration boundary.
- Current clean checkouts may not have the ignored active pack.
- Exact lineup slots are not canonical in `src/config/league_rules.yaml`; a starter format is hard-coded in `src/services/future_tools_rd_service.py`.
- This is a design/readiness lane, not implementation. It must specify missing-pack, empty roster, ambiguous identity, stale roster, and manual override behavior before code is authorized.

## Risk gates

| Gate | Pass condition | Stop condition |
|---|---|---|
| Formula | No formula import, output, ranking weight, or challenger use | Any numerical decision logic or frozen-comparator influence |
| Source | Existing admitted facts only; no source registry change | New endpoint, provider call, promotion, or authority change |
| Plugin | No Flaim/FantasyBot call, adapter, field, or influence | Any automated or numerical plugin path |
| Rookie registry | No registry reads/writes or queue work | Mapping, player/evidence row, identity, endpoint, or authority effect |
| Draft isolation | Live and Mock state snapshots unchanged by Trading Lab operations | Any draft event, pick, namespace, or persisted state mutation |
| Persistence | Explicit local action, allowlist, preview, atomicity, recovery | Silent autosave, implicit overwrite, arbitrary path, or derived-fact persistence |
| Frozen artifacts | Byte-identical before and after | Any content or metadata change in tracked frozen/freeze/prospective paths |

## Merge structure

Only one lane should be active:

1. implementation worktree from then-current verified HQ;
2. bounded implementation and focused tests;
3. independent merge-review worktree;
4. protected/frozen diff review;
5. local adoption only after review.

No later lane is a hidden dependency of the immediate lane.
