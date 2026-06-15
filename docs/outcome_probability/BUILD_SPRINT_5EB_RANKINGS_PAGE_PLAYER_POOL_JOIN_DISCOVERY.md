# Sprint 5EB - Rankings Page Player Pool Join Discovery

## Purpose

Sprint 5EB discovers how the Rankings page defines its player pool and which stable identity key should be used for future Outcome probability attachment.

This sprint is read-only discovery plus documentation and one audit script. It does not mutate data, edit app/source files, create probabilities, create app-readable outputs, change rankings/sorting, create hidden sort keys, create promoted artifacts, push, deploy, or release.

## Files Reviewed

| Area | File | Finding |
| --- | --- | --- |
| Rankings page | `app/pages/05_rankings.py` | Rankings renders `formula_rows` from `_load_formula_board(...)`, which calls `build_player_board_score_rows(...)`. Outcome columns currently render placeholders only. |
| Rankings pool builder | `src/services/player_board_score_service.py` | Builds current Rankings rows from active data-pack model outputs plus roster, official ranking, market display context, and current full-board value rows. |
| Full-board value service | `src/services/full_player_board_value_service.py` | Defines `DEFAULT_FULL_PLAYER_BOARD_ROWS` and the current full-board row contract including `player_id`, `player_name`, `position`, `pool_status`, and rookie/availability flags. |

## Local Evidence Export

Local-only evidence was written under:

`local_exports/outcome_probability/phase10_numeric_probability_display_runway/sprint_5eb_rankings_pool_join_discovery/`

Files:

- `rankings_pool_join_discovery_summary.json`
- `rankings_pool_join_discovery_rows.csv`

These exports are local-only evidence and are not app-readable production artifacts. They must not be committed.

## Player Pool Discovery

The Rankings page player pool is the same pool used by `build_player_board_score_rows(...)` in the app. The page does not define a separate Outcome universe.

Local audit note:

- `DEFAULT_DATA_PACK` points to `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`.
- That local active data-pack path was not present in this worktree during the audit, so the app builder returned zero rows in this local command-line context.
- The current full-board review export used by the Rankings page as the current value source was present at `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`.
- The audit used that full-board review export as read-only evidence for the current board row contract.

Observed full-board row coverage:

| Metric | Count |
| --- | ---: |
| Total rows | 240 |
| QB rows | 28 |
| RB rows | 79 |
| WR rows | 93 |
| TE rows | 32 |
| K rows | 8 |
| My Team rows | 24 |
| Other Team rows | 216 |
| Rookie rows | 0 |
| Missing `player_id` rows | 0 |
| Duplicate `player_id` values | 0 |

## Row Identity Fields

Available row identity fields in the current full-board row contract include:

- `player_id`
- `canonical_player_key`
- `player_name`
- `normalized_player_name`
- `position`
- `nfl_team`
- `pool_status`
- `is_my_team`
- `is_available`
- `is_rookie`

## Recommended Join Key

Recommended stable join key: `player_id`.

Reasons:

- present on all 240 observed full-board rows;
- no duplicate `player_id` values were found;
- already used across the active data-pack model outputs, rosters, official rankings, and app row construction;
- avoids name-only joins that can collide across positions or suffix variants.

`canonical_player_key` and `(normalized_player_name, position)` remain useful audit/provenance fields, but they should not replace `player_id` as the first app artifact join key unless a later sprint proves a stronger contract.

## Current Player Universe Policy

No new separate current-player universe should be invented. Future Outcome probability attachment must use the Rankings page player rows and fail closed for rows that cannot join or cannot satisfy current-player feature requirements.

Rookies are present in the row contract via `is_rookie`, even though the observed local full-board export reported zero rookie rows. If rookies appear in a later active pool, veteran Outcome heads must mark them unavailable or under review; rookies must not be scored through veteran heads.

Kickers are present in the row contract and observed locally. K rows remain unsupported for these target Outcome heads and must be unavailable if an Outcome artifact is ever joined.

## Non-Mutation Confirmation

The 5EB audit script only inspected source/app contracts and wrote local-only evidence. It did not edit app UI/source files, mutate data, change Rankings sorting, create hidden sort keys, create probabilities, create app-readable generated output, or create promoted artifacts.

## Recommendation

Verdict: GREEN for Sprint 5EC current-player feature coverage audit.

Rationale:

- the Rankings page and pool builder were identified;
- `player_id` is a stable join-key candidate with complete observed coverage;
- the current full-board row contract contains the needed identity, position, pool, and rookie flags;
- the missing local active data-pack path is recorded as an environment caveat, not a reason to invent a separate universe;
- future numeric work remains gated on feature coverage and local-only dry-run audits.
