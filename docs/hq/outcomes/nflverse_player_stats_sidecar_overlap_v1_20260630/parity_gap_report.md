# Parity Gap Report

Verdict: `OVERLAP_PARTIAL_ROW_LEVEL_PARITY_BLOCKED`

## What This Packet Can Say

- Existing Outcome V2 label count evidence exists by position and field.
- Rookie drafted-only feasibility count evidence exists by position and season.
- The tracked NFLVerse weekly player_stats template has a usable schema shape.
- The model candidate readiness matrix explicitly recommends this sidecar overlap lane.

## What This Packet Cannot Compute

- Row-level matched players between Outcome labels and NFLVerse player_stats.
- `unmatched_label_rows.csv`.
- `unmatched_nflverse_rows.csv`.
- identity match rate.
- scoring parity.
- first-down scoring parity.
- censoring parity.
- duplicate/collision resolution.
- mismatch categories.

## Primary Gap

No tracked row-level historical NFLVerse `player_stats` sidecar exists in the repo. The only tracked weekly player_stats file is a zero-row schema template.

## Secondary Gaps

- The drafted-only feasibility CSV reports count-level review evidence, not sidecar matches.
- The 2024/2025 receipt counts are aggregate context and cannot be used to infer row-level overlap.
- Existing Outcome labels remain evaluation targets only.
- Missing labels and incomplete windows require `Not enough information` or right-censoring treatment.

## Not a Failure

The absence of row-level sidecar matches is a blocker for parity promotion, not a negative player outcome or low-probability signal.
