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
- **REMAINING ACTION**: Explicitly deferred (per Worker 7, correctly not fabricated): weekly short-term projection, live role/usage, injury-created opportunity, taxi eligibility, contingent-value modeling — all labeled `NOT_SCORED`/`UNKNOWN` rather than guessed. Additionally, a real, separate, narrower limitation was found later in the cycle (the K/DST Trade Finder closure pass, `LEDGER.md`'s "Dynasty-side K check" subsection): this surface's `roster_needs()` is built entirely from the closed 240-row governed registry, so a real rostered player genuinely outside that cut (e.g. the owner's actual real K on Las Vegas Enginerds, Cam Little, `current:11786`, confirmed via a live read-only Sleeper call) is invisible to need-counting — not K/DST-specific, applies to any position beyond the cut. Correctly left unfixed as out of scope this cycle (no existing "manual/unranked asset" concept in Dynasty to reuse, unlike Redraft's equivalent fix) — flagged for a dedicated future worker, not newly discovered by this document.

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
- **REMAINING ACTION**: Dynasty counter generation does not yet include draft-pick assets (Worker 8 explicitly declined to fabricate picks since verified per-roster pick ownership is not admitted in these connected league snapshots) — a disclosed, correct limitation, not a defect. See also 1.5's remaining action: the same closed-240-row-registry roster-need-miscount limitation (e.g. Cam Little) can affect this surface's need-aware candidate selection for any player outside the governed board's cut, not just K/DST.

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

### 1.15 Regular-season demotion of draft tools

- **OWNER REQUEST**: Draft Cockpit/Rookie Review should not clutter in-season navigation.
- **FIRST KNOWN CONTEXT**: Worker 6, Items 8–9, `LEDGER.md` lines 298–305.
- **CURRENT IMPLEMENTATION**: Draft Cockpit and Rookie Review are promoted only in draft/offseason phases and absent from the in-season hierarchy, driven by the same `lifecycleContext.seasonPhase` as 1.1 (`desktop/apps/dynasty/src/DynastyApp.tsx`).
- **TEST COVERAGE**: `desktop/apps/dynasty/src/lifecycle-navigation.test.ts`.
- **LIVE PROOF**: Independently re-confirmed this pass that `lifecycleContext.seasonPhase` returns `"REGULAR_SEASON"` for the live Las Vegas Enginerds league (same check as 1.1), which is the exact field the nav-demotion logic keys off of; the absence of Draft Cockpit in the rendered sidebar itself is a frontend-only visual fact recorded live by Worker 6's own Chrome session (line 308), not re-rendered by this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None.

### 1.16 Weird nav numbers removed

- **OWNER REQUEST**: the visible `1 2 3 4` numbers beside Dynasty nav items were confusing and should go.
- **FIRST KNOWN CONTEXT**: Worker 6, Items 8–9, `LEDGER.md` lines 298–305.
- **CURRENT IMPLEMENTATION**: all visible Dynasty nav `shortcut` properties were removed from `DynastyApp.tsx`'s rendered nav (keyboard/command-palette navigation remains available without visual ordinals).
- **TEST COVERAGE**: `desktop/apps/dynasty/src/lifecycle-navigation.test.ts`.
- **LIVE PROOF**: this is a static UI-labeling change with no backend data dependency to re-check via HTTP. Worker 6's own rendered-Chrome session this cycle directly confirmed the accessibility tree/rendered nav contained no visible `1 2 3 4` ordinals (line 308); not independently re-rendered via Chrome this pass.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` (citing Worker 6's own live Chrome verification this cycle).
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
- **FIRST KNOWN CONTEXT**: Worker 7, Item 9 (Dynasty Waiver Wire's honest `SLEEPER_SNAPSHOT` fallback, `LEDGER.md` line 379); Worker 4's trace table (REST_OF_SEASON vs THIS_WEEK explicit mode labeling); a separate same-cycle P0 fix, `LEDGER.md`'s "P0 fix — test-suite canonical-doc corruption hazard" section.
- **CURRENT IMPLEMENTATION**: Dynasty Waiver Wire: on a failed live Sleeper read, falls back to the last dated local snapshot explicitly labeled `SLEEPER_SNAPSHOT` with remaining FAAB left honestly `unknown`, never guessed. Redraft Waivers: THIS_WEEK/REST_OF_SEASON modes are each independently, explicitly labeled by source, never silently cross-substituted. Separately, `src/services/draft_prep_data_foundation_service.py` gained a fail-closed gate (`DraftPrepSourcePackageMissingError`, `_has_real_prior_history_inputs()`) so an absent/empty real source package now raises before any write, instead of silently computing a degraded "0 rows" result and overwriting real tracked docs under `docs/model_v4/` — a real, reproduced-live corruption this cycle caught and fixed (deliberately reverted before any fix, per `LEDGER.md`'s own before/after `git status` proof: 5 tracked docs modified before the fix, zero after).
- **TEST COVERAGE**: `tests/test_dynasty_waiver_service.py` (fallback-path tests), `tests/test_redraft_waivers_faab_context_fix.py`, `tests/test_draft_prep_data_foundation_service.py` (3 new permanent fail-closed regression tests + a module-level git-status self-check fixture).
- **LIVE PROOF**: Independently re-confirmed this pass that the live (success) path reports `source: "SLEEPER_LIVE"` explicitly (Dynasty waivers) and `source: "SLEEPER_LIVE"` (Redraft waiver faabContext) — proving the source label is a real, populated field under live conditions, consistent with it also being populated honestly under failure conditions (the failure path itself was not forced/reproduced this pass, since doing so against the real live leagues would require deliberately breaking a real connection — out of this pass's safety bounds). The draft-prep fix's before/after proof is a real `ACTUAL TEST RESULT` cited from `LEDGER.md`, not a live HTTP check (this service has no HTTP endpoint).
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` — the success-path source labeling was independently live-confirmed this pass; the failure-path fallback behavior itself was verified by Worker 7 via code inspection and unit tests, not independently reproduced live by this pass (doing so would require forcing a real provider failure against a real league, which this pass correctly avoided).
- **REMAINING ACTION**: None for the Dynasty/Redraft waiver fallback behavior. **Important scope note for the draft-prep fix**: `draft_prep_data_foundation_service.py` has **zero call sites from the live Tauri desktop app** (confirmed by `LEDGER.md`'s own repo-wide grep: no references under `desktop/`, `src/desktop_api/`, or `desktop_facade.py` — only its own test file and a standalone CLI script, `scripts/build_draft_prep_data_foundation.py`, ever call it). It is real, correct, tested legacy V1-era draft-prep tooling, not a live-product surface — this master ledger records that classification explicitly, as `LEDGER.md` itself requested, so the fix is not misread as protecting the current live app from this exact failure mode.

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

The final architecture is provider-neutral below the authenticated fetch boundary:

```text
AUTHENTICATED PROVIDER FETCH
        ↓
PRIVATE RAW CAPTURE
        ↓
DETERMINISTIC NWR TRANSFORM
        ↓
VALIDATION
        ↓
ATOMIC SNAPSHOT
        ↓
CANONICAL LEAGUE STATE
        ↓
NWR DECISION TOOLS
```

NWR owns and tests everything from the private raw capture downward. `src/services/espn_flaim_snapshot_service.py`, `src/services/espn_flaim_snapshot_import_service.py`, and `scripts/refresh_espn_flaim_snapshot.py` remain the authoritative schema, deterministic transform/validation/activation service, and preview-by-default CLI. `src/services/league_capability_service.py::capabilities_from_espn_flaim_snapshot()` remains the capability boundary after activation.

**LIVE OBSERVATION (2026-10-01):** this Codex session had a separate, authenticated, read-only Flaim Fantasy connector. `get_user_session` returned both real ESPN leagues with the expected identities. Real `get_league_info`, `get_roster`, and `get_free_agents` calls succeeded for both leagues. Private, gitignored `nwr_espn_flaim_raw_capture_v1` files were saved under `local_exports/redraft_v1/espn_flaim_captures/`; neither raw payload nor generated snapshot is tracked by git.

**ACTUAL TEST RESULT:** the importer preview accepted both captures and passed every schema/profile/provider/team identity check:

- KHA: provider league `1298250946`, team `4`, `Colety Crusaders`, season `2026`, 16 teams, 13 current roster players, and a real bounded 100-player available pool.
- 403 N 18th and friends: provider league `1009373442`, team `5`, `Spencer's Smart Team`, season `2026`, 8 teams, 17 current roster players, and a real bounded 100-player available pool.

**INSPECTED CODE + LIVE OBSERVATION:** activation was deliberately withheld for both leagues. Flaim's current `get_league_info` response exposed `H2H_POINTS`, matchup periods, tie rules, and roster construction, but did not expose the league's actual per-stat scoring multipliers. The raw captures therefore contain no invented scoring rows, and the deterministic importer correctly reports `Scoring completeness: UNKNOWN`. The provider responses also exposed free-agent-versus-waiver state and waiver-clear timestamps, but the current `nwr_espn_flaim_raw_capture_v1`/snapshot schema has no fields for those facts, so they were observed but not silently forced into another field.

- **KHA FINAL STATUS:** `OWNER_ACTION_REQUIRED`.
- **403 N 18th FINAL STATUS:** `OWNER_ACTION_REQUIRED`.
- **EXACT ACTION:** provide a real authenticated ESPN/Flaim export or capture that includes each league's exact per-stat scoring multipliers. Do not describe the league only as standard, half-PPR, or PPR. The capture must identify each provider scoring setting and numeric value so NWR can map it honestly, re-run preview, and activate only after the scoring check passes.
- **EXPECTED SUCCESS SIGNAL:** importer preview reports real scoring rows with an honest `PARTIAL` or `COMPLETE` classification appropriate to the supplied provider fields, all existing identity/roster/pool checks still pass, and only then the snapshot is atomically activated and live-verified.
- **CURRENT TRUST BOUNDARY:** the real captures and preview results prove authenticated provider access, league identity, roster, lineup-slot classification, and bounded availability. Neither league is `LIVE_IN_NWR`; no active snapshot was written, no profile identity field was hand-edited, and no OAuth work is requested.

---

## Section 6 — The four long-running backend-API test failures

Per the dispatch's instruction, these are cited, not re-litigated. Full detail: `docs/codex/dogfood_rebuild_20260929/LEDGER.md`'s `# Exact full-suite failure reconciliation` section (lines 835–882) and `docs/codex/dogfood_rebuild_20260929/FULL_SUITE_FAILURE_INVENTORY.md`'s `## The four long-running backend-API failures -- final disposition` section (lines 41–80), both independently re-read by this pass and confirmed internally consistent with each other and with the dispatch's own stated expectations.

1. **`test_dynasty_facade_composes_real_governed_workflows`** — **`INTENTIONALLY_BLOCKED_WITH_CURRENT_REASON`**. Classified `ENVIRONMENT_DEPENDENCY`: fails at exactly one field (`marketMatched: 239` real vs. `230` hardcoded in the test), driven by the live, machine-wide, non-reproducible `%LOCALAPPDATA%\NinersWarRoom\data\refresh_data` DynastyProcess snapshot (this pass's own fresh `marketFreshness` live check — see sections 1.12/3.4 above — independently confirms this is the same real, independently-aging data source, still live and still drifting today). Deliberately not forced green, since hardcoding a new number against a source that "can change schema/values day to day" would only be correct until the next refresh.
2. **`test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`** — **`IMPLEMENTED_AND_TEST_VERIFIED`**. Fixed: `rookie_veteran_dynasty_bridge_service.py`'s stale pointer to an abandoned 608-row candidate snapshot was repointed to the real, currently-governed Freeze V7 (564-row) snapshot every other live surface already uses.
3. **`test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`** — **`IMPLEMENTED_AND_TEST_VERIFIED`**. Fixed: two stacked stale test assertions (an unforced real `NWR_FANTASYPROS_API_KEY` precondition, and a missing `nwrPureExperimental` preset key never added to the test's expected key set) — zero production code changed.
4. **`test_facade_has_no_streamlit_or_app_component_dependency`** — **`IMPLEMENTED_AND_TEST_VERIFIED`**. Fixed: a real AST-check bug in the test itself (it inspected every imported symbol name, not module name, false-triggering on real function imports like `apply_status_overrides_to_ranking`) — corrected to inspect module names only; the facade genuinely has zero real Streamlit/legacy-`app` coupling.

Combined result, quoted from both source documents: **`tests/test_desktop_application_api.py` final state: 50 passed, 1 failed** — down from the historically-documented 4 failures to exactly 1, by exact test name, not estimate.

---

## Part 2 — Historical Requirement Closure

Branch: `upgrade/nwr-prospective-outcomes-v1-20260914`
Worktree: `C:\NWR\prospective-outcomes-v1`
Starting HEAD for this pass: `5d89a8f7` (confirmed via `git log -1 --oneline` at session start — matched exactly; untracked entries were only the two known `local_exports.backup-*` directories, untouched).

This is Part 2 of the owner-demanded Master Requirement Ledger: older historical requirements going back months, predating the current dogfood-rebuild cycle documented in Part 1 above. It reuses Part 1's exact disposition taxonomy and evidence-labeling convention verbatim (see Part 1's header). Built by reading Part 1 in full, `LEDGER.md` (902 lines) and `FULL_SUITE_FAILURE_INVENTORY.md` (1195 lines) in full, all 38 files under the coordinating session's own `memory/` directory, and by independently spot-checking a representative sample of the resulting claims this pass — fresh `curl` calls against the real running dev backends (Redraft PID 2888/18742, Dynasty PID 22464/18741, both identity-verified via `Get-CimInstance Win32_Process` before use) against the real Las Vegas Enginerds and Fantasy Gamers leagues, plus direct code inspection — not merely citing prior sessions' claims. No source code was modified by this pass; it is pure documentation/verification, per this pass's own explicit hard boundary.

Per the owner's exact instruction, conflicting historical requirements are reconciled with **"NEWEST explicit owner request wins."** Where a genuinely older, now-superseded version of a Part-1-closed topic exists, it is dispositioned here explicitly rather than silently dropped.

---

### 7.1 Original custom Dynasty identity

- **OWNER REQUEST**: Give the owner's real Dynasty league its own real, custom identity (true scoring rules, true roster shape, true draft-pick capital) rather than a generic template.
- **FIRST KNOWN CONTEXT**: `nwr-dynasty-league-import-v1` memory (session `73e6052b`, 2026-09-18/19) — the owner supplied their real league identity (Las Vegas Enginerds, Sleeper league `1344772855908290560`, team "Niners", roster 7) after two prior passes ([[nwr-full-cycle-v1]], [[nwr-dogfood-v1]]) confirmed no real dynasty league was configured anywhere on the machine.
- **CURRENT IMPLEMENTATION**: `src/services/dynasty_sleeper_league_service.py` (real GET-only Sleeper fetch + a pure `annotate_ownership()` join, never touching `governed_asset_registry_service.py`'s valuation computation); real captured custom facts — non-PPR (`rec=0.0` despite 0.4 first-down bonuses), `pass_td=3`, all 2pt=2, real kicker-distance tiers, **no DST/DEF roster slot at all**, `taxi_slots=0`, `reserve_slots=2`, `num_teams=10`, FAAB waivers, pick trading on; real draft-pick capital (2026 historical 5 owned, 2027 projected 5, 2028 projected 6, correctly excluding the league's separate one-time 24-round startup draft from the baseline). Active-league selection persists server-side (`local_exports/dynasty_v1/active_league_profile.json`).
- **TEST COVERAGE**: byte-identical-when-omitted regression tests on `dynasty_bootstrap`/`dynasty_workspace`/`dynasty_asset`/`compare_dynasty_assets`/`evaluate_dynasty_trade` (all gained an optional `league_profile_id` param, every one a no-op when omitted, per `nwr-dynasty-league-import-v1`).
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `GET /api/v1/bootstrap` (dynasty): `leagueId: "1344772855908290560"`, `leagueName: "Las Vegas Enginerds"`, `myRosterId: 7`, `lifecycleContext.waiverType: "FAAB"`, `faabEnabled: true` — the exact real custom identity facts this topic asked for, still live and correct today, independently of Part 1's own separate fresh checks of the same league for different requirements (1.1/1.4/1.12).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: None for the identity capture itself. Rookie-pick-asset ownership still has no crosswalk (see 7.12 below); no multi-league picker UI exists for Dynasty yet (single active-league profile only) — a real, disclosed, still-open gap from the same memory entry, not newly found.

### 7.2 Current Dynasty value

Fully covered by Part 1 §1.4 ("Current NWR dynasty value vs. frozen base authority") and §1.13 ("NWR-vs-market disagreement"). Nothing older or distinct was found: before the current cycle's Worker 8 restructuring, the Dynasty Rankings page simply showed the frozen base board with no "current vs. base" separation at all — not a different implementation of the same idea, just the literal absence of the concept this topic asks about, which Part 1 §1.4 is the first and only real implementation of.

- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (via Part 1 §1.4/§1.13; cross-reference only).
- **REMAINING ACTION**: None beyond Part 1 §1.4's own remaining action.

### 7.3 NWR vs market

Fully covered by Part 1 §1.13 (Dynasty edge/gap cards) and §2.12 (Redraft's "Market Rank (ADP)" vs. "War Room Rank" columns, the AGENTS.md-mandated separation) and §3.4 (market freshness). The historical origin of this requirement is AGENTS.md's own standing rule ("Separate Official Rank, Market Rank, War Room Rank, and My Rank") — Part 1 Section 4 already dispositions Official Rank/My Rank as the two signals that genuinely don't exist; Market Rank vs. War Room Rank is the pair that does, and Part 1 §2.12 is its first and only real implementation (the column used to be a single plain "Rank").
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (via Part 1 §1.13/§2.12/§3.4; cross-reference only).
- **REMAINING ACTION**: None beyond Part 1's own remaining actions.

### 7.4 Dynasty waiver logic

Fully covered by Part 1 §1.5. Nothing older exists to reconcile: `nwr-pre-ui-architecture-v1`/Worker 7's own `INSPECTED CODE` finding confirmed Dynasty had **zero** waiver route, weekly-lineup route, streamer route, or backend of any kind before that cycle — there is no prior, now-superseded version of Dynasty waiver logic to compare against "newest wins" rules for; Part 1 §1.5 is the first real implementation, not a replacement of an older one.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (via Part 1 §1.5; cross-reference only).
- **REMAINING ACTION**: None beyond Part 1 §1.5's own remaining action (the closed-240-row registry roster-need-miscount limitation).

### 7.5 Trade-for / trade-away (general vision)

- **OWNER REQUEST**: A general trade-system vision distinct from the specific mechanics (ownership rules, counter generation, card density) already covered in Part 1 — the owner wanted real "who should I target" and "who should I shop" workspaces in both apps, not merely a package evaluator.
- **FIRST KNOWN CONTEXT**: Worker 7, `LEDGER.md` Item 10 ("Trade Finder discoverability") and the pre-existing Dynasty `Trade Block / Targets` manual workspace it found already real.
- **CURRENT IMPLEMENTATION**: Dynasty: `Analyze Trade` (governed package evaluator) + `Market Gaps` (NWR-vs-market view) + `Trade Block / Targets` (a real, persisted manual trade-shopping workspace, part of `src/services/personal_workspace_service.py`'s Dynasty Planning Console family) + `Generate counters` (Part 1 §1.10). Redraft: `Trade Finder` (3 real search modes, see 7.6–7.8 below) + `Analyze Trade` + counter generation (Part 1 §2.16). Together these satisfy the general "trade-for/trade-away" vision in both apps — a real workspace exists for proposing, evaluating, countering, and (Redraft only) searching trades; the specific remaining gap is Dynasty's own win-win/target-player SEARCH engine, already named and tracked as a real capability gap in Part 1 §1.6/1.7, not re-litigated here.
- **TEST COVERAGE**: Part 1 §1.6/§1.10/§2.16's own test files, plus `tests/test_desktop_application_api.py`'s Dynasty workspace/decision-journal coverage.
- **LIVE PROOF**: Independently re-confirmed this pass via fresh calls already made for Part 1 and 7.6–7.8 below (Redraft Trade Finder modes; Dynasty's `Analyze Trade`/counter endpoints) — all real, all live today.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` for the general vision as it exists today in both apps.
- **REMAINING ACTION**: Same as Part 1 §1.6/§1.7 — a real Dynasty win-win/target-player trade SEARCH engine (not just an evaluator/counter-generator) remains a named, deliberately-unbuilt capability gap, not a defect.

### 7.6 Find Win-Win

- **OWNER REQUEST**: A real trade-finder mode that broadly searches every opponent for mutually beneficial packages.
- **FIRST KNOWN CONTEXT**: `src/services/trade_package_search_service.py`'s own module docstring (`FIND_WIN_WIN — broad search across every opponent for mutually [beneficial trades]`); confirmed real and discoverable by Worker 7 (`LEDGER.md` Item 10: "the real search completed with 15 candidates across 8 opponent rosters, 900 packages evaluated").
- **CURRENT IMPLEMENTATION**: `TradeSearchMode = Literal["TARGET_PLAYER", "FIND_WIN_WIN", "IMPROVE_POSITION"]` (`trade_package_search_service.py` line 90); `GET /api/v1/redraft/trade-finder` is the dedicated FIND_WIN_WIN-shaped endpoint; `redraft_trade_finder()`/`redraft_trade_package_search(mode="FIND_WIN_WIN")` both reachable from the Redraft `Trade Finder` nav route.
- **TEST COVERAGE**: `tests/test_trade_finder_service.py`, `tests/test_trade_package_search_service.py`, `tests/test_redraft_trade_finder_package_search_kdst_composition_fix.py` (already cited in Part 1 §2.17).
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `GET /api/v1/redraft/trade-finder` against the real Fantasy Gamers league: HTTP 200, a real `decisionEnvelope` with a `primaryRecommendation` naming a real player — matching Part 1 §2.17's own post-fix `4`-candidate finding exactly (unregressed today).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` — Redraft only; absent for Dynasty per Part 1 §1.6/§1.7 (not re-litigated).
- **REMAINING ACTION**: None for Redraft. Dynasty equivalent remains the named gap in Part 1 §1.6/§1.7/7.5.

### 7.7 Target Player

- **OWNER REQUEST**: A real trade-finder mode where the owner names one specific player they want and the system searches for packages that could acquire them.
- **FIRST KNOWN CONTEXT**: Same `trade_package_search_service.py` docstring as 7.6 (`TARGET_PLAYER — the owner names one specific player they want; search [for acquiring packages]`); the K/DST-composition-gap-closure pass (`LEDGER.md`, "K/DST Trade Finder composition gap — closed") found and fixed a real, dispatch-unanticipated defect specifically in this mode (a real opponent-owned K/DST target unconditionally raised `TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED` before the fix).
- **CURRENT IMPLEMENTATION**: `search_target_player_packages()`; `POST /api/v1/redraft/trade-package-search` with `{"mode": "TARGET_PLAYER", "targetPlayerSleeperId": "<sleeper id>"}` (confirmed exact required field name via direct route inspection, `src/desktop_api/server.py` line ~819 — the field is Sleeper-ID-keyed, not canonical-ID-keyed, a real, load-bearing distinction from every other trade endpoint in this app).
- **TEST COVERAGE**: `tests/test_trade_package_search_service.py`, `tests/test_redraft_trade_finder_package_search_kdst_composition_fix.py` (the two TARGET_PLAYER-specific regression tests: real opponent K/DST resolves; genuinely-unknown id still fails honestly).
- **LIVE PROOF**: Independently exercised fresh this pass against the real Fantasy Gamers league: resolved a real opponent roster player (Jared Goff, sleeper id `3163`, on "Ben Luvs My Johnson"'s roster via `GET /api/v1/redraft/opponent-rosters`), then called `POST /api/v1/redraft/trade-package-search` with `{"mode":"TARGET_PLAYER","targetPlayerSleeperId":"3163"}` — HTTP 200, a real `decisionEnvelope` with `mode: "TARGET_PLAYER"` in the response, freshly reproduced today.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` — Redraft only.
- **REMAINING ACTION**: None for Redraft. No Dynasty equivalent (Part 1 §1.6/§1.7/7.5).

### 7.8 Improve Position

- **OWNER REQUEST**: A real trade-finder mode where the owner names a position of need and the system searches by-position for upgrades.
- **FIRST KNOWN CONTEXT**: Same `trade_package_search_service.py` docstring (`IMPROVE_POSITION — the owner names a position of need; every [opponent-owned player at that position is searched]`).
- **CURRENT IMPLEMENTATION**: `search_improve_position_packages()`; `POST /api/v1/redraft/trade-package-search` with `{"mode": "IMPROVE_POSITION", "position": "<POS>"}`.
- **TEST COVERAGE**: `tests/test_trade_package_search_service.py`.
- **LIVE PROOF**: Independently exercised fresh this pass against the real Fantasy Gamers league: `POST /api/v1/redraft/trade-package-search` with `{"mode":"IMPROVE_POSITION","position":"WR"}` — HTTP 200, a real `decisionEnvelope` with `mode: "IMPROVE_POSITION"`, freshly reproduced today.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` — Redraft only.
- **REMAINING ACTION**: None for Redraft. No Dynasty equivalent (Part 1 §1.6/§1.7/7.5).

### 7.9 Buy-low / sell-high

- **OWNER REQUEST**: A named "buy-low"/"sell-high" concept somewhere in the trade tooling — surface players whose market value is temporarily depressed (buy opportunity) or inflated (sell opportunity) relative to NWR's own view.
- **FIRST KNOWN CONTEXT**: Worker 7/8's own repeated disclosure that `BUY_LOW`/`SELL_HIGH` are not implemented Trade Finder search modes (Part 1 §1.6's REMAINING ACTION, §2.9's "Keep vs Stream" is a different, unrelated concept).

**Investigation (this pass, INSPECTED CODE — two genuinely separate code paths found, neither reachable by the owner today)**:
1. `src/services/trade_roster_negotiation_service.py` (confirmed by Part 1's own Worker-2-sourced finding to be "the legacy, dead" Dynasty trade service — zero references anywhere in `desktop_facade.py`, confirmed again by grep this pass) does compute a real `"potential buy-low"` string inside its `gap_interpretation` field (line 689). This is real, computed logic — but it belongs to a service with no live call site at all. Its architecture was superseded by the current `trade_decision_assistant_service.py` → `owner_asset_evidence_service.py` stack, none of which model a buy-low/sell-high concept.
2. `src/services/personal_workspace_service.py`'s Dynasty "Personal Board" entry schema (the backend for the `workspace.tsx` "My Board" page) has validated `sell_high`/`buy_low` boolean fields in its own `known` field set (line ~664-665) alongside `my_rank`/`my_tier`/`conviction` — but **this pass independently confirmed, by reading the full chain, that none of these four fields are reachable by the owner today**: the HTTP route's own field whitelist (`src/desktop_api/server.py` line 432: `{"assetId", "watchlist", "target", "avoid", "tags", "notes", "teamWindow"}`) never accepts them from any client, the facade's own `_dynasty_workspace_payload()` serializer (`desktop_facade.py` line ~1386) never includes them in what it sends back to the frontend, and `workspace.tsx`'s real "My Board" UI only ever renders `watchlist`/`target`/`avoid`/`tags`/`notes`/`teamWindow` (confirmed by direct grep — zero occurrences of `sellHigh`/`buyLow`/`myRank`/`myTier`/`conviction` anywhere in `desktop/apps/dynasty/src`). **This is a real, previously-undocumented finding from this pass**: the data model was clearly designed to support owner-tagged buy-low/sell-high/my-rank/my-tier/conviction, but the capability is completely orphaned — present in the schema, invisible and unreachable everywhere else. Not fixed this pass, per the dispatch's explicit "document, do not fix" boundary for a real, previously-undocumented finding.

- **CURRENT IMPLEMENTATION**: See above — a dead computed heuristic in an unreachable legacy service, plus an orphaned (schema-only) manual-tag capability in the live Personal Board service.
- **TEST COVERAGE**: None exercises the orphaned fields through the real HTTP/UI path (none can — the whitelist blocks them); `trade_roster_negotiation_service.py`'s own tests (if any) exercise dead code only.
- **LIVE PROOF**: Independently confirmed this pass via direct code read (not a live HTTP call, since the whitelist makes one impossible) that `POST` to the Personal Board update route with `buy_low`/`sell_high`/`my_rank` in the body would be rejected by the route's own field whitelist before ever reaching `_validate_personal_entry`.
- **FINAL STATUS**: `OWNER_ACTION_REQUIRED` — same category as Part 1 §4.1's "Official Rank" finding: a real, low-risk, scoped implementation path exists (extend the HTTP whitelist + `_dynasty_workspace_payload()` serializer + add 4 simple form controls to `workspace.tsx`, reusing the exact same validated-but-currently-inert backend fields), but whether to build real Buy-Low/Sell-High/My-Rank/My-Tier/Conviction owner tagging is a product decision only the owner can make, not an engineering default.
- **REMAINING ACTION**: Owner decides whether to (a) wire the orphaned Personal Board fields into the HTTP route + frontend (cheapest path, no new backend concept needed), (b) build a real COMPUTED buy-low/sell-high signal (distinct, larger work — would need a defined "temporarily depressed/inflated relative to NWR" formula, never built for the live stack), or (c) decline both. **Flagged prominently in this pass's final report, not silently fixed, per this pass's explicit hard boundary against touching source code.**

### 7.10 Roster-aware counters

Fully covered by Part 1 §1.10 (Dynasty) and §2.16 (Redraft). Nothing older or distinct found — before the current cycle, neither app had ANY trade-counter generation at all (confirmed by Worker 7/8's own `INSPECTED CODE` findings); Part 1 §1.10/§2.16 are the first and only real implementations.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (via Part 1 §1.10/§2.16; cross-reference only).
- **REMAINING ACTION**: None beyond Part 1's own remaining actions (no draft-pick assets in counters; the closed-240-row registry limitation).

### 7.11 Future picks

**7.11a — Dynasty future pick experience**

Fully covered by Part 1 §1.14 ("Future pick experience" — the `Dynasty Planning Console`'s `Future pick ledger` module). Nothing older or distinct found.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (via Part 1 §1.14; cross-reference only).
- **REMAINING ACTION**: None.

**7.11b — Redraft pick concept**

- **OWNER REQUEST**: Does Redraft have any pick-related concept at all, or is this Dynasty-only by design?
- **FIRST KNOWN CONTEXT**: Implicit in the topic list itself; no prior memory entry asks for Redraft picks specifically.
- **CURRENT IMPLEMENTATION**: **Investigated fresh this pass (INSPECTED CODE)**: a full grep of `trade_package_search_service.py` and `redraft_engine_v1_service.py` for `draft_pick`/`DraftPick`/`future_pick` found zero matches for any tradeable pick-asset concept (the only `draft_pick`-adjacent hit, `undo_last_draft_pick`, is the Draft Room's own in-draft pick-recording/undo function — an entirely unrelated meaning of "pick"). This is correct and deliberate: Redraft leagues re-draft their entire roster every season by this product's own design (confirmed by every real Redraft league profile — Fantasy Gamers, 403 N 18th, KHA, Las Vegas Enginerds' own Redraft-side profile — none carry forward draft capital across seasons), so a persistent, tradeable "future pick" asset genuinely does not apply to the Redraft format at all, unlike Dynasty where draft-pick capital is real and multi-year.
- **TEST COVERAGE**: N/A — no such concept exists to test.
- **LIVE PROOF**: N/A — absence confirmed by code-level grep, not a live check.
- **FINAL STATUS**: `NOT_RELEVANT_TO_CURRENT_PRODUCT` — a genuinely-absent concept that correctly does not apply to the single-season redraft format, not an oversight.
- **REMAINING ACTION**: None.

### 7.12 Rookie / identity issues

The historical rookie-identity crosswalk gaps, CFBD/UDK/identity-matching saga spans at least 8 months of memory entries ([[nwr-usage-opportunity-enrichment-v1]], [[nwr-next-draft-final-blocker-closure-v1]], [[nwr-post-draft-engine-forensics-v1]]'s UPDATE 14, [[nwr-prospective-outcomes-v1]]'s DST/suffix fixes). Summarizing current real state, not re-archaeologizing every past cycle, per the dispatch's own instruction:

**7.12a — Veteran/rookie name-identity matching (generational suffixes, team-code aliases)**
- **OWNER REQUEST**: Real players must identity-match correctly regardless of generational suffix (Jr./Sr./II/III) or team-code spelling differences between providers.
- **FIRST KNOWN CONTEXT**: `nwr-prospective-outcomes-v1` memory, "Waiver Night" update — a real, live-reproduced bug where the owner's own rostered Marvin Harrison Jr. failed to identity-match NWR's own ranking (Sleeper drops suffixes, NWR's data doesn't), affecting 26 real ranked players; separately, JAC/JAX team-code mismatch between FantasyPros and Sleeper.
- **CURRENT IMPLEMENTATION**: `normalize_identity_name()` (suffix-stripping, already the mechanism Part 1 §1.3 cites for Dynasty's status-override matching) and the new `src/services/team_code_alias_service.py` (confirmed present via `test -f` this pass).
- **TEST COVERAGE**: Covered by the waiver/streamer test suites referenced in the `nwr-prospective-outcomes-v1`/"Waiver Night" memory entry.
- **LIVE PROOF**: Independently re-confirmed this pass (INSPECTED CODE): `team_code_alias_service.py` exists on disk at the expected path; `fantasypros_kdst_consensus_service.py` (line 219) contains the exact `first_name`/`last_name` fallback the DST-identity fix introduced, still present and unregressed today.
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED`.
- **REMAINING ACTION**: Per `nwr-prospective-outcomes-v1`'s own disclosure, 32/32 K/DST team-code coverage was not independently re-chased this pass beyond confirming the alias service exists; a residual narrow gap may remain for an uncommon team-code spelling never exercised yet.

**7.12b — Dynasty rookie draft-pick-asset ownership crosswalk**
- **OWNER REQUEST**: Real per-roster ownership of rookie draft-pick assets (distinct from veteran player assets) so trade counters and the Future Pick Ledger can reason about them.
- **FIRST KNOWN CONTEXT**: `nwr-dynasty-league-import-v1` memory — "rookie asset IDs use a separate synthetic scheme with no crosswalk built yet."
- **CURRENT IMPLEMENTATION**: Rookie ownership is honestly rendered everywhere as "Ownership unresolved" rather than guessed (confirmed design choice, not a bug) — the same disclosed limitation Part 1 §1.10's REMAINING ACTION already names for picks broadly.
- **TEST COVERAGE**: N/A — no crosswalk exists to test.
- **LIVE PROOF**: Not independently re-verified live this pass (no change expected or found since `nwr-dynasty-league-import-v1`; out of this pass's live-check budget given the item is a disclosed, stable, unchanged gap).
- **FINAL STATUS**: `OWNER_ACTION_REQUIRED` — building a real Sleeper-rookie-pick-ID ↔ NWR-rookie-asset-ID crosswalk is a scoped, real, not-yet-authorized feature.
- **REMAINING ACTION**: Same as Part 1 §1.10's remaining action — owner decision on priority.

**7.12c — Rookie model admission pipeline (Freeze V7, Brooks-class fallback)**
- **OWNER REQUEST**: Rookies and insufficient-history players (lost-rookie-season cases) must be admitted honestly — never silently absent, never a fabricated recommendation-quality claim.
- **FIRST KNOWN CONTEXT**: `nwr-next-draft-final-blocker-closure-v1` memory — Freeze V7 (564 rows: 491 veteran + 73 rookie), the Brooks-class fallback's own real 168-case historical spot-check (cohort-median loses to a zero baseline, 16.79 vs 9.80 MAE), correctly kept `VISIBLE_REVIEW_ONLY`.
- **CURRENT IMPLEMENTATION**: `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/` (already Part 1 §1.4/§4.1's own cited source for Redraft's governed snapshot — same artifact, confirmed unchanged); Brooks-class players remain searchable/draftable/queueable via the manual-asset lane (`udk_unmodeled_skill_asset_service.py`), never silently absent, never promoted into Recommendations.
- **TEST COVERAGE**: Covered by the same governed-snapshot admission tests Part 1 §1.4/§1.12/§4.1 already cite.
- **LIVE PROOF**: Not independently re-verified live this pass beyond Part 1's own fresh confirmation that the Freeze V7-derived snapshot is still the live source for Redraft's ranking (Part 1 §3.2's fresh check).
- **FINAL STATUS**: `ALREADY_IMPLEMENTED`.
- **REMAINING ACTION**: None known; this is a stable, settled state.

### 7.13 Compare

- **OWNER REQUEST**: A Player Compare tool should exist in both apps, be wired to real data, and honestly disclose a player's current status (e.g. a `currentStatusOverride`/injury disclosure) rather than silently showing stale-looking numbers.
- **FIRST KNOWN CONTEXT**: Part 1 §1.3's own REMAINING ACTION ("Dynasty Compare and Rookie Review pages still do not render `currentStatusOverride`") — this topic is instructed to confirm/expand on that finding.

**Investigation (this pass, INSPECTED CODE — both apps)**:
- **Dynasty**: Compare lives at `desktop/apps/dynasty/src/pages/decisions.tsx`'s `ComparePage` (routed at `/compare`, confirmed via `DynastyApp.tsx`). A full grep of `decisions.tsx` for `currentStatusOverride`/`CurrentStatusBadge`/`SEASON_OUT`/any status-override text returned **zero matches** — independently re-confirms Part 1 §1.3's finding is still exactly true today, unregressed and unclosed by any worker across the entire current dogfood cycle, even though the underlying `AssetOption`/`PlayerDetail` rows it reads from (per the TypeScript contract, line 269/291) already carry the field.
- **Redraft**: Compare lives at `desktop/apps/redraft/src/pages.tsx`'s `CompareContent`/`CompareCards` (reachable from the Players tab per the UI-expansion-pass consolidation). **A real, distinct architectural difference from Dynasty was found**: Redraft's `RedraftRanking` TypeScript interface (contracts, line 811) has **no `currentStatusOverride`/`statusOverride` field at all** — Redraft's status-override layer (Part 1 §3.3) is baked directly into the numeric fields (`replacementAdjustedValue`, `overallRank`, `starterGap` — confirmed by Worker 4's own live Achane trace in `LEDGER.md`: `replacementAdjustedValue: 0.0`, `starterGap: 0.0`, `overallRank` sunk to 129, with `projectedPoints` preserved unchanged for provenance) rather than disclosed as a separate labeled field the way Dynasty discloses it. `CompareCards`' own `dimensions` array (pages.tsx line 482-489) renders Overall rank / Position rank / Projected points / Replacement value / Replacement points / Starter gap / Tier / Confidence — **no explicit "Status" row and no override reason/source text anywhere**. Practical consequence: a season-out Redraft player's Compare card silently shows a crushed rank/value with no on-card explanation of why, unlike Dynasty's (missing) badge mechanism — a real, previously-undocumented nuance in how the two apps' Compare pages each fail to fully disclose the same underlying override layer, for two architecturally different reasons.
- **CURRENT IMPLEMENTATION**: Both apps have a real, live, data-wired Compare tool. Neither renders an explicit current-status disclosure on the Compare card itself.
- **TEST COVERAGE**: Redraft: covered by the broader `pages.test.ts`/Players-surface vitest suite (no dedicated status-disclosure assertion). Dynasty: no dedicated test for this specific gap either.
- **LIVE PROOF**: Independently re-confirmed this pass via `GET /api/v1/bootstrap` (redraft, Fantasy Gamers) and direct code read of `decisions.tsx` (dynasty) — both apps' Compare data substrates are live and real; the disclosure gap is a frontend rendering gap in both, confirmed by code inspection rather than a fresh render (consistent with this pass's conservative evidence-labeling standard for presentation-only gaps).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` for Compare's existence/data-wiring in both apps; the specific status-disclosure gap Part 1 §1.3 flagged for Dynasty is independently reconfirmed still open, and a second, distinct instance of the same underlying disclosure gap (architecturally different) is newly documented for Redraft here.
- **REMAINING ACTION**: Dynasty: render the already-present `currentStatusOverride` field on Compare cards (small, mechanical, per Part 1 §1.3). Redraft: a materially larger change — would need a new, separate disclosure field threaded through `redraft_bootstrap()`/`RedraftRanking` (the override is currently baked into values with no label anywhere outside the Draft Room/Cheat Sheet's own admin-facing status-override list), not a simple badge port like Dynasty's fix would be.

### 7.14 Start/Sit historical bugs

Checked memory for the Sunday Readiness cycle's specific named Start/Sit bugs and re-confirmed current state via direct code inspection this pass (not a live render, since forcing a real lineup-illegal state against either real league would risk disrupting it):

- **W1 (hardcoded week=1)**: fixed via shared `useProviderWeek`/`useWeekSelection` hooks (`nwr-sunday-readiness-v1`). **Still holding**: confirmed these hooks remain the shared mechanism (no later pass replaced them).
- **W2/W3 (lock/reserve/taxi/injury-status gaps; a reserve player could beat an active starter; a locked starter could be swapped out; missing-projection players silently vanished)**: fixed via real Sleeper reserve/taxi fields threaded into `build_roster_candidates`/`optimize_weekly_lineup`, plus distinct `RESERVE`/`LOCKED`/`UNRESOLVED_IDENTITY` statuses. **Independently re-confirmed this pass (INSPECTED CODE)**: `src/services/weekly_lineup_optimizer_service.py` still contains `reserve_sleeper_player_ids`/`taxi_sleeper_player_ids` params, `is_reserve`/`is_taxi` tags, and the `OK | UNPROJECTED | EMPTY | UNRESOLVED_IDENTITY | SEASON_OUT` status vocabulary, unregressed.
- **W4 (false "Already optimal"; same incumbent could be benched twice)**: fixed via a real before/after starter-ID-set diff replacing the old swap-explanation logic.
- **The missing-bench-projection-treated-as-zero bug (the Zay Flowers case)**: fixed in `nwr-connection-update-v1` — `SwapReason.projected_delta` is `float | None` with a `delta_basis` (`KNOWN` vs `UNKNOWN_MISSING_BENCH_PROJECTION`) field, forcing LOW confidence rather than fabricating a number.
- **FIRST KNOWN CONTEXT**: `nwr-sunday-readiness-v1` and `nwr-connection-update-v1` memory entries (2026-09-19/20, both pre-dating this cycle).
- **TEST COVERAGE**: `tests/test_weekly_lineup_optimizer_service.py` and the dedicated swap-reason regression tests both memory entries describe.
- **LIVE PROOF**: Independently re-confirmed this pass via direct code read only (INSPECTED CODE) — all three fix mechanisms are still present in the current source tree, unregressed; not re-exercised live against a real lineup this pass since doing so would require manipulating a real league's active lineup, out of this pass's safety bounds.
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` for all four historical bugs — still holding, confirmed by code inspection this pass, not freshly re-rendered live.
- **REMAINING ACTION**: None known. A fresh live-rendered Start/Sit confirmation (last done in `nwr-connection-update-v1`, same-day verified against both real leagues) would be a reasonable but non-urgent follow-up.

### 7.15 Waiver legality/denial bugs

Checked memory for the Sunday Readiness / Waiver Night / Waiver Fix Cycle's specific named historical waiver bugs and re-confirmed current state via direct code inspection this pass:

- **The backwards FAAB-detection bug** (`waiver_type == 1` checked for FAAB when Sleeper's real enum is `0=rolling,1=reverse-standings,2=FAAB` — exactly backwards for both real leagues): fixed in `nwr-sunday-readiness-v1`. **Independently re-confirmed this pass (INSPECTED CODE)**: `src/application/desktop_facade.py` line 1042 now reads `is_faab = waiver_type == 2` — the corrected check, unregressed.
- **W5 (THIS_WEEK waiver ranking used season-long marginal utility as primary sort; `becomesStarter` never actually weekly-evaluated)**: fixed via `simulate_this_week_add_drop` (real before/after lineup-gain simulation).
- **IR/reserve players could be recommended as Add/Drop drops** (Waiver Night #3): fixed, reproduced with a fixture before the fix.
- **FAAB fabricating positive dollar bids for zero/negative-utility and even unmatched-identity candidates** (Waiver Fix Cycle V1 — a real, live-confirmed bug: C.J. Stroud at exactly 0.0 utility was pricing $28-47): fixed via a gate on the pricing formula. **Independently re-confirmed this pass (INSPECTED CODE)**: `src/services/waiver_engine_service.py` line 849 (`if ... pricing_utility <= 0`) and line 869 (`if candidate.marginal_utility <= 0`) — both gates present and unregressed.
- **LIVE FAAB budget double-request race / a failed budget read indistinguishable from a real $100**: fixed (budget now derived fresh server-side every request with an honest "unavailable" state).
- **Add/Drop's displayed "net" value compared the add against the original roster but the drop against a different post-drop roster** (a real sign-flip risk): fixed to same-context evaluation.
- **FIRST KNOWN CONTEXT**: `nwr-sunday-readiness-v1`, `nwr-prospective-outcomes-v1`'s "Waiver Night"/"Waiver Fix Cycle V1" updates (2026-09-15/16/19, all pre-dating this cycle).
- **TEST COVERAGE**: `tests/test_waiver_engine_service.py`, `tests/test_dynasty_waiver_service.py`, and the dedicated regression suites each memory entry names.
- **LIVE PROOF**: Independently re-confirmed this pass via direct code inspection of the FAAB-type check and the positive-utility gate (both still present, unregressed); not re-exercised live against a real waiver claim this pass (would require a real transaction window, out of this pass's read-only safety bounds — consistent with every prior pass's own discipline here).
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` for every bug listed — all confirmed still fixed and holding in the current source tree.
- **REMAINING ACTION**: None known. `nwr-prospective-outcomes-v1`'s own disclosed residual (waiver-ranking latency 1.1-12.6s from an uncached Sleeper catalog fetch) was separately closed by `nwr-full-cycle-v1`'s cross-request cache (0.70s cold vs ~0.00001s warm) — confirmed present via `src/services/sleeper_player_catalog_cache.py`'s existence this pass, not re-benchmarked fresh.

### 7.16 K/DST historical bugs

Distinct from the current cycle's own K/DST Trade Finder composition fix (Part 1 §2.17, cited not re-litigated). Checked memory for OLDER K/DST bugs and re-confirmed current state:

- **"KEEP CURRENT" structurally unreachable** (K/DST streamers always preferred the best-ECR unrostered player as primary even when the owned starter ranked better — `nwr-sunday-readiness-v1` W6): fixed to prefer the first genuinely actionable row in ECR order. **Independently re-confirmed this pass (INSPECTED CODE)**: `src/services/streamer_horizon_service.py` lines 123/132 still contain the literal `"KEEP CURRENT"` action string on a real, reachable code path.
- **Weekly K/DST points used generic provider `pts_ppr`, ignoring real league-custom scoring** (W7): fixed via a real raw-stat dot-product against the league's actual `scoring_settings`; DST pickups are now structurally never recommended for a league with no DST slot (Las Vegas Enginerds).
- **JAC/JAX team-code alias gap** (Waiver Night #1 — also caught a second instance on the K side): fixed via `team_code_alias_service.py`. Independently re-confirmed present this pass (same check as 7.12a).
- **DST identity-matching bug** (Sleeper's DST catalog entries carry no `full_name`, so no real DST could ever identity-match; `nwr-prospective-outcomes-v1`'s own dedicated fix-proposal-then-correction): fixed via the `first_name`/`last_name` fallback. Independently re-confirmed present this pass in `fantasypros_kdst_consensus_service.py` (line 219), unregressed — same evidence as 7.12a.
- **FIRST KNOWN CONTEXT**: `nwr-sunday-readiness-v1` memory entry (explicitly named by the dispatch's own topic text), `nwr-prospective-outcomes-v1`'s DST-identity-fix updates.
- **TEST COVERAGE**: `tests/test_streamer_horizon_service.py` and the dedicated DST-identity regression test `nwr-prospective-outcomes-v1` describes.
- **LIVE PROOF**: Independently re-confirmed this pass via direct code inspection (all four fix mechanisms present, unregressed in the current source tree); not re-exercised live against a real streamer request this pass beyond what Part 1 §2.17/this document's 7.12a already freshly checked.
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` for all four historical bugs.
- **REMAINING ACTION**: None known. `nwr-prospective-outcomes-v1`'s own disclosed residual (Jacksonville's JAC/JAX code specifically, confirmed fixed by this exact alias service) was closed by the Waiver Night pass per that memory's own update — not independently re-verified against a live Jacksonville row this specific pass, but the fix mechanism is confirmed present.

### 7.17 Rankings UX issues

Fully covered by Part 1 §2.10-§2.14. Nothing older or distinct found beyond what Section 7.3 above already traces to AGENTS.md's own standing terminology rule. The one historical detail worth naming explicitly: before Worker 9's restructuring, the Rest-of-Season board had a single plain `"Rank"` column with no Market Rank column at all, and the Weekly board had no rank ordinal whatsoever — both are now closed per Part 1 §2.10-§2.13, which are the first and only real implementations of this requirement, not a replacement of an older one.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (via Part 1 §2.10-§2.14; cross-reference only).
- **REMAINING ACTION**: None beyond Part 1's own remaining actions.

### 7.18 Lifecycle correctness

Fully covered by Part 1 §1.1/§1.15/§2.1/§3.1 for the CURRENT shared `LeagueLifecycleContext` mechanism. Older, now-superseded/fixed lifecycle bugs found in memory and re-confirmed current state this pass:

**7.18a — PRE_DRAFT-stuck bug for real completed drafts**
- **OWNER REQUEST**: A league with a real, completed draft must never be shown as still in Draft/Pre-Draft.
- **FIRST KNOWN CONTEXT**: `nwr-dogfood-v1` memory — KHA (157/192 picks, no K/DST in its stream) and 403 N 18th (118/128 picks) both stuck at PRE_DRAFT because the local draft-board pick count didn't exactly match `team_count * rounds`.
- **CURRENT IMPLEMENTATION**: `league_lifecycle_service.py::resolve_league_lifecycle` gained two additive, default-off params (real provider status takes priority when available; a draft-board stale >24h with ≥1 real pick resolves IN_SEASON for non-live-syncable providers), later tightened in `nwr-sunday-readiness-v1` to also require a ≥50% completion-ratio floor (verified not to regress KHA at 81.8% or 403N18th at 92.2%, while correctly refusing a genuinely barely-started case).
- **TEST COVERAGE**: Covered by `tests/test_league_lifecycle_service.py` (the same file Part 1 §1.1/§3.1 already cite).
- **LIVE PROOF**: Independently re-confirmed this pass via a fresh `GET /api/v1/bootstrap` (dynasty, Las Vegas Enginerds — a league with a real completed Sleeper draft): `lifecycleContext.draftStatus: "COMPLETE"`, `seasonPhase: "REGULAR_SEASON"` — the same live check already performed for Part 1 §1.1, independently reconfirming this historical fix still holds for a real league today.
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED`.
- **REMAINING ACTION**: `nwr-dogfood-v1`'s own disclosed residual (Fantasy Gamers' sidebar can still show Pre-Draft in the real app on first paint, since bootstrap makes zero live network calls by design) remains open — not independently re-checked live this pass.

**7.18b — Freshness-cliff test/governance recurrence**
- **OWNER REQUEST**: N/A (this is an internal test-environment reliability issue, not a direct owner feature request) — included here because it recurred across many historical passes and directly caused real, live-blocking symptoms for the owner's actual leagues on at least one occasion.
- **FIRST KNOWN CONTEXT**: `nwr-draft-upgrade-hq-baseline-failures` memory — a 30-day `MAX_PROJECTION_AGE_DAYS` per-row check (independent of any governance receipt's own `valid_until`) that recurs on its own clock; `nwr-403-n-18th-espn-league-unresolved`'s own UPDATE records this mechanism genuinely blocking 100% of the installed 2026 snapshot for every real profile on a real draft night (2026-09-07/08), requiring an emergency, scoped, time-boxed owner-authorized bypass.
- **CURRENT IMPLEMENTATION**: Resolved for real (not merely bypassed again) by `nwr-post-ui-product-v1`'s Worker 2 — migrated to a real, still-valid, owner-approved Freeze V7 artifact (`valid_until: 2026-10-08`), the same artifact Part 1 §1.4/§1.12/§3.2/§4.1 already cite as the live source today.
- **TEST COVERAGE**: Covered by the governed-snapshot admission tests Part 1 already cites.
- **LIVE PROOF**: Independently re-confirmed this pass via Part 1's own fresh checks (§1.12/§3.2: the governed model's `valid_until: 2026-10-08` approval window is correctly still active today, 8 days of runway remaining as of this pass).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` — the underlying artifact is current and the historical freshness-cliff mechanism is resolved, not merely bypassed again.
- **REMAINING ACTION**: The approval's own 8-remaining-days timing (expires 2026-10-08) is already flagged by Part 1 §2.14 as an owner-awareness item, not duplicated as a new finding here.

### 7.19 Draft/offseason experience

- **OWNER REQUEST**: The Draft Room / Cheat Sheet / Draft Cockpit experience must still work correctly when promoted during draft season, per the lifecycle-aware demotion logic Part 1 §1.1/§1.15/§2.1 describe for the regular season.
- **FIRST KNOWN CONTEXT**: Worker 6's own lifecycle-navigation design (`LEDGER.md` Items 6-9) — the same mechanism that demotes Draft Room/Cheat Sheet in season is explicitly bidirectional (promotes them in `ROOKIE_PRE_DRAFT`/`DRAFT_APPROACHING`/`DRAFT_DAY`/`OFFSEASON` phases).

**Investigation (this pass, INSPECTED CODE/TEST, explicitly INFERENCE-labeled since it is currently regular season, 2026-09-30, and this pass cannot safely force either real league into a draft-phase state to render it live)**:
- `desktop/apps/redraft/src/lifecycle-navigation.test.ts` line 19, `it("promotes draft tools during draft season", ...)` — confirmed present and part of the same test file Part 1 §2.1/§2.15 already cite as passing. **INFERENCE**: a passing test asserting the exact promotion behavior this topic asks about is strong evidence the code path is real and exercised, though it is evidence from a test fixture, not a live render of either real league in an actual draft state.
- `desktop/apps/dynasty/src/lifecycle-navigation.test.ts` carries the equivalent Dynasty-side coverage (Draft Cockpit/Rookie Review promotion), per Part 1 §1.15's own test-coverage citation.
- The underlying draft engine itself (`redraft_draft_room_v1_service.py`, `marginal_roster_utility_v2`, the K/DST timing backstop, the Superflex CPU-policy repair, the roster-legality service) was extensively exercised and promoted in the pre-cycle saga (`nwr-post-draft-engine-forensics-v1`, `nwr-overnight-v3-legality-repair-and-buildout`) and has not been touched by any worker in the current dogfood-rebuild cycle (confirmed by `git diff --stat` across every Part 1 worker's own reported file list — none touch `redraft_draft_room_v1_service.py`). **INFERENCE**: since nothing in the current cycle modified the draft engine itself, and the lifecycle-promotion test still passes, the draft experience most likely still works exactly as it was last live-verified (the real 403 N 18th draft, 2026-09-07) — but this is reasoned from an absence of changes plus a passing unit test, not a fresh live render this pass performed or could safely perform.
- **CURRENT IMPLEMENTATION**: Unchanged from the pre-cycle state described across the `nwr-draft-room-gui-consolidation-real-pass`/`nwr-owner-feedback-closure-v4-saga`/`nwr-post-draft-engine-forensics-v1`/`nwr-overnight-v3-legality-repair-and-buildout` memory chain.
- **TEST COVERAGE**: `desktop/apps/{redraft,dynasty}/src/lifecycle-navigation.test.ts` (draft-season promotion assertions); the full backend draft-engine test suite (`tests/test_redraft_draft_room_v1_service.py`, 54 tests per the last recorded count) — not re-run this pass (out of this pass's "targeted spot-checks only" boundary for a non-urgent confirmation).
- **LIVE PROOF**: Not performed this pass, by design — it is currently regular season for both real leagues, and forcing either into a simulated draft-phase render to test this would risk disrupting real league state, explicitly out of this pass's safety bounds. This is an honest INFERENCE-labeled disposition, not a claimed live render.
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` — based on passing lifecycle-promotion tests and the absence of any draft-engine change in the current cycle, not a fresh live render.
- **REMAINING ACTION**: A real live-rendered confirmation of Draft Room promotion, next time either real league approaches its own next draft (Fantasy Gamers/Las Vegas Enginerds are both annual-redraft/dynasty-rookie-draft leagues respectively, so this will recur), would close the one open INFERENCE in this disposition.

### 7.20 Live vs Mock isolation

- **OWNER REQUEST**: Mock-draft and live-draft data must never cross-contaminate.
- **FIRST KNOWN CONTEXT**: `nwr-owner-mock-qa-v1-findings`/`nwr-real-local-install-location-and-schedule-finding` memory entries (practice-draft profiles vs. real leagues) and the Dynasty FAAB/Redraft Trade lab's own explicit `Real trade` vs. `Hypothetical` mode distinction Part 1 §1.8 already covers for a different (trade-side) instance of the same general discipline.
- **CURRENT IMPLEMENTATION**: `src/services/redraft_draft_room_v1_service.py` line 47: `SUPPORTED_MODES = frozenset({"MOCK", "LIVE_READ_ONLY"})` — a real, structurally-enforced two-mode system, not a label. Multiple gated checks (`if state.get("mode") != "LIVE_READ_ONLY": ...`, lines 1633/1682/1789) guard every live-sync-specific function so a MOCK-mode draft board can never accidentally invoke a real Sleeper live-sync path, and vice versa.
- **TEST COVERAGE**: Covered by `tests/test_redraft_draft_room_v1_service.py`'s mode-gating tests (same file Part 1/7.19 already reference).
- **LIVE PROOF**: Independently confirmed this pass via direct code inspection (INSPECTED CODE) of the mode-gating checks; not exercised live this pass (would require starting a real or mock draft room against a real league's active data, out of this pass's safety bounds for a stable, long-settled mechanism).
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED`.
- **REMAINING ACTION**: None known.

### 7.21 Transaction history / lifecycle

- **OWNER REQUEST**: The app should show real transaction/trade history (adds, drops, trades actually executed on the real platform) distinct from the current roster snapshot.
- **FIRST KNOWN CONTEXT**: No single named memory entry demands this explicitly, but it is implied by multiple historical asks for "what has actually happened in my league" context; the closest existing concept, Redraft's Decision History (`decision-history.tsx`), was built across the `nwr-prospective-outcomes-v1`/`nwr-full-cycle-v1` cycles for a different purpose (NWR's own recommendation/decision traces, never real external platform transactions).

**Investigation (this pass, INSPECTED CODE)**: `src/services/canonical_league_state_service.py` carries its own explicit, honest capability flag: `recent_transactions_supported: bool = False` (line 144), with an accompanying disclosure string (line 148: "...and recent league transactions are not modeled by any [live surface]"). This is a real, deliberate, disclosed absence — not a bug, not a partial build. Redraft's Decision History page is a genuinely different concept (NWR's own recommendation-and-owner-action ledger, confirmed by `decision-history.tsx`'s own data source, `in_season_decision_trace_service.py`) — it has never claimed to be a real Sleeper/ESPN transaction log, and doesn't read one.
- **CURRENT IMPLEMENTATION**: No real external-platform transaction-history surface exists in either app. The one adjacent, real, honestly-distinct concept (Decision History / the Prospective Recommendation Ledger) is NWR's own decision trace, not a league transaction log.
- **TEST COVERAGE**: `canonical_league_state_service.py`'s own capability-flag tests (confirming the flag defaults correctly and is never silently flipped to claim support it doesn't have).
- **LIVE PROOF**: Independently confirmed this pass via direct code inspection; the flag's own value (`False`) was not independently re-verified live via an HTTP call this pass, since no live surface would change behavior based on it either way (it is a documentation/contract-level flag, not yet wired to gate any UI).
- **FINAL STATUS**: `INTENTIONALLY_BLOCKED_WITH_CURRENT_REASON` — honestly, explicitly modeled as unsupported via a real capability flag with a disclosed rationale, rather than silently absent or fabricated.
- **REMAINING ACTION**: Building a real transaction-history surface would need a live Sleeper `GET /league/{id}/transactions/{round}` read (confirmed, by this pass's own earlier grep, to have no existing call site anywhere in this codebase) plus an equivalent (currently nonexistent) ESPN read path. A real, scoped, not-yet-authorized feature — owner decision needed on priority.

### 7.22 Change detection

- **OWNER REQUEST**: A "what changed since I last looked" detection layer — surface what's materially different about the owner's league/roster/market view since a prior visit, not just the current-state snapshot.
- **FIRST KNOWN CONTEXT**: No single dedicated memory entry names this as a standalone historical ask; it is adjacent to (but distinct from) several already-covered concepts: the Attention Center's severity flags (current-state-only, see 7.23), the trade-counter cards' own "What changed" label (Part 1 §1.11 — describes what changed WITHIN one proposed trade, not session-to-session), and the internal rankings-model-patch-audit services (`rankings_post_patch_acceptance_service.py` etc. — research-only, compare one governed admission to the next, never user-facing).

**Investigation (this pass, INSPECTED CODE)**: a full grep for change-detection-shaped terms (`what.?changed`, `change.?detect`, `WhatChanged`, `diff.*snapshot`) across `src/services/` found exactly the three categories named above and nothing else — no session-to-session "since your last visit" diffing concept exists anywhere in either app, for the owner's roster, league state, or market data.
- **CURRENT IMPLEMENTATION**: None exists as a real, named, user-facing "what changed" feature. The closest adjacent real capabilities (Attention Center severity, trade-card "What changed," Decision History's own append-only trace) each answer a different, narrower question and were each already independently verified real in their own right (7.23, Part 1 §1.11, 7.21).
- **TEST COVERAGE**: N/A — no such feature exists to test.
- **LIVE PROOF**: N/A.
- **FINAL STATUS**: `OWNER_ACTION_REQUIRED` — a real, genuinely-unbuilt feature gap, not a defect and not a mislabeled version of something that already exists. No existing substrate (a stored "last-seen" state per owner, per surface) exists to repurpose; building this would be new engineering, not a wiring fix.
- **REMAINING ACTION**: Owner decides whether a real change-detection layer (e.g. "3 of your rostered players have a new status override since you last opened Rankings," "the market gap on X widened by 8 points since yesterday") is worth building, and if so, which surfaces it should cover first. Flagged, not built, per this pass's documentation-only boundary.

### 7.23 Attention Center

- **OWNER REQUEST**: A multi-league attention/notices aggregation — "which of my leagues needs me right now" — across every saved profile.
- **FIRST KNOWN CONTEXT**: `nwr-post-ui-product-v1` memory, Worker 5 — "Multi-League Attention Center (read-only, 'which of my leagues needs me' + cross-league player search)," later hardened across `nwr-full-cycle-v1`/`nwr-dogfood-v1` (a real cross-surface race against the background sweep, fixed; a severity-calibration bug, fixed).

**Investigation (this pass, INSPECTED CODE)**: `desktop/apps/redraft/src/attention-center.ts`'s own module docstring states the exact architecture: a READ-ONLY aggregation layer that activates each saved Redraft profile in turn, reads cheap per-league facts (data health, workspace context, and — for a Sleeper league only — roster/free-agent reads), then unconditionally reactivates whichever profile was active before, in a `finally` block, "regardless of success/failure/partial-completion." This is a real, carefully-designed safety property given this app has exactly ONE active-profile pointer.
- **CURRENT IMPLEMENTATION**: `desktop/apps/redraft/src/attention-center.ts` (orchestration/derivation) + `attention-center-page.tsx` (the rendered page, severity badges `OK`/`UNKNOWN`/`WATCH`/`URGENT` mapped to `safe`/`review`/`review`/`blocked` tones) + `shell-notices.ts`. **Scoped to Redraft's own saved profiles only** — confirmed by file location (`desktop/apps/redraft/src/`) and by the fact that Dynasty is a structurally separate app with its own, different active-league-pointer architecture (Part 1 §3.6/7.1); the Attention Center does not and cannot span Dynasty leagues without its own, separate implementation.
- **TEST COVERAGE**: `desktop/apps/redraft/src/attention-center.test.ts`, `attention-center-scale-benchmark.test.ts` (confirms linear scaling to 50 leagues per `nwr-prospective-outcomes-v1`'s own multi-league-scale characterization).
- **LIVE PROOF**: Independently re-confirmed this pass that the real, current Redraft profile selector returns exactly 3 real visible leagues (per Part 1 §2.3/§2.4's own fresh check this pass cites) — the exact real universe the Attention Center aggregates over today. Not independently re-rendered via Chrome this pass (a presentation-only confirmation already covered by `nwr-full-cycle-v1`'s own live-browser check of the fixed cross-surface race).
- **FINAL STATUS**: `IMPLEMENTED_AND_LIVE_VERIFIED` for its real, current scope (Redraft's own saved profiles, read-only, race-hardened).
- **REMAINING ACTION**: No Dynasty-side Attention Center exists — a real, disclosed, not-yet-built scope gap (Dynasty currently has only one active league at a time with no multi-league picker UI at all, per 7.1's own remaining action, so a Dynasty-side Attention Center would currently have nothing to aggregate over even if built).

### 7.24 Data freshness

Fully covered by Part 1 §3.2 (projection freshness) and §3.4/§1.12 (market freshness). Nothing older or materially distinct found. The one historical detail worth naming precisely: the very first instance of this requirement in this project's history is the "alarming 2026-09-08" owner complaint that opened the current dogfood-rebuild cycle itself (Worker 4, `LEDGER.md` Item 2) — i.e., this requirement's most recent explicit owner articulation IS the current cycle's own Item 2, which Part 1 §3.2/§2.14 already fully disposition; there is no genuinely older, separately-tracked version to reconcile against it.
- **FINAL STATUS**: `ALREADY_IMPLEMENTED` (via Part 1 §3.2/§3.4/§1.12/§2.14; cross-reference only).
- **REMAINING ACTION**: None beyond Part 1's own remaining actions (the governed model's 2026-10-08 approval-window timing flag).

### 7.25 Packaged Desktop / Tauri milestone

- **OWNER REQUEST**: A real, installable native desktop application (not just a browser-served dev build).
- **FIRST KNOWN CONTEXT**: `nwr-post-ui-product-v1` memory, Worker 3/B — "native Tauri packaging resolved via a privacy-safe governance-receipt split."

**Investigation (this pass, INSPECTED CODE + memory-cited evidence, not independently re-built this pass)**: the historical blocker chain is real and precisely traced: (1) Worker 3 found native packaging genuinely blocked by a real, pre-existing privacy guard (`check:resources` forbidding the owner's real name, legitimately present in the governance receipt's own audit trail) — confirmed NOT a toolchain problem (the Rust/Tauri sidecar built, `cargo check` passed). (2) Worker B (`nwr-post-ui-product-v1`'s closure pass) resolved this for real: a private-canonical-receipt vs. release-safe-runtime-summary split (the private receipt stays untouched/immutable/excluded from the bundle, verified two ways — allowlist inspection and extracting the real built MSI's installed payload; a new, hash-bound, zero-PII release-safe summary derives from it) — **the native Tauri package built successfully for the first time in this whole saga** (real NSIS/MSI installers produced), with a real privacy scan of the extracted installer finding zero traces of the owner's real identity/email/AppData path/secrets (one disclosed, unrelated, low-severity finding: the sandbox's own build-machine account name in generic Rust panic-location strings, a standard Cargo toolchain behavior, exact fix documented but not applied).
- **CURRENT IMPLEMENTATION**: The packaging mechanism (`NWR_PRIVACY_SAFE_PACKAGING_DESIGN_V1.md`'s design, `check:resources`'s allowlist, the release-safe-summary derivation) is real, tested (12+ dedicated tests per the memory entry), and was proven to produce a real installable artifact. This pass independently confirmed Dynasty has its own equivalent `bundle:dynasty` target (per `nwr-dynasty-league-import-v1`) mirroring Redraft's `bundle:redraft`.
- **TEST COVERAGE**: 12+ dedicated privacy/tamper-resistance tests per `nwr-post-ui-product-v1`'s own description (not independently re-run this pass — out of this pass's "targeted spot-checks only" boundary for a stable, already-proven mechanism).
- **LIVE PROOF**: **Not independently re-verified by this pass** — this exact worktree (`C:\NWR\prospective-outcomes-v1`) currently has no built native installer artifact (confirmed by this pass's own `find`/`ls` checks against the expected bundle output paths, both empty), and `nwr-full-cycle-v1`'s own Worker 10 found a LATER attempt in this same worktree genuinely failed due to host OOM (2.65GB→2.08GB free of 15.11GB, PyInstaller sidecar-build stage killed), not a code regression — the `check:resources` privacy/allowlist guard itself passed cleanly in that same attempt, confirming the packaging mechanism is still structurally sound, just not exercised to completion in this specific worktree recently.
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` — the packaging mechanism itself is proven to produce a real installable native artifact on this same branch lineage, not merely designed on paper.
- **REMAINING ACTION**: This exact worktree does not currently hold a freshly-built installer (environment-dependent — host RAM, not a code defect, per `nwr-full-cycle-v1`'s own OOM finding at the PyInstaller sidecar-build stage, with `check:resources` itself passing cleanly in that same attempt). Retry `npm run bundle:redraft`/`bundle:dynasty` when host free RAM exceeds the 4-6GB threshold `nwr-full-cycle-v1` recommends; no code change is needed.

### 7.26 Profile isolation

Fully covered by Part 1 §3.6 for the CURRENT Redraft-selector-hide mechanism. Older/distinct historical profile-isolation bugs found in memory and re-confirmed current state this pass:

- **Profile create/duplicate/import race against the Attention Center's background sweep** (a newly-created profile could silently revert to the previously-active league once the sweep's trailing restore fired — `nwr-dogfood-v1`, reproduced live): fixed by wrapping `profile.tsx`'s `create()`/`duplicate()`/`importSleeper()` through the existing `serializeActiveProfileCall` queue. **Independently re-confirmed this pass (INSPECTED CODE)**: `serializeActiveProfileCall` is now referenced in 7 files (`attention-center.ts`, `attention-center.test.ts`, `league.tsx`, `leagues.tsx`, `profile.tsx`, `RedraftApp.tsx`, `shell-identity.tsx`) — broader coverage than the single fix originally described, confirming the guard has since been applied consistently project-wide, not narrowly patched.
- **Manage-Leagues' own "Duplicate profile" silently reverting the active pointer back to the old profile** (a different root cause than the race above — `LeagueScopedPage`'s deep-link-sync effect re-activating whatever the stale URL's `leagueKey` still named): fixed by navigating to the new profile's own URL right after a successful duplicate.
- **A disclosed, NOT-fixed residual**: a ~370ms transient window where the active pointer still briefly touches the OLD profile before self-correcting, left open because the component has zero test coverage and the plausible fixes trade this for a different, unverified failure mode. Also disclosed-not-fixed: a structurally identical exposure at `/league/:leagueKey/profile` (ProfilePage), currently unreachable by any in-app link.
- **A real test beyond what Part 1 §3.6 cites**: `tests/test_redraft_engine_v1_service.py::test_profile_create_edit_duplicate_archive_delete_and_active_isolation` and `::test_profile_specific_draft_boards_are_isolated` (confirmed present via this pass's own grep) — broader profile-isolation coverage than Part 1 §3.6's own cited test names, worth recording here since it directly substantiates this topic.
- **FIRST KNOWN CONTEXT**: `nwr-dogfood-v1` memory (2026-09-17/18).
- **TEST COVERAGE**: `tests/test_redraft_engine_v1_service.py` (the two tests named above), plus the frontend `serializeActiveProfileCall` call sites' own existing test coverage.
- **LIVE PROOF**: `nwr-dogfood-v1`'s own live reproduction-then-fix (not independently re-reproduced live this pass, since deliberately reproducing a profile-activation race against a real league's active profile pointer would risk real state, out of this pass's safety bounds); this pass's own fresh Part 1 §2.3/§3.6 checks independently confirm the current profile universe (3 visible Redraft leagues, Las Vegas Enginerds correctly hidden/Dynasty-only) is stable and correct today.
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` for the two real fixed bugs; the disclosed ~370ms residual and the dormant `/league/:leagueKey/profile` exposure remain real, open, low-severity gaps.
- **REMAINING ACTION**: Same as `nwr-dogfood-v1`'s own disclosed remaining items — both require either new component-test infrastructure (this codebase has zero `.test.tsx` files/`@testing-library/react`, confirmed by `nwr-connection-update-v1`'s own independent finding) or accepting a different, unverified failure-mode tradeoff; neither has been judged worth the risk yet.

### 7.27 Failure behavior

Fully covered by Part 1 §3.5 (failed refresh honesty) and §3.8 (provider failures fail honestly) for request-level failure handling. **UPDATE (Codex F, 2026-10-01)**: the process-level gap this section originally flagged as entirely unbuilt has now been closed with a real, automated gauntlet — `tests/test_reliability_gauntlet.py`, cross-referenced in full in `docs/codex/dogfood_rebuild_20260929/RELIABILITY_GAUNTLET.md` and `LEDGER.md`.

- **ACTUAL TEST RESULT**: 6 passed, 2 `xfail` (expected failures, not errors), independently re-run by the coordinating session and confirmed identical. Cold start, `/startup-proof` HMAC identity validation, 32-way concurrent HTTP request safety, and active-profile-pointer JSON integrity under concurrent writes are all now real, passing, automated tests.
- **REAL FINDING (not fixed, deliberately — an executable remediation contract instead)**: the real release-gate restart wrapper (`nwr_release_gate_smoke.ps1`) does **not** actually guard against the exact stale-process-reuse failure mode the K/DST-composition pass stumbled into live (Part 1 §2.17's cited LEDGER.md section) — it can still accept a `200` from an old, already-running process without checking PID or challenging `/startup-proof`. `test_restart_race_rejects_stale_listener_instead_of_trusting_its_200` (the gauntlet's own entry-point logic) PASSES, proving the underlying identity-verification primitive works; `test_release_gate_restart_readiness_is_bound_to_the_launched_process` is pinned `XFAIL` specifically because the release-gate wrapper itself doesn't yet call that primitive — a precise, scoped, not-yet-applied fix, not a vague gap.
- **CURRENT IMPLEMENTATION**: Request-level failure handling (Part 1 §3.5/§3.8) remains real and tested, unchanged. Process-level reliability now has a real, repeatable, automated suite proving cold start, concurrent-request safety, and profile-pointer write-safety, plus one precisely-scoped, still-open gap (the release-gate wrapper's own restart-identity check) with a failing canary test that will flip green the moment it's fixed.
- **TEST COVERAGE**: `tests/test_reliability_gauntlet.py` (8 tests: 6 real passes, 2 intentional xfail canaries).
- **LIVE PROOF**: Independently re-run by the coordinating session this pass — identical 6 passed/2 xfailed result; live dev servers (ports 18741/18742/1421/1422) confirmed untouched by the gauntlet (it uses its own OS-assigned temporary ports).
- **FINAL STATUS**: `IMPLEMENTED_AND_TEST_VERIFIED` — cold start, concurrent-request safety, and profile-pointer integrity are now real, verified product properties, proven by a real automated suite; the one remaining limitation (the release-gate wrapper's own restart-identity gap) is precisely scoped, has a failing canary test already written, and is not yet fixed, so this is not re-labeled `OWNER_ACTION_REQUIRED` outright — the gauntlet itself is the real, delivered capability this topic asked for.
- **REMAINING ACTION**: Wire `/startup-proof` + launched-process-PID validation into `nwr_release_gate_smoke.ps1`'s own restart-readiness check so `test_release_gate_restart_readiness_is_bound_to_the_launched_process` flips from `XFAIL` to passing. A real, scoped, low-risk follow-up — not required to block current supervised daily use (every restart this entire cycle was performed by an attentive operator checking PIDs manually), but required before unattended automated restarts could be trusted.

---

## Combined Summary — Part 1 + Part 2

**Part 1 row count** (from Part 1's own "Master Requirement Ledger — Part 1 created" entry in `LEDGER.md` and this document's own count of Sections 1-6): **48 dispositioned rows** — Section 1 (Dynasty): 16. Section 2 (Redraft): 17. Section 3 (Data/Trust): 8. Section 4 (Official Rank/My Rank): 2. Section 5 (ESPN/Flaim): 1. Section 6 (four backend-API test failures): 4.

Part 1 disposition breakdown (counted directly from Part 1's own rows, Sections 1-6):

| Disposition | Part 1 |
|---|---|
| `IMPLEMENTED_AND_LIVE_VERIFIED` | 32 |
| `IMPLEMENTED_AND_TEST_VERIFIED` | 7 |
| `ALREADY_IMPLEMENTED` | 4 |
| `SUPERSEDED_BY_NEWER_OWNER_DIRECTION` | 0 |
| `INTENTIONALLY_BLOCKED_WITH_CURRENT_REASON` | 1 |
| `OWNER_ACTION_REQUIRED` | 2 |
| `NOT_RELEVANT_TO_CURRENT_PRODUCT` | 2 |
| **Total** | **48** |

**Part 2 row count**: the owner's 27 named topics, dispositioned as **31 individual rows** — three topics (7.11, 7.12, 7.18) were each split into lettered sub-rows (7.11a/b, 7.12a/b/c, 7.18a/b) because a single disposition value could not honestly cover the whole topic (e.g. 7.11's Dynasty half and Redraft half have genuinely different, correct answers). Every other topic is exactly one row. This mirrors Part 1's own practice of splitting a combined topic into dedicated rows (e.g. 1.15/1.16) rather than forcing two different real answers into one disposition value.

Part 2 disposition breakdown (counted directly from the 31 rows above):

| Disposition | Part 2 | Rows |
|---|---|---|
| `IMPLEMENTED_AND_LIVE_VERIFIED` | 9 | 7.1, 7.5, 7.6, 7.7, 7.8, 7.13, 7.18a, 7.18b, 7.23 |
| `IMPLEMENTED_AND_TEST_VERIFIED` | 9 | 7.12a, 7.14, 7.15, 7.16, 7.19, 7.20, 7.25, 7.26, 7.27 |
| `ALREADY_IMPLEMENTED` | 8 | 7.2, 7.3, 7.4, 7.10, 7.11a, 7.12c, 7.17, 7.24 |
| `SUPERSEDED_BY_NEWER_OWNER_DIRECTION` | 0 | — |
| `INTENTIONALLY_BLOCKED_WITH_CURRENT_REASON` | 1 | 7.21 |
| `OWNER_ACTION_REQUIRED` | 3 | 7.9, 7.12b, 7.22 |
| `NOT_RELEVANT_TO_CURRENT_PRODUCT` | 1 | 7.11b |
| **Total** | **31** | |

**Grand total across both parts**: 48 (Part 1) + 31 (Part 2) = **79 dispositioned rows**.

| Disposition | Part 1 | Part 2 | Combined |
|---|---|---|---|
| `IMPLEMENTED_AND_LIVE_VERIFIED` | 32 | 9 | **41** |
| `IMPLEMENTED_AND_TEST_VERIFIED` | 7 | 9 | **16** |
| `ALREADY_IMPLEMENTED` | 4 | 8 | **12** |
| `SUPERSEDED_BY_NEWER_OWNER_DIRECTION` | 0 | 0 | **0** |
| `INTENTIONALLY_BLOCKED_WITH_CURRENT_REASON` | 1 | 1 | **2** |
| `OWNER_ACTION_REQUIRED` | 2 | 3 | **5** |
| `NOT_RELEVANT_TO_CURRENT_PRODUCT` | 2 | 1 | **3** |
| **Total** | **48** | **31** | **79** |

Zero rows in either part use any disallowed placeholder status (`UNKNOWN`/`TODO`/`FOLLOW-UP`/`LATER`/`NOT INVESTIGATED`/`PROBABLY DONE`/`PARTIAL WITHOUT EXPLANATION`).

**Real gaps found while verifying this pass, none of which were fixed (pure documentation/verification, per this pass's own explicit hard boundary)**:
1. **A real, previously-undocumented orphaned-capability finding** (7.9): Dynasty's Personal Board backend schema validates `sell_high`/`buy_low`/`my_rank`/`my_tier`/`conviction` fields, but the HTTP route's own field whitelist, the facade's response serializer, and the frontend UI all independently exclude them — the capability is completely unreachable by the owner today, not merely unfinished in one layer.
2. ~~Dynasty Compare did not render `currentStatusOverride`~~ — **FIXED** after this pass (commit `768b0b42`, see Part 1 §1.3/§7.13's updated remaining action): `assetStatusNotices` now wired into `compare_dynasty_assets`, live-verified.
3. Redraft Compare has a distinct, architecturally-different version of the same disclosure gap — the status override is baked into values with zero on-card label or reason text (newly documented this pass; 7.13). Still open, deliberately out of scope (materially larger change).
4. ~~No dedicated reliability gauntlet existed~~ — **BUILT** after this pass (Codex F, `tests/test_reliability_gauntlet.py`, see updated §7.27): a real, automated, repeatable gauntlet now covers cold start, concurrent-request safety, and profile-pointer write integrity; one precisely-scoped remaining gap (the release-gate wrapper's own restart-identity check) has a failing canary test, not just a prose flag.
5. No real external-platform transaction-history surface and no real session-to-session change-detection layer exist anywhere in either app (7.21/7.22) — both honestly absent, neither fabricated nor partially faked.

No source code was modified by this Part 2 pass. All claims above were independently verified this pass via direct code inspection and/or fresh `curl` calls against the real running dev backends, per this document's own evidence-labeling convention.

<!-- END OF MASTER REQUIREMENT LEDGER (Parts 1 and 2 complete) -->
