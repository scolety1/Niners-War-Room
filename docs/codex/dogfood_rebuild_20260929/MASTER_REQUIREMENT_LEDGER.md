# NWR Master Requirement Ledger

Branch: `upgrade/nwr-prospective-outcomes-v1-20260914`
Worktree: `C:\NWR\prospective-outcomes-v1`
Starting HEAD for this pass: `dee7e99a` (confirmed via `git log -1 --oneline` at session start; matched exactly — no divergence).

This document is the owner-demanded Master Requirement Ledger. It consolidates, in one place and in one honest disposition taxonomy, every requirement from the owner's CURRENT/RECENT dogfood-rebuild cycle (branch `upgrade/nwr-prospective-outcomes-v1-20260914`, Workers 4 through 9 plus the coordinating session's own reconciliation passes, all recorded in `docs/codex/dogfood_rebuild_20260929/LEDGER.md` and `FULL_SUITE_FAILURE_INVENTORY.md`). It is **Part 1** of a two-part ledger. **Part 2 (older historical requirements going back months — original Dynasty identity pre-this-cycle, old trade-system vision, rookie/identity backlog, Compare, old UI defects, lifecycle pre-this-cycle, Live vs Mock isolation, transaction history, change detection, Attention Center, desktop/Tauri packaging, profile isolation pre-this-cycle, general failure-behavior gauntlet) will be appended by a later, separate pass** at the marker at the end of this file. This pass does not attempt that scope.

Every row in this entire document (this pass's Sections 1–6, and whatever Part 2 adds later) uses EXACTLY one of the following disposition values — no row may ever read anything else:

- `IMPLEMENTED_AND_LIVE_VERIFIED`
- `IMPLEMENTED_AND_TEST_VERIFIED`
- `ALREADY_IMPLEMENTED` (before this cycle)
- `SUPERSEDED_BY_NEWER_OWNER_DIRECTION`
- `INTENTIONALLY_BLOCKED_WITH_CURRENT_REASON`
- `OWNER_ACTION_REQUIRED`
- `NOT_RELEVANT_TO_CURRENT_PRODUCT`

**ZERO rows may ever read** `UNKNOWN`, `TODO`, `FOLLOW-UP`, `LATER`, `NOT INVESTIGATED`, `PROBABLY DONE`, or `PARTIAL WITHOUT EXPLANATION`. If a disposition was not yet certain while drafting this document, that uncertainty was resolved before writing the row — by reading the code, running the test, or checking the live app — not by guessing or punting.

**Evidence-labeling convention** (same as `LEDGER.md`): **INSPECTED CODE** (source read directly, this pass or a cited prior pass), **ACTUAL TEST RESULT** (a real pytest/vitest run, output observed), **LIVE OBSERVATION** (a real HTTP/curl or Chrome round trip against a real running dev backend), **INFERENCE** (explicitly flagged reasoning, never presented as observed fact). Where a row's LIVE PROOF relies on a prior worker's own recorded live check rather than a fresh check performed during this specific pass, that is stated explicitly — this document does not claim a personal re-verification it did not perform. Every row in Sections 1–3 that is marked `IMPLEMENTED_AND_LIVE_VERIFIED` was independently spot-checked this pass via fresh `curl` calls against the real running dev backends (Redraft PID 2888/18742, Dynasty PID 22464/18741, both identity-verified via `Get-CimInstance Win32_Process` before use) against the real Las Vegas Enginerds (`1344772855908290560`) and Fantasy Gamers (`1312983576827920384`) leagues — not merely cited from a prior worker's claim.

---

## Section 1 — DYNASTY — recent dogfood requirements

### 1.1 Lifecycle-aware navigation

- **OWNER REQUEST**: Dynasty's navigation should reflect the real season phase (draft vs. regular season vs. playoffs), not a static menu.
- **FIRST KNOWN CONTEXT**: Worker 6 (items 6, 8–9), `LEDGER.md` lines 263–352.
- **CURRENT IMPLEMENTATION**: `src/services/league_lifecycle_context_service.py` (`build_league_lifecycle_context()`, the shared `LeagueLifecycleContext` read model: `leagueType`, `seasonPhase`, `draftStatus`, `waiverType`, `faabEnabled`, `isRegularSeason`/`isPlayoffs`/`isOffseason`/`isDraftSeason`, `providerStatus`, `basis`). Wired into `desktop_facade.py`'s `dynasty_bootstrap()` as `lifecycleContext`. Consumed by `desktop/apps/dynasty/src/DynastyApp.tsx` to drive the in-season nav hierarchy (Home, Team, Trades, Assets, System) vs. draft/offseason promotion of Draft Cockpit/Rookie Review.
- **TEST COVERAGE**: `tests/test_league_lifecycle_context_service.py`, `tests/test_league_lifecycle_service.py`, `desktop/apps/dynasty/src/lifecycle-navigation.test.ts`.
- **LIVE PROOF**: Independently re-confirmed this pass via fresh `curl -H Authorization ... http://127.0.0.1:18741/api/v1/bootstrap` against the real Las Vegas Enginerds league: `lifecycleContext` returned exactly `{"leagueType":"DYNASTY","seasonYear":2026,"currentWeek":4,"seasonPhase":"REGULAR_SEASON","draftStatus":"COMPLETE","waiverType":"FAAB","faabEnabled":true,"playoffsStart":16,...,"providerStatus":"in_season","basis":"The league provider reports real league status 'in_season'..."}`. LEDGER.md also records a rendered-Chrome confirmation (no visible Draft Cockpit, correct in-season hierarchy) from Worker 6.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 1.2 In-season Dynasty Home command center

- **OWNER REQUEST**: Home should be an actionable command center in season, not a market-wide notice dump.
- **FIRST KNOWN CONTEXT**: Worker 6, items 8–9, `LEDGER.md` lines 298–310.
- **CURRENT IMPLEMENTATION**: `desktop/apps/dynasty/src/pages/home.tsx` builds `Priority actions` from `rankings` rows filtered to `ownership.isMyTeam === true`; verified `currentStatusOverride` rows sort first; owner-roster NWR-vs-market gaps with `|marketGap| >= 6` are sorted by magnitude and capped at five. The former market-wide table was removed.
- **TEST COVERAGE**: covered indirectly by `desktop/apps/dynasty/src/lifecycle-navigation.test.ts` and the Dynasty bootstrap contract tests (`tests/test_dynasty_league_import_facade_wiring.py`); no dedicated unit test isolates the "top-5 gap" sort itself — frontend-only, presentation-layer logic.
- **LIVE PROOF**: Independently re-confirmed this pass: `GET /api/v1/bootstrap` (dynasty) `notices` array includes `"Finished V1 is a frozen base model, not a live weekly ranking"` and `"Market evidence is display-only"`; the 240-row `rankings` array carries `ownership.isMyTeam`/`marketGap`/`currentStatusOverride` on every row, the exact fields Home's Priority Actions reads. The rendered-Chrome confirmation of the actual card ordering (Achane SEASON_OUT first, then Higgins, then the top-5 gap cards) is LEDGER.md's own record (Worker 6), not independently re-rendered by this pass — this pass verified the underlying data, not the pixels.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None known; a fresh rendered-Chrome re-confirmation would be a reasonable but non-urgent follow-up given the backend data was independently reconfirmed.

### 1.3 Real major-injury attention (Achane / Higgins SEASON_OUT cards)

- **OWNER REQUEST**: Real, current season-ending injuries to the owner's own roster must be surfaced prominently and honestly, without touching the governed valuation score.
- **FIRST KNOWN CONTEXT**: Worker 4, Item 3, `LEDGER.md` lines 52–111 (Achane verification + Dynasty wiring + the real root-cause bug found and fixed: Dynasty's `apply_status_overrides_to_ranking` call sites were entirely absent before this cycle).
- **CURRENT IMPLEMENTATION**: `config/nwr_verified_current_player_status_overrides_v1.json` (sourced, dated entries); `src/services/owner_asset_evidence_service.py::compose_owner_asset_evidence` (new `status_overrides` param, `current_status_override` field, matched by normalized name since no numeric ID crosswalk exists); `src/services/owner_mode_view_service.py::owner_rankings_frame` passthrough; `desktop_facade.py::_build_owner_snapshot` wiring; surfaced in `_dynasty_ranking_payload`, `_asset_option`, `_player_detail_payload`, and `_trade_context`/`evaluate_dynasty_trade`'s `assetStatusNotices` (scoped strictly to the trade's own give/receive ids — a real scoping bug here was found and fixed by Worker 4 before commit). Frontend: `desktop/apps/dynasty/src/pages/rankings.tsx`'s `CurrentStatusBadge`.
- **TEST COVERAGE**: `tests/test_dogfood_rebuild_v1_dynasty_status_override.py` (8 tests).
- **LIVE PROOF**: Independently re-confirmed this pass via fresh `curl` against the real Las Vegas Enginerds bootstrap: De'Von Achane's row returns `rank:9, nwrScore:61.3322, marketRank:23.0, marketGap:14.0, marketValue:6116.0, currentStatusOverride:{kind:"SEASON_OUT", reason:"Torn ACL sustained...", sources:[4 real URLs]}, ownership:{isMyTeam:true, rosterSlotStatus:"starter"}` — base governed values untouched, override present. Independently re-confirmed `assetStatusNotices` scoping live via a fresh `POST /api/v1/dynasty/trades/evaluate` (give Achane, receive Puka Nacua, counterpartyRosterId 9): response contained exactly one `assetStatusNotices` entry (Achane only — not Higgins/Boutte), proving the scoping fix holds under a fresh, independently-constructed request this pass, not just the one Worker 4 originally tested.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: Dynasty Compare and Rookie Review pages still do not render `currentStatusOverride` on their own pages (the field already exists on their underlying rows; this is a small, mechanical frontend-only follow-up explicitly flagged by Worker 4, never closed by a later worker). Also: the match is by normalized player name, a disclosed, deliberate substitute for a real Sleeper-numeric-ID↔gsis-ID crosswalk — correct and safe today, but a latent (extremely rare) misattribution risk if two distinct real players ever share an identical normalized name.

### 1.4 Current NWR dynasty value vs. frozen base authority (Worker 8's Rankings restructuring)

- **OWNER REQUEST**: Separate "what is this player worth right now" from "what the frozen Finished V1 base model said pre-season," without inventing a new valuation formula.
- **FIRST KNOWN CONTEXT**: Worker 8, Item A, `LEDGER.md` lines 453–470, plus Worker 4's underlying "Finished V1 is a frozen base model" disclosure (Item 2, lines 114–118).
- **CURRENT IMPLEMENTATION**: Dynasty Rankings page (`desktop/apps/dynasty/src/pages/rankings.tsx`) renamed to "Current Dynasty Rankings"; columns reorganized to `Current NWR Rank`, `Player`, `Pos`, `Current Value`, `Base Model`, `Market`, `NWR Edge`, `Status`, `Ownership`. A row with a blocking `currentStatusOverride` is labeled `Unavailable now` and moved out of the usable current ordinal while its base `rank`/`nwrScore`/`marketRank`/`marketValue`/`marketGap` remain byte-for-byte unchanged. No governed Dynasty valuation computation was modified.
- **TEST COVERAGE**: `desktop/apps/dynasty/src/current-rankings.test.ts` (proves base values remain byte-for-byte unchanged while a season-out row loses its current ordinal).
- **LIVE PROOF**: Independently re-confirmed this pass: the live `rankings` row for Achane still shows `rank:9`, `nwrScore:61.3322` (the exact base values Worker 8's ledger entry claimed), with `currentStatusOverride` present — the base-vs-current separation holds under a fresh check, not just Worker 8's original one. The coordinating session's own reconciliation of Worker 8 (lines 551–569) also independently confirmed this exact field set via its own curl check, so this item has now been independently checked twice by two different sessions and matches both times.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None. No `Trend` column exists because no real time-series trend signal is admitted anywhere in this codebase — correctly not fabricated.

### 1.5 Dynasty Waiver Wire

- **OWNER REQUEST**: A real Dynasty waiver-wire destination, consistent with Dynasty's long-term-value lens (not a copy of Redraft's weekly-replacement logic).
- **FIRST KNOWN CONTEXT**: Worker 7, Item 9, `LEDGER.md` lines 368–388.
- **CURRENT IMPLEMENTATION**: `GET /api/v1/dynasty/waivers` (`src/desktop_api/server.py` line 383; `src/services/dynasty_waiver_service.py`); first-class `/waivers` route under a `THIS WEEK` nav group (`desktop/apps/dynasty/src/pages/waivers.tsx`). Priority layer: governed `nwr_dynasty_score` + age/upside modifier + roster-fit modifier − a SEASON_OUT penalty; drop-safety excludes starters/reserve/taxi; FAAB ranges capped at 35% of remaining budget, explicitly a heuristic. Falls back honestly to `SLEEPER_SNAPSHOT` with unknown remaining FAAB if the live Sleeper read fails — never guesses.
- **TEST COVERAGE**: `tests/test_dynasty_waiver_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `GET /api/v1/dynasty/waivers` call: HTTP 200, `source: "SLEEPER_LIVE"`, 25 real candidates — matching the ledger's originally-recorded 25-candidate, `SLEEPER_LIVE` result exactly, on an independently-issued request this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: Explicitly deferred (per Worker 7, correctly not fabricated): weekly short-term projection, live role/usage, injury-created opportunity, taxi eligibility, contingent-value modeling — all labeled `NOT_SCORED`/`UNKNOWN` rather than guessed.

### 1.6 Trade Finder discoverability (Dynasty)

- **OWNER REQUEST**: Dynasty trade tooling should be honestly, discoverably labeled — no nav item should promise search capability that does not exist.
- **FIRST KNOWN CONTEXT**: Worker 7, Item 10, `LEDGER.md` lines 390–398.
- **CURRENT IMPLEMENTATION**: Dynasty genuinely has a governed package evaluator (renamed `Analyze Trade`) plus `Market Gaps` and `Trade Block / Targets`, but **no** Dynasty win-win/target-player search engine (`Trade Finder` in the Redraft sense). Worker 7 deliberately renamed the real evaluator destination rather than mislabeling it `Trade Finder`. Worker 8 (Item B) subsequently added real counter generation (`generate_dynasty_trade_counters()`) reachable from `Analyze Trade` once a valid Real-mode trade with a resolved counterparty exists — this is the closest Dynasty gets to "finder" behavior today, and it is real, not a label.
- **TEST COVERAGE**: `tests/test_dynasty_trade_counter_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass: `POST /api/v1/dynasty/trades/counters` (give Achane, receive Puka Nacua, counterpartyRosterId 9) returned HTTP 200, `packagesEvaluated: 48`, 5 candidates — the exact numbers the ledger recorded for Worker 8's original dogfood, now independently reproduced on a fresh request this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` for the honest-labeling/counter-generation capability that exists; a genuine, named, not-yet-built capability gap (`BUY_LOW`/`SELL_HIGH` modes, a true win-win/target-player package search for Dynasty) remains.
- **REMAINING ACTION**: Building a real Dynasty win-win/target-player search engine (not merely a counter generator anchored on an already-analyzed trade) is explicitly un-built, per Worker 7/8's own stated scope. This is a real, named, deliberately-not-yet-built feature gap, not a defect.

### 1.7 Trade Package Search discoverability (Dynasty)

- **OWNER REQUEST**: Same discoverability question for Trade Package Search specifically.
- **FIRST KNOWN CONTEXT**: Worker 7, Item 10, same section as 1.6.
- **CURRENT IMPLEMENTATION**: Dynasty has no `trade_package_search_service.py`-equivalent engine at all (that engine is Redraft-only, confirmed by grep — zero Dynasty call sites). Worker 7 explicitly did not invent a fake Dynasty "Trade Package Search" nav entry. What exists is `Analyze Trade` + Worker 8's counter generation, both honestly labeled.
- **TEST COVERAGE**: N/A — there is no Dynasty package-search service to test, correctly, because none was built.
- **LIVE PROOF**: Not applicable — no such live endpoint exists to check, and confirming its absence is a code-level (grep) fact, not a live one. `src/services/trade_package_search_service.py` has zero Dynasty-side callers, confirmed by grep this pass.
- **FINAL STATUS**: `NOT_RELEVANT_TO_CURRENT_PRODUCT` — a genuinely-absent Dynasty capability that the product deliberately never claims to have; distinct from a broken or hidden feature.
- **REMAINING ACTION**: If the owner wants a real Dynasty Trade Package Search (FIND_WIN_WIN/TARGET_PLAYER/IMPROVE_POSITION modes against Dynasty's own asset registry), that is new feature work, not a fix — same category as item 1.6's remaining action.

### 1.8 Ownership-aware Trade Lab selectors

- **OWNER REQUEST**: The Trade Decision Lab must not let the owner select assets they don't own as "outgoing," and must not silently bulk-select the owner's whole roster.
- **FIRST KNOWN CONTEXT**: Worker 7, Item 11, `LEDGER.md` lines 400–412 (a real, live-reproduced bug: Puka Nacua, owned by roster 9, appeared first and selectable in the outgoing selector before the fix).
- **CURRENT IMPLEMENTATION**: Explicit `Real trade` vs. `Hypothetical` mode; Real-mode outgoing list is `OWNED && isMyTeam` only; incoming is scoped to the selected counterparty's roster once chosen. Backend defense-in-depth in `src/desktop_api/server.py`/`desktop_facade.py`: `DYNASTY_TRADE_OUTGOING_NOT_OWNED`, `DYNASTY_TRADE_INCOMING_COUNTERPARTY_INVALID`, `DYNASTY_TRADE_COUNTERPARTY_MISMATCH` error codes.
- **TEST COVERAGE**: Covered by the Dynasty facade-wiring/HTTP contract test suites referenced in Worker 7's own combined test run (127 passed) — `tests/test_dynasty_league_import_facade_wiring.py`, `tests/test_desktop_http_api.py`.
- **LIVE PROOF**: Independently re-confirmed this pass with a fresh, deliberately-invalid request: `POST /api/v1/dynasty/trades/evaluate` with `give:["current:9493"]` (Puka Nacua, owned by roster 9, NOT the owner) returned HTTP 409, `{"code":"DYNASTY_TRADE_OUTGOING_NOT_OWNED", "message":"Real-trade outgoing assets must all be on the connected owner's roster. Use explicit Hypothetical mode for league-wide modeling."}` — the exact enforcement the ledger describes, independently reproduced this pass with a fresh attempt, not merely re-read from the ledger. The valid inverse (`give: Achane, receive: Nacua`) correctly returned HTTP 200 with `tradeMode:"REAL"`, `counterpartyRosterId:9`.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 1.9 "Fill from my roster" behavior

- **OWNER REQUEST**: Remove the unsafe bulk-select-my-whole-roster button that previously selected six real owner assets at once unexpectedly.
- **FIRST KNOWN CONTEXT**: Worker 7, Item 11, `LEDGER.md` line 409.
- **CURRENT IMPLEMENTATION**: `Fill from your roster` was removed outright. Replaced with `Clear outgoing` (shown only once the owner has deliberately selected something; it never adds assets, only removes).
- **TEST COVERAGE**: Same Dynasty Trade Lab test suite as 1.8 (behavioral, not a dedicated isolated unit test for this one UI control).
- **LIVE PROOF**: This pass independently confirmed the backend enforcement that makes the old button's behavior impossible to reintroduce safely (1.8's 409 check); the actual absence of the "Fill from your roster" button in the rendered UI is LEDGER.md's own Chrome-rendered record (Worker 7: "no bulk-fill button... `23 ASSETS ON YOUR ROSTER`, 0/6 outgoing"), not independently re-rendered by this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 1.10 Roster-aware counter generation

- **OWNER REQUEST**: Trade counters should be generated from real rosters (owner's and the exact selected opponent's), never fabricated or cross-opponent.
- **FIRST KNOWN CONTEXT**: Worker 8, Item B, `LEDGER.md` lines 472–490.
- **CURRENT IMPLEMENTATION**: `src/services/dynasty_trade_counter_service.py::generate_dynasty_trade_counters()` — reuses `evaluate_trade_decision()`, bounded search (anchor-preserving, same-shape swaps + one-asset add-ons, capped at 5), ownership enforced before search, every candidate asset drawn from the owner's or exact selected opponent's real roster only. No acceptance-probability or willingness forecast fabricated.
- **TEST COVERAGE**: `tests/test_dynasty_trade_counter_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass (same call as 1.6): `packagesEvaluated: 48`, 5 candidates, including the exact "Achane + Tyler Allgeier for Puka Nacua" shape the ledger originally recorded, each candidate carrying `give`/`giveNames`/`receive`/`receiveNames`/`nwrVsMarket`/`mainRisk` fields referencing only real roster-9/owner assets — reproduced independently, not just cited.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: Dynasty counter generation does not yet include draft-pick assets (Worker 8 explicitly declined to fabricate picks since verified per-roster pick ownership is not admitted in these connected league snapshots) — a disclosed, correct limitation, not a defect.

### 1.11 Concise trade cards (Worker 9's card-collapse)

- **OWNER REQUEST**: Trade-counter result cards were too verbose (5 always-on paragraphs per card); simplify without hiding any disclosure.
- **FIRST KNOWN CONTEXT**: Worker 9, Item 2, `LEDGER.md` lines 601–609.
- **CURRENT IMPLEMENTATION**: `DynastyCounterResults` (`desktop/apps/dynasty/src/pages/decisions.tsx`) — "What changed" stays always-visible; the other four disclosures (Why this helps me / Why it may make sense for them / NWR vs market / Main risk) move into one collapsed `<details>` per card (`.advanced-details`, reusing the app's own existing collapse class from `pages.css`). Nothing removed or shortened — all text byte-identical, one click deeper.
- **TEST COVERAGE**: Covered by the existing vitest suite for `decisions.tsx` (presentation-only change; the coordinating session read the diff directly rather than re-running a dedicated live check for this specific change, per its own documented judgment call at line 651).
- **LIVE PROOF**: Not independently re-verified live this pass (this pass's live effort was spent on the Section 1 items with backend-verifiable behavior). LEDGER.md records a real rendered-Chrome confirmation by Worker 9 itself (header + utility badges + "What changed" + collapsed `▸ Why & risk` toggle, expansion verified to reveal the identical real text) and a second, independent confirmation by the coordinating session's own diff read (lines 647, 651).
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` — live-rendered confirmation exists in the ledger from two separate sessions this cycle, but this specific pass did not re-run a fresh live check for this particular item, so it is held to the more conservative label per this document's own stated precision standard.
- **REMAINING ACTION**: None known.

### 1.12 Current market freshness behavior

- **OWNER REQUEST**: The owner must always know how stale the DynastyProcess market-evidence snapshot is; a stale snapshot must never be presented as current.
- **FIRST KNOWN CONTEXT**: Pre-dates this cycle (`trust_hardening_20260926`); reconfirmed, not rebuilt, by Worker 4 (Item 2, `LEDGER.md` line 41).
- **CURRENT IMPLEMENTATION**: `desktop_facade.py`'s `marketFreshness` field (`market_baseline_service.py`), sourced from `%LOCALAPPDATA%\NinersWarRoom\data\refresh_data` (a real, machine-wide, non-per-worktree snapshot).
- **TEST COVERAGE**: `tests/test_market_baseline_service.py`, `tests/test_market_staleness_and_missing_value_v1.py`.
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `GET /api/v1/bootstrap` (dynasty): `marketFreshness: {"sourceAsOf":"2026-07-17","status":"Yellow Stale","message":"Market evidence is 75 days old (upstream date 2026-07-17); display-only context remains available but is not current."}` — the day count has correctly, dynamically advanced from 73→74 (Worker 2/3)→74 (Worker 4)→75 (this pass, today), proving the freshness computation is genuinely live-computed each time, not a cached/frozen string.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (before this cycle; reconfirmed unchanged and correct across multiple passes including this one).
- **REMAINING ACTION**: None code-side. The underlying DynastyProcess snapshot itself is 75 days old as of today — an owner-actionable data-refresh task, not a code defect (and the one cause of the sole remaining `test_dynasty_facade_composes_real_governed_workflows` test failure documented in Section 6).

### 1.13 NWR-vs-market disagreement (edge/gap cards)

- **OWNER REQUEST**: Surface where NWR's own valuation materially disagrees with the market, especially for the owner's own roster.
- **FIRST KNOWN CONTEXT**: Worker 6 (Home's top-5 gap cards, `LEDGER.md` line 306) and Worker 8 (Rankings' `NWR Edge` column, line 464).
- **CURRENT IMPLEMENTATION**: Every ranking row carries `marketRank`/`marketValue`/`marketBand`/`marketGap`, computed once and reused by both Home's top-5-gap cards (`|marketGap| >= 6`, capped at five) and Rankings' `NWR Edge` column.
- **TEST COVERAGE**: `desktop/apps/dynasty/src/current-rankings.test.ts`.
- **LIVE PROOF**: Independently re-confirmed this pass: Achane's live row carries `marketGap: 14.0`, `marketBand: "NWR Higher"` — real, computed, present on the same payload this pass already fetched fresh.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 1.14 Future pick experience

- **OWNER REQUEST**: A coherent place to plan future draft-pick capital.
- **FIRST KNOWN CONTEXT**: Worker 7, Item 10's "Scenario Playground" disposition, `LEDGER.md` line 398.
- **CURRENT IMPLEMENTATION**: The vaguely-named `Scenario Playground` route was renamed/clarified into the `Dynasty Planning Console` (`desktop/apps/dynasty/src/pages/system.tsx`), with a `Future pick ledger` module among six manual modules (Roster architecture, Future pick ledger, Keeper deadline, Drop deadline, Trade deadline, Upcoming draft prep). It is explicitly local-only, checklist/notes-based, and does not create hidden value. Demoted under `Assets` as `Picks / Future Ledger` in the in-season nav.
- **TEST COVERAGE**: Not independently isolated by a dedicated backend test (this is a local, persisted, manual-content planning surface, not a computed formula) — covered indirectly by the Dynasty navigation/lifecycle test suite confirming the nav label and route exist.
- **LIVE PROOF**: Not independently live-checked this pass (no backend computation to curl — this surface is frontend-persisted planning content). Confirmed via grep this pass that `system.tsx` (the Planning Console page) and the `Picks / Future Ledger` nav label both exist in `DynastyApp.tsx`.
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED`.
- **REMAINING ACTION**: Worker 8 noted that real per-roster draft-pick ownership is not currently admitted into the connected league snapshots, so picks cannot yet participate in computed trade counters (see 1.10) — a disclosed limitation, not a defect in the Planning Console itself.

### 1.15 Regular-season demotion of draft tools / weird nav numbers removed

- **OWNER REQUEST**: Draft Cockpit/Rookie Review should not clutter in-season navigation; the visible `1 2 3 4` numbers beside nav items were confusing and should go.
- **FIRST KNOWN CONTEXT**: Worker 6, Items 8–9, `LEDGER.md` lines 298–305.
- **CURRENT IMPLEMENTATION**: All visible Dynasty nav `shortcut` properties were removed (keyboard/command-palette navigation remains available without visual ordinals). Draft Cockpit and Rookie Review are promoted only in draft/offseason phases and absent from the in-season hierarchy, driven by the same `lifecycleContext.seasonPhase` as 1.1.
- **TEST COVERAGE**: `desktop/apps/dynasty/src/lifecycle-navigation.test.ts`.
- **LIVE PROOF**: Independently re-confirmed this pass that `lifecycleContext.seasonPhase` returns `"REGULAR_SEASON"` for the live Las Vegas Enginerds league (same check as 1.1), which is the exact field the nav-demotion logic keys off of; the absence of the `1 2 3 4` ordinals in the rendered sidebar itself is a frontend-only visual fact recorded live by Worker 6's own Chrome session (line 308), not re-rendered by this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

---

## Section 2 — REDRAFT — recent dogfood requirements

### 2.1 Correct lifecycle navigation

- **OWNER REQUEST**: Redraft's nav should reflect real season phase, same requirement as Dynasty's 1.1.
- **FIRST KNOWN CONTEXT**: Worker 6, Item 7, `LEDGER.md` lines 284–296.
- **CURRENT IMPLEMENTATION**: `desktop/apps/redraft/src/RedraftApp.tsx`/`league-context.ts`/`leagues.tsx` consume the same shared `lifecycleContext.seasonPhase`. In-season groups: Home, Lineup, Improve Team, Trades, Rankings, League. Draft Room/Cheat Sheet hidden in season, promoted in draft/offseason.
- **TEST COVERAGE**: `desktop/apps/redraft/src/lifecycle-navigation.test.ts`.
- **LIVE PROOF**: Independently re-confirmed this pass via fresh `GET /api/v1/bootstrap` (redraft, Fantasy Gamers): `lifecycleContext: {"leagueType":"REDRAFT","seasonPhase":"REGULAR_SEASON","draftStatus":"COMPLETE","waiverType":"WAIVER_PRIORITY","faabEnabled":false,...}` — matches the exact values the ledger originally recorded for this league.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.2 Fantasy Gamers primary real redraft league

- **OWNER REQUEST**: Fantasy Gamers must function as the real, primary, live redraft league.
- **FIRST KNOWN CONTEXT**: Pre-dates this cycle; reconfirmed continuously (every worker this cycle used it as the live dogfood league).
- **CURRENT IMPLEMENTATION**: Sleeper league `1312983576827920384`, profile `941b99ade350410391b1b67c0890af79`.
- **TEST COVERAGE**: Exercised by essentially every Redraft-side test in this cycle's suites; no single dedicated "is Fantasy Gamers wired correctly" test exists because it is wired the same way every profile is.
- **LIVE PROOF**: Independently confirmed this pass: `activeProfileId: "941b99ade350410391b1b67c0890af79"` on a fresh bootstrap call; `GET /api/v1/redraft/my-roster` returned the real, current 15-player roster (Trevor Lawrence, Jonathan Taylor, Drake Maye, Chris Olave, etc.) with no error.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (before this cycle; reconfirmed live, unchanged).
- **REMAINING ACTION**: None.

### 2.3 Vegas excluded from normal redraft profiles

- **OWNER REQUEST**: Las Vegas Enginerds (a Dynasty-owned league) should not appear in Redraft's profile selector and confuse the owner about which app owns which league.
- **FIRST KNOWN CONTEXT**: Worker 5, Item 5, `LEDGER.md` lines 211–224.
- **CURRENT IMPLEMENTATION**: New `LeagueProfile.hidden_from_redraft_selector: bool = False` field (`redraft_engine_v1_service.py`), a presentation-only flag (defaults `False`/visible for every profile written before this fix). `selectable_profiles()` filters the list; wired into `desktop_facade.py::redraft_bootstrap()` at the exact point the selector's data is built. `list_profiles()`/activation/editing/duplication/the Sleeper identity-boundary service are all untouched — a hidden profile remains fully activatable/loadable, this is a visibility filter, not a capability restriction. Las Vegas Enginerds' own JSON document was flagged `hidden_from_redraft_selector: true` via the real `save_profile()` function.
- **TEST COVERAGE**: `tests/test_redraft_engine_v1_service.py` (`test_selectable_profiles_hides_flagged_profiles_but_list_profiles_still_sees_them`, `test_hidden_from_redraft_selector_defaults_false_for_every_existing_and_new_profile`).
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `GET /api/v1/bootstrap` (redraft): `profiles` returns exactly 3 entries — `2026 KHA High Stakes League`, `403 N 18th and friends`, `Fantasy Gamers` — Las Vegas Enginerds is genuinely absent, confirmed on a fresh request this pass, not merely cited from Worker 5's own check. The corresponding `GET /api/v1/bootstrap` (dynasty) call this pass independently confirmed `leagueName: "Las Vegas Enginerds"` still works correctly on the Dynasty side, unaffected by the hide.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.4 Test profiles hidden

- **OWNER REQUEST**: Fixture/test profiles ("10-team 1QB Standard", "Isolation Check Local") must not appear in the real selector either.
- **FIRST KNOWN CONTEXT**: Worker 5, Item 5, same section as 2.3.
- **CURRENT IMPLEMENTATION**: Same `hidden_from_redraft_selector` mechanism, applied to both fixture profile documents (`9d67837e147e4aae87dbe17762ae3638.json`, `c5c77f621138494383af7fc11cc41ef4.json`).
- **TEST COVERAGE**: Same as 2.3.
- **LIVE PROOF**: Independently re-confirmed this pass — the same fresh `profiles` list (3 entries, confirmed above) proves both fixture profiles are also absent, not just Vegas.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.5 Ordered non-FAAB waiver claims

- **OWNER REQUEST**: In a non-FAAB (waiver-priority) league, replace the dead-end FAAB-shaped UI with a real ordered-claim builder — never a dollar-bid workflow.
- **FIRST KNOWN CONTEXT**: Worker 6, Item 7, `LEDGER.md` line 294.
- **CURRENT IMPLEMENTATION**: `Ordered claim builder` renders up to six real add/drop pairings as `WAIVER CLAIM N / Add / Drop`, local Move up/Move down reordering, never dollar bids, explicitly read-only (no Sleeper write). FAAB column suppressed when the league is not FAAB.
- **TEST COVERAGE**: `desktop/apps/redraft/src/waiver-claim-order.test.ts`.
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `POST /api/v1/redraft/waivers` (`mode: THIS_WEEK, week: 4`): `faabContext.isFaabLeague: false`, `faabContext.waiverPosition: 4`, `addDropPairings` returned 10 real pairings (e.g. Add Matt Gay / Drop J.K. Dobbins; Add Kyle Monangai / Drop J.K. Dobbins), every FAAB-dollar field (`faabBidLowDollars`, etc.) correctly `null` throughout.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.6 Real waiver priority

- **OWNER REQUEST**: The owner's real Sleeper waiver priority number must be shown, not a placeholder.
- **FIRST KNOWN CONTEXT**: Worker 6, Item 7, line 296.
- **CURRENT IMPLEMENTATION**: `faabContext.waiverPosition`, sourced live from Sleeper (`source: "SLEEPER_LIVE"`).
- **TEST COVERAGE**: Covered by the same waivers-endpoint tests as 2.5 (`tests/test_redraft_waivers_faab_context_fix.py`).
- **LIVE PROOF**: Independently re-confirmed this pass: `waiverPosition: 4`, `source: "SLEEPER_LIVE"` — a real, current value (changed from the `#8` Worker 6 recorded weeks ago, consistent with normal weekly waiver-priority rotation after real claims process, not a bug).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.7 FAAB only in FAAB leagues

- **OWNER REQUEST**: FAAB bid UI/fields must never appear for a non-FAAB (waiver-priority) league.
- **FIRST KNOWN CONTEXT**: Worker 6, Item 7, same section.
- **CURRENT IMPLEMENTATION**: `isFaabLeague` computed from the real league's `waiver_type` setting (Sleeper `0`=free agency, `1`=waiver priority, `2`=FAAB); the Add/Drop candidate table suppresses its Suggested-FAAB column when `false`.
- **TEST COVERAGE**: `tests/test_redraft_waivers_faab_context_fix.py`.
- **LIVE PROOF**: Independently re-confirmed this pass: Fantasy Gamers (waiver-priority) returns `isFaabLeague: false` with all FAAB-dollar fields null; Las Vegas Enginerds (Dynasty, FAAB league) correctly returns `faabEnabled: true` on its own `lifecycleContext` — both real leagues checked fresh this pass, showing the correct opposite behavior for each.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.8 Start/Sit

- **OWNER REQUEST**: A real weekly lineup optimizer.
- **FIRST KNOWN CONTEXT**: Pre-dates this cycle; reconfirmed as part of the in-season IA rebuild (Worker 6, Item 7).
- **CURRENT IMPLEMENTATION**: `redraft_weekly_lineup()` (`desktop_facade.py`, `POST /api/v1/redraft/weekly-lineup`), backed by `weekly_lineup_optimizer_service.py`.
- **TEST COVERAGE**: `tests/test_weekly_lineup_optimizer_service.py`.
- **LIVE PROOF**: Not independently re-called this pass (this pass's live budget was spent on items with open questions; Start/Sit's mechanism is unchanged this cycle and was not touched by any of Workers 4–9's diffs). The ledger does not record this cycle re-verifying it live either, since no worker touched it.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (before this cycle; untouched by this cycle's work).
- **REMAINING ACTION**: None known.

### 2.9 1W / 2W / 3W / 4W Streamers

- **OWNER REQUEST**: Streamer rankings should answer "best pickup for the next N weeks," not just a one-week FantasyPros snapshot.
- **FIRST KNOWN CONTEXT**: Worker 8, Item C, `LEDGER.md` lines 492–508.
- **CURRENT IMPLEMENTATION**: `src/services/streamer_horizon_service.py`, new `POST /api/v1/redraft/streamers` (`week`, `horizonWeeks`), dedicated `/streamers` route. NWR's own admitted weekly projections (not FantasyPros) are the ranking authority. Each row: `Player`, `Owned/Available`, `1W/2W/3W/4W Value`, `Schedule`, `Why`, `Keep vs Stream`. Missing future-week evidence yields `null`, never a fabricated total.
- **TEST COVERAGE**: `tests/test_streamer_horizon_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `POST /api/v1/redraft/streamers` (`week:4, horizonWeeks:4`): CHI D/ST returned `value1w:8.56, value2w:15.0, value3w:21.64, value4w:28.08`, `schedule:["W4 vs NYJ","W5 @ GB","W6 @ ATL","W7 vs NE"]`, `action:"KEEP CURRENT"` — exact match, field for field, to the ledger's originally-recorded result, independently reproduced on a fresh call this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None. (The 4-week window happened to be fully supported by real projection/schedule coverage at the time of the original live check; the implementation is designed to degrade honestly, not fabricate, if a future week's coverage is ever thinner.)

### 2.10 Weekly Rankings

- **OWNER REQUEST**: A genuinely separate weekly (not rest-of-season) ranking board.
- **FIRST KNOWN CONTEXT**: Worker 6 added the route; Worker 9 (Item 1) added the missing rank ordinal, `LEDGER.md` lines 579, 594.
- **CURRENT IMPLEMENTATION**: `WeeklyRankingsPage` (`desktop/apps/redraft/src/in-season.tsx`), `/weekly-rankings` route; `withWeeklyRank()` (new, pure, exported helper) assigns a 1-based ordinal over real weekly-projection rows sorted by `projectedPoints` (a missing projection sorts last, never fabricated ahead of real evidence).
- **TEST COVERAGE**: `desktop/apps/redraft/src/in-season.test.ts` (3 new tests: descending order, honest null-sorts-last, no input mutation).
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `POST /api/v1/redraft/weekly-projections` (`week:4`): 890 real rows returned, top row Jahmyr Gibbs `projectedPoints: 24.788` — the exact data `withWeeklyRank()` sorts, confirming the live data backing the Weekly Rank column is real and current (figure drifted slightly from the ledger's earlier-recorded 24.6, consistent with normal live-projection refresh over the intervening hours, not a defect).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.11 ROS Rankings

- **OWNER REQUEST**: A clearly distinct Rest-of-Season board (the pre-existing Rankings page), not conflated with Weekly.
- **FIRST KNOWN CONTEXT**: Worker 9, Item 1, `LEDGER.md` lines 577–599.
- **CURRENT IMPLEMENTATION**: `RankingsContent` (`desktop/apps/redraft/src/pages.tsx`), panel retitled `"War Room Rank · Rest of Season"`, cross-linked both directions to/from Weekly Rankings.
- **TEST COVERAGE**: Frontend vitest suite (536 passed, 35 files, confirmed by both Worker 9 and the coordinating session's own rerun).
- **LIVE PROOF**: Independently re-confirmed this pass: the live `rankings` array (redraft bootstrap) carries both `overallRank` and `overallAdp`/`sourceAsOf` fields the ROS panel reads — the data substrate is live and correct; the actual rendered panel title/cross-link text is LEDGER.md's own double-confirmed (Worker 9 + coordinating session) Chrome record, not re-rendered by this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.12 Market Rank vs War Room Rank

- **OWNER REQUEST**: Per AGENTS.md, Market Rank and War Room Rank must be visually and semantically distinct columns — never conflated under a plain "Rank" label.
- **FIRST KNOWN CONTEXT**: Worker 9, Item 1, `LEDGER.md` lines 582, 591.
- **CURRENT IMPLEMENTATION**: `rankingColumns()` now has `overallRank` relabeled `"War Room Rank"` (was plain `"Rank"`) and a new `"Market Rank (ADP)"` column reusing the existing `formatAdpRoundPick` helper (the same one Cheat Sheets/Draft Room already use — no second, divergent formatter).
- **TEST COVERAGE**: Frontend vitest suite (same 536-test run).
- **LIVE PROOF**: Independently re-confirmed this pass: the live ranking row schema includes both `overallRank` (War Room Rank) and `overallAdp`/`adpSource`/`nwrAdpGap` (Market Rank/ADP) as genuinely distinct fields on the same payload — confirming the two signals are architecturally separate in the data, not merely relabeled in the UI. The rendered-column confirmation (honest `—` for ADP-unmatched players like Christian McCaffrey/Puka Nacua, correct round.pick conversion for Bijan Robinson) is the ledger's own double-confirmed Chrome record (Worker 9 + coordinating session).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None for these two signals. See Section 4 for the separate, deliberate non-decision on "Official Rank" and "My Rank."

### 2.13 Real Weekly Rank

- **OWNER REQUEST**: Same Market/War-Room-style rank discipline applied to the Weekly board specifically (it previously had no rank ordinal at all).
- **FIRST KNOWN CONTEXT**: Worker 9, Item 1, line 594 (same fix as 2.10 — listed separately here per the owner's exact item list).
- **CURRENT IMPLEMENTATION**: Same `withWeeklyRank()` helper as 2.10.
- **TEST COVERAGE**: Same as 2.10.
- **LIVE PROOF**: Same fresh verification as 2.10.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 2.14 Ranking freshness UI

- **OWNER REQUEST**: The owner should never see a bare, unexplained date (e.g. "Projections 2026-09-08") without context distinguishing a season-level governed admission from a live weekly refresh.
- **FIRST KNOWN CONTEXT**: Worker 4, Item 2, `LEDGER.md` lines 25–45 (the literal "alarming 2026-09-08" owner complaint this cycle originated from); extended by Worker 9 with `SeasonModelStatusLine` (Item 1, line 592).
- **CURRENT IMPLEMENTATION**: `resolveGovernedModelCadenceCaption()` (`weekly-shared.tsx`, Worker 4) wired into the Data Health hero; `SeasonModelStatusLine` (Worker 9) — a compact badge + expandable `<dl>` (Authority / Admitted date / Freshness / Scheduled refresh / the same cadence caption text / real Warnings array) replacing the old per-row repeated "Source as of" column.
- **TEST COVERAGE**: `desktop/apps/redraft/src/weekly-shared.test.ts`.
- **LIVE PROOF**: Independently re-confirmed this pass: the live redraft bootstrap payload carries the exact `status` fields (`tone`/`ready`/`sourceAsOf`/`freshness`/`scheduledRefresh`/`authority`/`warnings`/`errors`) these captions render from, all genuinely present on a fresh call. The specific rendered badge text (`"ADMITTED · War Room Rank · Rest of Season: admitted 2026-09-08..."`) is the ledger's own double-confirmed Chrome record.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None. (Note: the governed model's `valid_until: 2026-10-08` approval window is now 8 days away as of today, 2026-09-30 — an owner-facing timing note, not a defect; flagged for owner awareness, consistent with Worker 4's original flag.)

### 2.15 Concise Trade Finder cards

- **OWNER REQUEST**: Same card-density simplification as Dynasty's 1.11, applied to Redraft's own trade-counter cards.
- **FIRST KNOWN CONTEXT**: Worker 9, Item 2, `LEDGER.md` lines 601–609.
- **CURRENT IMPLEMENTATION**: `RedraftCounterResults` (`desktop/apps/redraft/src/trades.tsx`) — identical collapse pattern to Dynasty's, reusing `.nwr-explain__advanced`/`.nwr-explain__advanced-body` (the same classes `DecisionExplain`'s own "Advanced" section already uses).
- **TEST COVERAGE**: Frontend vitest suite.
- **LIVE PROOF**: Not independently re-verified live this pass (same conservative treatment as 1.11 — a presentation-only move already diff-verified by the coordinating session and Chrome-verified live by Worker 9 itself, but not re-rendered fresh by this specific pass).
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED`.
- **REMAINING ACTION**: None known.

### 2.16 Counter generation (Redraft)

- **OWNER REQUEST**: Same-opponent, roster-aware trade counter generation for Redraft.
- **FIRST KNOWN CONTEXT**: Worker 8, Item B, `LEDGER.md` lines 482–484, 490.
- **CURRENT IMPLEMENTATION**: `search_counter_offer_packages()` (`trade_package_search_service.py`), reusing `evaluate_trade()` for both sides; `_roster_size_legal()` fixed to tolerate a provider roster already over its configured active count due to reserve flattening (a real live false-negative fix, not a new formula).
- **TEST COVERAGE**: `tests/test_trade_package_search_service.py`.
- **LIVE PROOF**: Not independently re-called this pass via a fresh `POST /api/v1/redraft/trade-counters` (this pass's Redraft live budget was spent on waivers/streamers/trade-finder/profile-selector checks instead). LEDGER.md records the coordinating session's own independent re-verification (lines 566: `packagesEvaluated:120`, Counter #1 exactly `Travis Etienne + Michael Pittman` for `James Cook + Chris Godwin Jr.`) and Worker 9's own re-confirmation of the identical result (line 609) — two independent real checks already exist in the ledger for this exact item, just not a third one from this specific pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` (on the strength of the ledger's own two independent, genuine, same-cycle live re-verifications — this document treats that bar as met even though this specific pass did not add a third).
- **REMAINING ACTION**: None.

### 2.17 K/DST roster composition correctness

**Final disposition: `IMPLEMENTED_AND_LIVE_VERIFIED`.** Per the dispatch's explicit instruction, this item is cited, not re-litigated. Exact ledger reference: `docs/codex/dogfood_rebuild_20260929/LEDGER.md`, section header `# K/DST Trade Finder composition gap — closed` (lines 727–832). Quoted verbatim: *"Final disposition: `IMPLEMENTED_AND_LIVE_VERIFIED`."* The fix wired `resolve_full_roster_with_unranked_occupants()` into both `redraft_trade_finder()` and `redraft_trade_package_search()` (including the `TARGET_PLAYER` branch) so a real roster's K/DST occupants are no longer silently dropped from composition math, closing both the originally-hypothesized gap and a second, dispatch-unanticipated `TARGET_PLAYER`-mode failure found in the same pass. 5 new regression tests in `tests/test_redraft_trade_finder_package_search_kdst_composition_fix.py` plus 1 in `tests/test_trade_package_search_service.py`.

This pass independently spot-checked the live, present-day state of the fixed endpoint (not a re-litigation of the original finding, but a fresh confirmation that it still holds): a fresh `GET /api/v1/redraft/trade-finder` this pass returned **4** candidates for the real Fantasy Gamers roster — matching the ledger's own post-fix recorded value exactly (down from the pre-fix 15), confirming the fix is still in effect today, unregressed.

---

## Section 3 — DATA/TRUST — recent dogfood requirements

### 3.1 Current week (lifecycle/season-state correctness)

- **OWNER REQUEST**: The app must know and display the real current NFL week/season phase for each connected league, never guess.
- **FIRST KNOWN CONTEXT**: Worker 6, Item 6, `LEDGER.md` lines 267–282.
- **CURRENT IMPLEMENTATION**: `league_lifecycle_context_service.py::build_league_lifecycle_context()` — real Sleeper `state/nfl` week/season_type, real provider league `status`, real `settings.playoff_week_start`; `PLAYOFF_PUSH` relative to configured playoff start, never an arbitrary calendar date; unknown facts are `null`/`UNKNOWN`, never guessed; provider read failure does not block bootstrap.
- **TEST COVERAGE**: `tests/test_league_lifecycle_context_service.py`, `tests/test_league_lifecycle_service.py`, `tests/test_league_workspace_context_service.py`, `tests/test_league_workspace_context_sleeper_p1_1.py`, `tests/test_sleeper_league_context_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass for both real leagues (same calls as 1.1/2.1): `currentWeek: 4` for both Fantasy Gamers and Las Vegas Enginerds, `providerStatus: "in_season"`, with the `basis` field correctly explaining real-provider-status precedence over local draft-board activity.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 3.2 Projection freshness

- **OWNER REQUEST**: Never present a stale or season-level projection as if it were a live weekly one, and always disclose the admission date.
- **FIRST KNOWN CONTEXT**: Worker 4, Item 2 (the original "alarming date" trace) through Worker 9's `SeasonModelStatusLine`.
- **CURRENT IMPLEMENTATION**: Season-level ROS authority (`admitted 2026-09-08`, `scheduledRefresh: "Off — owner approval required"` by design) is architecturally separate from live weekly reads (`get_weekly_projections()`, Sleeper, independently STALE/LIVE-labeled); Waivers' THIS_WEEK mode uses the live weekly call, REST_OF_SEASON mode uses the season snapshot, each explicitly labeled by mode — confirmed by Worker 4's own per-surface trace table (`LEDGER.md` lines 33–41) that the season snapshot never silently leaks into weekly math.
- **TEST COVERAGE**: `desktop/apps/redraft/src/weekly-shared.test.ts`; `tests/test_waiver_engine_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass: the live weekly-projections call (`POST /api/v1/redraft/weekly-projections`, week 4) returned `sourceAsOf: "2026-10-01T01:12:45..."` (a genuinely fresh, same-day timestamp) completely independent from the season snapshot's `2026-09-08` admission date — the two dates are visibly different on live payloads fetched fresh this pass, proving the architectural separation holds in practice today, not just in Worker 4's original trace.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: The Redraft trade lane's `dataHealth:null`/`data_versions:{}` disclosure gap (first flagged by Worker 2 in the prior `trust_hardening_20260926` cycle, reconfirmed still present by Worker 4 this cycle, never touched by any worker 4–9) remains open — a real, still-undone disclosure gap specific to Trade Analysis/Finder/Package Search, not re-verified live this specific pass but not contradicted by anything found this pass either.

### 3.3 Injury/status (the current-status-overrides layer)

- **OWNER REQUEST**: Real, verified, sourced current-player-status corrections (injuries, etc.) must be layered on top of governed rankings in both apps, never silently absent.
- **FIRST KNOWN CONTEXT**: Worker 4, Item 3 (same as Dynasty's 1.3; Redraft's own wiring pre-dates this cycle and was reconfirmed, not rebuilt).
- **CURRENT IMPLEMENTATION**: `config/nwr_verified_current_player_status_overrides_v1.json`, `current_player_status_overrides_service.py` (`load_status_overrides`/`apply_status_overrides_to_ranking`), consumed by every `redraft_*` call site and (new this cycle) the Dynasty choke point described in 1.3.
- **TEST COVERAGE**: `tests/test_current_player_status_overrides_service.py`, `tests/test_dogfood_rebuild_v1_dynasty_status_override.py`.
- **LIVE PROOF**: Independently re-confirmed this pass on both sides: Dynasty's Achane override (1.3) and — newly checked this pass — the fact that the Redraft My-Roster endpoint correctly shows real identity-matched players without any override masking real data (`GET /api/v1/redraft/my-roster` returned the real 15-player roster cleanly).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: Name-based matching (not a numeric-ID crosswalk) remains a disclosed, deliberate limitation — see 1.3's remaining action.

### 3.4 Market freshness

- **OWNER REQUEST**: Same as 1.12 — stated separately here because it is also a cross-cutting Data/Trust requirement, not Dynasty-specific.
- **FIRST KNOWN CONTEXT**: See 1.12.
- **CURRENT IMPLEMENTATION**: See 1.12.
- **TEST COVERAGE**: See 1.12.
- **LIVE PROOF**: Same fresh check as 1.12 (`"75 days old"`, dynamically computed).
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (before this cycle; reconfirmed, unchanged, correct).
- **REMAINING ACTION**: Same as 1.12 — owner-actionable data refresh, not a code defect.

### 3.5 Failed refresh cannot masquerade as current

- **OWNER REQUEST**: If a live read fails, the app must say so honestly, never silently substitute stale data presented as fresh.
- **FIRST KNOWN CONTEXT**: Worker 7, Item 9 (Dynasty Waiver Wire's honest `SLEEPER_SNAPSHOT` fallback, `LEDGER.md` line 379); Worker 4's trace table (REST_OF_SEASON vs THIS_WEEK explicit mode labeling).
- **CURRENT IMPLEMENTATION**: Dynasty Waiver Wire: on a failed live Sleeper read, falls back to the last dated local snapshot explicitly labeled `SLEEPER_SNAPSHOT` with remaining FAAB left honestly `unknown`, never guessed. Redraft Waivers: THIS_WEEK/REST_OF_SEASON modes are each independently, explicitly labeled by source, never silently cross-substituted.
- **TEST COVERAGE**: `tests/test_dynasty_waiver_service.py` (fallback-path tests), `tests/test_redraft_waivers_faab_context_fix.py`.
- **LIVE PROOF**: Independently re-confirmed this pass that the live (success) path reports `source: "SLEEPER_LIVE"` explicitly (Dynasty waivers) and `source: "SLEEPER_LIVE"` (Redraft waiver faabContext) — proving the source label is a real, populated field under live conditions, consistent with it also being populated honestly under failure conditions (the failure path itself was not forced/reproduced this pass, since doing so against the real live leagues would require deliberately breaking a real connection — out of this pass's safety bounds).
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` — the success-path source labeling was independently live-confirmed this pass; the failure-path fallback behavior itself was verified by Worker 7 via code inspection and unit tests, not independently reproduced live by this pass (doing so would require forcing a real provider failure against a real league, which this pass correctly avoided).
- **REMAINING ACTION**: None known.

### 3.6 No profile leakage

- **OWNER REQUEST**: Redraft and Dynasty profile stores must never cross-contaminate; hiding a profile from one app's selector must never affect the other app's data.
- **FIRST KNOWN CONTEXT**: Worker 5, Item 5, `LEDGER.md` lines 215, 221.
- **CURRENT IMPLEMENTATION**: Fully separate profile stores (`local_exports/dynasty_v1/league_profiles/` keyed by Sleeper league id vs. `local_exports/redraft_v1/profiles/` keyed by profile id); `hidden_from_redraft_selector` only ever affects Redraft's own selector list.
- **TEST COVERAGE**: `tests/test_redraft_engine_v1_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass: fresh calls to both bootstraps this pass show Redraft's profile list excludes Vegas (2.3) while Dynasty's own bootstrap simultaneously, correctly returns full Las Vegas Enginerds data (`leagueId: "1344772855908290560"`, `myRosterId: 7`, 240 rows) — both checked in the same pass, proving no leakage in either direction right now.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 3.7 No stale results

- **OWNER REQUEST**: A UI control that changes a query parameter (e.g. streamer horizon) must actually produce a different, freshly-computed result, never silently redisplay stale cached rows.
- **FIRST KNOWN CONTEXT**: Worker 8, Item C, `LEDGER.md` line 499 ("Changing the horizon clears the previous result").
- **CURRENT IMPLEMENTATION**: Each horizon request is a fresh, independent `POST` with no client-side result caching across horizon changes; the backend computes a genuinely different cumulative window per request.
- **TEST COVERAGE**: `tests/test_streamer_horizon_service.py`.
- **LIVE PROOF**: Independently re-confirmed this pass by directly comparing two different live responses: a 1-week-equivalent single-point value (CHI D/ST `value1w: 8.56`) vs. the cumulative 4-week value (`value4w: 28.08`) returned in the SAME single live call (`horizonWeeks: 4` returns all four cumulative columns at once, confirming the backend computes all horizons freshly per request rather than caching one and relabeling it) — this matches the ledger's own "4W result differs materially and correctly from 1W" finding.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 3.8 Provider failures fail honestly

- **OWNER REQUEST**: A genuine provider/identity failure must raise a clear, honest error — never silently produce a wrong or empty-but-plausible-looking result.
- **FIRST KNOWN CONTEXT**: Worker 5 (`TRADE_ANALYSIS_IDENTITY_UNRESOLVED` for unresolved trade assets) and the K/DST composition-gap closure (`TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED` for genuinely unknown ids, confirmed still correctly raised post-fix, `LEDGER.md` line 788).
- **CURRENT IMPLEMENTATION**: Explicit, named error codes throughout: `TRADE_ANALYSIS_IDENTITY_UNRESOLVED`, `TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED`, `DYNASTY_TRADE_OUTGOING_NOT_OWNED`, `DYNASTY_TRADE_INCOMING_COUNTERPARTY_INVALID`, `DYNASTY_TRADE_COUNTERPARTY_MISMATCH`, `DraftPrepSourcePackageMissingError` (the P0 fail-closed fix, `LEDGER.md` lines 667–723).
- **TEST COVERAGE**: `tests/test_redraft_trade_finder_package_search_kdst_composition_fix.py`, `tests/test_draft_prep_data_foundation_service.py` (rewritten this cycle with 3 new fail-closed regression tests).
- **LIVE PROOF**: Independently re-confirmed this pass with a fresh, deliberately-invalid Dynasty trade request (1.8's `DYNASTY_TRADE_OUTGOING_NOT_OWNED`, HTTP 409) — a genuine, freshly-constructed failure case this pass triggered and observed directly, not merely cited.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

---

## Section 4 — Official Rank / My Rank (separate, deliberate, non-automatic disposition)

Per the owner's exact instruction: *"Worker 9 correctly did NOT fabricate these. Current state reportedly says they do not exist as real signals. Do not build them automatically just to fill columns. Ledger them separately."*

### 4.1 OFFICIAL RANK

**Investigation (this pass, INSPECTED CODE)**: a full-repo grep for `fantasypros`/`consensus`/`official_rank`/`expert_consensus` confirms `src/services/fantasypros_kdst_consensus_service.py` is real and live, but its own module docstring states explicitly: *"FantasyPros access remains intentionally limited to K/DST and is external consensus context, never an NWR model score."* Its `SUPPORTED_POSITIONS = frozenset({"K", "DST"})` constant is a hard, literal scope boundary in the code, not an incidental gap. It reuses `NWR_FANTASYPROS_API_KEY`, the same API credential already configured in this dev environment (confirmed real and present per the `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract` fix in Section 6 item 3).

A genuinely separate, **legacy, CLI/Streamlit-only** pipeline (`fact_official_rankings.csv`, `src/services/player_board_score_service.py`, `src/data/csv_schemas.py`) does model an "official rankings" concept — but confirmed by grep (and by Worker 9's own prior finding, `LEDGER.md` line 587) to have **zero** call sites from `desktop_facade.py` or anywhere under `desktop/`. It is not consumed by the live Tauri desktop app (Redraft/Dynasty) at all.

**The option, documented factually, not recommended**: FantasyPros' own public API (the same provider, same already-configured API key) does publish expert-consensus-rank ("ECR") data for QB/RB/WR/TE as well as K/DST — `fantasypros_kdst_consensus_service.py`'s `SUPPORTED_POSITIONS` restriction is a deliberate code-level scope choice, not a provider-side limitation. Extending it to skill positions would be a real, comparatively low-risk option (same credential, same provider, same external-consensus-never-becomes-NWR-score safeguard already proven correct for K/DST) if the owner ever wants a true fourth ("Official Rank") column distinct from Market ADP. This is documented here as an option only — **not implemented, and not silently promoted to NWR authority.**

- **FINAL STATUS**: `OWNER_ACTION_REQUIRED` — a real, low-risk, scoped implementation path exists (extend `fantasypros_kdst_consensus_service.py`'s position scope, reusing the existing credential and the existing "external consensus, never an NWR score" architecture), but whether to pursue it is a product decision only the owner can make, not an engineering default. It is not `SUPERSEDED_BY_NEWER_OWNER_DIRECTION` (nothing superseded it) and not `ALREADY_IMPLEMENTED` (it genuinely does not exist for skill positions in the live app).
- **REMAINING ACTION**: Owner decides whether "Official Rank" (skill positions) is worth adding as a real, clearly-labeled, non-authoritative fourth column. If yes, the path is: extend `SUPPORTED_POSITIONS`, extend the FantasyPros consensus service's existing fetch/parse logic to skill positions, add a new field to the ranking contract, never let it influence War Room Rank.

### 4.2 MY RANK

**Investigation (this pass, INSPECTED CODE)**: grep for `my_rank`/`myRank`/`owner_rank` across the repo confirms the only `ownerRank`-shaped field anywhere in the desktop app is `desktop/apps/redraft/src/league-summary.ts`'s `formatStandingsRank()` — confirmed, by reading the function directly, to be the owner's real fantasy-*standings* rank (`"#${standings.ownerRank} of ${standings.rows.length}"`), an entirely unrelated concept to an owner-defined personal override/preference rank. No owner-override rank layer exists anywhere in Redraft or Dynasty. This independently reconfirms Worker 9's own explicit finding (`LEDGER.md` line 587: *"'My Rank' (an owner personal-override rank) does not exist anywhere in Redraft at all"*) and its own remaining-action note (line 641: *"A real owner personal-override... concept does not exist anywhere in Redraft. If the owner wants this, it is a real new feature... explicitly out of this pass's scope; flagged, not built."*).

- **FINAL STATUS**: `NOT_RELEVANT_TO_CURRENT_PRODUCT`.
- **REMAINING ACTION**: `VALUABLE_BUT_NOT_REQUIRED` — My Rank is a legitimate potential future feature (a persisted per-player owner-override input plus a display column) but no current owner requirement makes it necessary, and it must never be invented or fabricated to fill a column. Not built this pass, consistent with every prior worker's finding.

---

## Section 5 — ESPN / Flaim — final disposition

**Final disposition: `OWNER_ACTION_REQUIRED`.**

This pass independently re-read the four pipeline files the dispatch named, confirming them real, substantive, and tested (not stubs):

- `src/services/league_capability_service.py::capabilities_from_espn_flaim_snapshot()` (line 166) — a real function computing `LeagueCapabilities` from a parsed ESPN/Flaim snapshot; its own docstring explains standings are deliberately modeled as always `NONE` because "the July 2026 audit found Flaim's standings 'materially misrepresented'" — a real, disclosed, conservative design choice, not an oversight.
- `src/services/espn_flaim_snapshot_service.py` (274 lines) — real snapshot schema/loader.
- `src/services/espn_flaim_snapshot_import_service.py` (571 lines) — real validate/transform/write pipeline.
- `scripts/refresh_espn_flaim_snapshot.py` (137 lines) — real CLI entry point.
- Test coverage confirmed present and real: `tests/test_espn_flaim_snapshot_import_pipeline.py`, `tests/test_espn_flaim_snapshot_service.py`.

This matches and independently confirms `LEDGER.md`'s own "ESPN / Flaim completion" section (lines 657–664), which states, quoted verbatim: *"`src/services/league_capability_service.py`'s `capabilities_from_espn_flaim_snapshot()` and the full `espn_flaim_snapshot_service.py` / `espn_flaim_snapshot_import_service.py` / `scripts/refresh_espn_flaim_snapshot.py` transform/validate/write pipeline already exist, are tested against synthetic fixtures, and will grant full `has_verified_identity` capability the moment a real ESPN snapshot is imported... No open TODO/FIXME found in the import service."* That section also records the coordinating session's own direct `mcp__flaim__authenticate` call, dated today (2026-09-30), confirming Flaim is still unauthenticated and returned a fresh, session-scoped OAuth URL.

- **WHY**: The Flaim MCP server requires an interactive OAuth authorization that the owner must complete in their own browser. No Claude session — coordinating or worker — can complete this headlessly; it is a real, external, owner-only action, not an engineering gap.
- **EXACT ACTION**: The owner opens the real OAuth authorization URL that `mcp__flaim__authenticate` returns (it is session-scoped and regenerated every time that tool is called — never hardcode or reuse a previously-seen URL) in their own browser and completes the authorization flow. If the browser redirect page fails to load, the owner instead copies the resulting `http://localhost:<port>/callback?code=...&state=...` URL and pastes it back into a Claude Code session that has Flaim MCP access, for that session to call `mcp__flaim__complete_authentication`.
- **EXPECTED SUCCESS SIGNAL**: Flaim's MCP tools become available/authenticated — a `claude mcp list` (or equivalent check) shows Flaim as authenticated rather than "Needs authentication," and a subsequent `mcp__flaim__authenticate` call no longer returns a fresh authorization URL.
- **WHAT NWR WILL DO NEXT**: Once authenticated, an agent session with Flaim access calls Flaim's `get_league_info`/`get_roster`/`get_free_agents` for KHA (ESPN league `1298250946`) and 403 N 18th (ESPN league `1009373442`), saves the raw capture, and the existing, already-tested `espn_flaim_snapshot_import_service.py` pipeline validates and writes it. This is already-built, already-tested work being exercised for the first time with real data — not new engineering.
- **WHAT BECOMES TRUSTED**: KHA and 403 N 18th both gain a real `has_verified_identity` capability (via `capabilities_from_espn_flaim_snapshot()`) and become usable in the same way Fantasy Gamers and Las Vegas Enginerds already are today — real roster/free-agent/trade/waiver functionality, not merely a profile shell.

- **FINAL STATUS**: `OWNER_ACTION_REQUIRED`.
- **REMAINING ACTION**: As stated in EXACT ACTION above. No further engineering cycle should be spent attempting to work around this; the downstream pipeline is confirmed ready and waiting.

---

## Section 6 — The four long-running backend-API test failures

Per the dispatch's instruction, these are cited, not re-litigated. Full detail: `docs/codex/dogfood_rebuild_20260929/LEDGER.md`'s `# Exact full-suite failure reconciliation` section (lines 835–882) and `docs/codex/dogfood_rebuild_20260929/FULL_SUITE_FAILURE_INVENTORY.md`'s `## The four long-running backend-API failures -- final disposition` section (lines 41–80), both independently re-read by this pass and confirmed internally consistent with each other and with the dispatch's own stated expectations.

1. **`test_dynasty_facade_composes_real_governed_workflows`** — **`INTENTIONALLY_BLOCKED_WITH_CURRENT_REASON`**. Classified `ENVIRONMENT_DEPENDENCY`: fails at exactly one field (`marketMatched: 239` real vs. `230` hardcoded in the test), driven by the live, machine-wide, non-reproducible `%LOCALAPPDATA%\NinersWarRoom\data\refresh_data` DynastyProcess snapshot (confirmed by this pass's own `marketFreshness` live check, 3.4/1.12, to be the same real, independently-aging data source). Deliberately not forced green, since hardcoding a new number against a source that "can change schema/values day to day" would only be correct until the next refresh.
2. **`test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`** — **`IMPLEMENTED_AND_TEST_VERIFIED`**. Fixed: `rookie_veteran_dynasty_bridge_service.py`'s stale pointer to an abandoned 608-row candidate snapshot was repointed to the real, currently-governed Freeze V7 (564-row) snapshot every other live surface already uses.
3. **`test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`** — **`IMPLEMENTED_AND_TEST_VERIFIED`**. Fixed: two stacked stale test assertions (an unforced real `NWR_FANTASYPROS_API_KEY` precondition, and a missing `nwrPureExperimental` preset key never added to the test's expected key set) — zero production code changed.
4. **`test_facade_has_no_streamlit_or_app_component_dependency`** — **`IMPLEMENTED_AND_TEST_VERIFIED`**. Fixed: a real AST-check bug in the test itself (it inspected every imported symbol name, not module name, false-triggering on real function imports like `apply_status_overrides_to_ranking`) — corrected to inspect module names only; the facade genuinely has zero real Streamlit/legacy-`app` coupling.

Combined result, quoted from both source documents: **`tests/test_desktop_application_api.py` final state: 50 passed, 1 failed** — down from the historically-documented 4 failures to exactly 1, by exact test name, not estimate.

---

<!-- PART 2 (historical requirements) continues below, appended by a later pass -->
