# Draft Prep Current State Audit - 2026-06-09

## Current Draft Board files
- Page: `app/pages/06_draft_board.py`.
- UI/session helper: `app/components/draft_session.py`.
- Product contract/ranking table: `src/services/draft_ux_service.py`.
- Core draft board builder: `src/services/draft_service.py`.
- Live/mock board state: `src/services/draft_state_service.py`.
- Saved mock drafts: `src/services/mock_draft_storage_service.py`.
- Draftable preview builder: `src/services/real_draft_pool_preview_service.py`.
- Rookie review exports: `src/services/model_v4_sprint14e_rookie_draft_review_service.py`.

## Current behavior
- The page currently mixes Draft Board planning, draft rankings, pick grid, live/mock drafted state, save/load mock controls, rookie model receipts, source-risk expanders, and audit/debug context.
- The scheduled draft grid is built from `fact_future_picks.csv`; the active pack has 50 scheduled picks for a 5 round x 10 team offline draft.
- Niners picks are resolved by matching `current_team_name`/team id to the `team_id='niners'` alias in `build_draft_room`.
- Mock/live state lives in Streamlit session state through `app/components/draft_session.py` and can be saved as JSON under `local_exports/mock_drafts`.

## Draftable pool status
- Active pack rookie draftables: missing_optional_or_inactive (0 rows).
- Active pack free agents/veterans: missing_optional_or_inactive (0 rows).
- Preview pack rookie draftables: loaded (80 rows).
- Preview pack free agents: loaded (460 rows).
- The current active pack draftable pool is effectively 0 because `fact_rookie_draftables.csv`, `fact_available_veterans.csv`, and `fact_manual_draftables.csv` are not present in the active pack.
- Draft-pool preview packs exist and can support scouting/readiness, but this task does not promote them into active app state.

## Model v4 rookie/pick exports loaded today
- `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- `local_exports/model_v4/rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv`
- `local_exports/model_v4/rookie_pick_decision_lab/latest/pick_decision_rows.csv`
- `local_exports/model_v4/human_decision_review_prep/latest/pick_review_cards.csv`
- These are review/product-prep context, not final recommendations.

## 2026 5.04
- The active pack contains an old `fact_pick_values.csv` row for `2026 5.04`, but Model v4 pick-decision rows correctly label it `manual_only_no_exact_model_baseline`.
- Draft Prep must keep `2026 5.04` visible as a late-round pick card with `No Baseline` / `Manual Watchlist` language.

## Missing legal source
- Dropped/released veterans are expected after Roster Declaration Day.
- Missing dropped-player source must not be interpreted as proof that no veterans are draftable.
