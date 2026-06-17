# Mock Draft Phase 1 Intake Design - 2026-06-17

## Repo State
- Repo/worktree: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft`
- Branch: `work/mock-draft-simulator`
- Latest commit at intake start: `c3022db` - `Document mock draft five-loop postrun status`
- Phase: intake/design only. No full simulation was run.

## Purpose
Build the next post-drop-day mock draft simulator plan using frozen/manual rookie input, dropped veterans, the full available player pool, all 10 post-drop team rosters, draft order, team needs, ADP/market behavior, and NWR value/guidance while preserving strict separation between market cost and private evaluation.

League settings to preserve in later modeling:
- 10 teams, dynasty/keeper hybrid, 1QB, non-PPR.
- First downs matter: `0.4` rush/receiving first down.
- Passing: `1 per 30 yards`, passing TD `3`, INT `-1`.
- Rushing/receiving: `1 per 10 yards`, TD `4`.
- Returns: `1 per 30 yards`, return TD `4`.
- 2-point conversions: `2`; fumble lost: `-1`.
- Kickers are not important.

## Input Files Found Locally

### Explicit Rookie Input
- Found and readable: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies\local_exports\rookie_framework\final_post_fill_runway_20260616\rookie_2026_mock_draft_input_20260616.csv`
- Rows: `54`
- Columns: `rookie_rank`, `player`, `position`, `nfl_team`, `age`, `nfl_draft_capital`, `adp_market_rank`, `depth_chart_role`, `tier_label`, `draft_action`, `warning_severity`, `upside_band`, `bust_risk_band`, `manual_question`, `rookie_source_status`, `formula_name`, `board_order_frozen`
- `formula_name`: `cfbd_enriched_baseline_v1_1`
- `board_order_frozen`: `yes`
- `adp_market_rank`: populated for `54` rows and must remain display/opponent-behavior context only.
- Warning values present: `none`, `soft_note`, `critical_trap_guard`, `manual_review`

This source was read only. No Rookie HQ file was modified.

### Existing Mock-Draft Local Inputs And Artifacts
- Post-drop roster extraction: `local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326/roster_rows_normalized_review.csv`
  - Rows: `294`
  - Columns: `source_pdf`, `source_page`, `source_row`, `team_name`, `manager`, `roster_slot`, `player_name`, `position`, `nfl_team`, `overall_rank`, `input_status`
  - Coverage found: `5` team names and `4` managers, not the required 10 teams.
- Draft-pick extraction: `local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326/draft_pick_rows_normalized_review.csv`
  - Rows: `151`
  - Seasons: `2026`, `2027`, `2028`
  - Columns: `source_pdf`, `source_page`, `source_row`, `current_owner`, `manager`, `pick_label`, `season`, `round_text`, `asset_type`, `original_owner`, `is_niners_pick`, `input_status`
- Free agents: `local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326/free_agent_rows_normalized_review.csv`
  - Rows: `77`
- Declared drops: `local_exports/mock_draft_simulator/input_snapshots/lve_rosters_061326/declared_top_five_drops_20260616.csv`
  - Rows: `10`
  - Brock Purdy duplicate declaration remains preserved/review-required.
- Combined review pool: `local_exports/mock_draft/combined_simulator_state_20260616/combined_available_pool_review_rows.csv`
  - Rows: `141`
  - Source counts: `54` frozen rookies, `10` declared drops, `77` free agents.
  - Value status: `54` frozen rookie guidance/no numeric score, `87` value-neutral rows.
  - Numeric NWR private value rows: `0`
- Simulator-ready 2026 picks: `local_exports/mock_draft/combined_simulator_state_20260616/simulator_ready_2026_pick_rows.csv`
  - Rows: `51`
- Fake market fixture: `tests/fixtures/mock_draft/fake_market_timing_rows.csv`
  - Rows: `3`
  - Fake/sample only; not a real dynasty ADP source.
- Existing review-only services/docs/artifacts:
  - combined simulator state
  - pick-by-pick run/report
  - draft-room kit
  - full-pool visibility overlay
  - ADP/market timing contract
  - fake-only market timing adapter
  - scenario variants
  - scenario comparison kit
  - manual review packet
  - local regeneration runner

## Missing Files Tim Still Needs To Provide
- Complete all-10-team post-drop roster snapshot. Current local roster extraction covers only 5 team names and 4 managers.
- Complete team/manager mapping for all 10 teams.
- Confirmed full 2026 draft order for all teams and all relevant rounds after drops/trades. Current simulator-ready rows exist, but owner coverage is incomplete relative to 10-team simulation requirements.
- Real dynasty ADP/market timing CSV, imported only under the committed behavior-only contract. Current real ADP source is missing; only fake fixture rows exist.
- Approved NWR overall value/guidance export for veterans/free agents if Tim wants value-aware veteran comparison. Current combined state has `0` numeric NWR private value rows; snapshot-only veterans/free agents remain value-neutral.
- Optional team-need rules or roster construction preferences for the dynasty/keeper hybrid format, especially QB/RB/WR/TE scarcity and kicker irrelevance.

## Phase 1 Can Proceed
Phase 1 intake/design can proceed: the worktree has enough local evidence to define the data contract, join plan, output plan, blockers, and guardrails.

## Full Simulation Is Currently Blocked
A full post-drop-day simulation is blocked until the missing inputs above are supplied and approved. The main blockers are incomplete all-10-team roster/manager coverage, no real behavior-only ADP/market timing source, and no approved numeric NWR private value export for veteran/free-agent quality.

## Mock Draft Data Contract

### Rookie Input Schema
Source: explicit Rookie HQ CSV, read-only/manual-use.

Required columns:
- `rookie_rank`
- `player`
- `position`
- `nfl_team`
- `age`
- `nfl_draft_capital`
- `adp_market_rank`
- `depth_chart_role`
- `tier_label`
- `draft_action`
- `warning_severity`
- `upside_band`
- `bust_risk_band`
- `manual_question`
- `rookie_source_status`
- `formula_name`
- `board_order_frozen`

Rules:
- `formula_name` must remain `cfbd_enriched_baseline_v1_1`.
- `board_order_frozen` must remain `yes`.
- `rookie_rank`/board order is frozen unless Tim explicitly requests a what-if view.
- `adp_market_rank` is display/opponent-behavior context only.
- Warning/manual-review fields must be preserved.

### Veteran/Drop/Free-Agent Schema
Minimum columns:
- `asset_id`
- `player`
- `position`
- `nfl_team`
- `source_label`: `declared_drop` or `free_agent`
- `source_overall_rank`
- `source_team`
- `source_manager`
- `value_status`
- `review_flags`
- `nwr_score_status`

Rules:
- Dropped veterans and free agents remain value-neutral unless an approved in-lane NWR value source is supplied.
- Duplicate declared drops remain separate review rows until manually resolved.

### Roster Schema
Minimum columns:
- `team_name`
- `manager`
- `roster_slot`
- `player_name`
- `position`
- `nfl_team`
- `overall_rank`
- `input_status`

Rules:
- Must cover all 10 teams after drops.
- Rosters drive team-need pressure by position and roster construction, not private NWR quality by themselves.

### Draft Order Schema
Minimum columns:
- `season`
- `round_text`
- `pick_label`
- `overall_pick`
- `round`
- `round_pick`
- `current_owner`
- `original_owner`
- `manager`
- `is_niners_pick`
- `source_status`

Rules:
- Future `1.00` placeholders remain review-required and excluded from simulator-ready pick windows.
- Draft order drives pick windows and availability timing.

### Team/Manager Schema
Minimum columns:
- `team_name`
- `manager`
- `team_id` or stable normalized team key
- optional aliases from roster and pick exports

Rules:
- Must reconcile roster team names, pick-owner names, and manager labels.
- Missing/ambiguous teams become review-required.

### ADP/Market Behavior-Only Schema
Minimum columns:
- `asset_id`
- `player`
- `position`
- `source_name`
- `source_type`
- `source_timestamp`
- `market_adp` or `overall_adp` or `expected_pick`
- `sample_size`
- `identity_match_method`
- `review_flags`

Rules:
- ADP/market may affect opponent behavior, likely pick timing, expected draft-room cost, and availability pressure only.
- ADP/market must not enter NWR private quality/value.
- Blocked columns include `stats_model_value`, `model_value`, `draft_value`, `nwr_draft_value`, `nwr_dynasty_score`, `nwr_quality_score`, `quality_score`, and `war_score`.

### NWR Value/Guidance Schema
Minimum rookie guidance columns:
- `rookie_rank`
- `tier_label`
- `draft_action`
- `warning_severity`
- `upside_band`
- `bust_risk_band`
- `manual_question`

Minimum veteran/free-agent guidance columns if supplied later:
- `asset_id`
- `player`
- `position`
- `nwr_value_status`
- `nwr_guidance_label`
- `nwr_warning`
- `source_status`

Rules:
- NWR guidance is Tim-facing evaluation, fit, warnings, and draft action.
- Numeric NWR scores must not be invented from market rank, snapshot rank, rookie rank, or ADP.

## Join Plan
- Rookie input joins to the available pool by normalized player name plus position, with `rookie_rank` and `tier_label` preserved as read-only guidance.
- Declared drops and free agents join by normalized player name, position, and source row identity, preserving duplicate declarations such as Brock Purdy.
- Rosters create team needs by grouping all players by team/manager/position after drops. Missing teams or ambiguous manager mappings become review-required.
- Draft order drives pick windows by `overall_pick`, `pick_label`, `current_owner`, and `is_niners_pick`.
- ADP/market timing can move opponent selections and availability pressure only; it cannot update NWR value, rookie guidance, or veteran value status.
- NWR value/guidance remains a separate Tim-facing layer. If no approved veteran value exists, veterans/free agents remain value-neutral visibility rows.

## Output Plan
- Likely available players at each Tim/Niners pick, separated into frozen rookie guidance and value-neutral veteran/free-agent visibility.
- Team-need pressure by opponent team and pick window once complete all-10-team rosters exist.
- Value pockets where NWR guidance is favorable relative to expected market cost, without blending market into NWR quality.
- Reach risk using market timing/cost versus Tim-facing guidance, not as a private-value score.
- Opponent behavior notes explaining why players are likely to be selected before/after Tim picks.
- Manual decision queue for Tim/Niners picks with blank/manual-only decision fields.
- Review-required flags for missing identity, incomplete teams, stale/missing market rows, Brock Purdy duplicate, future placeholders, and value-neutral veterans/free agents.

## Guardrails
- ADP/market is behavior-only: opponent behavior, likely timing, availability pressure, and expected draft-room cost.
- NWR value/guidance is separate: Tim-facing evaluation, fit, warnings, and draft action.
- Rookie board order remains frozen.
- Rookie `formula_name=cfbd_enriched_baseline_v1_1` and `board_order_frozen=yes` remain unchanged.
- No production/app/promotion impact.
- No Streamlit/app wiring.
- No Outcome HQ, Drop Decision HQ, Rookie HQ, production rankings, private scores, probabilities, bands, hidden sort keys, or promoted artifacts touched.
- No real ADP/market imported during this phase.
- No numeric NWR scores invented.
- `local_exports/` remains local-only and uncommitted.

## Recommended Next Step
Tim should provide or approve the missing post-drop-day inputs before a full simulation:
1. Complete all-10-team roster/manager snapshot after drops.
2. Confirm full draft order and pick ownership.
3. Provide a real dynasty ADP/market timing file under the committed behavior-only contract, if desired.
4. Provide an approved NWR veteran/free-agent value/guidance export if value-aware veteran comparisons are needed.

## Verdict
- Phase 1 intake/design: GREEN.
- Full simulation readiness: YELLOW/BLOCKED until missing inputs are supplied.
- Contamination status: GREEN. No real market data was imported, no Rookie files were modified, no production/app surfaces were touched, and no numeric NWR score was invented.
