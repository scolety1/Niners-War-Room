# Artifact Manifest

Packet: `sleeper_nflverse_usage_redzone_source_admission_v1_20260701`

Verdict: `YELLOW_USAGE_REDZONE_SOURCE_ADMISSION_REVIEW_ONLY_WITH_ROUTE_GAPS`

## Contents

| File | Purpose |
|---|---|
| `source_admission_summary.md` | Executive source-admission decision and coverage summary. |
| `sleeper_weekly_stats_receipt.csv` | Compact receipts for Sleeper public weekly stats API checks; no raw API payloads. |
| `usage_redzone_field_mapping.csv` | Requested field mapping, semantics, policy status, and next action. |
| `season_week_coverage_matrix.csv` | Week-level Sleeper coverage plus local approved NFLVerse cache inspection summary. |
| `route_field_presence_audit.csv` | Route candidate presence and deferral decision. |
| `missingness_and_zero_policy.md` | Missingness, sparse API, explicit-zero, and red-zone semantics policy. |
| `guardrail_report.md` | Guardrail proof for this review-only packet. |
| `next_dataset_handoff.md` | Follow-up instructions for a future lagged usage dataset lane. |
| `merge_safety_report.md` | Scope and path safety report. |

## Scope

Docs/CSV review-only artifacts. No runtime/app/model files. No raw shared/cache/local files.
