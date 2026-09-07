# NWR DRAFT ROOM — COMPLETE OWNER-FEEDBACK CLOSURE V3
## One existing Draft Room. Every requirement tracked. Real owner-build verification.

This is a continuation and consolidation of the owner's existing Draft Room feedback, not a new product, new model, or permission to start over.

Reconcile the current coherent work in progress first. Then use this document as the single acceptance contract. Earlier instructions that removed the contextual side panes, imposed an equal position quota, or treated a backend-only test as product completion are superseded by the requirements below.

PRIMARY OUTCOME:
The owner can repeatedly start, run, correct, and restart mocks in the current Draft Room; see an actionable three-pane workspace; and understand candidate differences without misleading numbers or hunting for controls.

Do not report completion after fixing only layout or only backend plumbing.

## 0. WORKING RULES AND DURABLE TRACKING

- Work in the existing consolidation lane/worktree. Inspect HEAD, dirty files, active processes, launcher targets, and the actual installed/local data root first. Preserve unrelated changes.
- Inventory Legacy, consolidated Draft Room, existing components, endpoints, stores, and prior commits BEFORE implementing any capability. Reuse/extract existing handlers; do not create another draft room, manual league setup, search engine, queue, simulator, ranking authority, or parallel state store.
- Keep the current room named Draft Room and the old one Legacy Draft Room. Preserve Legacy routes and fallback behavior; do not require Legacy for the normal workflow.
- Freeze an implementation plan before editing, but do not stop to request permission for ordinary reversible work.
- Create/update ONE owner-feedback ledger in the existing report/requirements system. Include every numbered section below with: requirement ID, owner complaint, existing implementation, precise change, test, rendered evidence, status, and unresolved reason if any.
- Statuses: NOT_STARTED, IN_PROGRESS, IMPLEMENTED_NOT_VERIFIED, VERIFIED, BLOCKED. A document, backend field, or screenshot alone is not enough for VERIFIED when an interaction is required.
- Keep historical/model artifacts intact. UI changes and faithful implementation repairs are authorized. No retraining, arbitrary score smoothing, fabricated differentiation, hardcoded player recommendations, or covert changes to frozen calibration.
- If a requested behavior needs a genuinely different statistical policy, preserve the validated reference, identify the exact limitation, and use the existing versioned challenger/capability mechanism. Do not claim changed shortlist/simulation/score behavior inherits historical validation merely because coefficients stayed unchanged.
- No push, merge, remote deployment, or automatic production promotion. Local commits and local preview builds/startup are expected. Never mutate real league boards during testing.

## 1. REPRODUCE THE OWNER'S REAL FAILURES BEFORE CHANGING THEM

Capture immutable practice-state fixtures from the relevant current states, without modifying the owner's real boards:

A. Fantasy Gamers slate with all Pick Scores 50, identical Team After and Equity.
B. Later mock state around R7 / overall 69: owner already has Kyle Pitts and other starters; Goedert/Kelce suggested; all Make-It-Back values 100%; all Pick Scores 50; Team After 99; DQ zero or unavailable for most rows.
C. QB-heavy slate containing seven quarterbacks among eight suggestions.
D. Fresh profile with no owner slot, previously requiring Legacy to start.
E. Restart, long league-name/Switch overlap, sidebar, and clipped Draft-button screenshots.

Record league/draft IDs, owner slot, pick index, every roster, available pool, data snapshots, active runtime code, endpoint, model/inference versions, candidate IDs, and numeric outputs. Preserve before evidence. Treat screenshot observations as symptoms, not proof of a particular cause.

## 2. FINAL LAYOUT — THE THREE PANES THE OWNER REQUESTED

Use NWR styling and existing components, with this functional organization:

    Compact room controls / current-pick context / search

    LEFT UTILITY PANE       CENTER WORKSPACE                  RIGHT CONTEXT PANE
    Rankings | Teams |      Suggestions | Cheat Sheets |       Selected-team dropdown
    Queue                   Draft Board                       Roster by lineup slots
    Actual player/team/     Tabs immediately above ONLY       Bench / IR
    queue content           the surface they control          ----------------------
                            Dense actionable main content      Recent picks
                                                              Picks until MY turn

- Primary tabs belong directly above the center content, not across unrelated side panes or separated from their content by large banners.
- Right pane defaults to MY TEAM. Move the owner-position counters and detailed roster context out of the center into that pane.
- Left pane must show real scrollable Rankings/Teams/Queue content, not just chips that lead to other pages.
- Both contextual panes can collapse independently. Distinguish them from the global application navigation.
- Keep the center dominant. Use responsive sizing and independent pane scrolling, not three oversized dashboards.
- Remove repeated league-name heroes, tab descriptions, permanent keyboard instructions, CPU NORMAL hero cards, duplicated on-clock summaries, and decorative empty space.
- Current pick, next owner turn, and actual controls remain useful; reduce them rather than deleting essential context.

## 3. GLOBAL NAVIGATION FULLY HIDDEN IN DRAFT MODE

The owner does NOT want a permanent icon rail taking draft space.

- Global navigation slides fully against/off the left edge, leaving only a small visible arrow/handle.
- Click the arrow to reveal it; click again or dismiss to close. Keep keyboard accessibility and clear focus behavior.
- Remember the preference per the existing settings mechanism. Do not globally alter other pages without need.
- The contextual Rankings pane remains a separate part of the draft workspace.
- No empty reserved strip when navigation or the details drawer is closed. No hidden nav capturing clicks or keyboard focus.

## 4. RIGHT ROSTER PANE AND RECENT PICKS

- Default roster dropdown to the owner's team. Allow inspecting any opponent without changing the ACTIVE league, owner slot, or whose recommendations are computed.
- List players in actual QB/RB/WR/TE/FLEX/Superflex/K/DST slots, then bench and IR. Show empty slots and counts; never double-assign a player to multiple slots.
- Use actual eligibility and configured slots, not universal 1QB assumptions. Show position/team context compactly.
- Below the roster, add recent picks: round.pick, player, position, selecting fantasy team. Update immediately on pick, undo, correction, restart, and sync.
- Show next OWNER pick and number of intervening selections clearly. Viewing an opponent does not change whose turn is being counted.
- Audit demand labels so filled starter slots, teams still needing starters, and picks before the owner are not conflated. FLEX/Superflex demand must not double-count the same player.

## 5. TWO DRAFT BOARD VIEWS

Reuse the corrected board. Add/reuse a compact view selector:

- BY ROUND: one fixed column per fantasy team; rows are rounds; snake order maps picks correctly while team columns remain fixed.
- BY ROSTER: same fixed fantasy-team columns; rows/groupings are lineup positions and bench, not when players were drafted.

Test 8/10/12/16 teams. Horizontal board scrolling is acceptable; arbitrary wrapping into 8/12 visual columns is not.

Keep team headers/round or position labels visible where practical. Distinguish the owner and on-clock team, use consistent position colors, and show drafted players' details/actions on click. The view switch must not mutate draft state.

## 6. ROUND.PICK EVERYWHERE, WITHOUT CORRUPTING ADP

The owner prefers 4.12 / 7.03 to overall pick numbers.

Use shared display helpers across current pick, next pick, board, recent picks, queue/details, suggestions, rankings, and cheat sheets.

For an integer overall pick p in an N-team draft:
- round = floor((p - 1) / N) + 1
- pick-within-round = ((p - 1) mod N) + 1
- display R.PP with two digits after the dot; it is a string, NOT a decimal number.

Examples: overall 69 in 10 teams = 7.09; overall 47 in 12 teams = 4.11. Snake team ownership is separate from this chronological notation.

ADP:
- Preserve original numeric overall ADP and provider-formatted ADP in storage. Sort and calculate market gaps numerically.
- Show approximate round.pick for numeric average ADP using a documented rounding policy, with original value/source league size in a tooltip.
- Converting a 12-team source to a displayed round in a 10-team league is DISPLAY CONVERSION, not a newly validated 10-team market forecast. Disclose source context.
- Never parse 4.12 as 4.12 overall picks. Never guess the source team count from the active league.
- For an imported round.pick string with unverified source settings, preserve it and mark its context unknown rather than inventing an overall pick.

## 7. CHEAT SHEETS — POSITIONAL UDK STRUCTURE, NOT ANOTHER OVERALL TABLE

Inspect the actual owner file:
`UDK - Position Rankings - Fantasy Footballers Podcast.csv`

It was inspected in ChatGPT: 36 rows, all QB. Exact headers:
Name, Position, Team, Bye Week, Rank, Points, Risk, Upside, ADP, Tier, Outlook, Dynasty, Markers.

Use that structure as the explicit reference:
- Distinct QB/RB/WR/TE/K/DST sections or adjacent positional tier columns at usable desktop widths.
- Position rank and compact tier separators are primary; Overall and FLEX views remain available.
- Useful compact fields: rank, player, team/bye, tier, ADP, projected points; source Risk/Upside and Outlook in details where available.
- Preserve NWR vs UDK/provider provenance. UDK positional Rank is not NWR overall rank; UDK Points/Risk/Upside are not automatically approved NWR model inputs or validated confidence.
- This particular CSV does not supply RB/WR/TE/K/DST rows. Reuse existing admitted exports for those positions. Never invent missing UDK ranks or label NWR data as UDK.
- `Dynasty` contains locked-content text, not a numeric rating. `Markers` contains action labels such as Mark Drafted/Mark Keeper/Mark Favorite/Mark Watchlist/Mark Avoid, NOT actual flags proving all rows are drafted or marked. Do not ingest them as active boolean state.
- Inspect provider ADP context before translating its strings; some entries use pick-within-round values beyond 12.
- Reuse the existing source selector so NWR and available UDK/provider rankings can be inspected without overwriting each other. Sort Rank/Points/ADP numerically with missing values last; never lexicographically sort displayed round.pick strings.
- Keep uploaded subscriber content private and under existing data-handling rules. Locate an accessible local copy; do not pretend a ChatGPT sandbox path exists on the owner's Windows machine.

## 8. DRAFTED PLAYERS DISAPPEAR CONSISTENTLY

Hide drafted players immediately by default from Suggestions, left Rankings, Cheat Sheets, normal search, and actionable Queue.

Provide Show Drafted where useful, with clearly disabled Draft actions. Restore availability correctly on undo/replace/clear/restart. Preserve original source ranks/tiers; do not renumber them merely because players were selected.

Use one canonical available-player state. No independent tab-specific draft filters that drift after switching league or restarting.

## 9. SEARCH, POSITION FILTERS, AND ACTIONS FROM EVERY SURFACE

- Suggestions needs All/QB/RB/WR/TE/FLEX/K/DST filters. FLEX means actual configured eligibility; OP/Superflex is not silently treated as ordinary FLEX.
- Apply position filters to the eligible candidate pool BEFORE shortlist truncation. A DST filter must not show empty merely because the default top eight had no defenses.
- Keep search obvious and usable by mouse and keyboard. Reuse existing lookup for name, NFL team, and position; tolerate normal name punctuation/spelling variants.
- Search must work independently of advanced-score availability.
- Suggestions, left Rankings, positional Cheat Sheets, Queue, and search results all support Draft / Queue / Details.
- The player popup/drawer MUST include a visible Draft button plus Queue. Do not require leaving the popup or remembering a secret shortcut.
- Attribute picks to the actual on-clock team by default with clear owner/opponent context and an explicit correction path. Clicking Details must never draft a player.
- DATA_LIMITED players, rookies, K/DST remain findable, draftable where legal, and visible without fabricated scores.

## 10. SELF-CONTAINED LEGACY CONTROL PARITY

Reuse the existing Legacy handlers and client calls inside the CURRENT room:

- Draft mode: Mock/CPU, manual/live tracking as already supported.
- My slot; Start; CPU speed; existing Pause/Resume, One CPU Pick, and Advance to My Pick controls where applicable.
- New/Restart; Undo; existing save/load/duplicate mock, event log, export/import/restore tools where supported.
- Refresh FFC ADP; Paste Rankings/ADP; Import Owner ADP CSV.
- Existing Replace Pick, Clear Pick, Fill Gap/correction operations.

Keep setup controls compact/collapsible. Restart is easy to reach in Mock mode; destructive restart/league switch in real tracking needs deliberate confirmation and must not be a stray-click risk.

No normal operation may require Legacy navigation. No new profile is necessary to restart. Preserve league settings and data; explicitly state whether queue is preserved/reset. Archive the previous practice run/log rather than overwriting its evidence.

Clarify auto-advance: a new mock may contain CPU picks before the owner's slot, but that must be disclosed. Offer/reuse a paused clean-start state to verify zero picks, and ensure old picks never survive a restart.

Do not impose a universal rule that roster size must equal draft rounds; IR, keepers, and supported special formats may differ.

## 11. QUEUE, COMPARE, AND PRIOR SMALL FEATURES

Reuse working Queue: add/remove/reorder, jump to details, draft directly, handle another team taking a queued player, and avoid cross-draft leakage.

Retain Compare and existing favorite/watch/avoid controls where implemented. Lower-priority history, draft analysis, trades, saved mocks, and import/export tools must not silently disappear during consolidation; map them to compact secondary controls or explicitly preserved Legacy-only archival features, not duplicate replacements.

Latest owner requirements take precedence over superseded layouts/names. Do not resurrect old dynasty-only behavior or rename this room again.

## 12. FIX OVERLAP, CLIPPING, AND DENSITY IN THE ACTUAL OWNER BUILD

- Repair Switch/ADP/status badge overlap at long profile names and collapsed navigation widths. Use separate layout cells, correct shrinking, ellipsis plus tooltip, and no overlaid hit targets.
- Fix sticky/global-header overlap with the title or controls. No content hidden behind the top bar.
- Draft buttons and player names must never be clipped off the table's left edge after horizontal scroll. Pin essential identity/action columns where appropriate.
- Compact current-pick row; roster information on the right; source freshness as small chips; close-call explanation inline/expandable rather than large banners.
- Remove repeated RESEARCH/EXPERIMENTAL wording from column headers while keeping evidence status visible in compact badges and details. Do not hide limitations entirely in tooltips.
- Render at approximately 1280x800, 1366x768, and 1650x930, including windowed and maximized desktop. With optional details closed, prioritize visible actions and roughly 8–12 rows at larger viewports; do not achieve this by making text unreadable.
- No page-wide horizontal overflow caused by side panes. The board/table may scroll inside its own container.

## 13. TRACE LIVE NUMBERS FROM THE ACTUAL UI, NOT A DETACHED MODULE

For the reproduced fixtures trace:

UI request -> actual endpoint -> authoritative draft state -> candidate roster clone -> feature vector -> raw Team Score -> calibrated score/reference population -> Equity -> completion/rollout -> Raw Action Value -> regret -> Pick Score -> serialized fields -> visible cells/drawer.

Identify the FIRST cause of uniform output or missing evaluation. Check:
- wrong V1/V2 endpoint or legacy fallback;
- candidate ignored/not inserted;
- mutated shared rosters or reused cached candidate state;
- tiny/degenerate comparison population, ceiling/floor saturation, rounding;
- deterministic opponent policies that ignore seeds/budgets;
- incomplete shortlist evaluation, early truncation, stale nulls;
- continuous values calculated in an unused module;
- UI rendering a different field from the tested one.

Cache keys must include league/config, draft/version, owner roster, complete opponent/available state, candidate, data/model versions, and inference settings as required by the computation.

Do not claim the problem fixed only because a new DQ column differs while the main score remains misleading or the live UI calls the old endpoint.

## 14. PICK SCORE, DQ, AND TEAM AFTER — HONEST SEMANTICS AND RESOLUTION

The owner sees identical 50 / 99 / zero or n/a values across different actions and cannot decide from them.

- Diagnose actual ties versus lost resolution. Preserve continuous underlying values; do not inject noise, spread equal values artificially, add decimals for appearance, or relabel a shortlist rank as historically calibrated decision quality.
- Every evaluated row should have its actual RAV/DQ/regret or a specific status: computing, budget-limited, unsupported, missing input. Never zero-fill missing results. Support on-demand evaluation of a searched/queued candidate outside the initial shortlist.
- Primary Pick Score must retain its documented scope. If the live score is only a within-slate relative rank, disclose that; it is not automatically the user's intended stable action-quality percentile.
- Filtering/sorting/paging must not silently change a candidate's absolute evaluation. Where a metric inherently depends on the comparison set, identify that dependency rather than pretending otherwise.
- Model/inference parameter changes, including larger Monte Carlo budgets, must be versioned, latency-tested, and compared to the prior path. Unchanged coefficients alone do not prove unchanged behavior.

TEAM AFTER:
- Distinguish current partial roster value from PROJECTED FINAL TEAM IF THIS PLAYER IS TAKEN.
- Do not describe full-draft-completion value as immediate single-player improvement.
- A delta must compare the same objective, completion horizon, league, and reference population on both sides. Subtracting an empty/partial roster score from a completed-roster forecast is not a meaningful isolated pick delta merely because the subtraction is arithmetically correct.
- Use paired completion scenarios for candidate comparisons where already supported. If a valid common baseline is unavailable, show candidate-conditioned final strength without a misleading delta.
- Real indistinguishable actions should display a close-call/tie indication, not fake precision. Expose independent market and roster context to help the owner decide.

## 15. MAKE-IT-BACK — AUDIT THE 100% SCREEN

All candidates at the reported state showed 100%. That is not automatically an implementation defect, but it must not imply guaranteed availability.

Verify the event definition: available when the owner next selects, conditioned on current availability and the actual intervening teams/picks. Check snake turns, owner slot, filtering, rounding, legal candidate coverage, sampled policies, and fallback behavior.

- Retain/reuse the existing opponent-roster-aware model. Do not create a second demand engine.
- Determine whether 100% is rounded probability, no picks intervening, all finite sampled trajectories surviving, or a deterministic ADP threshold.
- Distinguish deterministic/structural certainty from simulation frequency. When all N simulated drafts preserve a player, disclose that finite-sample fact and that reaches remain possible; do not label it guaranteed.
- Do not mechanically replace all 100% with 99%, invent reach probabilities, or introduce unsupported stochastic assumptions solely to make the display look better.
- Cross-check Make-It-Back against Cost of Waiting and expected replacement loss. Zero wait cost can be legitimate when alternatives are equivalent; unavailable calculations must not silently become zero, and a player certain to disappear with positive replacement loss cannot be presented as costless to wait on under that stated definition.
- In controlled comparable 1QB scenarios, verify opponent starter needs affect demand among the teams that actually select before the owner. Filling QB1 does not prohibit backup picks; Superflex/2QB must use their own requirements. Do not equate all-opponent counts with the intervening pick sequence.
- Check missing/unknown inputs and DATA_LIMITED rows do not default to 100%.
- Test warm vs cold cache, reproducible seeds, meaningful budget changes, opponent roster changes, and whether model outputs actually respond to each input.
- If changing opponent/reach assumptions is required, register a separate challenger, validate on permitted evidence, and label its scope. Never silently claim the existing calibration covers a newly invented behavior.

## 16. ROSTER-AWARE SECOND TE / QB DECISIONS

The owner drafted Kyle Pitts in round six; the next round suggested Goedert and Kelce. Also audit prior seven-QB suggestion slates.

- Separate legal roster caps from strategic value. A legal second TE is not automatically a good pick; an equal position quota is not intelligent roster construction.
- Check starter slot, FLEX eligibility, bench need, viable later replacements, opportunity cost, and actual candidate-conditioned terminal value.
- A second TE may be justified, but explain whether it upgrades a starter, competes for FLEX, or adds depth. Do not recommend it only because the round-robin selector owes TE two slots.
- Remove hard 2/2/2/2 suggestion quotas as the default decision policy. Show strongest supported overall actions; expose best positional alternatives without silently evicting superior same-position candidates.
- Position-filtered mode must show eligible depth on demand, including TE/K/DST.
- No blanket age penalties or hardcoded anti-Kelce/Goedert decisions. Use verified current outlook/role/age context where allowed; preserve governance around model-use age/rookie data. The named players are regression examples, not required winners/losers.

## 17. VERIFY PICK EVALUATION: QB NOW VS RB NOW / QB LATER

Reuse the existing RAV/lookahead/counterfactual path. The owner's example is:

A. Maye around overall 47, then best attainable RB/WR later.
B. Stronger RB/WR now, then Stafford around a later QB tier near overall 100, with alternatives if he is taken.

The numbers are illustrative, not current player advice or a promised future pick.

Prove the engine compares completed feasible roster paths, including actual future owner selections, intervening opponents, replacement alternatives, uncertainty, and opportunity cost. Never assume Stafford certainly survives or compare just Maye's standalone value with Stafford's.

Use consistent terminal objective and paired conditions; avoid adding an explicit waiting penalty on top of a rollout that already charges the same lost-player opportunity.

Provide a compact Why explanation of the path tradeoff. If the existing engine only scores immediate additions, disclose that limitation and close it through the existing versioned path rather than calling a one-step metric multi-pick planning.

## 18. ACTION AND VALUE ARE SEPARATE COLUMNS

Replace ambiguous DEEP TARGET / GOOD VALUE labels in the Action column.

ACTION = what to do now, for example:
Pick now | Consider now | Wait until next turn | Wait one round | Revisit later | Need more data.

VALUE = market context, for example:
Falling | Value | Fair | Reach | Market unknown.

- Derive labels from actual state and supported outputs, not decorative text.
- Identify players who have fallen relative to the active market, so real bargains are visible before remote deep targets.
- A fall relative to ADP is not automatically a good football value; injuries/news can explain it. Conversely, an intentional reach may be justified by roster/timing value.
- Show the numeric market gap in details with its source. Missing ADP is unknown, not an extreme bargain.
- Waiting advice must refer to a real future owner turn. 'Wait one round' cannot be a promise based only on ADP.
- Display horizons in round.pick; keep the underlying calculations in overall picks.
- Reuse existing action/value logic where sound. Any new display thresholds must be documented as UI heuristics, not claimed calibrated probabilities.

## 19. NEWS, CURRENT DATA, AND LIMITED PLAYERS

- Reuse the existing alert/current-data refresh and secure credential mechanisms. The owner previously obtained FantasyPros API access; check authorized local configuration before asking again. Never print/request keys, cookies, or tokens in chat; do not bypass access controls or buy services.
- Refresh approved sources where possible; timestamp retrieval and provider/source publication separately. Renewing a governance receipt does not make old projections or news fresh.
- Audit why projected data still shows August 8 and alerts show roughly 90–94 hours old. Report real refreshed coverage, not just a changed badge.
- Puka Nacua is a named NEWS-COVERAGE test. Verify current reputable reporting/official status before displaying anything; do not hardcode earlier allegations, claim guilt, or invent suspension status from chat prose.
- Separate confirmed injury/suspension/role news, reported risk, and unknown/stale source coverage. 'No alert in this snapshot' is not 'no real-world issue.'
- Compact freshness chips in the workspace; player-specific material risk visible on the row/card; source/time/neutral summary in expandable News.
- Retain all real rookies and K/DST in the legal pool. Missing projections or outcome support must remain explicit; never silently drop them or fabricate zero/complete model scores.
- News/UDK commentary cannot secretly alter frozen weights. State when the model has NOT incorporated a warning.
- If refresh is blocked, name the exact missing permission/credential/source once, continue unrelated product repairs, and do not call the real-draft data fully ready.

## 20. COMPACT PLAYER POPUP THAT CAN ACTUALLY DRAFT

Reuse the current drawer and make it work from every entry point:

Player / position / team
Draft | Queue | Compare where supported
Pick Score; correctly labeled Team/Delta; Make-It-Back; Equity where supported; Player Score; ADP
Action and separate Value
Why | News | Details expanders

No debug wall, stacked stale paragraphs, undefined DQ abbreviation, or LOW_MODEL_UNCERTAINTY inferred from zero SE. Decision Confidence remains unvalidated and non-authoritative.

Use the same candidate data as the table; show pending/not-evaluated honestly, with on-demand evaluation. The drawer must not permanently replace the roster pane or cover the only Draft action. Close/Escape returns all space and focus.

## 21. SINGLE SOURCE OF STATE AND SAFE FALLBACK

- Picks, queue, availability, all rosters, current turn, demand, and view filters must stay coherent across tabs/panes and browser/desktop reloads.
- Async old responses must not overwrite a newer league/draft/pick state. Cancel or reject stale response revisions.
- Pick writes must resist double-click/Enter duplication; buttons show pending status and recover from errors.
- If advanced analytics fails, rankings/search/queue/board/pick capture/undo still work with an explicit limited-mode status. Do not replace the workspace with a giant dead DecisionBundle panel.
- A data-limited selected player must not leave the roster-wide forecast falsely complete. Explain any coverage limitation in the aggregate.
- Preserve real KHA/Fantasy Gamers boards byte-for-byte before and after isolated QA; owner-approved practice reset is separate.

## 22. LAUNCH THE ACTUAL BUILD THE OWNER IS TESTING

- Verify shortcut -> launcher -> worktree/HEAD -> frontend -> backend -> data root -> hash route. UI route is `#/draft-room-v2`; do not mistake a Legacy fallback route for the consolidated room.
- A listening port 1422/Vite process does NOT prove a Tauri window exists. Reuse/focus a verified existing GUI, launch the shell against a verified compatible server, or restart only the positively identified stale managed process safely.
- Do not kill processes solely by port or all node/python processes. Keep agent test servers from occupying the owner's launch path; use separate test ports/settings where supported and clean up only your own processes.
- Avoid concurrent heavy suites/dev stacks during low memory. Save a durable checkpoint rather than leaving endless duplicate wakeups and orphan servers.
- Verify reopening the normal shortcut twice behaves safely and opens/focuses the intended window. Do not make the owner run netstat/taskkill again.
- Provide a compact build identity in About/Details so the owner can confirm the tested build, without adding more header clutter.

## 23. RENDERED ACCEPTANCE — EVERY COMPLAINT GETS A TEST

Use the established Vite/backend/browser GUI tools, then smoke-test the normal owner launcher. Browser-only evidence is useful but must not be called completed Tauri-launch verification.

Fresh mock, no Legacy visit:
1. Select profile/slot/mode/speed; start paused; verify clean state and controlled CPU advance.
2. Search by name, team, position; queue; draft from search, left Rankings, player popup, Suggestions, and Cheat Sheets.
3. Confirm drafted player disappears everywhere; undo restores; correction/clear/fill-gap works; restart preserves settings and contains no prior-run picks.
4. Test all three center tabs directly above their content, left utility content, right roster dropdown, recent picks, and owner-next-turn count.
5. Test by-round/by-roster boards at 8/10/12/16 and snake transitions; verify round.pick and numerical ADP sorting/conversion.
6. Reproduce Kyle Pitts -> next-round TE choices, QB-overload, and full opponent QB starters vs missing starters; inspect causes, not forced winners.
7. Reproduce R7/69 uniform scores/100% availability, audit every numeric stage, and prove the visible result is fixed OR honestly identifies genuine unsupported discrimination.
8. Test an unfiltered strong same-position slate is not amputated into a 2/2/2/2 quota. Test TE/FLEX/DST filters on the full eligible pool.
9. Demonstrate falling value vs deep reach, separate Action/Value, and Maye-now vs RB-now/later-QB path explanation.
10. Test stale/missing news, verified current alert, DATA_LIMITED rookie, K/DST, and missing ADP; no false clearance or fabricated scores.
11. Test global nav fully hidden, pane/drawer collapse, long selector text, small desktop viewport, table scrolling with Draft buttons visible, and ordinary keyboard use.
12. Test degraded analytics, asynchronous league switching, double-click pick, restart/resume, and normal launcher repeat.

At least one complete GUI-driven mock must exercise search/draft/undo/correction/restart; a handler-level scripted tournament is not a substitute. Do not claim a human owner test unless the owner performed it. Preserve exact before/after screenshots and state/output evidence for the named failures.

## 24. COMPLETION, EVIDENCE, AND HANDOFF

Update the existing report plus the requirement ledger. For each section provide implementation location, test evidence, screenshot/interaction evidence, and exact remaining limitation.

Report test identities/deltas against the verified base commit, not just equal failure counts. The known suite is flaky; unchanged counts alone are not proof of no regressions. Run focused unit/integration tests, frontend typecheck/build/tests, relevant GUI tests, and a controlled regression comparison without changing unrelated legacy failures.

Include:
- Starting/ending HEAD; owner launcher/build identity; frozen model/inference hashes.
- Full requirement closure map, including every layout and minor workflow request.
- CSV mapping and positional coverage, not invented UDK data.
- Exact causes/fixes for ties, survival certainty, TE/QB slate behavior, and misleading deltas.
- What remains a model/evidence limitation rather than a software bug.
- Current-data freshness and credentials/source blockers without secrets.
- Latency for full candidate batch, search-to-pick, warm/cold state, and on-demand evaluation.
- Prospective practice logs with state, data/model versions, displayed metrics, recommendations, and actual owner picks; no training on these mocks.
- One launch instruction and a short owner verification sequence.

Final statuses must be separate:
WORKFLOW: PASS or BLOCKED
LAYOUT: COMPLETE or INCOMPLETE
NUMERIC TRUST: SUPPORTED / LIMITED / BLOCKED with exact scope
DATA FRESHNESS: CURRENT / LIMITED / BLOCKED with timestamps

Overall:
GREEN_ALL_OWNER_FEEDBACK_CLOSED
only when every requested product behavior is verified and numeric limitations are honestly represented, not hidden.

Otherwise:
YELLOW_OWNER_FEEDBACK_PARTIALLY_CLOSED
or
RED_DRAFT_ROOM_CORE_WORKFLOW_BLOCKED
with the exact outstanding requirement IDs. Do not call this all fixed when ADP controls, popup drafting, filters, right roster, recent picks, or any other requested feature was quietly deferred.

Continue through ordinary reversible fixes without requesting approval after every subtask. Stop only the affected branch for an actual safety/integrity/authorization blocker; continue independent safe items. No extra speculative features or broad research detours.

THE OWNER ALREADY TESTED THE APP AND GAVE SPECIFIC FEEDBACK.
Implement that feedback, preserve what works, and verify the exact product the owner will open.
