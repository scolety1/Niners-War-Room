# Owner Dogfood Rebuild V1 -- LEDGER (Worker 4)

Branch: `upgrade/nwr-prospective-outcomes-v1-20260914`
Worktree: `C:\NWR\prospective-outcomes-v1`
Dispatch HEAD: `b5061437` (confirmed via `git log -1` at session start -- matched exactly; 4 commits ahead of origin, clean except the 2 known backup directories, per the dispatch's own framing).
Date: 2026-09-29.

Methodology labels used throughout, matching every prior cycle's vocabulary exactly: **INSPECTED CODE** (source read directly), **ACTUAL TEST RESULT** (a real pytest/vitest run, output observed), **LIVE OBSERVATION** (a real HTTP round trip against the real running dev backend, this session), **INFERENCE** (explicitly flagged reasoning, never presented as observed fact).

This worker covered the dispatch's items 1-3 (reconciliation, current-data freshness trace, Achane injury verification + override wiring). Items 4+ (K/DST trade-hole bug, Redraft/Dynasty profile separation, full IA rebuild, trade finder/counter generation, streamer horizons) are explicitly **NOT** covered here -- left for the next worker, see Open Issues.

---

## Item 1 -- Reconciliation

- **LIVE OBSERVATION**: `git log -1` confirmed HEAD `b50614377350b77be4d6f11218021efa5b42347d`, matching the dispatch exactly. `git status` showed clean except the 2 documented backup directories.
- **LIVE OBSERVATION**: read `docs/codex/trust_hardening_20260926/LEDGER.md` in full (319 lines, 3 prior workers) before starting any investigation, per the dispatch's explicit instruction not to re-investigate what's already documented.
- **LIVE OBSERVATION**: all 4 dev processes identity-verified via `Get-CimInstance Win32_Process` (`CommandLine` contains `C:\NWR\prospective-outcomes-v1`) before touching anything: redraft backend PID 35196 (port 18742), redraft frontend PID 25852 (port 1422), dynasty backend PID 39104 (port 18741), dynasty frontend PID 37864 (port 1421). Redraft's active profile was already **Fantasy Gamers** (`941b99ade350410391b1b67c0890af79`) at session start -- matches the dispatch's stated preference; left unchanged. Dynasty's active league remained Las Vegas Enginerds throughout, unchanged.
- Both backend processes were later restarted twice this pass (once to load the initial override-wiring code, once more after a real scoping bug was found and fixed in the Trade Decision Lab annotation -- see Item 3). **Final, currently-running, identity-verified PIDs**: redraft backend **41576** (port 18742), dynasty backend **9184** (port 18741). Both frontends (25852 / port 1422, 37864 / port 1421) were never restarted -- no frontend build changes required a rebuild for this pass's live verification (frontend changes were confirmed via `npm run typecheck` + `vitest`, not a rendered browser session -- see Open Issues).

---

## Item 2 -- Current-data freshness trace

### The exact source of the alarming "Projections 2026-09-08" the owner saw

**INSPECTED CODE + LIVE OBSERVATION**: traced to `src/application/desktop_facade.py`'s `redraft_bootstrap()` (`status.sourceAsOf` / `status.freshness`, ~line 2358), rendered on the **Redraft Data Health page's own top hero** (`desktop/apps/redraft/src/pages.tsx`, `DataHealthPage`, the health-hero `<section>`). Before this fix it read, verbatim: `"2026-09-08 · Governed current-season projection snapshot"` -- a bare date with zero context.

**Confirmed precisely, not assumed**: this date is the **season-level ROS governed-model admission date** (`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/NWR_DATA_GOVERNANCE.json`: `approved_by: "Spencer Colety (owner, explicit chat authorization, 2026-09-08, ...)"`, `valid_until: "2026-10-08"`). This is the same "Freeze V7" 564-row veteran+rookie snapshot every prior cycle has referenced. **It is real, owner-approved, still valid (9 days of runway remaining as of today), and by design is NOT meant to refresh weekly** -- it only changes through a new owner-approved governance admission, exactly as the dispatch's own hypothesis predicted.

**Does the stale-looking date actually leak into weekly math, or is it a correctly-isolated season baseline?** Traced per-surface:

| Surface | Source / version | Does the 2026-09-08 season snapshot enter its math? | Verdict |
|---|---|---|---|
| **Redraft ROS Rankings** | Governed Freeze V7 snapshot, admitted 2026-09-08 | Yes -- by design, this IS the ROS authority; `projected_points`/`replacement_adjusted_value` are season totals, never games-remaining-adjusted (`redraft_2026_projection_model_service.py`'s per-game-rate * games construction, confirmed unchanged this pass). | Correct by design. Disclosure gap was the issue, not the mechanism (see below). |
| **Redraft Weekly Rankings / Start-Sit** | `get_weekly_projections()` (Sleeper, approved temporary/stopgap provider) -- a genuinely separate, live, week-scoped call, confirmed via `redraft_weekly_projections()`/`redraft_weekly_lineup()` in `desktop_facade.py` (~lines 3539-3650, 3658+). `weekly-shared.tsx`'s own `resolveWeekDisplay`/`ProviderStatusLine` already carry independent STALE/LIVE captions for this lane. | No -- the September 8 season snapshot is never substituted for a missing weekly number; a stale/missing weekly projection is disclosed as `STALE`/`UNAVAILABLE` on its own terms, never silently backfilled from the season total. | TRUSTED_WITH_DISCLOSED_LIMITATION (pre-existing; reconfirmed this pass, not re-built). |
| **Waivers (THIS_WEEK mode)** | Same `get_weekly_projections()` live weekly call, confirmed in `redraft_waivers()` (~line 4369, `weekly_health_dict` in the `data_health` payload; ~line 4724 explicit `"This-week weekly projections are STALE..."` string). REST_OF_SEASON mode intentionally uses the season snapshot (`rosProjectionSha256` in `waivers_data_versions`, ~line 4576). | No leak -- THIS_WEEK is a real live weekly simulation; REST_OF_SEASON is explicitly, separately labeled by mode. | TRUSTED_WITH_DISCLOSED_LIMITATION (pre-existing; reconfirmed). |
| **Streamers / K-DST** | `fantasypros_kdst_consensus_service.py` (external, live, or honestly `UNAVAILABLE` if `NWR_FANTASYPROS_API_KEY` is unconfigured) | No -- entirely separate from the season projection snapshot. | Unchanged from Worker 1's PARTIAL finding (key config not re-tested this pass; out of this dispatch's scope). |
| **Trade Analysis / Finder / Package Search (Redraft)** | Season ROS authority (`redraft_trade_analysis_service.py`, shared by all 3 lanes) | Yes, by design -- trade evaluation is inherently a season-level, not single-week, decision. The lane's own `dataHealth:null`/`data_versions:{}` disclosure gap (Worker 2's open item #1) is STILL genuinely unfixed -- confirmed present this pass, not touched (out of this dispatch's scope; correctly left for a dedicated future pass). | Correct by design for using season data; the **disclosure** of that fact is still the pre-existing, documented gap, not newly found or newly fixed this pass. |
| **Dynasty Rankings ("Finished V1")** | `docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/rebuilt_full_player_board_value_review_rows.csv` -- a real, frozen, deterministically-rebuilt board. **New finding this pass**: the CSV's own `score_as_of_date` column reads `"2026-pre-draft"` for all 240 real rows -- i.e. the Finished V1 scores were computed BEFORE this season's games were even played, and until this pass, **nothing in the Dynasty UI ever surfaced this fact anywhere.** The only dated context shown anywhere was the separate, optional DynastyProcess market-evidence date. | The frozen rank/score itself never silently "updates" from anything live -- correct, deterministic, by design. But an owner had no way to learn the board predates the season, a materially more alarming gap than Redraft's (which at least showed *a* date). | **Real disclosure gap, found and fixed this pass** -- see below. |
| **Dynasty Trade Lab** | `trade_decision_assistant_service.py` -> `owner_asset_evidence_service.py` -> `market_baseline_service.py` (DynastyProcess), confirmed by Worker 2 as architecturally separate from the legacy, dead `trade_roster_negotiation_service.py`. **LIVE OBSERVATION, this session**: `GET /api/v1/bootstrap` (dynasty) returns `marketFreshness: {"sourceAsOf": "2026-07-17", "status": "Yellow Stale", "message": "Market evidence is 74 days old (upstream date 2026-07-17); display-only context remains available but is not current."}` -- **reconfirmed live, still honest**, message dynamically recomputed to 74 days (was 73 at Worker 2/3's own check 2-3 days ago) -- exactly the expected, correct, already-fixed behavior; no regression. | N/A -- reconfirmation only, per dispatch instruction ("already correctly disclosed... this is EXPECTED and CORRECT behavior, not a bug, just re-confirm"). | **Reconfirmed correct, unchanged.** |

### Fixes made (disclosure/labeling only -- no data re-fetched, no formula touched)

1. **Redraft Data Health hero now explains the admission-date/weekly-refresh distinction.** New function `resolveGovernedModelCadenceCaption(sourceAsOf, scheduledRefresh)` in `desktop/apps/redraft/src/weekly-shared.tsx`, wired into `DataHealthPage`'s hero in `desktop/apps/redraft/src/pages.tsx`. Surfaces the real `status.scheduledRefresh` field (`"Off — owner approval required"`) that the backend has computed for weeks (`desktop_facade.py:redraft_bootstrap`) but that **no frontend surface had ever rendered before this fix** (confirmed by a full-repo search: only test fixtures referenced the field). The hero now reads (paraphrased): *"This is the season-level governed model's admission date, not a live weekly refresh (scheduled refresh: Off — owner approval required — by design...). Start/Sit, Waivers (This Week), and Streamers layer separate, live, week-scoped data on top of this baseline."*
2. **Dynasty bootstrap now discloses the Finished V1 board's real scoring basis.** New notice in `dynasty_bootstrap()` (`desktop_facade.py`): *"Finished V1 is a frozen base model, not a live weekly ranking"* -- sourced from the real `score_as_of_date` CSV column (`"2026-pre-draft"`), never a fabricated or guessed date. Renders on the Dynasty Home page (`desktop/apps/dynasty/src/pages/home.tsx` already maps `data.notices`).

Neither fix touches `marginal_roster_utility_v2`, `governed_asset_registry_service.py`, the Dynasty base board CSV, or any Redraft projection value. Both are pure string/label additions sourced from data the backend already had.

---

## Item 3 -- Achane injury verification + override wiring

### Real injury verification (WebSearch, this session, current sources)

**CONFIRMED, real, current**: De'Von Achane (Miami Dolphins RB) suffered a torn ACL on a non-contact play in the Week 3 loss to the Kansas City Chiefs (Sunday 2026-09-27), ruled out, and the Dolphins placed him on Reserve/Injured on Monday 2026-09-28 -- season-ending for 2026. Sources (all real, dated 2026-09-28/29 articles, not assumption): [ESPN](https://www.espn.com/nfl/story/_/id/50052064/sources-dolphins-rb-devon-achane-suffered-torn-acl-vs-chiefs), [NFL.com](https://www.nfl.com/news/dolphins-rb-devon-achane-miss-2026-season-acl-tear), [CBS Sports](https://www.cbssports.com/nfl/news/devon-achane-knee-injury-dolphins-chiefs-2026/), [NBC Sports](https://www.nbcsports.com/fantasy/football/player-news/2026-09-28/devon-achane-suffered-torn-acl-in-loss-to-chiefs). The owner's recollection was **correct** -- verified independently, not assumed.

### Override entry added

`config/nwr_verified_current_player_status_overrides_v1.json` -- new entry, added via the real, validated `add_verified_status_override()` intake function (not a hand-edit), matching the existing file's exact convention:

```json
{
  "player_id": "00-0039040",
  "player_name": "De'Von Achane",
  "kind": "SEASON_OUT",
  "effective_date": "2026-09-27",
  "verified_at_utc": "2026-09-29T00:00:00Z",
  "reason": "Torn ACL sustained on a non-contact first-quarter run in the Week 3 loss to the Kansas City Chiefs (2026-09-27); Dolphins placed him on Reserve/Injured (2026-09-28), ruled out for the remainder of the 2026 season.",
  "sources": [4 real dated URLs, see file]
}
```

`player_id` (`00-0039040`) confirmed as Achane's real nflverse gsis ID by direct lookup in `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv`.

### Redraft propagation -- already correctly wired (reconfirmed, no code change needed)

**LIVE OBSERVATION, no backend restart required** (`load_status_overrides` reads the config file fresh on every call, no caching): `GET /api/v1/bootstrap` (Fantasy Gamers) immediately showed Achane's real row with `replacementAdjustedValue: 0.0`, `starterGap: 0.0`, sunk to `overallRank: 129` -- while `projectedPoints: 322.8` (the ORIGINAL, unmodified projection) was preserved unchanged for provenance, exactly as `current_player_status_overrides_service.py`'s own contract promises. This confirms the existing Redraft mechanism (already used for Jayden Higgins/Elijah Mitchell/Kayshon Boutte) worked correctly for a brand-new real event with zero code changes.

### Dynasty propagation -- REAL, CONFIRMED ROOT-CAUSE BUG, now fixed

**Confirmed by exhaustive grep before touching anything**: every call site of `load_status_overrides`/`apply_status_overrides_to_ranking` in `desktop_facade.py` was prefixed `redraft_*` (`redraft_bootstrap`, `redraft_weekly_lineup`, `redraft_waivers`, `redraft_trade_analysis`, `redraft_trade_finder`, `redraft_trade_package_search`, `_redraft_ranking_for_profile`, `list_player_status_overrides`) -- **zero occurrences in any `dynasty_*` function, `owner_asset_evidence_service.py`, or `governed_asset_registry_service.py`.** Confirmed live, before any fix: `GET /api/v1/bootstrap` (dynasty) showed **De'Von Achane ranked #9 overall in the "Finished V1" board, on the owner's own roster (`isMyTeam: true`, `rosterSlotStatus: "starter"`), with zero injury disclosure anywhere in the payload.** This is exactly the real trust problem the dispatch anticipated, now proven, not merely suspected.

**Root cause of why Dynasty never wired this in**: Dynasty's internal asset IDs (`current:9226` for Achane) are in a completely different ID space than the override file's nflverse gsis IDs (`00-0039040`) -- no live crosswalk between the two ID spaces exists anywhere in this codebase today (confirmed: `nflverse_identity_service.py` is a batch validation/report tool, not a live per-request lookup; `live_player_intelligence_shadow_v1_service.py` is explicitly shadow-only, zero call sites from production). This is very likely the actual reason Dynasty was never wired up in the first place, not an oversight alone.

**Fix implemented (display-only, additive, hard-boundary-compliant)**:

1. `src/services/owner_asset_evidence_service.py::compose_owner_asset_evidence` gained an optional `status_overrides: Sequence[StatusOverride] = ()` parameter (backward-compatible default; the one production call site and all existing tests pass zero or unaffected). Matches by **normalized player name** (`normalize_identity_name`, an existing, already-used-elsewhere-in-this-codebase helper -- lowercase, strips Jr/Sr/II/III/IV suffixes, strips non-alphanumerics), since no numeric-ID crosswalk exists. Adds one new field, `current_status_override` (a dict or `None`) -- **never touches `nwr_dynasty_score`, `dynasty_rank`, `market_*`, or any other governed value field.**
2. `src/services/owner_mode_view_service.py::owner_rankings_frame` passes the new field through into its output frame (new `"current_status_override"` column, never read by `sort_values`).
3. `src/application/desktop_facade.py`: wired `load_status_overrides(self.repo_root)` into the ONE real call site of `compose_owner_asset_evidence` (`_build_owner_snapshot`, the Dynasty choke point equivalent of Redraft's `_asset_pool`); surfaced the new field (as camelCase `currentStatusOverride`, via a new `_status_override_json` helper) in **`_dynasty_ranking_payload`** (Dynasty Rankings), **`_asset_option`** (Asset Explorer / trade selection search), and **`_player_detail_payload`** (single-asset detail page) -- all three read from the same underlying `snapshot.evidence.rows`/`by_id`, so this is one real choke point, not three separate patches.
4. **Dynasty Trade Decision Lab**: `_trade_context()` now also carries `current_status_override` through its existing display-annotation pattern (alongside the pre-existing `redraft_available`/`research_outlook_3y` context fields it already attaches post-valuation). `evaluate_dynasty_trade()` builds a new top-level `assetStatusNotices` array from this, **scoped strictly to the trade's own `give_ids`/`receive_ids`** -- never read by `evaluate_trade_decision()`'s own valuation dimensions, never changes `recommendation`/`preferredSide`.
5. `desktop/packages/contracts/src/index.ts`: new `DynastyCurrentStatusOverride` interface; optional `currentStatusOverride` field added to `DynastyRanking`, `AssetOption`, `PlayerDetail`; optional `assetStatusNotices` added to `TradeDecision`.
6. `desktop/apps/dynasty/src/pages/rankings.tsx`: a new `CurrentStatusBadge` renders next to the player name on the Dynasty Rankings table (e.g. "Season out") whenever `currentStatusOverride` is present -- purely additive, never affects row order or the `nwrScore`/`rank` columns.

**A real bug this worker found and fixed BEFORE committing** (caught via live testing, not assumed correct): the first version of the `assetStatusNotices` builder iterated `lookup.values()` -- the WHOLE trade-item registry universe `_trade_context()` builds once and shares across every possible trade -- instead of only the assets actually in the current trade. **Reproduced live**: evaluating a trade of only Achane-for-Nacua returned THREE notices, including Jayden Higgins and Kayshon Boutte, neither of whom was anywhere in that trade. Fixed by scoping strictly to `(*give_ids, *receive_ids)` via `key_for_id`. Re-verified live: the same trade now returns exactly one notice (Achane); a trade of two healthy, un-overridden players correctly omits the `assetStatusNotices` key entirely (never an empty-but-present array).

### Live propagation verification (this session, after the fix and after a full backend restart)

| Surface | LIVE result |
|---|---|
| Dynasty Rankings (`GET /api/v1/bootstrap`, `data.rankings`) | Achane's row: `"currentStatusOverride": {"kind": "SEASON_OUT", "reason": "...", "sources": [...]}`; `rank`/`nwrScore` unchanged (9 / 61.3322) -- disclosure without reordering, since the dispatch's hard boundary forbids touching the governed value. |
| Asset Options (same response, `data.assetOptions`) | Same override object present for `current:9226`. |
| Dynasty Asset detail (`GET /api/v1/dynasty/assets/current:9226`) | Same override object present in the single-player payload. |
| Dynasty Trade Decision Lab (`POST /api/v1/dynasty/trades/evaluate`, give Achane for Puka Nacua) | `assetStatusNotices: [{"assetId": "current:9226", "playerName": "De'Von Achane", "kind": "SEASON_OUT", ...}]` -- exactly one entry, correctly scoped. A control trade with two healthy players correctly has no `assetStatusNotices` key at all. |
| A healthy player (Puka Nacua, `current:9493`) in all of the above | `currentStatusOverride: null` everywhere, confirmed live -- absence is explicit, never a fabricated "healthy" claim. |

### Surfaces that do NOT yet consume the override layer

- **Dynasty Compare** (`compare_dynasty_assets`) and **Rookie Review** were not wired this pass -- both are lower-priority than Rankings/Trade Lab/Asset Detail for this dispatch's P0 framing, and adding them is a small, mechanical follow-up now that the choke point exists (they already read from `snapshot.evidence.by_id`/`.rows`, so the field is already ON their rows -- they just don't render it yet on the frontend). Flagged for the next worker.
- **Dynasty Waivers/FAAB/Weekly surfaces**: Dynasty does not have a redraft-style weekly optimizer in this codebase (dynasty is long-term-value-oriented, not a weekly lineup tool) -- not applicable.

---

## Base-model-vs-current disclosure (the broader "Finished V1" question)

**Finding**: "Finished V1" was being presented with an authoritative-sounding name and description ("The accepted long-term board...") but, before this pass, **carried no visible date of its own anywhere in the UI** -- only the separate, optional DynastyProcess market date was shown, which an owner could easily (and did) confuse for "how current is this board." The real underlying CSV's own `score_as_of_date` column (`"2026-pre-draft"`, uniform across all 240 rows) already existed as ground truth but was never surfaced.

**Fix**: the new Dynasty bootstrap notice (Item 2, fix #2 above) directly states the board is a frozen base model dated pre-season, explains that real current-status corrections are layered on top and shown per player, and that the underlying rank/score only changes via a new owner-approved governance admission. This is the "small, safe, non-model-mutating fix" the dispatch asked for -- not a new "current value layer" model, just honest labeling of the existing one plus wiring the existing override layer (which already WAS the intended "current value" mechanism) into the surfaces that had never consumed it.

---

## Tests

**ACTUAL TEST RESULT**, backend, combined run (17 files, includes every file touched or closely related, plus the new test file):
```
tests/test_current_player_status_overrides_service.py
tests/test_desktop_application_api.py
tests/test_redraft_trade_analysis_service.py
tests/test_roster_decision_readiness_service.py
tests/test_trade_package_search_service.py
tests/test_trade_package_search_facade_wiring.py
tests/test_waiver_engine_service.py
tests/test_trade_finder_service.py
tests/test_weekly_lineup_optimizer_service.py
tests/test_redraft_identity_boundary_opponent_and_trade_finder.py
tests/test_market_baseline_service.py
tests/test_market_staleness_and_missing_value_v1.py
tests/test_nwr_live_use_repair_v2.py
tests/test_trade_decision_assistant_v1.py
tests/test_dogfood_rebuild_v1_dynasty_status_override.py   <- NEW, 8 tests, all pass
tests/test_owner_mode_view_service.py
tests/test_dynasty_league_import_facade_wiring.py
```
Result: **261 passed, 4 failed** -- confirmed by name to be the **exact same 4 pre-existing failures** every prior cycle in this saga has documented: `test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_component_dependency`. None are new; none are in a file this pass touched.

`tests/test_draft_day_trade_lab_service.py` (12 pre-existing failures, `AppTest script not found` -- a Streamlit `AppTest` relative-path resolution issue, unrelated to this pass) confirmed **identical before and after** via a clean `git stash` comparison -- a genuine, separate, pre-existing environmental issue (flagged for the next worker; likely related to the recent "resolve Streamlit AppTest paths from repo root" work on the sibling `Niners-War-Room` repo not yet needed/applied here).

**Ruff**: `python -m ruff check` on the 3 touched Python files shows 119 findings both **before and after** this pass's changes (verified via `git stash`/re-run) -- confirmed pre-existing, zero new findings introduced.

**Frontend**: `npm run typecheck` (both dynasty+redraft) clean. Full `vitest run`: **525 passed (31 files)**, including the new/updated `resolveGovernedModelCadenceCaption` tests in `weekly-shared.test.ts`.

---

## Live re-verification of both real Sleeper leagues (post-fix, per the SAFETY requirement)

- **Fantasy Gamers (Redraft)**: `GET /api/v1/bootstrap` returns the correct active profile; `POST /api/v1/redraft/waivers` (REST_OF_SEASON) returns `200`, zero errors, real candidates -- confirmed intact after all changes.
- **Las Vegas Enginerds (Dynasty)**: `GET /api/v1/bootstrap` returns `200`, 240 real ranking rows, correct league identity (`leagueId: 1344772855908290560`, `myRosterId: 7`) -- confirmed intact. `POST /api/v1/dynasty/trades/evaluate` confirmed working for both an overridden-asset trade and a healthy-only control trade.

No Sleeper/ESPN write endpoint was ever called. KHA/403N18th were not touched. No Flaim/MCP access attempted.

---

## Files changed

- `config/nwr_verified_current_player_status_overrides_v1.json` -- new De'Von Achane SEASON_OUT entry (real, sourced, added via the validated intake function).
- `src/services/owner_asset_evidence_service.py` -- `status_overrides` parameter + `current_status_override` field on the Dynasty evidence choke point; new `_status_override_payload` helper.
- `src/services/owner_mode_view_service.py` -- `owner_rankings_frame` passthrough of the new field.
- `src/application/desktop_facade.py` -- wired `load_status_overrides` into `_build_owner_snapshot`; surfaced `currentStatusOverride`/`assetStatusNotices` in `_dynasty_ranking_payload`, `_asset_option`, `_player_detail_payload`, `_trade_context`, `evaluate_dynasty_trade`; new `_status_override_json` helper; new `board_as_of_label`-driven "Finished V1 is a frozen base model" notice in `dynasty_bootstrap`.
- `desktop/packages/contracts/src/index.ts` -- new `DynastyCurrentStatusOverride` interface; optional fields on `DynastyRanking`/`AssetOption`/`PlayerDetail`/`TradeDecision`.
- `desktop/apps/dynasty/src/pages/rankings.tsx` -- new `CurrentStatusBadge` on the Rankings table.
- `desktop/apps/redraft/src/weekly-shared.tsx` -- new `resolveGovernedModelCadenceCaption`.
- `desktop/apps/redraft/src/weekly-shared.test.ts` -- new test block for the above.
- `desktop/apps/redraft/src/pages.tsx` -- wired the new caption into the Data Health hero.
- `tests/test_dogfood_rebuild_v1_dynasty_status_override.py` -- new file, 8 tests.
- `docs/codex/dogfood_rebuild_20260929/LEDGER.md` -- this file.

No governed valuation model touched (`marginal_roster_utility_v2`, `governed_asset_registry_service.py`'s value formula, the Dynasty base board CSV, the Redraft projection snapshot -- all confirmed untouched by `git diff`). No Sleeper/ESPN writes. No Flaim/MCP access. KHA/403N18th profile identity fields never touched.

---

## Open issues for the next worker

1. **Dynasty Compare and Rookie Review pages do not yet render `currentStatusOverride`** even though the field already exists on their underlying rows (they read the same `snapshot.evidence.by_id`/`.rows`) -- a small, mechanical frontend-only follow-up.
2. **Name-based matching is a disclosed, deliberate substitute for a real ID crosswalk**, not a claim of certainty. If two distinctly-different real players ever share an identical normalized name (extremely rare in practice but not impossible), the override could misattribute. A real Sleeper-numeric-ID <-> gsis-ID crosswalk (likely via nflverse's own `ff_playerids` release, referenced by `nflverse_identity_service.py`'s existing `MATCH_METHOD_ORDER`) would close this properly; out of scope for this pass's size.
3. **The Redraft trade lane's `dataHealth:null`/`data_versions:{}` gap** (Worker 2's open item, reconfirmed still present this pass, not touched) remains a good candidate for a dedicated future pass.
4. **`tests/test_draft_day_trade_lab_service.py`'s 12 `AppTest script not found` failures** are a real, pre-existing, reproducible environmental issue in THIS worktree (confirmed via clean-HEAD `git stash`) -- worth checking whether the sibling `Niners-War-Room` repo's recent "resolve Streamlit AppTest paths from repo root" fix (commit `157b9601`, per this session's own git log) needs porting here.
5. **No browser-based/rendered UI confirmation of this pass's frontend changes** -- `npm run typecheck` and `vitest` both pass, and the new caption/badge logic is unit-tested, but nobody visually confirmed the Data Health hero text or the Dynasty Rankings badge in a real rendered browser session this pass (consistent with prior cycles' own disclosed limitation for similar changes).
6. **Item 4+ of the owner's 19-item work sequence** (K/DST trade-hole bug, Redraft/Dynasty profile separation, full IA rebuild for both apps, trade finder/counter generation, streamer horizons) is **entirely untouched by this worker** -- next in the queue per the dispatch.
7. All open issues from `docs/codex/trust_hardening_20260926/LEDGER.md` not explicitly superseded above still stand (73+-day-old DynastyProcess snapshot -- now 74 days, still an owner-actionable data-refresh task not a code fix; `NWR_FANTASYPROS_API_KEY` unconfigured-in-dev-worktree status not re-checked this pass; Redraft governed model's `2026-10-08` approval expiry is now **9 days away** -- worth flagging to the owner directly and soon).

---

# Worker 5 -- items 4-5 (K/DST trade-hole bug, Redraft/Dynasty profile separation)

Dispatch HEAD: `2512e06f` (Worker 4's commit, confirmed via `git log -1` at session start; clean except the 2 known backup directories). Final HEAD after this pass: see commit immediately following this ledger update.

## Item 4 -- K/DST TRADE-HOLE BUG (P0 correctness bug) -- FIXED

**LIVE OBSERVATION (real Fantasy Gamers league, before any fix)**: `GET /api/v1/redraft/my-roster` showed the owner's real roster with a real kicker (Ka'imi Fairbairn, sleeper id `3451`) and a real team defense (CIN) both marked `identityStatus: "UNMATCHED_IDENTITY"`, `canonicalPlayerId: null`. A real trade (`POST /api/v1/redraft/trade-analysis`, give J.K. Dobbins for free-agent Kenny Gainwell -- neither is K/DST) returned `starterHolesBefore: ["K 0/1", "DST 0/1"]` and `starterHolesAfter: ["K 0/1", "DST 0/1"]`, even though the owner's real Fantasy Gamers roster (`local_exports/redraft_v1/profiles/941b99ade350410391b1b67c0890af79.json`) configures `k: 1, dst: 1` and both slots are genuinely filled on the real Sleeper roster. Confirmed **unconditional** -- appears for every trade regardless of shape, not just ones touching K/DST, because the roster used for BEFORE was already missing K/DST before any trade is even constructed.

**INSPECTED CODE, exact root cause**: `desktop_facade.py::redraft_trade_analysis` builds `roster_before_ids` from `resolve_roster_canonical_ids()`'s (`waiver_engine_service.py`) `canonical_player_ids`. That resolver's own `ranking_by_identity` lookup table is built ONLY from `ranking_rows` -- i.e. NWR's governed ranking, which structurally never contains K or DST rows (`_asset_pool`'s own comment: "K/DST are always manual, NWR has no model for them"). So a K or DST roster occupant, no matter how cleanly its name/position/team resolves in the Sleeper player catalog, can NEVER match anything in `ranking_by_identity` and always lands in `unmatched_sleeper_player_ids` -- silently dropped from `canonical_player_ids`. This is a **deliberate, disclosed, correct** scope boundary for the WAIVER engine (K/DST have no ranked value to waiver-rank -- see `_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS`'s own comment, "not a bug"), but `redraft_trade_analysis` reuses the exact same resolver for the OWNER'S FULL ROSTER to feed `evaluate_trade`'s `roster_before_ids` -- and `_roster_players()`/`_select_starting_lineup()` (`shadow_numeric_authorities_service.py`) treat a player absent from that list as an EMPTY slot, not an unvalued-but-filled one. Not a "DST vs DEF" string bug (that normalization already works correctly inside the identity matcher via `_sleeper_position`) -- a genuine cross-tool reuse mismatch: a resolver whose "drop K/DST" behavior is correct for waivers is silently wrong for trade-composition reporting.

**Reproduced live via a controlled before/after (`git stash`/restart/re-test/`git stash pop`/restart)**: confirmed the exact bug present pre-fix (`starterHolesBefore`/`After` both `["K 0/1", "DST 0/1"]`) and absent post-fix (`[]`/`[]`), same trade, same running process family, same real Fantasy Gamers roster.

**Fix** (`src/services/waiver_engine_service.py`, new function `resolve_full_roster_with_unranked_occupants`; wired into `desktop_facade.py::redraft_trade_analysis` only): extends the resolver's already-matched canonical ids with one additional id per real, catalog-resolvable K/DST occupant (`OUT_OF_RANKED_MODEL_SCOPE`, per the pre-existing `describe_unmatched_roster_players`) -- reusing an existing manual K/DST asset's own id when this occupant's name/position/team identity already matches one loaded for the profile (so a real manual valuation is used, never a duplicate entry), or else synthesizing one new "NOT MODELED" pool row (identical shape to the manual K/DST rows `_asset_pool` already builds) when no manual data exists yet (today's real state for Fantasy Gamers -- zero manual K/DST assets loaded). No new identity system: reuses the same `_identity()`/`_sleeper_position()` matcher every other K/DST lookup in this codebase already uses. Genuinely `UNKNOWN_TO_CATALOG` occupants are left exactly as unmatched as before (verified by a dedicated test) -- this only recovers real, resolvable roster occupants that are merely outside NWR's ranked model, never masks a genuine identity gap. `gives`/`receives` identity resolution is completely unchanged -- a trade actually involving an unresolved player still fails loudly via `TRADE_ANALYSIS_IDENTITY_UNRESOLVED`.

**Scope note for the next worker**: Trade Finder (`redraft_trade_finder`) and Trade Package Search both build their own `own_resolved` the same way (`resolve_roster_canonical_ids` over the owner's full roster) and may exhibit an analogous composition gap if their downstream composition/starter-hole reporting (if any) also drops K/DST -- **not verified this pass** (out of the dispatch's explicit "Trade Analysis" scope); worth a quick live check with the same method if the owner reports a similar symptom there.

**Tests** (real regression coverage, all passing): `tests/test_waiver_engine_service.py` -- 3 new unit tests for `resolve_full_roster_with_unranked_occupants` (synthesizes NOT-MODELED rows when no manual data exists; reuses an existing manual asset's id instead of duplicating; leaves genuinely-unknown non-K/DST ids untouched). `tests/test_redraft_trade_analysis_service.py` -- 1 new end-to-end test (`test_real_kdst_roster_occupants_are_reported_filled_not_holes_before_and_after_trade`) building a realistic roster with a real kicker + real team defense and proving `evaluate_trade`'s `starter_holes_before`/`starter_holes_after` are both `()` for a trade that swaps two skill-position players.

## Item 5 -- REDRAFT / DYNASTY PROFILE SEPARATION (P0 product-confusion bug) -- FIXED

**LIVE OBSERVATION, before fix**: `GET /api/v1/bootstrap` (redraft) `data.profiles` listed all 6 real profile-store entries, including "Las Vegas Enginerds" (the owner's real DYNASTY league) and 2 fixture profiles ("10-team 1QB Standard", "Isolation Check Local").

**INSPECTED CODE, confirmed the profile stores are fully separate**: Dynasty owns Las Vegas Enginerds end-to-end via its own, completely independent store at `local_exports/dynasty_v1/league_profiles/1344772855908290560.json` (keyed by Sleeper league id) -- the Redraft-side profile at `local_exports/redraft_v1/profiles/6687d2b3aa21450ea0fc9e1792d461ff.json` is a real, harmless leftover import Dynasty never reads. Hiding it from Redraft's selector therefore cannot affect Dynasty in any way (confirmed live below).

**Mechanism chosen**: a new, presentation-only field on `LeagueProfile` (`redraft_engine_v1_service.py`): `hidden_from_redraft_selector: bool = False` (parsed from the document with the same default, so every existing profile document written before this fix is unaffected and defaults to visible). A new function `selectable_profiles()` filters a profile list by this flag; wired into `desktop_facade.py::redraft_bootstrap` at the exact point `list_profiles()` builds the `profiles` list serialized into the bootstrap payload (the ONLY place the frontend selector's data comes from -- confirmed via `desktop/apps/redraft/src/leagues.tsx`'s `data.profiles.map(...)`). `list_profiles()` itself, profile activation/editing/duplication/archival, `reconcile_sleeper_profile_identities`, and the Sleeper identity-boundary service are all completely untouched -- they keep seeing every real profile exactly as before (verified by test: a hidden profile can still be `set_active_profile`'d and `load_profile`'d normally).

**Data change (not a code/schema change -- reversible, no deletion)**: set `hidden_from_redraft_selector: true` on 3 real, already-existing local profile documents via the real `save_profile()` function (never a hand-edit): `6687d2b3aa21450ea0fc9e1792d461ff.json` (Las Vegas Enginerds), `9d67837e147e4aae87dbe17762ae3638.json` (Isolation Check Local), `c5c77f621138494383af7fc11cc41ef4.json` (10-team 1QB Standard). Left unflagged (still visible): Fantasy Gamers, 403 N 18th and friends, 2026 KHA High Stakes League -- all 3 real leagues. These profile JSON files live under `local_exports/` (gitignored local runtime state, same category as `active_profile.json`) -- not part of this commit's diff.

**Live verification, post-fix**: `GET /api/v1/bootstrap` (redraft, PID 37580, identity-verified) `data.profiles` now returns exactly `["2026 KHA High Stakes League", "403 N 18th and friends", "Fantasy Gamers"]` -- Las Vegas Enginerds and both fixtures are gone from the selector. Active profile remains Fantasy Gamers, unaffected. `GET /api/v1/bootstrap` (dynasty, PID 9184, identity-verified, never restarted) still returns `dynastyLeague.leagueName == "Las Vegas Enginerds"`, `leagueId == "1344772855908290560"`, `myRosterId == 7`, 240 real ranking rows, zero errors -- Dynasty's own Enginerds functionality is completely unaffected by the Redraft-side hide.

**Tests** (real regression coverage, all passing, `tests/test_redraft_engine_v1_service.py`): `test_selectable_profiles_hides_flagged_profiles_but_list_profiles_still_sees_them` (proves `list_profiles` sees all 3 real profiles including a hidden one, `selectable_profiles` shows only the unflagged one, and the hidden profile remains fully activatable/loadable -- presentation-only, not a capability restriction); `test_hidden_from_redraft_selector_defaults_false_for_every_existing_and_new_profile` (backward compatibility -- a profile document with the key entirely absent, simulating every profile written before this fix, still defaults to visible).

## Tests (combined, this pass)

**ACTUAL TEST RESULT**: `tests/test_redraft_trade_analysis_service.py`, `tests/test_waiver_engine_service.py`, `tests/test_redraft_engine_v1_service.py`, `tests/test_desktop_application_api.py`, `tests/test_desktop_http_api.py`, `tests/test_desktop_facade_architecture_wiring.py`, `tests/test_redraft_profile_practical_mode_toggle.py`, `tests/test_sleeper_redraft_owner_service.py`, `tests/test_redraft_identity_boundary_opponent_and_trade_finder.py`, `tests/test_trade_finder_service.py`, `tests/test_trade_package_search_service.py`, `tests/test_trade_package_search_facade_wiring.py`, `tests/test_redraft_waivers_starter_drop_exclusion_fix.py`, `tests/test_redraft_waivers_faab_context_fix.py`, `tests/test_redraft_waivers_position_eligibility_fix.py`, `tests/test_redraft_canonical_state_caller_conversions.py`, `tests/test_redraft_my_roster_canonical_state_conversion.py`.

Result: all pass except two **confirmed pre-existing** baselines, byte-identical before/after this pass's changes (verified via `git stash`/re-run comparison):
- `tests/test_desktop_application_api.py` -- exactly the same 4 failures every prior worker in this saga has documented: `test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_component_dependency`.
- `tests/test_redraft_engine_v1_service.py` -- 3 failed + 13 errors, all pre-existing in this worktree (confirmed via clean `git stash` comparison of just this file before touching it), unrelated to profile/K-DST logic -- appear to be a `MINIMUM_POSITION_DEPTHS`/fixture-depth gating issue in projection-snapshot test fixtures, not previously documented in this ledger chain; flagged for the next worker to note as a 3rd known baseline alongside the 4-failure `test_desktop_application_api.py` baseline and the 12-failure `test_draft_day_trade_lab_service.py` `AppTest` baseline Worker 4 already documented.

**Ruff**: `python -m ruff check` on all 6 touched files: 191 findings both before and after this pass (verified via `git stash`/re-run) -- zero new findings introduced (a few E501s were introduced by the new code and immediately fixed by wrapping lines before this final count).

**Frontend**: not touched this pass -- both fixes are entirely backend/facade-level (the frontend already renders whatever `data.profiles`/`starterHolesBefore`/`starterHolesAfter` the backend returns; no contract/TS change was needed for either fix). Not re-verified via `npm run typecheck`/`vitest` since no frontend file changed.

## Dev processes status (identity-verified this pass)

Redraft backend was restarted twice (once to load the fix, once for the controlled pre-fix reproduction, once more back to the fixed code) -- **final PID 37580**, port 18742, `--mode redraft --repo-root C:/NWR/prospective-outcomes-v1`, confirmed via `Get-CimInstance Win32_Process`. Dynasty backend was never restarted this pass -- **still PID 9184**, port 18741, confirmed identity-verified and functioning. Both frontends never restarted -- redraft PID 25852 (port 1422), dynasty PID 37864 (port 1421), both confirmed still listening and identity-matched to this worktree.

## Files changed

- `src/application/desktop_facade.py` -- item 4: wired `resolve_full_roster_with_unranked_occupants` into `redraft_trade_analysis`'s `roster_before_ids`/`manual_assets`. item 5: wired `selectable_profiles` into `redraft_bootstrap`'s `profiles` list.
- `src/services/waiver_engine_service.py` -- item 4: new function `resolve_full_roster_with_unranked_occupants`.
- `src/services/redraft_engine_v1_service.py` -- item 5: new `LeagueProfile.hidden_from_redraft_selector` field (default `False`, parsed with the same default) + new `selectable_profiles()` function.
- `tests/test_waiver_engine_service.py` -- item 4: 3 new unit tests.
- `tests/test_redraft_trade_analysis_service.py` -- item 4: 1 new end-to-end regression test.
- `tests/test_redraft_engine_v1_service.py` -- item 5: 2 new regression tests.
- `local_exports/redraft_v1/profiles/{6687d2b3aa21450ea0fc9e1792d461ff,9d67837e147e4aae87dbe17762ae3638,c5c77f621138494383af7fc11cc41ef4}.json` -- item 5: real, existing profile documents updated in place via `save_profile()` to set `hidden_from_redraft_selector: true`. Gitignored local runtime state, not part of the git commit.
- `docs/codex/dogfood_rebuild_20260929/LEDGER.md` -- this update.

No governed valuation model touched (`marginal_roster_utility_v2`, `governed_asset_registry_service.py`'s value formula, any base board CSV, any projection snapshot -- all confirmed untouched by `git diff`). No Sleeper/ESPN writes. No Flaim/MCP access. KHA/403N18th profile identity fields never touched (both remain visible/unflagged in the Redraft selector, as they are real leagues).

## Open issues for the next worker

1. **Trade Finder / Trade Package Search may have an analogous K/DST composition gap** (see Item 4's "Scope note" above) -- not verified this pass, worth a quick live check if the owner reports a similar symptom outside Trade Analysis specifically.
2. **`tests/test_redraft_engine_v1_service.py`'s 3 failed + 13 errors** are a newly-noticed (this pass), confirmed-pre-existing-in-this-worktree baseline (via `git stash` comparison) -- not previously catalogued in this ledger chain. Worth reconciling with `tests/test_draft_day_trade_lab_service.py`'s already-documented 12-failure `AppTest` baseline and checking whether either is fixed by the sibling `Niners-War-Room` repo's "resolve Streamlit AppTest paths from repo root" commit (`157b9601`, referenced in this session's own git log) or a similar fixture-depth fix.
3. **No native/rendered-browser visual confirmation** of either fix this pass -- both are backend/facade-only with zero frontend file changes, verified via direct HTTP round trips (`curl`) against the real running dev backends, not a rendered Chrome session.
4. **Item 6+ of the owner's original work sequence (LeagueLifecycleContext + the full Redraft/Dynasty information-architecture rebuild)** is next, per the dispatch that assigned this worker items 4-5.

---

# Worker 6 (Codex) -- items 6-9 (shared LeagueLifecycleContext + Redraft/Dynasty IA rebuild)

Dispatch HEAD: `deda149c` (verified with `git log -1 --oneline` before any edit). The only pre-existing worktree entries were the two known untracked `local_exports.backup-*` directories; neither was touched.

## Item 6 -- one shared LeagueLifecycleContext

**INSPECTED CODE**: `league_lifecycle_service.py` was already the authoritative provider-status/draft-completion resolver. `LeagueWorkspaceContext`, Weekly Home, Start/Sit, and waiver budget resolution already read Sleeper's real `state/nfl` week and league settings, but neither app bootstrap exposed one provider-neutral season phase. Frontend routing still depended on a smaller local lifecycle mirror and draft-board state. I extended the existing authority rather than creating a competing calendar.

**IMPLEMENTED**: new `src/services/league_lifecycle_context_service.py` defines the frozen `LeagueLifecycleContext` read model and `build_league_lifecycle_context()`. Its exact fields are:

- `leagueType`, `seasonYear`, `currentWeek`, `seasonPhase`, `draftStatus`
- `waiverType`, `faabEnabled`, `playoffsStart`
- `isDraftSeason`, `isRegularSeason`, `isPlayoffs`, `isOffseason`
- `providerStatus`, `seasonType`, `basis`

The phase vocabulary is `OFFSEASON`, `ROOKIE_PRE_DRAFT`, `DRAFT_APPROACHING`, `DRAFT_DAY`, `REGULAR_SEASON`, `PLAYOFF_PUSH`, `FANTASY_PLAYOFFS`, and `SEASON_COMPLETE`. The builder delegates draft/provider precedence to the existing `resolve_league_lifecycle()` function. It then uses Sleeper's real NFL `week`/`season_type`, the provider league `status`, real `settings.playoff_week_start`, and real `settings.waiver_type`. `PLAYOFF_PUSH` is relative to the league's configured playoff start (three provider weeks before it), not an arbitrary calendar date. Unknown facts remain `null`/`UNKNOWN`; provider read failure does not block bootstrap. Sleeper waiver types map as the already-established contract does: `0` free agency, `1` waiver priority, `2` FAAB.

`desktop_facade.py` now emits this same object as `lifecycleContext` in both bootstraps. Redraft uses the active profile plus draft board, persisted import status fallback, and optional read-only Sleeper evidence. Dynasty uses the active Dynasty profile plus its persisted league snapshot and the same optional read-only Sleeper evidence. `desktop/packages/contracts/src/index.ts` contains the one shared TypeScript contract consumed by both apps. No frontend calendar/date heuristic was added.

**LIVE OBSERVATION** after both backends were restarted: Fantasy Gamers returned `REGULAR_SEASON`, current week `4`, draft status `COMPLETE`, waiver type `WAIVER_PRIORITY`, `faabEnabled: false`; Las Vegas Enginerds returned `REGULAR_SEASON`, current week `4`, draft status `COMPLETE`, waiver type `FAAB`, `faabEnabled: true`. In both cases the returned `basis` cited Sleeper's real `in_season` league status taking precedence over local draft-board activity.

## Item 7 -- Redraft in-season IA and waiver-priority workflow

**INSPECTED CODE**: the prior Redraft sidebar still included Draft Room in its in-season groups and treated Improve Team and Trades as consolidated single destinations. The underlying Waivers, Add/Drop, FAAB, Streamers, Trade Analysis, and Trade Finder implementations already existed. `faabContext.isFaabLeague` and real `waiverPosition` were already correctly computed; the non-FAAB tab stopped at an explanatory empty state.

**IMPLEMENTED**:

- The sidebar now consumes bootstrap `lifecycleContext.seasonPhase`.
- In `REGULAR_SEASON`/`PLAYOFF_PUSH`/`FANTASY_PLAYOFFS`, its exact primary groups are Home (Weekly Home), Lineup (Start / Sit), Improve Team (Waiver Wire, Streamers), Trades (Trade Finder, Analyze Trade), Rankings (Weekly Rankings, Rest of Season Rankings), and League (Rosters / Opponents, Data Health).
- Draft Room and Cheat Sheet are hidden in season and promoted again in draft/offseason phases; neither route or feature was deleted.
- `/waivers` and `/streamers` are now separate first-class routed destinations while reusing the existing `ImproveTeamPage` data fetching and panels. Trade Finder and Analyze Trade are separately discoverable routes into the existing `TradesPage`. A new `/weekly-rankings` destination reuses the established provider-week and weekly-projection contracts, keeping weekly and rest-of-season ranks distinct.
- For confirmed non-FAAB leagues, the old dead-end FAAB-shaped state is replaced by an `Ordered claim builder`. It displays real waiver priority when available, renders up to six real add/drop pairings as `WAIVER CLAIM N / Add / Drop`, allows local Move up/Move down reordering, never displays dollar bids, and explicitly remains read-only (NWR never submits claims). The Add/Drop candidate table also suppresses its Suggested FAAB column when the league is not FAAB.

**LIVE OBSERVATION**, rendered Chrome session against Fantasy Gamers: the sidebar showed the exact regular-season groups above and did not show Draft Room or Cheat Sheet. Waiver Wire loaded 25 real targets; its tab renamed itself from `FAAB` to `CLAIMS` once real settings resolved. The Claims view showed real waiver priority `#8`, six ordered real claims (starting with Add Kenny Gainwell / Drop J.K. Dobbins), reorder controls, and no FAAB dollar workflow. The separate Streamers route resolved the provider week to Week 4; a read-only refresh displayed real K and DST tables, including the owner's real K starter and real available alternatives. Direct HTTP corroboration returned `isFaabLeague: false`, `waiverPosition: 8`, 10 legal add/drop pairings, and `NO_SLEEPER_WRITES`.

## Items 8-9 -- Dynasty season-aware IA, nav ordinal removal, and Home command center

**INSPECTED CODE**: the visible `1 2 3 4` values were `shortcut` properties rendered by the shared shell beside Home, Dynasty Rankings, Compare, and Trade Decision Lab. They were keyboard/navigation hints, not data. The existing Dynasty Home scanned market-wide gaps and rendered general notices, but it did not prioritize verified current-status overrides on the owner's own roster.

**IMPLEMENTED**:

- All visible Dynasty nav `shortcut` properties were removed; keyboard/command-palette navigation remains available without visual ordinals.
- Dynasty navigation now consumes the same bootstrap `lifecycleContext.seasonPhase`. Its in-season hierarchy is Home (Command Center), Team (Dynasty Rankings, Current Roster, ROS / Current Value, Rookie Watch), Trades (Trade Decision Lab, Market Gaps, Trade Block / Targets), Assets (Picks / Future Ledger, Player Explorer, Compare), and System (Data Health). Draft Cockpit and Rookie Review are promoted in draft/offseason phases and Draft Cockpit is absent in season. A compatibility fallback remains only for old bootstrap fixtures that do not carry the additive context.
- Home now builds `Priority actions` from `rankings` rows where `ownership.isMyTeam` is true. Verified `currentStatusOverride` rows sort starters first and render the real kind, reason, slot, and verification date. Owner-roster market discrepancies with absolute `marketGap >= 6` are sorted by magnitude and capped at five. The former market-wide table is now owner-roster-only; blanket notice noise is removed from Home. Governed values and ordering are untouched.

**LIVE OBSERVATION**, rendered Chrome session against Las Vegas Enginerds: the sidebar showed the in-season hierarchy, contained no visible `1 2 3 4` ordinals, and did not show Draft Cockpit. Home identified the connected real league and displayed `REGULAR SEASON · OWNER ROSTER ONLY`. Its first action was the real De'Von Achane `SEASON OUT` card, explicitly marking him as a starter and showing the verified torn-ACL reason/date. Jayden Higgins' real season-out reserve finding followed. The remaining cards were the five largest real owner-roster NWR-versus-market gaps, including Lamar Jackson and Jerry Jeudy. Direct HTTP corroboration found 23 owner-roster ranking rows, two with real status overrides, and the same market-gap values shown by the UI.

**INFERENCE**: because the rendered accessibility tree contained the lifecycle-driven groups and real roster facts after a production build and backend restart, the observed pages were consuming the new bootstrap contract rather than a test fixture. This is corroborated by the direct HTTP payloads and the real league-specific Week 4/waiver/ownership values.

## Tests and verification

**ACTUAL TEST RESULT**, backend targeted lifecycle/workspace/Dynasty-status suite:

- `tests/test_league_lifecycle_context_service.py`
- `tests/test_league_lifecycle_service.py`
- `tests/test_league_workspace_context_service.py`
- `tests/test_league_workspace_context_sleeper_p1_1.py`
- `tests/test_sleeper_league_context_service.py`
- `tests/test_dynasty_league_import_facade_wiring.py`
- `tests/test_dogfood_rebuild_v1_dynasty_status_override.py`

Result: **88 passed**. The 23 setup errors in the first attempt were a Windows global pytest-temp permission problem; rerunning against a new repository-local `--basetemp` produced the clean result above.

**ACTUAL TEST RESULT**, HTTP contract suite: `tests/test_desktop_http_api.py` -- **44 passed**.

**ACTUAL TEST RESULT**, required `tests/test_desktop_application_api.py`: **47 passed, exactly 4 failed**, with the exact documented pre-existing names and no others:

- `test_dynasty_facade_composes_real_governed_workflows`
- `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`
- `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`
- `test_facade_has_no_streamlit_or_app_component_dependency`

The additive Redraft bootstrap key assertion was updated to include `lifecycleContext`; the named failure remains part of the existing broader baseline.

**ACTUAL TEST RESULT**, frontend: `npm run typecheck` passed; full `npx vitest run` passed **531 tests in 34 files**. This includes new lifecycle-navigation coverage for both apps, draft-season promotion coverage, legacy/new Trade Finder active-route coverage, and ordered-claim reordering coverage. `npm run build` completed both Vite production builds; the only output was the pre-existing-style Redraft chunk-size advisory.

**ACTUAL TEST RESULT**, lint: the new lifecycle service and its test are Ruff-clean. `desktop_facade.py` reports 119 whole-file findings (117 E501, 2 I001); none point into the new lifecycle methods, but no clean-parent baseline comparison was performed, so they are recorded as an existing-file result rather than claimed away.

**LIVE OBSERVATION**, final services: both API `/healthz`/bootstrap paths and both preview ports were healthy after the backend restart and production frontend build. Final identity-verified processes: Redraft API PID 36440 on 18742, Dynasty API PID 31212 on 18741, Redraft Vite preview PID 25852 on 1422, and Dynasty Vite preview PID 37864 on 1421. No Sleeper or ESPN write endpoint was called; all provider calls were GET/read-only. KHA/403N18th identity fields, governed valuation formulas, base-board CSVs, projection snapshots, and the owner's AppData installation were untouched. No generated data pack was modified.

## Files changed

- `src/services/league_lifecycle_context_service.py` -- new shared lifecycle dataclass/builder.
- `src/application/desktop_facade.py` -- shared lifecycle evidence/composition and both bootstrap fields.
- `desktop/packages/contracts/src/index.ts` -- shared lifecycle TypeScript contract on both bootstraps.
- `desktop/apps/redraft/src/RedraftApp.tsx`, `league-context.ts`, `leagues.tsx` -- lifecycle-aware navigation/routing/landing.
- `desktop/apps/redraft/src/improve-team.tsx`, `in-season.tsx` -- first-class Waiver Wire/Streamers, weekly rankings, non-FAAB ordered claims.
- `desktop/apps/dynasty/src/DynastyApp.tsx`, `pages/home.tsx` -- lifecycle-aware navigation, no visible shortcut ordinals, real owner command center.
- `tests/test_league_lifecycle_context_service.py`, `desktop/apps/{redraft,dynasty}/src/lifecycle-navigation.test.ts`, `desktop/apps/redraft/src/waiver-claim-order.test.ts`, `tests/test_desktop_application_api.py` -- contract/formula/IA coverage.
- `docs/codex/dogfood_rebuild_20260929/LEDGER.md` -- this entry.

## Exact remaining owner sequence for the next worker (items 10-16)

1. Build the real Dynasty Waiver Wire destination (not added here; this pass only reorganized existing Dynasty capabilities).
2. Improve Trade Finder discoverability in both apps beyond this pass's Redraft route split.
3. Enforce trade selector ownership rules and build counter generation.
4. Rebuild streamer horizons.
5. Restructure rankings.
6. Simplify cards and warning presentation.
7. Complete the remaining ESPN path.

Also retain Worker 5's open investigation of analogous K/DST composition behavior in Trade Finder/Trade Package Search. Items 10+ were deliberately not implemented in this pass.

---

# Worker 7 (Codex) -- items 9-11 (Dynasty Waiver Wire + trade discoverability + ownership rules)

Dispatch HEAD: `96a99736` (verified exactly with `git log -1 --oneline` before any edit). The only pre-existing worktree entries were the two known untracked `local_exports.backup-*` directories; neither was touched. All four starting listeners were identity-checked with `netstat`/`Get-CimInstance` before a server was restarted.

## Item 9 -- real Dynasty Waiver Wire

**INSPECTED CODE**: Dynasty had no `THIS WEEK` group, waiver route, weekly-lineup route, streamer route, or Dynasty waiver backend. Redraft's waiver engine correctly owns redraft replacement-value/season-horizon logic, so copying its candidate score would have violated the requested Dynasty lens. The reusable boundary is the real Sleeper league context (current roster ownership, settings, and FAAB used), while Dynasty ranking must consume the existing governed Dynasty asset rows unchanged.

**IMPLEMENTED**:

- Added `GET /api/v1/dynasty/waivers`, a typed API-client method/contract, and a first-class `/waivers` table page under a new in-season `THIS WEEK` navigation group.
- Availability is a read-only Sleeper GET of the connected league and all rosters. If that optional read fails, the endpoint honestly falls back to the last dated local Dynasty snapshot, labels it `SLEEPER_SNAPSHOT`, and leaves remaining FAAB unknown rather than guessing. No Sleeper write path exists (`writePolicy: NO_SLEEPER_WRITES`).
- The ranking consumes the existing governed `nwr_dynasty_score` without changing it. The separate, deterministic priority layer is exactly: governed Dynasty score + age/upside modifier (+3 through -1) + roster-fit modifier (+4 starter need, +2 depth need, up to +3 governed-value upgrade) - 5 only for a verified `SEASON_OUT` status. Dedicated starter slots determine needs; flex slots are not incorrectly counted as a simultaneous need for every eligible position.
- Implemented dimensions: real current unrostered availability, long-term NWR value/rank, age/upside band, roster fit (`STARTER_NEED`, `DEPTH_NEED`, `ROSTER_UPGRADE`, `STASH_ONLY`), age/value-based stash band, verified current-status penalty, protected-slot-aware drop candidate, add/drop value net, and relative FAAB range against the real remaining budget. Positive FAAB ranges are capped at 35% of remaining budget and are explicitly a relative heuristic, never a predicted winning bid.
- Drop safety: starters, reserve, and taxi assets are never suggested. A same-position bench drop is preferred; if none exists, the weakest governed-value bench asset is the fallback. An open active slot suppresses the drop requirement.
- Explicitly deferred and visibly labeled `NOT_SCORED`/`UNKNOWN`: weekly short-term projection, live role/usage, injury-created opportunity, taxi eligibility, and a separate contingent-value model. Those need real Dynasty weekly evidence and were not fabricated from Redraft replacement logic.
- `THIS WEEK` intentionally contains only Waiver Wire this pass. Dynasty has no genuine weekly lineup/start-sit or streamer service to expose; those remain follow-up work rather than empty nav destinations.

**LIVE OBSERVATION**, final read-only HTTP after the last backend restart: Las Vegas Enginerds returned `SLEEPER_LIVE`, 25 real unrostered candidates, FAAB total `$100` / remaining `$100`, and a full 24/24 active roster. The rendered Chrome page showed `THIS WEEK -> Waiver Wire`, `LIVE SLEEPER AVAILABILITY`, `$100 FAAB LEFT`, `READ ONLY`, and the real 25-row table with NWR, age/upside, roster fit, stash, FAAB, and drop/net columns. No candidate payload was copied into the repository and no provider write was attempted.

**INFERENCE**: the browser and direct endpoint agreed on league name, candidate count, live-source badge, FAAB balance, and candidate facts, so the page was using the real connected league response, not a fixture or hardcoded player list.

## Item 10 -- Trade Finder discoverability and Scenario Playground disposition

**INSPECTED CODE**, Redraft: the existing real package-search implementation already supports exactly `FIND_WIN_WIN`, `TARGET_PLAYER`, and `IMPROVE_POSITION`. Worker 6 had added a top-level `TRADES -> Trade Finder` route; this pass verified that route instead of duplicating the engine. `BUY_LOW` and `SELL_HIGH` are not implemented search modes today.

**LIVE OBSERVATION**, Redraft Chrome / Fantasy Gamers: clicking the visible sidebar `Trade Finder` opened `/trade-finder`; the real search completed with **15 candidates across 8 opponent rosters, 900 packages evaluated**, and rendered packages plus before/after dimensions. Therefore Redraft Trade Finder is genuinely discoverable and functional.

**INSPECTED CODE**, Dynasty: there is a governed package evaluator (`Trade Decision Lab`), market-gap view, and manual Trade Block/Targets workspace, but no Dynasty counter generator, win-win package search, target-player search, or Trade Finder backend. A nav label pretending otherwise would still be a product failure. This pass renamed the actual evaluator destination to the clearer `Analyze Trade`; `Market Gaps` and `Trade Block / Targets` remain visible peers. A real Dynasty `Trade Finder`/package-search destination remains a larger, precisely documented backend gap for the counter-generation pass.

**INSPECTED CODE / DISPOSITION**, Scenario Playground: the route is not trade search. It is the distinct, locally persisted `Dynasty Planning Console` with six manual modules: Roster architecture, Future pick ledger, Keeper deadline, Drop deadline, Trade deadline, and Upcoming draft prep, plus checklists, notes, and governed-asset context that explicitly does not create hidden value. It is useful but not primary trade navigation. The vague `Scenario Playground` name is gone: the in-season nav keeps it demoted under Assets as `Picks / Future Ledger`, the page title remains `Dynasty Planning Console`, and its context eyebrow now says `Planning console · no hidden value`. It was not deleted because it owns a separate persistent planning workflow.

## Item 11 -- Trade Decision Lab ownership rules

**LIVE OBSERVATION, before fix**: on the real Las Vegas Enginerds Trade Decision Lab, Puka Nacua (owned by opponent roster 9; `ownership.isMyTeam=false`) appeared first in the outgoing selector and could be selected. The UI only warned after selection while still counting Puka as 1/6 outgoing. Clicking `Fill from your roster` then unexpectedly selected six real owner assets at once.

**IMPLEMENTED**:

- The default mode is now explicit `Real trade`. Its outgoing list contains only `OWNED && isMyTeam` assets (23 in the live league). Incoming is empty until one real opponent is selected, then contains only assets whose `ownership.rosterId` matches that counterparty.
- Added explicit `Hypothetical` mode for league-wide modeling. Switching modes clears both sides; switching counterparties clears only incoming. Reopening an old saved package uses Real mode only if its ownership is valid, otherwise it is explicitly Hypothetical.
- Enforcement is defense-in-depth: the backend rejects any unowned Real-mode outgoing asset, incoming assets from multiple/wrong opponent rosters, or a selected-counterparty mismatch. Exact error codes are `DYNASTY_TRADE_OUTGOING_NOT_OWNED`, `DYNASTY_TRADE_INCOMING_COUNTERPARTY_INVALID`, and `DYNASTY_TRADE_COUNTERPARTY_MISMATCH`.
- Removed `Fill from your roster`. The safe replacement is `Clear outgoing`, shown only when the owner has deliberately selected something; it never adds assets.

**LIVE OBSERVATION, after fix**: the rendered Real-mode page showed `23 ASSETS ON YOUR ROSTER`, 0/6 outgoing, and no bulk-fill button. Searching outgoing for `Puka Nacua` returned no selectable row. Selecting Achane changed the side to exactly 1/6 and exposed `Clear outgoing`; clicking it returned the count to 0/6. Direct HTTP with Puka outgoing returned HTTP 409 and `DYNASTY_TRADE_OUTGOING_NOT_OWNED`; the valid inverse package (owner's Achane out, roster 9's Puka in) returned success with `tradeMode=REAL` and `counterpartyRosterId=9`.

## Tests and verification

**ACTUAL TEST RESULT**, final targeted backend suite (`test_dynasty_waiver_service`, Dynasty league/facade wiring, desktop HTTP, trade-decision assistant, Dynasty status override, Dynasty Sleeper service, decision-bundle API): **127 passed**. This includes formula boundaries/determinism, flex-slot need correctness, FAAB caps and unavailable balance, full-league roster exclusion, unsupported-position exclusion (including no DST in this real no-DST format), protected drop slots, live/fallback facade behavior, HTTP contract, and Real/Hypothetical ownership enforcement.

**ACTUAL TEST RESULT**, required `tests/test_desktop_application_api.py`: **47 passed, exactly the same 4 pre-existing failures and no others**:

- `test_dynasty_facade_composes_real_governed_workflows`
- `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`
- `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`
- `test_facade_has_no_streamlit_or_app_component_dependency`

**ACTUAL TEST RESULT**, frontend: `npm run typecheck` passed. Full `npx vitest run` passed **532 tests in 34 files**. `npm run build` completed both production builds; Redraft emitted only its existing chunk-size advisory. The benchmark JSON rewritten by the benchmark test was restored byte-for-byte and is not part of this change.

**ACTUAL TEST RESULT**, lint/diff: the new waiver service, its formula tests, and the touched Dynasty facade-wiring test are Ruff-clean. `git diff --check` passed. Existing whole-file lint debt in `desktop_facade.py`/`server.py` was not represented as newly clean.

**LIVE OBSERVATION**, safety: all provider interaction was read-only GET. No Sleeper/ESPN transaction endpoint, KHA/403N18th identity field, governed formula, base-board CSV, projection snapshot, generated data pack, or owner AppData file was modified.

**LIVE OBSERVATION**, final services: both authenticated API health payloads returned `data.status=ok`, and both Vite previews returned HTTP 200. All four listeners remain identity-matched to this worktree: Redraft API PID 36440 / port 18742, Dynasty API PID 20808 / port 18741, Redraft preview PID 25852 / port 1422, and Dynasty preview PID 37864 / port 1421.

## Files changed

- `src/services/dynasty_waiver_service.py`, `src/application/desktop_facade.py`, `src/desktop_api/server.py` -- deterministic Dynasty waiver service/endpoint and server-side real-trade ownership enforcement.
- `desktop/packages/contracts/src/index.ts`, `desktop/packages/api-client/src/index.ts` -- typed waiver contract/client and explicit trade mode/counterparty fields.
- `desktop/apps/dynasty/src/pages/waivers.tsx`, `pages/decisions.tsx`, `pages/system.tsx`, `pages/index.ts`, `DynastyApp.tsx` -- Waiver Wire, real/hypothetical chooser rules, safe clear action, clearer planning/trade labels, and navigation.
- `tests/test_dynasty_waiver_service.py`, `tests/test_dynasty_league_import_facade_wiring.py`, `tests/test_desktop_http_api.py`, Dynasty lifecycle/decision tests, and API-client tests -- formula, fallback, contract, ownership, and navigation coverage.
- `docs/codex/dogfood_rebuild_20260929/LEDGER.md` -- this entry.

## Exact remaining work for the next worker

1. Build a real Dynasty counter/package generator before adding a `Trade Finder` destination; add `BUY_LOW`/`SELL_HIGH` only when their search semantics and evidence are real. Redraft currently has three, not five, implemented modes.
2. Add real Dynasty weekly lineup/start-sit and streamer evidence/routes; extend waiver ranking with weekly usability, live role/usage, injury-created opportunity, taxi eligibility, and separate contingent value only from governed inputs.
3. Rebuild streamer horizons (today/this week/next week/ROS where supported).
4. Restructure rankings while preserving Official, Market, War Room, and My Rank separation.
5. Simplify cards/warnings without hiding source/date/limitation disclosures.
6. Complete the honest ESPN path for KHA/403 N 18th.

Counter generation, streamer horizons, rankings restructuring, card simplification, and ESPN were deliberately not attempted in this pass.

---

# Worker 8 (Codex) -- current Dynasty value + exact-opponent counters + 1-4W Streamers

Dispatch HEAD: `3f2b49d9` (verified exactly with `git log -1 --oneline` before any edit). The only pre-existing worktree entries were the two known untracked `local_exports.backup-*` directories; neither was touched. All four starting listeners were identity-checked with `netstat` and `Get-CimInstance` before either backend was restarted.

## Item A -- Dynasty Current Rankings presentation

**INSPECTED CODE**: the Rankings page was still led by the governed base-board rank/value even though each live row already carried the independently sourced `currentStatusOverride`, `marketRank`, `marketValue`, `marketBand`, and `marketGap` fields. That made the page look like a finished frozen-model board and forced the owner to infer current usability from secondary details.

**IMPLEMENTED**, presentation-only:

- Renamed the primary view `Current Dynasty Rankings` and made its question explicit: who is worth more right now, with the frozen base model and market reference visibly separated.
- Reorganized the primary table to `Current NWR Rank`, `Player`, `Pos`, `Current Value`, `Base Model`, `Market`, `NWR Edge`, `Status`, and `Ownership`.
- Current usability ordering uses the existing verified status layer. A blocking current-status override does not receive a fabricated injury discount: the row says `Unavailable now`, retains its exact governed base rank/score and market reference, and is moved out of the usable current ordinal. `TEAM_CORRECTION` is not treated as player unavailability.
- Base `rank`, `nwrScore`, range, market rank/value/band, and market gap are displayed unchanged. No governed Dynasty valuation computation was modified.
- No `Trend` column was invented because this repository does not currently admit a real time-series trend signal.
- Added a pure ranking-presentation test proving base values remain byte-for-byte unchanged while a season-out row loses a current ordinal and usable rows close the ordinal gap.

**LIVE OBSERVATION**, rendered Chrome against Las Vegas Enginerds: the page displayed the new current-value disclosure and columns. De'Von Achane retained base rank **#9**, governed score **61.3322**, market rank **#23**, market value **6116**, and NWR edge **+14**, while his verified `SEASON_OUT` status removed him from the current usable ordinal. The next healthy rows visibly closed the current order (for example George Pickens current #9/base #10, James Cook current #10/base #11, and Zay Flowers current #11/base #12). This is status-aware presentation, not a hidden score rewrite.

## Item B -- Trade counter generation in both apps

**IMPLEMENTED**, shared safety/design boundaries:

- Added an explicit `Generate counters` action only after a valid analyzed real trade with one resolved counterparty. Hypothetical/mixed-owner packages remain ineligible.
- Both searches are bounded, preserve the strongest requested incoming modeled asset as the anchor, search same-shape swaps and one-asset add-ons, cap output at five, and evaluate every candidate through the app's existing trade evaluator rather than a new value formula.
- Ownership is enforced before search and every generated asset is drawn from the owner's or exact selected opponent's real roster. No cross-opponent asset can enter a candidate.
- Candidate cards explain `What changed`, `Why this helps me`, `Why it may make sense for them`, `NWR vs market`, and `Main risk`, plus both sides' existing-model result. No acceptance probability, willingness forecast, or claim that the opponent will accept is generated.
- Current picks were not added because verified per-roster pick ownership is not admitted in these connected league snapshots. No fake picks were constructed.

**REDRAFT IMPLEMENTATION**: `search_counter_offer_packages()` reuses `evaluate_trade()` for both sides and ranks a bounded exact-opponent search by mutual utility. The facade resolves raw Sleeper IDs to canonical players, verifies outgoing ownership and the incoming counterparty, and excludes `RESERVE` entries from active lineup evaluation while retaining them for ownership validation. `_roster_size_legal()` now correctly tolerates a provider roster that is already over its configured active count due to reserve flattening: a counter may hold or reduce the real current count but may not worsen it. This fixes a live false-negative without weakening package ownership or active-slot legality.

**REDRAFT LIVE DOGFOOD**, Fantasy Gamers: the owner's exact example is still real. Chris Olave and Jonathan Taylor are on the owner's roster; James Cook is owned by roster 1, `Show Me Your TDs`. The original package evaluated at **-144.8** net marginal utility and **-200.3** ROS value delta. The same-opponent counter search evaluated **120** bounded packages and rendered **5 constructible counters**. Example 1 was Travis Etienne + Michael Pittman for James Cook + Chris Godwin Jr. (owner utility **+22.8**, opponent utility **-7.3**); example 2 was Chris Olave + Travis Etienne for James Cook + Quinshon Judkins (owner **-15.7**, opponent **+5.6**). All named assets were verified on the respective two real rosters. The UI explicitly said there was no Redraft live-market overlay and no acceptance probability.

**DYNASTY IMPLEMENTATION**: `generate_dynasty_trade_counters()` reuses `evaluate_trade_decision()` for the owner's selected team window and for an explicit `Balanced` opponent comparison because the other manager's actual competitive window is not verified. It incorporates the existing Dynasty NWR/market/status context and real roster-need signals; every card discloses that opponent-window limitation.

**DYNASTY LIVE DOGFOOD**, Las Vegas Enginerds: a real Zay Flowers-for-Puka Nacua package against roster 9, `Rocky Mountain High`, analyzed as `COUNTER` with the counter action available. The bounded search evaluated **48** packages and returned **5** real alternatives. Examples included Drake Maye for Puka and De'Von Achane for Puka + Tyler Allgeier; the Achane card explicitly surfaced the verified `SEASON_OUT` risk rather than treating the base score as current availability. Exact ownership was preserved throughout.

**LIVE BROWSER OBSERVATION**, Redraft: Chrome was driven through the actual Chris Olave + Jonathan Taylor / James Cook selection and analysis. The rendered page showed `SAME EXACT OPPONENT · REAL ROSTER SEARCH`, `VS. SHOW ME YOUR TDS · 120 EVALUATED`, `5 constructible counters`, all five package cards, both-side utilities, explanations, risks, and the no-acceptance-probability disclosure.

## Item C -- Redraft Streamers 1-4 week horizons

**INSPECTED CODE**: Worker 6's dedicated `/streamers` navigation destination was present, but the reused panel was still a FantasyPros-driven one-week presentation. It did not answer “best pickup now for the next N weeks” from NWR's own weekly projections.

**IMPLEMENTED**:

- Rebuilt the dedicated Streamers route around a new deterministic `redraft_streamers` facade/API and `streamer_horizon_service`.
- Added real `1 Week`, `2 Weeks`, `3 Weeks`, and `4 Weeks` controls. Changing the horizon clears the previous result; the next request ranks by the selected cumulative projection window, so the control cannot merely relabel stale rows.
- NWR's admitted weekly projections under the connected league's real scoring are the primary ordering authority. FantasyPros is explicitly not used as the ranking authority on this destination.
- Candidates are the owner's current players plus genuinely available players; players owned by other teams are excluded. Positions are format-aware and include QB, TE, K, and DST only when relevant to the connected roster rules.
- Each row shows `Player`, `Owned / Available`, `1W Value`, `2W Value`, `3W Value`, `4W Value`, `Schedule`, `Why`, and `Keep vs Stream`.
- Extended the existing `weekly_game_lock_service` result additively with opponent and home/away context. Schedule is descriptive only; no undocumented matchup multiplier changes the projection score.
- Missing future projection evidence yields `null`/not-enough-data rather than a made-up total. Bye weeks and actual schedule gaps remain visible.

**REAL COVERAGE FINDING**: for the live Week 4 read, NWR had admitted weekly projection rows and real schedule/opponent coverage for all of Weeks **4, 5, 6, and 7**. Each week's four projection-provider reads returned `OK`/`LIVE`, roughly **9,418-9,422** raw rows with **983-1,044** nonzero rows. Therefore the 4-week result was genuinely supported in this live window; the implementation still degrades honestly when a later week is absent.

**LIVE BROWSER OBSERVATION**, Fantasy Gamers: the 1-week QB order began Trevor Lawrence **19.0**, C.J. Stroud **17.8**, Drake Maye **17.4**. Selecting 4 Weeks cleared the old table; rerunning produced Drake Maye **80.7**, C.J. Stroud **63.1**, Jacoby Brissett **61.4**, proving the control changed the ranking window. TE also changed (Brenton Strange was #2 at 1W but fell behind Hunter Henry and Kyle Pitts at 4W). The live page displayed Weeks 4-7 opponents, all four cumulative value columns, ownership/availability, explanations, and Keep/Stream guidance for QB, TE, K, and DST. Example schedule evidence: CHI D/ST showed `W4 vs NYJ · W5 @ GB · W6 @ ATL · W7 vs NE` with **8.6 / 15.0 / 21.6 / 28.1** cumulative values.

## Tests and verification

**ACTUAL TEST RESULT**, final targeted backend suite (streamer horizon, Dynasty counter service, Redraft package/counter search, Dynasty facade wiring, desktop HTTP, Redraft trade analysis, and weekly lock/schedule): **113 passed**.

**ACTUAL TEST RESULT**, required `tests/test_desktop_application_api.py`: **47 passed, exactly the same 4 pre-existing failures and no others**:

- `test_dynasty_facade_composes_real_governed_workflows`
- `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`
- `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`
- `test_facade_has_no_streamlit_or_app_component_dependency`

**ACTUAL TEST RESULT**, required `tests/test_redraft_engine_v1_service.py`: unchanged confirmed baseline of **25 passed, 3 failed, 13 errors**. The three failures remain `test_projection_install_is_separate_and_hash_verified`, `test_projection_install_requires_separate_bound_approval_receipt`, and `test_review_only_stale_and_shallow_projection_evidence_fail_closed`; all 13 setup errors remain the documented fixture snapshot `no rankable player rows` path.

**ACTUAL TEST RESULT**, frontend: `npm run typecheck` passed. Full `npx vitest run` passed **533 tests in 35 files**, including the new current-rank presentation test. `npm run build` completed both production Vite builds; the only build note was the existing-style Redraft chunk-size advisory.

**ACTUAL TEST RESULT**, diff/lint: `git diff --check` passed. The two new backend services and their tests are Ruff-clean. Existing whole-file line-length debt in older touched services/facade was not represented as newly clean.

**LIVE OBSERVATION**, safety: every provider call was read-only. No Sleeper/ESPN transaction endpoint, KHA/403N18th identity field, governed formula, base-board CSV, projection snapshot, generated data pack, credential, provider payload, or owner AppData file was modified or committed.

**LIVE OBSERVATION**, final services: both authenticated API health payloads returned `data.status=ok`, and both Vite previews returned HTTP 200 after the final production build. All listeners remained identity-matched to this worktree: Redraft API PID **816** / port **18742**, Dynasty API PID **20704** / port **18741**, Redraft preview PID **25852** / port **1422**, and Dynasty preview PID **37864** / port **1421**.

## Files changed

- `src/services/dynasty_trade_counter_service.py`, `src/services/streamer_horizon_service.py` -- bounded Dynasty counter search and deterministic multi-week Streamer aggregation.
- `src/services/trade_package_search_service.py`, `src/services/weekly_game_lock_service.py` -- exact-opponent Redraft counter search, live roster-size legality, and additive opponent/home-away context.
- `src/application/desktop_facade.py`, `src/desktop_api/server.py` -- live league composition, ownership validation, counter/streamer endpoints, and response serialization.
- `desktop/packages/contracts/src/index.ts`, `desktop/packages/api-client/src/index.ts` -- typed counter and streamer contracts/client calls.
- `desktop/apps/dynasty/src/pages/rankings.tsx`, `pages/decisions.tsx` -- current-value presentation and real-trade counter action/cards.
- `desktop/apps/redraft/src/trades.tsx`, `improve-team.tsx` -- same-opponent counter action/cards and the NWR-primary 1-4W Streamers page.
- `tests/test_dynasty_trade_counter_service.py`, `tests/test_streamer_horizon_service.py`, `tests/test_trade_package_search_service.py`, `tests/test_dynasty_league_import_facade_wiring.py`, `desktop/apps/dynasty/src/current-rankings.test.ts` -- formula, ownership, legality, availability, and presentation coverage.
- `docs/codex/dogfood_rebuild_20260929/LEDGER.md` -- this entry.

## Exact remaining work

1. Restructure Redraft Weekly and Rest-of-Season Rankings around owner-facing current/weekly questions and audit projection freshness; this pass changed only Dynasty Rankings and Streamers.
2. Simplify card density and warning presentation without hiding source, date, status, or limitation disclosures.
3. Complete the honest ESPN path for KHA / 403 N 18th without inventing unsupported capabilities or changing identity fields.
4. Run the broader final owner browser dogfood and full-repository regression, then push only from the coordinating session. This worker does not push.
