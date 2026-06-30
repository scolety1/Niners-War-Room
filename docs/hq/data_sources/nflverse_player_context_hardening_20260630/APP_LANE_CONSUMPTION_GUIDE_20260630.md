# App Lane Consumption Guide - NFLVerse Player Context

All app lanes must read only the tracked player context artifact:

`docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv`

Never read raw `C:\NWR_SHARED_DATA` from app pages.

## Required Row Filter

- Join by `nwr_player_id`.
- Require `identity_join_status=SAFE_NOW_DISPLAY_ONLY`.
- Require `review_required=false`.
- Treat `Not enough information` as missing, not false/healthy/no-role/zero/UDFA.
- Identity proposals are not approved joins.

## Forbidden Uses

Do not use NFLVerse player context for model input, rank logic, source truth, hidden sort, trade value, pick value, recommendations, start/sit, or valuation logic.

## Lane Notes

- Rankings / Outcome Lens: display-only fields may be shown after the required row filter; never sort/rank by them.
- Player Compare: display only; do not score players from the fields.
- Trading Lab: display only; no trade value or pick value use.
- Development Lab: diagnostics/review only; no model promotion.
- Draft Room / Analyzer: display context only; no recommendations or hidden sort.
- Injury Availability: missing injury remains `Not enough information`, not healthy.
- Rookie Outcomes: identity proposals remain review-only and are not current-player activation.

Schedule/opponent/bye fields are available only when populated in the tracked artifact for safe identity rows. Missing schedule remains `Not enough information`.