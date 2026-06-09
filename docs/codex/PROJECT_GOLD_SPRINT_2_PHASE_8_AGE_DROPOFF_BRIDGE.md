# Project Gold Sprint 2 / Phase 8: Age Dropoff Bridge

Generated: 2026-05-14

## Status

Age/dropoff is now a first-class auditable model layer in the regenerated stats-first preview. Rankings remain review-only.

Before this pass, `age_curve` existed as a model feature, but the base normalization path treated age as a neutral/default 50 unless the preview generator patched it later. That meant age could affect preview scores without being clearly visible in the normalized feature receipts. This pass makes age visible in normalized rows, source coverage, and receipts.

## What Changed

- Added a reusable age curve service.
- Imported/derived raw age from trusted public identity/player bio sources:
  - Sleeper player universe `birth_date` / `age`
  - nflverse player bio `birth_date`
- Added position-specific age buckets:
  - `prime_window`
  - `mild_decline`
  - `cliff_risk_window`
  - `age_not_available`
- Added normalized row fields:
  - `age_raw`
  - `age_bucket`
  - `age_warning`
  - `age_source_status`
  - `age_interaction_flags`
- Updated age receipts so `age_curve` shows raw age, bucket, warning, source status, and imputation status.
- Updated source coverage so age/bio is ready only when age is actually derived, not merely because `age_curve` has a number.

## Interaction Flags

The age layer now emits review flags where age interacts with position-specific risk:

- `rb_age_injury_workload_fragility`
- `wr_age_target_route_decline`
- `qb_rushing_age_or_start_security_decline`
- `te_late_prime_no_premium_route_dependency`

These flags do not tune formulas by themselves. They make the age/dropoff risk visible for audit and receipt review.

## Audit Counts

| item | count |
|---|---:|
| age audit rows | 1,039 |
| derived real age rows | 1,039 |
| neutral age rows | 0 |
| prime window | 656 |
| mild decline | 220 |
| cliff-risk window | 163 |
| age interaction rows | 295 |

## Artifacts

- Audit folder: `local_exports/model_audits/sprint2_phase8_age_dropoff_20260514`
- Age audit: `age_dropoff_audit.csv`
- Age summary: `age_dropoff_summary.csv`
- Manifest: `age_dropoff_manifest.json`

## Remaining Concern

Age is now visible and derived, but this does not solve the broader model-trust problem by itself. Role/usage still has large proxy coverage gaps from Phase 7 Audit, especially routes and participation. Keep rankings review-only until those gaps are resolved or explicitly accepted.
