# NWR Live Draft Room Tab Repair - 2026-06-22

## Verdict

GREEN. This repair changes only Streamlit/session-state presentation for the Live Draft Room workflow. It does not change model logic, final board rank, frozen board contents, latest_candidate, latest_approved, or the pinned snapshot.

## Root Cause: Rookie vs Dropped Veteran Ranking Concern

The Live Draft Room was reading the frozen Final Draft Board V1 source of truth. The apparent rookie-over-veteran concern is not a Live Draft Room reranking bug.

Frozen board facts observed locally:

| Group | Count | Rank posture | Visible score basis |
| --- | ---: | --- | --- |
| Rookies | 54 | occupy the top rookie-board portion of the frozen board | `rookie_score_from_frozen_rookie_rank_and_tier` |
| Dropped veterans | 12 | appear later in the frozen board | `pinned_veteran_candidate_value_for_dropped_legal_draftable_pool` |

Selected diagnostic rows:

| Player | Pos | Asset Type | Final Board Rank | Visible Score | Score Basis | Draft Action |
| --- | --- | --- | ---: | ---: | --- | --- |
| Jeremiyah Love | RB | rookie | 1 | 96.00 | rookie score from frozen rookie rank/tier | target |
| Makai Lemon | WR | rookie | 2 | 94.50 | rookie score from frozen rookie rank/tier | target |
| Carnell Tate | WR | rookie | 3 | 93.00 | rookie score from frozen rookie rank/tier | target |
| Zay Flowers | WR | dropped_veteran | 31 | 56.53 | pinned veteran candidate value | target |
| Chris Olave | WR | dropped_veteran | 34 | 54.07 | pinned veteran candidate value | target |
| Drake Maye | QB | dropped_veteran | 40 | 49.35 | pinned veteran candidate value | watch |

Interpretation: the board order is the current frozen source order, and the visible score is mixed-basis context across rookie and dropped-veteran pools. The app should make that clear and default to visible `final_board_rank` order. If Tim wants dropped veterans moved above rookies, that is a source-of-truth/frozen-board decision requiring human approval, not a Live Draft UI repair.

## Columns Used By Live Draft Room

| Purpose | Column |
| --- | --- |
| Default order | `final_board_rank` ascending |
| Visible board score | `final_board_score_visible`, now labeled `Visible Score (Mixed Basis)` |
| Final board rank | `final_board_rank` |
| Asset type / dropped veteran / rookie indicator | `asset_type` |
| Board availability | `availability_status` |
| Draft action | `draft_action_display_only` |
| Session draft status | Streamlit session-state derived `draft_status` |
| Assigned pick | Streamlit session-state derived `assigned_pick` |

No hidden sort field is displayed. The transient helper sort column used internally by the service is dropped before display.

## UI Repair

Before:

- Large stat cards pushed the ranking table down.
- The visible score label did not explain that rookie and dropped-veteran rows use different score bases.
- The primary table showed less useful context ordering.
- Pick slot selection could remain on the just-assigned pick after assignment.

After:

- Large cards were replaced with compact caption/status rows.
- The table appears higher on the page and remains the primary workflow surface.
- Default order is explicitly described as Final Board Rank ascending.
- Visible score is labeled as mixed-basis context.
- Asset Type filter was added for `rookie`, `dropped_veteran`, or all rows.
- Practical columns now lead the table: Draft Status, Assigned Pick, Final Board Rank, Player, Pos, NFL Team, Asset Type, Board Availability, Draft Action.
- Assign/undo/remove now request pick-slot resync to the next open/current pick.

## Pick Auto-Advance

Implementation:

- After `Assign Pick`, the workflow sets a session sync flag and reruns.
- The pick slot selector is then synced to the next unassigned pick computed from the draft board.
- Undo and remove also trigger a recompute so the current pick returns to the earliest open slot.
- Duplicate player assignments remain blocked by service validation and by the available-only default table.

Focused service proof:

- Pick 1 assigned -> current pick becomes 2.
- Pick 2 assigned -> current pick becomes 3.
- Remove pick 1 -> current pick recomputes to 1.
- Undo remaining assignment -> current pick remains 1.

Browser proof on `http://127.0.0.1:8501/live-draft-room`:

- Initial page showed `Frozen board rows: 66 | Drafted: 0 | Available: 66 | Current pick: 1.01 - Golden Boy Productions`.
- `Assign Pick` on the current selection updated the page to `Drafted: 1 | Available: 65 | Current pick: 1.02` and the pick slot selector advanced to `1.02 - WhoDat? (overall 2)`.
- The selected player left the available-only selector; after assigning the first row, the selector advanced from the drafted player to the next available player.
- `Undo Last` restored `Drafted: 0 | Available: 66 | Current pick: 1.01`.
- Assigning again and using `Remove Player` restored `Drafted: 0 | Available: 66 | Current pick: 1.01`.

## Validation

- Focused pytest: `43 passed`.
- Ruff on touched files: PASS.
- Python compile check: PASS.
- Browser smoke:
  - `/rankings`: PASS, no page-not-found.
  - `/live-draft-room`: PASS, table/status/pick workflow rendered.
  - `/mock-draft`: PASS, table and draft board rendered.
  - `/trading-lab`: PASS, page rendered.
- Frozen board row count: 66.
- No rank/source/model mutations were made.

## Remaining YELLOW/RED

None for Live Draft Room UI mechanics after browser smoke. Source-order dissatisfaction remains a human board-order decision if Tim wants dropped veterans reprioritized relative to rookies.
