# NWR Historical Tuned Overlay App Integration - 2026-06-22

## Final Verdict: GREEN with YELLOW data caveat

The historical tuned cross-asset overlay is integrated into the draft-day app as a **Review-Only Candidate Best Available** layer. It improves the current rookie-veteran comparison posture without mutating the frozen board, Dynasty Rank, latest_candidate, latest_approved, pinned snapshot, or any model/source-truth artifact.

The remaining YELLOW caveat is unchanged from the tuning lane: no complete prior-season verified dropped-veteran league truth panel exists. The tuned overlay is therefore useful for human draft review, not production model approval.

## Integrated?

Yes. `src/services/draft_day_app_v1_service.py` now loads the existing emergency cross-asset candidate board, then overlays the 66-player historical tuned candidate rows from:

`docs/hq/parallel_lanes/historical_cross_asset_tuning_20260622/tuned_candidate_app_overlay.csv`

This preserves existing emergency ADP/current-pick display context while replacing the review-only candidate rank/value/band/confidence for tuned frozen-board players.

## Draft Usability

The app remains draft-usable. Live Draft Room still shows Final Board Rank beside Historical Tuned Candidate Rank, picked-player workflow remains session-only, and Player Compare can compare tuned candidate context without changing final ranks.

## Key Player Before / After

| Player | Frozen Rank | Emergency Candidate Rank | Historical Tuned Candidate Rank | Result |
| --- | ---: | ---: | ---: | --- |
| Jeremiyah Love | 1 | 1 | 1 | Remains near top |
| Makai Lemon | 2 | 4 | 2 | Top rookie/prospect remains visible with lower confidence |
| Carnell Tate | 3 | 7 | 3 | Top rookie/prospect remains visible with lower confidence |
| KC Concepcion | 4 | 8 | 4 | Top rookie/prospect remains visible with lower confidence |
| Jadarian Price | 5 | 9 | 6 | Top RB prospect remains visible |
| Zay Flowers | 31 | 2 | 10 | No longer buried vs prospects; still not a source-truth rank change |
| Chris Olave | 34 | 3 | 11 | No longer buried vs prospects; still not a source-truth rank change |
| Jameson Williams | 42 | 5 | 13 | No longer buried vs prospects |
| Drake Maye | 40 | 11 | 20 | Discounted for 1QB but still review-visible |
| Dak Prescott | 60 | 57 | 32 | Remains 1QB-discounted but no longer meaningless |
| Jaylen Warren | 54 | 19 | 24 | Review-visible, age/role caveats remain |
| Brian Thomas | 63 | 22 | 28 | Depth/review-only |
| Rashee Rice | 62 | 20 | 26 | Depth/review-only |
| Brock Purdy | 65 | 63 | 65 | Still heavily 1QB-discounted |
| Keenan Allen | 64 | 65 | 64 | Human-review / age-risk constrained |
| Darren Waller | 66 | 66 | 66 | Human-review / age-risk constrained |

## Why Review-Only

- It does not replace Final Board Rank.
- It does not replace Dynasty Rank.
- It does not use ADP as model input.
- It keeps ADP/range as display-only context.
- It is based on historical rookie replay plus current internal dynasty/veteran anchors, but lacks a complete verified historical dropped-veteran panel.

## Live Draft Proof

Service-level proof confirms the app-loaded board has:

- Zay Flowers: Final Board Rank 31, Historical Tuned Candidate Rank 10.
- Drake Maye: Final Board Rank 40, Historical Tuned Candidate Rank 20.
- Frozen board row count remains 66.

Browser smoke confirmed `/live-draft-room` opens and exposes Historical Tuned Candidate Best Available copy, Final Board Rank, pick controls, and draft board. Assigning 1.01 advanced the current pick to 1.02, and Undo restored current pick to 1.01.

## Dynasty Rankings Proof

The tuned candidate columns remain optional/review-only in the unified player board. Dynasty Rank remains the primary full-dynasty ordering and is not overwritten.

## Player Compare Proof

Player Compare opens cleanly. It uses the same enriched frozen-board frame, so selected players receive Historical Tuned Candidate Rank/Value where available. Direct service proof confirmed Zay Flowers, Chris Olave, Jameson Williams, Drake Maye, Dak Prescott, Keenan Allen, and Darren Waller all carry tuned review-only candidate context. The copy explicitly states that these metrics do not replace Final Board Rank, Dynasty Rank, or the frozen source of truth.

## Remaining Caveats

- Historical dropped-veteran proxy rows are sensitivity-only.
- Missing Outcome values remain `Not enough information`.
- This is not latest_candidate, latest_approved, private value, final rank approval, or model promotion.

## Files Changed

- `src/services/draft_day_app_v1_service.py`
- `src/services/draft_day_workflow_service.py`
- `app/components/draft_workflow.py`
- `app/pages/21_live_draft_room_v1.py`
- `app/pages/22_player_compare_v1.py`
- `tests/test_draft_day_app_v1_service.py`
- `docs/hq/parallel_lanes/NWR_HISTORICAL_TUNED_OVERLAY_APP_INTEGRATION_20260622.md`

## Tests / Smoke

- CSV load validation: PASS; `tuned_candidate_app_overlay.csv` loaded with 66 rows and required fields.
- Focused pytest: BLOCKED by local environment (`pytest` is not installed in the repo venv or shell).
- Ruff: BLOCKED by local environment (`ruff` is not installed in the repo venv or shell).
- Python compile/import checks: PASS for touched Python files.
- Direct service assertions: PASS for tuned ranks, frozen row count 66, and pinned manifest hash.
- `git diff --check`: PASS.
- Browser smoke: PASS for `/live-draft-room`, `/rankings`, `/player-compare`, `/mock-draft`, and `/trading-lab`. `/rankings` showed no kickers by default. Live Draft assign/undo flow passed.

## Guardrails

No frozen board mutation, no final_board_rank change, no latest_candidate/latest_approved update, no pinned snapshot mutation, no vendor CSV, no raw prediction dump, and no `C:\NWR_SHARED_DATA` tracking.
