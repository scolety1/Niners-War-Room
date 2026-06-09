# Phase 10E Player Identity Crosswalk

## Summary

Phase 10E builds a review-only identity crosswalk from exact normalized names, explicit aliases, source IDs, team/college context, draft year, and player URLs where available. It does not score players and does not promote any app rankings.

## Outputs

- Crosswalk: `local_exports\model_v4\player_identity\latest\canonical_player_identity_crosswalk.csv`
- Unresolved report: `local_exports\model_v4\player_identity\latest\unresolved_identity_report.csv`
- Ambiguous report: `local_exports\model_v4\player_identity\latest\ambiguous_identity_report.csv`
- Summary JSON: `local_exports\model_v4\player_identity\latest\player_identity_crosswalk_summary.json`

## Counts

- Source records: 287557
- Canonical rows: 110023
- Unresolved rows: 7610
- Ambiguous rows: 41852

## Guardrails

- No fuzzy joins were used.
- Suffixes Jr., Sr., II, III, and IV are stripped for normalized matching while source names are preserved.
- `KC Concepcion` to `Kevin Concepcion` is the only explicit alias currently applied.
- Duplicate normalized names, conflicting positions, conflicting team/college histories, and multiple IDs are flagged for review.
- Missing IDs remain visible in the unresolved report instead of being silently accepted.
