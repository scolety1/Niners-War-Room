# CFBD Rookie Bridge Audit - 2026-06-30

## Result

`BLOCKED_NEEDS_DRAFT_CLASS_BRIDGE`

Gate-A CFBD identities are approved only for identity review. They bridge
to NWR/Sleeper-style player IDs, but not to the GSIS/NFL player IDs used by
the Outcome V2 historical target labels.

## Counts

- Approved identity rows audited: 157
- Outcome link `not_linked_current_2026_outside_2012_2024_outcome_window`: 54
- Outcome link `not_linked_missing_draft_class_and_nfl_id`: 103
- Draft capital `MISSING_DRAFT_CAPITAL_REVIEW_REQUIRED`: 103
- Draft capital `PARTIAL_REVIEW_ONLY_DRAFT_CAPITAL_AVAILABLE`: 54

## Limitations

- CFBD college team/timeline is review-only context, not outcome truth.
- Draft year is present for only the partial Gate B rows.
- Current 2026 rookie rows are outside the 2012-2024 historical outcome window.
- Historical rookie classes need a separate identity/draft-class bridge.
