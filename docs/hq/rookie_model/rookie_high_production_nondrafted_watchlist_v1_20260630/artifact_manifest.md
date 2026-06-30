# Artifact Manifest

All artifacts in this packet are review-only. They do not edit source truth, do not patch the original entry-status artifact, and do not approve training or model use.

## Input Artifacts Used

- `docs/hq/rookie_model/rookie_udfa_source_policy_confirmation_pilot_v1_20260630/`
- `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv`
- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_production_review.csv`
- `docs/hq/rookie_model/rookie_model_historical_cfbd_and_outcome_backfill_policy_20260630/cfbd_identity_candidate_audit.csv`

## Source Policy Status

- Parent UDFA pilot reviewed 2514 likely rows and proposed 0 confirmed UDFA candidates.
- Approved CFBD production/context joined to likely non-drafted candidates is unavailable.
- Current CFBD production/context artifacts remain review-only and identity-review-required.
- Watchlist population is therefore blocked and candidate output is header-only.

## Output Artifacts

| Artifact | Row Count | Purpose |
|---|---:|---|
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/artifact_manifest.md` | n/a | Packet manifest and source-policy status. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/high_production_nondrafted_policy.md` | n/a | Defines review-only watchlist policy. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/high_production_thresholds.md` | n/a | Future conservative threshold rules and current availability decision. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/high_production_nondrafted_candidate_watchlist.csv` | 0 | Candidate watchlist; header-only because approved production join is unavailable. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/nondrafted_ignore_policy_summary.csv` | 100 | Class/position ignored-or-blocked summary. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/identity_risk_blockers.csv` | 0 | High-production candidates blocked by identity risk; header-only because no candidates surfaced. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/rookie_outcome_handoff_watchlist_update.md` | n/a | Outcome handoff limits. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/final_watchlist_recommendation.md` | n/a | Verdict, counts, and required merge order. |
| `docs/hq/rookie_model/rookie_high_production_nondrafted_watchlist_v1_20260630/merge_safety_report.md` | n/a | Guardrail and command evidence report. |

## What This Packet Does Not Approve

- No conversion from `likely_udfa_needs_review` to `confirmed_udfa`.
- No training, tuning, probabilities, app wiring, Gate F release, Gate G release, or Rankings wiring.
- No fake round 8, draft round 0, draft pick 0, or missing-as-zero logic.
