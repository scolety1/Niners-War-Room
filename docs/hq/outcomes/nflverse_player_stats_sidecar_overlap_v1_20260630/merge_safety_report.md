# Merge Safety Report

Verdict: `SAFE_DOCS_CSV_ONLY_NO_ACTIVATION`

## Changed Surface

This lane creates only review-only docs and one overlap matrix under:

`docs/hq/outcomes/nflverse_player_stats_sidecar_overlap_v1_20260630/`

## Guardrail Confirmation

- No app files changed.
- No Rankings files changed.
- No Player Compare files changed.
- No Rookie Outcome runtime files changed.
- No model files changed.
- No rank logic changed.
- No source-truth gate changed.
- No probabilities created.
- No label truth promoted.
- No model/training/source-truth approvals granted.
- No Rookie Gate G approval granted.
- No raw, shared, private, cache, local export, or secret files tracked.
- No `latest_candidate`, `latest_approved`, pinned, or frozen artifacts changed.

## Unmatched Files

`unmatched_label_rows.csv` and `unmatched_nflverse_rows.csv` were not created because row-level sidecar overlap is not computable from the tracked artifacts. Creating row-level unmatched files would require fabricating rows.
