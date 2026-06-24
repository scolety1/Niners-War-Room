# NWR Draft-Day App V2 Requirements - 2026-06-23

Source feedback: Google Doc `Issues After Draft`.

This package converts post-draft feedback into V2 requirements only. It does not approve code changes, source-truth mutation, model promotion, latest file updates, or any DynastyProcess/app wiring.

## Executive Summary

Draft-Day App V1 was technically usable, but it failed at several real on-clock workflows. The biggest failure was that drafted-player state lived only in session state, so a reload erased pick history. The second major gap was no way to record in-draft trades, such as trading away 1.04 for a 2028 1st plus 2.03. Player Compare had useful information but was too hard to process under pressure. The next version should be built around Drafting Mode: a persistent, pick-by-pick draft room with draft state, trade events, cheat sheets, search, player compare, and trade tools all tuned for fast decisions.

## User Pain Points

- Reload erased who had already been drafted.
- In-draft trades could not be entered or reflected in the board.
- The user had to draft for other teams after a trade because ownership/pick context could not be updated.
- Player Compare contained useful data but was too confusing when deciding between players.
- Injury modeling was unclear: per-game production, injury-shortened yearly totals, recovery risk, and chronic injury risk were not visibly separated.
- No tool existed to find trade-back options when the current pick felt bad.
- No tool existed to find the cheapest way to trade up for a falling player.
- Draft room navigation did not feel like a dedicated mode.
- The user wants Drafting Mode and Normal/Post-Draft Mode separated.
- The user wants a top-left Enter Draft Room button, with Live Draft or Mock Draft choices.
- The draft room should look consistent whether it is the user's pick or another team's pick.
- The user wants fast player search for off-table picks.
- The user likes a Your Team sidebar.
- The user wants configurable information density and model-native note styles.
- Cheat sheets should emphasize overall rankings and clear tiers more than position-only lists.

## Priority Summary

### P0

- Persistent draft state with reload restore.
- Draft event log for every pick/trade/edit/reset.
- In-draft trade events that update pick ownership and draft board context.
- Pick-by-pick Drafting Mode shell that works for user picks and other teams' picks.
- Search and manual player selection for any draftable player.
- Reset with confirmation and exportable draft log.

### P1

- Player Compare V2 decision summary.
- Trade Finder for trade-back options.
- Trade For for acquiring a pick when a player falls.
- Cheat Sheet / overall tiered board.
- Your Team sidebar.
- Configurable information density and notes.
- Injury/per-game/risk model audit and display contract.

### P2

- Normal/Post-Draft Mode separation.
- SOS-like model-native sections if NWR has equivalent data.
- Advanced trade scenario review and post-draft recap.
- Richer settings/data-health UX for draft runtime files.

## Drafting Mode Requirements

- Add an obvious `Enter Draft Room` action near the top left of the app shell, near but separate from deploy/runtime controls.
- Enter Draft Room presents a choice between `Live Draft` and `Mock Draft`.
- Drafting Mode is task-focused and hides normal app clutter.
- Drafting Mode tabs should include:
  - Cheat Sheets
  - Draft Board
  - Trade Lab
  - Player Compare
  - Search
  - Settings / Data Health
- Drafting Mode should use one shared draft state service for Live Draft and Mock Draft.
- Drafting Mode must support both user picks and other teams' picks with the same pick-by-pick layout.
- Drafting Mode should prioritize best player at value, not team-need-first recommendations.

## Normal / Post-Draft Mode Requirements

- Normal Mode is the regular app outside the live draft workflow.
- Post-Draft Mode focuses on review, roster implications, trade follow-ups, and lessons learned.
- Post-Draft Mode must not reuse Drafting Mode state as if it were source truth without a completed draft import/review step.
- Post-Draft Mode should allow draft log review, selected/passed player review, and next-actions triage.

## Live Draft Room Requirements

- Must persist picks and trades outside Streamlit session state.
- Must restore state after reload.
- Must show the current pick, current owner, original owner, and whether it is an NWR pick.
- Must support selecting a player for another team's pick.
- Must support search when the picked player is not near the top of the table.
- Must support undo/edit/remove pick.
- Must prevent duplicate player selection or warn clearly.
- Must hide drafted players by default, with a toggle to show them.
- Must show a draft board and a main ranking/cheat-sheet table without table sprawl.
- Must keep Final Board Rank visible where relevant, but allow review-only on-clock/candidate ranks as decision aids.

## Mock Draft Requirements

- Mock Draft should use the same persistent draft state/event framework, but stored in a mock namespace.
- Manual mock picks must be separate from simulator logic.
- Simulator/model value logic must not change unless explicitly authorized later.
- Mock Draft should allow reset/export without affecting Live Draft state.

## Persistent Draft State Requirements

- Draft state must survive browser reload and Streamlit rerun.
- Runtime storage path: `C:\NWR_SHARED_DATA\draft_day_runtime\`.
- Store:
  - active draft id
  - mode: live/mock
  - pick assignments
  - trade events
  - pick ownership changes
  - undo/edit history
  - created/updated timestamps
  - source checkpoint and app commit
- Export:
  - draft log CSV
  - draft log JSON
  - human-readable draft recap markdown
- Reset requires explicit confirmation.
- Runtime storage must not mutate frozen board/source truth.
- Runtime storage must not be committed.

## In-Draft Trade Event Requirements

- Must support trading picks during the draft.
- Example trade to support: NWR trades away 1.04 and receives 2028 1st + 2.03.
- Trade event entry must capture:
  - timestamp
  - teams involved
  - NWR gives
  - NWR gets
  - current-year picks
  - future picks
  - players, if any
  - notes
- Current-year pick ownership updates the draft board immediately.
- Future picks are recorded in the event log and Your Team/sidebar context.
- Trade events must not run a trade calculator or final advice model unless explicitly added later.
- Trade events are draft-state events, not source-truth mutation.

## Player Compare V2 Requirements

- Must reduce pressure-time cognitive load.
- Default compare output should start with a decision summary:
  - quick verdict
  - why draft Player A
  - why draft Player B
  - biggest risk
  - what would change the decision
  - confidence
- Detailed data should be behind expanders/tabs.
- Support 2-4 players.
- Show comparable fields side-by-side without raw table clutter.
- Include injury/per-game/risk context when available.
- Missing data must say `Not enough information`.
- Candidate/review-only context must be labeled.

## Trade Finder Requirements

User story: "I don't like this pick. Find trade-back options."

- Input: current pick, board tier, players available, owned roster/picks, optional trade partners.
- Output should be conservative decision support:
  - possible trade-back ranges
  - picks/players to ask for
  - tier-drop risk
  - player targets likely still available
  - confidence
  - manual review notes
- Should not generate final trade advice unless later approved.
- Must not use external trade calculators as model inputs.

## Trade For Requirements

User story: "A player is falling. What is the cheapest way to trade for that pick?"

- Input: target player, target pick, current owner, NWR assets, available picks.
- Output:
  - cheapest plausible packages by internal context
  - overpay warning
  - whether target is worth pursuing
  - impact on current/future picks
  - confidence and caveats
- Must support pick acquisition during the draft.
- Must write accepted trades into the draft event log.

## Injury / Per-Game / Risk Model Requirements

V2 must separate these concepts:

- Per-game performance: how good the player is when active.
- Yearly totals: total season value including missed games.
- Injury-shortened-year context: strong per-game profile but reduced totals due to injury.
- Future recovery risk: return from ACL/major injury or similar.
- Chronic injury history risk: repeated missed time or fragile profile.
- Current injury/status risk: latest known current-state issue.

Required outputs:

- injury_data_available: yes/no
- per_game_signal_available: yes/no
- annual_total_signal_available: yes/no
- injury_history_risk_band
- current_recovery_risk_band
- model_treatment_summary
- human_review_warning

Missing injury data must not be treated as clean health. It should be `Not enough information` or a confidence cap.

## Cheat Sheet / Tier Display Requirements

- Cheat Sheet should emphasize overall ranking first.
- Position tabs can exist, but overall is the primary draft-day view.
- Tiers must be visually separated.
- Show enough players for the user's current settings.
- Configurable display:
  - number of players shown
  - summary notes
  - detailed notes
  - expert-style notes, if NWR has support
  - model-native SOS-like sections only if data exists
- Cheat Sheet should work pick-by-pick and remain useful when it is not the user's pick.

## Search Requirements

- Global draft room search.
- Search by player name.
- Search must include players not visible in the top table.
- Search result should allow marking player drafted for current/selected pick.
- Search must show source coverage and missing-data warnings compactly.

## Your Team Sidebar Requirements

- Left sidebar can show:
  - current NWR roster
  - owned picks
  - future picks
  - trades made during this draft
  - drafted players
  - needs/context as optional, not primary ranking logic
- Team needs should not override best-player-at-value posture.

## Settings / Data Health Requirements

- Show draft runtime path.
- Show active draft id.
- Show app commit/source checkpoint.
- Show frozen board path and row count.
- Show whether draft state autosave is active.
- Show last autosave time.
- Show event log count.
- Show warning if runtime folder is unavailable.
- Show explicit `not source truth mutation` label.

## Guardrails

- Do not mutate Frozen Final Draft Board V1.
- Do not change Final Board Rank.
- Do not overwrite Dynasty Rank.
- Do not update latest_candidate or latest_approved.
- Do not mutate pinned snapshot.
- Do not fabricate players, trades, picks, ranks, injuries, ages, or probabilities.
- Do not use ADP, market rankings, projections, trade calculators, DynastyProcess values, or vendor ranks as model inputs.
- Display-only market context must be labeled.
- Runtime draft state must remain local-only and untracked.
- No hidden sort fields.
- No hosted deployment.

## Recommended First Lane

Start with Persistent Draft State + Event Log. It fixes the reload-loss P0 and creates the foundation for in-draft trades, mock/live shared workflow, draft log export, and post-draft review.
