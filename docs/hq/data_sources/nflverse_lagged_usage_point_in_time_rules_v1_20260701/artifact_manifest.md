# Artifact Manifest

Packet: `nflverse_lagged_usage_point_in_time_rules_v1_20260701`

Verdict: `GREEN_REVIEW_ONLY_LAGGED_USAGE_ASOF_RULES_READY`

Branch context: `work/sleeper-nflverse-usage-redzone-source-admission-v1-20260701`

Base HQ HEAD: `866e3d0c0ff61a7c13f761d3999cc2e8d77e9a05`

## Files

| File | Purpose |
|---|---|
| `point_in_time_rules_summary.md` | Executive summary and final as-of policy posture. |
| `lagged_usage_asof_policy_matrix.csv` | Feature-family as-of classification for review-only season N to season N+1 construction. |
| `season_anchor_policy.md` | Required season-close and prediction-anchor rules. |
| `feature_availability_timeline.md` | Timeline for when lagged factual usage may become available. |
| `current_only_field_exclusion_report.md` | Current-only families excluded from historical feature construction. |
| `guardrail_report.md` | Closed approval flags and behavior-change guardrail proof. |
| `next_dataset_builder_handoff.md` | Actionable handoff for Core Usage Review Dataset V1. |
| `merge_safety_report.md` | Docs-only scope and merge caveats. |

## Scope

This packet defines review-only point-in-time/as-of rules. It does not build features, train models, approve experiments, create probabilities, or wire app behavior.
