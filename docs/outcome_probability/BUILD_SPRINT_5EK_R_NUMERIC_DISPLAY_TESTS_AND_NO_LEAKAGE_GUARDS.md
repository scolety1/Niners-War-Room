# Sprint 5EK-R - Numeric Display Tests And No-Leakage Guards

## Purpose

Sprint 5EK-R adds a Phase 11 static guard proving the numeric Outcome display wiring remains display-only and cannot leak into name-based joins, sorting, ranking, hidden keys, unapproved heads, or promoted artifacts.

## Preconditions

- Sprint 5EJ-R completed GREEN and committed as `a60571d`.
- Sprint 5EJ-R2 completed GREEN and committed as `dd2c12b`.
- Repo path and branch were verified before guard work.
- Expected dirty state before guard work was limited to `?? data/`.

## Files Changed

- `docs/outcome_probability/BUILD_SPRINT_5EK_R_NUMERIC_DISPLAY_TESTS_AND_NO_LEAKAGE_GUARDS.md`
- `scripts/outcome_probability/audit_phase11_numeric_outcome_display_static_guard_v1.py`

No source behavior changed in this sprint.

## Guard Added

The new static guard:

- Verifies the app-readable numeric artifact has 240 rows.
- Verifies availability counts remain 227 available and 13 unavailable.
- Verifies only approved display heads are present:
  - `qb_t12`
  - `rb_t12`
  - `rb_t24`
  - `wr_t12`
  - `wr_t24`
  - `wr_t36`
  - `te_t12`
- Verifies blocked Top 6 and unapproved labels are absent from the Rankings page.
- Verifies `src/services/player_board_score_service.py` exposes `player_id` for internal joining.
- Verifies the Rankings page calls `numeric_outcome_display_for_player(...)` with `row.get("player_id")`.
- Verifies the visible default Dynasty columns do not include `player_id`.
- Verifies the advanced raw-row display drops `player_id`.
- Verifies the private-rank calculation function contains no Outcome display logic.
- Verifies no `outcome_sort`, `hidden_outcome`, `outcome_hidden`, or numeric Outcome sort helper appears in the Rankings page.
- Verifies no promoted Outcome model artifact directory is present.

## No-Leakage Results

- Name-based numeric Outcome joins remain blocked.
- Outcome probabilities are not used for ranking score calculation.
- Outcome probabilities are not used as default sort fields.
- No hidden Outcome sort key was created.
- No Top 6 or unapproved head was displayed.
- Unavailable rows remain safe and do not display fake `0%`.

## Checks

Required checks for this sprint:

- `python tests\test_nwr_outcome_numeric_probability_display_service.py`
- `python tests\test_nwr_outcome_phase8_status_contract_service.py`
- `python tests\test_nwr_outcome_phase9_status_release_gate.py`
- `python scripts\outcome_probability\audit_phase8_non_numeric_status_static_guard_v1.py`
- `python scripts\outcome_probability\audit_phase9_outcome_status_release_gate_v1.py`
- `python scripts\outcome_probability\audit_phase11_numeric_outcome_display_static_guard_v1.py`
- `python -m py_compile scripts\outcome_probability\audit_phase11_numeric_outcome_display_static_guard_v1.py`
- `git diff --check`

`pytest` is not installed in the local environment; no package installation was performed.

## Boundaries Preserved

- No model training was performed.
- No current-player inference was created.
- No new probability generation was performed.
- No app-readable artifact was created or modified.
- No app wiring changed in this sprint.
- No ranking, sorting, hidden-key, or promoted-artifact path was created.
- No rookie files were touched.
- `data/` and `local_exports/` were not staged or committed.
- No push, deploy, release, merge, or main push occurred.

## Verdict

GREEN for 5EK-R guard coverage, pending successful checks and exact-file commit.
