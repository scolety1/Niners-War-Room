# NWR Backtest V1 Snap Join Audit - 2026-06-21

Owner: Master/Main HQ

Status: GREEN for root-cause identification and a narrow builder repair.
YELLOW for overnight tuning because full historical snap-source regeneration
still needs coverage verification. This does not approve model use, private
value, hidden ranking/sort, recommendations, simulations, final draft decisions,
deployment, Mock Draft logic, `latest_candidate`, or `latest_approved`.

## Local-Only Diagnostics

Audit root:

`C:\NWR_SHARED_DATA\backtests\backtest_v1_snap_join_audit_20260621`

Local-only files:

- `snap_source_coverage_by_year_position.csv`
- `snap_join_coverage_by_year_position.csv`
- `snap_join_key_analysis.csv`
- `unmatched_snap_join_samples.csv`
- `snap_fixed_validation_summary.csv`
- `snap_join_audit_report.md`
- `audit_manifest.json`

None of these artifacts are committed.

## Root Cause

Backtest V1 requested `offense_snaps` and `offense_pct`, but the V0 expanded
feature helper dropped those columns before V1 selected them.

Flow:

1. `_snap_features()` generated `offense_snaps` and `offense_pct`.
2. `_build_expanded_features()` narrowed output to
   `IDENTITY_COLUMNS + BASELINE_NUMERIC_COLUMNS + EXPANDED_EXTRA_COLUMNS`.
3. `EXPANDED_EXTRA_COLUMNS` did not include the snap columns.
4. V1 `_select_with_defaults()` later created zero-filled `offense_snaps` and
   `offense_pct` defaults.
5. `snap_pct_missing` therefore appeared effectively universal.

This was a transformation/preservation bug, not a vendor data issue and not a
market/projection/ranking issue.

## Source Coverage

The direct scheduled snap source inspected was:

`C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\20260621_000000_nflverse_expansion_v1\snap_counts.csv`

That local scheduled file contains 2024-2025 snap rows only. The original
Backtest V1 build manifest did not warn that `snap_counts` was unavailable, so
the audit separates two concerns:

- Code bug: snap columns were dropped even when available.
- Runtime/source coverage: full historical 2018-2024 snap loading still needs
  verification when the next dataset is regenerated.

## Join Coverage

Existing Backtest V1 artifacts were built before the fix. The local audit found
almost no current V1 artifact rows with populated snap columns.

The intended join key remains:

`player_name_norm`, `position`, `recent_team`, `feature_season`

The audit did not identify team abbreviation mismatch or duplicated player name
collisions as the primary root cause. The primary issue was column loss after
the snap feature merge.

## Repair

Implemented a narrow repair in `scripts/build_backtest_dataset_v1.py`:

- compute `_snap_features()` once from `snap_counts`
- merge snap features into the V1 baseline frame
- merge snap features into the V1 clean-expanded frame
- keep the existing join keys and leakage guardrails

Focused validation with fixture snap rows confirms snap fields now survive in
both V1 baseline and V1 clean-expanded outputs.

## Backtest V1 Interpretation

Backtest V1 conclusions are provisional for snap-based features because the
published V1 run did not actually carry snap coverage through the final feature
tables.

The V1 no-snap portions still remain useful as a disciplined baseline cleanup
result, but any claim about snap-share usefulness should wait for a regenerated
snap-fixed dataset and an isolated snap ablation.

## Overnight Tuning Recommendation

Use both:

- snap-fixed variants, because the builder now preserves snap fields
- no-snap variants, because they are required controls and a safe fallback

Do not rely only on snap-fixed variants until the regenerated dataset confirms
historical snap coverage across the full feature window.

## Guardrails

- No ADP, rankings, projections, trade calculators, or market data were used.
- No vendor archive fields were used.
- `fantasy_points` and `fantasy_points_ppr` remain blocked as input features.
- No model was trained or promoted.
- No private value, rankings, recommendations, simulations, deployment, Mock
  Draft behavior, `latest_candidate`, or `latest_approved` were changed.

## Verdict

GREEN for safe builder repair and focused tests.

YELLOW for tuning readiness until full historical snap coverage is regenerated
and verified.
