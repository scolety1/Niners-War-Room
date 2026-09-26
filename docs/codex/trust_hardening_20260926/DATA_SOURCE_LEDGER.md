# Data Source Ledger — Full Trust Hardening Cycle, Worker 1

Branch: `upgrade/nwr-prospective-outcomes-v1-20260914`
Worktree: `C:\NWR\prospective-outcomes-v1`
HEAD at dispatch and at ledger-write time: `332d56f9` (no commits made until this cycle's own docs-only commit)
Date: 2026-09-26

Methodology: **INSPECTED CODE** (this worker or a delegated read-only research subagent read the actual source), **ACTUAL TEST RESULT** (a test was run and its output observed — none run this pass), **LIVE OBSERVATION** (a real HTTP request against the real running backend, made either by this worker directly this session or relayed from a prior cycle's own reported live check — each is labeled which), **INFERENCE** (a reasoned synthesis, explicitly flagged). All source-boundary findings below are INSPECTED CODE unless marked otherwise; two general-purpose research subagents did the bulk of the code reading for sources 2-9 (their reports are the basis for this table, cross-checked against this worker's own reads of `trade_roster_negotiation_service.py`, `market_baseline_service.py`, and `dynastyprocess_connector.py`, plus this worker's own LIVE OBSERVATION of the K/DST streamer today).

---

## 1. Sleeper (live API) — two structurally separate lanes

**1a. League/roster/user/draft-pick read endpoints** (rosters, players/nfl catalog, league settings, users, traded_picks) — the backbone of every Redraft in-season tool.
- Authorization: none required (public, unauthenticated GET).
- Retrieval mechanism: `SleeperHttpClient`, direct HTTP GET via `urllib.request`, on demand per request (no fixed schedule) from `desktop_facade.py` call sites. Two-tier caching (INSPECTED, `desktop_facade.py:8204-8239`): the global player catalog (`players/nfl`) uses a bounded cross-request TTL cache (`sleeper_player_catalog_cache.py`, safe because it's Sleeper-global, not league-specific); roster/user/traded-pick data uses only an opt-in, thread-local, per-request cache that never persists across requests (explicit code comment calls a cross-request cache of roster data "a real correctness bug").
- Timestamp availability: `retrievedAt`/`retrievedAtUtc` fields on responses that embed provider health; `leagueSnapshotId` (sha256 hash) embedded per response for anti-cross-league-correlation.
- Intended use: read-only source of truth for roster/league identity, scoring settings, FAAB budget, standings/opponent context.
- Prohibited use: writes. Project-wide policy (`docs/hq/master/NWR_FULL_PRODUCT_AUDIT_AND_COMPLETION_PLAN_V1.md:789`, INSPECTED): "Sleeper remains read-only unless explicitly changed later" — no automated waiver claims, roster moves, or any other write anywhere in the codebase (independently corroborated by this cycle's own zero-write hard boundary and by the prior waiver-night cycle's byte-diff-verified 0-write import proof).
- Fallback/stale behavior: on fetch failure, no fabricated substitute; individual tools either 409 (`SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED`) or degrade a specific field.

**1b. Weekly projections endpoint** — `https://api.sleeper.app/v1/projections/nfl/{season_type}/{season}/{week}` (INSPECTED, `sleeper_import_service.py:12`, `weekly_projection_service.py:311`).
- Authorization: none (public, unauthenticated).
- **Explicitly UNDOCUMENTED by Sleeper itself** (INSPECTED, `weekly_projection_service.py:19-31`): "Sleeper's own docs (docs.sleeper.com)... this endpoint is not among them... NOT officially guaranteed stable." A non-commercial-use disclosure also appears in the same docstring.
- Owner governance receipt (INSPECTED, `weekly_projection_provider_service.py:4-6`): "Owner governance decision (2026-09-10): the live Sleeper weekly-projection endpoint is APPROVED as a TEMPORARY/STOPGAP provider ONLY." `integrationStatus="EXPERIMENTAL_EXTERNAL"` is surfaced live in every `dataHealth.weeklyProjections` block this worker observed today (LIVE OBSERVATION, `GET`-equivalent `POST /api/v1/redraft/weekly-lineup` for Fantasy Gamers, 2026-09-26).
- Retrieval: on-demand fetch, 5-minute on-disk TTL cache per league/season/week (INSPECTED, `weekly_projection_provider_service.py:79`).
- Schema/coverage validation (INSPECTED, `weekly_projection_service.py:199-227`): rejects empty payloads, <1000 total rows, >50% malformed rows, <50 nonzero rows, and a coverage-collapse check (<0.4 of prior baseline) — a collapsed payload is a treated as a FAILURE, never a legitimate zero.
- Fallback/stale behavior: on live-fetch failure, reuses a cached snapshot up to 36 hours old, explicitly relabeled `status="DEGRADED"`/`freshness="STALE"` — never silently re-served as live. No usable fetch and no usable cache → an honest raised error, not a fabricated payload.
- Timestamps: `retrieved_at`, `source_as_of`, plus a SHA-256 `schema_fingerprint`/`payload_hash` persisted per successful fetch to detect silent schema drift.

---

## 2. FantasyPros — two structurally separate lanes

**2a. Live K/DST consensus API (Redraft K/DST Streamer only)**
- URL: `https://api.fantasypros.com/public/v2/json/nfl/{season}/consensus-rankings` (INSPECTED, `fantasypros_kdst_consensus_service.py:44,95-97`).
- Scope: K and DST Expert Consensus Rank + tier **only** — QB/RB/WR/TE are explicitly rejected by the module (`SUPPORTED_POSITIONS = {"K","DST"}`).
- Authorization: **required**, env var `NWR_FANTASYPROS_API_KEY`, sent as header `x-api-key`. Without a key, `provider_status().configured=False` and no live call is attempted.
- Retrieval: on-demand per streamer-panel open, `urllib.request.urlopen(timeout=20)`, **no caching at all** (explicit code-comment disclosure at `desktop_facade.py:3168-3173`).
- **LIVE OBSERVATION, this worker, 2026-09-26** (Fantasy Gamers, week 4, `POST /api/v1/redraft/kdst/streamer`): the running dev backend returned HTTP 200 with `authority: "EXTERNAL CONSENSUS — FANTASYPROS"` but **zero K/DST rows** — both position envelopes came back `confidenceState: "UNAVAILABLE"`, `confidenceBasis: "No K[/DST] rows were returned by the FantasyPros consensus read."` This means `NWR_FANTASYPROS_API_KEY` is **not configured in this dev worktree's runtime today**, contradicting the 2026-09-22 waiver-night ledger's claim of real live FantasyPros ECR data for both Sleeper leagues that same cycle (that session's environment evidently had a key set that is not present now, or the key was later removed/rotated). This is a genuine, current, re-verified finding, not an assumption carried forward — the mechanism degrades honestly (no fabricated pick), but the tool is **not currently live-functional in this dev environment** pending a real key.
- Prohibited use (INSPECTED, `docs/hq/product/nwr_external_kdst_consensus_streamer_v1_20260814/PROVIDER_BOUNDARY.md`): "No HTML scraping, key discovery, terms bypass, NWR K/DST prediction, and cross-scale math with Redraft Champion values."
- Fallback/stale behavior: malformed response fails closed; never fabricates a rank.

**2b. Dynasty offline "FantasyPros Advanced Stats Export"** — manually owner-downloaded CSV (never a live call), classified "historical evidence, not projections" (`model_v4_source_trust_contract_service.py:233-245`). FantasyPros ADP/rankings generally: `CLASSIFICATION_MARKET_CONTEXT_ONLY` — cannot directly drive private football value.

**Cross-cutting FantasyPros prohibition**: `public_source_import_service.py` `SOURCE_POLICY["fantasypros_scrape"]` = `status="rejected"`, forbidden uses = automated page extraction / required dependency. General policy catalog (`docs/hq/data_sources/NWR_PERSONAL_DATA_SOURCE_ACCOUNTABILITY_CATALOG_20260623.md`) classifies FantasyPros ECR/ADP/projections display-only-or-blocked, never a safe model input.

---

## 3. DynastyProcess (Dynasty market-value baseline)

- Repo: `https://github.com/dynastyprocess/data`, GPL-3.0 license. Values methodology is DynastyProcess's own (exponential decay over FantasyPros Dynasty ECR) — treated by NWR as an opaque, externally-produced black box, not reverse-engineered.
- Authorization: none (public GitHub raw file access). No API key.
- Retrieval mechanism: `src/connectors/dynastyprocess_connector.py` — `RAW_BASE_URL = "https://raw.githubusercontent.com/dynastyprocess/data"`, branch `master`, files `values.csv`/`values-players.csv`/`values-picks.csv`/`db_playerids.csv`/`db_fpecr_latest.csv`. **Manual/on-demand only** — fires only when the owner clicks a refresh action in `app/pages/28_settings_data_health_v1.py` (wired via `data_refresh_orchestrator_service.py` as source `dynastyprocess_market_baseline`, `AUTO_QUICK`). Upstream's OWN cadence is informational only (their GitHub Action `weekly-playervalues`, cron `23 2 * * 5` = Friday 02:23 UTC); NWR's advisory pull window is Friday 06:00 America/Denver with a Saturday backup retry — neither is an automatic NWR-side schedule.
- Cache root (outside repo): `C:\NWR_SHARED_DATA\market_sources\dynastyprocess`. Artifact dir (repo-relative default): `local_exports/refresh_data/dynastyprocess_market_baseline`; packaged-app path `%LOCALAPPDATA%\NinersWarRoom\data\refresh_data\dynastyprocess_market_baseline` (env override `NWR_REFRESH_DATA_ROOT`), preferred at runtime if present.
- Timestamp availability: `upstream_scrape_date` parsed verbatim from DynastyProcess's own CSV `scrape_date` column; `nwr_fetch_timestamp` set locally at NWR's own fetch time. Both are required columns in the freshness report.
- Freshness vocabulary (6 states, INSPECTED — not 3 as might be assumed): `GREEN_CURRENT`, `GREEN_SAME_WEEK_NO_CHANGE`, `YELLOW_STALE`, `RED_STALE`, `YELLOW_FETCH_FAILED_USING_LAST_CACHE`, `RED_NO_VALID_CACHE`.
- **Real inconsistency found**: two different, non-identical staleness thresholds exist. The connector's own `evaluate_freshness()` uses `age_days > 14` → RED_STALE, `age_days > 8` → YELLOW_STALE; but `market_baseline_service.load_market_freshness()` does a SECOND, independent recheck at `age_days > 7` that can downgrade an already-GREEN status to YELLOW_STALE. Not fixed this pass (investigation only).
- Intended/prohibited use — explicit Safe Use Policy (`docs/hq/parallel_lanes/NWR_DYNASTYPROCESS_SUSTAINABLE_CONNECTOR_V1_20260622.md`): ALLOWED = display-only market baseline, player-ID crosswalk audit, age/birthdate source audit, pick-value sanity context, NWR-vs-market disagreement flags. NOT ALLOWED without Master approval = ranking-formula input, candidate rank override, hidden sort field, private value/recommendation/simulation/final-decision input, or source-truth replacement for the NWR board/rank. Enforced structurally: every DP-derived artifact schema carries `display_only: true, model_input_allowed: false, sort_allowed: false` plus a standard row-level warning label. A separate master-level guardrail explicitly says: "Do not inspect or use opaque DynastyProcess files without explicit authorization" — no broader authorization than the original GREEN-for-display-only connector verdict was found anywhere in `docs/hq`.
- Fallback/stale behavior: fetch failure → reuse last cache, relabeled `YELLOW_FETCH_FAILED_USING_LAST_CACHE`; no valid cache at all → `RED_NO_VALID_CACHE`. Never silently served as current.
- **See the separate "Market Staleness Investigation" section of this cycle's `LEDGER.md` for the precise, hardcoded `MARKET_DATE = "2026-07-17"` finding** — that hardcode lives in `src/services/trade_roster_negotiation_service.py`, which is **legacy/dead code** from the live desktop app's perspective (only importer: `app/pages/23_trading_lab_v1.py`, the superseded Streamlit page). The LIVE Dynasty Trading Lab uses `owner_asset_evidence_service.py` → `market_baseline_service.py`'s real, dynamically-computed freshness labels instead (`"Stale as of {date}"` / `"Current as of {date}"`, never a hardcoded literal date).

---

## 4. KeepTradeCut (KTC) / FantasyCalc

Neither is wired into any live code path. Both exist only as:
- Detection/gating tokens that flag any future third-party mention of "fantasypros"/"ktc"/"keeptradecut" as requiring a source-gate/authorization before any use (`build_historical_market_adp_source_gate_v1.py:481-486`).
- An explicitly rejected policy entry (`public_source_import_service.py` `SOURCE_POLICY["ktc"]` = rejected, "No clean API/CSV and scraping is forbidden").
- FantasyCalc appears only as part of an externally-audited repository whose valuation logic was explicitly rejected ("NWR's trade authority is materially stronger... reject its valuation logic," `docs/hq/product/nwr_complete_capability_external_adoption_audit_v1_20260817/EXTERNAL_REPOSITORY_DEEP_AUDIT.md`).
- Conclusion: no connector, schema, refresh mechanism, or safe-use policy exists for either today — both are gated-out/rejected candidates, not partially-integrated sources. This is the exact gap Worker 2 is being asked to research a real, legally-available alternative for.

---

## 5. nflverse (schedules, play-by-play, rosters, player identity)

- Retrieval mechanism: the `nflreadpy` Python package, which itself pulls from nflverse's own public GitHub data releases (CC-BY-4.0; participation data CC-BY-SA-4.0 with required FTN/nflverse attribution, per a prior cycle's own source-access disclosure).
- **Schedule — three separate code paths, not one** (INSPECTED):
  1. A genuine **live runtime call** inside `weekly_game_lock_service.py` (`nfl.load_schedules(seasons=[season])`) — computes which teams are locked for a given week at request time. Fetch failure → `source_status="UNAVAILABLE"` with an empty locked-team set; the module's own docstring states "no separate live delay feed exists in this codebase."
  2. A registered "safe refresh" snapshot dataset (`nflverse_refresh_health_service.py`) — `loader="load_schedules()"`, policy `display_only`, snapshot root `local_exports/refresh_data/scheduled_ingest/nflverse`, refreshed on demand (not always-live).
  3. A display-only static CSV artifact consumer (`nflverse_schedule_context_display_service.py`) reading a tracked file, gated `SAFE_NOW_DISPLAY_ONLY`/"Not model input."
- **Player identity/crosswalk — three layers, not one monolithic table** (INSPECTED):
  1. Rookie/prospect crosswalk (`model_v4_player_identity_crosswalk_service.py`) — automated multi-source join across CFBD/RotoWire/FantasyPros/market/Kaggle-draft/third-party sources, with manual alias overrides; unresolved/ambiguous rows flagged for human follow-up.
  2. Veteran identity (`nflverse_identity_service.py` + `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_identity_map.csv`) — cascading match order (player_id → sleeper_id → gsis_id → fantasy_data_id → espn_id → pfr_id → fuzzy name/position/team), human-review-gated statuses.
  3. The governance binding packet actually named in the dispatch (`docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/`) — a human-approval-gated join certifying NWR canonical player ID = Sleeper player ID for current/veteran players, requiring `human_decision=APPROVE_REVIEW_ONLY` AND `approved_by_human=true` plus 4-file agreement (name/position/team/GSIS/Sleeper ID). Explicit exclusion: "DynastyProcess IDs were not used as binding evidence... Market, ADP, vendor, Gmail, or private sources were not used." Missingness policy: "Missing identity data remains 'Not enough information'... never treated as a clean match." This is the exact file `trade_roster_negotiation_service.py` reads to resolve rookie identity (`_approved_rookie_sleeper_ids`).
- Fallback/stale behavior: consistently display-only/local-snapshot-based rather than always-live; no evidence of silent substitution.

---

## 6. Injury / player-availability status (the "shared status-override layer")

- **Real data source: a manually-maintained JSON file, NOT an automated feed.** `src/services/current_player_status_overrides_service.py` reads `config/nwr_verified_current_player_status_overrides_v1.json` — no network call anywhere in the module. The only write path (`add_verified_status_override`) requires at least one cited source URL per entry ("an uncited event is exactly what this intake contract exists to refuse"). Four override kinds only: `SEASON_OUT`, `NOT_WITH_TEAM`, `ADMINISTRATIVE_EXEMPT`, `TEAM_CORRECTION`.
- Applied to live rankings at both Start/Sit and Waivers call sites (`desktop_facade.py`, 8 call sites total).
- **Explicit disclosure (INSPECTED, exact citation)**: `player_availability_status_service.py:8-16` — "there is no live/automated in-season injury-news ingestion system anywhere in this codebase... The ONLY real, current-season status source this app has is the manual override mechanism above." The `automatedFeed: False` flag and the "No automated injury/practice-report feed exists" phrasing live in `player_availability_status_service.py` (`player_availability_authority_health()`, ~lines 218-219) — **not** in `data_health_dashboard_service.py`, which contains zero injury-related code on full-file inspection (a citation correction worth carrying forward: any doc attributing that disclosure string to the data-health dashboard file is wrong).
- **LIVE OBSERVATION, this worker, 2026-09-26**: Fantasy Gamers' live `data-health` response showed `PLAYER_STATUS: OK / MANUAL` — the freshness label itself literally says `MANUAL`, directly corroborating the code-level disclosure in a real running response.
- A separate, unrelated module (`injury_availability_context_service.py`) is a DIFFERENT, display-only historical/factual nflverse injury-report-week-count feed for the Rankings/Compare panel — explicitly gated `SAFE_NOW_DISPLAY_ONLY`/`model_input_allowed: false`, deliberately independent of the live-decision override layer above. Do not conflate the two.
- Fallback/stale behavior: N/A — this is a static file, not a live fetch; absence of an override for a given player is the correct/default state, not a failure.

---

## 7. Data-health / freshness disclosure surfaces

- **`data_health_dashboard_service.py`** (1092 lines, INSPECTED in full by the delegated subagent): its real structure is sections `App/Board/Market/Runtime/NGS context/Refresh Data/Evidence/Missing data/Guardrail` with `GREEN/YELLOW/RED/INFO` statuses — **not** a `LEAGUE_SYNC/ROS_PROJECTIONS/WEEKLY_PROJECTIONS/...` enum (that enum does not exist as a defined constant anywhere; those are the LIVE `/api/v1/redraft/data-health` response's own category labels, generated by a different code path — see below). This file has **no numeric hour/day threshold logic of its own** — it mostly re-buckets freshness status already computed elsewhere (e.g., the Market section passes through `market_baseline_service.load_market_freshness()`'s own status). Two real, pre-existing precision quirks found (not fixed this pass, investigation only): (1) `_missing_data_health()` has a broken ternary where both branches produce `"YELLOW"` regardless of actual queue length; (2) several rows are unconditionally hardcoded `"GREEN"` with no real computed check behind them (documentary/assertion rows, e.g. "App mode," "No model/rank mutation").
- **The `/api/v1/redraft/data-health` endpoint's own category set** (`LEAGUE_SYNC`, `ROS_PROJECTIONS`, `WEEKLY_PROJECTIONS`, `MARKET_ADP`, `PLAYER_STATUS`, `DECISION_ENGINE`, `SNAPSHOT`) is real and LIVE-CONFIRMED this session (Fantasy Gamers: all 7 categories returned `OK`, with per-category freshness labels `CURRENT`/`LIVE`/`MANUAL` as appropriate) — this is the Redraft in-season freshness authority actually seen by an owner, distinct from the older, more Dynasty-oriented dashboard file above.
- **No separate Dynasty-specific health/freshness service file exists** (confirmed by name and content search) — Dynasty and Redraft share the one `data_health_dashboard_service.py`, whose sections happen to be overwhelmingly Dynasty-side artifacts (frozen board, DynastyProcess baseline, model-eval CSVs) plus a generic refresh-health section that also covers Sleeper/nflverse.
- Missing-data handling: no exception path defaults to a false "OK"; the closest quirk is `_read_csv()` silently returning an empty DataFrame on any read exception (collapsing "file missing" vs. "file corrupt" into one case), but every caller treats an empty frame as YELLOW, never GREEN.

---

## 8. Redraft governed model ("Redraft Champion" / Redraft Engine V1)

- No single file literally named `MODEL_SPEC` exists for the live product; the closest equivalents are per-lane `EXECUTIVE_VERDICT`/registration docs.
- `docs/hq/model/nwr_redraft_engine_v1_20260808/EXECUTIVE_VERDICT.md`: verdict `BLOCKED_NWR_REDRAFT_ENGINE_V1_MISSING_CURRENT_SEASON_EVIDENCE` at that time; gauntlet winner `R2_FLEX_AWARE_REPLACEMENT` (Spearman 0.6949, top-50 hit rate 0.5246) — explicitly scoped to "the frozen NWR non-PPR/first-down historical scoring profile," not a blanket authorization of 2026 ranks. K/DST supported only via a governed override; missing evidence is blocked, never scored as zero.
- Later admitted seed: `docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/PROVENANCE.md` — "Freeze V7," 491 veteran + 73 rookie rows, owner-approved via `NWR_DATA_GOVERNANCE.json` (`approval_status: "APPROVED_FOR_REDRAFT_V1"`, `valid_until: "2026-10-08"` — **worth flagging: this approval has an explicit expiry date that is now less than two weeks away from today, 2026-09-26**). Explicitly a pure data-source swap — "No projection value, formula, model weight, scoring, roster-legality, or `marginal_roster_utility` logic" changed.
- `marginal_roster_utility_v2` (INSPECTED location: `src/services/shadow_numeric_authorities_service.py`) is consumed **read-only** by `decision_bundle_service.py`, `redraft_trade_analysis_service.py`, `waiver_engine_service.py`, `weekly_lineup_optimizer_service.py`, and `desktop_facade.py` — status `CLOSED, unchanged, called read-only` per the most recent freeze doc. This cycle did not touch it, per the hard boundary.
- Team Score V2 / Championship Equity V2 is a registered CHALLENGER, not yet full champion (`docs/hq/adoption/champion_challenger_registry/decision-bundle-v2-team-score-championship-equity-v1/registration.json`): `verdict: GREEN_2025_FINAL_HOLDOUT_PASSED`, with an explicit disclosed limitation that "Championship Equity V2 ranking evidence is NOT_DECISIVE per its own frozen report" and that real owner leagues will report `TRANSPORT_SUPPORTED_NOT_HISTORICALLY_VALIDATED`, not `HISTORICALLY_VALIDATED`.

## 9. Dynasty governed model ("Finished V1" + governed asset registry)

- `docs/hq/master/nwr_golden_lane_v1_20260731/CURRENT_CANONICAL_STATE.md`: "Finished V1: 240 current players; SHA-256 `263cc8aa...`"; registry exposes exactly 240 Finished V1 players, 73 scored Review-Only rookies, 7 blocked identities, 50 frozen draft-context picks; explicitly "creates no common value or recommendation" across the veteran/rookie boundary — a unified rookie/veteran common scale was tried and explicitly rejected (`BLOCKED_NWR_ROOKIE_OR_VETERAN_COMMON_SCALE`), on the documented principle that "a validated 'no' is an acceptable final answer."
- Rookie Review (80-player candidate) status: `HOLD_80_PLAYER_ROOKIE_REVIEW_CANDIDATE` — "ready for owner review, not canonical promotion."
- `governed_asset_registry_service.py` (inspected at a high level only, per this cycle's boundary): a read-only, source-separated registry for governed NWR assets (current/rookie/blocked/rookie-overlay/pick/future-pick), with SHA-256 file verification on every admitted source.
- Overall governance pattern across both Redraft and Dynasty model lanes (INFERENCE from the pattern observed across many `docs/hq/model/*` folders): every promotion path follows (1) a frozen/backtested candidate with quantified metrics, (2) an explicit statement of what is NOT proven/authorized by that backtest alone, (3) a required separate owner-approval receipt before canonical/production status. A "GREEN" verdict means "this specific gate passed," never "live and authoritative for every use."

## 10. General data-governance charter (cross-cutting)

- `docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708/`: docs-only charter; six mandatory questions per source review (do we have it / where from / reliable enough / use classification / reproducible / leakage-testable); 11 formal use-gate statuses (`PRODUCTION_MODEL_USE`, `REVIEW_ONLY`, `DISPLAY_ONLY`, `BLOCKED`, `IDENTITY_UNSAFE`, `LEAKAGE_UNSAFE`, `NOT_ENOUGH_INFORMATION`, `MISSING_SOURCE`, `MISSING_RECEIPT`, `REBUILD_BLOCKED`, `JOIN_BLOCKED`); default rule "use the strictest accurate status; do not upgrade by implication." Data Hygiene review cannot itself approve production/model use, ranking changes, or canonical merges.
- Master-level general guardrail list (`docs/hq/master/NWR_FULL_PRODUCT_AUDIT_AND_COMPLETION_PLAN_V1.md:784-805`): "Missing data stays UNKNOWN, not zero. Research remains labeled Research Only. External consensus is not NWR model authority. No model promotion without validation. Do not train to consensus/market. No canonical publication without explicit owner approval. Do not inspect or use opaque DynastyProcess files without explicit authorization. Do not introduce paid/provider dependencies silently." This is the standing charter every source-specific policy above (FantasyPros, DynastyProcess, KTC) is a specific instance of.

Note: `C:\NWR\Niners-War-Room\AGENTS.md` (the separate from-scratch "Niners Dynasty: War Room" Streamlit/SQLite project referenced by this session's own system prompt) governs a **different, sibling** project directory and has no bearing on the `docs/hq` governance documented in this worktree — confirmed identical text in both locations, already reconciled as stale product-vision framing by an earlier cycle (see this ledger's Part 0 section).

---

## Key file index

- `src/services/weekly_projection_service.py`, `weekly_projection_provider_service.py`, `sleeper_import_service.py`
- `src/services/fantasypros_kdst_consensus_service.py`, `model_v4_fantasypros_advanced_intake_service.py`, `model_v4_fantasypros_identity_mapping_service.py`, `model_v4_source_trust_contract_service.py`, `public_source_import_service.py`
- `src/connectors/dynastyprocess_connector.py`; `src/services/market_baseline_service.py`, `data_refresh_orchestrator_service.py`; `src/services/trade_roster_negotiation_service.py` (legacy market staleness hardcode)
- `src/services/data_health_dashboard_service.py`, `app/pages/28_settings_data_health_v1.py`
- `src/services/current_player_status_overrides_service.py`, `player_availability_status_service.py`, `injury_availability_context_service.py`
- `src/services/weekly_game_lock_service.py`, `nflverse_refresh_health_service.py`, `nflverse_schedule_context_display_service.py`
- `src/services/model_v4_player_identity_crosswalk_service.py`, `nflverse_identity_service.py`; `templates/real_data_inputs/nflverse_stats_upgrade/nflverse_identity_map.csv`
- `src/services/waiver_engine_service.py`, `shadow_numeric_authorities_service.py`, `governed_asset_registry_service.py` (read-only inspection only), `desktop_facade.py`
- `docs/hq/master/NWR_FULL_PRODUCT_AUDIT_AND_COMPLETION_PLAN_V1.md`; `docs/hq/master/nwr_golden_lane_v1_20260731/CURRENT_CANONICAL_STATE.md`
- `docs/hq/model/nwr_redraft_engine_v1_20260808/`, `nwr_rookie_review_candidate_v1_20260814/`, `nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/PROVENANCE.md`
- `docs/hq/parallel_lanes/NWR_DYNASTYPROCESS_SUSTAINABLE_CONNECTOR_V1_20260622.md`; `docs/hq/contracts/market_baseline/market_baseline_schema_v1.json`
- `docs/hq/product/nwr_external_kdst_consensus_streamer_v1_20260814/PROVIDER_BOUNDARY.md`, `EXECUTIVE_VERDICT.md`
- `docs/hq/data_sources/NWR_PERSONAL_DATA_SOURCE_ACCOUNTABILITY_CATALOG_20260623.md`; `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/`
- `docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708/`
- `docs/hq/adoption/champion_challenger_registry/decision-bundle-v2-team-score-championship-equity-v1/registration.json`
