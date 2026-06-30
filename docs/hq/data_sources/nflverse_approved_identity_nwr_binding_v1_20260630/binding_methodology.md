# Binding Methodology

## Grain

`approved_identity_nwr_binding_matrix.csv` has one row per human-approved NFLVerse identity overlay row. The grain is not one row per app player context row and is not a replacement for the tracked player context artifact.

## Binding Rule

A row may be marked `BOUND_REVIEW_ONLY` only when all required conditions hold:

1. The source overlay row has `human_decision=APPROVE_REVIEW_ONLY` and `approved_by_human=true`.
2. The identity-hardening packet has exactly one matching row by normalized player name, position, team, approved NFLVerse ID, and approved GSIS ID.
3. The current tracked NWR/Sleeper context has exactly one matching row by normalized player name, position, and team.
4. The frozen-board identity audit has exactly one matching row by normalized player name, position, and team.
5. The candidate NWR player ID is present in the current NWR/Sleeper context.
6. Any available candidate Sleeper ID from the identity-hardening packet agrees with the current NWR/Sleeper context and frozen-board identity audit.
7. There are no same-name collisions, position mismatches, team mismatches, many-to-one joins, or one-to-many joins.
8. If the identity-hardening packet does not carry a candidate Sleeper ID, the frozen-board identity audit must agree with current NWR/Sleeper context and must not require manual review.

Rows that fail any condition are left as `NEEDS_MORE_INFO` or `AMBIGUOUS_BLOCKED`.

## Why Sleeper ID Is Used As Candidate NWR Player ID

The existing tracked player-context display artifact has 240 / 240 safe rows where `nwr_player_id` equals `nflverse_sleeper_id`, with `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`. This packet uses that tracked convention only for review-only binding rows and only when the candidate Sleeper ID is uniquely supported.

## Sources Used

- Human-approved NFLVerse overlay: approved NFLVerse/GSIS identity evidence.
- Identity-hardening packet: candidate NFLVerse/GSIS/Sleeper evidence and collision flags.
- Current NWR/Sleeper context: candidate NWR player ID source.
- Frozen-board identity audit: board-presence and Sleeper ID agreement cross-check.
- Existing player context display artifact: NWR/Sleeper ID convention proof.

## Sources Not Used

- `ff_rankings` was not used.
- DynastyProcess IDs were not used as binding evidence.
- Raw/shared/cache/local_exports/secrets were not read or tracked.
- Market, ADP, vendor, Gmail, or private sources were not used.

## Missingness

Missing identity data remains `Not enough information`. Missing data is never treated as a clean match, healthy state, zero usage, no role, confirmed UDFA, or low-risk signal.
