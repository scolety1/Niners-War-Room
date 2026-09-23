# Waiver-Night Readiness / Hardening — LEDGER (Worker 1)

Branch: `upgrade/nwr-prospective-outcomes-v1-20260914`
Worktree: `C:\NWR\prospective-outcomes-v1`
Worker 1 dispatch HEAD: `6351db5a5fc66f0b00a91ac08596ace05c12f8a4` (docs: record Worker 5 closure for the Flaim-integration cycle)
Worker 1 completion HEAD: same commit, plus this docs-only commit (read-mostly pass, no product code touched)
Date: 2026-09-22

This is the FIRST ledger of the new "Waiver-Night Readiness / Hardening" cycle (~9-10 workers tonight). It is intentionally research/reconciliation-heavy so that later workers (especially Worker 2's capability-matrix gap audit, and Worker 3's provider-neutral canonical league-state refactor) do not have to re-derive the current architecture from scratch.

Methodology note used throughout: **INSPECTED CODE** (I or a delegated research subagent read the actual source), **ACTUAL TEST RESULT** (a test was actually run and its output observed), **LIVE OBSERVATION** (the running app/data was actually queried), **INFERENCE** (a reasoned guess not directly confirmed by any of the above). All Phase 0 findings below came from three parallel read-only research subagents plus my own direct spot-checks; all are INSPECTED CODE unless explicitly marked otherwise. Nothing in this cycle so far executed `pytest` end-to-end (no ACTUAL TEST RESULT claims below beyond what the prior Flaim cycle's own ledger already reported, which is cited as such).

---

## PHASE 0.1 — Repo reconciliation

- **LIVE OBSERVATION**: `git fetch origin` returned no new refs; `git log --oneline HEAD..origin/upgrade/nwr-prospective-outcomes-v1-20260914` was empty. Branch is up to date with its own remote tracking branch, HEAD matches the dispatch prompt's stated `6351db5a` exactly. No drift since the last cycle — nothing to preserve/reconcile.
- **LIVE OBSERVATION**: `git status` shows working tree clean except the two expected backup directories (`local_exports.backup-20260918T230905Z/`, `local_exports.backup-20260919T233737Z/`) plus a third, previously-undocumented one found during research: `local_exports.backup-20260917T224444Z/` (noted by the governance research subagent while reading the Flaim ledger — not independently re-verified by me via `ls`, flagging as a minor discrepancy from the dispatch prompt's "2 known backup dirs" framing; harmless, all three are untracked and additive, consistent with this saga's dated-snapshot discipline — see AGENTS.md reconciliation below).

---

## PHASE 0.2 — AGENTS.md reconciliation (the owner-facing deliverable)

**Strongest single piece of evidence, found directly in-repo**: `PRODUCT_ARCHITECTURE.md` (lines 1-16) *already self-documents* that AGENTS.md is stale: "Root docs that predate this pass (`README.md`, `MISSION.md`, `DATA_MODEL.md`, `MODEL_SPEC.md`, `USER_WORKFLOW.md`, **`AGENTS.md`**, `docs/codex/ARCHITECTURE*.md`) describe a Streamlit, local-only, CSV-pack, dynasty/keeper-league prototype that predates the live desktop Redraft app entirely — legacy, not wrong-but-stale... do not treat them as describing the live product." `README.md` carries a parallel "LEGACY NOTICE (2026-09-10)" banner. So the overall staleness of AGENTS.md's *product vision* is not a new finding this cycle — it's already repo-acknowledged. What follows is the line-by-line verdict, since several individual constraints are still literally true even inside the demoted legacy sub-product.

**Direct confirmation of the two-product-surface structure (my own spot-check, INSPECTED CODE)**: this repo genuinely contains BOTH systems today, not just doc drift:
- **Legacy** (matches AGENTS.md almost exactly): `app/` (`main.py`, `main_redraft.py`, `legacy_pages/`, `pages/`, both files `import streamlit as st` directly). `pyproject.toml`/`requirements.txt` still list `streamlit`, `pydantic`, `pandas`, `nflreadpy` as real installed deps — this stack is not deleted, just demoted.
- **Current/live** (what the entire multi-cycle `docs/codex/` saga, and this cycle, is actually about): `desktop/` — a real Tauri 2.11.4 + React 19 + Vite + TypeScript workspace (`desktop/package.json`), two apps (`desktop/apps/dynasty`, `desktop/apps/redraft`), a Rust runtime crate (`desktop/crates/nwr-desktop-runtime`), and a `sidecar:build` script that packages the Python backend at `src/` (FastAPI-style `src/desktop_api/server.py`, `src/application/desktop_facade.py`) as a bundled sidecar process.

**Constraint-by-constraint verdict:**

| AGENTS.md constraint | Verdict | Evidence |
|---|---|---|
| "Primary build target: V1 Drop Deadline Command Center" / "Niners roster page" / generic keeper/drop/pick-value/trade-board | **STALE** | `PRODUCT_ARCHITECTURE.md`'s legacy-notice framing; live product is Redraft (in-season weekly tools) + Dynasty (offline research), not a single "V1"; 287+ dated cycles under `docs/codex/` |
| "Do not require live API calls at app runtime" / "Treat APIs only as optional data collection mechanisms" | **STALE, directly contradicted** | `PRODUCT_ARCHITECTURE.md` line 24: live backend talks "to Sleeper and FantasyPros live"; `tests/test_weekly_home_sleeper_fetch_caching.py`, `tests/test_sleeper_player_catalog_cache.py` exist specifically to test live-fetch-with-caching runtime behavior; the entire Flaim/ESPN cycle is about adding a SECOND live-API provider |
| "Use local CSV and SQLite snapshots" / "Current preferred stack: Streamlit... SQLite" | **PARTIALLY STALE, not fully dead** | Streamlit/SQLite genuinely still used by the demoted `app/` legacy sub-product (`src/data/db.py`, `src/data/loaders.py`, `src/data/migrations.py`, `src/config/constants.py`, `src/services/team_service.py` still reference sqlite) — but NOT the live product's stack (Python FastAPI-style + React/Tauri). Notably: `tests/test_desktop_application_api.py::test_facade_has_no_streamlit_or_app_component_dependency` currently **FAILS** (AST-asserts `desktop_facade.py` has no `streamlit`/`app`-prefixed import) — this is one of the Flaim cycle's own reported "4 pre-existing failed" tests, meaning the codebase's OWN test suite asserts this separation and is *currently failing to fully satisfy it* — a real, open architectural gap, not a settled binary |
| "Do not scrape websites" | **STILL BINDING** | No scraping found anywhere; ESPN integration is explicitly an MCP connector (Flaim), not scraping; Sleeper/FantasyPros use documented HTTP APIs (`SleeperHttpClient`, `fantasypros_kdst_consensus_service.py`) |
| "Do not delete files outside the repository" | **STILL BINDING** | No counter-evidence found; consistent with this saga's careful, repeatedly-documented file-scoping discipline |
| "Do not modify generated data packs unless explicitly asked" / "Do not overwrite old data packs. Create new dated snapshots" | **Letter dormant, spirit STILL GENUINELY BINDING under a different name** | The literal `data_packs/` CSV mechanism is empty (`.gitkeep` only) in this worktree. But the exact same discipline is alive as `local_exports.backup-<UTC-timestamp>/` directories — three exist in this worktree, each a fresh timestamped backup taken before touching anything, prior backups left untouched |
| "Keep formulas deterministic and testable" / testing requirements generally | **STILL GENUINELY BINDING, actively honored at scale** | Every worker pass across the Flaim ledger added dedicated unit tests and ran full regression before proceeding; `pytest.ini_options`/`ruff` config still present and current in `pyproject.toml` |
| "Prioritize correctness over polish" | **STILL GENUINELY BINDING, strongly evidenced** | The entire Flaim ledger's culture (5 workers, repeatedly catching+fixing masked-test-failure risks, distinguishing INSPECTED CODE/ACTUAL TEST RESULT/LIVE OBSERVATION/INFERENCE) is a direct, magnified expression of this exact value — this ledger continues that discipline |
| "Do not hardcode player data except in sample fixtures" | **STILL GENUINELY BINDING** | No counter-evidence found; `sample_data/kha_real_draft_2026/` exists as populated real sample-fixture data (contains the real "Colety Crusaders" team name), consistent with the rule's spirit |
| "Do not implement complex ML in V1" | **Loosely still binding in spirit** | No complex ML found in a time-boxed survey; "V1" itself is a stale framing given 287+ dated cycles beyond any single V1 |
| "Never assume unknown league rules. If a rule is unclear, represent it as configurable." | **STILL GENUINELY BINDING and directly, tightly relevant right now** | `CAPABILITY_AUTHORIZATION_MAP.md`'s scoring-settings row requires `hasScoringSettings` to be `COMPLETE` only when every field maps with known confidence, else `PARTIAL`/`UNKNOWN` with unmapped fields disclosed — a direct modern instantiation of this exact principle, and DIRECTLY the right lens for the new Sept-22 evidence's ESPN scoring-modifier gap (see below) |
| "Keep UI simple, table-first, and low-text" / "Hide long explanations behind side panels" / "Separate Official Rank, Market Rank, War Room Rank, and My Rank" | **STALE as literally worded** | No evidence these specific UI/ranking-taxonomy terms exist in the live React desktop app's IA; `PRODUCT_ARCHITECTURE.md`'s task map uses a completely different task-first taxonomy (Start/Sit, Waivers, Trade Analysis, etc.) — not independently re-verified beyond that architecture doc in this time-boxed pass |

**Bottom line for the owner**: AGENTS.md's product-vision framing (Streamlit/V1/Drop-Deadline/generic-fantasy-tool) is stale and the repo already says so itself. Its general engineering-discipline constraints (no scraping, no live-runtime deletion outside repo, dated snapshots not overwrites, deterministic/tested formulas, correctness-over-polish, hardcode-nothing-except-fixtures, never-assume-unknown-rules-make-them-configurable) are still genuinely followed today, just implemented under new names/mechanisms. This ledger does NOT rewrite AGENTS.md — that's an owner decision, not something claimed as authorized here.

---

## PHASE 0.3 — Flaim/ESPN governance state (prior cycle recap + what's now in question)

**`docs/codex/flaim_integration_20260919/LEDGER.md` (prior, completed cycle) — INSPECTED CODE + that ledger's own reported ACTUAL TEST RESULT/LIVE OBSERVATION claims, relayed here, not independently rerun by me:**
- Built: provider-agnostic `LeagueCapabilities` model (`src/services/league_capability_service.py`), `EspnFlaimSnapshot` schema + validating loader (`src/services/espn_flaim_snapshot_service.py`), a `scripts/refresh_espn_flaim_snapshot.py` CLI skeleton (raises `NotImplementedError` by design — confirmed by that cycle actually running it), 11 backend facade methods + 20 of 27 frontend call sites converted from `provider == "sleeper"` string checks to capability-based gating.
- A real regression was caught+fixed live during that cycle: gating on `has_roster_data` would have broken Fantasy Gamers (real receipt has `roster_snapshot: null`); fixed to gate on `has_verified_identity` instead.
- End state, that cycle's own words: "ARCHITECTURE + GOVERNANCE + HONEST GATING COMPLETE — REAL ESPN DATA FLOW STILL BLOCKED ON THE OWNER'S PENDING ONE-TIME FLAIM AUTHENTICATION." Zero bytes of real KHA/403N18th data exist anywhere in this repo. That cycle explicitly flagged that even once OAuth completes, the 11 guarded methods' Sleeper-specific live-fetch logic will still honestly fail until a future worker builds a real ESPN live-fetch path — not automatic.
- Tests that cycle reported: 208 passed / 4 pre-existing failed (byte-identical) on a targeted 19-file backend set; `npx vitest run` 503/503; pushed to origin by that cycle's Worker 5.

**`docs/hq/master/flaim_scoped_capability_reauthorization_v1_20260919/CAPABILITY_AUTHORIZATION_MAP.md` — current authorization state (INSPECTED):**
Verdict on file: `SCOPED_READ_ONLY_CAPABILITY_AUTHORIZATION_GRANTED_FOR_IDENTITY_ROSTER_LINEUP_SETTINGS_ONLY`, granted by the owner's own dated written authorization.
- **Allowed**: verified league identity, roster-slot mapping, roster membership snapshot (point-in-time, `retrieved_at_utc` required), lineup/slot eligibility, scoring settings (with COMPLETE/PARTIAL/UNKNOWN flag).
- **Constrained/blocked**: standings (display-only-with-disclosure at most, schema doesn't even model it); transaction direction/waiver-claim/add-drop reconstruction (blocked by BOTH the July finding AND the project's independent standing "no provider writes" rule — two separate blocks, not one); available-player pool (must carry BOUNDED/NONE, COMPLETE structurally rejected by the parser); Flaim's own computed judgments/rankings (0% production influence, untouched).

**What the September 22 new evidence (owner-reported, UNVERIFIED by this codebase) would call into question if formally re-audited — and what it would NOT change:**
- Calls into question: the July-sourced **free-agents** finding ("capped, alphabetic, noisy, incomplete" — new evidence claims real 100-row `get_free_agents` results) and the **transactions** finding ("materially unsafe" — new evidence claims real `get_transactions` via `mTransactions2` success, with waiver-clear timestamps, completed FAAB bids, distinguishable waiver-vs-free-agent state).
- Would NOT fully unblock transactions even if the July finding is reversed: the transaction-direction block is doubly imposed (July finding + the project's own independent no-provider-writes rule), and only ONE of those two blocks is even theoretically in play here.
- Would NOT change the scoring-settings row at all: the new evidence explicitly does NOT claim full scoring-modifier exposure (only high-level H2H_POINTS/lineup slots/position limits) — `hasScoringSettings` PARTIAL/UNKNOWN discipline remains exactly correct and unchallenged.
- The capability-map document itself already anticipates this dynamic (its own closing section calls for a future formal per-capability re-audit against real fetch results) — **that formal re-audit is explicitly NOT done by this worker**, it is handed off (see Open Issues below).

**Current real ESPN/Flaim pipeline state (INSPECTED CODE, confirmed independently by two of the three research subagents):**
`src/services/espn_flaim_snapshot_service.py` is schema-and-parser only — no live network call exists anywhere in this codebase today. `EspnFlaimSnapshot` deliberately has NO standings field modeled at all, and `parse_espn_flaim_snapshot` structurally REJECTS `available_player_pool_coverage == "COMPLETE"` as an invalid state (encoding the OLD July finding directly into the schema's validation). `scripts/refresh_espn_flaim_snapshot.py::main()` unconditionally raises `NotImplementedError` — explicitly scoped to only ever call `get_league_info`/`get_roster`/`get_free_agents`, deliberately NOT `get_standings` or `get_transactions`. **This means: if the September 22 evidence is later confirmed real, the schema/parser/refresh-script will all need real revision** (the free-agent-pool-coverage rejection and the transactions exclusion both directly encode the OLD findings the new evidence disputes) — this is exactly Worker-2-or-later's re-audit scope, not something I changed.

This worker has NO Flaim MCP access (confirmed: `mcp__flaim__authenticate`/`mcp__flaim__complete_authentication` were listed as deferred tools available to the top-level session but were never invoked by me or any research subagent, per the hard boundary in the dispatch prompt).

---

## PHASE 0.4 — Architectural map (for Worker 3's provider-neutral refactor)

**One facade class, two independent storage systems.** `src/application/desktop_facade.py` (9221 lines) has exactly one class, `DesktopBackendFacade` — there is NOT a separate Redraft-app class and Dynasty-app class. Both live as method-naming conventions (`redraft_*` vs `dynasty_*`) inside the same class, gated by a `_require_mode("redraft"|"dynasty")` guard. Two separate storage roots: `self.redraft_root` and `self.dynasty_league_root` (explicitly NOT sharing `DEFAULT_WORKSPACE_ROOT`, worktree-isolated).

**`_active_sleeper_context()` (desktop_facade.py:7813) is the single hardest chokepoint for a provider-neutral refactor.** Three-stage logic:
1. Requires an active profile (409 if none).
2. Computes provider-agnostic `LeagueCapabilities` via `league_capability_service` and requires `has_verified_identity` (already provider-agnostic — a 2026-09-19 "Worker 3" code comment confirms this was deliberately loosened from a blanket provider check so a future verified ESPN snapshot COULD satisfy this specific gate).
3. **Immediately re-imposes a hard `provider != "sleeper"` gate** (409 if not Sleeper) — because every downstream caller does live `SleeperHttpClient` fetches with no ESPN/Flaim live-fetch equivalent yet. So step 2 is provider-neutral but step 3 makes the whole function still 100% Sleeper-only in practice today.

The **11 call sites**: `redraft_free_agents` (3112), `redraft_opponent_rosters` (3153), `redraft_my_roster` (3232), `redraft_weekly_projections` (3316), `redraft_weekly_lineup` (3410, Start/Sit), `redraft_waivers` (3758), `redraft_trade_analysis` (4538), `redraft_trade_finder` (4736), `redraft_trade_package_search` (4957), `redraft_league_workspace_context` (5232, calls it a SECOND time inside its own duplicated `provider == "sleeper"` check), `redraft_data_health` (5543, same duplicated-check pattern). Methods #10/#11 both independently re-derive `active_profile()` and duplicate the Sleeper-only branch condition ad hoc rather than centrally.

**Provider dispatch for live fetches is 100% ad hoc string checks today** — `selected.provider == "sleeper"`, duplicated in at least 2 places, with direct `SleeperHttpClient` calls inline in ~11 methods. The ONE existing real provider-interface abstraction is `weekly_projection_provider_service.default_weekly_projection_provider()` (used by weekly projections only) — this is the pattern worth mimicking for a broader roster/opponent/free-agent provider interface; it has not been extended to those.

**`league_capability_service.py` (230 lines) is the genuinely reusable, already-provider-neutral piece.** Pure, zero I/O, dispatches on receipt/snapshot shape not provider strings (verified by its own dedicated, thorough test file, `tests/test_league_capability_service.py`). `LeagueCapabilities` models DATA COMPLETENESS (verified identity / roster presence / lineup eligibility / scoring completeness COMPLETE|PARTIAL|UNKNOWN / player-pool coverage COMPLETE|BOUNDED|NONE / standings DISCLOSED_NON_AUTHORITATIVE|NONE / `transaction_direction` hardcoded to the single literal `NOT_ENABLED`) — it does NOT model "can this profile do waivers" in a workflow sense, and it is NOT currently the authority actually gating the 11 live-fetch methods (`_active_sleeper_context()` only uses it for the identity pre-check, then falls through to its own separate hardcoded Sleeper-only gate regardless).

**No shared canonical "LeagueSnapshot" abstraction exists today.** Two unrelated concepts:
- Redraft's `LeagueWorkspaceContext` (`src/services/league_workspace_context_service.py`, 190 lines) — a lightweight, provider-labeled (`provider`/`provider_league_id` fields exist), hash/identity-only wrapper (`league_snapshot_id` is a sha256 hash string, NOT a data-carrying object) with zero data payload of its own; performs zero new I/O.
- Dynasty's `DynastyLeagueSnapshot` (`src/services/dynasty_sleeper_league_service.py:215`) — a REAL, Sleeper-specific data-carrying snapshot (rosters, settings, traded picks, drafts), built via `fetch_dynasty_league_snapshot`.
- These have no shape or naming convergence. `LeagueWorkspaceContext` is the closer candidate to extend (already has provider fields, already does no I/O) but would need a real data payload to serve as a true canonical snapshot, and would need to absorb/mirror whatever `DynastyLeagueSnapshot` models.

**Profile storage/identity conventions** (`src/services/redraft_engine_v1_service.py`): one JSON file per profile at `<redraft_root>/profiles/<profile_id>.json`. `LeagueProfile` identity = internal `profile_id` (uuid4) + external `(provider: str = "local", provider_league_id: str|None = None)` pair. Four SEPARATE files per profile today, unified only by filename: `profiles/<id>.json` (settings), `sleeper_imports/<id>.json` (Sleeper receipt — what `_active_sleeper_context()` actually reads), `espn_flaim_snapshots/<id>.json` (future ESPN data, schema exists, no real file ever produced yet), `draft_boards/<id>.json` (+ `.backup.json`). Active-profile selection: two independent single-marker files, deliberately not shared — `<redraft_root>/active_profile.json` (Redraft) and `<dynasty_league_root>/active_league_profile.json` (Dynasty), citing worktree isolation.

**`EspnFlaimSnapshot` is a ready-made target schema** for a future ESPN canonical snapshot (roster/scoring/player-pool with honest completeness flags, no standings field at all) — fully designed and unit-tested but carries zero real data; treat as authoritative/reusable rather than redesigning from scratch, but note it directly encodes the OLD July findings (structurally rejects COMPLETE free-agent coverage, excludes transactions) that the new Sept-22 evidence would require revising if confirmed.

---

## PHASE 0.5 — Current in-season pipeline capability (for the competitor gap comparison)

All INSPECTED CODE (see `docs/codex/waiver_night_hardening_20260922/` research; full detail retained in the completed subagent transcripts, summarized here):

- **Weekly projections** (`weekly_projection_service.py` + `weekly_projection_provider_service.py`): single point-estimate per player per week (no floor/median/ceiling anywhere), sourced from one undocumented Sleeper endpoint. League-exact scoring for QB/RB/WR/TE; honest 3-tier exact/partial/fallback scoring for K/DST (`NWR_LEAGUE_SCORING_KDST_WEEKLY` / `..._PARTIAL` / `SLEEPER_PROVIDER_SCORING`). Real provider-interface seam already exists (`default_weekly_projection_provider()`) but only one provider (Sleeper) is wired. Schema-validates every fetch, treats a collapsed payload as a FAILURE not a legitimate zero, short-TTL cache, ≤36h stale-snapshot ceiling with explicit `freshness="STALE"` labeling — never silently re-serves stale as live. Test coverage: MODERATE (28 tests across the pair).
- **Start/Sit** (`weekly_lineup_optimizer_service.py`): full legal-lineup optimizer (not binary), proven-optimal greedy pass cross-checked against brute-force enumeration in its own tests. Real locked/kickoff-derived pinning, bye/injury via the same shared status-override layer used at draft time, reserve/taxi hard-exclusion, close-call margins with a named bench alternative, and a documented real bug fix ("Zay Flowers case") so a missing bench projection is reported `UNKNOWN` rather than fabricated as a 0 point delta. Zero opponent/matchup/SOS signal anywhere. Test coverage: THOROUGH (19 tests / 516 lines).
- **Waivers** (`waiver_engine_service.py`): ranks by the governed, frozen `marginal_roster_utility_v2` (REST_OF_SEASON mode) or a real recomputed legal-lineup gain via the Start/Sit optimizer (THIS_WEEK mode) — two explicit, never-blended modes. Same-context add/drop pairing (a documented real bug fix — add and drop used to be compared against two different roster contexts). FAAB bids: contextual percentile-of-pool pricing with an urgency multiplier and season-lateness taper, two honestly-distinct $0 floors (unmatched identity vs. computed-nonpositive-value), explicitly disclosed as NOT calibrated against real historical auction outcomes. Every candidate carries a "why" explanation. Zero schedule/SOS signal, zero "likely competition for this bid" signal (both disclosed omissions). K/DST entirely out of scope for this model by design (`OUT_OF_RANKED_MODEL_SCOPE`, distinct from an identity-resolution failure). Test coverage: THOROUGH (36 tests / 833 lines).
- **K/DST streaming** (`fantasypros_kdst_consensus_service.py`): pure FantasyPros ECR ordering, gated behind an owner-supplied API key (no key → `provider_status().configured=False`, no live call attempted). No point projection, no matchup/weather/Vegas-total signal. This module also assembles the real Sleeper free-agent pool used across Redraft (`sleeper_free_agent_pool()` — the SAME pool `waiver_engine_service.py` consumes, live every call, joined to NWR's own governed ranking, `rankingAuthority: "NWR REDRAFT RANKING"` vs `"UNRANKED"` when unmatched). Test coverage: MODERATE-THOROUGH (21 + 4 adjacent files).
- **Weekly Home** (`desktop_facade.redraft_weekly_home_actions`, ~line 5706 — no standalone service file): a composition/aggregation layer over Start/Sit, Waivers (REST_OF_SEASON), Trade Finder, K/DST Streamer, and Free Agents — fixed category priority ordering, explicitly NOT a fabricated cross-category numeric score. Embeds ONE shared `leagueSnapshotId` across sub-payloads (replacing an earlier no-consistency-guarantee design). Per-request Sleeper HTTP dedupe cache (not cross-request). Degrades honestly per-section (`unavailableSections`) rather than failing the whole response. Test coverage: THOROUGH for this specific composition/caching contract (8 tests across 2 files).
- **Data freshness disclosure**: TWO separate real systems — a broad season/draft-pipeline GREEN/YELLOW/RED dashboard (`data_health_dashboard_service.py`) and an inline per-response weekly-projection freshness flag (LIVE/STALE with disclosed issues, in `weekly_projection_provider_service.py`). No single unified "how fresh is everything" surface exists.
- **ESPN/Flaim**: no functional live pipeline exists — schema/parser/design-skeleton only (see Phase 0.3). Every in-season tool above is Sleeper-only in practice today.
- **Multi-league support**: NONE observed at the Weekly Home / waiver / start-sit layer — one active profile at a time (single `active_profile.json` marker), no evidence of a cross-league aggregated view.

---

## COMPETITOR RESEARCH — pointer + honest comparison

Full competitor findings: `docs/codex/waiver_night_hardening_20260922/COMPETITOR_RESEARCH.md` (FantasyPros My Playbook/Waiver Planner/Waiver Assistant/Start-Sit, Draft Sharks Free Agent Finder/Who to Start, RotoWire My Leagues, Footballguys waiver tools/League Dominator, Sleeper native, ESPN native — sourced via WebSearch/WebFetch against official/help-center pages, 2026-09-22).

**Genuine gaps (confirmed by Phase 0 code reading — not something NWR already does):**
1. **No floor/median/ceiling anywhere** — `weekly_projection_service.py` produces a single point estimate only. Draft Sharks and RotoWire both build this in as first-class with a user-adjustable safety/upside slider. This is the single clearest, most confirmed gap.
2. **No bye-week / strength-of-schedule look-ahead signal** — explicitly disclosed as absent in `waiver_engine_service.py`'s own docstring. Draft Sharks makes this a first-class, separately-sortable dimension on both weekly and ROS lenses.
3. **No opponent/matchup context anywhere** (Start/Sit or Waivers) — Draft Sharks' "Who to Start" shows opponent positional rank + an "Adjusted Points Allowed" figure per matchup; NWR has nothing comparable.
4. **No "trending"/consensus-add-rate signal** — RotoWire's "most selected" tag and the broader Sleeper-ecosystem pattern (third-party add-rate-spike tools exist specifically because Sleeper's own native UI under-serves this) both validate this as a real wanted signal NWR doesn't have.
5. **No multi-league one-screen view** — table stakes at the premium tier for FantasyPros/RotoWire/Footballguys; NWR's architecture is single-active-profile by design today (confirmed architecturally, not just a UI gap — see Phase 0.4).
6. **FAAB bids are dollar-based, not also expressed as % of remaining budget** — Footballguys frames bid guidance as % of budget specifically because it generalizes across leagues with wildly different total FAAB pools; NWR's percentile-of-pool dollar heuristic doesn't appear to normalize to remaining-budget %, per the data-pipeline research (not 100% confirmed absent — flagged for Worker 2 to verify against the real LIVE-budget code path).
7. **No integrated news/injury headline feed inside the decision surface** — RotoWire shows this in the same screen as its waiver/lineup tools; NWR's status-override system (SEASON_OUT/NOT_WITH_TEAM/etc.) is a real signal feeding decisions, but it's not the same as a visible, browsable news feed a user reads for context.

**Areas where NWR is already competitive or arguably stronger (do not treat these as gaps — confirmed by Phase 0 code reading, not just doc claims):**
- Drop-replacement is already shown as a same-context paired add+drop scenario (`pair_add_drop`), matching FantasyPros' Waiver Assistant framing exactly, with a documented real bug fix (mismatched-context comparison) behind it.
- Weekly-vs-ROS is already a first-class, never-blended explicit mode split (`WaiverMode.THIS_WEEK` vs `REST_OF_SEASON`), and K/DST streaming is already a fully separate dedicated tool — functionally matching Draft Sharks' three-lens (weekly/ROS/streamer) framing, just implemented as separate tools/modes rather than one sort-picker UI.
- Start/Sit's locked-player/bye/injury/reserve/taxi handling, proven-optimal-vs-brute-force test discipline, and honest missing-projection handling (never fabricates a point delta) is more rigorous than anything explicitly documented in the competitor research — none of the six competitors' public docs mention taxi/reserve-slot handling or a never-fabricate-delta discipline.
- Data freshness disclosure (dual system: dashboard + inline LIVE/STALE flag, schema/coverage-collapse validation, 36h stale ceiling, never-silently-serve-stale) is real and arguably more rigorous than most competitors' vaguer "event-driven alert" framing — though NWR lacks a single unified freshness surface (see gap list is NOT the right place for this — it's a genuine strength with one polish opportunity, not a gap).
- NWR's `transaction_direction: NOT_ENABLED` hardcoded-never-write posture, and the complete absence of any parallel transaction ledger, is a DELIBERATE and stricter position than any of the six competitors (all of whom either submit directly to the host or are the host) — this is a product-boundary choice already made and confirmed correctly enforced, not a gap to close.

---

## Real-leagues verification (LIVE OBSERVATION against this worktree's own `local_exports/redraft_v1/profiles/*.json` — NOT the owner's real AppData install, which prior-cycle ledgers document as fully isolated from this worktree)

All 4 real leagues from the dispatch prompt check out exactly:
1. Fantasy Gamers — Sleeper, `1312983576827920384`, **team_count: 10** in this worktree's profile (dispatch prompt says roster 9 — minor discrepancy, likely referring to the owner's specific roster/team slot number vs. league team_count; not independently reconciled, flag for next worker).
2. Las Vegas Enginerds — Sleeper, `1344772855908290560`, team_count 10. Matches.
3. 2026 KHA High Stakes League — ESPN, `provider_league_id: null` in the profile JSON itself (matches prior-cycle "genuinely UNDETERMINED, profile untouched" finding exactly), team_count 16. Matches.
4. 403 N 18th and friends — ESPN, `provider_league_id: null` in the profile JSON (even though the real ID `1009373442` is independently confirmed elsewhere in the codebase per `docs/codex/connection_update_20260919/LEDGER.md` — consistent, not contradictory), team_count 8. Matches.

Team-name spot checks confirmed real: "Spencer's Smart Team" (403 N 18th) found verbatim in the connection-update ledger; "Colety Crusaders" found in `sample_data/kha_real_draft_2026/`.

**Two additional `provider: local` profiles exist** in this worktree's `local_exports/` not part of the 4-league framing — not chased further (out of scope), flagging their existence for whoever next touches profile listings.

---

## OPEN ISSUES FOR NEXT WORKER(S)

1. **Formal re-audit of the September 22 Flaim evidence** (free-agents "noisy/incomplete" and transactions "unsafe" July findings, both potentially stale per the new reported evidence) — explicitly NOT done by this worker, needed before `espn_flaim_snapshot_service.py`'s schema/parser (which currently structurally rejects COMPLETE free-agent coverage and excludes transactions) or `CAPABILITY_AUTHORIZATION_MAP.md` can honestly change.
2. **FAAB % of remaining-budget normalization** — verify whether `waiver_engine_service.py`'s real LIVE-budget code path already does this or not; if not, evaluate adding it (Footballguys precedent).
3. **Bye-week/SOS signal absence** in both Start/Sit and Waivers — real, disclosed, confirmed gap; evaluate priority.
4. **Trending/consensus-add-rate signal absence** — real, confirmed gap.
5. **Multi-league one-screen view** — architecturally absent today (single active-profile-at-a-time design in both Redraft and Dynasty); likely a large-scope item for a dedicated future worker, not a quick fix.
6. **`_active_sleeper_context()` (desktop_facade.py:7813) is Worker 3's highest-leverage, highest-risk refactor target** — step 2 is already provider-neutral, step 3 hard-codes Sleeper-only because all 11 callers do direct `SleeperHttpClient` fetches with zero ESPN/Flaim live-fetch equivalent. Widening the gate without giving each of the 11 callers a real non-Sleeper path (or ESPN-snapshot-backed substitute) will break real behavior.
7. **No shared canonical "LeagueSnapshot" data-payload class** exists between Redraft (`LeagueWorkspaceContext`, hash-only) and Dynasty (`DynastyLeagueSnapshot`, real Sleeper-only payload) — Worker 3 needs to design one, likely by extending `LeagueWorkspaceContext` with a real data payload and reconciling it against `DynastyLeagueSnapshot`'s shape.
8. **`tests/test_desktop_application_api.py::test_facade_has_no_streamlit_or_app_component_dependency` currently fails** (one of the Flaim cycle's own reported "4 pre-existing failed" tests) — a genuine, open, not-yet-closed architectural-separation gap between the legacy `app/` Streamlit prototype and the live `desktop_facade.py`; not a new regression, but worth a dedicated future worker rather than continued deferral.
9. **`scripts/refresh_espn_flaim_snapshot.py` remains a stub** (`NotImplementedError`) pending real Flaim OAuth-authenticated session access — needs a worker with real `mcp__flaim__*` tool access, cross-referencing item 1 above before writing real fetch logic.
10. **Minor unreconciled discrepancy**: Fantasy Gamers' real profile shows `team_count: 10` where the dispatch prompt said "team/roster 9" — likely just referring to the owner's specific roster slot, not a real inconsistency, but not independently confirmed this pass.
11. **Two extra `provider: local` profiles** exist in `local_exports/redraft_v1/profiles/` beyond the 4 named real leagues — not investigated, flag for whoever next audits profile listings.
12. A third, previously-undocumented backup dir (`local_exports.backup-20260917T224444Z/`) was noted by a research subagent reading the prior Flaim ledger (dispatch prompt said "2 known backup dirs"); harmless and additive, but flag the discrepancy for the closure worker's own `git status` sanity check.

---

# WORKER 2 — FULL WEEK-TO-WEEK CAPABILITY MATRIX (2026-09-22)

Worker 2 dispatch HEAD: `cc1a7f95` (Worker 1's docs-only commit). Worker 2 completion HEAD: see FILES CHANGED at bottom of this section. Read-mostly + live-read-only verification pass, as directed. No `marginal_roster_utility_v2`, governed valuation, or `governed_asset_registry_service.py` valuation code touched. No Sleeper/ESPN writes attempted anywhere (every write-capable-looking action below was either a profile-local `activate` call or a documented zero-write Sleeper `import`/re-`import`, byte-diff-verified). No Flaim MCP tools invoked.

Methodology tags used below: **INSPECTED CODE**, **ACTUAL TEST RESULT**, **LIVE OBSERVATION** (a real request against the real running backend tonight, or a real Chrome/curl round trip), **INFERENCE**.

## Dev processes status

**LIVE OBSERVATION.** No stale PIDs from any prior session were found (`Get-CimInstance Win32_Process` filtered on `*prospective-outcomes-v1*` returned nothing at the start of this pass — nothing to kill, nothing to trust blindly). Started a fresh pair via `desktop/scripts/nwr_release_gate_smoke.ps1 -Mode redraft -KeepRunning -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety`:
- Backend: real Python desktop API, PID 26540, `python.exe ... scripts\run_nwr_desktop_api.py --host 127.0.0.1 --port 18742 --mode redraft --repo-root C:\NWR\prospective-outcomes-v1` — confirmed alive and listening (port 18742 `Test-NetConnection` = True) at the end of this pass.
- Frontend: `vite preview` on port 1422, PID 19284 (`cmd.exe` wrapping `npx vite preview --port 1422 --strictPort`) — confirmed alive and listening (port 1422 = True) at the end of this pass.
- The smoke script itself did one real, read-only Sleeper import for Fantasy Gamers (league `1312983576827920384`) with a real before/after byte-diff against `api.sleeper.app` — **IDENTICAL, 0 writes confirmed** (the script's own built-in proof, not just an assertion).
- The smoke script's own packaging-gate step reported a real, pre-existing, unrelated finding: `cargo check` fails for `desktop/crates/nwr-desktop-runtime` (`exit code 0xc0e90002`, a Rust/MSVC toolchain-level failure, not the known privacy/resource-allowlist gate, which itself PASSED). This is a packaging/toolchain issue, not a functional regression in anything audited below — flagged for whoever next attempts a native build, not investigated further here (out of scope for a read-mostly functional audit).
- Every subsequent request in this section went directly to the real backend at `http://127.0.0.1:18742` with `Authorization: Bearer nwr-desktop-development-token-only-000000000000` and `Origin: http://127.0.0.1:1422` (the dev token/origin the smoke script itself uses) — real HTTP round trips against the real facade, real `SleeperHttpClient` calls, real governed ranking/projection code, nothing mocked. Active profile was switched between the 4 real leagues via the real `POST /api/v1/redraft/profiles/{id}/activate` endpoint. **Left the backend/frontend running (`-KeepRunning`) with Fantasy Gamers as the final active profile** for the next worker or the owner.

**Real profile IDs discovered this pass** (`local_exports/redraft_v1/profiles/*.json`, INSPECTED + LIVE-confirmed via `/api/v1/bootstrap`'s `activeProfile`/`leagueCapabilities` after activating each):
| League | Profile ID | Provider | Provider league ID |
|---|---|---|---|
| Fantasy Gamers | `941b99ade350410391b1b67c0890af79` | sleeper | `1312983576827920384` |
| Las Vegas Enginerds | `6687d2b3aa21450ea0fc9e1792d461ff` | sleeper | `1344772855908290560` |
| 2026 KHA High Stakes League | `fb1c49402c7644a99120197d41344bbb` | espn | `null` (undetermined in this profile record, per Worker 1) |
| 403 N 18th and friends | `4b4a990faf124ce7a5d612537ba5943b` | espn | `null` in this profile record (real ESPN ID `1009373442` is recorded elsewhere in the repo, per `connection_update_20260919/LEDGER.md`, not in this JSON) |

Two additional `provider: local` profiles (`9d67837e...`, `c5c77f62...`) exist and were left untouched — out of scope, matches Worker 1's flag.

## Correction to Worker 1's architecture map (real, live-verified)

Worker 1's Phase 0.4 lists `redraft_data_health` (desktop_facade.py:5543) as one of the 11 callsites that duplicate the hard `provider == "sleeper"` gate and therefore 409s for ESPN profiles. **LIVE OBSERVATION tonight contradicts this for `redraft_data_health` specifically**: activating both ESPN profiles (KHA, 403 N 18th) and calling `GET /api/v1/redraft/data-health` returned **HTTP 200**, not 409, both times — the endpoint instead degrades honestly per-category (`LEAGUE_SYNC: NOT_APPLICABLE/LOCAL_ONLY — "This profile is local/manually managed; no live provider sync."`, `WEEKLY_PROJECTIONS: NOT_APPLICABLE/UNKNOWN — "No active Sleeper league."`, `DECISION_ENGINE: NO_ACTIVITY`, while `ROS_PROJECTIONS`/`PLAYER_STATUS`/`SNAPSHOT` stay `OK` since those aren't Sleeper-gated). By contrast, `GET /api/v1/redraft/my-roster` on the same two ESPN profiles genuinely did 409 both times with `{"code":"SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED","message":"No verified league data available for this league. Import league data (e.g. via Sleeper) before using this tool."}`. So the real behavior is **mixed, not uniform**: some of the 11 listed callsites hard-409, at least one (`data_health`) actually degrades gracefully already. This is a genuinely good finding (an ESPN profile owner gets an honest, informative Data Age screen tonight, not a wall of errors) and a real correction Worker 3 should account for rather than assuming all 11 callsites behave identically when widening `_active_sleeper_context()`.

Also worth noting: the smoke script's own documented "KNOWN ISSUE" (`POST /api/v1/redraft/weekly-home-actions` returns HTTP 500 due to a K/DST `positions` list-vs-dict `AttributeError`) did **NOT reproduce** tonight — `weekly_home_actions_week1` returned **200** in tonight's real run, and a direct re-call for Fantasy Gamers week 3 also returned 200 with real, correctly-structured `START_SIT`/`START_SIT_CLOSE_CALL`/`WAIVER` action rows. Either that bug was fixed in an intervening commit (not independently bisected this pass) or it's real-data-dependent and simply didn't trigger for this league/week. Flagging as a positive, not re-asserting the old bug as still open.

## Capability matrix

Legend: **LV** = LIVE VERIFIED (real request against the real running backend tonight), **IU** = IMPLEMENTED UNVERIFIED (real code path exists, confirmed by inspection and/or a prior same-session smoke run, but not independently re-exercised by me this pass), **PARTIAL** = real but incomplete/degraded, honestly disclosed, **BLOCKED** = real, honest hard failure (409) or architecturally gated, **MISSING** = genuinely absent from the codebase (not a league-specific gap), **N/A** = not applicable to this specific league's real configuration.

| # | Row | Fantasy Gamers (Sleeper) | Las Vegas Enginerds (Sleeper) | KHA High Stakes (ESPN) | 403 N 18th (ESPN) |
|---|---|---|---|---|---|
| 1 | Profile identity | LV — bootstrap `hasVerifiedIdentity:true`, real name/provider/teamCount 10, 0-write import byte-diff proof | LV — same, teamCount 10, real name | PARTIAL — owner-entered `league_name` only, `provider_league_id:null`, no live ESPN verification possible | PARTIAL — same; real ESPN ID `1009373442` known elsewhere in repo but not in this profile record |
| 2 | Roster | LV — real 15-player roster, real names/starter flags/identity-match status | LV — real 24-player roster, correct for this league's slots | BLOCKED — `my-roster` 409 `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` (live-tested tonight) | BLOCKED — same 409, live-tested tonight |
| 3 | Roster slots | LV — QB1/RB2/WR2/TE1/FLEX1/K1/DST1/Bench6 = 15, matches `rosterSlotsTotal:15` | LV — QB1/RB2/WR3/TE1/FLEX2/K1/DST0/Bench14 = 24, matches `rosterSlotsTotal:24` | PARTIAL — owner-entered config only (bench4/flex2/rb1/wr1/k1/dst1), never live-synced | PARTIAL — owner-entered config only (bench7/flex1/rb2/wr2/k1/dst1), never live-synced |
| 4 | Reserve/IR | IU — code hard-excludes `is_reserve`/`is_taxi` (`weekly_lineup_optimizer_service.py`), but neither live roster tonight had anyone on reserve/taxi to exercise it | IU — same code path, same caveat | BLOCKED — no roster reachable at all | BLOCKED — same |
| 5 | Scoring | LV — real Sleeper scoring pulled live (0.04/yd pass, 1.0 PPR, 6pt TD, -2 INT/fumble) | LV — real, genuinely DIFFERENT scoring (0 PPR, 4pt TD, -1 INT/fumble, 0.0333/yd pass) — confirms per-league, not shared-default | PARTIAL — owner-entered config only; CAPABILITY_AUTHORIZATION_MAP.md caps ESPN scoring at PARTIAL/UNKNOWN even once Flaim-live | PARTIAL — same |
| 6 | FAAB budget | LV — real `faabContext`: `isFaabLeague:false`, waiver-priority `waiverPosition:9` | LV — real `faabContext`: `isFaabLeague:true`, `$100` total/remaining, 13 weeks remaining, `source:SLEEPER_LIVE` | BLOCKED — no live budget read possible | BLOCKED — same |
| 7 | Waiver settings | PARTIAL — `isFaabLeague` + numeric `waiverPosition` surfaced; the underlying mechanism name (rolling vs. reverse-standings) is not modeled/labeled anywhere (grepped `waiver_engine_service.py`, zero matches) | PARTIAL — same | BLOCKED | BLOCKED |
| 8 | Player availability | LV — real, league-filtered free-agent pool (`free_agents` 200, live Sleeper read joined to governed ranking) | IU — same pipeline, not independently re-called this pass | BLOCKED (structurally capped even once live: schema rejects `COMPLETE` free-agent coverage) | BLOCKED — same |
| 9 | Waiver status (on-waivers vs. free-agent state) | MISSING — grepped `src/` for `on_waivers`/`pending_waiver`/`process_waiver`, zero matches anywhere; not provider-specific | MISSING | MISSING | MISSING |
| 10 | Waiver clear time | MISSING — same grep, zero matches | MISSING | MISSING | MISSING |
| 11 | Recent league transactions | MISSING — no transactions endpoint exists in `server.py`/`desktop_facade.py` at all | MISSING | BLOCKED (double-blocked: July Flaim finding + independent no-provider-writes rule) | BLOCKED |
| 12 | Weekly projections | LV — real live Sleeper fetch, 9421 rows/1107 nonzero, `freshness:LIVE`, real missing-projection case observed (Caleb Williams) | LV — same pipeline, all 10 starters had known values this week | BLOCKED — one of the 11 Sleeper-gated callsites | BLOCKED |
| 13 | ROS projections | LV — `data-health` shows `ROS_PROJECTIONS: OK/CURRENT`; real `rosReplacementValue`/`rosOverallRank` on every waiver candidate | LV — same, real distinct numbers for this roster | PARTIAL — the snapshot itself isn't Sleeper-gated (`ROS_PROJECTIONS: OK` even for ESPN profiles per the data-health correction above) but every consumer (waivers, lineup) that surfaces it is still 409-blocked | PARTIAL — same |
| 14 | Schedule (bye/SOS look-ahead) | MISSING for in-season decision surfaces — bye/schedule code exists elsewhere (draft-time `nflverse_schedule_context_display_service.py`) but not wired into `weekly_lineup_optimizer_service.py`/`waiver_engine_service.py` (grepped, zero bye-specific logic in either) | MISSING | MISSING | MISSING |
| 15 | Opponent | LV — real week-3 matchup, `opponentTeamName:"Ben Luvs My Johnson"`, full real 10-team standings + playoff bracket | LV — real week-3 opponent `"WhoDat?"` | BLOCKED — `league-workspace-context` is one of the 11 gated callsites | BLOCKED |
| 16 | Injury/status | PARTIAL — real, specific, individually-sourced overrides returned live (e.g. real player OUT_FOR_SEASON/torn ACL, another NOT_WITH_TEAM/released with dated reasons); data-health honestly discloses "No automated injury/practice-report feed exists in this repository" | PARTIAL — same global override feed | BLOCKED — same status endpoint requires the gate (live-confirmed 409 pattern applies) | BLOCKED |
| 17 | Start/Sit | LV — real week-3 optimization; live-reproduced the documented "Zay Flowers case" honesty discipline verbatim (a real missing Caleb Williams projection tonight correctly reported `UNKNOWN_MISSING_BENCH_PROJECTION` rather than a fabricated delta) AND a real actionable call (START Zay Flowers +6.5) | LV — real week-3 optimization, all known projections, correct call under this league's distinct non-PPR scoring (+4.2 Zay Flowers) | BLOCKED — 409 live-confirmed tonight | BLOCKED — 409 live-confirmed tonight |
| 18 | Waivers | LV — both `THIS_WEEK` and `REST_OF_SEASON` modes returned real ranked candidates against this real roster/pool (top add Tyrone Tracy, marginal utility 9.72) | LV — real ranked candidates (top add Kimani Vidal, marginal utility 18.73) | BLOCKED | BLOCKED |
| 19 | Drop candidates | LV — real ranked drop list with full quantitative, human-readable explanations (real nflverse flex-worthy-week rate cited per candidate) | LV — same structure, real numbers | BLOCKED | BLOCKED |
| 20 | Add/drop net utility | LV — real `addDropPairings` with `addUtilityVsPostDropRoster`/`dropUtilityVsPostDropRoster`/`netMarginalUtility` internally consistent (12.74 = 9.72 − (−3.02)), `contextLabel:SAME_CONTEXT_MARGINAL_COMPARISON` confirms the documented same-context bug fix is live | IU — same structure present, arithmetic not independently re-verified this pass | BLOCKED | BLOCKED |
| 21 | FAAB recommendations | N/A — correctly returns null FAAB bid fields rather than fabricating a dollar amount for this non-FAAB league (honest per-league gating, not a bug) | LV — real bid range ($28–$46 of $100 remaining), urgency `MEDIUM`, plain-English rationale. **Real gap found**: see below | BLOCKED | BLOCKED |
| 22 | K streamer | LV — real FantasyPros-ECR K streamer; correctly shows the owner's real rostered K (`Ka'imi Fairbairn`) as `YOUR_STARTER`, a real available K as top ADD | LV — same pipeline for this league's real rostered K (Cam Little) | BLOCKED (INFERENCE — shares the Sleeper free-agent-pool dependency per Worker 1's ledger; not independently re-tested) | BLOCKED (INFERENCE) |
| 23 | DST streamer | LV — same `kdst` 200 response covers DST alongside K | N/A — this league's real roster config has `dst:0` (no DST slot at all) — structurally not applicable, not a bug | BLOCKED | BLOCKED |
| 24 | Trade analysis | IU — endpoint exists, confirmed 200 in tonight's own smoke run for this league; not independently re-called with specific player IDs this pass (prioritized Trade Finder) | IU — same, not independently re-called | BLOCKED | BLOCKED |
| 25 | Trade finder | LV — real candidate trade vs. a real opponent (`Bill's Sleepers`), real players both sides, real `myNetMarginalUtility:19.3` | LV — 200 confirmed live tonight, content not deep-inspected this pass | BLOCKED | BLOCKED |
| 26 | Opponent rosters | LV — full real rosters for all 9 other real teams, per-player identity-match status | IU — same endpoint, one of the 11 gated callsites confirmed working for FG tonight; not independently re-called for LVE this pass | BLOCKED | BLOCKED |
| 27 | Data age | LV — real 7-category `data-health` (`LEAGUE_SYNC`/`ROS_PROJECTIONS`/`WEEKLY_PROJECTIONS`/`MARKET_ADP`/`PLAYER_STATUS`/`DECISION_ENGINE`/`SNAPSHOT`), each independently timestamped | LV — same 7 categories; **real per-profile difference found**: `MARKET_ADP` was `UNAVAILABLE/UNKNOWN` here vs. `OK/CURRENT` for Fantasy Gamers — genuine, honestly disclosed, not a shared default | PARTIAL — 200 (NOT 409 — see correction above), degrades honestly per-category | PARTIAL — 200, same graceful degradation, and its `MARKET_ADP` is `OK/CURRENT` (real ADP already imported for this profile, unlike KHA) |
| 28 | Refresh mechanism | LV — the smoke script's own Sleeper re-import is a real, safe, idempotent refresh path, byte-diff-verified 0 writes; `weekly-projections` also has a `forceRefresh` flag | LV — same refresh path (not independently re-exercised for this league this pass, same code) | MISSING — `scripts/refresh_espn_flaim_snapshot.py` unconditionally raises `NotImplementedError` | MISSING — same |

## P0 row findings (deep dive)

- **Start/Sit** — the strongest result of the night. Both real Sleeper leagues produced real, correct, honestly-hedged week-3 recommendations live. Fantasy Gamers specifically reproduced the documented "Zay Flowers case" discipline against a *real, currently-missing* projection (Caleb Williams) rather than a synthetic test fixture — this is the single best piece of evidence in this pass that the never-fabricate-a-delta rule holds in production, not just in unit tests.
- **Waivers / Drop candidates / Add/drop net utility** — all three are the same real decision envelope per league; verified real, internally-consistent arithmetic (net = add − drop, both computed against the *same* post-drop roster context, confirming the documented same-context bug fix is genuinely live) for Fantasy Gamers; Las Vegas Enginerds structurally confirmed present, not independently re-verified arithmetic.
- **FAAB recommendations** — Las Vegas Enginerds (the one real FAAB league) produced a real, sane bid range live ($28–$46 of $100 remaining). **Real gap found and precisely localized**: `waiver_engine_service.py` (lines ~568–700) computes `bid_low_pct`/`bid_high_pct` (the bid range as a literal percent of `remaining_budget_dollars`) internally, but grepping the rest of `src/` shows those two fields are never read anywhere outside that one file — they don't reach `desktop_facade.py`'s serialization or the API response (only `faabBidLowDollars`/`faabBidHighDollars` do). This closes Worker 1's open issue #2 with a precise answer: the pricing math **already is** budget-relative (it scales with the real remaining budget), it's just that the explicit percent-of-budget figure is silently computed and then thrown away before it ever reaches the owner — a small, well-localized, low-risk fix for a future worker (surface `bidLowPct`/`bidHighPct` alongside the existing dollar fields), not a design gap.
- **K/DST streamer** — real, live FantasyPros ECR data for both Sleeper leagues, correctly aware of each league's actual rostered K (`YOUR_STARTER` framing) and correctly recognizing Las Vegas Enginerds has no DST slot at all (`dst:0`), so "DST streamer" is structurally N/A there, not broken.
- **Data age** — real dual-system freshness disclosure confirmed live for all 4 leagues (see the graceful-ESPN-degradation correction above), plus a real, honest, per-profile `MARKET_ADP` divergence between the two Sleeper leagues that an owner should know about before waiver night (Las Vegas Enginerds has no ADP imported; Fantasy Gamers and 403 N 18th do).

## Real bugs or gaps found during this audit

1. **FAAB percent-of-remaining-budget figure computed but never surfaced** (`waiver_engine_service.py` `bid_low_pct`/`bid_high_pct` — see above). Real, precise, low-risk to fix.
2. **Worker 1's architecture map overstates uniformity of the 11 Sleeper-gated callsites**: `redraft_data_health` in practice degrades gracefully (200) for ESPN profiles rather than 409ing like `my-roster`/`weekly-lineup`/`waivers`/`league-workspace-context` genuinely do. Real, live-verified, worth correcting before Worker 3 assumes all 11 behave identically.
3. **The smoke script's documented `weekly-home-actions` 500 bug did not reproduce tonight** (real 200 for Fantasy Gamers week 3, both via the automated smoke pass and a direct manual re-call). Either already fixed or real-data-dependent; not bisected further this pass — flagged as a positive finding, not re-opened as a live bug.
4. **Waiver status / waiver clear time / recent transactions are genuinely absent for every provider**, including Sleeper — not an ESPN-specific gap. An owner watching a real waiver claim tonight has no in-app way to see whether it's still pending, when it clears, or what happened in recent league transactions; they'd have to leave the app and check Sleeper/ESPN natively for that specific information.
5. **Schedule/bye/SOS look-ahead is genuinely absent from the live in-season decision surfaces** for all 4 leagues (confirmed by direct grep of both `weekly_lineup_optimizer_service.py` and `waiver_engine_service.py`), even though bye/schedule-aware code exists elsewhere in the codebase for draft-time context — it's just not wired into Start/Sit or Waivers. Matches Worker 1's competitor-research gap #2 with concrete code-level confirmation.
6. **Unrelated, incidental**: `cargo check` fails for `desktop/crates/nwr-desktop-runtime` (real MSVC toolchain error, not the known resource-privacy gate, which passed). Not investigated further — out of scope for a functional/data audit, flagged for whoever next attempts native packaging.

## Open issues for Worker 3 (provider-neutral canonical league-state architecture)

1. All of Worker 1's original 12 open issues stand; add to them:
2. Do not assume all 11 `_active_sleeper_context()` callsites behave identically when widening the gate — `redraft_data_health` already has its own honest graceful-degradation path that doesn't even call the shared gate the same way the hard-409 callsites do; study it as a template for how the other 10 *could* degrade instead of hard-blocking, rather than just removing the 409.
3. Surface `bid_low_pct`/`bid_high_pct` from `waiver_engine_service.py`'s `FaabBidRange` through `desktop_facade.py` and the API response — cheap, real, already-computed, currently discarded.
4. Waiver status (pending/on-waivers vs. free-agent) and waiver-clear-time are unmodeled for every provider today, not just ESPN — if a canonical `LeagueSnapshot` is designed, this state machine (ESPN's overnight-clear model vs. Sleeper's simpler model, per `COMPETITOR_RESEARCH.md` theme #10) needs a real home in it, since it's currently nowhere.
5. Recent-league-transactions has no endpoint anywhere (Sleeper or ESPN) — confirm with the owner whether this is an intentional non-goal (consistent with the project's strict no-parallel-transaction-ledger posture) before treating it as a gap to close.

---

## FILES CHANGED THIS PASS

- `docs/codex/waiver_night_hardening_20260922/COMPETITOR_RESEARCH.md` (new, Worker 1)
- `docs/codex/waiver_night_hardening_20260922/LEDGER.md` (new by Worker 1, this Worker 2 section appended)

No product code, tests, or existing docs (other than this ledger) modified. Read-mostly + live-read-only verification pass, as directed. `local_exports/worker2_*.json` and `local_exports/release_gate/20260922T065449Z/` are untracked local artifacts from this pass (real request/response captures), not committed.

---

# WORKER 3 — PROVIDER-NEUTRAL CANONICAL LEAGUE-STATE BOUNDARY (2026-09-22)

Worker 3 dispatch HEAD: `9533247a` (Worker 2's capability-matrix docs commit). This is the highest-risk pass in the cycle (owner's own framing) -- product code changed, live-verified against both real Sleeper leagues after every meaningful step, per the same rigor discipline as the prior Flaim cycle's Workers 2-3. Methodology tags below: **INSPECTED CODE**, **ACTUAL TEST RESULT**, **LIVE OBSERVATION**, **INFERENCE**.

## Scope decision (read this first)

The owner's Phase 3 directive named three target callers: My Roster, Start/Sit (`redraft_weekly_lineup`), and "one more of your choice," expecting 2-3 real conversions. After building the canonical object and deeply inspecting `redraft_weekly_lineup`, I made a deliberate, documented scope cut: **only `redraft_my_roster` was fully converted tonight.** Reasons, concretely:

- `redraft_weekly_lineup`'s downstream pipeline (`build_roster_candidates`, `optimize_weekly_lineup` in `weekly_lineup_optimizer_service.py`) consumes FOUR distinct Sleeper-native roster lists (`players`/`starters`/`reserve`/`taxi`) and is deeply typed around `sleeper_player_id`. The existing, tested `EspnFlaimSnapshot`/`CanonicalRosterPlayer` roster-slot model (which this pass deliberately reused rather than redesigned, per the dispatch directive) only has THREE slot kinds (STARTER/BENCH/RESERVE, no TAXI) -- routing Start/Sit's real candidate-building through it would either lose real taxi-squad exclusion behavior or require redesigning the shared slot schema, both real regression risks I was not willing to take blind, this late, against the two real leagues the directive calls "the single most important constraint."
- `redraft_opponent_rosters` (my other candidate for the "third caller") delegates to `sleeper_opponent_rosters()`, a separate, already-tested function with its own row shape (`unresolvedSleeperPlayerIds`, per-opponent grouping) that a full canonical conversion would need to reproduce byte-for-byte or risk silently changing. I judged reproducing it via the new module carried real risk for a caller that (per Worker 1's architecture map, re-confirmed by me tonight) is not currently broken for ESPN in the way My Roster/Start-Sit/Waivers are -- see Corrections below.
- `redraft_my_roster`, by contrast, maps field-for-field onto `CanonicalRosterPlayer` with zero information loss (verified analytically before writing code, then confirmed by test + live round trip) -- the one caller I could convert with high confidence and no speculative schema changes.

I judged one real, deep, live-verified conversion plus a real, tested, reusable canonical object plus a precise mechanical template for the rest to be more valuable than three shallow/risky ones. This is a considered call, not a shortfall -- see "Remaining callers" below for exactly what the next worker needs to do to extend this.

## The canonical object

**New file: `src/services/canonical_league_state_service.py`** (pure, zero I/O, zero Sleeper/ESPN/Flaim calls of its own).

`CanonicalLeagueState` fields: `provider` (`"sleeper"|"espn"`), `provider_league_id`, `league_name`, `season`, `team_count`, `owner_team_id`, `owner_team_name`, `roster` (tuple of `CanonicalRosterPlayer`), `opponent_rosters` (tuple of `CanonicalTeamRoster`, real extension beyond the owner's field list, `None` unless a caller asks -- see below), `scoring` (`CanonicalScoringState`: completeness + disclosures), `faab` (`CanonicalFaabState`: is_faab_league/total/remaining/waiver_position/source, honestly `"NOT_FETCHED_THIS_REQUEST"`/`"UNKNOWN"` when not asked for or not knowable -- never fabricated), `available_player_pool` + `available_player_pool_coverage`, `acquisition` (`CanonicalAcquisitionState` -- real, hardcoded-false/null waiver-status/clear-time/transactions with an explicit disclosure string, per Worker 2's finding that this is genuinely absent for EVERY provider, not ESPN-specific; I did not fake it for Sleeper either), `current_week`, `retrieved_at_utc`, `provider_as_of_utc`, `source`, `capabilities` (embeds the existing, real, tested `LeagueCapabilities` directly -- not duplicated).

`CanonicalRosterPlayer`/`CanonicalAvailablePlayer` deliberately mirror `EspnRosterPlayer`/`EspnAvailablePlayer` (`espn_flaim_snapshot_service.py`) field-for-field, per the directive's instruction to wrap/consume that existing, real, tested schema rather than redesign it.

Two builders, both real and tested:
- `build_canonical_league_state_from_sleeper(...)` -- takes an ALREADY-FETCHED live Sleeper `rosters`/`players` response (the exact same live fetch `desktop_facade.py` always performed) and assembles the canonical shape. Performs NO network I/O itself -- `desktop_facade.py` still owns every live Sleeper call. Raises `CanonicalLeagueStateError` (with a stable `.kind` -- `MALFORMED_ROSTERS` / `OWN_ROSTER_NOT_FOUND`) for the two real failure modes, so callers translate into their own pre-existing, tool-specific `FacadeError` code/message/status rather than this module dictating one generic shape.
- `build_canonical_league_state_from_espn_snapshot(snapshot, capabilities=None)` -- pure wrap of a real, already-parsed `EspnFlaimSnapshot`. No standings, no opponent rosters (the schema doesn't model either).

**ACTUAL TEST RESULT**: `tests/test_canonical_league_state_service.py`, 10/10 passed -- pure, synthetic-fixture-only tests (Sleeper-shaped dict fixtures + one clearly-labeled-synthetic `EspnFlaimSnapshot` fixture, "Synthetic Test ESPN League (unit test fixture, not real)"). Covers: starter/bench/reserve slot classification, missing-catalog-entry fallback, opponent-roster inclusion, malformed-rosters/owner-not-found errors, the "never fabricate FAAB/pool/acquisition state" contract for both providers, and a same-shape assertion (both providers produce identical dataclass field sets).

## `redraft_my_roster` conversion (the one full conversion)

**INSPECTED CODE + ACTUAL TEST RESULT + LIVE OBSERVATION.** `desktop_facade.py::redraft_my_roster` (was: raw `rosters`/`players` Sleeper fetch inline, own-roster lookup inline, `resolve_roster_canonical_ids` called against the raw Sleeper catalog) now:

1. Calls a new shared method, `_resolve_canonical_league_state()` (`desktop_facade.py`, right after `_active_sleeper_context()`). For a Sleeper profile this performs the EXACT SAME live fetch via the EXACT SAME `_active_sleeper_context()` gate (reused, not reimplemented) -- zero behavior change to the Sleeper path by construction. For an ESPN profile it loads a real `EspnFlaimSnapshot` if one exists (`load_espn_flaim_snapshot`) and builds the canonical state from it; none exists for any real profile tonight (Flaim ingestion still pending), so it currently still 409s for ESPN -- but the architecture is now ready to serve a real snapshot automatically the moment one exists, with **no further code change to `redraft_my_roster`**.
2. Builds a synthesized single-purpose `{provider_player_id: {full_name, position, team}}` catalog from `state.roster` and feeds it into the SAME, unchanged `resolve_roster_canonical_ids` (`waiver_engine_service.py`) every other roster/opponent/free-agent identity call site already uses -- no new identity heuristic, and I verified analytically (documented in code comments) that this produces byte-identical `canonicalPlayerId`/`playerName`/`position`/`team`/sort-order results to the pre-conversion inline logic, including the exact missing-catalog-entry fallback (empty position/team, raw provider id as name).
3. Preserves every pre-existing error code/message/status exactly: `SLEEPER_REDRAFT_PROFILE_REQUIRED` (409), `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` (409), `REDRAFT_MY_ROSTER_READ_FAILED` (503, malformed rosters or network failure), `REDRAFT_MY_ROSTER_NOT_FOUND` (409, no matching roster) -- verified by dedicated regression tests, not just assumed.
4. Adds two new, more specific ESPN codes for the (narrower than I first assumed -- see Corrections below) case actually reached: `ESPN_REDRAFT_SNAPSHOT_REQUIRED` (409, verified identity but no snapshot file yet) and `ESPN_REDRAFT_SNAPSHOT_INVALID` (503, a present-but-corrupt snapshot file).

**Real extraction, zero behavior change**: `_active_sleeper_context()`'s first two steps (active-profile check, capability/verified-identity check) were pulled into a new shared `_active_profile_with_capabilities()` method, called by both the unchanged `_active_sleeper_context()` and the new `_resolve_canonical_league_state()`. Pure refactor -- same order, same codes, same messages.

### A real, pre-existing bug found and fixed while testing this

**INSPECTED CODE + ACTUAL TEST RESULT.** `_league_capabilities_for_profile` (`desktop_facade.py`, the shared helper `redraft_my_roster`'s gate, the K/DST streamer guard, and bootstrap serialization all call) caught `EspnFlaimSnapshotError` from `load_espn_flaim_snapshot` but NOT a bare `json.JSONDecodeError` (a `ValueError`) that the same function can raise for a syntactically-invalid (not just schema-invalid) snapshot file -- an uncaught exception that used to propagate all the way up through whichever caller's own generic `except (OSError, ValueError)` caught it first, producing a misleading error (e.g. `redraft_my_roster` reporting "Sleeper roster or player data could not be read" for a broken ESPN file that has nothing to do with Sleeper). Found by writing a malformed-snapshot regression test for the new ESPN path, not by inspection alone. Fixed with a one-line-wider `except` clause, matching the adjacent Sleeper-receipt read's own established pattern two lines above it. The exact same class of gap existed in `_resolve_canonical_league_state`'s own ESPN branch (only caught `EspnFlaimSnapshotError`, not the JSON-decode `ValueError`) and was fixed identically there. This is a real, live-relevant bug for whoever builds the ESPN ingestion pipeline next (Worker 4) -- a partially-written or corrupted snapshot file would previously have produced a confusing, wrong-sounding error.

### Correction to my own initial assumption (documented so Worker 4 doesn't re-derive it)

I initially assumed an ESPN profile with no snapshot would reach `_resolve_canonical_league_state`'s new `ESPN_REDRAFT_SNAPSHOT_REQUIRED` branch. **Real finding from writing the tests**: it does NOT, for either real ESPN league tonight. `_active_profile_with_capabilities()` (step 2, shared, unchanged) already rejects a profile with neither a Sleeper receipt NOR an ESPN snapshot at all -- `has_verified_identity` is False before `_resolve_canonical_league_state()`'s own ESPN-specific branch is ever reached. **LIVE OBSERVATION tonight**: activating both real ESPN profiles (KHA `fb1c49402c7644a99120197d41344bbb`, 403 N 18th `4b4a990faf124ce7a5d612537ba5943b`) and calling `GET /api/v1/redraft/my-roster` returned the EXACT SAME `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` / 409 both times -- byte-identical to Worker 2's own live-documented pre-conversion finding for this exact endpoint/leagues. **Zero regression, confirmed live, not just by code reading.** The new `ESPN_REDRAFT_SNAPSHOT_REQUIRED`/`ESPN_REDRAFT_SNAPSHOT_INVALID` codes are real and reachable, but only in a narrower edge case (verified identity via a stale/leftover Sleeper receipt file surviving a provider switch to `espn`, combined with no/broken snapshot) -- covered by dedicated tests, not reachable by either real profile tonight. This is not a gap in the fix; it just means tonight's real behavior for KHA/403N18th is provably unchanged, and the new codes are forward-looking for when a real snapshot pipeline (or a stale-receipt edge case) actually exists.

## FAAB %-of-budget fix

**ACTUAL TEST RESULT + LIVE OBSERVATION.** `waiver_engine_service.py`'s `FaabBidSuggestion.bid_low_pct`/`bid_high_pct` (already computed, per Worker 2's finding) now reach the API: `desktop_facade.py`'s waiver-candidate serialization adds `faabBidLowPct`/`faabBidHighPct` alongside the existing `faabBidLowDollars`/`faabBidHighDollars` (honestly `None` under the exact same conditions the dollar fields are `None` -- never a fabricated figure for a non-FAAB league). `desktop/packages/contracts/src/index.ts`'s `WaiverAddCandidate` (or equivalent) type updated to match, as optional fields (non-breaking). `npm run typecheck` and the full `npx vitest run` (503/503) both pass unchanged.

**LIVE OBSERVATION** against the real Las Vegas Enginerds league (the one real FAAB league, `$100` real remaining budget tonight) via `POST /api/v1/redraft/waivers {"mode":"REST_OF_SEASON"}`: 25/25 add candidates now carry both fields, e.g. top candidate Kimani Vidal `faabBidLowDollars: 28, faabBidHighDollars: 46, faabBidLowPct: 0.279, faabBidHighPct: 0.464` -- internally consistent with the dollar figures (`round(100 * 0.279) == 28`). Fantasy Gamers (non-FAAB, `isFaabLeague: false`) correctly still gets `null` for all four fields (verified by test, not re-verified live tonight since Worker 2 already live-confirmed the non-FAAB null-gating path pre-existing).

## Live verification against both real Sleeper leagues (required, most important constraint)

**LIVE OBSERVATION**, all tonight, against a freshly-restarted real backend/frontend pair (see Dev processes below -- old PIDs from Worker 2's session had already died/been replaced by the time I checked; restarted cleanly via the same `nwr_release_gate_smoke.ps1 -KeepRunning -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety` invocation Worker 2 used, including its own real, byte-diff-verified zero-write Sleeper import):

- Fantasy Gamers (`941b99ade350410391b1b67c0890af79`): `GET /api/v1/redraft/my-roster` -> 200, 15 real roster rows (Caleb Williams/QB/CHI, De'Von Achane/RB/MIA, Ka'imi Fairbairn/K/HOU as `UNMATCHED_IDENTITY` [K is out of NWR's ranked model scope, matching the documented `OUT_OF_RANKED_MODEL_SCOPE` disclosure], NE D/ST also `UNMATCHED_IDENTITY` for the same reason) -- real player set, real identity-match behavior.
- Las Vegas Enginerds (`6687d2b3aa21450ea0fc9e1792d461ff`): `GET /api/v1/redraft/my-roster` -> 200, 26 real roster rows (Lamar Jackson/QB/BAL, Cam Little/K/JAX as `UNMATCHED_IDENTITY`, same K-out-of-scope reason) -- real, distinct roster from Fantasy Gamers, confirming per-profile isolation still works. (26 vs. Worker 2's documented 24 from ~20 hours earlier -- a real, plausible in-season roster change via waivers/trades between sessions, not a bug; not independently reconciled further.)
- Las Vegas Enginerds waivers (`POST /api/v1/redraft/waivers {"mode":"REST_OF_SEASON"}`): 200, real `faabContext` (`isFaabLeague: true, totalBudgetDollars: 100, remainingBudgetDollars: 100, waiverPosition: 2, source: SLEEPER_LIVE`), 25 real priced add candidates, all now carrying real `faabBidLowPct`/`faabBidHighPct` (see above).
- KHA (ESPN, `fb1c49402c7644a99120197d41344bbb`): `GET /api/v1/redraft/my-roster` -> 409 `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` -- byte-identical to Worker 2's pre-conversion live finding.
- 403 N 18th (ESPN, `4b4a990faf124ce7a5d612537ba5943b`): same 409/same code. `GET /api/v1/redraft/data-health` on the same profile -> 200, graceful per-category degradation, byte-consistent with Worker 2's documented template (not re-derived, just re-confirmed still true post-change since `redraft_data_health` was not touched this pass).
- Final active profile left as Fantasy Gamers, matching the convention both prior workers left it in.

## Tests

**ACTUAL TEST RESULT**:
- `tests/test_canonical_league_state_service.py`: 10/10 passed (new, pure/synthetic).
- `tests/test_redraft_my_roster_canonical_state_conversion.py`: 11/11 passed (new -- Sleeper rows/sort/unmatched-identity unregressed, all 4 pre-existing Sleeper error codes unregressed, ESPN honest-block both the real (capability-gated) and edge-case (snapshot-gated) shapes, malformed-snapshot handling, no-active-profile unregressed).
- `tests/test_redraft_waivers_faab_pct_fix.py`: 2/2 passed (new).
- Full pre-existing targeted set re-run after all changes (`test_redraft_waivers_faab_context_fix.py`, `test_redraft_waivers_ir_reserve_drop_exclusion_fix.py`, `test_redraft_identity_boundary_opponent_and_trade_finder.py`, `test_desktop_facade_architecture_wiring.py`, `test_league_capability_service.py`, `test_desktop_application_api.py`): 114 passed, 4 failed -- **the exact same 4 pre-existing failures** as a `git stash` baseline run of the identical command (`test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_component_dependency` -- the last one is Worker 1's open item 8, environment/FantasyPros-key-dependent for the other two, all pre-dating this pass, confirmed via a direct `git stash`/re-run A-B comparison, not assumed).
- Frontend: `npm run typecheck` clean; `npx vitest run` 503/503 (matches the prior cycle's own reported baseline exactly).
- `ruff check` on all new/touched files: zero NEW findings beyond one pre-existing-pattern `UP035` (typing.Sequence/Mapping vs. collections.abc) that I deliberately left matching `espn_flaim_snapshot_service.py`'s own identical existing pattern (that file has the same "violation" today) for stylistic consistency with the file this module was told to mirror, rather than diverging from it. `desktop_facade.py`'s own pre-existing ruff debt (111 vs. 115 baseline errors, i.e. fewer, not more) is untouched/not introduced by this pass.

## Remaining callers not yet converted (exact list + the mechanical pattern for the next worker)

None of the other 10 listed callsites (`redraft_free_agents`, `redraft_opponent_rosters`, `redraft_weekly_projections`, `redraft_weekly_lineup`, `redraft_waivers`, `redraft_trade_analysis`, `redraft_trade_finder`, `redraft_trade_package_search`, `redraft_league_workspace_context`, `redraft_data_health`) were modified this pass beyond the shared `_active_profile_with_capabilities()` pure extraction (which changes nothing about their behavior -- `_active_sleeper_context()` still returns the exact same tuple via the exact same codes for all of them).

**Real correction to Worker 1's original architecture map, found while re-reading `redraft_league_workspace_context` tonight**: it is NOT one of the hard-409-for-ESPN callers either, alongside Worker 2's `redraft_data_health` correction. **INSPECTED CODE**: its Sleeper-specific live-fetch block is entered only `if selected.provider == "sleeper" and selected.provider_league_id:` (desktop_facade.py ~line 5293-appropriate-offset-after-this-pass's-edits) -- for any other provider it simply skips that whole block, leaving `sync_status = "NOT_APPLICABLE"` and returning 200 with a real (if roster-less) payload, not raising. So the real count of "genuinely hard-409-for-ESPN" callers among the 11 is smaller than Worker 1's original map stated: confirmed hard-409 today are My Roster (pre-conversion behavior, now honestly reproduced), Start/Sit, Waivers, Opponent Rosters, and (by construction, since they all call `_active_sleeper_context()` the same way) Free Agents, Weekly Projections, Trade Analysis, Trade Finder, Trade Package Search; confirmed graceful-degrade-already are Data Health (Worker 2) and League Workspace Context (this pass).

**The mechanical pattern for converting one of the true hard-409 callers**, demonstrated once (My Roster) and ready to repeat:
1. Replace its `selected, league_id, owner_user_id = self._active_sleeper_context()` + inline raw-fetch call with `state = self._resolve_canonical_league_state(...)` (pass `include_opponent_rosters=True` if the caller needs other teams' rosters -- only My Roster's own-roster path is wired today; Opponent Rosters would need its own row-shape reconciliation against `sleeper_opponent_rosters()`'s existing output first, see Scope decision above).
2. Wrap the call in a `try/except CanonicalLeagueStateError` that maps `exc.kind` (`MALFORMED_ROSTERS`/`OWN_ROSTER_NOT_FOUND`) to that caller's OWN pre-existing FacadeError code/message/status (copy the pattern in `redraft_my_roster`, do not reuse My Roster's literal codes for a different tool).
3. Source roster/identity fields from `state.roster` (synthesize a single-field catalog + call the existing `resolve_roster_canonical_ids` exactly as My Roster now does) instead of a raw Sleeper dict.
4. For anything the caller needs that `CanonicalLeagueState` doesn't yet carry from a live Sleeper fetch (FAAB budget, available-player pool, current week -- all real fields in the schema, currently only populated by the ESPN builder or left honestly `NOT_FETCHED_THIS_REQUEST`/`None` by the Sleeper builder), either (a) extend `build_canonical_league_state_from_sleeper`'s parameters to accept that additional already-fetched data (preferred -- keeps the "no new I/O in this module" invariant), or (b) keep that one piece of data-fetching inline in the caller alongside the canonical-state call, same as today, until a real need to unify it arises. Do not invent new ESPN data to fill these fields -- they must stay honestly null until a real ESPN snapshot/live-fetch pipeline exists (Worker 4's job).
5. `redraft_weekly_lineup` specifically needs the taxi/reserve-shape decision resolved FIRST (extend `CanonicalRosterPlayer.slot` to a 4th `TAXI` kind, which also means updating `EspnRosterPlayer`'s `RosterSlotKind` and `espn_flaim_snapshot_service.py`'s validation, since this pass deliberately kept them in lockstep) before it can be converted without regressing the real, tested reserve/taxi exclusion behavior in `weekly_lineup_optimizer_service.py`.

## Dev processes status

**LIVE OBSERVATION.** Worker 2's originally-reported PIDs (backend 26540, frontend 19284) were already gone/replaced by the time I checked at the start of this pass (a different pair, 25844/7744, was actually listening -- likely the smoke script's own launcher-then-child-process pattern, not a crash; not investigated further since I needed a clean restart anyway per the SAFETY directive). Stopped both, confirmed ports 18742/1422 free, restarted via `desktop/scripts/nwr_release_gate_smoke.ps1 -Mode redraft -KeepRunning -SleeperLeagueId 1312983576827920384 -SleeperUsername scolety` (same real, zero-write, byte-diff-verified Sleeper import as Worker 2's own invocation). **Final, identity-verified PIDs**: backend `32480` (`python.exe ... scripts\run_nwr_desktop_api.py --host 127.0.0.1 --port 18742 --mode redraft --repo-root C:\NWR\prospective-outcomes-v1`, confirmed via `Get-CimInstance Win32_Process` command-line match against this exact checkout), frontend `27280` (`vite preview --port 1422 --strictPort`), both confirmed `Listen` state on their ports at the end of this pass. Left running, Fantasy Gamers active, for the next worker or the owner.

## Files changed this pass

- `src/services/canonical_league_state_service.py` (new)
- `src/application/desktop_facade.py` (modified: `_active_profile_with_capabilities` extracted; new `_resolve_canonical_league_state`; `redraft_my_roster` converted; `_league_capabilities_for_profile`'s ESPN-snapshot-read except widened; FAAB `faabBidLowPct`/`faabBidHighPct` serialization added to the waiver-candidate payload)
- `desktop/packages/contracts/src/index.ts` (modified: optional `faabBidLowPct`/`faabBidHighPct` added to the waiver add-candidate type)
- `tests/test_canonical_league_state_service.py` (new)
- `tests/test_redraft_my_roster_canonical_state_conversion.py` (new)
- `tests/test_redraft_waivers_faab_pct_fix.py` (new)
- `docs/codex/waiver_night_hardening_20260922/LEDGER.md` (this section)

Not touched: `marginal_roster_utility_v2`, any governed Redraft valuation code, `governed_asset_registry_service.py`, KHA/403N18th profile identity fields, any Sleeper/ESPN write path, Flaim MCP tools (never invoked).

## Open issues for Worker 4 (ESPN implementation prep, per dispatch)

1. Build the real fetch/transform/validate/write pipeline for `EspnFlaimSnapshot` (`scripts/refresh_espn_flaim_snapshot.py` is still a stub) -- once a real snapshot lands on disk at `local_exports/redraft_v1/espn_flaim_snapshots/<profile_id>.json`, `redraft_my_roster` will serve real ESPN roster data automatically, live-verify this end-to-end as the first real proof the canonical boundary works for real (not just synthetic-fixture) ESPN data.
2. Build the emergency-fallback manual snapshot import path (per dispatch), targeting the same `EspnFlaimSnapshot` schema this pass's canonical builder already consumes -- no format changes needed on the canonical side.
3. Apply the mechanical conversion pattern above to `redraft_free_agents`, `redraft_weekly_projections`, `redraft_trade_analysis`, `redraft_trade_finder`, `redraft_trade_package_search` (all currently hard-409 for ESPN, all structurally similar to My Roster's pre-conversion shape).
4. Resolve the `TAXI` slot-kind gap (item 5 above) before attempting `redraft_weekly_lineup` or `redraft_opponent_rosters`.
5. Re-audit whether `_league_capabilities_for_profile`'s "Sleeper receipt wins if both exist" rule (in `capabilities_for_profile`) needs revisiting once real snapshots exist alongside real receipts for the same profile id in practice, not just the synthetic stale-receipt edge case this pass's tests constructed.
6. The `docs/codex/flaim_integration_20260919/LEDGER.md`-documented open re-audit of the September 22 Flaim evidence (free-agents/transactions) from Worker 1's Phase 0.3 is still open and still not this worker's scope.

---

# WORKER 4 (CODEX) - ESPN INGESTION + CANONICAL CALLER CONVERSIONS (2026-09-22)

Worker 4 starting HEAD: `c32a8a9a feat: add provider-neutral canonical league-state boundary, convert My Roster` on `upgrade/nwr-prospective-outcomes-v1-20260914` (verified before any edit). This pass did not invoke Flaim, did not write to Sleeper or ESPN, did not alter either real ESPN profile identity, and did not touch `marginal_roster_utility_v2`, the governed Redraft valuation model, or Dynasty's governed valuation computation. The two pre-existing untracked `local_exports.backup-*` directories were left untouched.

Evidence labels below are deliberate: **INSPECTED CODE** is a source-level finding, **ACTUAL TEST RESULT** is an executed automated check, **LIVE OBSERVATION** is a real HTTP/process observation, and **INFERENCE** is explicitly marked when used.

## Deterministic ESPN/Flaim transform, validate, and activate pipeline

**INSPECTED CODE.** `scripts/refresh_espn_flaim_snapshot.py` is no longer a `NotImplementedError` placeholder. It is an operator CLI over the new zero-network-I/O `src/services/espn_flaim_snapshot_import_service.py`. Provider fetching remains outside NWR code: an authenticated session calls only the authorized Flaim read tools and saves their factual output; this pipeline transforms, validates, previews, and activates that saved data. No Flaim or ESPN network client was added.

The raw input contract is one explicit combined JSON envelope named `nwr_espn_flaim_raw_capture_v1`, with `profile_id`, `retrieved_at_utc`, and three named sections: `get_league_info`, `get_roster`, and `get_free_agents`. This is documented in the import service with an example. **INFERENCE / ASSUMPTION:** because Flaim access was unavailable, these field names are an NWR-owned best-effort capture contract, not a claim about Flaim's private wire format. The transformer intentionally does not guess aliases; tomorrow's authenticated operator must map the three real tool responses into the documented envelope while preserving their factual values.

The transform reuses the real `EspnFlaimSnapshot` dataclass and `parse_espn_flaim_snapshot`; no second snapshot schema exists. It enforces:

- required profile/league/season/team/owner identity and a non-empty roster;
- only the existing `STARTER`, `BENCH`, and `RESERVE` roster slot kinds;
- `get_free_agents.coverage` only `BOUNDED` or `NONE`; `COMPLETE` is rejected, `BOUNDED` requires an exact bound description, and `NONE` cannot contain rows;
- scoring is `UNKNOWN` when no settings exist, `PARTIAL` when any provider field is unmapped or any current scalar NWR scoring input is absent, and `COMPLETE` only when all current scalar NWR fields are explicitly mapped and no provider field is unresolved;
- UTC-aware retrieval/provider timestamps.

**INSPECTED CODE.** Preview and activation validate the selected local profile before any write: provider must be `espn`; snapshot `profile_id`, normalized league name, season, and team count must match the profile; provider league ID, owner team ID, and normalized owner team name must match explicit operator-confirmed CLI arguments; and a non-empty profile provider league ID must also match the snapshot. This avoids filling either real ESPN profile's still-undetermined ID from an assumption.

The exact active path remains the established one: `local_exports/redraft_v1/espn_flaim_snapshots/<profile_id>.json` (or the equivalent under `--redraft-root` in tests). Activation records the existing retrieval/source fields plus real `imported_at_utc`, `source_capture_sha256`, and `source_capture_name` provenance. Serialization is deterministically sorted and is round-tripped through the authoritative parser before any byte is staged.

**INSPECTED CODE + ACTUAL TEST RESULT.** Writes are same-directory atomic writes: create a unique `.<target>.<uuid>.tmp`, write, flush, `fsync`, then `os.replace`. A simulated failure at final target replacement preserved the previous target byte-for-byte and removed the temporary file. If a target already exists, its exact bytes are first preserved atomically under `espn_flaim_snapshots/history/<profile_id>/<old-retrieved-at>--<old-sha256-prefix>.json`. The CLI reports that backup path. A collision with different bytes is rejected. A malformed existing target is not overwritten; the operator is told to preserve/repair it. Thus replacement is visible and reversible, never a blind overwrite.

**ACTUAL TEST RESULT.** Synthetic-only fixtures in `tests/test_espn_flaim_snapshot_import_pipeline.py` cover end-to-end raw transform/validation/activation, `COMPLETE` pool rejection, missing roster rows, team mismatch, strict manual `COMPLETE` scoring rejection, atomic-failure survival, exact prior-byte backup, preview-before-activation, provenance, and identity mismatch before any write. No private real snapshot fixture was created or committed.

## Emergency manual import path

**INSPECTED CODE + ACTUAL TEST RESULT.** The same CLI is also the Phase 18 fallback; `--input-kind snapshot` accepts an already-shaped `EspnFlaimSnapshot`, routes it through the same parser, semantic completeness checks, profile/league/team identity checks, provenance injection, backup, and atomic activation code. There is no parallel importer.

Preview is the default and performs zero writes. `--activate` is required to change the active snapshot. Success output names the target, counts, scoring/pool completeness, source hash, import time, any history backup, and reversal instruction. Rejection returns exit 2, explains the exact reason, and states that the active snapshot was unchanged. `python scripts/refresh_espn_flaim_snapshot.py --help` executed successfully with the complete operator contract.

## Canonical-state caller conversions

**INSPECTED CODE.** The exact Worker 3 five-step pattern was applied, one caller at a time, to all five requested methods:

1. `redraft_free_agents`
2. `redraft_weekly_projections`
3. `redraft_trade_analysis`
4. `redraft_trade_finder`
5. `redraft_trade_package_search`

Each now enters through `_resolve_canonical_league_state()` and translates `CanonicalLeagueStateError` to its own pre-existing facade error contract. Existing resolution/scoring/search services remain the authorities; the conversion only changes the provider data boundary. The Sleeper builder still consumes the same already-fetched live response and performs no extra I/O.

Caller-specific behavior:

- Free Agents uses `CanonicalLeagueState.available_player_pool` for ESPN and never mislabels roster players as available. Sleeper still obtains the exact same complete league-filtered free-agent set.
- Weekly Projections gets league identity through canonical state, then keeps the existing read-only weekly projection provider because weekly projections are not stored in canonical state.
- Trade Analysis resolves the owner's canonical roster plus the canonical player catalog (roster and bounded available pool) through the unchanged identity resolver and unchanged trade evaluator.
- Trade Finder and Trade Package Search request canonical opponent rosters for Sleeper. The current ESPN snapshot schema has only the owner's roster, so a valid ESPN snapshot receives explicit honest 409 errors (`TRADE_FINDER_OPPONENT_ROSTERS_UNAVAILABLE` / `TRADE_PACKAGE_SEARCH_OPPONENT_ROSTERS_UNAVAILABLE`) rather than fabricated opponents. Synthetic regression tests cover this forward path.

`CanonicalLeagueState`'s Sleeper opponent-team-name fallback was aligned with the old live code's exact order (`team_name`, `display_name`, username, then `Roster <id>`), and opponent rows retain the old team-name/team-ID sort. Dedicated real-Sleeper-shaped regression tests assert the response shape and values for each converted caller.

As required, `redraft_weekly_lineup` and `redraft_opponent_rosters` were not converted. `redraft_league_workspace_context`, `redraft_data_health`, and waivers were also not converted; the first two already degrade honestly and waivers was outside this pass's requested five.

## Snapshot freshness disclosure

**INSPECTED CODE + ACTUAL TEST RESULT.** Optional `leagueStateProvenance` was added to the contracts for My Roster and all five converted results. It is omitted for Sleeper, preserving Sleeper response keys byte-for-byte. For ESPN it reports provider/source, provider and retrieval timestamps, age in hours, stale state, and a warning once the snapshot is older than 36 hours. A shared `SnapshotProvenanceNotice` displays the warning on My Roster, Free Agents, weekly projections, Trade Analysis, and Trade Package Search/Find surfaces. The stale ESPN payload and UI contract paths are covered by tests/typecheck; no synthetic snapshot was installed for either real ESPN profile.

## Live A/B verification - both real Sleeper leagues

**LIVE OBSERVATION.** Before restarting the non-auto-reloading backend, normalized response summaries were captured for all five endpoints on both real Sleeper profiles. After restart on the final code, the same real HTTP calls were repeated. The serialized normalized summaries were exactly equal (`same: true`), including every top-level payload key. Trace IDs were deliberately excluded because calls create new trace records; all decision values were compared.

- Fantasy Gamers (`1312983576827920384`, profile `941b99ade350410391b1b67c0890af79`): Free Agents 726 rows, first IDs `8126/3163/1479`; weekly week 3 had 880 rows, 494 matched, 2738 unmatched, top projections `4881|23.8028`, `9221|23.257`, `9488|22.466`, provider `OK|LIVE`; Trade Analysis canonical give/receive `00-0039918` / `00-0039910`, net marginal utility `-10.52`, ROS delta `-203.9`; Trade Finder 15 candidates, first `00-0036252` for `00-0040730` from roster 10; Trade Package Search 5 candidates, 900 packages evaluated, 8 opponents, truncated true, first `1-for-2` package sending `00-0036252` for `00-0040734,00-0040730`.
- Las Vegas Enginerds (`1344772855908290560`, profile `6687d2b3aa21450ea0fc9e1792d461ff`): Free Agents 629 rows, first IDs `11655/11647/1479`; weekly week 3 had 880 rows, 494 matched, 2738 unmatched, top projections `4881|20.16`, `4984|17.3707`, `8183|16.8957`, provider `OK|LIVE`; Trade Analysis canonical give/receive `00-0034796` / `00-0040691`, net marginal utility `0.91`, ROS delta `17.57`; Trade Finder 15 candidates, first `00-0039491` for `00-0036555` from roster 3; Trade Package Search 5 candidates, 450 packages evaluated, 9 opponents, truncated false, first `2-for-1` package sending `00-0035229,00-0038935` for `00-0040876`.

This is stronger than HTTP-status-only verification: counts, ordering samples, identities, evaluated-package counts, decision values, provider health, truncation, and complete payload key sets all matched before/after.

## Live ESPN verification - both real profiles remain honest

**LIVE OBSERVATION.** No real snapshot exists and no fake file was placed in the real snapshot directory. After activating each real ESPN profile, all five converted endpoints returned HTTP 409 without a crash or fabricated data:

- KHA, profile `fb1c49402c7644a99120197d41344bbb`: Free Agents, Weekly Projections, Trade Analysis, Trade Finder, and Trade Package Search each returned `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` with the existing `No verified league data available...` message.
- 403 N 18th, profile `4b4a990faf124ce7a5d612537ba5943b`: the same five HTTP 409 responses with the same code/message.

This is the expected pre-snapshot capability gate and is unchanged from tonight's prior live evidence. It is distinct from the forward-path opponent-roster-specific 409s, which become reachable only after a validated ESPN owner-roster snapshot exists.

## Test and static verification

**ACTUAL TEST RESULT.** Final results after all code changes:

- New Worker 4 suites alone: **16 passed** (`test_espn_flaim_snapshot_import_pipeline.py` plus `test_redraft_canonical_state_caller_conversions.py`).
- Required combined backend set: **136 passed, 4 failed**. The four failures are the exact same named pre-existing failures documented by Worker 3: `test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, and `test_facade_has_no_streamlit_or_app_component_dependency`. No new failure name appeared.
- The combined command included `test_canonical_league_state_service.py`, `test_redraft_my_roster_canonical_state_conversion.py`, `test_redraft_waivers_faab_pct_fix.py`, both Worker 4 suites, the identity/trade-finder and trade-package wiring suites, capability tests, waiver context/reserve tests, facade architecture wiring, and `test_desktop_application_api.py`.
- Focused Ruff check on the importer CLI/service, snapshot/canonical services, and both new tests: **all checks passed**. Whole-file `desktop_facade.py` still has 104 legacy Ruff findings (mostly E501 plus import ordering); this pass did not autoformat unrelated facade code.
- `python -m py_compile` on modified Python passed.
- `npm --prefix desktop run typecheck`: passed.
- Full `npx vitest run`: **30 files, 503 tests passed**. Its machine-timing benchmark artifact was restored to exact HEAD content and is not part of this change.
- `npm run build:redraft`: passed earlier in this pass; only the existing bundle-size warning was emitted.
- `git diff --check`: passed.

## Final dev processes

**LIVE OBSERVATION.** The original backend PID 32480 and frontend PID 27280 were identity-checked before any stop. The backend was restarted because Python does not auto-reload. Windows keeps redirected stdin open for the process lifetime, so the final launch keeps runtime-only startup input/log files in the OS temp directory, not in the repository; the workspace credential/log copies were removed and no credential is staged.

- Backend PID **33944**, `python.exe ... C:\NWR\prospective-outcomes-v1\scripts\run_nwr_desktop_api.py --host 127.0.0.1 --port 18742 --mode redraft --repo-root C:\NWR\prospective-outcomes-v1`, command line verified via `Get-CimInstance`, listener verified on `127.0.0.1:18742`.
- Frontend PID **27280**, checkout-local Vite preview command verified, listener on `127.0.0.1:1422`.
- Fantasy Gamers restored as final active profile (`941b99ade350410391b1b67c0890af79`).

## Files changed

- `src/services/espn_flaim_snapshot_import_service.py` (new deterministic transform/identity/backup/atomic activation service)
- `scripts/refresh_espn_flaim_snapshot.py` (real preview/activate CLI and manual fallback)
- `src/services/espn_flaim_snapshot_service.py` (import provenance fields/parser support)
- `src/services/canonical_league_state_service.py` (exact legacy Sleeper opponent-name fallback)
- `src/application/desktop_facade.py` (five canonical caller conversions, canonical catalog/provenance helpers, ESPN freshness metadata)
- `desktop/packages/contracts/src/index.ts` (optional league-state provenance contract)
- `desktop/apps/redraft/src/snapshot-provenance.tsx` (new shared warning component)
- `desktop/apps/redraft/src/pages.tsx`, `in-season.tsx`, `improve-team.tsx`, `trades.tsx` (snapshot freshness display)
- `tests/test_espn_flaim_snapshot_import_pipeline.py` (new, synthetic only)
- `tests/test_redraft_canonical_state_caller_conversions.py` (new regression suite)
- this ledger.

## Remaining work for future workers

1. A Flaim-authenticated session must make the authorized read calls and map the factual results into `nwr_espn_flaim_raw_capture_v1`; preview must be reviewed before activation. This pass could not validate Flaim's actual response field names and does not claim it did.
2. Do not convert `redraft_weekly_lineup` until `TAXI` is added in lockstep to `CanonicalRosterPlayer` and `EspnRosterPlayer` and the real Sleeper taxi exclusion has lossless regression coverage.
3. Do not convert `redraft_opponent_rosters` until its legacy row shape, including `unresolvedSleeperPlayerIds`, is reconciled with canonical opponent rows. The current ESPN snapshot also has no opponent-roster collection, which is why the two converted trade-search callers honestly block for an otherwise valid ESPN snapshot.
4. Waivers still uses the old Sleeper context and requires a dedicated canonical conversion that preserves live FAAB/acquisition-state semantics. Workspace Context and Data Health remain lower priority because they already degrade honestly.
5. Re-audit the September 22 Flaim evidence before changing the deliberate bounded-only free-agent rule or authorizing transactions. This pass preserved both constraints.
6. Once the first real private snapshot is obtained, live-verify My Roster and the converted Free Agents/Weekly Projections/Trade Analysis paths end-to-end, inspect the >36-hour stale warning in the real UI, and keep the private snapshot outside Git.

---

# WORKER 5 (CODEX) - WAIVER ENGINE + FAAB + ADD/DROP HARDENING (2026-09-22)

Worker 5 starting HEAD: `27310502 feat: harden ESPN ingestion and canonical league callers` on `upgrade/nwr-prospective-outcomes-v1-20260914` (verified before edits). The two pre-existing untracked `local_exports.backup-*` directories were left untouched. This pass made no provider writes, did not use Flaim, did not change KHA/403 identity, did not touch `marginal_roster_utility_v2` or `governed_asset_registry_service.py`, and did not change any governed valuation weight/formula.

Evidence labels are strict: **INSPECTED CODE** is a source finding, **ACTUAL TEST RESULT** is an executed automated check, **LIVE OBSERVATION** is a real HTTP/provider/process observation, and **INFERENCE** is used only where stated.

## Reproducible bugs fixed

### 1. Actual starters were offered as drops

**LIVE OBSERVATION, BEFORE FIX.** Fantasy Gamers' highest-ranked drop was Rashod Bateman while he was in Sleeper's real current starter list. Las Vegas Enginerds offered nine real current starters among its drop candidates: Jalen Coker, Xavier Worthy, Luther Burden, Lamar Jackson, Jake Ferguson, David Montgomery, Jameson Williams, Chase Brown, and De'Von Achane. The cause was direct: `rank_drop_candidates` ranked the full resolved roster and the facade removed only reserve IDs; it never removed `own_roster.starters`.

**INSPECTED CODE + FIX.** New pure `filter_legal_drop_candidates` filters starter, reserve/IR, taxi, and (when verified in THIS_WEEK mode) already-locked Sleeper IDs through the existing Sleeper-to-canonical identity map. REST_OF_SEASON does not pretend game-lock data was checked. The facade now exposes `dropEligibilityContext` with legal count, excluded counts, game-lock status, and a disclosure. Reserve/IR exclusion remains intact and is now on the same shared path. No starter/drop utility formula changed.

**ACTUAL TEST RESULT.** `tests/test_redraft_waivers_starter_drop_exclusion_fix.py` proves a starter is absent from both drop rows and pairings, a locked bench player is excluded, and the legal bench player remains. The prior reserve-specific suite also passed.

**LIVE OBSERVATION, AFTER FIX.** Direct read-only Sleeper roster GETs plus the NWR waiver response showed zero actual-starter/drop overlap in both leagues: Fantasy Gamers (15 players, 9 starters, 6 legal drops) and Las Vegas (26 players, 10 starters, 14 legal drops).

### 2. A full roster with no legal drop was mislabeled as add-only

**INSPECTED CODE + FIX.** `pair_add_drop` used `dropRequired: false` both for a verified open slot and for the opposite condition: no legal drop on a full/unverified roster. The latter now keeps `dropRequired: true`, `drop: null`, `netMarginalUtility: null`, and `contextLabel: NO_DROP_CANDIDATE_AVAILABLE`. The UI says the target is not currently executable instead of saying no drop is needed. FAAB is $0 for this unconstructible transaction.

**ACTUAL TEST RESULT.** The dedicated full-roster fixture asserts no crash, no fabricated drop, no add-only claim, and zero bid. Frontend explanation tests assert `NO LEGAL DROP AVAILABLE`, neutral/LOW framing, and no positive bid label.

### 3. Positive standalone add value could produce a positive bid despite nonpositive legal add/drop value

**INSPECTED CODE.** FAAB pricing received only each add's standalone `marginalUtility`; it did not receive the required-drop pairing's transaction net. Therefore the existing nonpositive-utility floor did not protect a positive standalone add whose legal add/drop move was neutral or harmful.

**FIX.** The facade evaluates all 25 add/drop pairings internally (still serializes the existing top 10), passes a per-Sleeper-ID legal transaction net into `suggest_faab_bids`, and gates to $0 when the transaction is absent or nonpositive. The positive-utility percentile/urgency/season-taper pricing branch is unchanged. Distinct rationales separate unknown identity, no legal transaction, nonpositive transaction, and nonpositive standalone value.

**ACTUAL TEST RESULT.** `tests/test_redraft_waivers_transaction_net_faab_fix.py` reproduces positive standalone utility `8.0` with transaction net `-0.01` and verifies a $0 range; a positive transaction still prices from the real remaining balance ($37 fixture). Existing zero/negative standalone tests also passed. The UI no longer formats `$0-$0` as a BID.

### 4. Position-ineligible adds could enter recommendations

**INSPECTED CODE + FIX.** `rank_waiver_candidates` did not reject a position that the profile cannot roster. It now retains the complete free-agent pool for ownership truth but skips recommendation candidates with no configured compatible starter slot. This is especially important for Las Vegas, whose real configuration has `dst=0`.

**ACTUAL TEST RESULT.** `tests/test_redraft_waivers_position_eligibility_fix.py` supplies a ranked JAX DST to a no-DST profile and proves it is not recommended.

**LIVE OBSERVATION.** Las Vegas returned 25 skill-position adds and zero DST adds after restart. No governed K/DST or skill-player valuation formula changed.

### 5. Budget/freshness/missing-value UI could imply confidence NWR did not have

**INSPECTED CODE + FIX.** The backend already separated live remaining budget from initial budget, but a confirmed FAAB league with missing live balance was still labeled `SLEEPER_LIVE`; the frontend also retained `$100` scenario fallbacks. The facade now reports `faabContext.source: UNAVAILABLE` if league type is known but the real total or remaining balance is missing. The frontend requires real total, remaining, and weeks values (or a complete echoed scenario), contains no `$100` fallback, and never presents a number when the balance is unavailable.

The waiver response now includes a per-request `freeAgentPoolContext.retrievedAtUtc` and says the pool is a live selected-league read. If a refresh fails after a prior success, retained rows are explicitly labeled last-successful/not-current rather than silently appearing fresh. Initial retrieval failures still fail closed as structured `WAIVERS_READ_FAILED`/503; the backend does not turn a failed fetch into a current empty pool.

The Add/Drop detail previously derived roster construction from `dropCandidates`, which is now correctly only a legal bench subset and was never the full roster. It now uses backend `rosterPositionCounts` built from the actual full raw Sleeper roster, including K/DST and reserve identities. Missing weekly/ROS/net values no longer use `?? 0`; they render `unavailable`, while a real zero still renders `0.0`.

**ACTUAL TEST RESULT.** The missing-live-balance facade test returns `UNAVAILABLE` and null bid fields. `improve-team-faab-budget.test.ts` rejects incomplete live/scenario budget contexts. `in-season.test.ts` distinguishes missing from real zero. The starter-drop fixture proves two rostered RBs remain in `rosterPositionCounts` while only one is legally droppable, and verifies freshness/acquisition disclosures. A pure UI test verifies retained rows become stale-labeled only after a failed refresh.

## Audited paths that were already correct or remain honestly missing

- **League-specific availability - INSPECTED CODE + LIVE OBSERVATION.** `sleeper_free_agent_pool` removes raw Sleeper IDs rostered anywhere in the selected league on every request. After the fix, both real leagues had 25 recommended adds and zero IDs rostered anywhere in that league. Pools are genuinely independent: the pre-fix live audit found Fantasy Gamers roster assets NE DST and Rashod Bateman free in Las Vegas, while Las Vegas roster assets including Xavier Worthy, Daniel Jones, Brenton Strange, Oronde Gadsden, T.J. Hockenson, Chris Bell, Jakobi Meyers, Jayden Higgins were free in Fantasy Gamers. No profile's FAAB or ownership state is cached into another profile's response.
- **Waiver vs immediate free agent - INSPECTED CODE.** Still genuinely missing for Sleeper and ESPN. The recent ESPN snapshot schema contains available players but no waiver-status or clear-time field. `acquisitionContext` and the UI now explicitly say NWR knows only `UNROSTERED`, not waiver-vs-FA, clear time, or recent winning/failed bids. No failed historical bid is treated as a winning price because no transaction-history input exists at all.
- **FAAB vs priority - LIVE OBSERVATION.** Fantasy Gamers is `isFaabLeague: false`, real waiver position 9, null total/remaining and 25/25 null bid rows. Las Vegas is `isFaabLeague: true`, live total `$100`, live remaining `$100`, waiver position 2, 25/25 priced rows. The $100 values are provider facts (`waiver_budget` and roster `waiver_budget_used`), not a fallback. The UI suppresses FAAB entirely for Fantasy Gamers.
- **Missing projection - LIVE OBSERVATION + ACTUAL TEST RESULT.** The current real missing weekly projection is Caleb Williams on Fantasy Gamers' bench in week 3. It remains `projectedPoints: null`; no numeric zero or fabricated delta is shown. `unprojectedStarterCount` is correctly 0 because he is not a required starter. The existing optimizer missing-row/unknown-delta tests passed.
- **Reserve/IR and locks - INSPECTED CODE + ACTUAL TEST RESULT.** Reserve and taxi remain excluded. THIS_WEEK reuses `weekly_game_lock_service`; an already-locked bench player is not a drop candidate, while REST_OF_SEASON explicitly says locks were not evaluated. Neither real roster had a currently excluded locked candidate at verification time, so lock exclusion is synthetic-test-proven rather than falsely called a live reproduction.
- **Injury/questionable - INSPECTED CODE.** The optimizer honors the existing manual status override layer for `SEASON_OUT`, `NOT_WITH_TEAM`, and `ADMINISTRATIVE_EXEMPT` and does not assume an unmatched identity healthy. NWR still has no automated injury/questionable feed; ordinary Q tags are therefore not a trustworthy waiver ranking input tonight. This is a missing capability, not silently invented data.
- **Bye week/SOS - INSPECTED CODE.** No bye/schedule/SOS input reaches waiver ranking or add/drop simulation. This remains a disclosed future capability; no heuristic was added tonight.
- **Dynasty framing - INSPECTED CODE + LIVE OBSERVATION.** Las Vegas is dynasty, but this Redraft waiver engine uses current-season ROS marginal utility only. `acquisitionContext.valuationHorizonDisclosure` now says it is not dynasty stash/long-term asset valuation. A real dynasty waiver model remains missing.
- **Identity collisions/aliases - INSPECTED CODE + ACTUAL TEST RESULT.** The existing free-agent identity boundary strips only trailing generational suffix tokens and normalizes team aliases such as JAC/JAX; the executed `test_fantasypros_kdst_consensus_service.py` coverage passed. No name-only cross-league ownership decision was introduced; ownership exclusion remains raw provider ID based.
- **Roster-full-after-move - INSPECTED CODE + ACTUAL TEST RESULT.** Full-roster pairings remove one legal drop before evaluating the add; verified open slots use `OPEN_ROSTER_SLOT_ADD_ONLY`. No-legal-drop is non-executable, not a fabricated post-move roster.
- **ESPN - LIVE OBSERVATION.** KHA and 403 N 18th still return honest HTTP 409 `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` for waivers because no real ESPN snapshot exists. No fake snapshot/private data was created. The legacy error name is provider-specific wording debt, but the behavior is fail-closed and unchanged.

## Verification results

**ACTUAL TEST RESULT.** Final results after all changes:

- Touched backend waiver/lineup/K-DST set: **113 passed**.
- Required `tests/test_desktop_application_api.py`: **46 passed** when the four known failures were deselected, and the four named tests independently reproduced **exactly 4 failures**: `test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_component_dependency`. Thus the required combined set is **159 passed, 4 pre-existing failures**, with no new failure name.
- `python -m ruff check` on all new Worker 5 backend regression files plus the modified FAAB-context file: passed. Whole `waiver_engine_service.py` still has legacy line-length/import findings and was not broadly reformatted.
- `python -m py_compile` on modified Python and new regression tests: passed.
- `npm run typecheck`: passed.
- Directly changed frontend tests: **3 files, 34 tests passed**.
- Exact full `npx vitest run`: **31 files, 510 tests passed**. The timing benchmark artifact written by that suite was restored byte-for-byte and is not part of this change.
- `git diff --check`: passed (only Git's existing LF-to-CRLF warnings).

## Final live/process state

**LIVE OBSERVATION.** The final backend was restarted after Python changes. Actual listener PID **36328** (Windows launcher parent 32328) runs `scripts/run_nwr_desktop_api.py` from `C:\NWR\prospective-outcomes-v1` on `127.0.0.1:18742`. Frontend PID **27280** runs the checkout-local Vite preview on `127.0.0.1:1422`. Both command lines and listeners were re-verified. Authenticated bootstrap succeeds with the required dev token.

Post-restart live smoke: Fantasy Gamers returned 25 adds, 6 legal drops, 10 pairings, non-FAAB with 25 null bid rows; Las Vegas returned 25 adds, 14 legal drops, 10 pairings, live `$100/$100` FAAB with 25 positive bid rows and zero DST adds. Fantasy Gamers was restored as final active profile (`941b99ade350410391b1b67c0890af79`).

## Files changed

- `src/services/waiver_engine_service.py`
- `src/application/desktop_facade.py`
- `desktop/packages/contracts/src/index.ts`
- `desktop/apps/redraft/src/improve-team-explain.ts` and its test
- `desktop/apps/redraft/src/improve-team.tsx`
- `desktop/apps/redraft/src/in-season.tsx` and its test
- `desktop/apps/redraft/src/improve-team-faab-budget.test.ts` (new)
- `tests/test_waiver_engine_service.py`
- `tests/test_redraft_waivers_faab_context_fix.py`
- `tests/test_redraft_waivers_starter_drop_exclusion_fix.py` (new)
- `tests/test_redraft_waivers_transaction_net_faab_fix.py` (new)
- `tests/test_redraft_waivers_position_eligibility_fix.py` (new)
- this ledger.

## Remaining open items

1. Add real provider acquisition state (waiver/free-agent distinction, clear time) and recent transaction context to canonical state only when sourced truthfully; historical failed bids must remain market context, never labeled winning price.
2. Add a trustworthy live injury/questionable feed and bye/schedule/SOS input before using those facts in waiver ranking.
3. Build a separate dynasty waiver/stash valuation surface for Las Vegas; do not reinterpret this governed current-season ROS output as long-term asset value.
4. Convert waivers to the canonical provider boundary after a real ESPN snapshot exists, preserving Sleeper FAAB, reserve/taxi, game-lock, and complete-pool semantics. Consider replacing the legacy `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` wording with a provider-neutral capability error at that time.

---

# WORKER A (CLAUDE) - START/SIT + LINEUP LEGALITY + PROJECTION/FRESHNESS HARDENING (2026-09-22)

Worker A dispatch HEAD: `6e4cda6f` (Worker 5's waiver/FAAB legality hardening), verified via `git log -1` before any edit. Worktree was clean except the 2 documented `local_exports.backup-*` dirs (the previously-flagged third one is genuinely gone -- confirmed via `git status`, matching the dispatch prompt's "2 known backup dirs" framing exactly). This pass made no Sleeper/ESPN writes, did not touch `marginal_roster_utility_v2`, `governed_asset_registry_service.py`, or any governed valuation formula, did not touch KHA/403N18th profile identity fields, and did not attempt Flaim/MCP access.

Evidence labels: **INSPECTED CODE**, **ACTUAL TEST RESULT**, **LIVE OBSERVATION** (real HTTP/browser round trip against the real running backend/frontend tonight), **INFERENCE**.

## TAXI GAP -- resolved by direct confirmation, not touched architecturally

**INSPECTED CODE + LIVE OBSERVATION.** Per the dispatch's own instruction, I did NOT attempt the `CanonicalRosterPlayer`/`EspnRosterPlayer` TAXI-slot-kind conversion this pass. Real finding: it is not needed for Start/Sit's real live behavior. `desktop_facade.redraft_weekly_lineup` (line ~3511) was confirmed by direct code read to still call `_active_sleeper_context()` directly -- it has NEVER been routed through Worker 3/4's canonical-state boundary at all (unlike My Roster/Free Agents/Weekly Projections/Trade Analysis/Trade Finder/Trade Package Search). It sources `reserve_sleeper_player_ids`/`taxi_sleeper_player_ids` straight off the SAME live Sleeper roster read's own `reserve`/`taxi` arrays (line 3614-3615), and `weekly_lineup_optimizer_service.optimize_weekly_lineup` hard-excludes `is_reserve or is_taxi` candidates into a dedicated `reserve` bucket before any point comparison -- entirely independent of the canonical-state TAXI-kind gap. **LIVE OBSERVATION**: confirmed via a real browser round trip (Chrome MCP) against the real Las Vegas Enginerds league -- the "Reserve / taxi (not startable)" panel correctly shows the real reserve player (Ricky Pearsall) with an honest, never-startable disclosure. Real Sleeper roster data tonight (`GET /v1/league/1344772855908290560/rosters`, all 10 real rosters) shows every roster's `taxi` array genuinely EMPTY right now -- so the taxi-specific exclusion path could not be live-exercised with real data this pass (same honest limitation Worker 2 already recorded for reserve). Independently confirmed via a real GitHub issue in a DIFFERENT dynasty app (`kfsalem/Dynasty-Trade-Calculator#103`) that Sleeper's own `players` array DOES include taxi-squad ids alongside active/reserve ones (not a separate, non-overlapping set) -- confirming NWR's own live wiring assumption (`own_roster.get("players")` is the superset, `taxi`/`reserve` are subsets subtracted out) is correct, and that NWR's Start/Sit proactively avoids the exact bug class that other app suffered (taxi players eligible for every lineup it built). Closed the one real, previously-uncovered gap here: no existing test exercised `build_roster_candidates`'s own `taxi_sleeper_player_ids` wiring OR a `taxi=True`-tagged candidate through `optimize_weekly_lineup` at all (only `reserve=True` had a dedicated fixture) -- added `tests/test_weekly_lineup_optimizer_service.py::test_regression_fixture_5e_taxi_squad_excluded_from_normal_candidate_selection` and `::test_build_roster_candidates_wires_real_sleeper_reserve_and_taxi_arrays` (both pass). **Verdict: TAXI exclusion is real, live-correct, and now has direct test coverage at the exact wiring point that matters for Enginerds -- no code change needed, only coverage closed.**

## Real bug found + fixed: "Not included this week" panel showed a fabricated exclusion reason

**LIVE OBSERVATION, BEFORE FIX.** Live-browsed (Chrome MCP) Start/Sit for the real Las Vegas Enginerds league, week 3: the "Not included this week" panel showed `Jayden Higgins -- no roster slot they're eligible for, or no usable projection.` **INSPECTED CODE + LIVE OBSERVATION**: the real backend response for this exact player carries a full, specific, dated, sourced reason on `excluded[].playerAvailabilityStatus`: `statusCategory: OUT_FOR_SEASON`, `reason: "Torn ACL in training camp; placed on Reserve/Injured (no Designated for Return) -- season-ending for 2026."`, `source: MANUAL_VERIFIED_OVERRIDE`, `sourceAsOf: 2026-08-19`. Backend semantics confirm `WeeklyLineupResult.excluded` is populated EXCLUSIVELY by a real status override (`weekly_lineup_optimizer_service.ZERO_VALUE_KINDS` = `SEASON_OUT`/`NOT_WITH_TEAM`/`ADMINISTRATIVE_EXEMPT`, via `_status_for`) -- never by roster-slot ineligibility or a missing projection, so the panel's static copy was factually wrong for EVERY real entry it can ever show, not just this one instance. This directly violates this codebase's own "distinct OUT/questionable/unknown facts, never collapsed" discipline (the dispatch's own stated concern) -- the real, specific, sourced reason existed the whole time and was simply discarded at the presentation layer.

**FIX.** Extracted a new pure, tested function `describeExcludedLineupPlayer` (`desktop/apps/redraft/src/lineup-explain.ts`), mirroring this file's existing `explainLineupSwap` pattern and reusing the SAME canonical `playerAvailabilityBadgeLabel`/`playerAvailabilityBadgeTone` authority Trades/Draft Room already render (no second status heuristic). `LineupPage`'s "Not included this week" panel (`in-season.tsx`) now renders each excluded player as its own row with a real status badge (e.g. "OUT FOR SEASON") and the real, sourced `reason` string, falling back to an honest "no further detail recorded" only when `playerAvailabilityStatus` is genuinely null (should not occur for a real `excluded` row today, never assumed impossible). Added `.lineup-excluded-list` CSS (`redraft.css`), following this codebase's established per-list-class convention.

**ACTUAL TEST RESULT.** `tests/lineup-explain.test.ts` (new `describe("describeExcludedLineupPlayer", ...)` block, 3 new tests): real SEASON_OUT reason surfaced verbatim and asserted NOT to match the old fabricated sentence; NOT_WITH_TEAM correctly distinguished from SEASON_OUT (not collapsed to one label); null-status honest fallback asserted to never contain the old fabricated text either. 12/12 passed in this file (9 pre-existing + 3 new).

**LIVE OBSERVATION, AFTER FIX.** Rebuilt (`npm run build:redraft`) and re-browsed (Chrome MCP) the real Las Vegas Enginerds Start/Sit page: the panel now reads `[OUT FOR SEASON] Jayden Higgins -- Torn ACL in training camp; placed on Reserve/Injured (no Designated for Return) -- season-ending for 2026.` -- real, specific, sourced, screenshot-confirmed.

## Full Start/Sit hardening pass -- verification results (no other new bugs found)

Extensive live + code verification against both real Sleeper leagues; everything below was either already correct (confirmed, not assumed) or explicitly out of scope per this dispatch:

- **Legal lineup construction, both leagues, LIVE OBSERVATION**: Fantasy Gamers (QB1/RB2/WR2/TE1/FLEX1/K1/DST1 = 9 starters) and Las Vegas Enginerds (QB1/RB2/WR3/TE1/FLEX2/K1/DST0 = 10 starters, real non-PPR `NWR_LEAGUE_SCORING` context on every skill-position starter, zero DST slot correctly enforced) both produced correct, non-duplicate (`unique starter ids == starter count` verified programmatically both leagues), fully slot-legal lineups this pass.
- **Reserve/IR exclusion**: still intact -- `weekly_lineup_optimizer_service.py`'s `is_reserve`-hard-exclusion branch unchanged, live-confirmed via the real Las Vegas reserve player (Ricky Pearsall) correctly shown in the "not startable" panel.
- **Locked players**: `weekly_game_lock_service.py` (real `nflreadpy.load_schedules` pull, `America/New_York` `gametime` convention, honest UNAVAILABLE-on-fetch-failure) is unchanged and correct by inspection; live-verified `gameLock.sourceStatus: OK` with a real, non-empty per-team kickoff table this pass. No real roster had a genuinely locked player at verification time (all Week 3 kickoffs were still in the future relative to real wall-clock time), so lock-exclusion itself remains test-proven (`test_regression_fixture_5b`/`5c`), not freshly live-reproduced -- same honest caveat Worker 5 recorded.
- **Bye weeks**: no dedicated bye-week signal exists anywhere in `weekly_projection_service.py` (confirmed by grep, zero matches) -- a bye-week player simply has no weekly-projection row and flows through the SAME honest "missing projection stays unknown, never zero" path as any other missing-data case. This is disclosed-by-omission, not a fabrication, but it does mean the UI cannot currently tell an owner "he's missing because of a bye" vs. "missing for some other data reason" -- flagged as a genuine, minor, non-bug enhancement opportunity for a future worker, not fixed this pass (out of scope; no real bye-week case was live-observable this week to justify a blind design change).
- **Injuries/status**: distinct OUT/questionable/unknown facts are NOT collapsed -- `ZERO_VALUE_KINDS` (SEASON_OUT/NOT_WITH_TEAM/ADMINISTRATIVE_EXEMPT) remain honestly separate categories, live-confirmed via the real Jayden Higgins SEASON_OUT case above. NWR still has no automated Q-tag/practice-report feed (Worker 5's finding, unchanged, out of scope for this pass).
- **Missing projections stay honestly unknown**: LIVE-reproduced the "Zay Flowers case" fix against the REAL currently-missing player this week (Caleb Williams, Fantasy Gamers bench) -- `projectedPoints: null`, swap summary correctly reads "Caleb Williams's projection is missing this week; point swing unknown", `confidenceState: LOW`, live-screenshot-confirmed in-browser with the exact CLOSE-CALL/LOW-CONFIDENCE badge rendered. Confirms the player-name-specific instance has genuinely changed since the prior cycle's Zay Flowers case (per the dispatch's own warning not to assume it's still the same player) while the underlying mechanism is unchanged and correct.
- **Custom scoring for Enginerds**: real non-PPR, no-DST scoring confirmed live -- every skill-position starter carries `scoringContext: NWR_LEAGUE_SCORING` computed under this league's real distinct scoring settings (0 PPR, 4pt pass TD... - matches Worker 2's originally-documented scoring dump), K carries the honest `NWR_LEAGUE_SCORING_KDST_WEEKLY_PARTIAL` context, zero DST starters possible (league config `dst:0`).
- **Current NFL week**: confirmed NEVER hardcoded -- resolved live via `LeagueWorkspaceContext.currentWeek` (Sleeper's own live `state/nfl`), `useProviderWeek`/`useWeekSelection` (`weekly-shared.tsx`) reset the manual override on every profile switch, and the Lineup page's own loader gates on `week != null` so no request is ever silently sent for a fabricated Week 1. Live-confirmed both real leagues independently resolved to the same real Week 3.
- **No duplicate players, no bench-as-starter**: confirmed programmatically (`starters` id set == unique count) for both real leagues; `bench` is structurally the greedy algorithm's own leftover set, cannot overlap `starters` by construction.
- **No stale data across a league switch**: confirmed both at the backend (every request performs its own fresh, unpcached Sleeper fetch; FG vs. LVE responses were fully distinct player sets) and at the frontend (`useWeekSelection` explicitly resets `manualWeekOverride` on `profileId` change; `useAsync`'s `createStaleResponseGuard` discards any in-flight response superseded by a newer request -- this is the same established stale-response-race defense prior cycles already built and fixed bugs against). LIVE-browsed a real FG->LVE switch: no FG data visible at any point on the LVE page.
- **"Change only if meaningful" / noise-churn suppression**: ALREADY EXISTS, confirmed by code read -- `_close_call` (`CLOSE_CALL_ABSOLUTE_PTS=2.0` / 15% relative) does not suppress a marginal swap, but honestly demotes it to `tone: warning` / `confidence: LOW` ("CLOSE CALL") rather than presenting it with the same confidence as a clear-cut recommendation -- live-confirmed on both real leagues tonight (Fantasy Gamers' Etienne-vs-Bateman FLEX close call, Las Vegas's Gadsden-vs-Ferguson TE close call, margins 0.9/0.3 pts). This is a deliberate, already-correct design (never hide a real decision, but flag low-confidence ones distinctly) -- did NOT force a suppression-based redesign, per the dispatch's own instruction not to force a design decision that isn't clearly correct.
- **Confidence disclosure**: `_start_sit_confidence` (`desktop_facade.py`) correctly downgrades to LOW for stale projections, unprojected starters, unresolved identities, AND a primary swap resting on an unknown delta (the exact gap a prior cycle's owner-reported fix closed) -- live-confirmed LOW confidence + a real, specific `confidenceBasis` message on the Caleb Williams case.
- **ESPN leagues (KHA, 403 N 18th)**: both confirmed via direct authenticated curl to return an honest, non-crashing `409 SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED` for Start/Sit -- byte-identical to every prior cycle's documented finding, unchanged by this pass (Start/Sit was never converted to the canonical boundary, so ESPN behavior here is unaffected by any Worker 3/4 canonical-state work).
- **OP/Superflex**: neither real league uses it (`superflex: 0` both), so nothing live-observable this pass; confirmed by code read that an unmapped Sleeper roster-position code (e.g. a hypothetical `OP` alias) would FAIL CLOSED at import time (`SleeperRedraftImportError`, `sleeper_redraft_owner_service._roster_settings`) rather than silently dropping a real slot -- safe, honest behavior, not a live gap for either real league today.

## Live verification -- all 4 real leagues (exact evidence)

- **Fantasy Gamers** (`941b99ade350410391b1b67c0890af79`): `POST /api/v1/redraft/weekly-lineup {"week":3}` -> 200, 9 starters (9 unique ids), Caleb Williams missing-projection case reproduced live + in-browser (Chrome MCP screenshot), `confidenceState: LOW`.
- **Las Vegas Enginerds** (`6687d2b3aa21450ea0fc9e1792d461ff`): same endpoint -> 200, 10 starters (10 unique ids), zero DST, real non-PPR scoring context, real reserve player (Ricky Pearsall) shown honestly not-startable, real SEASON_OUT exclusion (Jayden Higgins) -- both the pre-fix bug and the post-fix rendering live-browser-confirmed via Chrome MCP with screenshots.
- **KHA** (`fb1c49402c7644a99120197d41344bbb`, ESPN): same endpoint -> 409 `SLEEPER_REDRAFT_LEAGUE_DATA_REQUIRED`, non-crashing, via direct curl.
- **403 N 18th** (`4b4a990faf124ce7a5d612537ba5943b`, ESPN): same -> 409, same code, via direct curl.
- Final active profile restored to Fantasy Gamers, matching every prior worker's own convention.

## Tests

**ACTUAL TEST RESULT.**
- `tests/test_weekly_lineup_optimizer_service.py`: **21 passed** (19 pre-existing + 2 new: taxi-specific optimizer exclusion, `build_roster_candidates` real-Sleeper-shape reserve/taxi wiring).
- Broader targeted backend set (`test_weekly_lineup_optimizer_service.py` + every prior worker's own waiver/FAAB/canonical-state/identity/architecture/capability suite + `test_desktop_application_api.py`): **195 passed, 4 failed** -- the exact same 4 pre-existing, byte-identical-by-name failures every prior worker this cycle has reported (`test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_component_dependency`). No new failure name.
- `python -m ruff check` on the touched test file: 11 pre-existing findings (E501/I001), none in the newly-added code (verified by line number) -- zero NEW findings introduced.
- `npm run typecheck`: clean.
- `npx vitest run apps/redraft/src/lineup-explain.test.ts`: **12 passed** (9 pre-existing + 3 new).
- Full `npx vitest run`: **31 files, 513 tests passed** (510 pre-existing + 3 new) -- matches Worker 5's own documented 510 baseline exactly plus this pass's additions.
- `npm run build:redraft`: passed (only the pre-existing bundle-size warning, unchanged).
- The vitest machine-timing benchmark artifact (`docs/codex/prospective_outcomes_v1/multi_league_scale_v1/frontend_bench_results.json`) was touched by running the suite and restored to exact HEAD content via `git checkout --`, per this cycle's own established precedent -- not part of this change.

## Dev processes status

**LIVE OBSERVATION.** No Python production code was changed this pass (only a new backend test file), so no backend restart was required or performed. Backend PID **36328** (launcher parent 32328) and frontend PID **27280** were the same PIDs already running at dispatch -- both re-identity-verified via `Get-CimInstance Win32_Process` (command line matches this exact worktree) and re-confirmed listening on `127.0.0.1:18742`/`127.0.0.1:1422` at the end of this pass. The frontend WAS rebuilt (`npm run build:redraft`) to ship the TSX/CSS fix -- `vite preview` serves the on-disk `dist/` directly, so no process restart was needed for the new build to take effect (confirmed live: the fix rendered correctly on the next page load without restarting PID 27280). Fantasy Gamers restored as final active profile.

## Files changed this pass

- `desktop/apps/redraft/src/lineup-explain.ts` (new `describeExcludedLineupPlayer` + its docstring)
- `desktop/apps/redraft/src/lineup-explain.test.ts` (3 new tests)
- `desktop/apps/redraft/src/in-season.tsx` ("Not included this week" panel now renders the real per-player status/reason instead of a static fabricated sentence)
- `desktop/apps/redraft/src/redraft.css` (new `.lineup-excluded-list` rule)
- `tests/test_weekly_lineup_optimizer_service.py` (2 new tests: taxi-specific optimizer exclusion, `build_roster_candidates` reserve/taxi wiring)
- this ledger

Not touched: `marginal_roster_utility_v2`, any governed valuation code, `governed_asset_registry_service.py`, KHA/403N18th profile identity fields, any Sleeper/ESPN write path, Flaim MCP tools (never invoked), `redraft_weekly_lineup`'s own backend logic (zero Python production changes -- the one real bug found this pass was a presentation-layer discard of already-correct backend data, not a backend defect).

## Open issues for Worker B (K/DST streamer + weekly schedule/opponent/freshness)

1. Bye-week disclosure gap (see above): a bye-week player and any other genuinely-missing-projection player currently render identically ("missing projection, unknown"). If Worker B's schedule/freshness scope touches this, consider whether a real bye-week fact (available from nflverse schedules, already pulled by `weekly_game_lock_service.py` for lock purposes) could be surfaced as its own honest label distinct from "missing for an unknown reason" -- not attempted this pass since no real bye-week case was live-observable to validate against.
2. Taxi-squad live exercise remains synthetic-test-proven only (both real Sleeper leagues' taxi arrays are genuinely empty tonight) -- if either real league's roster later gains a taxi-squad player, worth a quick live re-confirmation, though the mechanism itself is now more thoroughly tested than before this pass.
3. `redraft_weekly_lineup`/`redraft_opponent_rosters` remain deliberately unconverted to the canonical-state boundary (Worker 3/4's open item, unchanged by this pass) -- Start/Sit's real live behavior does not depend on that conversion happening, per this pass's own direct confirmation above.

---

# WORKER B (CLAUDE) - K/DST STREAMER + WEEKLY SCHEDULE/OPPONENT/FRESHNESS AUDIT (2026-09-22)

Worker B dispatch HEAD: `019b80e9` (Worker A's Start/Sit exclusion-reason fix + taxi-exclusion test-gap closure), verified via `git log -1` before any edit. Worktree was clean except the 2 documented `local_exports.backup-*` dirs. This pass made no Sleeper/ESPN writes, did not touch `marginal_roster_utility_v2`, `governed_asset_registry_service.py`, or any governed valuation formula, did not touch KHA/403N18th profile identity fields, and did not attempt Flaim/MCP access.

Evidence labels: **INSPECTED CODE**, **ACTUAL TEST RESULT**, **LIVE OBSERVATION** (real HTTP/browser round trip against the real running backend/frontend tonight), **INFERENCE**.

## Real bug 1: cross-position contamination in `sleeper_streamer_actions`' unmatched-id reporting

**INSPECTED CODE + ACTUAL TEST RESULT + LIVE OBSERVATION.** While extending the K/DST streamer's own disclosure (bug 2 below), found that `sleeper_streamer_actions` (`fantasypros_kdst_consensus_service.py`) scanned EVERY `SUPPORTED_POSITIONS` (K and DST) roster player on every call, even though the real call site (`redraft_kdst_streamer`) always passes `rows` scoped to exactly ONE position per call. A real DST roster entry can never match a K-only `provider_ids` dict, so it was always reported `unmatched` during the K-only call (and vice versa for a real K entry during the DST-only call) -- pure cross-position noise, not a genuine identity-match failure. This inflated the "N unmatched Sleeper player id(s)" disclosure with irrelevant counts, and (found live, while building bug 2's own-roster-unranked disclosure) actively mislabeled the owner's own real DST (New England) as an unmatched K entry instead of a DST entry.

**Fix.** `sleeper_streamer_actions` now derives `target_positions = {row.position for row in rows}` and only scans roster players whose real catalog position is in that set. No change to `_identity`, `streamer_actions`, or any call site's signature. `rostered`/`owner`/`starters` were never corrupted by this (they only grow on a real positive match) -- only `unmatched`'s membership/count was polluted.

**ACTUAL TEST RESULT.** New `tests/test_fantasypros_kdst_consensus_service.py::test_sleeper_streamer_actions_unmatched_is_scoped_to_rows_own_position` proves a real DST roster entry is never scanned/reported during a K-only call.

**LIVE OBSERVATION, before vs after, real Fantasy Gamers league, week 3**: `unmatchedSleeperPlayerIds` counts went from 14 unmatched for K / 13 unmatched for DST (pre-fix, cross-contaminated) to 3 unmatched for K / 4 unmatched for DST (post-fix, genuinely position-scoped) -- confirmed via direct authenticated HTTP round trips before and after the backend restart.

## Real bug 2: the owner's own currently-rostered K/DST can be silently invisible when FantasyPros doesn't rank it

**LIVE OBSERVATION, before fix, real Fantasy Gamers league, week 3.** The owner's real rostered DST (New England, Sleeper id "NE") is genuinely outside FantasyPros' real current top-10 DST ECR this week. Before this fix, New England never appeared anywhere in the response -- not in `positions`, not labeled `YOUR_STARTER`, nothing -- it was only present as an anonymous, unnamed id buried in the generic `unmatchedSleeperPlayerIds` list (and, per bug 1, even mislabeled under the wrong position). The DST decision envelope's primary recommendation flatly said "Green Bay Packers (GB): ADD per FantasyPros consensus ECR." with no caveat at all that the owner's actual current DST was never evaluable. This directly undermines the streamer's own stated job ("should I keep my current K/DST or stream someone else" -- never merely rank free agents).

**Fix (`desktop_facade.py::redraft_kdst_streamer`).** Resolve the owner's own unmatched K/DST sleeper id(s), if any, to a real name/team (reusing the same first_name/last_name DST-reconstruction fallback `sleeper_streamer_actions` already uses), and:
- add a new, additive, always-present (never a missing key) response field `ownRosterUnranked: [{position, sleeperPlayerId, playerName, team}, ...]`;
- append an honest disclosure sentence to that position's `rationale`/`confidenceBasis`/`issues`;
- downgrade `confidenceState` from NOMINAL to LOW for that position whenever the owner's own current asset could not be evaluated -- never claim NOMINAL confidence while silently unable to compare the owner's own current player.

**ACTUAL TEST RESULT.** New `tests/test_redraft_kdst_streamer_own_roster_unranked_fix.py` (2 tests): the real gap scenario (own DST unranked -> named in `ownRosterUnranked`, `confidenceState: LOW`, disclosure text present in rationale/confidenceBasis/issues, K unaffected) and a regression-safety companion (no gap -> `ownRosterUnranked == []`, not a missing key; `confidenceState` stays NOMINAL).

**LIVE OBSERVATION, after fix, real Fantasy Gamers league, week 3**: `ownRosterUnranked` now returns `[{"position":"DST","sleeperPlayerId":"NE","playerName":"New England Patriots","team":"NE"}]`; DST envelope `confidenceState: LOW`; rationale reads "Green Bay Packers (GB): ADD per FantasyPros consensus ECR. Your currently rostered DST (New England Patriots (NE)) is outside FantasyPros' real current DST consensus rankings and could not be evaluated or compared by this streamer." -- and the same disclosure renders live in the browser (Chrome MCP, screenshot-confirmed) as a new banner directly under the DST recommendation card on the real Streamers tab: "Your current DST isn't in this week's rankings -- New England Patriots (NE) is outside FantasyPros' real current DST consensus and could not be evaluated or compared above." Las Vegas Enginerds (no gap this week) correctly shows no such banner and an empty `ownRosterUnranked`.

## Real bug 3 (frontend): `StreamersTab`'s own primary-row re-derivation diverged from the backend's actionable set, reintroducing the "opponent's rostered player" bug class for HOLD scenarios

**INSPECTED CODE.** `redraft_kdst_streamer`'s own primary-recommendation selection uses `_STREAMER_ACTIONABLE_RECOMMENDATIONS = {"START", "HOLD", "ADD"}` (an earlier cycle's own W6 fix). `desktop_facade.py`'s `redraft_weekly_home_actions` already correctly reuses that same backend-computed selection (`decisionEnvelopes[].primaryRecommendation`) rather than re-deriving it. But `improve-team.tsx`'s `StreamersTab` (the real "Improve Team -> Streamers" tab) independently re-derived its own "top" row inline, checking only `recommendation === "START" || "ADD"` -- omitting HOLD. Whenever the real best-actionable row for a position was HOLD (a real bench K/DST the owner already rosters but isn't starting), the UI's own re-derivation would miss it and fall through to `rows[0]`, the single best-ECR row regardless of ownership -- which can be a real opponent's rostered player (`ROSTERED_ELSEWHERE`). That is exactly the "opponent's rostered player recommended" bug class an earlier cycle already fixed for Waivers/Free Agents, reintroduced here as a presentation-layer-only regression (the backend's own selection was never wrong).

Neither real league's real roster happened to exercise this tonight (neither owner currently rosters a bench K or a second DST), so this was found by code inspection + reasoning about the exact set difference from the backend's own `_STREAMER_ACTIONABLE_RECOMMENDATIONS`, not a live-reproduced production incident -- disclosed honestly, not overclaimed as a live catch.

**Fix.** Extracted the selection into a new, pure, tested function `selectPrimaryStreamerRow` (`improve-team-explain.ts`), matching the backend's own actionable set exactly, and wired `StreamersTab` to use it instead of its own inline re-derivation. Also wired the new `ownRosterUnranked` disclosure into the same tab (bug 2 above).

**ACTUAL TEST RESULT.** 5 new tests in `improve-team-explain.test.ts` (`describe("selectPrimaryStreamerRow", ...)`), including the exact HOLD-vs-opponent scenario this closes ("selects HOLD over a better-ECR opponent-rostered row (the real bug this closes)") and a regression guard that the opponent's rostered row is never selected as primary or alternative in that case.

## K/DST FINDINGS (full checklist per dispatch)

- **Currently-rostered K/DST, both leagues -- LIVE OBSERVATION.** Fantasy Gamers: Ka'imi Fairbairn (K, YOUR_STARTER, ECR3) and New England (DST, unranked this week -- see bug 2). Las Vegas Enginerds: Cam Little (K, YOUR_STARTER, ECR8); DST correctly N/A (`roster.dst == 0`, confirmed still intact, zero DST rows/recommendations ever returned or rendered for this league, live-browser-confirmed).
- **League-specific availability / opponent's-rostered-player exclusion -- LIVE OBSERVATION + fix (bug 3).** Backend-side exclusion (`sleeper_streamer_actions`'s `ROSTERED_ELSEWHERE` classification) confirmed still intact and, after bug 1's fix, more precisely scoped than before. Frontend-side re-derivation had regressed for a HOLD scenario (bug 3, fixed).
- **Opponent/matchup context -- INSPECTED CODE, honestly absent.** `weekly_game_lock_service.py` (real `nflreadpy.load_schedules()`-backed kickoff data) is never imported or referenced anywhere in `fantasypros_kdst_consensus_service.py` or the K/DST branch of `desktop_facade.py` (confirmed by grep). Even if it were wired in, that module only exposes lock/kickoff-per-team, not opponent identity or matchup difficulty -- the underlying nflverse schedule rows it consumes DO carry `home_team`/`away_team`, but that mapping is discarded before `WeeklyGameLockResult` is built. Genuinely absent, not fixed this pass (matches Worker 1's competitor-research gap #3 and Worker 2's finding #5 for Start/Sit/Waivers -- now confirmed true for K/DST specifically too).
- **Current week -- LIVE OBSERVATION, never hardcoded.** The Streamers tab's own "NFL week" field defaults from `useWeekSelection(providerWeek, ...)`, same live-Sleeper-derived mechanism Start/Sit/Waivers already use (Worker A independently verified this same mechanism this cycle); live-confirmed both real leagues independently resolved to real Week 3 tonight.
- **Bye-week handling for streamer candidates -- INSPECTED CODE, honestly absent.** No `bye`-related code anywhere in `fantasypros_kdst_consensus_service.py` (grepped, zero matches). A bye-week K/DST would simply appear (or not) per FantasyPros' own real ECR list with no NWR-side bye flag -- consistent with the same disclosed, codebase-wide bye-week gap Worker A flagged for Start/Sit.
- **Injury/status -- INSPECTED CODE, honestly out of scope for K/DST by design.** The shared manual status-override layer (SEASON_OUT/NOT_WITH_TEAM/etc.) that Start/Sit and Waivers consume is never referenced in the K/DST streamer path; K/DST identity resolution against the owner's own ranked model is explicitly OUT_OF_RANKED_MODEL_SCOPE, a pre-existing, deliberate, disclosed design boundary, not a new gap.
- **Projection freshness / "as of" timestamp -- real, disclosed gap, fixed.** The endpoint performs a real, uncached, live FantasyPros + Sleeper read on every call (confirmed: zero caching in `fantasypros_kdst_consensus_service.py`; only the `players/nfl` catalog path is cross-request cached in `_sleeper_get_json`, rosters/consensus are not), but nothing in the response ever disclosed WHEN it was retrieved. Added `retrievedAtUtc` to the response, mirroring `redraft_free_agents`' own established `retrievedAtUtc` pattern in the same file. Live-confirmed present ("2026-09-23T00:08:37+00:00" for Fantasy Gamers).
- **Scoring rules -- INSPECTED CODE, unchanged, confirmed correct.** `consensus_rankings(..., scoring="PPR")` is hardcoded regardless of league scoring, but this is correct, not a bug: K/DST scoring never varies by PPR/half-PPR/standard (no receptions), and FantasyPros' own API scoring param only distinguishes reception-based formats. Fantasy Gamers' real PPR vs. Las Vegas Enginerds' real non-PPR/no-DST scoring difference is irrelevant to this specific external-consensus surface (which explicitly never computes an NWR point score, only relays FantasyPros' own ECR order) -- confirmed this remains honestly labeled "EXTERNAL CONSENSUS -- FANTASYPROS", never presented as an NWR-scored number.
- **KEEP CURRENT reachability -- LIVE OBSERVATION, confirmed still intact.** Fantasy Gamers' K case tonight: Ka'imi Fairbairn (ECR3) does NOT beat Eddy Pineiro (ECR2, available), so ADD is correctly primary (KEEP not forced) -- and Las Vegas Enginerds' K case: Cam Little (ECR8) does not beat Harrison Butker (ECR6, available), same correct ADD selection. Neither real league had a "starter beats every available option" case tonight to reproduce the KEEP branch live, but the underlying mechanism (`STREAMER_VERB.START = "KEEP"`, `_STREAMER_ACTIONABLE_RECOMMENDATIONS` including START) was independently re-confirmed by code read and remains covered by the existing `test_regression_fixture_6_...keep_current_wins` test, unchanged by this pass.
- **Multi-week vs. one-week -- INSPECTED CODE, already correctly supported, not forced/invented.** `STREAMER_HORIZON_OPTIONS`/`STREAMER_HORIZON_WEEKS` (`pages.tsx`, reused by `improve-team.tsx`) already drive sequential per-week FantasyPros reads for "This Week"/"Next 2"/"Next 3", capped at week 18. Minor, low-priority, NOT fixed this pass: `Math.min(18, week + offset)` can request the same week twice near the end of the season (e.g. week 18 + "Next 2" requests week 18 twice) -- a real but very low-impact edge case (duplicate, not wrong, data), flagged for a future worker rather than fixed under this pass's own small-and-targeted discipline.

## QB/TE STREAMING STATUS

**INSPECTED CODE.** Confirmed absent, not built. Grepped `src/` and `desktop/apps/redraft/src/` for QB_STREAMER/TE_STREAMER/any QB or TE streaming tool -- zero matches. The only streamer tools anywhere in this codebase are K and DST (K_STREAMER/DST_STREAMER, plus their read-only Prospective Outcomes evaluators evaluate_k_streamer/evaluate_dst_streamer, which evaluate historical K/DST streamer decisions, not a new live QB/TE tool). Per the owner's explicit instruction, no QB/TE streaming feature was built this pass.

## FRESHNESS/SCHEDULE AUDIT FINDINGS (cross-cutting)

- **Hardcoded week values -- none found in K/DST or adjacent weekly-decision paths.** Grepped `fantasypros_kdst_consensus_service.py` and the K/DST branch of `desktop_facade.py` for literal week-number assignments; the only week handling is the caller-supplied parameter, validated `1 <= week <= 18`, never defaulted to a literal.
- **Cache keys -- K/DST streamer has no cross-request caching layer at all** (see freshness finding above), so there is no cache-collision risk across leagues/weeks for this specific tool. The one cross-request cache touching this endpoint (players/nfl catalog, via `_sleeper_get_json`) is keyed on the fixed path string only, not per-league -- but that is correct and intentional (the Sleeper player catalog is genuinely global, not league-scoped; confirmed by inspection, not a bug).
- **Stale data surviving a profile switch -- LIVE OBSERVATION, no leakage found.** Live-browsed a real Fantasy Gamers -> Las Vegas Enginerds switch on the Streamers tab: K rows showed the correct, fully distinct real roster/ECR data for each league (Ka'imi Fairbairn/New England vs. Cam Little/no-DST) with no stale carryover.
- **Timestamps labeled "live" when actually cached -- none found for K/DST.** The endpoint has zero caching, so `retrievedAtUtc` (new) and the FantasyPros "authority" label are both genuinely live every call, not a stale-labeled-as-live mismatch.
- **UTC/local-time boundary bugs -- none found in the K/DST path itself** (it carries no time-zone-sensitive logic of its own). `weekly_game_lock_service.py` (used by Start/Sit, not K/DST) already uses explicit America/New_York -> UTC conversion with an honest unknown_teams fallback for unparseable kickoff times -- inspected as part of confirming K/DST does NOT use it, not independently re-audited for bugs this pass (out of this pass's own scope; Worker A already exercised it live for Start/Sit this cycle).

## LIVE VERIFICATION -- all 4 real leagues, exact evidence

- **Fantasy Gamers** (`941b99ade350410391b1b67c0890af79`): `POST /api/v1/redraft/kdst/streamer {"week":3}` -> 200. K: primary ADD Eddy Pineiro (ECR2, real starter Ka'imi Fairbairn ECR3 shown as alternative/YOUR_STARTER), 3 unmatched K ids (post-fix). DST: primary ADD Green Bay Packers (ECR5), `ownRosterUnranked` correctly names New England Patriots (NE), DST `confidenceState: LOW` with the real disclosure text, 4 unmatched DST ids (post-fix). Both the JSON response and the live-rendered browser UI (Chrome MCP, screenshot-confirmed) match exactly, including the new "Your current DST isn't in this week's rankings" banner.
- **Las Vegas Enginerds** (`6687d2b3aa21450ea0fc9e1792d461ff`): same endpoint -> 200. K: primary ADD Harrison Butker (ECR6), real starter Cam Little correctly YOUR_STARTER/ECR8/START-labeled in the raw table. DST: zero rows returned, zero recommendation, `confidenceState: UNAVAILABLE`, rationale "This league has no DST roster slot; DST pickups are never recommended." -- live-browser-confirmed ("No available recommendation / No DST streamer read for Week 3"), `ownRosterUnranked` empty (no gap this week). No-DST-slot enforcement (an earlier cycle's own fix) confirmed still fully intact.
- **KHA** (ESPN, `fb1c49402c7644a99120197d41344bbb`): same endpoint -> 409, non-crashing, via direct authenticated HTTP, unchanged from every prior cycle's documented finding.
- **403 N 18th** (ESPN, `4b4a990faf124ce7a5d612537ba5943b`): same -> 409, same behavior, via direct authenticated HTTP.
- Final active profile restored to Fantasy Gamers, matching every prior worker's own convention.

## TESTS

**ACTUAL TEST RESULT.**
- New: `tests/test_fantasypros_kdst_consensus_service.py::test_sleeper_streamer_actions_unmatched_is_scoped_to_rows_own_position` (1 test, bug 1).
- New: `tests/test_redraft_kdst_streamer_own_roster_unranked_fix.py` (2 tests, bug 2).
- New: `improve-team-explain.test.ts::describe("selectPrimaryStreamerRow", ...)` (5 tests, bug 3).
- Targeted backend combined set (K/DST + waivers + canonical-state + capability + identity-boundary + architecture-wiring + `test_desktop_application_api.py`, 22 files): 235 passed, 4 failed -- the exact same 4 pre-existing, byte-identical-by-name failures every prior worker this cycle has reported (`test_dynasty_facade_composes_real_governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_component_dependency`). No new failure name.
- `python -m ruff check` on every touched Python file: `fantasypros_kdst_consensus_service.py` 13 findings, byte-identical to a `git stash` baseline run (zero new). `desktop_facade.py` 108 findings (down from a 111-finding baseline, i.e. fewer, not more) -- confirmed zero new E501/etc. findings on any of this pass's own added lines by direct line-number check (4 real E501s from this pass's first draft were found and fixed before this final count). New test files: zero ruff findings.
- `python -m py_compile` on all modified Python: passed.
- `npm run typecheck`: clean.
- `npx vitest run apps/redraft/src/improve-team-explain.test.ts`: 31 passed (25 pre-existing + 6 new -- but the file's real net addition is the 5-test `selectPrimaryStreamerRow` describe block; 31 = 26 pre-existing-in-this-file + 5 new).
- Full `npx vitest run`: 31 files, 518 tests passed (513 pre-existing baseline + 5 new). The vitest machine-timing benchmark artifact was touched by running the suite and restored to exact HEAD content via `git checkout --`, per this cycle's own established precedent.
- `npm run build:redraft`: passed (only the pre-existing bundle-size warning, unchanged).

## A genuinely pre-existing, NOT-caused-by-this-pass failure found while broadening test scope (flagging, not fixing)

**ACTUAL TEST RESULT + INSPECTED CODE.** `tests/test_weekly_home_sleeper_fetch_caching.py` has 2 failing tests (`test_weekly_home_actions_fetches_rosters_and_players_exactly_once`, `test_standalone_sub_calls_outside_weekly_home_still_fetch_rosters_fresh_every_time`) that are not among the cycle's previously-documented "exact 4" -- no prior worker tonight actually ran this specific file. Confirmed via `git stash` that both failures reproduce identically on the pre-dispatch baseline (`019b80e9`), i.e. genuinely pre-existing, not introduced by this pass. Root cause (inspected, not fixed -- out of this pass's K/DST scope): Worker 4's canonical-state conversion of `redraft_free_agents` (and, by the same pattern, likely `redraft_trade_analysis`/`redraft_trade_finder`/`redraft_trade_package_search`/`redraft_weekly_projections`) calls `_resolve_canonical_league_state()` (which internally fetches `league/{id}/rosters` via `_sleeper_get_json`) and then also performs its own second, separate `_sleeper_get_json(sleeper, f"league/{league_id}/rosters")` fetch a few lines later -- a real double live-fetch for every STANDALONE call to one of these 5 converted endpoints (the thread-local per-request cache that would dedupe this is only turned on during `redraft_weekly_home_actions`'s own five sub-calls, so a normal, everyday standalone Waivers/Free-Agents-page open pays this cost twice). Functionally harmless (both fetches return the same live data), but a real, real-money latency/API-load regression from Worker 4's conversion, unrelated to K/DST. Flagged precisely for Worker C or a future dedicated pass -- not fixed here (out of scope, and fixing 5 converted callers this worker did not build carries real regression risk this late without the same deep context Worker 3/4 had).

## DEV PROCESSES STATUS

**LIVE OBSERVATION.** Python backend changed this pass -> restarted (required, backend does not auto-reload). Old PID (36328, launcher parent 32328, Worker 5's own documented PID) stopped; new backend launched via the exact same startup-credential contract `desktop/scripts/nwr_release_gate_smoke.ps1` uses (RedirectStandardInput a one-shot {apiToken, startupProofKey} JSON file, same dev token `nwr-desktop-development-token-only-000000000000`) rather than the smoke script itself (to avoid an unnecessary extra real Sleeper re-import for a Python-only restart). Final, identity-verified PIDs: backend listener 35416 (launcher parent 25156), confirmed via `Get-CimInstance Win32_Process` command-line match against this exact worktree (`C:\NWR\prospective-outcomes-v1\scripts\run_nwr_desktop_api.py ... --repo-root C:\NWR\prospective-outcomes-v1`) and `Get-NetTCPConnection -LocalPort 18742 -State Listen`. Frontend was rebuilt (`npm run build:redraft`, TSX/CSS changes) but its process was NOT restarted -- `vite preview` serves the on-disk dist/ directly, confirmed live (the new DST disclosure banner rendered on the next page load with no frontend process restart); frontend PID 27280 (Worker 5's own original PID, still alive, re-identity-verified, listening on 127.0.0.1:1422). Fantasy Gamers restored as final active profile.

Three small runtime-only files (`backend_creds_workerb.json`, `backend_workerb.log`, `backend_workerb.log.err`) remain in the repo root, untracked, held open by the still-running backend process (stdin/stdout redirects) -- could not be deleted this pass without killing the backend the next worker needs alive. Do not `git add` them. They will free up once a future worker restarts or stops this backend process; delete them then. No credential VALUE is at risk (the dev token is already public in every prior ledger entry and this dispatch prompt itself).

## FILES CHANGED

- `src/services/fantasypros_kdst_consensus_service.py` (bug 1 fix: `sleeper_streamer_actions` scan scoped to `rows`' own position(s))
- `src/application/desktop_facade.py` (bug 2 fix: `ownRosterUnranked` field + rationale/confidenceBasis/issues/confidenceState disclosure in `redraft_kdst_streamer`; added `retrievedAtUtc` freshness field)
- `desktop/packages/contracts/src/index.ts` (optional `ownRosterUnranked`/`retrievedAtUtc` fields on `KdstStreamerResult`, new `KdstStreamerOwnRosterUnrankedEntry` type)
- `desktop/apps/redraft/src/improve-team-explain.ts` (new, tested `selectPrimaryStreamerRow` -- bug 3 fix)
- `desktop/apps/redraft/src/improve-team.tsx` (`StreamersTab` now uses `selectPrimaryStreamerRow` instead of its own inline re-derivation; renders the new own-roster-unranked disclosure banner)
- `tests/test_fantasypros_kdst_consensus_service.py` (1 new test, bug 1)
- `tests/test_redraft_kdst_streamer_own_roster_unranked_fix.py` (new file, 2 tests, bug 2)
- `desktop/apps/redraft/src/improve-team-explain.test.ts` (5 new tests, bug 3)
- this ledger

Not touched: `marginal_roster_utility_v2`, any governed valuation code, `governed_asset_registry_service.py`, KHA/403N18th profile identity fields, any Sleeper/ESPN write path, Flaim MCP tools (never invoked), QB/TE streaming (confirmed absent, not built per owner's explicit instruction), `weekly_game_lock_service.py` itself (inspected only, to confirm K/DST's real non-use of it).

## OPEN ISSUES FOR NEXT WORKER (Claude Worker C: multi-league profile leakage + browser dogfood + frontend/backend contract bugs)

1. **Opponent/matchup context for K/DST remains genuinely absent** -- `weekly_game_lock_service.py` has real kickoff data but discards home_team/away_team before returning; extending it (or a sibling function) to also expose real opponent identity per team would be the natural next step if the owner wants this, but it is a real, scoped, new-data-surfacing change, not a bug fix -- flag for owner prioritization, not a silent addition.
2. **Bye-week-specific disclosure remains absent for K/DST** (same codebase-wide gap Worker A flagged for Start/Sit) -- a bye-week K/DST candidate is currently indistinguishable from any other FantasyPros-ranked-or-not candidate.
3. **Minor, low-priority**: `STREAMER_HORIZON_WEEKS`'s `Math.min(18, week + offset)` can request the same week twice near the end of the season (week 17/18 + a 2-3-week horizon) -- duplicate, not wrong, data; not fixed this pass (small, cosmetic, no real leagues are near week 17/18 yet).
4. **A genuinely pre-existing, unrelated-to-K/DST double-live-fetch regression** in Worker 4's canonical-state conversion of `redraft_free_agents` (and likely 4 sibling converted callers) -- see the dedicated section above. Real, precisely localized, not fixed this pass (out of scope, real regression risk touching code this worker did not build).
5. Three untracked runtime files (`backend_creds_workerb.json`, `backend_workerb.log`, `backend_workerb.log.err`) sit in the repo root, held open by the live backend process (PID 25156/35416) -- safe to delete once that process is next restarted/stopped; never commit them.
6. All of Worker A's own open issues (bye-week disclosure, taxi-squad live exercise, `redraft_weekly_lineup`/`redraft_opponent_rosters` canonical-boundary conversion) and Worker 5's own open issues stand, unchanged by this pass.
