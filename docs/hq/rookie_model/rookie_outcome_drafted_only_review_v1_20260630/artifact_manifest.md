# Drafted-Only Rookie Outcome Review V1

## Verdict

`YELLOW_DRAFTED_ONLY_REVIEW_READY`

## Inputs Used

- Entry-status hygiene CSV: `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv`
- Historical Outcome V2 label CSV: `C:/NWR_SHARED_DATA/rookie_outcomes/historical_labels_v1/rookie_historical_outcome_labels_v1.csv`

## Outputs Created

- `drafted_only_outcome_coverage.csv`
- `drafted_only_outcome_player_audit.csv`
- `outcome_window_censoring_policy.md`
- `drafted_only_baseline_plan.md`
- `udfa_blocker_report.md`
- `gate_f_gate_g_status.md`
- `merge_safety_report.md`

## Source Policy

The entry-status packet is YELLOW and review-only. The Outcome V2 labels are
review-only exact verified first-down labels. This packet consumes them only
for coverage review and does not approve model input, training, tuning, scoring,
app wiring, or source-truth promotion.

## Blocked Populations

- Confirmed UDFA rows: 0
- Likely UDFA needs review rows: 2514
- Wrong universe rows: 138
- Name collision rows: 2

This packet approves drafted-player-only review. UDFA modeling remains blocked.
