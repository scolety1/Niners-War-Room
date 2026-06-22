# NWR Live Draft Room Source And UI Repair - 2026-06-22

## Verdict

YELLOW. The Live Draft Room workflow and table UI were repaired without changing ranks, model logic, frozen board rows, latest_candidate/latest_approved, or the pinned snapshot. Remaining YELLOW is source coverage: a true Sleeper free-agent all-player pool was not safely available as an approved app source, and ADP remains display-only from a YELLOW undocumented Sleeper endpoint.

## Rookie/Veteran Comparability Root Cause

The frozen board contains two asset groups with different visible score bases:

- 54 rookie rows use `rookie_score_from_frozen_rookie_rank_and_tier`.
- 12 dropped-veteran rows use `pinned_veteran_candidate_value_for_dropped_legal_draftable_pool`.

These scores are not directly comparable as one universal long-term value scale. The UI no longer foregrounds `Visible Score (Mixed Basis)` in the default Live Draft Room table. It keeps `Final Board Rank`, `Position Rank`, `Asset Type`, tier, age, ADP context, and manual risk notes visible.

Named dropped-veteran examples inspected:

- Zay Flowers: WR, dropped veteran, final board rank 31, veteran score basis.
- Chris Olave: WR, dropped veteran, final board rank 34, veteran score basis.
- Drake Maye: QB, dropped veteran, final board rank 40, veteran score basis.
- Jameson Williams: WR, dropped veteran, final board rank 42, veteran score basis.
- Dak Prescott: QB, dropped veteran, final board rank 60, veteran score basis.

Human source/rank decision required: YES, if Tim wants a new cross-asset "best available long-term player" rank that re-compares rookies and dropped veterans. This repair does not rerank.

## Free-Agent Pool Discovery

Existing sources found:

- Frozen Final Draft Board V1: 66 rows, source of truth for live draft workflow.
- Full Dynasty Rankings: 240 rows, but all `is_available` values are `0`; this is not a live free-agent pool.
- Sleeper league roster snapshot: candidate/review-only rostered IDs, with allowed use limited to audit/crosscheck. It does not include an approved all-player free-agent universe with player metadata for app expansion.
- Mock Draft availability context: 89 rows, but this is board/unavailable/dropped context, not a full free-agent sweep.

Result: no safe approved free-agent expansion was wired into the Live Draft Room. Missing off-board free agents remain a YELLOW data gap for Master/human review.

## Age Source

Age is display-only and is filled only where an existing roster DOB context matches by player name and position:

- Source: `C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context\20260621_011500_timing_metadata_v1\player_roster_display_context.csv`
- As-of date: 2026-06-22
- Frozen board age support: 11/66
- Full Dynasty age support after display enrichment: 224/240
- Missing age display: `Not enough information`

No age values were fabricated.

## ADP / Range / Current Pick Value

ADP source:

- `market_behavior/sleeper_adp_display_context`
- Pointer: `C:\NWR_SHARED_DATA\lane_exchange\market_behavior\sleeper_adp_display_context\latest_candidate.json`
- Source risk: `YELLOW_UNDOCUMENTED_ENDPOINT`
- Allowed use: display-only, market awareness, draft timing context, mock draft display overlay.
- Blocked use: private value, hidden sort, rankings, model training, recommendations, final draft decisions, simulations.

Live display coverage:

- Meaningful ADP: 48/66
- ADP range: 31/66
- Current Pick Value: 48/66
- Missing ADP/range/value display: `Not enough information`

`ADP Range` is derived only from meaningful existing Sleeper ADP source fields (`adp_dynasty_std`, `adp_dynasty`, `adp_std`). Sleeper sentinel-like values at or above 900 are treated as `Not enough information`.

Current Pick Value is display-only and recalculates from current pick versus preferred ADP:

- `Reach`
- `Slight reach`
- `Fair`
- `Value`
- `Steal`
- `Not enough information`

This column does not drive sort, rank, model value, or recommendations.

## UI Changes Made

- Removed the large top source/status block from Live Draft Room.
- Moved frozen-board source details and lane prop status into collapsed expanders.
- Replaced large status cards/captions with one compact status line.
- Default table now hides drafted players.
- Added `Show drafted players` toggle.
- Removed these from the default table:
  - Draft Status
  - Assigned Pick
  - Board Availability
  - Draft Action
  - Visible Score (Mixed Basis)
- Default table now focuses on:
  - Final Board Rank
  - Player
  - Pos
  - NFL Team
  - Age
  - Position Rank
  - Asset Type
  - ADP (Display-Only)
  - ADP Range (Display-Only)
  - Current Pick Value (Display-Only)
  - Source
  - Final Tier
  - Risk Notes
  - Manual Review

## Pick Auto-Advance Proof

The existing session-state repair remains in place:

- Assigning a player sets the selected pick sync flag and reruns the page.
- Current pick is recomputed from the next unassigned pick.
- Undo, remove, and edit also recompute the current pick.
- Duplicate player assignment is blocked by service validation.

Focused tests passed for assign, duplicate prevention, undo, remove/edit, and current-pick recomputation.

## Remaining YELLOW/RED

- YELLOW: true off-board free-agent expansion needs an approved all-player Sleeper/player metadata source. It was not safely available in current app props.
- YELLOW: ADP is useful but sourced from a YELLOW undocumented Sleeper endpoint, so it remains display-only.
- YELLOW: rookie/veteran cross-asset rank comparability requires human approval if Tim wants a new source-truth board order.
- GREEN: no frozen board, model, rank, Mock Draft simulator, latest, approved, or pinned snapshot mutation was made.
