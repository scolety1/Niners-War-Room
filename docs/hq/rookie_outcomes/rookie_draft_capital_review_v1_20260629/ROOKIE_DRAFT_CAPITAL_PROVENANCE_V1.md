# Rookie Draft Capital Provenance V1 - 2026-06-29

## Source Chain

- Input identity approval: tracked CFBD rookie identity approval V1.
- Draft-capital source used: tracked Rookie HQ overlay display artifact.
- Raw/source-cache files were not committed.
- The artifact is review-only and not source truth.

## Row Counts

- Approved identity rows inspected: 157
- Tracked overlay source rows inspected: 54
- Rows with parsed round/pick/team: 54

## Parsing Rules

- Parsed `round=<number>; pick=<number>` text from the display-only field.
- Assigned `draft_year=2026` only where round/pick was parsed.
- Assigned drafted team only from the same tracked display row.
- Left missing values as `Not enough information`.

## Review-Only Warning

These rows do not authorize model input, training truth, Rankings columns,
Dynasty Rank changes, tier changes, trade values, pick values, or source-truth
promotion.
