# Model v4.6 Warning Code Dictionary

## Scope

This review-only dictionary maps raw warning codes into plain-English groups. It does not change formulas, scores, rankings, or decision outputs.

## Outputs

- `local_exports/model_v4/warning_dictionary/latest/warning_code_dictionary.csv`
- `local_exports/model_v4/warning_dictionary/latest/warning_group_display_map.csv`

## Warning Groups

| Group | Severity | Raw Codes |
|---|---|---:|
| Manual review required | high | 9 |
| Review-only guardrail | info | 10 |
| 1QB QB caution | medium | 3 |
| Data incomplete | medium | 93 |
| Low draft investment | medium | 1 |
| No-premium TE caution | medium | 3 |
| Source-limited role data | medium | 6 |
| General review | review | 46 |
| Model edge | review | 2 |

## Highest Frequency Codes

| Raw Code | Group | Count |
|---|---|---:|
| gray_missing | Data incomplete | 2934 |
| market_context_excluded_from_private_value | General review | 2143 |
| current_college_team_mismatch_quarantined | Manual review required | 1885 |
| missing_age_lifecycle_component | Data incomplete | 1771 |
| source_shape_warning | Model edge | 1426 |
| green_complete | General review | 1368 |
| yellow_partial | Data incomplete | 1357 |
| missing_draft_capital_component | Data incomplete | 1340 |
| source_limited_evidence_cap | Source-limited role data | 1231 |
| third_party_combine_source_limited | Source-limited role data | 1231 |
| missing_landing_context_review | Data incomplete | 1090 |
| missing_athletic_prior_component | Data incomplete | 980 |
| combine_absent_not_zero_filled | Data incomplete | 912 |
| review_only_vorp_context_excluded_from_private_value | Review-only guardrail | 800 |
| missing_recruiting_prior_component | Data incomplete | 785 |
| licensed_route_metrics_not_available | Source-limited role data | 710 |
| not_used_in_stats_first_value | General review | 710 |
| missing_evidence | Data incomplete | 541 |
| orange_source_limited | Source-limited role data | 476 |
| team_or_context_mismatch_warning | General review | 402 |
| missing_prospect_or_college_evidence | Data incomplete | 330 |
| workout_metric_missing_after_zero_repair | Data incomplete | 290 |
| workout_metric_zero_placeholder_repaired | General review | 290 |
| red_manual_review | Manual review required | 262 |
| missing_market_share_component | Data incomplete | 241 |

## Drilldown Fields

Each dictionary row includes `primary_module`, `primary_export`, `receipt_or_drilldown_to_open`, and `example_review_question` so a reviewer can move from a raw code to the right app surface or CSV.

## Safety

- Raw warning codes remain available in source exports and drilldowns.
- Dictionary rows are review-only.
- Warning text is not a final cut, keep, trade, defer, or draft instruction.
