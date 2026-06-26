# NWR CFBD + NFL Usage Final Reconciliation - 2026-06-24

## Verdict

GREEN.

Merged the completed NFL Usage Target Backtest branch into the CFBD-integrated `work/hq-parallel-control` branch as review-only evaluation/data-source artifacts. This reconciliation did not enable model input, did not wire app decision pages, did not modify CFBD outputs, and did not alter rankings/source-truth artifacts.

## Starting Main HEAD

`fa2d8af693e871c2bd4f8a6ab344f6be6f2e3747`

## NFL Branch HEAD

`e7c1aa564040d9c1dad61907c9f48cfc47931702`

## Merge Method

Normal merge commit:

`merge: integrate nfl usage target backtest with cfbd master`

Merge-base:

`3c06623d7dc511d2dc4db0d2131776b42d8def36`

## Conflicts

None.

## Files Integrated From NFL Branch

Integrated files are limited to:

- `docs/hq/data_sources/nfl_usage/historical_panel/`
- `docs/hq/data_sources/nfl_usage/target_backtest/`
- `scripts/build_nfl_usage_target_labels_v0.py`
- `scripts/run_nfl_usage_target_backtest_v0.py`
- `src/services/nfl_usage_target_label_service.py`
- `src/services/nfl_usage_target_backtest_service.py`
- `tests/test_nfl_usage_target_label_service.py`
- `tests/test_nfl_usage_target_backtest_service.py`

No app page, app navigation, Refresh Data UI, Settings/Data Health UI, dependency file, CFBD script/service/test, model/rank, candidate, frozen, pinned, latest, or source-truth file was changed by the merge.

## CFBD Files Preserved

CFBD identity matching artifacts under:

`docs/hq/data_sources/cfbd_identity_matching_v1_20260624/`

were preserved unchanged by the NFL merge.

CFBD status remains:

- `review_required=true`
- `model_use_allowed=false`
- `training_allowed=false`
- draft registry `approved_by_human=false`
- rows approved for model use: `0`

## NFL Usage Review-Only Status

NFL usage target/backtest artifacts remain review-only:

- `model_input_allowed=no`
- `app_wiring_allowed=no`
- raw/shared panels are referenced as ignored cache paths only
- no app decision wiring is enabled
- no active model input is enabled

Historical expansion facts:

- Feature seasons: `2018;2019;2020;2021;2022;2023`
- Target seasons: `2019;2020;2021;2022;2023;2024`
- Joined leakage-safe row count: `2,848`

Committed summary artifacts:

- Expanded target backtest result rows: `286`
- Expanded target stability summary rows: `44`
- Expanded target position summary rows: `4`
- Expanded field coverage rows: `31`
- Expanded historical panel manifest rows: `5`

## No Model Input / No App Decision Wiring

Confirmed:

- No `model_input_allowed=yes` found in NFL usage CSVs.
- No `app_wiring_allowed=yes` found in NFL usage CSVs.
- No CFBD `model_use_allowed=true`, `training_allowed=true`, or `approved_by_human=true` rows found.
- No ranking, model, source-truth, or candidate files were changed.
- No app decision pages or navigation files were changed.

## Raw / Shared / Local / Runtime Tracking

Confirmed:

- No raw nflverse downloads tracked.
- No raw CFBD downloads tracked.
- No `C:\NWR_SHARED_DATA` files tracked by this merge.
- No `local_exports` files tracked by this merge.
- No runtime JSON files tracked by this merge.

Tracked references to `C:\NWR_SHARED_DATA` in NFL usage CSV manifests are provenance strings for ignored cache locations, not tracked raw data.

## Frozen / Pinned / Latest Confirmation

Confirmed:

- Frozen board row count remains `66`.
- Pinned hash unchanged: `5780156F09FBDA61FB906715C7341DB1B6D320C8D8EFA588070F19C4C50F45CE`.
- `latest_candidate` / `latest_approved` untouched.
- No `final_board_rank` mutation.
- No Dynasty Rank mutation.
- No Candidate Rank mutation.

## Tests / Checks

Focused pytest:

- `tests/test_nfl_usage_target_label_service.py`
- `tests/test_nfl_usage_target_backtest_service.py`
- `tests/test_nfl_usage_historical_panel_service.py`
- `tests/test_cfbd_identity_matching_v1.py`
- `tests/test_cfbd_review_artifacts_v1.py`
- Result: `27 passed`

Static checks:

- Ruff on touched NFL usage / CFBD test Python files: passed
- Python compile on touched NFL usage / CFBD test Python files: passed
- `git diff --check`: passed

CSV/schema/flag validation:

- NFL usage target/backtest CSVs loaded successfully.
- NFL usage historical panel CSVs loaded successfully.
- CFBD identity matching CSVs loaded successfully.
- No model/app wiring flag violations found.

## Browser Smoke

Not run. No app behavior changed in this reconciliation; app pages/navigation were outside the merge scope.

## Final HEAD

Final HEAD will be the reconciliation report commit after this file is committed.

## Push Status

Pending at report creation time.

## Remaining Recommended Next Steps

1. Keep both CFBD and NFL usage outputs review-only until a separate explicit promotion gate approves display or model use.
2. If NFL usage fields are considered for app display later, create a dedicated app-wiring readiness gate with field-level labels and caveats.
3. If CFBD identities are considered for any player matching workflow later, require human approval of the draft identity registry first.

