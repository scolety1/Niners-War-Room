# Rookie HQ Pause And Handoff Prompts

Date: 2026-06-16

Purpose: copy/paste prompts for pausing Rookie HQ and starting a separate Mock Draft HQ lane.

Rookie HQ status: frozen/manual-use ready, not production/app integrated.

## MASTER_HQ_ROOKIE_PAUSE_AND_MOCK_DRAFT_START_PROMPT

You are Master/Main HQ for Niners War Room.

Rookie HQ is now paused/frozen after the final manual draft kit post-fill runway.

Rookie repo:

`C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies`

Rookie branch:

`work/rookie-framework-path`

Latest Rookie commit:

`6fba96d9a08f635e19aeee2fe38599691a52dc99`

Final display/data-fill commits after the final kit freeze:

- `19a117a5ec4a32ab647c0e1ef4809cbdd00bcf97` - stat enrichment
- `0aadbe3ba83d6dadfb103bec4f3eb96d2e326186` - display cleanup
- `ac84f7fc71d379a658cbbd287f48734afa7a1fd2` - local display data fill
- `6fba96d9a08f635e19aeee2fe38599691a52dc99` - final post-fill runway / Mock Draft input handoff

Final Rookie artifacts:

- Preview:
  `local_exports/rookie_framework/final_post_fill_runway_20260616/preview/index.html`
- Final rookie board:
  `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_final_manual_draft_board_post_fill_runway_20260616.csv`
- Mock Draft rookie input:
  `local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv`
- Missing-data templates:
  `local_exports/rookie_framework/final_post_fill_runway_20260616/missing_data_templates/`

Final Rookie verdicts:

- Final kit quality: GREEN
- Mock Draft rookie input readiness: GREEN
- Preview/readability: GREEN
- Data integrity: GREEN
- Anti-cheat/leakage: GREEN
- Manual draft trust: YELLOW because some display-only fields still have `needs_data`

Coverage:

- ADP / Market: 46/54 populated, 8 `needs_data`
- NFL Team: 46/54 populated, 8 `needs_data`
- Age: 27/54 populated, 27 `needs_data`
- Depth Chart / Role: 11/54 populated, 43 `needs_data`
- NFL Draft Capital: 54/54 populated

Guardrails:

- Formula unchanged: `cfbd_enriched_baseline_v1_1`
- Board order unchanged
- Rookie artifacts are manual-use inputs only
- Rookie artifacts are not production/app rankings
- ADP/market is display-only and must not affect NWR private/model quality
- No production/app/outcome/veteran contamination occurred
- No probabilities, bands, hidden sort keys, or promoted artifacts were created

Request:

Please record Rookie HQ as paused/frozen and approve opening a separate Mock Draft HQ/lane.

Do not reopen Rookie HQ unless one of these is explicitly true:

- factual correction
- player update
- broken export
- push/backup request
- later explicit production integration request

Do not treat Rookie outputs as production rankings. Use the Rookie Mock Draft input only as a manual-use rookie input for the separate Mock Draft HQ.

Expected Rookie git status:

```text
?? data/
```

Do not stage or commit `data/`.

## MOCK_DRAFT_HQ_START_PROMPT

You are starting a new Mock Draft HQ / Mock Draft Codex lane for Niners War Room.

Purpose:

Simulate the post-drop-day fantasy draft using rookies, dropped veterans, all team rosters, pick order, team needs, ADP/market behavior, and NWR value. Start with Phase 1 intake/design only unless enough inputs already exist locally to safely proceed.

League settings:

- 10 teams
- Dynasty/keeper hybrid
- 1QB
- Non-PPR
- First-down scoring matters: 0.4 rush/rec first down
- Passing yards: 1 per 30
- Passing TD: 3
- INT: -1
- Rush/rec yards: 1 per 10
- Rush/rec TD: 4
- Return yards: 1 per 30
- Return TD: 4
- 2-point conversions: 2
- Fumble lost: -1
- Kickers not important

Use the Rookie mock draft input CSV as the rookie input:

`C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies\local_exports\rookie_framework\final_post_fill_runway_20260616\rookie_2026_mock_draft_input_20260616.csv`

Important Rookie input rules:

- Treat the rookie input as manual-use only.
- Keep rookie board order frozen unless Tim explicitly requests a what-if view.
- Keep `formula_name = cfbd_enriched_baseline_v1_1`.
- Keep `board_order_frozen = yes`.
- Preserve warning/manual-review fields.
- Treat `adp_market_rank` as display/opponent-behavior context only.
- Do not use ADP/market as NWR private quality.
- Do not convert Rookie outputs into production/app rankings.

Separate these concepts:

- ADP/market: opponent behavior, availability pressure, expected draft-room cost
- NWR value/quality: Tim-facing evaluation, fit, warnings, and draft action

Files Tim should provide next:

1. Post-drop available player pool
   - Suggested columns: `player_name`, `position`, `nfl_team`, `source_name`, `as_of_date`, `notes`

2. All 10 team rosters after drops
   - Suggested columns: `team_name`, `manager`, `player_name`, `position`, `nfl_team`, `keeper_status`, `notes`

3. Draft order
   - Suggested columns: `round`, `pick`, `overall_pick`, `team_name`, `manager`

4. Team names / managers, if useful
   - Suggested columns: `team_name`, `manager`, `notes`

5. Dynasty ADP/market CSVs
   - Suggested columns: `player_name`, `position`, `adp_or_market_rank`, `source_name`, `as_of_date`

6. Dropped veterans list
   - Suggested columns: `player_name`, `position`, `nfl_team`, `dropped_by_team`, `source_name`, `as_of_date`, `notes`

7. Existing NWR overall value/rank exports, if available
   - Suggested columns: `player_name`, `position`, `nfl_team`, `nwr_rank`, `nwr_value`, `warning_flags`, `source_name`

Phase 1 deliverables:

- Inventory local Mock Draft inputs and missing inputs.
- Confirm repo/worktree/branch for Mock Draft HQ.
- Define the Mock Draft data contract.
- Define how Rookie input joins with available veterans and rosters.
- Define opponent-behavior logic separately from NWR private value.
- Define simulation outputs Tim wants, such as likely available players at each pick, team-need pressure, value pockets, reach risk, and manual decision queue.
- Do not run a full simulation until inputs and gates are clear.

Hard rules:

- Do not touch Rookie files unless explicitly requested.
- Do not touch Outcome files.
- Do not touch production rankings, private scores, outcome columns, app wiring, Streamlit production files, veteran production logic, probabilities, bands, hidden sort keys, promoted artifacts, secrets, `data/`, or committed `local_exports/`.
- Do not push.

Start by reporting:

- Mock Draft repo/worktree/branch
- input files found
- missing files Tim needs to provide
- whether Phase 1 can proceed
- no files changed unless the prompt explicitly authorizes a tracked Phase 1 doc/script/test
