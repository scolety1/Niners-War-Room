# Sprint 5EL-R - Static Audit And Human Review Sample

## Purpose

Sprint 5EL-R audits the implemented Phase 11 numeric Outcome display wiring and records a human-review sample without creating new model outputs, current-player inference, promoted artifacts, or local export files.

## Preconditions

- Sprint 5EJ-R committed GREEN as `a60571d`.
- Sprint 5EJ-R2 committed GREEN as `dd2c12b`.
- Sprint 5EK-R committed GREEN as `f395dec`.
- Repo path and branch were verified before audit work.
- Expected dirty state before audit work was limited to `?? data/`.

## Files Changed

- `docs/outcome_probability/BUILD_SPRINT_5EL_R_STATIC_AUDIT_AND_HUMAN_REVIEW_SAMPLE.md`

No source, app, test, artifact, ranking, or sorting file changed in this sprint.

## Artifact Audit

Audited app-readable artifact:

- `app/generated/outcome_probability/numeric_outcome_display_v1.csv`

Results:

- Total rows: 240
- Available rows: 227
- Unavailable rows: 13
- Position counts:
  - QB: 28
  - RB: 79
  - WR: 93
  - TE: 32
  - K: 8

Approved display-head nonblank counts:

- `qb_t12`: 28
- `rb_t12`: 76
- `rb_t24`: 76
- `wr_t12`: 91
- `wr_t24`: 91
- `wr_t36`: 91
- `te_t12`: 32

No blocked Top 6, unapproved, sorting, hidden-key, market, trade, projection, or promoted artifact fields were found in the artifact contract.

## Display Head Verification

The Rankings page consumes approved display heads through:

- `APPROVED_NUMERIC_OUTCOME_HEADS`
- `numeric_outcome_column_labels()`

Displayed heads remain limited to:

- `qb_t12` -> `QB T12`
- `rb_t12` -> `RB T12`
- `rb_t24` -> `RB T24`
- `wr_t12` -> `WR T12`
- `wr_t24` -> `WR T24`
- `wr_t36` -> `WR T36`
- `te_t12` -> `TE T12`

Top 6, caution/deferred, and blocked heads do not appear in the Rankings display path.

## Join Verification

The numeric display path joins by `player_id` only:

- `src/services/player_board_score_service.py` exposes `player_id` in the internal Rankings row dictionaries.
- `app/pages/05_rankings.py` passes `row.get("player_id")` to `numeric_outcome_display_for_player(...)`.
- No player-name, team, position, or display-label join was introduced.

`player_id` remains internal-only:

- It is not in `DEFAULT_DYNASTY_COLUMNS`.
- It is not an Outcome display column.
- The advanced raw-row expander drops `player_id` before display.

## Sorting, Ranking, Hidden-Key Verification

The existing private-rank calculation remains unchanged:

- Rank calculation uses `private_score`.
- Name is used only as the existing tie-breaker inside `_assign_valid_private_ranks(...)`.
- Outcome percentages are not used for score, rank, default sort, filters, league-rank movement, player-card behavior, or hidden sort keys.

The 5EK-R static guard returned GREEN for:

- `join_key=player_id_only`
- `top6_displayed=false`
- `name_based_join=false`
- `rank_sort_hidden_keys_created=false`
- `promoted_artifacts_created=false`

## Human Review Sample

No local export was created for this sample. The sample below was read directly from the committed app-readable artifact for audit documentation.

| Position | Player | player_id | Display values |
| --- | --- | --- | --- |
| QB | Josh Allen | `4984` | `qb_t12=82%` |
| RB | Bijan Robinson | `9509` | `rb_t12=67%`, `rb_t24=84%` |
| WR | Puka Nacua | `9493` | `wr_t12=65%`, `wr_t24=86%`, `wr_t36=93%` |
| TE | Trey McBride | `8130` | `te_t12=85%` |
| WR unavailable | Brandon Aiyuk | `6803` | `under_review`, no fake `0%` |

Human-review focus before release approval:

- Confirm each displayed value is position-relevant only.
- Confirm unavailable rows display safe unavailable/review language rather than fake numeric certainty.
- Confirm no Top 6 or unapproved head appears in the table.
- Confirm displayed percentages do not change sort order.

## Checks

Required checks for this sprint:

- `python tests\test_nwr_outcome_numeric_probability_display_service.py`
- `python tests\test_nwr_outcome_phase8_status_contract_service.py`
- `python tests\test_nwr_outcome_phase9_status_release_gate.py`
- `python scripts\outcome_probability\audit_phase8_non_numeric_status_static_guard_v1.py`
- `python scripts\outcome_probability\audit_phase9_outcome_status_release_gate_v1.py`
- `python scripts\outcome_probability\audit_phase11_numeric_outcome_display_static_guard_v1.py`
- `git diff --check`

## Boundaries Preserved

- No model training was performed.
- No current-player inference was created.
- No new probability generation was performed.
- No app-readable artifact was created or modified.
- No app wiring changed in this sprint.
- No sorting, ranking, hidden-key, or promoted-artifact path was created.
- No rookie files were touched.
- `data/` and `local_exports/` were not staged or committed.
- No push, deploy, release, merge, or main push occurred.

## Verdict

GREEN for static audit and human-review sample.
