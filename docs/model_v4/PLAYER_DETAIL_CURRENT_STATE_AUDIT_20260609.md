# Player Detail Current State Audit - 2026-06-09

## Scope

This audit covers the accepted human-review pages that need a shared player inspection pattern:

- Rankings: `app/pages/05_rankings.py`
- Draft Prep: `app/pages/06_draft_board.py`
- Live Draft Room: `app/pages/07_live_draft_room.py`
- Future Roster Decisions: not wired in this task; Decision Board remains out of scope.

No formulas, active data packs, draft state, or page defaults were changed.

## Existing Detail Patterns

### Rankings

Rankings has the most complete detail pattern today. It renders a `Player detail` selectbox and an expanded `Details: <player>` expander through `_render_player_detail`.

Current sections:

- Header metrics: rank, position, age, team.
- Status line: roster/pool/private-score status.
- Why he ranks here: uses `manual_review_notes` when available; otherwise says explanation is unavailable.
- Outcome profile: explicitly shows outcome model in development.
- Private model components: NWR score, source path, source column, model version, lineage, confidence cap, confidence status.
- Trust and warnings: trust label, warning count, translated warning bullets.
- Data needed: human-readable source/data needs.
- Market / league comparison: display-only note plus market and league gaps.
- Legacy disclosure: shown only when a legacy active-pack score is present.
- Advanced source receipts and raw warnings: collapsed by default.
- Notes: says no persistent manual notes are written.

Pattern: selectbox plus expanded expander, with receipts collapsed inside the detail panel.

### Draft Prep

Draft Prep does not have a per-player detail card yet. It exposes context through:

- Pick cards for owned picks.
- Candidate-window tables by pick.
- Main `Scouting Prep Pool` table.
- Collapsed `League History Context`.
- Collapsed `Advanced Audit` with source readiness, pick rows, scouting receipts, and raw history rows.

Useful detail fields are present in `scouting_prep_pool_review_rows.csv`, but they are mostly table columns today. The page intentionally keeps raw receipts out of the default view.

Pattern: no player detail; page-level collapsed audit expander.

### Live Draft Room

Live Draft Room does not have a per-player detail card yet. It projects the scouting pool into draft session state rows and shows:

- Draft grid.
- Pick controls.
- Best Remaining / Scouting Pool table.
- My Upcoming Picks.
- Recent Picks.
- Collapsed `Advanced Session Details` with session export and remaining-pool export.

The Live Draft Room state rows currently keep a reduced set of scouting fields: player, position, NFL team, source type, draftable lifecycle, score-like display field, warning summary, draft status, and drafted pick.

Pattern: session-state tables plus collapsed session exports, no player detail.

### Future Roster Decisions

Future Roster Decisions will need a player card, but this task did not inspect or alter Decision Board code. The shared card should be designed so Roster Decisions can later supply roster pressure, forced-drop context, owner/team status, replacement context, trust, warnings, and receipts without reusing recommendation language.

## Source Fields Available

### Rankings Fields

`local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` includes:

- Identity: `player_id`, `canonical_player_key`, `player_name`, `normalized_player_name`, `position`, `age`, `nfl_team`.
- Private model: `nwr_rank`, `nwr_dynasty_score`, `score_status`, `trust_status`, `score_type`, `score_as_of_date`, `confidence_cap`, `confidence_status`.
- Roster/pool: `pool_status`, `is_my_team`, `is_available`, `is_rookie`, `roster_team_id`, `roster_team_name`, `roster_status`.
- Display-only comparison: `league_rank`, `league_rank_source`, `market_rank`, `market_rank_source`.
- Legacy/context: `legacy_active_pack_score`, `legacy_active_pack_score_allowed_use`, `risk_level`, `risk_level_source`.
- Receipts: `source_path`, `source_column`, `upstream_source_path`, `upstream_source_column`, `model_version`, `lineage_class`, `allowed_use`, `blocked_use`.
- Warnings/data: `raw_model_warning_flags`, `team_resolution_status`, `canonical_team_source`, `warning_flags`, `data_needed`, `raw_source_repair_notes`, `full_board_version`.

### Draft Prep Fields

`local_exports/model_v4/draft_prep/latest/scouting_prep_pool_review_rows.csv` includes:

- Identity/context: `player`, `position`, `nfl_team`, `college_team`, `age`.
- Pool status: `source_type`, `draftable_status`, `legal_draftable`, `roster_owner`, `protected_status`, `rookie_status`, `free_agent_status`, `dropped_veteran_status`, `manual_status`.
- Source-safe values/context: `nwr_draft_value`, `nwr_rookie_score`, `nwr_dynasty_score`, `expected_league_slot_context`, `nwr_slot_context`, `value_threshold_context`.
- Football prep context: `prospect_talent_context`, `landing_spot_context`, `draft_capital_context`, `role_path_context`.
- Trust/receipts: `trust_status`, `warning_flags`, `data_needed`, `allowed_use`, `blocked_use`, `source_path`, `source_column`, `lineage_class`.

`prior_league_draft_history_review_rows.csv` adds display-only user/history context: draft year, area, slot, drafted-at field, user rank, user note, user drafted flag, must-review-at-cost flag, highlight context, transcription confidence, allowed/blocked use, warnings, and data needed.

### Live Draft Room Fields

Live Draft Room reads the Draft Prep scouting pool, then projects it into `DraftBoardState` via `_scouting_rows_for_state`.

Current projected fields:

- `asset_id`
- `player`
- `position`
- `nfl_team`
- `asset_type`
- `asset_lifecycle`
- `why_available`
- `draft_status`
- `stats_model_value`
- `model_value`
- `market_value`
- `market_edge`
- `confidence`
- `warning`
- `recommended_range`

This projection is intentionally session/mock oriented. A future shared card should keep a lookup back to the original scouting-pool row so source path, blocked use, data needed, legal status, and prospect context are not lost.

## Warning And Data-Needed Translation

Existing patterns:

- Rankings has page-local `WARNING_EXPLANATIONS`, `_human_warning`, `_data_needed`, and `_data_needed_summary`.
- General warning text helpers exist in `src/services/warning_language_service.py`.
- Draft Prep and Live Draft Room currently show compact warning counts through page-local `_warning_summary` helpers.
- Draft Prep preserves raw warnings and data-needed fields in the Advanced Audit section.

Gap: warning translation is duplicated and inconsistent. The shared card should call one helper that can translate raw warning flags into human-readable missing-data messages while still preserving raw flags in collapsed receipts.

## Duplicated Fields

Common or near-common fields appear across pages:

- player/name
- position
- age
- team/NFL team
- source type/lifecycle
- score/value display
- trust status/confidence
- warning flags/summary
- data needed
- source path
- source column
- lineage class
- allowed use
- blocked use

## Page-Specific Fields

Rankings-specific:

- NWR rank
- NWR Dynasty Score
- market rank and NWR vs market
- league rank and NWR vs league
- legacy active-pack score
- outcome status
- confidence cap/status

Draft Prep-specific:

- pick window
- fit band
- draftable/legal status
- prospect/landing/draft-capital/role context
- prior user/history tags
- 2026 5.04 no-baseline/manual watchlist handling

Live Draft Room-specific:

- drafted status
- drafted pick
- selected pick/current pick
- hide drafted state
- best remaining context
- mock/live session state
- legal-pool-pending state

Future Roster Decisions-specific:

- roster pressure
- keep/cut context as review context only, not final recommendations
- forced-drop rule context
- owner/team status
- replacement context

## Audit-Heavy Areas

The following should stay collapsed or advanced in a shared card:

- raw warning strings
- source paths and source columns
- lineage and model version details
- allowed/blocked use receipts
- prior draft transcription details
- startup/pick equivalence/debug context
- market/league comparison details beyond concise display-only rows

## Current UX Conclusion

Rankings has a useful first version of player detail, but it is page-local and too large to copy directly. Draft Prep and Live Draft Room need a consistent shared card that starts with fantasy-football context, keeps source risk visible, and hides receipts behind a collapsed section.

