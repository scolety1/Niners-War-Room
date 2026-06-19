# QA/Data Hygiene Audit QD2

## Executive verdict

QD2 verdict: `YELLOW`.

The six broad `outcome` failures are not true constrained-prototype code blockers. They are `model_v4` local-export dependency failures and empty-context assertion failures from ignored/generated artifacts that are missing in this worktree.

5BF/5BG constrained prototype readiness: not blocked by these six failures.

Broad Outcome release readiness: blocked from GREEN until the broad `python -m pytest tests -k "outcome" -q` command can run in a proper test environment and either required local artifacts are restored/regenerated or the local-export-dependent tests are isolated with an HQ-approved fixture/skip strategy.

No model tuning, app display wiring, rankings/sorting changes, promoted outputs, rookie framework edits, package installs, `data/` commits, or `local_exports/` commits were made.

## Evidence sources

Static sources reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BG_CONSTRAINED_ORDINAL_PROTOTYPE_ADVERSARIAL_AUDIT.md`
- `tests/test_model_v4_historical_similarity_service.py`
- `tests/test_model_v4_rookie_outcome_label_service.py`
- `tests/test_model_v4_startup_slot_simulator_service.py`
- `src/services/model_v4_historical_rookie_tuning_service.py`
- `src/services/model_v4_rookie_outcome_label_service.py`
- `src/services/model_v4_historical_similarity_service.py`
- `src/services/model_v4_startup_slot_simulator_service.py`

The 5BG audit records `136 passed, 6 failed, 1509 deselected` for `python -m pytest tests -k "outcome" -q` and explicitly classifies those failures as existing `model_v4` local-export dependency failures, not 5BF blockers.

## Per-failure inventory

| Failing test | Missing artifacts required | Classification | 5BF/5BG constrained prototype readiness | Broad Outcome release readiness | Recommended remedy |
| --- | --- | --- | --- | --- | --- |
| `tests/test_model_v4_historical_similarity_service.py::test_historical_similarity_missing_outcomes_are_unknown_not_misses` | Primary missing input: `local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv`. Historical tuning rows are present at `local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv`. | Empty fixture/context assertion. The service returns empty rows when required CSVs are absent, so assertions looking for `unknown=` and `missing_outcome_unknown_not_miss` fail. | No effect. This is outside the constrained ordinal prototype path. | Blocks broad GREEN because the broad outcome suite cannot pass without deterministic context. | Local artifact regeneration instruction or HQ-approved fixture strategy. A skip/xfail guard is acceptable only after HQ approves test-hygiene patching. |
| `tests/test_model_v4_rookie_outcome_label_service.py::test_rookie_outcome_labels_use_rotowire_stats_without_changing_scores` | `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`; next dependency also missing: `local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv`. | Local artifact dependency. Hard `FileNotFoundError` on missing historical backtest matrix. | No effect. This is `model_v4` rookie outcome-label code, not 5BF/5BG prototype code. | Blocks broad GREEN. | Regenerate/restore ignored local exports, or create HQ-approved deterministic fixtures. No model tuning. |
| `tests/test_model_v4_rookie_outcome_label_service.py::test_rookie_outcome_label_writer_exports_expected_files` | `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`; next dependency also missing: `local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv`. | Local artifact dependency. Writer calls the same label builder and hard-fails before writing to `tmp_path`. | No effect. | Blocks broad GREEN. | Regenerate/restore ignored local exports, or fixture-backed writer test after HQ approval. |
| `tests/test_model_v4_rookie_outcome_label_service.py::test_historical_tuning_report_uses_full_outcome_labels` | `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`. Present supporting output: `local_exports/model_v4/historical_rookie_outcomes/latest/historical_rookie_outcome_labels.csv`. | Local artifact dependency. Historical tuning hard-opens the matrix; outcomes file can be absent without hard fail, but the matrix cannot. | No effect. | Blocks broad GREEN. | Restore/regenerate the evidence matrix locally, or move to a committed sample fixture if HQ approves. |
| `tests/test_model_v4_rookie_outcome_label_service.py::test_historical_tuning_summary_separates_universe_and_hit_strictness` | `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`. Present supporting output: `local_exports/model_v4/historical_rookie_outcomes/latest/historical_rookie_outcome_labels.csv`. | Local artifact dependency. Same missing matrix as the previous tuning test. | No effect. | Blocks broad GREEN. | Same as above: local artifact regeneration or HQ-approved fixture strategy. |
| `tests/test_model_v4_startup_slot_simulator_service.py::test_outcome_buckets_are_context_only_and_honest_about_samples` | Missing inputs include `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv`, `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`, `local_exports/model_v4/rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv`, `local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv`, `local_exports/model_v4/prospect_value/latest/prospect_value_component_rows.csv`, `local_exports/model_v4/prospect_value/latest/prospect_value_receipts.csv`, `local_exports/model_v4/decision_calibration/latest/niners_roster_state_review.csv`, `local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv`, `local_exports/model_v4/trade_review/latest/trade_away_candidate_review_rows.csv`, and `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv`. Historical tuning rows are present. | Empty fixture/context assertion. The simulator returns empty `bucket_rows` because many upstream review-only local exports are absent. | No effect. | Blocks broad GREEN. | Local artifact regeneration instruction for the model_v4 review stack, or HQ-approved fixture strategy for startup slot context. Skip/xfail only if HQ decides local-only artifacts should not be required for broad outcome-keyword checks. |

## Missing artifact summary

Confirmed missing:

- `local_exports/model_v4/evidence_matrices/latest/historical_rookie_backtest_feature_matrix.csv`
- `local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv`
- `local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv`
- `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv`
- `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- `local_exports/model_v4/rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv`
- `local_exports/model_v4/prospect_value/latest/prospect_value_component_rows.csv`
- `local_exports/model_v4/prospect_value/latest/prospect_value_receipts.csv`
- `local_exports/model_v4/decision_calibration/latest/niners_roster_state_review.csv`
- `local_exports/model_v4/decision_pressure/latest/cut_keep_pressure_review_rows.csv`
- `local_exports/model_v4/trade_review/latest/trade_away_candidate_review_rows.csv`
- `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv`

Confirmed present:

- `local_exports/model_v4/historical_rookie_outcomes/latest/historical_rookie_outcome_labels.csv`
- `local_exports/model_v4/historical_rookie_tuning/latest/historical_rookie_tuning_board_rows.csv`

## Recommendations

- Keep QD2 as a docs note until HQ chooses a remediation path.
- For local development, restore or regenerate the ignored `model_v4` local-export stack needed by these tests.
- For CI-like or broad-suite hygiene, prefer HQ-approved fixture-backed tests over relying on ignored local exports.
- If fixtures are not appropriate, add explicit skip/xfail guards for missing ignored local artifacts only after HQ approves a test-hygiene patch.
- Do not solve these by model tuning, app wiring, promoted outputs, ranking/sorting changes, or committing generated `local_exports/` artifacts.

## Checks run

- `git status --short`
- `git diff -- docs/hq/parallel_lanes/QA_DATA_HYGIENE_AUDIT_QD1.md`
- `git diff --check`
- `git diff --cached --name-only`
- `git commit -m "Document QA data hygiene artifact risk"`
- Static `Select-String` reads against the 5BG audit, failing test files, and relevant service constants/read behavior.
- `Test-Path` existence inventory for required `local_exports/model_v4` paths.

Not run:

- `python -m pytest tests -k "outcome" -q` for QD2, because QD1 confirmed local Python runtimes do not have `pytest` and QD2 forbids installing packages.

## Files changed

- Committed in QD1: `docs/hq/parallel_lanes/QA_DATA_HYGIENE_AUDIT_QD1.md`
- Created for QD2: `docs/hq/parallel_lanes/QA_DATA_HYGIENE_AUDIT_QD2.md`

## Final git status

Expected after QD2 report creation:

```text
?? data/
?? docs/hq/parallel_lanes/QA_DATA_HYGIENE_AUDIT_QD2.md
```

`data/` remains untouched, unstaged, and uncommitted. `local_exports/` remains untouched, unstaged, and uncommitted. QD2 remains uncommitted for HQ review.
