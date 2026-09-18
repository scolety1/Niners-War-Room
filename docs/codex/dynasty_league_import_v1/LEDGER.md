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
