# Lagged Usage Candidate Gate V1 - Artifact Manifest

## Verdict

`YELLOW_LAGGED_USAGE_CANDIDATE_GATE_READY_REVIEW_ONLY`

## Base

`origin/work/hq-parallel-control` at `866e3d0c0ff61a7c13f761d3999cc2e8d77e9a05`.

## Scope

Review-only policy packet for season N to season N+1 NFLVerse/Sleeper/NFL Usage model-candidate feature families. This packet does not approve production model use, training, tuning, probabilities, rankings, recommendations, hidden sort, source truth, or app wiring.

Deep Research confirmation incorporated: finish through review-only lagged factual usage artifacts; do not block on full fantasy scoring parity or return TD subtype; do not build route proxies; treat red-zone as source-admit / coverage-audit.

## Output artifacts

| File | Purpose |
| --- | --- |
| `lagged_usage_feature_candidate_matrix.csv` | Candidate feature classification matrix. SHA256: `aa686fb607579948eeb122d041cd8cc17de96f23de72dfa0b826e85c448ee256` |
| `lagged_usage_candidate_summary.md` | Executive summary and candidate counts. |
| `season_n_to_n_plus_1_policy.md` | Practical lagged season policy. |
| `excluded_or_optional_feature_report.md` | Optional or excluded fields. |
| `redzone_feature_decision.md` | Red-zone decision. |
| `route_metric_decision.md` | Route metric decision. |
| `guardrail_report.md` | Approval and missingness guardrails. |
| `next_dataset_builder_prompt.md` | Prompt for the next review-only builder lane. |
| `merge_safety_report.md` | Merge safety statement. |
