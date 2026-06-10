# Post Rankings / Draft / Live Detail Checkpoint - 2026-06-09

## Summary

This checkpoint covers the completed Rankings, Draft Prep, Live Draft Room, and shared Player Detail Card work.

Current accepted surfaces:

- Rankings is accepted for human review.
- Draft Prep is accepted for human review.
- Live Draft Room is accepted for human review.
- Shared Player Detail Card is wired into Rankings, Draft Prep, and Live Draft Room.
- Dropped/released player import template and validator are ready for future Roster Declaration Day data.
- Decision Board remains separate and untouched in this checkpoint.

## What Changed

- Rankings was rebuilt as a dynasty-first board and now uses the full-board private NWR export.
- Full-board Rankings coverage was repaired to score 232 QB/RB/WR/TE rows, with 8 unscored kickers hidden by default.
- QB/TE upper-band guard v2 production patch was applied through the production pipeline and accepted for human review.
- Draft Board was rebuilt into Draft Prep, a scouting/planning page around owned picks and candidate windows.
- Live Draft Room was split into a separate mock/live tracking page.
- Dropped/released player source contract, template, and validator were created for future final legal draft pool work.
- Shared Player Detail Card now handles:
  - Rankings context.
  - Draft Prep context.
  - Live Draft Room context.
- Broader Draft UX stale source-text tests were updated to the accepted page split and shared-card architecture.

## Active Rankings Source

Current active Rankings source:

`local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`

Current local SHA256:

`73786D1F58F1FF8071839883B34F48EAE239EA17FF9D98960FD65EFC2928E006`

This file remains ignored under `local_exports/` and was not changed by this checkpoint.

## Rankings Status

- Default page is Dynasty Rankings.
- Market and league ranks remain display-only.
- Outcome percentages remain planned/in development.
- Kickers remain hidden by default.
- Player details use the shared Player Detail Card.
- Keenan Allen and Darius Slayton legacy active-pack scores remain comparison-only.

## Draft Prep Status

- Draft Prep remains planning/scouting only.
- Source is the scouting prep pool:
  `local_exports/model_v4/draft_prep/latest/scouting_prep_pool_review_rows.csv`
- Legal draft pool remains pending until dropped/released veterans are supplied.
- Owned pick cards remain visible:
  - 2026 1.03
  - 2026 1.04
  - 2026 2.04
  - 2026 2.08
  - 2026 5.04
- 2026 5.04 remains No Baseline / Manual late-round watchlist / No exact equivalence.
- Draft Prep player details use the shared Player Detail Card.

## Live Draft Room Status

- Live Draft Room remains mock/scouting mode until the final legal pool is loaded.
- Draft state is session/local mock state only.
- Active data packs are not mutated.
- Best Remaining rows now support read-only selected player detail through the shared Player Detail Card.
- Mark Drafted, Replace Pick, Undo Last, Reset Mock, and save/load/duplicate/clear mock controls remain separate from the detail card.

## Player Detail Card Status

Shared paths:

- `src/services/player_detail_card_service.py`
- `app/components/player_detail_card.py`

Supported contexts:

- `rankings`
- `draft_prep`
- `live_draft_room`

Shared behavior:

- Missing fields fail closed with `-` or explicit unavailable/source-needed copy.
- Raw source receipts are collapsed by default.
- Market, league, prior draft, RotoWire/status, and legacy fields remain display/context/comparison only.
- No card writes persistent notes or mutates draft state.
- No card creates final trade, cut, keep, draft, buy, sell, defer, target, or start/sit recommendations.

## Dropped/Released Player Template Status

- Source contract exists for future dropped/released veteran data.
- Import template exists.
- Validator exists.
- No dropped players have been invented or imported.
- No preview veteran/free-agent rows are marked confirmed legal draftable without source proof.

## Sentinel Status

- Keenan Allen legacy active-pack `private_score = 82.4` remains comparison-only.
- Darius Slayton legacy active-pack `private_score = 78.88` remains comparison-only.
- Current Keenan Allen and Darius Slayton NWR scores remain sourced from admitted current Model v4 lineage, not legacy active-pack scores.
- 2026 5.04 remains no-baseline/manual watchlist with no invented equivalence.
- Outcome percentage fields remain blank/in development.

## Contamination Guardrails

The accepted surfaces preserve these rules:

- Market Rank and League Rank are display-only.
- Prior draft history and spreadsheet highlights are display/context only.
- RotoWire remains source-repair/status/context only unless already admitted through a source-safe private component.
- Legacy active-pack scores are comparison-only.
- Dropped-player status will be legal draft pool context only and will not alter private value.
- No generated model outputs or active data packs were changed by this checkpoint.

## Tests And Checks

Focused validation run:

```text
python -m py_compile app/components/player_detail_card.py app/pages/07_live_draft_room.py src/services/player_detail_card_service.py
python -m ruff check app/components/player_detail_card.py app/pages/07_live_draft_room.py src/services/player_detail_card_service.py tests/test_draft_ux_service.py tests/test_live_draft_room_page.py tests/test_player_detail_card_component.py tests/test_player_detail_card_service.py
python -m pytest tests/test_player_detail_card_service.py tests/test_player_detail_card_component.py tests/test_dynasty_rankings_page.py tests/test_draft_prep_page.py tests/test_live_draft_room_page.py tests/test_draft_ux_service.py tests/test_draft_room_ux_smoke_checklist.py tests/test_draft_ux_acceptance.py tests/test_dropped_released_players_source_service.py tests/test_player_board_score_service.py -q
```

Results:

- `py_compile`: passed.
- `ruff`: passed.
- Focused pytest: 73 passed.

Full repo pytest was not run because the repository has a large long-running test suite and the checkpoint requested the strongest practical focused set.

## Current Uncommitted Change Groups

Player Detail Card:

- `src/services/player_detail_card_service.py`
- `app/components/player_detail_card.py`

Live Draft Room:

- `app/pages/07_live_draft_room.py`

Tests:

- `tests/test_player_detail_card_service.py`
- `tests/test_player_detail_card_component.py`
- `tests/test_live_draft_room_page.py`
- `tests/test_draft_ux_service.py`

No generated local exports are changed.

## Remaining Blockers

- Final legal dropped/released veteran list is still pending until Roster Declaration Day data is supplied.
- Decision Board remains separate and should stay blocked until this checkpoint is committed and the next scoped task begins.
- Outcome percentages remain in development.
- Full repo pytest remains a possible longer validation run before a release-style milestone.

## Commit Readiness Recommendation

Recommended commit title:

`Wire player detail card into Live Draft Room`

Recommended commit body bullets:

- Add Live Draft Room context to the shared Player Detail Card service/component.
- Render read-only selected-player detail under Best Remaining / Scouting Pool.
- Preserve mock/live draft state behavior and active data-pack immutability.
- Update broader Draft UX tests to match accepted Draft Prep / Live Draft Room / shared-card architecture.
- Validate Rankings, Draft Prep, Live Draft Room, dropped-player source tests, and sentinel/player board checks.

Recommended include list:

- `src/services/player_detail_card_service.py`
- `app/components/player_detail_card.py`
- `app/pages/07_live_draft_room.py`
- `tests/test_player_detail_card_service.py`
- `tests/test_player_detail_card_component.py`
- `tests/test_live_draft_room_page.py`
- `tests/test_draft_ux_service.py`
- `docs/model_v4/POST_RANKINGS_DRAFT_LIVE_DETAIL_CHECKPOINT_20260609.md`

Recommended exclude list:

- `local_exports/`
- runtime caches
- pytest temp folders
- any generated active data pack output

Branch is ready for user-approved commit/push after reviewing this checkpoint.

## Recommended Next Task

After commit, start the Roster Decisions page as the next product surface, unless the user chooses to run full repo pytest first.
