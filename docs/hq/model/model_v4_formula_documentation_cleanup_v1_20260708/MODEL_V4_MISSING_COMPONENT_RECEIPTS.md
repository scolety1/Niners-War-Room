# Model v4 Missing Component Receipts / Checkpoint Map

Date: 2026-07-08

Status: `EXACT_REPLAY_BLOCKED_BY_MISSING_RECEIPTS`

## Highest Priority Missing Receipts

| Rank | Expected Name/Path | Why Needed | Dependent Component | Can Regenerate Locally? | Source Admission Needed? | Leakage Risk | Next Lane? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv` | Current board names it as upstream source for `checkpoint_review_score`, but it is absent locally. | Full board and candidate overlay | Unknown | Yes, if regenerated from inputs | High if current-only context is reused historically | Yes |
| 2 | `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` | Needed to prove `checkpoint_review_score`. | Current value checkpoint | Likely, if all upstream receipts exist | Yes | High for historical replay | Yes |
| 3 | `local_exports/model_v4/current_value/latest/current_player_value_component_rows.csv` | Needed to reconcile checkpoint score from position score, lifecycle modifier, and confidence cap. | Current value checkpoint | Likely, if upstream receipts exist | Yes | Medium | Yes |
| 4 | `local_exports/model_v4/current_value/latest/current_player_value_receipts.csv` | Needed for source trace and auditability of checkpoint generation. | Current value checkpoint | Likely, if upstream receipts exist | Yes | Medium | Yes |
| 5 | `local_exports/model_v4/current_value/latest/rb_wr_current_value_component_rows.csv` | Needed to prove RB/WR component values, weights, and contributions. | RB/WR current value | Unknown | Yes | Medium | Yes |
| 6 | `local_exports/model_v4/current_value/latest/rb_wr_current_value_receipts.csv` | Needed to trace RB/WR inputs to admitted sources. | RB/WR current value | Unknown | Yes | Medium | Yes |
| 7 | `local_exports/model_v4/current_value/latest/qb_te_current_value_component_rows.csv` | Needed to prove QB/TE component values, weights, confidence, and discipline transforms. | QB/TE current value | Unknown | Yes | Medium | Yes |
| 8 | `local_exports/model_v4/current_value/latest/qb_te_current_value_receipts.csv` | Needed to trace QB/TE inputs to admitted sources. | QB/TE current value | Unknown | Yes | Medium | Yes |
| 9 | `local_exports/model_v4/replacement_vorp/latest/*component*` and `*receipt*` files | Needed to prove NWR scoring points, first-down points, replacement ranks, and positive VORP. | Replacement/VORP | Unknown | Yes | Medium | Yes |
| 10 | `local_exports/model_v4/current_value/latest/lifecycle_archetype_component_rows.csv` | Needed to prove lifecycle modifiers. | Lifecycle modifier | Unknown | Yes | High if current age/role is reused historically | Yes |
| 11 | `local_exports/model_v4/current_value/latest/lifecycle_archetype_receipts.csv` | Needed to trace lifecycle source/status. | Lifecycle modifier | Unknown | Yes | High | Yes |
| 12 | `local_exports/model_v4/current_value/latest/confidence_missingness_receipts.csv` | Needed to prove confidence caps and missingness semantics. | Confidence cap | Unknown | Yes | Medium | Yes |
| 13 | `local_exports/model_v4/current_value/candidates/wr_qb_v2/*receipts*` | Needed only if WR/QB v2 candidate overlay is selected as the replay/promotion target. | Candidate adjustment | Unknown | Yes | Medium | Human review first |
| 14 | Historical season-by-season equivalents of all current receipts | Needed for true historical replay and accuracy benchmark. | All components | Not in this lane | Yes | Highest | Later |

## Runtime Folder Finding

The local runtime folder inspected for the current board contains:

- `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`

The following expected current receipt/checkpoint artifacts were not found in the runtime folder:

- `current_player_value_full_board_review_rows.csv`
- `current_player_value_review_rows.csv`
- `current_player_value_component_rows.csv`
- `current_player_value_receipts.csv`
- `current_player_value_warnings.csv`
- `rb_wr_current_value_review_rows.csv`
- `rb_wr_current_value_component_rows.csv`
- `rb_wr_current_value_receipts.csv`
- `qb_te_current_value_review_rows.csv`
- `qb_te_current_value_component_rows.csv`
- `qb_te_current_value_receipts.csv`
- `lifecycle_archetype_review_rows.csv`
- `lifecycle_archetype_receipts.csv`
- `confidence_missingness_review_rows.csv`
- `confidence_missingness_receipts.csv`

## Historical Replay Consequence

Because the current score cannot be reconciled from local component receipts, exact historical replay remains blocked. A historical benchmark would otherwise risk evaluating a proxy formula family rather than the displayed Model v4 board.

## Regeneration Rule

Receipt regeneration must not occur in this lane. A later backfill/source-admission lane may regenerate receipts only if it:

- Uses admitted sources.
- Preserves row-level source trace.
- Proves decision-date safety for historical seasons.
- Does not promote review-only or blocked inputs by implication.
- Separates current receipt recovery from historical receipt generation.
