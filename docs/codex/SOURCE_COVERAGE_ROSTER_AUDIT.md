# Source Coverage Roster Audit

Date: 2026-05-12

Active pack: `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

Audit artifacts:

- `local_exports/source_coverage_global_summary.csv`
- `local_exports/source_coverage_roster_top_assets_audit.csv`
- `local_exports/source_coverage_roster_top_assets_bucket_gaps.csv`

## Result

The source-coverage gate is stricter after this pass. The audit now treats weak role/usage and injury warnings from the stats-first normalized features as actual coverage weakness instead of marking those buckets fully ready.

No formula weights changed. Rankings remain review-only.

## What Is Clean

- Identity coverage is ready for the Niners roster and top league assets.
- Age/bio coverage is ready.
- League-rank governance coverage is ready.
- Market/liquidity gaps are optional and accepted for now; confidence penalties remain visible.
- Projection gaps are accepted for pre-declaration roster review, but still visible.

## Material Blockers

### 1. Role/Usage Is Critical And Currently Proxy-Level

All reviewed Niners roster players and top league assets carry `missing_participation_proxy`. The app has enough data to create a role proxy, but not enough to treat role/usage as fully trusted.

Impact: this can materially move Model Value, Keep Priority, Cut Risk, WR/TE route-role reads, RB workload reads, and QB start/security confidence.

Next action: import or derive stronger participation/route/snap/depth-chart role inputs, then regenerate the stats-first preview outputs.

### 2. Young Bridge Players With No NFL Production History Need Review

The following Niners young players have critical production review gaps because the model is relying on young-player bridge/prospect prior rather than real NFL production:

- Luther Burden
- Kaleb Johnson
- Jayden Higgins
- Oronde Gadsden

Impact: these rows are not safe as final model truth. They can still be useful as audit hypotheses, but not decision-ready rankings.

Next action: keep these players in young-player review, verify rookie/prospect prior inputs, and require receipts before using them in roster decisions.

### 3. Injury Review Gaps Are Optional But Not Solved

Some players have derived injury durability with `no_injury_report_rows`. That is now shown as an optional review gap rather than clean ready coverage.

Impact: injury does not block roster review by itself, but it should lower confidence and stay visible.

Next action: import a stronger public injury snapshot or add audited acceptance rows only when comfortable keeping the confidence penalty.

## Non-Blocking Optional Gaps

Market/liquidity remains missing or neutral for many players. This is accepted for private Model Value because public market data should not drive private football value. It still limits trade-edge interpretation.

Projection gaps are accepted for this pre-declaration pass, but they remain visible and should not be confused with real projection confidence.

## Patch Made

`src/services/source_coverage_audit_service.py` now checks normalized-feature warnings when classifying stats-first source coverage:

- `missing_participation_proxy` or `missing_snap_counts` marks role/usage as proxy-level review coverage.
- `missing_role_usage_features` marks role/usage as missing.
- `no_injury_report_rows` or `no_activity_rows` marks injury as optional review coverage.
- `missing_injury_features` marks injury as missing.

## Decision Status

Do not mark roster decisions ready yet. The current blocker is not identity or stale output; it is source strength. The next accuracy work should focus on improving role/usage coverage and reviewing young bridge production priors.
