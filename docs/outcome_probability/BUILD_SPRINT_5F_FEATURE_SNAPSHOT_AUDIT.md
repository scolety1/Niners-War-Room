# Build Sprint 5F - Feature Snapshot Audit

## Scope

Sprint 5F audited the narrow feature snapshots produced in Sprint 5E and documented blocker repairs for row families that failed cutoff/timestamp legality. It did not train calibrated models, create app percentage values, create player-facing probabilities, create rankings, push, or deploy.

## Readiness Verdict

`FEATURE_SNAPSHOTS_PASS_DIAGNOSTICS_ONLY`

The 35 valid `all_player_pre_week1` snapshots pass legality and integrity checks for aggregate diagnostics only. Production/app modeling remains blocked.

## Snapshot Quality Summary

| Check | Result |
| --- | --- |
| Emitted rows | 35 |
| Unique players | 35 |
| Positions covered | QB:3|RB:8|TE:4|WR:20 |
| Source seasons represented | 2024:35 |
| Unique features | 9 |
| Duplicate row IDs | 0 |
| Duplicate snapshot hashes | 0 |
| Cutoff violations | 0 |
| Forbidden feature hits | 0 |
| Same-season leakage hits | 0 |

## Feature Safety Confirmation

The emitted snapshots use only:

- age/DOB metadata
- experience
- prior games played
- prior first-down production
- prior receptions
- prior rushing yards
- prior receiving yards
- prior passing yards

The audit found no feature-name evidence of ADP, rankings, projections, market/trade data, legacy private score, target labels, public fantasy totals, same-season final stats, or label supplement sources.

## Missingness Summary

The emitted packet has full coverage for the narrow features that were exported. Optional sources stayed excluded rather than zero-filled.

See `feature_missingness_by_family.csv` for feature-level coverage.

## Offseason Carryover Blocker

- Source date found: `2026-05-15`
- Cutoff: `2026-02-15`
- Blocker: `blocked_by_source_after_cutoff`
- Secondary blockers: `needs_earlier_source_snapshot`, `needs_source_availability_manifest`

Safest repair path: obtain or reconstruct a source snapshot available on/before `YYYY-02-15`. Do not move the cutoff later merely to fit the file unless HQ explicitly approves a new row-family definition.

## Rookie Post-Draft Blocker

- Cutoff: `YYYY-05-01`
- Draft-capital manifest collected at: `2026-05-25T23:45:00+00:00`
- Blocker: `blocked_by_manifest_after_cutoff`
- Secondary blockers: `needs_draft_manifest_timestamp_policy`, `needs_cutoff_policy_review`, `manual_review_required`

Safest repair path: approve a post-draft cutoff policy matching actual draft-result availability, or provide an on/before-cutoff manifest. Do not admit draft capital without manifest/cutoff approval.

## Internal Experiment Allowance

`allowed_aggregate_snapshot_diagnostics_only`

A later pass may run aggregate snapshot diagnostics only. Do not run calibrated models, toy models, app probabilities, player-facing probabilities, or rankings from this packet without HQ approval.

## Local Exports

Local-only outputs were written to:

`C:\Dev\niners-war-room\local_exports\outcome_probability\sprint_5f_feature_snapshot_audit`

- `feature_snapshot_quality_report.csv`
- `feature_missingness_by_family.csv`
- `feature_legality_audit_summary.csv`
- `snapshot_hash_integrity_report.csv`
- `offseason_carryover_blocker_report.csv`
- `rookie_post_draft_blocker_report.csv`
- `internal_experiment_allowance.csv`
- `README_SPRINT_5F.md`

## Remaining Blockers Before True Calibrated Modeling

- broader legal rows and more seasons
- repaired cutoff/timestamp policy for blocked row families
- optional source registration if richer feature sets are needed
- out-of-time validation plan
- confidence gates
- app display gates
- final leakage audit
