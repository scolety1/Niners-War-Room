# Dynasty League Import V1 — Durable Ledger

New, bounded feature-build cycle: implementing a real Sleeper DYNASTY league
import into the Dynasty app. Each worker appends its own dated section.
Do not delete or rewrite a prior worker's section — append only, correct
forward.

---

## Worker 1 — Architecture investigation, real league data capture, design (2026-09-18)

**Branch/worktree:** `upgrade/nwr-prospective-outcomes-v1-20260914` at
`C:\NWR\prospective-outcomes-v1`. Started at HEAD `37dc156a` (clean, matched
origin). This section is a docs-only commit — no application code was
written this pass (see "Why no code this pass" below). Did not push, did
not touch `main`, did not force anything.

### Methodology key

- **INSPECTED CODE** — read directly from the repo.
- **ACTUAL TEST RESULT** — a real pytest/vitest run.
- **LIVE OBSERVATION** — a real running process/browser/API hit, observed
  directly.
- **INFERENCE** — a conclusion drawn from the above, explicitly labeled as
  such, never presented as a fact.

---

### PART A — Dynasty's existing architecture (INSPECTED CODE)

**Headline finding: Dynasty has ZERO live per-owner roster/league concept
anywhere today — frontend or backend — confirmed by direct inspection, not
just the prior cycle's grep.** `grep -rniE "sleeper" desktop/apps/dynasty/src`
returns zero file matches. The only "roster" language in the Dynasty
frontend is `system.tsx`'s Planning Console module, whose own copy says
"Map positional pressure and manual succession notes **without automated
roster hydration**" and "Confirm current **owner-entered** roster state" —
i.e. the app's own UI text already, explicitly, honestly discloses that
roster data is manual-only today. This independently confirms the prior
cycle's finding rather than just repeating it.

**Dynasty's backend surface is exactly 3 methods** on
`DesktopBackendFacade` (`src/application/desktop_facade.py`):
`dynasty_bootstrap` (L566), `dynasty_workspace` (L724), `dynasty_asset`
(L1234). All three route through one shared private builder,
`_owner_snapshot()` -> `_build_owner_snapshot()` (L6667-6763), which loads:
- `load_governed_asset_registry(...)` — the hash-gated valuation core
  (`governed_asset_registry_service.py`, `CURRENT_BOARD_SHA256` /
  `ROOKIE_BOARD_SHA256` / `BLOCKED_ROOKIES_SHA256`-gated).
- `load_unified_research_preview(...)`, `load_outcome_v3_display(...)`,
  `load_owner_rookie_board(...)` — all read-only, repo-tracked docs inputs.
- `compose_owner_asset_evidence(...)`, `build_player_compare_universe(...)`,
  `owner_rankings_frame(...)` — pure composition over the above, no Sleeper
  call anywhere in the chain.

**"Owner" in Dynasty today means the local human annotating a market-wide
board (Watch/Target/Avoid tags, a personal board, a decision journal, saved
scenarios) — NOT a fantasy-league roster.** This is a real, load-bearing
distinction, not semantics: `personal_workspace_service.py`'s
`_validate_workspace_location()` (L936-941) explicitly **forbids** the
workspace root from having `local_exports` anywhere in its path
(`PROTECTED_WORKSPACE_PATH_PARTS` includes `"local_exports"` verbatim), and
the real default (`DEFAULT_WORKSPACE_ROOT`, used because
`scripts/run_nwr_desktop_api.py` never passes `workspace_root=` when
constructing the facade) is `C:\NWR_SHARED_DATA\nwr_personal_workspace_v1`
— a path **outside every worktree, shared across all of them.** LIVE
OBSERVATION: that directory already exists on this machine with real data
(`stores/personal_board.json`, `stores/saved_scenarios.json`, both dated
2026-09-16 — a prior worker's own write-cycle testing). This directly
corrects one premise in this pass's own dispatch: the "same isolated
`local_exports/` pattern" claim is true for the **governed valuation
inputs' artifact cache** (`market_baseline_service.DEFAULT_ARTIFACT_DIR` =
`<repo_root>/local_exports/refresh_data/dynastyprocess_market_baseline`,
confirmed worktree-relative via `Path(__file__).resolve().parents[2]`) but
is **false** for the owner-annotation workspace, which is deliberately kept
OUT of `local_exports` by a real validation guard and lives in a single
shared external location today. Any new Dynasty league-import design must
not casually reuse `personal_workspace_service.load_store`/`workspace_root`
for league-roster data — that module's contract is "local-only annotation
overlay, never inside a regenerable source path," a different category of
data with a different durability contract than a roster import cache.

**The governed valuation board itself is git-tracked docs, not
`local_exports`.** `FROZEN_DYNASTY_BOARD_RELATIVE` =
`docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/
rebuilt_full_player_board_value_review_rows.csv`; the rookie board is
`docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/
MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv`. Both are version-controlled repo
paths, resolved via `self.repo_root / <RELATIVE constant>` — not
`local_exports`. This worktree's own `local_exports/model_v4/` only
contains `draft_prep/` and `workouts/` subfolders (confirmed via `find`) —
no `current_value/` tree exists here at all; the governed board Worker 6 of
the prior cycle saw rendering "240 Finished V1 assets" was read from the
git-tracked `docs/hq/model/...` path, not from `local_exports`.

**A real, load-bearing surprise: the ALREADY-ADMITTED governed board CSV
carries a real, but FROZEN and STALE, ownership snapshot of this exact
league.** The board's columns include `is_my_team`, `roster_team_id`,
`roster_team_name`, `roster_status` per current-player row (confirmed by
reading the CSV header + real rows directly). Filtering `is_my_team==1`
returns real rows with `roster_team_id=7`, `roster_team_name="Niners"` —
the exact real roster/team identity this task independently confirmed live
via the Sleeper API (see Part B). The CSV's own folder name dates this
snapshot to **2026-07-08** — roughly 10 weeks stale versus today
(2026-09-18, real season week 2). Diffing the frozen `is_my_team=1` player
list against today's real live roster-7 player list (Part B) shows real
drift: 2 frozen-board "Niners" players (`6130` Devin Singletary, `11650`
Luke McCaffrey) are **not** on the real live roster, and several real live
roster-7 players (`11786`, `13296`, `13311`, `13320`, `13402`, `8148`,
`9997`) are **not** flagged `is_my_team=1` in the frozen board — real
season-long roster churn (adds/drops/trades), exactly as expected for a
10-week-stale snapshot. `grep`-confirmed: **nothing in
`governed_asset_registry_service.py` or `desktop_facade.py` reads
`is_my_team`/`roster_team_id`/`roster_team_name`/`pool_status` at all** —
these columns exist in the admitted data but are entirely unconsumed and
unsurfaced by the current Dynasty pipeline. Same pattern for draft picks:
`_pick_assets()` (`governed_asset_registry_service.py` L237-258) builds
`asset_id = f"pick:2026:{row['pick_label']}"` with a `current_owner` /
`is_nwr_pick` field sourced from a **"Frozen 2026 Draft Context"** —
single-season-only (no 2027/2028 pick assets exist in the registry at all,
even though real 2027/2028 picks are actively being traded in the real
league — see Part B).

**A second, independent piece of evidence for the same conclusion:**
`player_id=9493` for Puka Nacua in the governed board is the exact same
numeric ID Sleeper's own player catalog uses for Puka Nacua — confirmed by
cross-referencing against the real live roster fetch in Part B, where the
same small-integer ID scheme appears (`"9226"`, `"9224"`, `"8126"`, etc.
match `9226` De'Von Achane / `9224` Chase Brown / `8126` Wan'Dale Robinson
in the frozen board's own `is_my_team=1` rows). **Current-player `asset_id`
values (`current:{player_id}`) are therefore directly Sleeper-ID-keyed —
no GSIS/canonical crosswalk is needed to join a live Sleeper roster fetch
to the current-player portion of the governed board.** Rookies are a real
exception: the rookie board's own `player_id` values are a different,
synthetic scheme (e.g. `LOV121782` for Jeremiyah Love, `identity_method:
EXACT_SHARED_GSIS_ID`) — NOT a Sleeper numeric ID — so annotating rookie
ownership (taxi-squad rookies especially) genuinely does need an identity
crosswalk that does not yet exist in an obviously reusable form; flagged
as an open item, not solved this pass.

**Redraft's reusable vs. non-reusable Sleeper machinery** (read
`sleeper_import_service.py`, `sleeper_redraft_owner_service.py`,
`sleeper_player_catalog_cache.py`, `sleeper_league_context_service.py` in
full):

- **Genuinely reusable, generic, zero Redraft-specific behavior:**
  - `SleeperHttpClient` (`sleeper_import_service.py` L24-31) — a ~7-line
    class wrapping `urllib.request.urlopen`, `GET`-only by construction (no
    verb parameter, no body/data argument anywhere), `api_base` swappable.
    This is the correct low-level client for Dynasty to reuse as-is.
  - `SleeperPlayerCatalogCache` / `get_sleeper_player_catalog`
    (`sleeper_player_catalog_cache.py`) — process-wide, TTL-bounded,
    thread-safe cache for the `players/nfl` catalog specifically. Fully
    generic (keyed only on the literal path, no Redraft-shaped data);
    directly reusable if Dynasty ever needs full-catalog player-name
    resolution for non-governed-board players (e.g. a Sleeper roster
    player who isn't yet a governed asset).
  - `sleeper_league_context_service.py` — pure functions over raw Sleeper
    JSON (`parse_current_nfl_week`, `team_name_by_roster_id`,
    `build_standings_context`, `build_playoff_context`,
    `build_week_matchup_context`). Currently wired only into Redraft's
    in-season pages, but every function takes raw dicts/lists and returns
    plain dicts — zero Redraft-specific types. `team_name_by_roster_id` in
    particular is exactly the team-naming convention a Dynasty league
    profile should reuse (so a "Niners"/"Rocky Mountain High" name never
    drifts between the two apps).
- **NOT reusable — Redraft-specific, must not be dragged into Dynasty:**
  - `import_sleeper_redraft_profile` (`sleeper_redraft_owner_service.py`)
    builds a `LeagueProfile`/`RosterSettings`/`ScoringSettings`/
    `DraftContext` from `redraft_engine_v1_service` — Redraft's own
    profile shape, including its `_SCORING_FIELDS` map that translates
    Sleeper scoring keys into Redraft's own **projection stat fields**
    (`passing_yards`, `receiving_td`, etc.) for **draft-pool valuation**.
    Dynasty must not call this or anything downstream of it — the owner's
    explicit instruction ("Do not run dynasty decisions through redraft
    valuation just to make the interface populate") rules this out
    structurally, not just by preference: Redraft's scoring/valuation is
    tied to `marginal_roster_utility_v2` and Redraft's own draft-pool
    model, both out of this cycle's hard boundary regardless.
  - `reconcile_sleeper_profile_identities` (`redraft_engine_v1_service.py`
    L512) operates over Redraft's own `LeagueProfile` file store — not
    reusable as a function, though the identity-reconciliation *pattern*
    (never silently drop an unresolved player; report it) is worth
    following.
  - `export_sleeper_snapshot` (`sleeper_import_service.py`) is a one-shot
    CSV-dump tool with its own bespoke row-shaping helpers
    (`_league_settings_rows`, `_roster_rows`, `_future_pick_rows`, etc.) —
    useful as a reference for "what does a full read-only Sleeper pull
    look like," not as a function to call directly for a live, structured
    Dynasty profile (it writes flat CSVs, not a queryable data model).

**Curiosity, not load-bearing:** `sleeper_import_service.py`'s own
`DEFAULT_LEAGUE_ID` constant (L13) has been `"1344772855908290560"` — the
exact same real league ID this task was dispatched against — since a
commit on **2026-08-11** (`git log`, confirmed), over five weeks before
this task described the league as newly "identified." No snapshot data
from that constant was ever materialized in this worktree
(`local_exports/sleeper/` does not exist) — this is a dormant default
value, not evidence of a prior real import. Noted for completeness only.

---

### PART B — Real, read-only Sleeper API investigation (LIVE OBSERVATION)

**Method:** reused `SleeperHttpClient` exactly as-is (no modification) from
a standalone script
(`fetch_dynasty_league.py`, run from this session's scratch directory, not
committed to the repo) against the real league id
`1344772855908290560`. Six real `GET` calls issued: `league/{id}`,
`league/{id}/rosters`, `league/{id}/users`, `league/{id}/traded_picks`,
`league/{id}/drafts`, `state/nfl`. **Zero-writes verification:**
`SleeperHttpClient.get_json` is structurally GET-only — `urlopen(url,
timeout=30)` with no HTTP method or body argument anywhere in the call
chain, confirmed by direct inspection of the class (7 lines total); no
other Sleeper client or write-capable call was invoked this pass. This
matches the "GET-only, verify zero writes" standard this project has used
elsewhere; for a pure remote-read investigation (no local mutable state
involved) the applicable proof is "only `get_json`/`GET` was ever called,"
not a before/after byte-diff (there is no local file being written to by
Sleeper's own state).

**League settings — real, confirmed CUSTOM scoring, non-PPR:**
- Name: **"Las Vegas Enginerds"** (confirmed exact match). `status:
  "in_season"`. `season: "2026"`. `league_id: "1344772855908290560"`
  (confirmed exact match).
- `num_teams: 10`. `type: 2` (Sleeper's dynasty league-type code; the
  draft's own `scoring_type` metadata independently says
  `"dynasty_std"`).
- **Scoring is real and custom, and is NOT PPR**: `rec: 0.0` (zero points
  per reception — standard, not PPR, despite `rec_fd: 0.4` / `rush_fd: 0.4`
  first-down bonuses existing). `pass_td: 3.0`, `pass_2pt: 2.0`, `rec_2pt:
  2.0`, `rush_2pt: 2.0`, `pass_int: -1.0`, `fum_lost: -1.0`, `pass_yd:
  0.0333...` (1pt/30yd — slightly below the common 1pt/25yd default),
  `rush_yd: 0.1`, `rec_yd: 0.1`, `rec_td: 4.0`, `rush_td: 4.0`. Real kicker
  granularity (`fgm_0_19: 2.0` ... `fgm_50p: 4.0`, with an odd redundant
  `fgm_50_59: 0.0` alongside `fgm_50p: 4.0`). All `pts_allow_*` (defense
  points-allowed bands) are `0.0` — consistent with the roster having **no
  DEF/DST slot at all** (see below), so those fields are simply unused by
  this league, not a data gap.
- `roster_positions`: `["QB","RB","RB","WR","WR","WR","TE","FLEX","FLEX",
  "K","BN"x14]` — **24 total slots, no DEF/DST slot anywhere.** This
  league does not roster team defenses.
- `taxi_slots: 0` — confirmed by cross-checking every one of the 10 real
  rosters: **every roster's `taxi` field is literally `null`**, no
  exceptions. `reserve_slots: 2` — real, populated per-roster (e.g. roster
  7 has `reserve: ["11638", "12484"]`, 2 entries, consistent with the
  setting).
- `playoff_teams: 4`, `playoff_week_start: 16`, `trade_deadline: 99` (no
  real trade deadline), `pick_trading: 1` (enabled — matches the real,
  heavy pick-trading activity found below), `waiver_type: 2` (FAAB),
  `waiver_budget: 100`, `max_keepers: 1`, `draft_rounds: 5` (the
  *currently configured* league-level draft_rounds — see drafts below for
  why this doesn't fully describe real draft history).

**Rosters — roster 7 confirmed as Niners/mcolety1, real drift from the
frozen governed-board snapshot already noted in Part A:**
- `roster_id: 7`, `owner_id: "1352768154031374336"` — **exact match** to
  the task's stated owner ID.
- `co_owners: ["1000507609050337280"]` — a real co-owner on this roster,
  resolved via `users.json` to `display_name: "scolety"` (distinct Sleeper
  account from `mcolety1`). Real, disclosed finding, not asked for by the
  task but present in the raw data — worth the owner's awareness since it
  means Sleeper itself recognizes two accounts with write access to this
  roster (irrelevant to a read-only import, but relevant if any future
  write-capable feature is ever built).
- Real record: `wins: 1, losses: 0, ties: 0` (1-0, matches `state/nfl`'s
  real `week: 2` — the team's only game so far). `fpts: 108.10`, `ppts:
  144.70` (points scored vs. optimal-lineup points possible).
- Real roster: 28 total players
  (`["11564","11624","11638","11646","11786","12484","12493","12519",
  "13296","13311","13320","13402","4881","5844","5870","5892","5947",
  "6783","6803","8110","8121","8126","8148","9224","9226","9480","9754",
  "9997"]`), `reserve: ["11638", "12484"]` (2, matches `reserve_slots:
  2`), `taxi: null` (matches `taxi_slots: 0` league-wide).
- `users.json` independently confirms `user_id: "1352768154031374336"` ->
  `display_name: "mcolety1"`, `metadata.team_name: "Niners"` — **exact
  match to the task's stated username and team name.**
- All 10 other rosters/owners captured too (needed for opponent-ownership
  context later) — real user_ids, team_names, records, `co_owners` arrays
  (only rosters 6 and 7 have a `co_owners` entry) — see raw file
  `raw/rosters.json` / `raw/users.json` in this session's scratch dir
  (not committed to the repo; a future worker should re-fetch live rather
  than rely on a point-in-time scratch copy, since roster contents change
  weekly in-season).

**Draft-pick ownership — real, confirmed non-trivial (dynasty pick trading
is genuinely active in this league):**
- Two real drafts exist for season 2026, both `status: "complete"`:
  `draft_id: "1353280212753723392"` (5 rounds, the current/latest —
  matches `league.draft_id` and `league.settings.draft_rounds`) and an
  earlier `draft_id: "1344772856487108608"` (24 rounds, `player_type: 2` —
  almost certainly the original startup draft). Both already happened;
  neither is a live/upcoming draft to prep for right now.
- `league/{id}/traded_picks` returned **31 real trade-delta records**
  spanning seasons 2026, 2027, and 2028. Real example for roster 7
  (Niners): the league's own 2026 R1/R3/R4 picks **originally belonging to
  roster 7 have all been traded away** (to rosters 2, 5, and 1
  respectively), while roster 7 **acquired** roster 1's 2026 R2, roster
  2's 2026 R1, roster 2's 2026 R2, and roster 2's 2028 R1. Because Sleeper's
  `traded_picks` endpoint only returns picks that have moved at least once
  from their original owner (untraded picks are implicit, not listed),
  **computing a team's full current draft-pick capital for a future season
  requires reconciling this delta list against the league's own default
  per-season round count — Sleeper does not return "your total picks"
  directly.** This is real complexity, not something to gloss over in
  Worker 2's implementation; flagged explicitly in the design below and in
  Open Issues.
- The governed board's own pick-ownership context
  (`_pick_assets`/`"pick:2026:{pick_label}"`) only covers 2026 and is
  already a "Frozen 2026 Draft Context" (Part A) — it has no 2027/2028 pick
  assets at all, even though real 2027/2028 pick trades already exist in
  this league today.

**Real NFL/season state:** `state/nfl` returned `week: 2, season: "2026",
season_type: "regular", season_start_date: "2026-09-09",
season_has_scores: true` — internally consistent with the real roster
records above (1 real game played) and with today's real date
(2026-09-18).

---

### PART C — Design: smallest complete import path

**Scope of this design:** a new, Dynasty-shaped "league profile" concept
that ANNOTATES the existing governed board with live ownership/roster/pick
context for one real league at a time — it does not compute or alter any
valuation, and it does not touch `governed_asset_registry_service.py`,
`CURRENT_BOARD_SHA256`, or the underlying board CSV.

**1. New backend service — `dynasty_sleeper_league_service.py`
(proposed name, not yet created).**

Responsibilities, deliberately kept separate from valuation:
- `fetch_dynasty_league_snapshot(league_id, *, client=None) ->
  DynastyLeagueSnapshot` — issues the same 5 real, read-only GET calls
  Part B used (`league/{id}`, `league/{id}/rosters`, `league/{id}/users`,
  `league/{id}/traded_picks`, `league/{id}/drafts`), reusing
  `SleeperHttpClient` as-is (no subclassing, no modification). Returns a
  small, frozen dataclass bundle: league settings (verbatim
  `scoring_settings`/`roster_positions`/`taxi_slots`/`reserve_slots`/etc.,
  never silently reinterpreted), the full roster list (owner_id,
  roster_id, players, starters, reserve, taxi, co_owners), the user/team-
  name map (reuse `sleeper_league_context_service.team_name_by_roster_id`
  verbatim rather than writing a second team-naming rule), and the raw
  `traded_picks` delta list.
- `resolve_owned_pick_capital(league_settings, traded_picks, *,
  seasons) -> dict[roster_id, list[PickOwnership]]` — the real
  reconciliation Part B flagged as non-trivial: for each requested season,
  start from "every roster owns 1 pick per round of that season's default
  round count" (the *startup*/rookie draft's own `settings.rounds` — note
  the two real drafts found in Part B have *different* round counts, 24
  vs 5; Worker 2 must decide, and explicitly disclose, which one is the
  real "default future-season round count" — this is a genuine, real
  ambiguity in the source data, not a bug to paper over), then apply every
  `traded_picks` delta in order. Must never silently drop an unresolved
  trade record.
- `annotate_ownership(governed_board_rows, roster_snapshot) ->
  list[AnnotatedAssetRow]` — a **pure join, no scoring**: for each
  `current:{player_id}` asset row, look up `player_id` directly against
  the live roster's Sleeper player IDs (Part A confirmed this is a direct
  key match, no crosswalk needed for current players) and attach a live
  `myRoster: bool`, `rosterTeamId`, `rosterTeamName`, `rosterSlotStatus`
  (`starter`/`bench`/`reserve`/`taxi`, taxi will always be absent for this
  specific league but the field should still exist generically) — a live,
  always-current counterpart to the frozen `is_my_team`/`roster_team_id`/
  `roster_status` columns Part A found already baked into (and unused
  from) the admitted CSV. For `rookie:{player_id}` assets, the direct-key
  join does **not** apply (Part A: rookie board uses a synthetic ID, not
  a Sleeper ID) — Worker 2 must either build a real name+college+position
  crosswalk or, more honestly for a first pass, surface rookie ownership
  as "unresolved, needs identity crosswalk" rather than silently guessing
  a match. For `pick:{season}:{pick_label}` assets, extend
  `_pick_assets`-style rows for every season actually found in
  `traded_picks` (2026/2027/2028 today, not just 2026), sourced from
  `resolve_owned_pick_capital` above — genuinely new pick-asset rows, not
  a mutation of the existing frozen 2026-only ones.
- Explicit non-goal, stated in the module docstring: this service **never
  computes or adjusts any score, rank, or value** — every numeric ranking
  field on an annotated row is byte-identical to the governed board's own
  value; only ownership/roster-context fields are added.

**2. Persistence location — worktree-isolated `local_exports/`, following
Redraft's own profile-store convention, explicitly NOT
`personal_workspace_service`'s shared workspace.**

Proposed path: `local_exports/dynasty_v1/league_profiles/<profile_id>.json`
(mirrors Redraft's `local_exports/redraft_v1/profiles/<profile_id>.json`
shape/precedent exactly) plus
`local_exports/dynasty_v1/league_snapshots/<profile_id>/<timestamp>.json`
for the raw resync history (so a bad resync is always recoverable, same
spirit as Redraft's `sleeper_imports/` receipts). Rationale for choosing
`local_exports` over the shared `C:\NWR_SHARED_DATA` workspace path:
(a) it is per-worktree, isolated, and disposable the same way every other
piece of this cycle's Dynasty test state already is; (b) it is a
roster/league **import cache** analogous to Redraft's profile store, not a
durable personal annotation the owner hand-edits — a fundamentally
different data category from what `personal_workspace_service`'s guard is
protecting; (c) `_validate_workspace_location` would actively reject
`local_exports` as a workspace root anyway, so reusing that module's
storage layer for this purpose isn't even mechanically available without
either subverting the guard (wrong) or passing an explicit non-default
`workspace_root` (defeats the guard's purpose). Flagged explicitly as a
judgment call for Worker 2/the owner to confirm, not a settled fact: if the
owner wants league-profile data to have the SAME durability guarantee as
the personal workspace (survive a `local_exports` wipe/regeneration), the
alternative is a *third* sibling location next to
`C:\NWR_SHARED_DATA\nwr_personal_workspace_v1` — not recommended by this
worker (mixes a multi-worktree-shared path with per-league real data that
should stay test-isolated during this build-out), but worth a single
explicit confirmation before Worker 2 writes anything real.

**3. Composition with the governed valuation board — annotate, never
recompute.**

`dynasty_bootstrap()`/`dynasty_workspace()`/`dynasty_asset()` should each
gain an **optional** parameter (e.g. `league_profile_id: str | None`) that,
when set, calls `annotate_ownership()` on top of the *already-built*
`_OwnerSnapshot` (i.e. after `_build_owner_snapshot()` returns, not inside
it) and merges the extra ownership fields onto each asset/ranking row
before serializing the payload. When `league_profile_id` is `None` (no
Dynasty league imported yet, or the owner is looking at the pure market
board), behavior must be **byte-identical** to today — this is the
concrete mechanism for the hard-boundary requirement "compose without the
valuation core being modified." `governed_asset_registry_service.py`
itself, `CURRENT_BOARD_SHA256`, and `_build_owner_snapshot()`'s own
internals should not need a single line changed.

**4. Custom-scoring disclosure.**

Checked whether any Dynasty recommendation surface implicitly assumes a
scoring format: `owner_rankings_frame`, `build_player_compare_universe`,
and every field in `rebuilt_full_player_board_value_review_rows.csv`
(`nwr_dynasty_score`, `league_rank`, `market_rank`, etc.) are built from
dynasty **startup-ADP/consensus-rank/production-share** inputs — real-world
per-game receptions/yards-style production components, not a simulated
weekly fantasy-points total under any specific scoring rule. **No Dynasty
scoring surface found this pass computes or implies a specific PPR/standard
points value** — the entire model is rank/percentile-based, which is
inherently format-agnostic in the way Part C's dispatch anticipated. The
real custom scoring settings captured in Part B (non-PPR, 2pt-conversion
bonuses, no DST) therefore do **not** need to be threaded into any existing
Dynasty score. What DOES need explicit disclosure: if/when Worker 2 builds
any weekly or seasonal points-projection surface on top of this import
(not asked for this pass, but a plausible next step), it must show the
league's real captured `scoring_settings` verbatim next to any such number
— exactly the same "never silently substitute a scoring assumption"
principle Redraft's own Sleeper-scoring-reconciliation receipt already
follows (`local_exports/redraft_v1/sleeper_imports/<id>.json`'s
`unsupported_scoring` field, confirmed to exist by the full_cycle_v1
ledger). For this pass's actual scope (ownership annotation only, no new
points computation), the concrete, sufficient action is: the new
`DynastyLeagueSnapshot`/persisted profile JSON must store the real,
verbatim `scoring_settings` and `roster_positions` from Part B (not a
paraphrase, not a "standard/PPR" label) so any future consumer has the
real source of truth available rather than needing a second Sleeper call.

---

### PART D — Backup

Backed up this worktree's entire `local_exports/` directory (the correct,
complete backup target: Part A/C establish that any new Dynasty
league-profile writes will land under `local_exports/dynasty_v1/`, and
`local_exports/` here also already holds Redraft's own live profile/import
state) before any future worker writes anything new:

- **Source:** `C:\NWR\prospective-outcomes-v1\local_exports\` (114 files,
  5.8 MB at backup time).
- **Backup:** `C:\NWR\prospective-outcomes-v1\local_exports.backup-20260918T230905Z\`
  (114 files, verified identical count via `find ... | wc -l` on both
  sides; created via `cp -a`, the same plain recursive-copy pattern the
  dogfood cycle used for its own `local_exports/redraft_v1.backup-...`
  precedent). Untracked by git (same as the existing
  `redraft_v1.backup-20260917T224444Z` sibling already in this worktree —
  `.gitignore` only ignores the literal `local_exports/` directory name,
  not `local_exports.backup-*`, so this is intentionally left as a plain
  untracked directory on disk, not committed).
- **Not backed up, deliberately, with reasoning:** the shared owner
  workspace at `C:\NWR_SHARED_DATA\nwr_personal_workspace_v1` (outside
  every worktree, shared across all of them — backing up or restoring it
  from inside one worktree's bounded task would be a real over-reach
  outside this pass's blast radius) and the governed board's own
  git-tracked `docs/hq/...` CSVs (already durable via git itself; this
  pass made zero writes to them).

---

### CODE WRITTEN THIS PASS

**None.** Per the dispatch's own explicit permission to skip code "unless
Part C's design is so trivially small that a minimal, well-tested scaffold
naturally falls out" — it is not: a real service module, a new persisted
data shape, a facade composition change, and a genuine (not padding)
draft-pick-capital reconciliation algorithm are all real implementation
work, not a trivial scaffold. This pass's own investigation (Part A)
surfaced a real design fork (frozen-but-unused ownership columns already
in the governed board vs. a new live layer; `local_exports` vs. the shared
workspace path for persistence) that is more valuable resolved in writing,
for Worker 2 to build against deliberately, than rushed into a half-tested
first draft this same pass. One standalone investigation script
(`fetch_dynasty_league.py`) was written to THIS SESSION'S SCRATCH
DIRECTORY only (not the repo) to perform Part B's real API calls — not
committed, not part of the repo's file tree.

### DYNASTY PROCESSES STATUS

Confirmed running and untouched throughout this pass (LIVE OBSERVATION,
`netstat -ano` plus direct HTTP probes at the end of this pass): frontend
`http://127.0.0.1:1421/` (PID 5288, `GET /` -> `200`), backend
`http://127.0.0.1:18741/` (PID 12852, `GET /api/v1/bootstrap` ->
`401 AUTHENTICATION_REQUIRED`, the same contract-shaped response every
prior worker in this whole saga has documented as healthy, not a crash).
These PIDs differ from the prior cycle's own recorded PIDs (`24900`/
`24240`) — consistent with the dispatch's own warning that the machine has
been restarted since; re-verified live rather than assumed. Redraft's own
frontend (1422, PID 16376) and backend (18742, PID 31352) were also
confirmed listening, untouched, not part of this pass's scope.

### FILES CHANGED

- `docs/codex/dynasty_league_import_v1/LEDGER.md` (new — this file).
- `local_exports.backup-20260918T230905Z/` (new, untracked, not part of
  the git diff — see Part D).
- No application code, test, or config file was modified.

### OPEN ISSUES FOR NEXT WORKER (Worker 2 — implements the import service)

1. **Build `dynasty_sleeper_league_service.py`** per the Part C design:
   `fetch_dynasty_league_snapshot`, `resolve_owned_pick_capital`,
   `annotate_ownership`. Reuse `SleeperHttpClient` and
   `sleeper_league_context_service.team_name_by_roster_id` as-is; do not
   reuse `sleeper_redraft_owner_service.py`'s Redraft-shaped profile
   builder or its scoring-field map.
2. **Resolve the real round-count ambiguity** found in Part B before
   writing `resolve_owned_pick_capital`: the league's two real completed
   drafts have different `settings.rounds` (24 vs. 5) — decide, and
   explicitly disclose in the profile JSON, which one (if either) is
   treated as the "default future-season pick count" for reconciling
   `traded_picks` deltas into real per-roster draft capital for 2027/2028
   and beyond.
3. **Rookie-asset ownership needs a real identity crosswalk**, not a
   direct key join — the rookie board's `player_id` (e.g. `LOV121782`) is
   not a Sleeper numeric ID, unlike current-player assets where Part A
   confirmed a direct match. Until that crosswalk exists, rookie rows on a
   Sleeper roster should surface as "ownership unresolved," never a guessed
   match.
4. **Confirm the persistence-location judgment call** in Part C section 2
   with the owner or a later worker before treating it as final: this
   worker recommends `local_exports/dynasty_v1/` (worktree-isolated,
   matches Redraft's own profile-store precedent) over reusing
   `personal_workspace_service`'s shared `C:\NWR_SHARED_DATA` path, but
   flags the durability trade-off explicitly rather than deciding it
   unilaterally for good.
5. **Facade composition point**: add the optional `league_profile_id`
   parameter to `dynasty_bootstrap`/`dynasty_workspace`/`dynasty_asset`
   as described in Part C section 3, verified byte-identical output when
   the parameter is omitted (a real regression test asserting this, not
   just an assumption, should be part of Worker 2's own test suite).
6. **Multiple Sleeper accounts on roster 7** (`co_owners:
   ["1000507609050337280"]`, display_name `"scolety"`) — real, found in
   Part B, not investigated further; irrelevant to a read-only import but
   worth the owner's awareness if any write-capable Dynasty/Sleeper
   feature is ever considered later.
7. **Re-fetch live data rather than reuse this session's scratch JSON** —
   the raw API responses captured in Part B are a point-in-time snapshot
   (2026-09-18, week 2); roster/waiver/trade activity changes weekly
   in-season, so Worker 2's actual implementation must call the real API
   again rather than hardcode anything from this ledger's captured values
   (the values here are for design/verification reference, not a frozen
   fixture to build against).
8. No frontend work has started at all (no Dynasty page reads any
   ownership field yet, since none exists) — entirely Worker 2+ scope,
   after the backend service and persistence shape exist.

---

## Worker 2 — Backend import + annotation service, persistence, facade wiring (2026-09-18)

**Branch/worktree:** same as Worker 1, `C:\NWR\prospective-outcomes-v1`.
Started at HEAD `678a81d2` (Worker 1's docs-only commit). Did not push, did
not touch `main`, did not force anything. Real, live Sleeper GET calls
made throughout (see below); zero writes to Sleeper, zero writes to the
owner's real AppData, zero writes to the governed board CSVs, zero writes
anywhere in `local_exports/` outside the new `dynasty_v1/` subtree
(byte-diff-confirmed against Worker 1's own backup, see below).

### Round-count ambiguity — real resolution (LIVE OBSERVATION)

Re-fetched (not reused from Worker 1's scratch captures, per this pass's
own instruction) `league/{id}/drafts` and, new this pass,
`draft/{draft_id}/picks` for both real completed drafts. The real
explanation, confirmed directly from live per-pick data:

- `1344772856487108608` (24 rounds, 240 picks): round-1 pick is Christian
  Watson, an established WR with `metadata.years_exp: "4"`. Across all 240
  picks, **0% have `years_exp == "0"`** — zero real rookies. 24 rounds x
  10 teams = 240 = exactly `len(roster_positions)` (this league's full
  starter+bench slot count). This is the one-time **STARTUP draft**
  (created earlier, `created: 1774981342946`).
- `1353280212753723392` (5 rounds, 50 picks, this is `league.draft_id` /
  matches `league.settings.draft_rounds`): round-1 pick is Jeremiyah Love,
  a real 2026 rookie prospect, `years_exp: "0"`. **62% of all 50 picks
  have `years_exp == "0"`** — real rookies. This is the recurring annual
  **ROOKIE draft** (created later, `created: 1777009654754`).

`_classify_draft` (in the new service) turns this real per-pick evidence
into an honest `"startup" | "rookie" | "unknown"` label per draft (never a
round-count-only guess): `rookie_fraction >= 0.5` → `"rookie"`;
`rounds == len(roster_positions)` (with low rookie fraction) → `"startup"`;
otherwise `"unknown"`. `resolve_round_count_baseline` then uses the
uniquely-classified `"rookie"` draft's round count (5) as the baseline for
projecting NOT-yet-drafted future seasons (2027+), explicitly excluding the
one-time startup draft, and would fall back to the league's own
currently-configured `settings.draft_rounds` — disclosed, not silent — if
classification were ever ambiguous (zero or 2+ real "rookie" drafts
found). For this league today the classified value (5) and the
currently-configured value (5) agree; the disagreement-disclosure path is
covered by a dedicated unit test using synthetic data since this league
doesn't currently exercise it.

### Pick-capital result — real, live-computed (LIVE OBSERVATION)

`resolve_owned_pick_capital` against the real, freshly-fetched league
state, for roster 7 (Niners, owner `1352768154031374336`):

- **2026** (actual completed rookie draft, 5 rounds): **5 owned picks** —
  kept own R2 and R5 (R1/R3/R4 traded away, matching Worker 1's finding
  exactly), acquired roster 1's R2 and roster 2's R1 and R2 (three
  distinct round-2 picks land on roster 7 this season — a real, correctly
  representable multi-pick-per-round shape, not a bug).
- **2027** (no draft yet → baseline projection, 5 rounds): **5 owned
  picks** — no 2027 `traded_picks` record touches roster 7 at all in
  either direction, so it owns exactly its own 5 rounds.
- **2028** (no draft yet → baseline projection, 5 rounds): **6 owned
  picks** — own 5 rounds plus roster 2's real traded-away 2028 R1.

All matches Worker 1's own qualitative description of the real trade
activity; this pass adds the exact, reconciled per-round accounting Worker
1 flagged as still needing a real algorithm.

### Service built

New `src/services/dynasty_sleeper_league_service.py` (see its module
docstring for the full design rationale):

- `fetch_dynasty_league_snapshot(league_id, *, client=None, fetch_draft_picks=True) -> DynastyLeagueSnapshot`
  — real GET-only fetch of `league/{id}`, `.../rosters`, `.../users`,
  `.../traded_picks`, `.../drafts`, and (new vs. Worker 1's design)
  `draft/{id}/picks` per draft for real-evidence classification. Reuses
  `SleeperHttpClient` and `team_name_by_roster_id` unmodified. Stores
  `scoring_settings`/`roster_positions` verbatim.
- `resolve_round_count_baseline(drafts, *, configured_draft_rounds) -> RoundCountBaseline`
  and the private `_classify_draft` — the real-evidence resolution above.
- `resolve_owned_pick_capital(league_snapshot, *, seasons=None) -> dict[int, tuple[PickOwnership, ...]]`
  — reconciles `traded_picks` deltas against a real-or-projected
  per-season round count; never drops a malformed record silently (skips
  with no crash); discloses `round_source` (`"actual_draft"` vs.
  `"baseline_projection"`) per row.
- `annotate_ownership(asset_rows, league_snapshot, *, my_owner_id=None) -> dict[str, dict]`
  — pure join, keyed only by the governed board's own `asset_id` string
  convention (`current:{sleeper_id}` direct join; `rookie:`/
  `blocked-rookie:` always `UNRESOLVED` with a real, human-readable reason;
  everything else, e.g. `pick:`/`future-pick:`, absent from the result,
  never guessed). Deliberately does NOT depend on any resolved `player_id`
  field from `owner_asset_evidence_service` — it parses the Sleeper ID
  straight out of the `current:` asset-id prefix, which is more robust
  since `dynasty_bootstrap`'s `rankings`/`rookies`/`assetOptions` payloads
  are built from three different underlying frames that are not guaranteed
  to carry an identically-resolved `player_id` column.
- Persistence: `dynasty_league_store_root`, `save_league_profile`/
  `load_league_profile`, `save_league_snapshot`/`load_latest_league_snapshot`,
  and the orchestration `import_dynasty_league(league_id, root, *, client=None, my_owner_id=None, profile_id=None, seasons=None) -> DynastyLeagueImportResult`.

Worker 1's persistence-location recommendation (worktree-isolated
`local_exports/dynasty_v1/`, not the shared `C:\NWR_SHARED_DATA` workspace)
was confirmed sound during implementation and used as designed — no
problem found with it. One concrete decision made during implementation
that Worker 1 left open: **`profile_id` defaults to the Sleeper
`league_id` itself** (not a generated UUID) — simplest possible lookup
key for "one profile per real league," matching how
`import_dynasty_sleeper_league`/`load_dynasty_league_profile` are used
from the facade; a future worker can add multi-profile-per-league support
later if the owner ever wants two saved configurations of the same
league, but nothing here blocks that (the `profile_id` override parameter
already exists end-to-end).

### Persistence — exact paths, confirmed live

- `local_exports/dynasty_v1/league_profiles/<profile_id>.json` — stable
  league config (name/season/num_teams/scoring_settings verbatim/
  roster_positions verbatim/taxi/reserve/etc., `my_owner_id`/`my_roster_id`,
  `created_at_utc`/`updated_at_utc`).
- `local_exports/dynasty_v1/league_snapshots/<profile_id>/<UTC timestamp>.json`
  — one file per import/resync (`utc_snapshot_stamp()`, same filename
  convention Redraft's own Sleeper snapshot tooling uses), holding the full
  fetched roster/draft/traded-pick state plus the computed pick-capital
  table. `load_latest_league_snapshot` picks the lexicographically-last
  (== chronologically-last) file.
- Both written via the same atomic-write convention Redraft's
  `redraft_engine_v1_service._atomic_json` established (temp file +
  `os.replace`, `indent=2, sort_keys=True`) — the CONVENTION was reused,
  not Redraft's code (a fresh, small `_atomic_json` lives in the new
  module, per the dispatch's explicit instruction).
- **Real, live import performed this pass** against league
  `1344772855908290560`: `local_exports/dynasty_v1/league_profiles/1344772855908290560.json`
  and one real snapshot file now exist in this worktree
  (`local_exports/` is `.gitignore`d, same as Redraft's own profile store,
  so these are untracked, exactly as intended). Round-trip verified
  byte-for-byte equal (`dataclasses.asdict` comparison, see live
  verification below).

### Facade wiring

`src/application/desktop_facade.py`:

- Constructor gained `dynasty_league_root: str | Path | None = None`
  (defaults to `dynasty_league_store_root(self.repo_root)`, i.e.
  `<repo_root>/local_exports/dynasty_v1`, overridable via
  `NWR_DYNASTY_LEAGUE_HOME` exactly like Redraft's own `NWR_REDRAFT_HOME`
  pattern).
- New: `import_dynasty_sleeper_league(league_id, *, my_owner_id=None, profile_id=None, seasons=None, client=None) -> FacadePayload`
  — dynasty-mode-only, calls `dynasty_sleeper_league_service.import_dynasty_league`
  end to end (fetch → resolve pick capital → persist), returns a summary
  payload (league name/season/team count/round-count-baseline disclosure/
  my real pick-capital-by-season counts/snapshot path).
- New: `load_dynasty_league_profile(profile_id) -> FacadePayload` — reads
  the persisted profile + latest snapshot back out (used by the three
  annotated methods below, and directly callable on its own).
- `dynasty_bootstrap`, `dynasty_workspace`, `dynasty_asset` each gained an
  **optional, keyword-only** `league_profile_id: str | None = None`.
  Structural guarantee, not just a tested behavior: every pre-existing line
  of each method's body is UNCHANGED (verify via `git diff`); the new
  parameter is checked only in one `if league_profile_id is None: return
  payload` guard added at the very end, right before the original
  `return`. When `None` (the default), the exact same `FacadePayload`
  object that existed before this pass is returned — no new code path
  executes at all. When set, `_annotate_dynasty_bootstrap_payload`/
  `_annotate_dynasty_workspace_payload`/`_annotate_dynasty_asset_payload`
  load the persisted league state, call `annotate_ownership` (from the new
  service, unchanged), and merge an additive `"ownership"` key onto each
  row that has a resolvable asset id (`rankings`/`rookies`/`assetOptions`
  for bootstrap, `personalBoard` for workspace, the asset payload itself
  for `dynasty_asset`) plus a top-level `"dynastyLeague"` context block —
  every pre-existing field on every row is passed through via `dict(row)`,
  never rebuilt.
- **Regression test proving byte-identical output when omitted**
  (`tests/test_dynasty_league_import_facade_wiring.py`): `json.dumps(...,
  sort_keys=True)` equality between the no-argument call and the explicit
  `league_profile_id=None` call, for all three methods, run against this
  repo's REAL governed board (`repo_root=REPO_ROOT`, matching the existing
  `test_desktop_facade_architecture_wiring.py` convention) — **passes**.
  Also added a call-ordering test
  (`test_repeated_bootstrap_calls_without_annotation_stay_stable`) proving
  an annotated call sandwiched between two unannotated calls does not leak
  any mutation into the shared cached `_OwnerSnapshot` — **passes**
  (confirms the annotation path only ever builds new dicts, never mutates
  `snapshot.evidence.rows`/dataframes in place).

### Live verification (LIVE OBSERVATION, real Sleeper API, this pass)

Real GET calls made directly against `1344772855908290560` (not the fake
client used by the pytest suite): `league/{id}`, `.../rosters`,
`.../users`, `.../traded_picks`, `.../drafts`, and `draft/{id}/picks` for
both real drafts (240 + 50 real pick records fetched). Confirmed, matching
Worker 1's own live findings exactly: league name "Las Vegas Enginerds",
`rec: 0.0`, `roster_positions` length 24 / no DST slot, `taxi_slots: 0`,
`reserve_slots: 2`, roster 7 `owner_id "1352768154031374336"` / team name
"Niners" / `reserve: ["11638", "12484"]`. New this pass: real per-pick
`years_exp` evidence for both drafts (see round-count section above), and
the real reconciled 2026/2027/2028 pick-capital table for roster 7.
`annotate_ownership` exercised against the real fetched roster: Puka Nacua
(`current:9493`) currently shows real roster 9 ("Rocky Mountain High"),
**not** roster 7/"Niners" — real, live season drift versus both the
10-week-stale frozen board snapshot Worker 1 found AND versus whatever
roster he sat on at Worker 1's own capture time; disclosed as a real,
expected data-freshness fact, not a bug. 199 of the 240 governed
current-player board rows resolved to a real roster somewhere in this
10-team league; 41 are real free agents relative to this specific league
(expected — the governed board is a league-agnostic 240-player universe).

**Zero-writes verification, two methods:**
1. Code inspection (same as Worker 1): `SleeperHttpClient.get_json` is
   GET-only by construction, unmodified, confirmed by re-reading the class
   this pass.
2. Real before/after byte-diff of `local_exports/` (the concrete
   requirement this pass's dispatch asked for, beyond Worker 1's own
   read-only investigation): `diff -rq --exclude=dynasty_v1 local_exports
   local_exports.backup-20260918T230905Z` returned **zero differences** —
   nothing outside the new, intentional `dynasty_v1/` subtree changed
   anywhere in `local_exports/` during this entire pass, including the
   real live import.

### Tests added

`tests/test_dynasty_sleeper_league_service.py` (16 tests, all pass, no
network access — every test builds synthetic Sleeper-shaped data or a
fake GET-only client):
- `annotate_ownership`: current-player match on my roster, current-player
  match on an opponent roster (with real slot-status resolution:
  starter/bench/reserve), current-player matching nobody (free agent),
  rookie asset always `UNRESOLVED` with a non-empty reason (both `rookie:`
  and `blocked-rookie:` prefixes), pick/future-pick assets never annotated,
  camelCase `assetId` key accepted, and an explicit proof it never returns
  any score/rank/value-shaped key.
- `resolve_round_count_baseline`: real startup-vs-rookie classification
  pattern, an agreement case, a disagreement-with-configured-rounds
  disclosure case, and an ambiguous-fallback disclosure case.
- `fetch_dynasty_league_snapshot` end-to-end classification (fake client
  returning 240 veteran-shaped picks + 50 rookie-shaped picks, reproducing
  this league's exact real shape) — proves the classification pipeline
  reaches the correct conclusion from raw pick data, not just when
  classification is hand-supplied to `resolve_round_count_baseline`
  directly.
- `resolve_owned_pick_capital`: the real 3-roster trade shape (including
  the real multi-pick-per-round edge case this league's own live data
  actually has), and a malformed-record-is-skipped-not-fatal case.
- Persistence round-trip (profile + snapshot + pick capital), a
  missing-profile error case, and a full `import_dynasty_league`
  orchestration test against a fake client.

`tests/test_dynasty_league_import_facade_wiring.py` (10 tests, all pass,
run against this repo's REAL governed board via `repo_root=REPO_ROOT`):
byte-identical-when-omitted for all three annotated methods (the
correctness-critical guarantee this whole feature depends on), a
call-ordering/no-mutation-leak test, real import + persistence via the
facade, annotated bootstrap actually adding ownership (spot-checked that
every OTHER field on the annotated row equals the unannotated row's same
field, proving pure addition), annotated single-asset `dynasty_asset`,
rejecting an unknown `league_profile_id` (`FacadeError` /
`DYNASTY_LEAGUE_PROFILE_NOT_FOUND`), mode-gating
(`import_dynasty_sleeper_league` unavailable outside dynasty mode, same
`MODE_ROUTE_UNAVAILABLE` convention every other mode-gated method uses),
and `load_dynasty_league_profile` round-tripping persisted state.

**Full-suite regression check:** ran the pre-existing
`test_desktop_facade_architecture_wiring.py` (all pass),
`test_status_override_intake_facade.py` (all pass), and
`test_desktop_application_api.py` (4 pre-existing failures, confirmed via
`git stash` to be identical on the untouched Worker-1 HEAD — unrelated to
this pass: 2 are date-freshness/model-drift failures, 1 is a real
pre-existing `ast`-based import-hygiene check unrelated to Dynasty, 1 is a
`redraft_bootstrap` data-freshness gap already documented in this branch's
own known baseline). A `-k dynasty` sweep of the whole `tests/` tree found
3 further pre-existing, unrelated failures (all date/freshness-window
drift in `model_v4_rotowire_dynasty_candidate_service`/
`rookie_veteran_dynasty_bridge_service`, confirmed via `git stash`
identical on untouched HEAD) — consistent with this worktree's own
documented ~323-pre-existing-failure baseline (see
`nwr-full-suite-preexisting-failures` in project memory); zero new
failures introduced by this pass.

### Dynasty processes status

Confirmed running and untouched throughout (LIVE OBSERVATION): frontend
`http://127.0.0.1:1421/` (PID 5288, `GET /` → `200`) and backend
`http://127.0.0.1:18741/` (PID 12852, `GET /api/v1/bootstrap` → `401`,
same healthy contract-shaped response prior workers documented) — same
PIDs Worker 1 recorded, confirmed still alive, not restarted. Note for
Worker 3: these long-running dev processes loaded `desktop_facade.py`
before this pass's edits landed, so this pass's new backend code is **not
yet live** in that running process — a restart (or the dev server's own
hot-reload, if configured) will be needed before Worker 3 can exercise the
new facade methods through the actual running HTTP API rather than via
direct Python import, as this pass did.

### Files changed

- `src/services/dynasty_sleeper_league_service.py` (new).
- `src/application/desktop_facade.py` (modified — see Facade wiring above;
  every pre-existing line before each method's final `return` is
  unchanged, confirmed via the byte-identical regression tests).
- `tests/test_dynasty_sleeper_league_service.py` (new).
- `tests/test_dynasty_league_import_facade_wiring.py` (new).
- `docs/codex/dynasty_league_import_v1/LEDGER.md` (this section).
- `local_exports/dynasty_v1/` (new, untracked/`.gitignore`d, real live
  import data — see Persistence above).

### Open issues for Worker 3 (frontend wiring)

1. **No frontend surface reads any of this yet** — `league_profile_id` is
   never passed from any UI today; Dynasty Home/ownership display/Compare/
   Trade Decision Lab wiring is entirely this next worker's scope, exactly
   as the dispatch specified.
2. **Dev processes need a restart** (see Dynasty processes status above)
   before the new facade methods are reachable through the live HTTP API
   at `127.0.0.1:18741` — confirm the current hot-reload behavior before
   assuming a restart is required.
3. **Rookie ownership is `UNRESOLVED` by design, not a bug to silently
   paper over** — Worker 3's UI should render this as an honest "ownership
   unknown for this rookie asset" state (per the original dispatch), not
   omit the field or guess a value. No rookie identity crosswalk exists
   yet; building one is out of scope for both this pass and (per the
   dispatch) Worker 3's frontend pass.
4. **`import_dynasty_sleeper_league` is not yet exposed over the HTTP API
   layer** (only as a Python facade method) — Worker 3 will need to find
   or add the corresponding HTTP route in whatever wraps
   `DesktopBackendFacade` for the Dynasty desktop app (out of scope for
   this backend-only pass; not investigated this pass beyond confirming
   the facade method itself works end-to-end via direct Python calls).
5. **Multi-Sleeper-account co-owner on roster 7** (`scolety`, found by
   Worker 1) remains unresolved/unused — irrelevant to this read-only
   import, still worth the owner's awareness for any future write-capable
   feature.
6. **The real 2026 pick-capital table (5 owned picks for roster 7) reflects
   an ALREADY-COMPLETED draft** — i.e. this is historical fact (who
   exercised which pick), not upcoming capital to plan around; Worker 3
   should present 2026 differently from 2027/2028 (real future capital) in
   any UI that surfaces this, rather than implying all three seasons are
   equally "upcoming."
7. **`local_exports/dynasty_v1/` now contains one real, live-imported
   league profile+snapshot** (league `1344772855908290560`) from this
   pass's live verification — safe to keep/reuse for Worker 3's frontend
   testing, or re-import fresh at any time (`import_dynasty_league` is
   idempotent-safe: it always fetches live and writes a new timestamped
   snapshot file; the profile file is updated in place, preserving
   `created_at_utc`).

---

## Worker 3 — HTTP routes, Connect League UI, Home/Asset Explorer/Player Detail ownership wiring, live verification (2026-09-18)

**Branch/worktree:** same as Workers 1-2, `C:\NWR\prospective-outcomes-v1`.
Started at HEAD `b2c11c80` (Worker 2's backend commit). Did not push, did
not touch `main`, did not force anything. Did not touch
`governed_asset_registry_service.py`, any board CSV, `marginal_roster_
utility_v2`, or Redraft's processes (1422/18742) at all.

### 1. HTTP routes (INSPECTED CODE + ACTUAL TEST RESULT)

Read `src/desktop_api/server.py` in full first -- confirmed the exact
existing conventions (`_json_body`/`_reject_unknown_fields`/
`_invalid_body`, path regexes, "mutate then return the current bootstrap"
pattern used by every other Dynasty/Redraft mutation route) before adding
anything, per the dispatch's own instruction not to invent a new pattern.

New routes, all in `src/desktop_api/server.py`:
- `POST /api/v1/dynasty/league/import` -- body `{leagueId, myOwnerId?,
  profileId?}`. Calls `facade.import_dynasty_sleeper_league(...)` (Worker
  2's frozen, tested method -- unchanged), then
  `facade.set_active_dynasty_league_profile(profileId)` (new, see below),
  then returns `facade.dynasty_bootstrap(league_profile_id=profileId)` --
  the freshly annotated bootstrap in one round trip, matching the
  established "mutate, then return current bootstrap" convention exactly
  (e.g. `_SLEEPER_REDRAFT_IMPORT`).
- `POST /api/v1/dynasty/league/disconnect` -- no body. Clears the active
  marker, returns the plain (unannotated) `dynasty_bootstrap()`.
- `GET /api/v1/dynasty/league/{profileId}` -- thin pass-through to
  `facade.load_dynasty_league_profile(profileId)` (Worker 2's method,
  unchanged).

**Real design decision, not in Worker 2's scope:** `_validated_path`
rejects ANY query string on every route (`QUERY_NOT_SUPPORTED`), so there
was no way to pass `league_profile_id` on a GET request. Rather than
relax that contract, I added a persisted "active league" concept -- the
same shape Redraft already uses for its own active-profile selection
(`redraft_engine_v1_service.set_active_profile`/`active_profile_id`,
`active_profile.json`). New functions in `dynasty_sleeper_league_service.py`:
`set_active_league_profile(root, profile_id)` (validates the profile
actually exists via `load_league_profile` before persisting; `None`
disconnects) and `active_league_profile_id(root)` (reads the marker,
`None` if absent/corrupt) -- both use the module's existing `_atomic_json`
helper, persisted at
`local_exports/dynasty_v1/active_league_profile.json`.

New facade methods (`desktop_facade.py`): `dynasty_active_league_profile_id()`
and `set_active_dynasty_league_profile(profile_id)`, both dynasty-mode-
gated. Critically, **Worker 2's `dynasty_bootstrap`/`dynasty_workspace`/
`dynasty_asset` method bodies are UNCHANGED** -- the active-profile lookup
happens only at the call site: `bootstrap()`'s dynasty branch now reads
`self.dynasty_active_league_profile_id()` and passes it in, and the two
HTTP routes for `/api/v1/dynasty/workspace` and `/api/v1/dynasty/assets/
{id}` do the same. This preserves Worker 2's own byte-identical-when-
omitted tests exactly as written (they call `dynasty_bootstrap()` with no
active-profile marker on disk, so they still get `None` -> unannotated).
Added a new regression test proving the composed behavior:
`test_bootstrap_is_unannotated_by_default_and_annotated_once_a_league_is_
set_active` plus a real cross-process-restart-simulation test
(`test_set_active_dynasty_league_profile_disconnect_and_restart_
persistence` -- constructs a SECOND, independent `DesktopBackendFacade`
instance pointed at the same `dynasty_league_root` to prove there is zero
shared in-memory state involved, only the on-disk marker).

Full test file `tests/test_desktop_http_api.py`'s `FakeFacade` was updated
to accept the new `league_profile_id` kwargs on `dynasty_workspace`/
`dynasty_asset` (previously it had none) and gained the new methods --
this was REQUIRED, not optional: the pre-existing
`test_dynasty_routes_decode_ids_and_accept_canonical_receive_key` and
`test_dynasty_workspace_routes_are_bounded_and_authenticated` tests would
otherwise 500 on the new kwarg. Added 3 new route-level tests (import +
persists-active, profile-get + disconnect, workspace/assets pass the
active id through only when connected).

### 2. Connect League UI (LIVE OBSERVATION)

Lives on Data Health (`desktop/apps/dynasty/src/pages/system.tsx`,
`DynastyLeagueConnectionPanel`) -- per the dispatch's own hint, this is
the page whose Planning Console copy already discloses "without automated
roster hydration," so it's the natural, existing place to add a real
connect action rather than inventing a new nav destination. Minimal real
form: Sleeper league ID + optional owner ID -> `POST /api/v1/dynasty/
league/import` -> on success, `onReload()` (the same `reload` callback
`DynastyApp.tsx` already threads through every page, which re-runs the
top-level bootstrap fetch). Connected state shows league name, team name
(derived from any owned ranking row's real `ownership.rosterTeamName`,
never hardcoded), roster number, import timestamp, and a real
**Disconnect** button (`POST /api/v1/dynasty/league/disconnect`) -- not
explicitly asked for by the dispatch, added because "selectable" implies
being able to select "no league" again, and it made the byte-identical
fallback path independently live-testable without restarting the backend.

**Persistence mechanism:** entirely server-side (the `active_league_
profile.json` marker above) -- no browser localStorage/sessionStorage
involved at all. This means the "connected" selection survives not just a
page reload but a FULL BACKEND RESTART, which is the strictly stronger
guarantee the dispatch actually asked for ("survive a restart").

### 3. Home wiring (LIVE OBSERVATION)

`desktop/apps/dynasty/src/pages/home.tsx`: `data.dynastyLeague` (present
only once connected, per the byte-identical contract) gates a new "Your
roster -- {team}" panel showing the real rows where
`row.ownership?.isMyTeam` is true (rank, player, position, real roster
slot status, NWR score), plus a status-row "Connected: {league name}"
badge and (when NOT connected) a "No Dynasty league connected" strip with
a real "Connect league" button that navigates to Data Health. **Verified
LIVE, not just from the backend's own tests**: with no league connected,
Home rendered pixel-for-pixel identical to its pre-existing appearance
(screenshot-compared before and after this whole pass, and again after a
real Disconnect); with `1344772855908290560` connected, Home showed a
real "LAS VEGAS ENGINERDS" status badge and a real "Your roster -- Niners"
table with real players (De'Von Achane, Zay Flowers, Drake Maye, Chase
Brown, Jameson Williams, ...) and real slot statuses (starter/bench).

### 4. Asset Explorer / Player Detail ownership (LIVE OBSERVATION)

New pure helper `desktop/apps/dynasty/src/lib/ownership.ts`,
`resolveOwnershipDisplay(ownership)` -- follows this codebase's own
`resolveFaabDisplay`-style precedent explicitly named in the dispatch
(`desktop/apps/redraft/src/improve-team-explain.ts`): returns `null` for
no-ownership-data (no league connected, or an asset type with no
ownership concept, e.g. picks), and a `{label, tone, detail}` badge for
`OWNED` (split into "On your roster" vs. "Owned by {team}"), `FREE_AGENT`,
and `UNRESOLVED` (rookies -- always shown, never omitted or guessed).
7 unit tests in `ownership.test.ts`, all passing, covering every branch
including the empty-team-name and empty-reason-string fallbacks.

Wired into: `AssetExplorerPage` and `RankingsPage`
(`pages/rankings.tsx`, an additive "Ownership" column, only added when
`data.dynastyLeague` is set), `RookieReviewPage`
(`pages/research.tsx`, same additive column -- proves rookies show
`UNRESOLVED` in a real list view, not just in one-off detail), and
`PlayerDetailBody`'s identity header (a real ownership badge next to the
player's name/team/authority line, sourced from the per-asset `GET /api/
v1/dynasty/assets/{id}` response).

**Real, live spot-checks (via Chrome MCP, `get_page_text` over the full
Asset Explorer table after connecting the real league -- 379 real rows
inspected, not a sample):**
- **My-roster player:** De'Von Achane (#9) -> "ON YOUR ROSTER". Confirmed
  again on its own Player Detail page (`/#/players/current%3A9226`) --
  real badge in the identity header.
- **Opponent-roster player:** Puka Nacua (#1) -> "OWNED BY ROCKY MOUNTAIN
  HIGH" -- this independently reproduces Worker 2's own live finding (Puka
  Nacua sits on roster 9, not roster 7, as of this same season) from a
  completely different code path (UI rendering vs. Worker 2's direct
  Python `annotate_ownership` call).
- **Free agent:** Darius Slayton (#89), Joe Mixon (#97), Calvin Austin
  (#100), and 30+ others -> "FREE AGENT".
- **Rookie (unresolved):** every one of the 73 real Rookie Review rows
  (Jeremiyah Love, Jordyn Tyson, ...) and all 7 Manual Review rookies
  (De'Zhaun Stribling, Carson Beck, ...) -> "OWNERSHIP UNRESOLVED" -- the
  honest disclosed state, never silently omitted or guessed, exactly as
  designed.
- **Pick/future-pick assets:** no ownership badge rendered at all (the
  Ownership column shows `—`) -- `annotate_ownership` correctly leaves
  these unannotated (draft-pick capital is a separate structure Worker 4
  was never asked to surface here), and the UI never fabricates a status
  for them.

### 5. Live verification -- full sequence (LIVE OBSERVATION)

Killed the stale dev processes from Worker 2's session (frontend PID
5288, backend PID 12852 -- confirmed dead via `netstat`), rebuilt the
frontend for real (`npm run build:dynasty` -- **required**, this app's
dev process runs `vite preview`, which serves the last build, not source;
confirmed this the same way the dogfood-cycle lesson referenced in the
dispatch describes), and relaunched both: backend via
`scripts/run_nwr_desktop_api.py --port 18741 --mode dynasty` (dev
bearer-token credentials piped over stdin, matching `browserRuntime`'s
own hardcoded dev-mode fallback token in `api-client/src/index.ts`, so no
Tauri shell was needed to exercise this through a real browser), frontend
via `vite preview --port 1421 --strictPort` from
`desktop/apps/dynasty`.

Full Chrome MCP sequence, all real, all confirmed via screenshot or
`get_page_text` (never asserted from code alone):
1. Home, no league connected -- confirmed the "No Dynasty league
   connected" strip + Connect League CTA, real `239` market-matched
   count (matches this session's own live pytest baseline exactly).
2. Clicked through to Data Health, typed the real league ID
   (`1344772855908290560`) and real owner ID (`1352768154031374336`) --
   **note:** the MCP `form_input` tool coerces its `value` through a
   JS number internally and silently lost precision on these 19-digit
   IDs (`...290560` became `...290600`); switched to `computer` click+type
   instead, which preserves the exact string. Worth remembering for any
   future 19-digit-Sleeper-ID UI test.
3. Clicked "Connect league" -- real success message, "Connected: Las
   Vegas Enginerds · Your team: Niners · Roster #7 · Imported 9/18/2026,
   5:55:18 PM".
4. Home -- real "CONNECTED: LAS VEGAS ENGINERDS" status badge, real "Your
   roster -- Niners" panel with real players.
5. Asset Explorer -- full-table real spot-checks (section 4 above).
6. Player Detail -- real "ON YOUR ROSTER" badge on De'Von Achane.
7. Hard browser reload (`navigate` to `/`) -- connection persisted.
8. **Killed the backend process entirely** (`Stop-Process`, confirmed
   port `18741` free via `netstat`) and started a **brand-new, unrelated
   backend process** (new PID, zero shared memory) -- reloaded the
   browser -- **connection still showed "CONNECTED: LAS VEGAS
   ENGINERDS"**, proving persistence is real (on-disk), not an artifact
   of one long-lived process.
9. Clicked "Disconnect league" -- Home reverted to the exact original
   "No Dynasty league connected" appearance (screenshot-compared).
10. Reconnected the real league again (same flow) to leave a real,
    working, connected state on disk for Worker 4 to build against
    immediately, rather than an artificially-disconnected one.

No console errors at any point (`read_console_messages`, `onlyErrors:
true`, checked mid-sequence).

### Tests added

- `tests/test_dynasty_sleeper_league_service.py`: 4 new tests for
  `active_league_profile_id`/`set_active_league_profile` (default-none,
  persists-and-survives-a-fresh-read, disconnect, rejects-unimported).
- `tests/test_dynasty_league_import_facade_wiring.py`: 3 new tests --
  `bootstrap()`'s composed default-vs-connected behavior, a real
  independent-second-facade-instance restart simulation, and the
  unknown-profile rejection path.
- `tests/test_desktop_http_api.py`: 3 new route-level tests (import +
  persists active + returns annotated bootstrap; profile-get +
  disconnect; workspace/assets pass the active id through only once
  connected) plus required `FakeFacade` updates for the new
  `league_profile_id` kwargs/methods.
- `desktop/apps/dynasty/src/lib/ownership.test.ts`: 7 new tests for
  `resolveOwnershipDisplay` (null-when-disconnected, my-team, opponent
  team with a real name and with an empty-name fallback, free agent,
  unresolved with a real reason and with an empty-reason fallback).

**Full-suite regression check, this pass:** `pytest tests/
test_desktop_http_api.py tests/test_dynasty_league_import_facade_wiring.py
tests/test_dynasty_sleeper_league_service.py
tests/test_desktop_facade_architecture_wiring.py` -- 83 passed. `npm run
typecheck` (both dynasty and redraft `tsconfig.json` projects) -- clean,
zero errors. `npx vitest run` (whole `desktop/` workspace, both apps) --
486 passed, 30 files. One incidental finding: running the full `vitest`
suite regenerates `docs/codex/prospective_outcomes_v1/multi_league_scale_
v1/frontend_bench_results.json` with new real-but-noisy timing numbers
(a benchmark test writes its own results file) -- reverted that file via
`git checkout --` before committing since it's timing noise unrelated to
this pass, not a real regression.

### Dynasty processes status (final)

Backend: `http://127.0.0.1:18741/` -- PID `41112` (the SECOND restart in
this pass, per the persistence test above; the very first restart, PID
`13552`, was intentionally killed as part of that same test). Frontend:
`http://127.0.0.1:1421/` -- PID `37176`, serving the real rebuilt
`dist/` (`vite preview`). Both confirmed healthy via live browser use
through this entire pass. Redraft's own processes (1422/18742) were never
touched.

### Files changed

- `src/desktop_api/server.py` (3 new routes).
- `src/application/desktop_facade.py` (`bootstrap()` composed with the
  active-profile lookup; 2 new methods; Worker 2's 3 annotated methods'
  bodies unchanged).
- `src/services/dynasty_sleeper_league_service.py` (2 new persistence
  functions, same `_atomic_json` convention).
- `desktop/packages/contracts/src/index.ts` (new `AssetOwnership`/
  `DynastyLeagueContext`/`DynastyLeagueImportInput`/
  `DynastyLeagueProfileSummary`/`DynastyLeagueRosterSummary` types;
  additive optional `ownership?`/`dynastyLeague?` fields on the existing
  ranking/asset/rookie/workspace/bootstrap/player-detail types).
- `desktop/packages/api-client/src/index.ts` (3 new client methods).
- `desktop/apps/dynasty/src/lib/ownership.ts` (new, pure).
- `desktop/apps/dynasty/src/lib/ownership.test.ts` (new).
- `desktop/apps/dynasty/src/DynastyApp.tsx` (passes `client` into
  `DataHealthPage`).
- `desktop/apps/dynasty/src/pages/system.tsx` (new
  `DynastyLeagueConnectionPanel`, `DataHealthPage` signature change).
- `desktop/apps/dynasty/src/pages/home.tsx` (Your Roster panel, connect
  CTA).
- `desktop/apps/dynasty/src/pages/rankings.tsx` (Ownership column on
  Asset Explorer + Dynasty Rankings).
- `desktop/apps/dynasty/src/pages/research.tsx` (Ownership column on
  Rookie Review, ownership badge on Player Detail).
- `tests/test_dynasty_sleeper_league_service.py`,
  `tests/test_dynasty_league_import_facade_wiring.py`,
  `tests/test_desktop_http_api.py` (new/updated tests, see above).
- `docs/codex/dynasty_league_import_v1/LEDGER.md` (this section).

Not committed (pre-existing untracked leftovers from Worker 2's own
session, not touched or relied upon by this pass): `dynasty_smoke_
stderr.log`, `dynasty_smoke_stdout.log`,
`local_exports.backup-20260918T230905Z/`.

### Open issues for Worker 4 (Compare + Trade Decision Lab + full closure)

1. **Compare and Trade Decision Lab remain entirely unwired**, exactly as
   scoped -- `compare_dynasty_assets`/`evaluate_dynasty_trade` never
   receive a `league_profile_id` and their pages never read `ownership`.
   This is real, deliberate, in-scope-for-Worker-4 work, not an oversight.
2. **A real league IS currently connected** on disk
   (`local_exports/dynasty_v1/`, profile id
   `1344772855908290560`) -- Worker 4 can build/test against it
   immediately; re-running the Connect League flow is idempotent-safe if
   a fresher snapshot is ever wanted (re-fetches live, writes a new
   timestamped snapshot, profile file updated in place).
3. **Rookie ownership is still `UNRESOLVED` by design** -- no crosswalk
   was built this pass either; still an honest, disclosed gap, not
   something Compare/Trade Lab should silently paper over if Worker 4
   surfaces rookie ownership there too.
4. **The Connect League form has no client-side re-validation beyond
   "non-empty league ID"** -- a garbage/nonexistent league ID surfaces the
   real backend `DYNASTY_LEAGUE_FETCH_FAILED`/network error message
   as-is (via `ErrorState`), not a friendlier pre-check; acceptable for
   this pass's scope but worth polishing later if the owner hits it.
5. **No UI exists yet for picking a SECOND or different league profile**
   once one is connected (only connect-a-new-one, which overwrites which
   profile is "active" via a fresh import, or disconnect) -- the backend
   supports arbitrary `profileId`s and `GET /api/v1/dynasty/league/
   {profileId}` already, so a "switch between previously-imported
   leagues" picker is straightforward to add later but was not asked for
   this pass and wasn't built.
6. **Dev-mode bearer token used for this pass's live verification**
   (`nwr-desktop-development-token-only-000000000000`, the same hardcoded
   fallback `browserRuntime()` already uses when not running inside
   Tauri) -- this is the established, pre-existing convention for
   testing this app through a plain browser rather than the native shell;
   not a new credential or weakening of anything.

---

## Worker 4 — Compare + Trade Decision Lab wiring, isolation testing, closure (2026-09-18)

**Branch/worktree:** same as Workers 1-3, `C:\NWR\prospective-outcomes-v1`.
Started at HEAD `684c2b98` (Worker 3's commit). This is the CLOSURE worker
for this cycle. Did not touch `main`, did not force anything, did not
touch `governed_asset_registry_service.py`/any board CSV/
`CURRENT_BOARD_SHA256`/`evaluate_trade_decision`/`compare_dynasty_assets`'s
own scoring internals, did not touch Redraft's `marginal_roster_utility_v2`
or Redraft's running processes. Read-only Sleeper access only throughout
(confirmed by re-inspecting `SleeperHttpClient` -- unchanged, GET-only by
construction -- and by never calling any write-shaped Sleeper endpoint;
also confirmed via a direct, independent live `GET
https://api.sleeper.app/v1/league/.../rosters` call used only for the
roster-accuracy spot-check below).

### 1. Compare wiring (INSPECTED CODE + ACTUAL TEST RESULT + LIVE OBSERVATION)

`src/application/desktop_facade.py`'s `compare_dynasty_assets` gained an
optional `league_profile_id: str | None = None` keyword parameter. The
existing body -- which builds `leans`/`ranges`/`players`/`bridge`/
`warnings` from `rows` via `build_owner_compare_summary`/
`build_rookie_veteran_bridge`/`build_player_compare_decision_summary`/
`decision_summary_rows` -- is completely unchanged; the new parameter is
only read in one `if league_profile_id:` block added at the very end,
after `data` (renamed from the old inline dict literal) is already fully
built. When set, it loads the persisted league state and calls
`annotate_ownership` (Worker 2's frozen, unchanged function) over the
compared asset ids, attaching two new top-level keys: `ownership` (a flat
list of `{assetId, ownership}` entries -- see the flat-list note below) and
`dynastyLeague` (the same context block `dynasty_bootstrap` already uses).

**A real bug found and fixed this pass, before it ever reached the live
app:** my first draft returned ownership as a dict keyed by the literal
asset id (`{"current:9493": {...}}`). This worktree already has a
documented, load-bearing hazard for exactly this shape --
`contracts.public_json_value`/`camel_case_key` walks every JSON object key
and camelCases it as if it were a schema field name, so `"current:9493"`
silently became `"currentFixturePlayer"`-style mangled garbage (reproduced
live via a direct HTTP call against `FakeFacade` in
`test_desktop_http_api.py` before any browser was involved -- see the
"Differing items" `KeyError` this pass's own test run surfaced). Fixed by
switching to a flat `Array<{assetId, ownership}>` list, the exact same
shape `redraft_decision_bundle`'s own `positions`/`traceIds`/
`decisionEnvelopes` already use for the identical reason (their own code
comments cite the same hazard). This is now the second real, independently
found instance of this exact class of bug in this codebase (the first
being the "camelCase-dict-key serialization bug" the owner feedback
closure V4 saga already found in Cheat Sheets) -- worth the owner's
continued awareness any time a dict is keyed by a live data id rather than
a fixed schema field name.

**Byte-identical-when-omitted, tested**
(`tests/test_dynasty_league_import_facade_wiring.py`,
`test_compare_dynasty_assets_is_byte_identical_when_league_profile_id_omitted`):
`compare_dynasty_assets(ids)` and `compare_dynasty_assets(ids,
league_profile_id=None)` produce byte-identical JSON, `"ownership"` and
`"dynastyLeague"` both absent.

**Annotation is provably additive, tested**
(`test_compare_dynasty_assets_with_league_profile_id_adds_ownership_without_touching_scores`):
strips the two new keys back out of the annotated response and asserts
byte-identical equality against the unannotated response for everything
else -- `leans`/`ranges`/`players`/`bridge`/`warnings` are untouched by
connecting a league. Also asserts a real `current:9493` (Puka Nacua, this
fixture's one owned asset) resolves `OWNED`/`isMyTeam: true`/`rosterTeamName:
"Niners"`, and that no `pick:*` asset ever appears in `ownership` (no
ownership concept for picks -- never guessed).

**Frontend (`desktop/apps/dynasty/src/pages/decisions.tsx`):**
`ComparePage`'s `AssetPicker`/`SelectedChips` (shared with Trade Lab) show
a live ownership badge per asset sourced from the already-annotated
`data.assetOptions` (bootstrap-time truth -- present the instant the
picker renders, before any comparison runs). After running a comparison,
`ComparisonResult` additionally renders the comparison's OWN `ownership`
list (evaluation-time truth) as a small badge in the BODY of each
`ranges`/`players` Panel, plus a one-line "Ownership context: connected to
{league}" disclosure directly under the section title stating explicitly
that the label never changes a lean/range/dimension/advantage. New pure
helper `ownershipLookup()` (`desktop/apps/dynasty/src/lib/ownership.ts`)
turns the flat list back into a `Map` for lookups; the module's own
comment documents exactly why the list shape exists (the camelCase-key
hazard above).

**A real, live, reproduced-and-fixed layout bug (LIVE OBSERVATION via
Chrome MCP, not just code review):** my first attempt put the ownership
badge inside `AssetPicker`'s own per-row `<button>` (stacked as a third
line under the player name/position). Live in the browser this visually
OVERLAPPED into the next row -- `getBoundingClientRect()` proved the
button's own box stayed a fixed 38px tall (`.asset-picker` is a CSS grid
whose row tracks resolved to a uniform 38px, matching only the
`min-height: 38px` media-query rule, not the taller actual content) while
the badge's own rect extended 8px past the button's bottom edge, into the
next grid row. Fixed by removing the badge from `AssetPicker`'s row
entirely (kept it in `SelectedChips`, which is a flex-wrap row and
provably does not have this constraint) and, separately, by moving the
`ComparisonResult`/`TradeResult` panel badges from the `Panel` component's
`action` header slot into the panel BODY -- the header slot also
overlapped/clipped text live when paired with a multi-word eyebrow
("Advantages & uncertainty" wrapped to 3 lines and the badge visually cut
across it, confirmed via `zoom` screenshot before the fix and confirmed
clean after). Both fixes verified live via a real rebuild
(`npm run build:dynasty`) + hard reload + screenshot before reporting
either "fixed."

**Tests added:** `ownership.test.ts` unchanged (no new branches needed for
`ownershipLookup`, which is a one-line pure transform); no new dedicated
unit test file for the layout fix itself since it is not pure logic --
verified instead by the live `getBoundingClientRect()` evidence above plus
a final live screenshot showing zero overlap.

### 2. Trade Decision Lab wiring (INSPECTED CODE + ACTUAL TEST RESULT + LIVE OBSERVATION)

`evaluate_dynasty_trade` gained the identical optional
`league_profile_id: str | None = None` parameter, with the identical
structural guarantee: `evaluate_trade_decision(state, lookup,
team_window=team_window)` is called and converted to `data` via
`_trade_decision_payload(decision)` BEFORE the new `if league_profile_id:`
block ever runs -- `evaluate_trade_decision` never receives
`league_profile_id` at all, so there is no code path by which ownership
could influence the trade-value computation, not just a tested behavior
but a structural fact provable from the diff alone. When set, it
annotates the union of `give_ids`/`receive_ids` and attaches the same
`ownership`/`dynastyLeague` shape as Compare.

**Byte-identical-when-omitted and provably-additive, tested** (same two
test patterns as Compare, in `test_dynasty_league_import_facade_wiring.py`):
`test_evaluate_dynasty_trade_is_byte_identical_when_league_profile_id_omitted`
and
`test_evaluate_dynasty_trade_with_league_profile_id_flags_a_real_non_roster_give_side`
-- the latter builds a real give-side asset that is NOT on the fixture
league's roster 7 (confirmed `FREE_AGENT`/`isMyTeam: false`) and a
receive-side asset that IS (`current:9493`, `isMyTeam: true`), and asserts
the trade decision's own fields are byte-identical whether or not the
league is connected.

**The owner's exact correctness requirement -- real, live, working (LIVE
OBSERVATION):** new pure functions in `decisions.tsx`
(`rosterOwnedAssetIds`, `fillTradeSideFromRoster`,
`resolveTradeRosterWarnings`; 5 new unit tests in `decisions.test.ts`,
covering opponent-owned/free-agent/unresolved-rookie give-side cases, an
already-owned receive-side case, and the "no ownership data at all ->
never warn" case) compute LIVE warnings from the bootstrap-time
`data.assetOptions` ownership as soon as the owner selects assets --
before any "Evaluate" click. Live-reproduced against the real connected
league (Las Vegas Enginerds): selected Puka Nacua (real roster 9, "Rocky
Mountain High") onto the GIVE side and the app immediately rendered *"Puka
Nacua is on your give side, but is currently owned by Rocky Mountain High
in your connected league, not your roster."* -- the exact real scenario
the dispatch asked to catch, using real annotated ownership data, with
zero code path into `evaluate()`/the trade computation.

**"My side" is now REAL by default, override still fully manual (the
dispatch's other explicit requirement):** a new "Fill from your roster"
button (`Panel`'s `action` slot on the "You give" panel, shown only when a
league is connected and at least one real roster-owned asset exists) calls
`fillTradeSideFromRoster`, which appends real `isMyTeam` asset ids onto
whatever the owner has already picked -- never removes/reorders an
existing manual pick, never adds past the 6-asset side limit, and every
filled asset remains individually removable via its chip's `x` exactly
like a manually added one. Live-verified: clicking it on an empty "You
give" side filled exactly the 6 real roster-7 starters/bench players
(De'Von Achane, Zay Flowers, Drake Maye, Chase Brown, Jameson Williams,
Wan'Dale Robinson -- all real, all matching the live Sleeper roster
fetched independently below), each chip correctly labeled "ON YOUR
ROSTER". The owner can still freely remove any of these or add a
non-owned asset (as demonstrated by the Puka Nacua warning scenario
above) -- this is a real default, never a hard constraint.

**Post-evaluation ownership record, also live-verified:** `TradeResult`
renders a new "Roster context at evaluation" panel (only when
`decision.dynastyLeague` is present) listing every give/receive asset with
its ownership badge sourced from `decision.ownership` -- the real snapshot
AS OF that specific evaluation, kept deliberately separate from the live
picker-time warnings above so a saved/exported trade brief always carries
what was true when it was evaluated. Live-evaluated a real 6-for-1 package
(5 real roster players + Puka Nacua vs. Jonathan Taylor) and the app
correctly rendered `REJECT`/`MEDIUM` confidence (the real, untouched
trade-value computation) alongside a correct roster-context table (5x "ON
YOUR ROSTER", Puka Nacua "OWNED BY ROCKY MOUNTAIN HIGH" on the give side,
Jonathan Taylor "OWNED BY DIRT DEVILS" on the receive side) and the
explicit disclosure line: *"This ownership record never changed the
recommendation, confidence, or any dimension above."*

### 3. HTTP routes (INSPECTED CODE + ACTUAL TEST RESULT)

`src/desktop_api/server.py`: `POST /api/v1/dynasty/compare` and `POST
/api/v1/dynasty/trades/evaluate` now pass
`league_profile_id=self.server.facade.dynasty_active_league_profile_id()`
-- the exact same "read the persisted active-league marker at the call
site" pattern Worker 3 established for `/api/v1/dynasty/workspace` and
`/api/v1/dynasty/assets/{id}`; no new persistence mechanism, no new mode
gate (both routes were already dynasty-only; `dynasty_active_league_profile_id`
is itself dynasty-mode-gated, so a redraft-mode request still fails with
the same `MODE_ROUTE_UNAVAILABLE` it always did, just raised one call
earlier in the chain -- confirmed no test anywhere asserts the specific
call site for that error, only the code). New route-level test
`test_dynasty_compare_and_trade_routes_pass_the_active_league_profile_id`
in `tests/test_desktop_http_api.py` proves both routes read the active
marker without the frontend resending a profile id.

### 4. Isolation testing (LIVE OBSERVATION, real running apps)

- **Dynasty vs. Redraft independence:** opened a second tab against
  Redraft's real running frontend (`http://127.0.0.1:1422/`, untouched
  PID `16376`) while Dynasty's tab simultaneously showed "CONNECTED: LAS
  VEGAS ENGINERDS" -- Redraft independently showed its own real active
  league, "Fantasy Gamers" (`local_exports/redraft_v1/`'s own
  `active_profile.json`), completely unaffected. Did not click or modify
  anything in the Redraft tab (read-only observation only, per the hard
  boundary); closed the tab immediately after. This is consistent with,
  and now re-confirms with a real simultaneous two-tab observation, the
  structural fact Worker 3 already established: the two apps use entirely
  separate persistence roots (`local_exports/dynasty_v1/` vs.
  `local_exports/redraft_v1/`) and entirely separate backend processes.
- **Persistence across a real backend restart (second independent
  confirmation of Worker 3's own result):** killed the Dynasty backend
  process this session inherited (PID `41112`) to pick up this pass's
  Python changes, relaunched a brand-new process
  (`scripts/run_nwr_desktop_api.py --port 18741 --mode dynasty`, new PID
  `40244`, confirmed via `netstat`), and confirmed via a direct
  `GET /api/v1/bootstrap` call that `dynastyLeague.profileId` was still
  `1344772855908290560` -- zero shared memory with the killed process,
  same result as Worker 3's own restart test.
- **Hard reload:** `location.reload()` in the live browser tab preserved
  the connected state (server-side marker, no browser storage involved).
- **Disconnect -> reconnect cycle, live, end to end:** clicked
  "Disconnect league" on Data Health -- real message "League disconnected.
  Ownership context is hidden again." and the form reverted to its
  disconnected state. Re-entered the exact league id
  (`1344772855908290560`) and owner id (`1352768154031374336`) using the
  `computer` click+type technique (per Worker 3's own documented
  `form_input`-precision-loss gotcha for 19-digit Sleeper ids -- re-hit
  this pass while testing the flow, confirmed still a live tool
  limitation), clicked "Connect league" -- real success message "League
  connected. Ownership context is now live across Home, Asset Explorer,
  and Player Detail," a fresh real import timestamp
  (`Imported 9/18/2026, 6:25:55 PM`, distinct from the pre-existing
  connection's `5:57:02 PM` timestamp, proving a real new live Sleeper
  fetch happened, not a cached replay).
- **Roster-accuracy spot-check against live Sleeper data, fetched
  independently this pass (not reused from any prior worker's capture):**
  `GET https://api.sleeper.app/v1/league/1344772855908290560/rosters`
  (direct call, this session, 2026-09-18) confirmed roster 7's real
  `owner_id` (`1352768154031374336`) and real player list. Cross-referenced
  6 of those real player ids against `GET
  https://api.sleeper.app/v1/players/nfl` (also fetched fresh this pass)
  and against what the Dynasty app's own live "Fill from your roster"
  button populated: **De'Von Achane (9226), Zay Flowers (9997), Jameson
  Williams (8148), Drake Maye (11564), Chase Brown (9224), Wan'Dale
  Robinson (8126) -- all 6 independently confirmed on the real live
  Sleeper roster 7 AND all 6 rendered by the app as "ON YOUR ROSTER."**
  This exceeds the requested 2-3-player minimum. No real roster drift was
  found since Worker 2/3's own captures earlier the same day (expected --
  same in-season week, no waiver claims processed in the intervening
  hours).

### 5. Tests -- cumulative counts (ACTUAL TEST RESULT)

- `pytest tests/test_desktop_http_api.py tests/test_dynasty_league_import_facade_wiring.py tests/test_dynasty_sleeper_league_service.py tests/test_desktop_facade_architecture_wiring.py tests/test_status_override_intake_facade.py`
  -- **93 passed** (Worker 3's 83 baseline + 5 new facade tests + 1 new
  service-level assertion set folded into existing files + 4 new HTTP
  route/behavior tests worth of net growth; exact breakdown: 4 new tests
  in `test_dynasty_league_import_facade_wiring.py`, 1 new test in
  `test_desktop_http_api.py`, plus the pre-existing 83 + the previously
  un-summed `test_status_override_intake_facade.py` file now included in
  this pass's combined run for completeness).
- `pytest tests/test_desktop_application_api.py` -- **4 failed, 46
  passed**, `git stash`-confirmed identical to the untouched Worker-3 HEAD
  (same 4: `test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_facade_has_no_streamlit_or_app_component_dependency` -- all real,
  pre-existing date-freshness/market-drift/import-hygiene failures
  unrelated to Dynasty league import, matching this worktree's own
  documented baseline). Zero new failures introduced.
- `npm run typecheck` (both `apps/dynasty` and `apps/redraft` tsconfig
  projects) -- clean, zero errors.
- `npx vitest run` (whole `desktop/` workspace) -- **491 passed, 30
  files** (Worker 3's 486 baseline + 5 new pure-function tests in
  `decisions.test.ts`). The `frontend_bench_results.json` timing-noise
  regeneration Worker 3 already documented recurred this pass too;
  reverted via `git checkout --` before committing, same as Worker 3.

### 6. Native build (INSPECTED CODE + LIVE OBSERVATION)

**Applies to Dynasty -- inspected, not assumed.** `desktop/package.json`
has `bundle:dynasty` (`check:resources && sidecar:build &&
tauri:build --workspace @nwr/dynasty-desktop`), the exact structural
mirror of `bundle:redraft`. Dynasty is NOT web-only by design in this
repo; a native Tauri package is a real, supported target for it.

**Skipped this pass due to genuinely insufficient host memory, not
forced into a doomed attempt.** `Get-CimInstance Win32_OperatingSystem`
at the time of this decision: **0.98 GB free out of 15.11 GB total** --
lower than the prior cycle's own documented OOM-blocking condition for
Redraft's native build. A Tauri/Rust release build needs multiple GB of
free RAM for the Rust compiler alone; attempting one here would almost
certainly repeat the prior documented failure rather than produce a real
result. Per this pass's own explicit instruction ("if memory is
insufficient, skip and report why rather than forcing a failure"), no
`bundle:dynasty` attempt was made. This remains a real, open item for a
future pass once the host has more free RAM -- not evidence that Dynasty
lacks native packaging.

### 7. Dynasty processes status (final, LIVE OBSERVATION)

Frontend: `http://127.0.0.1:1421/` -- PID `37176` (same process the whole
pass; a real rebuild via `npm run build:dynasty` was run twice this pass
to pick up the frontend code/CSS changes -- required, since this process
runs `vite preview`, which serves the last build from disk, not source;
each rebuild was followed by a real `location.reload()` and a live
screenshot/DOM check before treating it as picked up). Backend:
`http://127.0.0.1:18741/` -- PID `40244` (restarted once this pass to pick
up the Python facade/route changes; confirmed via `netstat` and a direct
`GET /api/v1/bootstrap` call). **Real league IS connected** at the end of
this pass: `dynastyLeague.profileId == "1344772855908290560"`,
`leagueName == "Las Vegas Enginerds"`, `myRosterId == 7` -- reconnected
deliberately after the disconnect/reconnect test, left live for the owner.

### 8. Redraft processes status (final, LIVE OBSERVATION)

Frontend: `http://127.0.0.1:1422/` -- PID `16376`. Backend:
`http://127.0.0.1:18742/` -- PID `31352`. **Both identical to the PIDs
observed at the very start of this pass** -- neither process was ever
restarted, killed, or had any file under its control modified. The one
interaction with Redraft this pass was a single read-only `navigate` +
`screenshot` in a second browser tab (see Isolation testing above),
immediately closed.

### Files changed

- `src/application/desktop_facade.py` (`compare_dynasty_assets`/
  `evaluate_dynasty_trade` gained the optional `league_profile_id`
  parameter and the additive `ownership`/`dynastyLeague` block; every
  pre-existing line of each method's body before that point is
  unchanged).
- `src/desktop_api/server.py` (2 routes now pass the active league
  profile id through, same pattern as Worker 3's other routes).
- `tests/test_dynasty_league_import_facade_wiring.py` (4 new tests).
- `tests/test_desktop_http_api.py` (1 new route-level test, `FakeFacade`
  signature updates for the new kwarg and the flat-list `ownership`
  shape).
- `desktop/packages/contracts/src/index.ts` (new `AssetOwnershipEntry`
  type; additive optional `ownership`/`dynastyLeague` fields on
  `DynastyComparison`/`TradeDecision`).
- `desktop/apps/dynasty/src/lib/ownership.ts` (new `ownershipLookup()`
  helper).
- `desktop/apps/dynasty/src/pages/decisions.tsx` (Compare + Trade
  Decision Lab wiring: ownership badges, live roster-mismatch warnings,
  "Fill from your roster," post-evaluation roster-context panel; new pure
  functions `rosterOwnedAssetIds`/`fillTradeSideFromRoster`/
  `resolveTradeRosterWarnings`/`ownershipLookup` usage/`OwnershipTag`).
- `desktop/apps/dynasty/src/pages/decisions.test.ts` (5 new tests for the
  new pure functions).
- `desktop/apps/dynasty/src/pages.css` (new, narrowly-scoped rules for
  the chip badge, the roster-warning strips, and the roster-context body
  layout; explicitly does NOT add a rule for the reverted
  `AssetPicker`-row badge attempt, with a comment explaining why).
- `docs/codex/dynasty_league_import_v1/LEDGER.md` (this section).

Not committed (pre-existing untracked leftovers from earlier workers'
sessions, not touched or relied upon by this pass):
`dynasty_smoke_stderr.log`, `dynasty_smoke_stdout.log`,
`local_exports.backup-20260918T230905Z/`.

### For the owner -- precise, evidence-backed summary

**Working capabilities (all live-verified this pass, not inferred):**
- Connect/Disconnect a real Sleeper Dynasty league from Data Health,
  surviving a hard reload AND a full backend process restart.
- Home, Asset Explorer, Dynasty Rankings, Rookie Review, and Player Detail
  all show real ownership badges once connected (Worker 3; re-confirmed
  live this pass).
- **Compare** now shows real ownership badges (picker/chips live,
  per-asset panels after running a comparison) without altering any lean,
  range, dimension, advantage, or bridge value -- structurally guaranteed
  and tested.
- **Trade Decision Lab** now shows real ownership on both sides, a live
  "you don't actually own this give-side asset" warning the instant it's
  selected (before evaluating), a one-click "Fill from your roster" that
  defaults the give side from real roster data while leaving every pick
  manually removable/addable, and a post-evaluation "Roster context at
  evaluation" record -- none of it touches the trade recommendation,
  confidence, or dimension outcomes.
- Rookie assets consistently show "Ownership unresolved" everywhere
  (Compare and Trade Lab included) -- never a guessed or omitted status.

**Remaining gaps (precise, not glossed over):**
- No multi-league picker UI still exists (Worker 3's own open item,
  unchanged) -- connecting a different league overwrites which profile is
  "active"; the backend supports arbitrary saved profiles already.
- Rookie ownership crosswalk still does not exist -- "unresolved" is
  correct behavior, not a placeholder for a future real answer without
  new work.
- No native Tauri build was produced this pass (host had 0.98 GB free
  RAM) -- browser-based verification through the real running app is the
  only verification status for this pass; the installed native app was
  NOT rebuilt or re-verified.
- The Connect League form still does no client-side league-id
  pre-validation beyond non-empty (Worker 3's own open item, unchanged).
- "Fill from your roster" only fills the GIVE side (matches the exact
  wording of the dispatch's own requirement); there is no equivalent
  one-click helper for auto-suggesting realistic receive-side targets.

**Click-to-test instructions (for the owner, using the browser build left
running):**
1. Open `http://127.0.0.1:1421/#/data-health` -- confirm the connected
   league banner reads "Connected: Las Vegas Enginerds · Your team: Niners
   · Roster #7."
2. Open `http://127.0.0.1:1421/#/compare` -- pick 2-4 assets (opponent-
   owned assets show a real "Owned by {team}" badge in the picker chips);
   click "Compare now"; scroll to any player panel and confirm the
   ownership badge appears under the player name, separate from the
   floor/expected/ceiling and advantages/risks content above it.
3. Open `http://127.0.0.1:1421/#/trades` -- click "Fill from your roster"
   to see the real give side populate; try adding an opponent's player to
   the give side and watch the real warning banner appear immediately;
   click "Evaluate trade" and scroll to "Roster context at evaluation" to
   see the ownership record tied to that specific evaluation.
4. On Data Health, click "Disconnect league" then reconnect with league id
   `1344772855908290560` and owner id `1352768154031374336` to see the
   full real cycle again.

**Browser-vs-installed-app verification status:** every claim above was
verified through the real running browser build
(`http://127.0.0.1:1421/`, `vite preview` serving a real
`npm run build:dynasty` output) against the real backend
(`http://127.0.0.1:18741/`, real HTTP requests, real Sleeper data). The
native Tauri-packaged desktop app was NOT built or verified this pass (see
Native build above) -- this is an honest, disclosed gap, not an
overclaim.

---
