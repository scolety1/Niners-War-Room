# Sprint 5CK-R: 2019 QB Source/Target Position Mismatch Blocker Resolution

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_A_ACCEPTED_EXCLUDED_BLOCKER`

Sprint type: `BLOCKER_RESOLUTION_NO_REPAIR_NO_MODELING_NO_RELEASE`

## 1. Scope

Sprint 5CK-R investigated the single non-missing-label blocker that stopped the consolidated 2010-2019 historical readiness audit:

`blocked_source_target_position_mismatch`

This sprint used local files only. It did not train models, create probabilities, create exact percentages, create coarse bands, create app-readable outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie files, edit `data/`, edit raw source data, or create promoted artifacts.

## 2. Evidence Sources

Committed sources searched:

- `docs/outcome_probability/BUILD_SPRINT_5BV_LOCAL_ONLY_2018_2019_HISTORICAL_FEATURE_LABEL_REBUILD_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BW_5BV_HISTORICAL_FEATURE_LABEL_REBUILD_ADVERSARIAL_AUDIT.md`
- `scripts/outcome_probability/build_sprint_5bv_2018_2019_historical_feature_label_rebuild.py`
- later historical rebuild scripts that share the same source/target mismatch guard

Local-only sources inspected:

- `local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/blocked_historical_2018_2019_rows.csv`
- `local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/historical_2018_2019_feature_snapshots.csv`
- `local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/historical_2018_2019_outcome_labels.csv`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Created local-only 5CK-R evidence export:

`local_exports/outcome_probability/sprint_5ck_r_2019_qb_source_target_position_mismatch_blocker_resolution/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5ck_r.json` | exact accepted blocker metadata and release-blocker flags | no |
| `accepted_excluded_blocker.csv` | one-row accepted blocker evidence | no |
| `README_SPRINT_5CK_R.md` | local evidence summary | no |

## 3. Exact Blocker Row

The blocked row is exactly:

| Field | Value |
| --- | --- |
| Source package | `5BV` |
| Source file | `blocked_historical_2018_2019_rows.csv` |
| Player ID | `00-0033357` |
| Player | Taysom Hill |
| Feature source season | 2018 |
| Target season | 2019 |
| Source team | NO |
| Target team | NO |
| Source position | QB |
| Source position group | QB |
| Target position | TE |
| Target position group | TE |
| Block reason | `blocked_source_target_position_mismatch` |
| Release impact | `blocked_not_app_readable` |

This is exactly one row and exactly one non-missing-label block reason.

## 4. Classification Fields

The 5BV builder creates the blocker in `block_reason_for(source, target)`.

The fields used to classify this mismatch are:

- target aggregate exists for the same `player_id`
- `source.position`
- `target.position`
- membership of both positions in `MODELED_POSITIONS`
- equality check between `source.position` and `target.position`

The row reaches the mismatch branch because:

- source aggregate position is `QB`
- target aggregate position is `TE`
- both positions are modeled positions
- source and target positions are not equal

Required source fields were not the reason for this block.

## 5. Row Exclusion Result

The Taysom Hill row is excluded from usable 5BV feature/label rows.

The 5BV feature export contains no emitted usable row for `player_id=00-0033357`.

The 5BV label export contains no emitted usable row for `player_id=00-0033357`.

The row remains only in the local-only blocked-row table with `app_readable=no` behavior inherited from the package quarantine.

## 6. Repair Assessment

No deterministic repair is recommended in 5CK-R.

This row is not a blank-position repair case and not a raw-data duplicate case. The local source evidence shows a real source/target position transition from 2018 `QB` to 2019 `TE` for the same player ID. Repairing it would require choosing whether to model the player as the source position, the target position, or a special multi-position case. That would be a modeling policy decision, not a source-safe repair.

Because the row is already excluded from usable model rows, it does not contaminate future feature/label rows, app outputs, rankings, hidden sort keys, or promoted artifacts.

## 7. Accepted-Blocker Contract For 5CK-R2

5CK-R2 may accept exactly one non-missing-label blocker:

| Player ID | Player | Source season | Target season | Source position | Target position | Accepted reason |
| --- | --- | ---: | ---: | --- | --- | --- |
| `00-0033357` | Taysom Hill | 2018 | 2019 | QB | TE | `blocked_source_target_position_mismatch` |

5CK-R2 must fail or stop if:

- any additional non-missing-label blocker appears
- this blocker count is not exactly one
- the player ID, player name, source season, target season, source position, target position, or reason differs
- the row appears in usable feature/label rows
- any app-readable, ranking, sorting, hidden-key, probability, band, model-training, or promoted artifact path is created

## 8. Verdict

5CK-R verdict: `GREEN-A`.

This is an accepted excluded blocker, not a repaired row.

5CK-R2 is approved to run next after this 5CK-R doc is committed.

## 9. Release Stance

Model training remains blocked.

Probabilities remain blocked.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

No app-readable probability, band, or status output was created.

## 10. Checks

Checks run:

- local-only blocker inspection completed
- `git diff --check` passed

No Python file was created or changed for 5CK-R, so `python -m py_compile` and Ruff are not required. Pytest is not required because no code or tests changed.
