# NWR Overnight Model Tune V0 Readiness - 2026-06-21

Owner: Master/Main HQ

Status: YELLOW readiness. The scaffold, feature registry, blocked-field guards,
checkpointing, and dry run are in place. Full overnight tuning has not been
started. No tuned model is approved or promoted.

## Scope

This is a local-only historical backtest/tuning scaffold. It does not approve
private value, rankings, hidden sort, Mock Draft behavior, simulations, final
draft advice, deployment, `latest_candidate`, or `latest_approved`.

Local-only output root:

`C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v0_20260621`

Repo scaffold files:

- `scripts/build_overnight_tune_dataset_v0.py`
- `scripts/run_overnight_tune_v0.py`
- `tests/test_overnight_tune_v0.py`

## Readiness Status

YELLOW, not GREEN, because sklearn is not installed in the current runtime and
the current Backtest V1 artifact was built before the snap-count repair. The
runner falls back to numpy ridge and the snap-fixed variant is planned, but it
requires a regenerated snap-fixed dataset before any full tuning claim.

The scaffold supports:

- rolling-origin evaluation for 2021-2025
- QB, RB, WR, TE
- per-position feature sets
- safe baseline, expanded, no-snap, and snap-fixed variant plans
- isolated vendor challenger plans
- sklearn model hooks when local-only sklearn is available
- numpy ridge fallback when sklearn is unavailable
- time-budget controls
- checkpointing and resume
- blocked-field scanning before fitting
- per-position winner reports
- stability metrics by evaluation year

## Feature Families

Prepared feature-family labels:

- `SAFE_BASELINE`
- `SAFE_EXPANDED`
- `SAFE_NO_SNAP`
- `SAFE_SNAP_FIXED`
- `YELLOW_CHALLENGER`
- `VENDOR_YELLOW_CHALLENGER`
- `BLOCKED`

Variant-plan summary:

- `SAFE_BASELINE`: ready
- `SAFE_EXPANDED`: ready
- `SAFE_NO_SNAP`: ready
- `SAFE_SNAP_FIXED`: planned, not ready from current artifact
- `VENDOR_YELLOW_CHALLENGER`: planned isolated research only

## Snap Audit Impact

The snap audit repair is present in code, but the current V1 artifact still has
near-zero populated snap coverage:

- QB: 0 populated snap rows
- RB: 1 populated snap row
- TE: 0 populated snap rows
- WR: 2 populated snap rows

Therefore:

- no-snap variants are required controls for overnight tuning
- snap-fixed variants should be included only after regenerating the V1 dataset
  with the repaired builder and verifying historical snap coverage
- Backtest V1 conclusions involving snap share remain provisional

## Vendor Challenger Status

Vendor archive root is present:

`C:\NWR_SHARED_DATA\vendor_archive_recovery\rotowire_fantasypros_stats_organized_20260621_v2`

Vendor variants are scaffolded only as `VENDOR_YELLOW_CHALLENGER` research
plans. They are not joined into safe variants and are not eligible for private
value, rankings, Mock Draft, simulations, or final advice.

Prioritized vendor challenger families:

- RotoWire receiving route metrics
- RotoWire red-zone usage
- RotoWire rushing advanced factual metrics
- FantasyPros factual non-ranking metrics only

Vendor rank/rating/score fields remain blocked pending definition and license
review.

## Blocked Fields

The scaffold blocks ADP, ECR, rankings, projections, trade values/calculators,
market values, `fantasy_points`, `fantasy_points_ppr`, private value fields,
hidden sort fields, FantasyPros `RK`, FantasyPros `RTG`, RotoWire QBR/rating,
and vendor rank/rating/score aggregates without clear definitions.

The dry-run runner scans planned feature columns before fitting. Tests confirm
blocked vendor rank-like fields are rejected.

## Dry-Run Result

Dry run completed locally with numpy ridge fallback.

Local dry-run files:

- `feature_registry_v0.csv`
- `blocked_field_registry_v0.csv`
- `dataset_variant_plan_v0.csv`
- `dry_run_predictions.csv`
- `dry_run_metrics_by_position.csv`
- `dry_run_metrics_by_year.csv`
- `dry_run_winner_report.csv`
- `dry_run_manifest.json`
- `checkpoints\dry_run_checkpoint.json`
- `OVERNIGHT_TUNE_V0_DRY_RUN_REPORT.md`

Dry-run scope:

- variants: `safe_baseline`, `safe_expanded`, `safe_no_snap`
- positions: QB, RB, WR, TE
- model: `numpy_ridge`
- prediction rows: 2,814
- position-metric rows: 12
- year-metric rows: 24

sklearn status:

- unavailable in current runtime
- fallback used: `numpy_ridge`

## Metric Priority

Winner reports are ordered by:

1. Top-N hit rate
2. Stability across years
3. Spearman / ranking quality
4. MAE / RMSE
5. Simplicity and leakage safety

Stability metrics include years beating baseline, yearly Top-N improvement
variance, worst-year drawdown, median yearly improvement, and one-lucky-season
flagging.

## Later Overnight Command

Do not run this until Tim explicitly starts the overnight tune and confirms the
preflight state.

Recommended later command:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\run_overnight_tune_v0.py --full-run --confirm-full-run --dataset-root 'C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v0_20260621' --output-root 'C:\NWR_SHARED_DATA\backtests\overnight_model_tune_v0_20260621' --positions QB RB WR TE --time-budget-minutes 480 --resume
```

Before running snap-fixed variants, regenerate the Backtest V1 dataset with the
snap repair and rebuild the tune registry.

## Stop Conditions

Stop if any of the following occurs:

- branch mismatch
- dirty repo before starting the full tune
- `latest_candidate` or `latest_approved` changes
- pinned snapshot changes
- blocked field scan fails
- raw vendor data becomes tracked
- `C:\NWR_SHARED_DATA` contents become tracked
- vendor challenger fields leak into safe variants
- sklearn/local tooling install mutates repo dependency files
- full tuning attempts to promote a model automatically

## Validation

Completed:

- `pytest tests/test_overnight_tune_v0.py`: passed
- `ruff check scripts/build_overnight_tune_dataset_v0.py scripts/run_overnight_tune_v0.py tests/test_overnight_tune_v0.py`: passed
- local-only dry run: passed

Remaining before full tuning:

- regenerate snap-fixed V1 artifact if snap variants are required
- optionally create a local-only sklearn environment under
  `C:\NWR_SHARED_DATA\tool_envs\overnight_tune_v0`
- rerun preflight guard checks

## Verdict

YELLOW for overnight tuning readiness.

GREEN for scaffold creation, blocked-field guards, local-only dry run, and
safe documentation.
