# Identity Namespace and Join Contract

## Controlling rule

Hydration may join roster assets only through explicit stable identifiers in declared namespaces. Display names, normalized names, team/name/position composites, rank/name/position composites, hashes of display fields, and inferred opaque IDs are prohibited.

## Existing authority

- Canonical NWR player field: dim_players.player_id, per docs/codex/DATA_CONTRACT.md.
- Admitted roster-source field: Sleeper roster player ID.
- Declared crosswalk field: dim_players.sleeper_id.
- Admitted source policy: sleeper/players and sleeper/rosters in config/source_registry.csv.

The existing field shapes do not prove current completeness. A blank or duplicate sleeper_id blocks the affected roster entry and the complete-roster claim.

## Asset contract

| Asset type | Source identity | Canonical identity | Current result | Cross-season rule | Missing/duplicate behavior |
| --- | --- | --- | --- | --- | --- |
| Active NFL player | Sleeper player ID | NWR player_id through exact unique dim_players.sleeper_id | IDENTITY_GATED | Source ID must be retained; crosswalk changes require an audited assertion | Preserve unresolved row; no facts or weakness indicator for that asset |
| Rookie | Sleeper player ID when assigned | Same NWR player_id namespace | IDENTITY_GATED | Never create a name-derived temporary NWR ID | Mark unresolved until exact admitted ID exists |
| Veteran | Sleeper player ID | Same NWR player_id namespace | IDENTITY_GATED | Same source ID may persist across team/status changes | Duplicate source or canonical ID blocks the snapshot |
| Retired/inactive player | Retained Sleeper player ID | Existing NWR player_id | NOT_ENOUGH_INFORMATION | Do not recycle IDs; status is separate from identity | Retain source row and display inactive/unresolved truth |
| Kicker | Sleeper player ID | Existing NWR player_id | NOT_ENOUGH_INFORMATION | Same player rules | No silent omission; block complete coverage |
| DST | Sleeper defense ID/team token | No proved NWR asset mapping | NOT_ENOUGH_INFORMATION | Team abbreviation changes cannot be guessed | Product exclusion or explicit stable mapping required |
| Taxi entry | Underlying Sleeper player ID | Same NWR player_id | IDENTITY_GATED | Taxi is status, not a new identity | Unresolved player remains visible |
| IR entry | Underlying Sleeper player ID | Same NWR player_id | IDENTITY_GATED | IR is status, not a new identity | Unresolved player remains visible |
| Draft pick | Source-native season, round, original roster coordinates | No declared tracker asset key | NOT_ENOUGH_INFORMATION | Ownership may change; original asset coordinates must not | Product decision and stable identity contract required |
| Unknown provider object | Explicit source ID, if any | None | SOURCE_GATED | No namespace invention | Retain count and type; prohibit join/calculation |

## Uniqueness and completeness proof

Before a snapshot may be COMPLETE:

1. Every non-excluded source asset has a nonblank declared source ID.
2. Every source ID appears once within the same league/roster snapshot.
3. Every supported player source ID maps to exactly one NWR player_id.
4. Every NWR player_id maps back to no more than one active source ID in the same namespace.
5. Duplicate source rows, duplicate canonical IDs, and conflicting asset types fail validation.
6. Coverage numerator, denominator, unresolved count, and excluded count are shown.

The tracked synthetic fixture proves only that 24 sample player_id values are unique and present in its sample dim_players table. It has zero nonblank sleeper_id values and is not evidence of a production source join.

## Join algorithm

1. Validate admitted_source_id and source namespace.
2. Validate source snapshot integrity and schema.
3. Partition by declared asset_type.
4. For player and kicker assets, look up exact source_player_id in dim_players.sleeper_id.
5. Accept only a one-to-one result.
6. Record EXACT_STABLE_ID, UNRESOLVED, DUPLICATE_SOURCE_ID, DUPLICATE_CANONICAL_ID, UNSUPPORTED_ASSET_TYPE, or SOURCE_GATED.
7. Never attempt another join method after an exact lookup fails.

## Snapshot behavior

- One unresolved player makes identity coverage partial, not complete.
- A duplicate identity makes the snapshot invalid for calculations.
- Unsupported assets remain counted and visible.
- Resolved rows may be displayed descriptively only if partial-coverage labeling remains visible.
- Rankings or values may join only through the resolved NWR player_id and retain their own trust/freshness state.
- Name fields are display-only and may never repair identity.

## Re-entry proof

Re-entry requires an approved local test pack manifest and an aggregate audit proving zero blank, duplicate, ambiguous, or missing exact mappings for every in-scope asset. DST and draft picks require either separate product authority excluding them or an approved stable identity contract.
