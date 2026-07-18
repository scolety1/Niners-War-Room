# Current Implementation Gap Analysis

## Current state

The current tracker is a visible Streamlit Development Lab route. It:

- accepts comma-separated manual roster rows;
- displays position, age, and dynasty-rank buckets;
- optionally accepts an NWR player ID for display-only context;
- persists manual lab notes outside the repository;
- makes no active recommendation.

## Gaps

| Area | Current implementation | Required future state | Result |
| --- | --- | --- | --- |
| Source | Manual text; no roster source adapter | Read an admitted retained snapshot | BLOCKED |
| Source admission | Registry admits Sleeper | Bind an exact admitted source ID in the snapshot | GREEN authority, no adapter |
| Identity | Optional manual NWR ID; identity services contain name fallbacks | Exact source ID to NWR ID only | BLOCKED |
| Snapshot | fact_rosters date/season rows | Immutable snapshot ID, schema, integrity, lifecycle | BLOCKED |
| Roster fields | Rostered player inventory | Starter/bench/taxi/IR/eligibility/ownership states | BLOCKED |
| League config | Partial YAML and hard-coded thresholds | Typed canonical lineup/flex/phase config | YELLOW |
| Freshness | No roster-specific receipt | Existing Data Health semantics with retained state | YELLOW |
| LocalData | Default ignored pack path | Approved pack and manifest present | BLOCKED |
| Privacy | Manual notes in shared local root; old puller raw data outside Git | Bounded normalized local_exports root | YELLOW |
| Calculation | Counts and manual buckets | Descriptive facts only at first | YELLOW |
| Trust | Page has manual/display-only copy | Decision Trust Strip plus roster lifecycle | GREEN design reuse |
| Tests | Service/static tests | Exact-ID, lifecycle, corruption, clean-checkout, route tests | YELLOW |
| Route | Registered and file exists | Read-only empty/missing/stale behavior | YELLOW |

## Unsafe reuse

The following current behavior must not be carried into hydration:

- STARTER_FORMAT as league authority;
- player-name or normalized-name matching;
- player_id or player_name validation that accepts either as identity;
- identity-audit name fallback;
- manual NWR ID as an implicit trusted source join;
- active-pack existence assumptions;
- source snapshot date strings that do not distinguish as-of and hydration time;
- any model recommendation, ranking bucket, or market signal as weakness.

## Existing reusable authority

- source registry and source-governance firewall;
- canonical league rules lock;
- data-pack validation patterns, after identity hardening;
- refresh receipt lifecycle vocabulary;
- Decision Trust Strip state vocabulary;
- LocalData no-copy/no-check-in contract;
- synthetic fixture and focused test patterns.
