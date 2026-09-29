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
