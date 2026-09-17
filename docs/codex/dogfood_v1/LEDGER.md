# NWR Dogfood + Bug-Fix Cycle V1 — LEDGER

New, bounded ledger for this cycle. Separate from `docs/codex/full_cycle_v1/LEDGER.md`
(prior 10-worker cycle) and `docs/codex/prospective_outcomes_v1/LEDGER.md` (earlier
still). Do not conflate the three.

## Worker 1 — real-league chooser gap: investigation + safe data recovery (2026-09-17)

### Context / trigger

Owner's PC was accidentally restarted, killing the Redraft (127.0.0.1:1422/18742)
and Dynasty (127.0.0.1:1421/18741) dev-server processes from the prior 10-worker
cycle. Owner reported that the Redraft chooser at `http://127.0.0.1:1422/#/leagues`
showed only 3 entries — **Fantasy Gamers**, **10-team 1QB Standard**, **Isolation
Check Local** — versus a real scope of 4 leagues (Fantasy Gamers, a Sleeper dynasty
league, KHA High Stakes (ESPN), 403 N 18th and friends (ESPN, league ID
`1009373442`)). This worker's task was investigation + safe, read-based recovery
only — no dev servers were started, no engine/scoring code was touched.

### 1. Data-root resolution — INSPECTED CODE

- `desktop/scripts/nwr_release_gate_smoke.ps1` (the script used to start this
  worktree's Redraft instance in the prior cycle) invokes
  `scripts/run_nwr_desktop_api.py --repo-root $RepoRoot --mode redraft ...`
  with `$RepoRoot` defaulting to the worktree root
  (`desktop/scripts/..\..` = `C:\NWR\prospective-outcomes-v1`). **It never sets
  `NWR_REDRAFT_HOME`.**
- `scripts/run_nwr_desktop_api.py` passes `repo_root` straight into
  `DesktopBackendFacade(repo_root=repo_root, mode=args.mode)`
  (`src/application/desktop_facade.py:497-515`).
- `DesktopBackendFacade.__init__` sets `self.redraft_root =
  redraft_store_root(self.repo_root)` when no explicit `redraft_root` is passed.
- `redraft_store_root()` (`src/services/redraft_engine_v1_service.py:255-260`):
  ```python
  def redraft_store_root(repo_root=None):
      configured = os.environ.get("NWR_REDRAFT_HOME", "").strip()
      if configured:
          return Path(configured).expanduser().resolve()
      base = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[2]
      return base / "local_exports" / "redraft_v1"
  ```
- `desktop/scripts/save-kha-draft-checkpoint.ps1` (comment header) independently
  confirms and documents the same resolution order, and states the REAL Tauri
  app sets `NWR_REDRAFT_HOME` itself:
  `desktop/crates/nwr-desktop-runtime/src/lib.rs:196-241`:
  `state_dir = app.path().app_local_data_dir() / "state"`;
  `env NWR_REDRAFT_HOME = state_dir / "redraft"`.
- **Conclusion (ACTUAL TEST RESULT, verified live this session):** this shell/
  environment has `NWR_REDRAFT_HOME` unset (`env | grep NWR_REDRAFT` → empty).
  With that env var unset and `--repo-root` pointed at this worktree, the
  backend's real store root resolves to
  `C:\NWR\prospective-outcomes-v1\local_exports\redraft_v1` — a **stale,
  repo-relative fallback seed directory, not the real Tauri app's live state**.
  This exactly matches what `save-kha-draft-checkpoint.ps1`'s own header already
  warns about ("a stale, pre-draft seed copy, NOT live app state... silently
  missing the real KHA board on 2026-09-02 is the incident this fixes").

This is a **real, reproducible characteristic of how the worktree's dev
instance was started** — not a code bug. No code change was made or is
recommended here; `NWR_REDRAFT_HOME` behaves exactly as designed. The owner's
"only 3 leagues" observation is fully explained: the smoke-script-started
backend was reading the worktree-local fallback store, which only ever had 3
profiles in it, while the owner's 2 other real leagues live only in the real
Tauri app's AppData state that this dev-server invocation never pointed at.

### 2. Locations inventoried (LIVE OBSERVATION — filesystem reads only)

| # | Location | What's there |
|---|----------|---------------|
| 1 | `C:\NWR\prospective-outcomes-v1\local_exports\redraft_v1\profiles\` (this worktree's fallback store — what the smoke-script-started backend actually reads) | 3 profiles: Fantasy Gamers (real, sleeper), Isolation Check Local (test, local), 10-team 1QB Standard (see below) |
| 2 | `%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\` (real Tauri app's live state root — read-only inspected, NOT modified) | 6 profiles + `active_profile.json` currently pointing at "Tester" — see table below |
| 3 | `%LOCALAPPDATA%\com.ninerswarroom.redraft.backup-20260916T140835Z\` (verified backup, read-only inspected, NOT modified) | Structurally identical file set to #2 (same 6 profile IDs, same draft boards) — a full snapshot taken 2026-09-16T14:08:35Z, consistent with #2 |
| 4 | `%LOCALAPPDATA%\com.ninerswarroom.dynasty\` (real Tauri Dynasty app data, read-only inspected, NOT modified) | Only `logs/` and `state/runtime.json` — **no per-league profile store of any kind exists in the Dynasty app's data directory** |
| 5 | Sibling worktree `C:\NWR\live-player-intelligence-v1\local_exports\redraft_v1\profiles\` | Fantasy Gamers (same real Sleeper ID `1312983576827920384`) + 1 local test/QA profile only |
| 6 | Sibling worktree `C:\NWR\post-closure-fixes-v1\local_exports\redraft_v1\profiles\` | Fantasy Gamers (same ID) + 1 local test/QA profile only |
| 7 | Sibling worktree `C:\NWR\post-ui-product-v1\local_exports\redraft_v1\profiles\` | Fantasy Gamers (same ID) + 7 local test/QA profiles only |
| 8 | Sibling worktree `C:\NWR\overnight-full-advance-v3\local_exports\redraft_v1\profiles\` | Fantasy Gamers (same ID) + 3 local test/QA profiles only |
| 9 | Sibling worktrees `post-ui-v2-research`, `upgrade-pre-ui-architecture-v1`, `overnight-lane3-league-shell`, and the bare `Niners-War-Room` checkout | No `local_exports/redraft_v1/profiles/` directory at all — structurally cannot hold profile data |
| 10 | `docs/` repo-wide (this worktree) | No dynasty-Sleeper-league setup doc, checklist, or league-ID reference anywhere (grepped for "sleeper dynasty" / "dynasty sleeper league" style terms — zero hits, consistent with prior cycle's Worker 8 finding) |

None of the other worktrees or the `docs/` tree contain any KHA, 403 N 18th, or
dynasty-Sleeper profile that isn't already accounted for by the real AppData
install (#2/#3).

### Real AppData profiles (`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\profiles\`) — full inventory

| profile_id | league_name | provider | team_count | updated_at_utc | draft picks | Disposition |
|---|---|---|---|---|---|---|
| `4c5f04762921420595e4d8c7cda76582` | Fantasy Gamers | sleeper (`1312983576827920384`) | 10 | 2026-08-14 | n/a (Sleeper-imported) | Same real league as the worktree's own Fantasy Gamers profile (different, older profile_id/copy) — already present and real in the worktree; not recovered (would be a duplicate of an already-present real league) |
| `fb1c49402c7644a99120197d41344bbb` | **2026 KHA High Stakes League** | espn | 16 | 2026-09-02T04:01:25Z | **157** | REAL, complete. **RECOVERED.** |
| `f92cff21ca33456d91f880a2b457b3fe` | 2026 KHA High Stakes League — TEST | espn | 16 | 2026-09-02T04:01:25Z | 9 | Test duplicate, not recovered (owner did not ask for it; incomplete draft board) |
| `16d2e55044f64b1891e57c7481d18723` | 2026 KHA High Stakes League — PRACTICE 20260905 | local | 16 | 2026-09-05 | 6 | Practice/test variant, not recovered |
| `4b4a990faf124ce7a5d612537ba5943b` | **403 N 18th and friends** | espn | 8 | 2026-09-09T00:48:33Z | **118** | REAL, complete (118 picks matches memory's documented real draft exactly). **RECOVERED.** |
| `eafa580e18d646b3906af9c9e213602a` | Tester | espn | 10 | 2026-09-09 | n/a | Test profile. **This is the real AppData install's CURRENT `active_profile.json` target** — flagged as an open issue below, not touched |

`provider_league_id` is stored as `null` in the profile JSON for both ESPN
leagues; the real ESPN league ID `1009373442` for 403 N 18th was confirmed
instead via `grep` inside
`state/redraft/projections/2026/DRAFT_DAY_AUTHORIZATION.json`
(`"effective_scope": "403 N 18th and friends real draft only (2026-09-07 8:00
PM MDT, ESPN leagueId 1009373442, 8-team, full PPR)"`) — a real, dated
owner-authorization receipt, not an inference.

### 3. Per-league disposition

**LEAGUE 1 — Fantasy Gamers.** Confirmed REAL, not a stub. Worktree profile
`941b99ade350410391b1b67c0890af79`: provider `sleeper`, `provider_league_id
"1312983576827920384"`, `created_at_utc 2026-09-15`, `updated_at_utc
2026-09-16T23:01:52Z`, backed by a 214KB `decision_traces/…jsonl`, real
`sleeper_imports/…json` (7.7KB), and 2 real `weekly_projection_health` files
(~900KB/1MB each, dated through this morning). This is the most complete,
most recently touched profile of anything found anywhere. No action taken —
already correct.

**LEAGUE 2 — Dynasty Sleeper league.** Still **genuinely not found anywhere**
on this machine. Checked: this worktree's own store (no dynasty/2nd-Sleeper
profile), the real AppData Redraft install and its backup (same), the real
AppData **Dynasty app's own data directory** (`com.ninerswarroom.dynasty` —
only `logs/` + `runtime.json`, no profile store structure exists at all — this
independently reconfirms the prior cycle's Worker 8 architecture finding that
Dynasty is a governed asset board with no per-league import path, not merely
"not configured yet"), and every sibling worktree with a `local_exports/
redraft_v1/profiles/` directory. `docs/` repo-wide grep for dynasty-Sleeper
setup language: zero hits. **This is a real, reportable product-scope gap, not
a data-recovery task** — nothing was fabricated to fill it.

**LEAGUE 3 — KHA High Stakes (ESPN).** Found REAL and complete at
`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\profiles\
fb1c49402c7644a99120197d41344bbb.json` — 16-team, 157-pick completed draft
board, real `manual_assets` and `owner_test_instrumentation/events.jsonl`.
**RECOVERED** (see Data Copied below).

**LEAGUE 4 — 403 N 18th and friends (ESPN, `1009373442`).** Found REAL and
complete at `…\profiles\4b4a990faf124ce7a5d612537ba5943b.json` — 8-team,
118-pick completed draft board (matches memory's "118 picks, live 2026-09-07
~8pm MDT" exactly), plus a real dated `DRAFT_DAY_AUTHORIZATION.json` receipt
naming league ID `1009373442` explicitly, real `manual_assets`,
`owner_test_instrumentation/events.jsonl` (417 lines),
`prospective_decision_log/…/decisions.jsonl` (72 lines),
`nwr_pure_experiments/…` (corrections + decisions), an ADP provider-cache
league-selection entry, and an ADP snapshot file. **RECOVERED** (see Data
Copied below).

**"10-team 1QB Standard" profile — what it actually is.** `INSPECTED CODE +
LIVE DATA`: `10_TEAM_1QB_STANDARD` is a **builtin preset key** defined in
`redraft_engine_v1_service.py:builtin_presets()` — display name "10-team 1QB
Standard" is the preset's own label, always available for creating a new
profile. This worktree's profile
`c5c77f621138494383af7fc11cc41ef4.json` is a **separate, real saved profile**
(provider `local`, `preset_key "10_TEAM_1QB_STANDARD"`,
`created_at_utc/updated_at_utc` both `2026-09-16T22:16:08Z`, i.e. created and
never touched again) — i.e., a prior worker created a profile *from* that
preset (likely for smoke-testing) and it was saved to disk with no further
edits, no draft, no roster. It is **not** a duplicate of Fantasy Gamers and
**not** one of the owner's 4 real leagues — it is a throwaway/smoke-test
artifact, same category as "Isolation Check Local," just named after its
source preset instead of being given a distinguishing test name. **Left in
place, not deleted, per the directive** (do not delete test profiles).

### 4. Backup made before any reconciliation

Before copying anything into this worktree's data root, the pre-recovery state
of that root was fully snapshotted:

- **Source:** `C:\NWR\prospective-outcomes-v1\local_exports\redraft_v1\`
  (11 files at the time)
- **Backup:** `C:\NWR\prospective-outcomes-v1\local_exports\redraft_v1.backup-20260917T224444Z\`
  (11 files, verified identical count; created via `cp -a`, a plain recursive
  copy — same pattern as the existing
  `com.ninerswarroom.redraft.backup-20260916T140835Z` convention)

The real AppData install and its existing backup (`…backup-20260916T140835Z`)
were **never written to** — only read. No backup of them was needed since this
was a pure read/copy-out operation; verified after the fact by re-hashing
(`md5sum`) all 4 source files that were copied from and confirming byte-for-
byte match against the destination copies (see below) — the source files
themselves were never opened for writing.

### 5. Data copied (source → destination, all additive, zero overwrites)

Source root: `%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\`
Destination root: `C:\NWR\prospective-outcomes-v1\local_exports\redraft_v1\`

KHA (`fb1c49402c7644a99120197d41344bbb`):
- `profiles/fb1c49402c7644a99120197d41344bbb.json`
- `draft_boards/fb1c49402c7644a99120197d41344bbb.json`
- `draft_boards/fb1c49402c7644a99120197d41344bbb.backup.json`
- `manual_assets/fb1c49402c7644a99120197d41344bbb.json`
- `owner_test_instrumentation/fb1c49402c7644a99120197d41344bbb/events.jsonl`
- (KHA has no `prospective_decision_log/`, `nwr_pure_experiments/`,
  `adp_provider_cache` league entry, or `adp_snapshots` entry in the source —
  correctly nothing copied for those, not an omission)

403 N 18th (`4b4a990faf124ce7a5d612537ba5943b`):
- `profiles/4b4a990faf124ce7a5d612537ba5943b.json`
- `draft_boards/4b4a990faf124ce7a5d612537ba5943b.json`
- `draft_boards/4b4a990faf124ce7a5d612537ba5943b.backup.json`
- `manual_assets/4b4a990faf124ce7a5d612537ba5943b.json`
- `owner_test_instrumentation/4b4a990faf124ce7a5d612537ba5943b/events.jsonl`
- `prospective_decision_log/4b4a990faf124ce7a5d612537ba5943b/decisions.jsonl`
- `nwr_pure_experiments/4b4a990faf124ce7a5d612537ba5943b/corrections.jsonl`
- `nwr_pure_experiments/4b4a990faf124ce7a5d612537ba5943b/decisions.jsonl`
- `adp_provider_cache/owner_platform_snapshot/leagues/4b4a990faf124ce7a5d612537ba5943b.json`
- `adp_snapshots/4b4a990faf124ce7a5d612537ba5943b.json`

**Every copy target path was confirmed not to already exist in the
destination before copying** (script logic: copy only if source exists AND
destination does not — zero `SKIP`/overwrite events occurred for either
league; both profile IDs were entirely new to the worktree's store). Shared,
non-per-profile state (`projections/2026/current.*`, the global ADP/Ballers
snapshots) was deliberately **NOT** copied — the worktree already has its own
(more recent) `projections/2026/` and touching shared season-level projection
files was out of scope and risked overwriting newer local state with older
AppData state.

**Verification (ACTUAL TEST RESULT):**
- `md5sum` of all 4 largest copied files (both profiles' `profiles/*.json`
  and `draft_boards/*.json`) matched byte-for-byte between source and
  destination.
- All 10 copied `.json` files parse cleanly via `json.load` (zero
  `JSONDecodeError`).
- All 5 copied `.jsonl` files have real line counts (1, 417, 72, 1, 2 —
  493 lines total), not empty/stub files.
- **Ran the real, unmodified backend service function** (no mocks):
  ```python
  from services.redraft_engine_v1_service import redraft_store_root, list_profiles
  root = redraft_store_root(".")  # == this worktree, NWR_REDRAFT_HOME unset
  list_profiles(root, include_archived=True)
  ```
  Result: 5 profiles now resolve with **zero errors** —
  `10-team 1QB Standard`, `2026 KHA High Stakes League`,
  `403 N 18th and friends`, `Fantasy Gamers`, `Isolation Check Local`.
  This is the exact function the desktop API's profile-listing endpoint calls,
  so the next worker starting the dev server pair the same way the prior
  cycle did (smoke script / `run_nwr_desktop_api.py --repo-root <this
  worktree>`, no `NWR_REDRAFT_HOME` override) should see KHA and 403 N 18th
  appear in the `/#/leagues` chooser alongside Fantasy Gamers.

Source files in the real AppData install were left completely untouched
(read-only inspection + `cp` copy-out only, never written to).

### Remaining gaps

1. **Dynasty Sleeper league — genuinely absent everywhere checked.** Not
   recoverable from any local data; would require either (a) the owner
   supplying a real Sleeper dynasty league ID for a future cycle to import
   from live Sleeper, or (b) the owner confirming Dynasty's governed-asset-
   board architecture is intentionally not meant to track a specific league
   roster (per its existing design, it isn't a per-league tool at all). Do
   not build a fake import path or fabricate a profile to close this gap.
2. **Real AppData install's `active_profile.json` currently points at
   "Tester,"** not a real league. Not fixed here (out of scope — this worker
   never writes into the real AppData install per the hard boundary). Flagged
   for the owner / next worker who touches the real app directly.
3. This worker's recovery only fixes **this worktree's** fallback store. If a
   future worker starts the Redraft dev server pair with `NWR_REDRAFT_HOME`
   pointed at something else (or via the real Tauri app itself, which reads
   its own AppData state directly and already has KHA + 403 N 18th — this was
   never actually missing there), the fix here is a no-op / not needed. This
   recovery specifically targets the smoke-script code path the owner's
   browser observation matches.
4. `f92cff21…` (KHA TEST) and `16d2e550…` (KHA PRACTICE) test variants remain
   in the real AppData install, untouched, as the owner's/prior workers'
   scratch artifacts — not evaluated further, not this worker's call to prune.

### Code changes

None. `NWR_REDRAFT_HOME` / `redraft_store_root()` behave exactly as designed;
no bug was found in the resolution logic itself. This pass was data-location
investigation + safe additive recovery only.

### Final HEAD

Unchanged — `2477b901b167085c3494664ed6f06210a10f93d8` (no commits made; all
recovered data lives under the gitignored `local_exports/` path, confirmed via
the same `git check-ignore` pattern the prior cycle's Worker 8 used, and
correctly does not appear in `git status`).

### Open issues for next worker

1. Start the Redraft (127.0.0.1:1422/18742) and Dynasty (127.0.0.1:1421/18741)
   dev-server pair the same way the prior cycle did (this worker deliberately
   did not) and verify LIVE in the browser at `http://127.0.0.1:1422/#/leagues`
   that KHA High Stakes and 403 N 18th and friends now both appear alongside
   Fantasy Gamers, with correct pick counts (157 / 118) and no console errors.
2. Confirm the recovered KHA/403 N 18th profiles render correctly across
   Draft Room, Cheat Sheets, and Weekly Home surfaces once live — this worker
   only verified parse-level/service-level correctness (`list_profiles()`),
   not full UI rendering (explicitly out of scope for this pass).
3. The dynasty-Sleeper-league gap (see Remaining Gaps #1) needs an owner
   decision, not more searching — flag it to the owner rather than re-
   investigating.
4. Consider (owner's call, not this worker's) whether to fix the real
   AppData install's `active_profile.json` (currently "Tester") back to a
   real league — this worker deliberately did not touch the real AppData
   install per the hard boundary.
5. `local_exports/redraft_v1.backup-20260917T224444Z/` in this worktree is
   the pre-recovery snapshot from this pass — safe to leave in place
   (gitignored) or prune once the recovery is confirmed good live; not
   deleted automatically by this worker.

## Worker 2 — servers restarted + real lifecycle-derivation fix (2026-09-17)

### Part 1 — servers restarted, chooser confirmed live

Both dev-server pairs killed by the owner's PC restart were brought back up
the same way as the prior cycle (`desktop/scripts/nwr_release_gate_smoke.ps1
-KeepRunning`, `NWR_REDRAFT_HOME` deliberately left unset so it resolves to
this worktree's `local_exports/redraft_v1` per Worker 1's finding):

- **Redraft**: backend `http://127.0.0.1:18742` (PID 22716 as of this
  writing), frontend `http://127.0.0.1:1422` (PID 15588). Confirmed HTTP 200
  on both directly (`curl`), plus a full smoke pass (cargo check, vite
  build, real read-only Sleeper before/after byte-diff — 0 writes, every
  surface endpoint 200).
- **Dynasty**: backend `http://127.0.0.1:18741` (PID 12852), frontend
  `http://127.0.0.1:1421` (PID 5288). Bootstrap 200/200 cold+warm, own
  isolated data intact (no per-league profile store, as already established
  by Worker 1 — unaffected by anything this worker did).

**LIVE (Chrome MCP) verification of the chooser** at
`http://127.0.0.1:1422/#/leagues`: all 5 profiles render with real content —
"2026 KHA High Stakes League" (16-Team PPR, 1QB), "403 N 18th and friends"
(8-Team PPR, 1QB), "Fantasy Gamers" (Sleeper, 10-Team PPR, Active), plus the
2 throwaway local profiles. Zero console errors captured across the whole
session (chooser load, 2 league activations, a hard page reload).

### Part 2 — lifecycle-derivation bug: real, and NOT fixed by data recovery alone

**Tested live first, as directed.** Activated KHA and 403 N 18th via the
real `/api/v1/redraft/profiles/{id}/activate` + `/api/v1/redraft/league-
workspace-context` endpoints (dev token, same as the smoke script uses).
Recovering the real draft-board data (Worker 1) *did* clear the very first
`PRE_DRAFT` branch (`draft_configured`/`drafted_count` are no longer
0/false) — but both leagues then resolved to **`LIVE_DRAFT`**, not
`IN_SEASON`. Still wrong, just a different wrong state. A code fix was
required, exactly as the owner suspected.

**Root cause 1 (ESPN leagues, the directive's explicit target).**
`desktop_facade.py`'s `redraft_league_workspace_context` computes
`total_draft_picks = team_count * draft.rounds` and requires
`drafted_count >= total_draft_picks` for `IN_SEASON`. Inspected the real
recovered draft-board JSON directly:
- KHA: 157 real picks recorded, but `team_count(16) * rounds(12) = 192`.
  Position breakdown of the 157 real picks: **zero K, zero DST** picks
  anywhere (`{'RB': 45, 'WR': 65, 'TE': 25, 'QB': 22}`) — K/DST were never
  part of this league's live pick stream at all (consistent with the
  already-known `practical_mode` K/DST-outside-the-draft pattern).
- 403 N 18th: 118 real picks recorded vs `8 * 16 = 128` configured; K/DST
  *do* appear here (6 of 8 teams each) but the draft still ends 10 picks
  short of the full configured total.
- Neither profile has any live ESPN re-sync path in this codebase at all
  (confirmed by search: no ESPN service exists anywhere in `src/services`,
  and `provider_league_id` is `null` for both) — these are one-time,
  by-hand-recorded historical imports. Once a board like this goes quiet, no
  further picks are ever coming, so an exact-count check can get stuck in
  `LIVE_DRAFT` forever.

**Root cause 2 (found beyond the explicit ask, fixed because it's the same
root pattern and nearly free — data already fetched).** Activated Fantasy
Gamers (real Sleeper league, genuinely mid-season: week 2, real standings,
real matchups, real playoff bracket) via the same endpoint and found it
**also** resolves `PRE_DRAFT`, with basis "No draft board activity has been
recorded for this league yet." This is a real, live-reproduced instance of
the owner's own general diagnosis ("absent history produces PRE_DRAFT") —
Fantasy Gamers was drafted on Sleeper's own platform, never inside this
app's Draft Room, so it has zero local draft-board rows and always will.
`desktop_facade.py` already fetches Sleeper's real, provider-native
`league.status` (`pre_draft`/`drafting`/`in_season`/`complete`) for the
playoff-context read (`sleeper_league_context_service.build_playoff_context`
-> `leagueStatus`) — it was just never plumbed into lifecycle resolution.

### Fix

**Backend** (`src/services/league_lifecycle_service.py`): `resolve_league_
lifecycle` gained two additive, keyword-only, default-off parameters (every
existing call site and test is byte-for-byte unaffected):
- `provider_status: str | None` — when recognized
  (`pre_draft`/`drafting`/`in_season`/`complete`), takes priority over local
  draft-board signals immediately after the `archived` check.
- `live_sync_capable: bool` + `draft_last_activity_utc: str | None` (+
  injectable `now_utc` for tests) — when `live_sync_capable=False` (no live
  re-sync path for this provider) and the draft board has gone quiet for
  `STALE_DRAFT_THRESHOLD` (24h — no realistic single real draft session
  runs anywhere near that long) with at least one real pick recorded,
  resolves `IN_SEASON` instead of staying stuck in `LIVE_DRAFT`.

Neither fix manufactures picks or hardcodes any league to `IN_SEASON`: a
genuinely `PRE_DRAFT` league (no provider status, zero local picks) still
resolves `PRE_DRAFT`; a genuinely fresh/active `LIVE_DRAFT` (recent
activity, or a live-syncable provider) still resolves `LIVE_DRAFT` — see
the new "recent activity stays LIVE_DRAFT" and "live-syncable stays
unaffected by staleness" tests.

Wired through `src/services/league_workspace_context_service.py`
(`build_league_workspace_context` derives `provider_status` from the
already-passed `playoff` mapping's `leagueStatus` field — zero new I/O) and
`src/application/desktop_facade.py` (`redraft_league_workspace_context` now
captures `draft_board_payload["updatedAtUtc"]` into `draft_last_activity_
utc` and passes it through; `live_sync_capable` is computed as
`profile.provider == "sleeper" and bool(profile.provider_league_id)`, the
exact same condition the function already uses to decide whether to attempt
live Sleeper reads at all).

**Frontend** (`desktop/apps/redraft/src/league-context.ts`):
`resolveLeagueLifecycle(profile, draftBoard)` — the function RedraftApp.tsx
/ in-season.tsx / shell-identity.tsx / leagues.tsx actually use for
routing/labels/nav (NOT the backend `/league-workspace-context` endpoint,
which only `attention-center.ts` calls) — gained the SAME staleness
fallback using data already present in the bootstrap payload
(`draftBoard.updatedAtUtc`, `profile.provider`/`providerLeagueId`, no new
network call). This fixes the ESPN half (KHA, 403 N 18th) live, in the
actual rendered app. Added an optional `now: Date` parameter (default
`new Date()`) purely for test injectability.

**Known, disclosed, NOT fixed in this pass:** the frontend's local
heuristic has no access to Sleeper's live `league.status` (bootstrap
deliberately makes zero live network calls, by design, for latency —
confirmed via the smoke script's own cold/warm bootstrap timing, ~280ms vs.
~900ms+ for `league-workspace-context`, which does several live Sleeper
reads). So Fantasy Gamers' sidebar in the actual running app still shows
"Pre-Draft" today, even though the BACKEND `/league-workspace-context`
endpoint (and therefore Attention Center, which consumes it) now correctly
reports `IN_SEASON` for it. Closing this fully would mean either accepting
a new live network call on the league-open/nav-render hot path, or caching
a confirmed lifecycle value from a prior `league-workspace-context` call —
both are real architecture decisions bigger than this bounded lifecycle-
derivation fix; flagging for the next worker/owner rather than guessing.

### Live verification (Chrome MCP, not inferred)

Restarted the Redraft backend process to load the new code (killed old PID,
same smoke-script pattern), re-ran the full smoke pass (all green), then in
the real rendered browser:
- Activated **KHA**: sidebar badge changed from (pre-fix) `PRE-DRAFT` to
  **`IN SEASON`**; landed on **Weekly Home**, not Draft Room; nav
  reordered to the in-season set (Home/Lineup/Improve Team/Trades/Players/
  Cheat Sheet/League/Attention Center — Draft Room item gone, as designed).
- Activated **403 N 18th and friends**: same result, **`IN SEASON`**,
  landed on Weekly Home.
- Hard page reload (F5) on 403 N 18th's Weekly Home: lifecycle stayed
  `IN SEASON`, stayed on Weekly Home — refresh behavior is stable, not a
  one-time fluke of the activation call.
- Zero console errors across the whole session.
- The top-bar "DRAFT BOARD READY" chip is a SEPARATE, pre-existing,
  lifecycle-independent indicator (`data.status.ready`, the governed
  projection-snapshot pipeline's own readiness, shown identically for every
  league) — inspected `RedraftApp.tsx` to confirm this before assuming it
  was part of the same bug; it is unrelated and intentionally left alone.

### Tests added

`tests/test_league_lifecycle_service.py`: 11 new cases (provider_status ->
each of the 4 mapped lifecycles, an unrecognized value falling back safely,
the real KHA/403-N-18th-shaped stale-partial-draft cases, a "recently
active stays LIVE_DRAFT" case, a "live-syncable provider is NOT affected by
staleness" case, and the 24h threshold boundary both sides). All pass (19/19
in this file).

`tests/test_league_workspace_context_service.py`: 2 new cases proving the
facade-level wiring end-to-end (real Sleeper `playoff.leagueStatus` ->
`IN_SEASON`; a stale ESPN-shaped partial draft -> `IN_SEASON`). All pass
(10/10 in this file).

`desktop/apps/redraft/src/league-context.test.ts`: 4 new cases mirroring
the same real KHA/403-N-18th shapes, plus the "recent activity stays
LIVE_DRAFT" and "Sleeper is unaffected by staleness" cases, for the
frontend heuristic. All pass (26/26 in this file). `npm run typecheck`
(desktop workspace) clean.

Full command reference: `python -m pytest tests/test_league_lifecycle_
service.py tests/test_league_workspace_context_service.py tests/test_league_
workspace_context_sleeper_p1_1.py tests/test_desktop_facade_architecture_
wiring.py` -> 42/42 passed. `cd desktop && npx vitest run apps/redraft/src/
league-context.test.ts` -> 26/26 passed. `npm run typecheck` -> clean.

### Final HEAD

One commit on top of `7c80c8a5` — see `git log -1` in this worktree.

### Files changed

- `src/services/league_lifecycle_service.py`
- `src/services/league_workspace_context_service.py`
- `src/application/desktop_facade.py`
- `desktop/apps/redraft/src/league-context.ts`
- `tests/test_league_lifecycle_service.py`
- `tests/test_league_workspace_context_service.py`
- `desktop/apps/redraft/src/league-context.test.ts`
- `docs/codex/dogfood_v1/LEDGER.md` (this entry)

### Open issues for next worker

1. **Part 3, as originally scoped**: league isolation race testing —
   profile create/import/duplicate vs. Attention Center hypothesis. Not
   started by this worker.
2. Frontend Sleeper-live-status gap (see "Known, disclosed, NOT fixed"
   above): Fantasy Gamers' sidebar still shows `Pre-Draft` in the real
   rendered app despite the backend now being correct. A real, bounded,
   separate follow-up: either accept a live network call on the hot path,
   or thread a confirmed `league-workspace-context` lifecycle value through
   `leagues.tsx`'s `activate()` / `RedraftApp.tsx`'s initial load and prefer
   it via the existing (currently unused in the hot path)
   `confirmedLifecycle` parameter on `resolveLeagueHomeSubpath`.
3. Dev servers (all 4) are currently running — Redraft backend PID 22716 /
   frontend PID 15588 (port 18742 / 1422), Dynasty backend PID 12852 /
   frontend PID 5288 (port 18741 / 1421). Leave running for the next worker
   unless a further backend code change requires another restart (same
   pattern as this pass: kill the backend PID on the target port, rerun
   `nwr_release_gate_smoke.ps1 -KeepRunning`).
4. Untracked smoke-run log files (`*_smoke_std{out,err}*.log`) were left in
   the worktree root by this pass (some still open/busy from the running
   processes) — harmless scratch output, not part of the repo, safe to
   delete once the servers are stopped.

## Worker 3 — Part 3: league isolation race testing, real repro found + fixed (2026-09-17)

### Step 1 — code inspection

Grepped every direct `client.activateRedraftProfile`/`createRedraftProfile`/
`duplicateRedraftProfile`/`importSleeperRedraftProfile` call site in
`desktop/apps/redraft/src/*.tsx`:

**Wrapped in `serializeActiveProfileCall` (pre-existing, from the prior
cycle):** `RedraftApp.tsx`'s route gate, `shell-identity.tsx`'s header
quick-switcher, `leagues.tsx`'s Manage Leagues switcher, and — already fixed,
apparently by a prior pass not separately logged — `profile.tsx`'s own
`activate()`.

**NOT wrapped (confirmed live-vulnerable):** `profile.tsx`'s `create()`
(→ `client.createRedraftProfile`), `duplicate()` (→
`client.duplicateRedraftProfile`), and `importSleeper()` (→
`client.importSleeperRedraftProfile`) — each called its contract method
directly. A **second, previously undocumented instance of the same class**
was also found: `league.tsx`'s unified League-surface Settings tab
(`LeagueSettingsTab`) has its **own separate** `duplicate()` that also called
`client.duplicateRedraftProfile` directly, unwrapped — a second reimplementation
of the same action, not previously flagged in either this cycle's or the prior
cycle's ledger.

**Confirmed server-side that all four targets change the shared active-profile
pointer, not just return data:**
- `src/desktop_api/server.py`'s `POST /api/v1/redraft/profiles` handler calls
  `facade.create_redraft_profile(...)` then, in the SAME request, explicitly
  calls `facade.activate_redraft_profile(profile_id)` before returning
  bootstrap (line ~579).
- `desktop_facade.py`'s `duplicate_redraft_profile` (line 5373) and
  `import_sleeper_redraft_profile` (line 2281) each call `set_active_profile`
  internally.
- By contrast, `resync_sleeper_redraft_profile`/`redraft_sleeper_resync`
  (`profile.tsx`'s `refreshSleeper` / `league.tsx`'s resync action) never
  calls `set_active_profile` — it only refreshes the already-active profile's
  stored data in place. Confirmed correctly OUT of scope; left unwrapped.
  `updateRedraftProfile` (save) and `startPracticalMock` were checked the
  same way — neither touches the pointer either, correctly left alone.

**Sweep vulnerability window — INSPECTED CODE:** `attention-center.ts`'s
`runAttentionCenterAggregationUnserialized` iterates every saved profile
sequentially (`activate(id)` then 5 reads), then in an unconditional
`finally` restores whichever profile was active when the sweep began. The
sweep is NOT a periodic background poll (no `setInterval` anywhere in the
codebase) — it runs once automatically on `AttentionCenterPage` mount
(`useEffect` at line 175) and again on the manual "Refresh" button. On this
worktree's real local dataset (6 saved profiles as of this pass) a full sweep
takes **~2.0–5.6s wall-clock** (observed live, see Step 2/3), i.e. the
real window during which an unwrapped create/duplicate/import racing the
sweep's own activate/restore sequence can interleave.

### Step 2 — create/duplicate/import race: REPRODUCED LIVE

Reproduced against the real running Redraft backend (port 18742, real KHA/
403-N-18th/Fantasy-Gamers/2 throwaway profiles all live) via a Chrome MCP
console session (directive approach (b): controlled artificial delay to make
the interleaving deterministic rather than a rare accident):

1. Activated KHA (`fb1c4976...`) as a clean starting point.
2. Fired a **simulated sweep**: sequential raw `POST .../activate` for all 5
   real profile IDs with a 400ms delay between steps, ending with the exact
   same unconditional restore-to-original the real sweep performs.
3. ~900ms into that sequence (mid-sweep), fired a **raw, unwrapped**
   `POST /api/v1/redraft/profiles` (create, preset `10_TEAM_1QB_STANDARD`,
   name "RACE TEST TEMP (Worker3)", provider `local` — disposable, no real
   provider write) — byte-for-byte the same unwrapped call `profile.tsx`'s
   pre-fix `create()` made.
4. Read the backend's own `/api/v1/bootstrap` after both settled.

**Result (ACTUAL TEST RESULT):**
- Immediately after create resolved: `activeProfileId` == the new profile
  (`117f05c5...`) — the create's own server-side activation worked correctly
  in isolation.
- After the simulated sweep's own trailing restore fired (queued/timed to
  land after create): `activeProfileId` reverted to `fb1c4976...` (KHA) —
  **the just-created profile silently lost active status**, clobbered by the
  sweep's unconditional restore, even though the real UI message says
  "Profile created and activated."
- Confirmed via a hard page reload (F5) in the real rendered app: KHA showed
  as ACTIVE, and "RACE TEST TEMP (Worker3)" appeared correctly in the
  chooser as a real, separately-saved (but not active) profile — matching
  the corrupted-pointer theory exactly, not a fluke of the console script.

This is a genuine, reproducible bug matching the directive's hypothesis
exactly, not a theoretical code-reading conclusion. Test profile deleted
after verification (`local_exports/redraft_v1/profiles/117f05c5....json`
removed directly; `active_profile.json` already pointed at KHA, so no
dangling reference).

### Step 3 — broader isolation testing (real KHA/403N18th/Fantasy Gamers, Chrome MCP)

All done against the real running app, spot-checking team counts (KHA=16,
403N18th=8, Fantasy Gamers=10) as the distinguishing giveaway per the
directive:

1. **Sweep-timed switch (real UI, real concurrent sweep):** Clicked
   "Refresh" (starts a real sweep) then, in the same batch with no
   artificial delay, immediately opened the header "Switch league" dropdown
   and selected KHA — a genuinely concurrent real request against the
   already-wrapped quick-switcher call site. Result: **PASS** — landed
   correctly on KHA (16-Team PPR, IN SEASON), no corruption. This is the
   direct positive control showing the wrapped mechanism holds under real
   concurrency, contrasting with Step 2's unwrapped failure.
2. **Back/forward:** KHA Weekly Home → switched to 403 N 18th Weekly Home
   (URL correctly carried the profile ID, page text confirmed "8-TEAM PPR ·
   1QB · 403 N 18th and friends") → browser back → landed on
   `/#/attention-center` (an intermediate route in this session's history,
   not a dedicated "previous league" state — expected HashRouter behavior,
   not a bug) → its on-mount sweep correctly re-confirmed 403 N 18th as
   still active (8-Team PPR) once it finished. **PASS.**
3. **Refresh mid-switch:** Clicked "Switch league" → Fantasy Gamers, then
   immediately F5 before the activate call could have resolved. After
   reload: correctly landed on Fantasy Gamers (10-Team PPR) with no
   cross-league data bleed. It DID show as PRE-DRAFT rather than the
   backend's true IN_SEASON status — this is the already-known, already-
   disclosed frontend Sleeper-live-status gap from Worker 2's entry, not a
   new bug, and not a data-isolation failure (team count / identity were
   still correct). **PASS for isolation; known gap re-confirmed, not
   newly caused by this test.**
4. **Slow/in-flight-request switch:** Patched `window.fetch` to delay any
   `/activate` request by 2.5s, then triggered a switch to KHA. While
   "Switching…" was visibly showing in the sidebar (confirmed no stale/wrong
   league data was displayed during the in-flight window), attempted a
   second overlapping switch — by the time the second click fired, the
   first request had already resolved (the delay elapsed faster than the
   click sequence), so this specific run did not produce a genuine
   overlapping pair. Given Step 3.1 already demonstrates the wrapped queue
   correctly serializes two genuinely concurrent real requests, this is
   treated as corroborating, not a gap requiring a re-run.

### Step 4 — fixes

**REPRODUCED-LIVE-BUG fix:** `desktop/apps/redraft/src/profile.tsx` —
`create()`, `duplicate()`, and `importSleeper()` now each wrap their
contract call in `serializeActiveProfileCall(...)`, the exact existing
pattern already used by this same file's `activate()` and by
`shell-identity.tsx`/`leagues.tsx`/`RedraftApp.tsx`. No new mechanism
invented.

**PREVENTIVE-CODE-PARITY fix:** `desktop/apps/redraft/src/league.tsx` —
`LeagueSettingsTab`'s own separate `duplicate()` (the unified League
surface's Settings tab, reusing `ProfileEditor`) was found structurally
identical (same unwrapped `client.duplicateRedraftProfile` call, same
active-profile-changing backend endpoint) during Step 1's inspection, but
was not independently live-race-tested from this specific surface in the
time available. Wrapped through the same `serializeActiveProfileCall` for
code-pattern parity with `profile.tsx`'s now-fixed `duplicate()`, since it
is literally the same contract call from a second call site.

Both fixes reuse the established `attention-center.ts` queue mechanism only
— no new pattern, no change to `serializeActiveProfileCall` itself, no
change to any governed valuation/scoring/roster-legality/lifecycle code.

### Tests added

`desktop/apps/redraft/src/attention-center.test.ts`: one new case in the
existing `describe("runAttentionCenterAggregation -- state-leakage
regressions")` block — "never interleaves a sweep with a create/duplicate/
import-style call that also activates its result server-side" — extends the
existing pattern (the prior cycle's "sweep vs. unrelated direct
activateRedraftProfile call" test) using `client.activateRedraftProfile` as
the faithful stand-in for create/duplicate/import's own server-side
activation (structurally indistinguishable from the queue's point of view;
documented as such in the test's own comment). Asserts the sweep's full
`A, B, C, A` sequence stays contiguous before the create-like call's `NEW`
activation, and that the final backend pointer lands on `NEW`, not silently
reverted.

**Results:** `npx vitest run apps/redraft/src/attention-center.test.ts` →
30/30 passed. Full `npx vitest run apps/redraft` → 430/430 passed (19 test
files, no regressions). `npm run typecheck` (desktop workspace) → clean.

### Cleanup

The disposable "RACE TEST TEMP (Worker3)" local test profile created during
Step 2 was deleted directly from
`local_exports/redraft_v1/profiles/117f05c5f42c44aeb6267067fe2856c0.json`
after verification (no API delete endpoint exists for profiles). Confirmed
gone from the real rendered chooser after a hard reload. The pre-existing 2
throwaway profiles ("10-team 1QB Standard", "Isolation Check Local") were
left untouched per the directive. No real Sleeper/ESPN writes were made at
any point — the create test used `provider: "local"` only.

An unrelated file, `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/
frontend_bench_results.json`, was regenerated as a side effect of running
the full `apps/redraft` vitest suite (a live timing benchmark test writes to
it); reverted via `git checkout --` before committing since it isn't part of
this pass's actual change.

### Final HEAD

One commit on top of `11837b62` — see `git log -1` in this worktree.

### Files changed

- `desktop/apps/redraft/src/profile.tsx`
- `desktop/apps/redraft/src/league.tsx`
- `desktop/apps/redraft/src/attention-center.test.ts`
- `docs/codex/dogfood_v1/LEDGER.md` (this entry)

### Running processes status

All 4 confirmed healthy and unchanged by this pass (frontend-only fix, no
backend restart needed — verified live via a hard reload with zero console
errors after the fix landed): Redraft backend PID 20368 (18742) / frontend
PID 17016 (1422); Dynasty backend PID 12852 (18741) / frontend PID 5288
(1421). (Note: the Redraft PIDs differ from the ones Worker 2 recorded —
20368/17016 vs. 22716/15588 — same ports, both healthy; something restarted
them between that entry being written and this pass starting, not something
this worker did.)

### Open issues for next worker

1. **Part 4 is next**: dogfood every tool through meaningful interactions
   across both apps, using the now-available real KHA/403N18th leagues in
   addition to Fantasy Gamers.
2. Frontend Sleeper-live-status gap (Worker 2's entry, re-confirmed still
   present in Step 3.3 above): Fantasy Gamers' sidebar can still show
   Pre-Draft in the real rendered app. Not this worker's fix (out of this
   pass's scope), still open.
3. Step 3.4 (slow in-flight-request switch) did not produce a genuinely
   overlapping pair of real UI-triggered requests in the time available
   (the artificial 2.5s delay had already elapsed before the second click
   fired) — Step 3.1's real concurrent-sweep-vs-switch test already
   corroborates the same mechanism, but a future worker wanting a second,
   independent confirmation could retry with a longer artificial delay or a
   scripted double-click.
4. Untracked smoke-run log files from Worker 2 (`*_smoke_std{out,err}*.log`)
   are still present in the worktree root, still harmless scratch output.

## Worker 4 — Part 4 (first half): Weekly Home, Start/Sit, Improve Team, Trades, Players, League tabs, Attention Center (2026-09-17)

### Scope and method

Owner's directive: exercise real meaningful interactions (not page loads) across
Weekly Home, Start/Sit, every Improve Team tab, Trades, Players/Compare/Market,
League tabs, and Attention Center, using the now-available real leagues
(Fantasy Gamers = Sleeper 10-team, KHA = ESPN 16-team, 403 N 18th = ESPN
8-team). History/Manage Leagues/Data Health/Draft Room/Cheat Sheet/Dynasty are
explicitly left for Worker 5, not touched here except incidentally (Draft Room
was visited once, unavoidably, because the league chooser's "Open workspace"
routes Fantasy Gamers there — see Bug/Gap note below).

Processes at start: all 4 confirmed already healthy via `netstat` — same PIDs
Worker 3 left running (Redraft backend 20368/18742, frontend 17016/1422;
Dynasty backend 12852/18741, frontend 5288/1421). No restart needed. Confirmed
unchanged (same PIDs) at end of this pass too.

All testing done live via Chrome MCP against the real running Redraft
frontend/backend. No Sleeper writes were made anywhere — every action taken
was a read (search, filter, sort, compare, trade *analysis*, attention-center
sweep, cross-league ownership search) or a local/read-only external fetch
(Fantasy Football Calculator ADP refresh, a public consensus-ADP read, not a
Sleeper endpoint). No lineup was submitted, no waiver claimed, no trade
proposed/accepted, matching the app's own on-page disclosures ("NWR never
writes a lineup to Sleeper" / "NWR never proposes or accepts a trade on
Sleeper"). The frontend tab's own network log showed zero `sleeper` requests
(Sleeper reads happen server-side in the backend, not from the browser tab, so
this is corroborating rather than exhaustive proof, consistent with the app's
architecture).

### 1. Weekly Home — LIVE OBSERVATION

- **Fantasy Gamers**: PASS. Navigated directly to
  `/#/league/941b99ade350410391b1b67c0890af79/home` (see Bug/Gap note — the
  chooser's own "Open workspace" link does not land here for this league).
  Real content: "Fantasy Gamers · Week 2", real Sleeper standings table (10
  real team names, W/L/PF), real matchup card (opponent "shittin and tuten",
  score 0.0-0.0, record 1-0 #1 of 10), real waiver suggestion (Tyrone Tracy,
  marginal utility 9.7, with full v2-challenger reasoning text). Not
  empty/placeholder.
- **KHA / 403 N 18th**: LIMITED, real reason — both show "Sleeper league
  required — Weekly in-season tools (Start/Sit, Waivers, Trade, streamers)
  require an active Sleeper-imported league. Choose or import one." This is a
  genuine, correctly-labeled, non-fabricated empty state (both are ESPN,
  one-time-imported, no live Sleeper roster source), not a bug.

### 2. Start/Sit — ACTUAL TEST RESULT (real edit exercised)

- **Fantasy Gamers**: PASS. Real recommendation shown ("Start Trevor Lawrence
  over Caleb Williams — LOW CONFIDENCE — CLOSE CALL, +0.5 projected points").
  Changed the NFL WEEK input from 1 to 2 (a real scenario edit): the
  recommendation set changed to a different, real player/margin ("Start
  Michael Pittman over Travis Etienne, +0.7"), confirming the page reacts to
  the edit rather than showing static content.
- **KHA (the owner's genuine unavailable-data edge case)**: LIMITED, real and
  correctly-behaved — "Sleeper league required — Start/Sit needs a live
  Sleeper roster and the real weekly-projection source." No crash, no
  fabricated lineup, no silent fallback to stale/wrong data. This is exactly
  the owner's framed edge case (post-draft ESPN league whose real-world 2026
  games this app has no live weekly-projection/roster path for): the app
  correctly refuses rather than guessing.

### 3. Improve Team — every tab — ACTUAL TEST RESULT (real edits exercised)

All 5 tabs tested for Fantasy Gamers with real edits; Targets spot-checked
against KHA for the unavailable-data case.

- **Targets**: PASS. Real ranked list (25 targets). Toggled MODE
  REST_OF_SEASON → THIS_WEEK: content changed to include a real "THIS WEEK"
  starter-impact line ("Would not become a starter this week..."). Changed
  POSITION filter ALL → RB: top target re-ranked to a real RB-only
  recommendation (Tyrone Tracy). Both edits produced correctly different,
  real content.
- **Add/Drop**: PASS. Position filter (RB) correctly carried over from
  Targets tab (real cross-tab state). Toggled VIEW "Available to add" →
  "Consider dropping": real weakest-roster-player ranking appeared (Kenny
  Gainwell lowest, with real marginal-utility reasoning), plus a real,
  honest K/DST disclosure ("K/DST are not part of the governed ranking").
- **FAAB**: PASS. Real bid recommendation with real dollar range and percentile
  language (Dalton Schultz, $24-39, 83rd percentile of the real free-agent
  pool).
- **Streamers**: PASS, exercised the external-API edit path. Default state is
  empty ("No streamer read yet — Refresh K/DST ECR above"), correctly not
  fabricating data before the user asks. Clicked "Refresh K/DST ECR (This
  Week)": real FantasyPros consensus data returned (Jacksonville Jaguars #1
  DST for Week 1, Chargers #2 alternative).
- **All Free Agents**: PASS. Real 727-row unrostered-player pool with real
  ranks/points/replacement-value columns.
- **KHA spot-check (Targets tab)**: LIMITED, real and correctly-labeled —
  "Sleeper league required — Improve Team needs a live Sleeper roster and the
  governed NWR ranking." Same honest-refusal pattern as Start/Sit.

### 4. Trades — ACTUAL TEST RESULT (real player selection + real ownership check)

- **Fantasy Gamers, Analyze**: PASS. Built a real trade (I give: Kenny
  Gainwell from my own roster; I receive: searched "James Cook", which
  correctly resolved to "James Cook (RB) — Show Me Your TDs" showing real
  opponent ownership in the search dropdown itself before selection).
  Clicked Analyze: real before/after impact returned (starting lineup value
  1033.6 -> 1081.9, net marginal utility +21.8, bench/position-effect
  breakdown, an honest disclosed gap: "Championship Equity is not evaluated —
  this repo has no live standings store").
- **Fantasy Gamers, Find Trades**: PASS. Real auto-generated proposal (1-for-2
  vs. Bill's Sleepers: send Marvin Harrison Jr. for Jayden Reed + TreVeyon
  Henderson) with real "why it helps you" / "why it may fit them" reasoning
  and the same before/after structure.
- **KHA**: LIMITED, real and correctly-labeled — "Sleeper league required —
  Trades needs your live Sleeper roster and every live opponent roster."
- Incidentally confirmed real per-league ownership data via the Trades page's
  "Browse opponent rosters" link (routes to the League > Teams tab): all 10
  Fantasy Gamers teams' real rosters (names, starters/bench, real players)
  rendered correctly, and James Cook's roster location there
  (Show Me Your TDs) matched the Trades search result exactly — cross-surface
  data-consistency check, passed.

### 5. Players (Rankings/Compare/Market) — ACTUAL TEST RESULT (real search, filters, comparison)

- **Rankings**: PASS. Real 564-player board. Typed "Kittle" into search:
  correctly filtered to "1 of 1 matches" (George Kittle, #91, TE13, real
  proj/VOR/evidence columns).
- **Compare**: PASS, full end-to-end exercise. Default comparison (#1
  McCaffrey vs #2 Nacua) showed a real "NWR Redraft Lean" verdict. Changed
  Player B to George Kittle (#91 TE13): both player cards and the lean
  verdict recalculated correctly. Toggled MODE Rest of Season -> Roster Fit:
  content changed to real roster-context numbers (Kittle's starter gap
  flipped to -16.2 vs. McCaffrey's +224.7, reflecting each player's real fit
  on this specific roster).
- **Market**: PASS, real external-data edit exercised (see Bugs/Findings —
  this doubled as the persistence check). Initial state was honestly empty
  ("No active ADP snapshot — UNAVAILABLE"). Clicked "Refresh FFC ADP": a real
  live read from Fantasy Football Calculator returned (71/78 players matched,
  source dated 2026-09-10 to 2026-09-17, FRESH), and the top-bar "data
  issues" counter correctly dropped from 3 to 2 as a direct, real side
  effect.
- **KHA cross-check**: PASS. Rankings board correctly shows a different
  "Available" filtered count (413 of 564, vs. Fantasy Gamers' own filtered
  set) reflecting KHA's own real, different set of drafted players — real
  per-league data isolation confirmed, not a shared/bleeding board.

### 6. League tabs (Overview/My Roster/Teams/Scoring/Settings/Sync) — LIVE OBSERVATION, 3-league cross-check

Directive's suggested cross-check (16 vs 10 vs 8 teams) run directly:

- **Fantasy Gamers Overview**: 10-Team PPR, Platform Sleeper, 15 rostered
  players, Current week 2, Sync health LIVE.
- **KHA Overview**: 16-Team PPR, Platform Local, "My roster: Not tracked for
  a Local/ESPN profile", Current week "Not available", Sync health "NOT
  APPLICABLE".
- **403 N 18th Overview**: 8-Team PPR, same Local/ESPN-profile disclosures.
- All three team counts (10/16/8) rendered correctly and distinctly — real
  cross-league differentiation confirmed, not a shared/stale value.
- **403 N 18th Teams tab**: LIMITED, real and correctly-labeled — "Sleeper
  league required — ESPN and local profiles have no live opponent-roster
  source."
- **403 N 18th My Roster tab**: a well-designed partial-availability state,
  worth calling out as a good pattern rather than a gap — it does NOT just
  say unavailable; it discloses "NWR's last known roster for this league is
  from draft results as of 2026-09-08T02:50:29+00:00; it does not reflect
  any waiver, trade, or free-agent move since" with a link to open Draft Room
  (My Team) for that last-known state. Honest, not fabricated, not a dead
  end.

### 7. Attention Center — ACTUAL TEST RESULT (real sweep + real cross-league search edit)

- Triggered a real sweep by navigating to `/#/attention-center` fresh (also
  the automatic on-mount sweep). Took ~10.1s wall-clock for all 5 saved
  profiles (10-team 1QB Standard, KHA, 403 N 18th, Fantasy Gamers, Isolation
  Check Local) — consistent with Worker 3's documented 2-5.6s-per-sweep
  finding, scaled for profile count.
- Real, non-fabricated issues surfaced per league: Fantasy Gamers correctly
  showed "2 rostered players could not be matched to an NWR identity" plus a
  real actionable note ("Jared Goff (#41 overall) is available as a free
  agent") alongside real week/record/rank/deadline data (2, 1-0, #1 of 10,
  "Playoffs start Week 15"); KHA/403N18th/local-test profiles correctly
  showed "MARKET ADP: UNAVAILABLE" (matching the real "no ADP snapshot"
  state observed directly on their own Market tabs — cross-surface
  consistency, not a fabricated Attention Center-only claim).
- **Real edit exercised**: typed "James Cook" into the cross-league ownership
  search. Real per-league results returned: AVAILABLE in the two local/test
  leagues, "ROSTERED BY YOU" in KHA, "ROSTERED BY AN OPPONENT" in 403 N 18th,
  and "ROSTERED BY AN OPPONENT — Show Me Your TDs" in Fantasy Gamers — the
  last of which matches the exact team identified independently via the
  Trades page and the League > Teams roster browse in section 4, a genuine
  cross-tool data-consistency confirmation, not a lucky coincidence.

### Bugs/Gaps found (not code bugs requiring a fix in this pass)

1. **Re-confirms Worker 2/3's already-documented, already-disclosed frontend
   Sleeper-live-status gap** (not new, not fixed here — out of this worker's
   scope per the open issue list): clicking Fantasy Gamers' "Open workspace"
   from the league chooser still lands on Draft Room (draft setup screen),
   not Weekly Home, even though the league is genuinely `IN_SEASON`
   (`leagues.tsx`'s `activate()` calls `resolveLeagueHomeSubpath` without a
   `confirmedLifecycle` argument, so it falls back to the local
   no-draft-board heuristic → `PRE_DRAFT` → `draft`). Worked around by
   navigating directly to `/#/league/{id}/home` and the other league-scoped
   routes for all testing in this pass, per Worker 2's documented follow-up
   (thread a confirmed lifecycle value through `leagues.tsx`'s `activate()`).
   Flagging again here only because it was directly re-observed live during
   this pass's Weekly Home testing, not because it's new.
2. No other genuine, reproducible bug was found in the 7 tool areas covered.
   Every "unavailable" state observed (Start/Sit, Improve Team, Trades,
   Teams, My Roster for the two ESPN leagues; Market ADP before the refresh)
   was honestly labeled with a real, specific reason and a real remediation
   path where one exists (e.g., "Open Draft Room (My Team)"), never a blank
   page, crash, or fabricated placeholder value. This is a genuinely clean
   result, not a gap in testing effort — see the exact edits/toggles
   exercised in each section above.

### Persistence check

Real edit: refreshed Fantasy Gamers' Market/ADP source from Fantasy Football
Calculator (Players > Market tab), which changed "Current source" from "No
active ADP snapshot" to "Fantasy Football Calculator ADP" and reduced the
top-bar data-issues count from 3 to 2. Navigated away (to `/#/leagues`), back
to the same league's Players page, then did a **hard reload (F5)** — the
strongest form of this check, not just an in-SPA navigation. After reload:
Market tab still showed "Fantasy Football Calculator ADP · FRESH · 71/78
matched", and the top-bar data-issues counter still read 2 (not reverted to
3). Confirmed real backend-persisted state, not a client-side-only cache.

### Tests added

None. No code was changed this pass — no genuine, reproducible bug was found
within this worker's scope that required a fix (see Bugs/Gaps above; the one
gap identified is Worker 2/3's already-tracked, already-scoped frontend
lifecycle-routing follow-up, not a new finding).

### Files changed

- `docs/codex/dogfood_v1/LEDGER.md` (this entry only)

### Running processes status at end

Unchanged from start — confirmed via `netstat` before handoff: Redraft
backend PID 20368 (18742) / frontend PID 17016 (1422); Dynasty backend PID
12852 (18741) / frontend PID 5288 (1421). No restart was needed or performed.

### Open issues for next worker

1. **Worker 5's assignment**: History, Manage Leagues, Data Health, Draft
   Room, Cheat Sheet, existing Dynasty tools — none of these were exercised
   in this pass (Draft Room was only visited incidentally via the
   still-open chooser-routing gap in item 1 below, not tested for its own
   sake).
2. The frontend Sleeper-live-status / chooser-routing gap (Worker 2/3,
   re-confirmed live again in this pass — see Bugs/Gaps #1) is still open
   and still not this pass's fix. It's a real, if minor, piece of friction
   worth closing at some point: the owner will land on Draft Room instead of
   Weekly Home every time they open Fantasy Gamers from the chooser.
3. Untracked smoke-run log files (`*_smoke_std{out,err}*.log`,
   `dynasty_smoke_std{out,err}.log`, `redraft_smoke_stderr2.log`,
   `redraft_smoke_stdout2.log`) remain in the worktree root from earlier
   workers — still harmless scratch output, not part of the repo, safe to
   delete once servers are stopped for good.
4. This pass did not exercise Improve Team's Add/Drop or FAAB tabs against
   KHA/403N18th specifically (only Targets was spot-checked there) — low
   risk given the identical "Sleeper league required" gating observed
   consistently across every in-season tool for those two leagues, but not
   independently re-verified tab-by-tab.

## Worker 5 — Part 4 (second half): History, Manage Leagues, Data Health, Draft Room, Cheat Sheet, Dynasty (2026-09-17)

### Scope and method

Owner's directive covered History, Manage Leagues, Data Health, Draft Room,
Cheat Sheet, and existing Dynasty tools — exercising edits, switches, empty/
error states, persistence after restart, and unavailable data. All testing
done live via Chrome MCP against the real running Redraft/Dynasty frontends
and backends. Processes at start: all 4 confirmed already healthy via
`Get-NetTCPConnection` — same PIDs Worker 4 left running (Redraft backend
20368/18742, frontend 17016/1422; Dynasty backend 12852/18741, frontend
5288/1421). No restart needed at start. **Important environment note for
Worker 6**: the Redraft frontend process (PID 17016) runs `vite preview`
(a static build server), NOT `vite dev` — frontend source edits require
`npm run build` in `desktop/apps/redraft` before they take effect; the
running process itself never needs restarting (it just re-serves the
rebuilt `dist/`). This worktree does not run Vite dev/HMR at all for the
frontend under this cycle's process-startup convention.

### 1. Decision History — ACTUAL TEST RESULT (real OwnerActionCell edits, 2)

- **Fantasy Gamers**: PASS. 155 real recorded events with real provenance
  (Sleeper league ID `1312983576827920384`, real dates/times through
  2026-09-17, real recommendation text for FAAB/Waiver/Trade/Start-Sit/K-DST
  streamer classes), plus real per-class outcome summaries (all correctly
  "NOT ENOUGH DATA YET" / "OUTCOME PENDING" — no fabricated calibration,
  matching the page's own disclosure that real season outcomes don't exist
  yet). **Re-verified the OwnerActionCell interaction the prior cycle's
  "stuck Recording..." bug affected**: clicked "Followed it" on the most
  recent FAAB-bid row — recorded instantly, no stuck/spinner state, survived
  a hard reload (F5) unchanged. Then clicked "Change" -> "Didn't act" on the
  same row — updated instantly, survived a second hard reload unchanged.
  Bug does NOT reproduce; the fix holds.
- **KHA / 403 N 18th**: LIMITED, real and correctly-labeled — both show "0
  recorded events" / "Nothing recorded yet," an honest empty state, not an
  error.
- **Worker 1's recovered `prospective_decision_log`/`nwr_pure_experiments`
  data for 403 N 18th does NOT surface here — confirmed why, not a bug.**
  INSPECTED CODE: `redraft_decision_trace_history` (desktop_facade.py:4835)
  reads `load_decision_traces(...)` from `decision_traces/<profile_id>.jsonl`
  (the in-season, owner-facing ledger). Only Fantasy Gamers has a file there
  (`local_exports/redraft_v1/decision_traces/941b99ade...jsonl`, 270KB).
  `prospective_decision_log_v1_service.py`'s own docstring confirms it is a
  **structurally separate, draft-time-only logging lane** ("NWR Big-Draft
  Readiness Overnight V1... every real practice or real draft pick... is
  potential prospective evidence for this program's NEXT piece of
  independent validation") feeding future research validation, not this
  owner-facing History page, which is explicitly in-season-scoped (its own
  DRAFT card says draft evaluation is deferred to
  `marginal_roster_utility_v2`, "never scored here"). Two genuinely
  different data lanes, correctly not conflated — not a gap, not a bug.

### 2. Manage Leagues — ACTUAL TEST RESULT (real switches + create/duplicate, hard boundary respected)

- **Real switching via this page's own "Open workspace" links (not the
  header quick-switcher)**, all 3 real leagues:
  - **KHA**: PASS. Landed on Weekly Home, IN SEASON badge, 16-Team PPR,
    correct honest "Sleeper league required" in-season-tools message.
  - **403 N 18th**: PASS. Landed on Weekly Home, IN SEASON badge, 8-Team
    PPR, same correct honest message.
  - **Fantasy Gamers**: LIMITED, a re-confirmation of the already-tracked,
    already-disclosed routing bug (Worker 2/3/4) — lands on Draft Room
    (PRE-DRAFT) instead of Weekly Home. Newly confirmed here: this
    reproduces from the **Manage Leagues page's own "Open workspace" link**
    too, not only the header quick-switcher — same root cause (the frontend
    lifecycle heuristic has no live Sleeper status for a league drafted
    entirely outside this app, so it can only fall back to a local
    no-draft-board PRE_DRAFT read). Confirmed this is the SAME known gap,
    not a new one; not fixed here per Worker 2's own assessment that closing
    it fully needs a bigger architecture decision (live network call on the
    hot path, or caching a confirmed lifecycle) — out of "small and clearly
    scoped."
- **Create/duplicate/import re-verification (Worker 3's fix)**: created one
  real disposable local test profile ("WORKER5 DISPOSABLE TEST", preset
  `10_TEAM_1QB_STANDARD`) via `/profile`'s Fast Setup form — created and
  activated correctly, survived a hard reload. **Found and fixed a genuine,
  reproducible, DIFFERENT bug** while exercising Worker 3's own
  "Duplicate profile" fix from the League > Settings tab (`league.tsx`'s
  `LeagueSettingsTab`) — see Bugs Found below. After the fix: duplicate now
  correctly activates and stays on the new profile, verified via real
  network-request logs (`POST .../duplicate` 200 with NO follow-up
  `.../<old-id>/activate` call afterward) and a hard reload.
- **Cleanup**: all disposable test profiles from this session (the original
  create, plus 3 "…Copy" profiles created across the pre-fix/post-fix
  duplicate attempts — repeated attempts were needed while diagnosing why
  the fix wasn't taking effect, see the `vite preview` note above) were
  deleted directly from `local_exports/redraft_v1/profiles/` +
  `draft_boards/` (no API delete endpoint exists, same pattern Worker 3
  used). Fantasy Gamers was reactivated as the real active league via the
  normal UI ("Open workspace") before deleting, so `active_profile.json`
  was never left pointing at a deleted profile. Verified via a hard reload
  of `/#/leagues`: exactly the 5 real/pre-existing profiles remain (KHA,
  403 N 18th, Fantasy Gamers [ACTIVE], Isolation Check Local, 10-team 1QB
  Standard), zero leftover disposable entries.

### 3. Data Health — ACTUAL TEST RESULT (2 leagues + refresh re-verification)

- **Fantasy Gamers (Sleeper)**: PASS. Real, differentiated cards: "SLEEPER ·
  League sync" OK/CURRENT, "NWR GOVERNED PROJECTION SNAPSHOT" OK/CURRENT,
  "SLEEPER · Weekly projections" OK/**LIVE**, "Fantasy Football Calculator
  ADP" OK/CURRENT, "CURRENT_PLAYER_STATUS_OVERRIDES_SERVICE" OK/MANUAL,
  "IN_SEASON_DECISION_TRACE_SERVICE" OK. Top bar: "2 data issues."
- **KHA (ESPN) and 403 N 18th (ESPN)**: PASS, and genuinely, visibly
  different from Fantasy Gamers, not a copy-paste same-looking page: both
  show "ESPN · League sync" = **NOT APPLICABLE / LOCAL_ONLY**, "This profile
  is local/manually managed; no live provider sync," and "NO SOURCE ·
  Weekly projections" = NOT APPLICABLE/UNKNOWN. Each has its own real,
  distinct `Last update` timestamp matching its own real draft-completion
  time (KHA 2026-09-02T04:01:25Z, 403N18th 2026-09-09T00:48:33Z). Top bar
  issue counts differ too (KHA "3 data issues," 403N18th "2 data issues,"
  Fantasy Gamers "2 data issues") — real per-league variation, not a shared/
  stale value.
- **Refresh action re-verified against KHA specifically** (not previously
  available before this cycle's data recovery): clicked "Refresh," captured
  real network requests — `GET /api/v1/redraft/data-health` (200),
  `GET /api/v1/redraft/status-overrides` (200), `GET /api/v1/bootstrap`
  (200). Real, live backend calls, not a no-op button.

### 4. Draft Room — ACTUAL TEST RESULT (KHA 157 picks, 403N18th 118 picks — real completed boards, not PRE_DRAFT)

Both confirmed from the Draft Room page's OWN content (a different angle
than Worker 2's sidebar-badge/landing-route check):

- **KHA**: PASS. On-clock banner reads "TEAM 3 IS ON THE CLOCK," "10.14 On
  clock: Team 3," confirming the real 157 already-recorded picks left the
  room correctly positioned at real pick 158 of 192 (16 teams x 12 rounds)
  — not reset to pick 1, not stuck at PRE_DRAFT. Suggestions panel correctly
  refuses to guess ("DecisionBundle unavailable — it is not currently the
  owner's turn (pick 158 belongs to team 3)"). Draft Board tab (By Picks):
  real round-by-round grid, real players in real ADP-consistent order
  (Gibbs/Robinson/Chase/Nacua/Taylor/Smith-Njigba round 1). Draft Board (By
  Roster): real derivable per-team rosters by slot, K/DST correctly all
  "Empty" for every team (matches Worker 2's finding that K/DST were never
  part of this league's real pick stream).
- **403 N 18th**: PASS. "TEAM 7 IS ON THE CLOCK," "15.07 On clock: Team 7,"
  matching the real 118 already-recorded picks (next real pick is 119 of
  128 = 8 teams x 16 rounds). Draft Board (By Picks): real, distinct
  round-1 order (Gibbs/Chase/Allen/Robinson/Smith-Njigba/Nacua) — correctly
  different from KHA's board, confirming no cross-league bleed.

### 5. Cheat Sheet — ACTUAL TEST RESULT (Fantasy Gamers, 3 real edits)

PASS. 564-player sheet. Clicked the **RB position tab**: count changed to
129, all-RB content, correct re-filter. Toggled **"Show Drafted"**: no
visible row-count change for this specific league (correct, not a bug —
Fantasy Gamers is a Sleeper-native league with no local NWR draft board, so
there is nothing locally marked "drafted" to reveal/hide; this control's
effect is real but legitimately a no-op here). Clicked the **Market ADP
column header to sort**: table correctly re-ordered ascending by ADP
(Bijan Robinson 1.01, Jahmyr Gibbs 1.02, Ja'Marr Chase 1.04, ... in the
right order). Print/export were NOT tested, consistent with the
already-disclosed "no print stylesheet" gap from the prior cycle — not
re-claimed as working here.

### 6. Dynasty tools — LIVE OBSERVATION (light re-check, not full re-audit)

PASS. Home: real Owner Command Center (240 Governed board assets, 239
Market coverage [1 unmatched], 80 Rookie Review [7 manual], 0 open
decisions, FINISHED V1 AUTHORITY / YELLOW STALE badges). Dynasty Rankings:
real 240-player board (Puka Nacua #1, real NWR scores/pos ranks/ages).
Asset Explorer: real 379-asset governed registry (7 manual review), real
read-only-registry disclosure. Zero console errors captured across all
three pages. Did not redo the prior cycle's full write-cycle tests (not in
scope for this light re-check).

### Bug found + fixed: Manage Leagues duplicate silently reverted the active-profile pointer

**Real, reproduced, root-caused, fixed.** Different from — and NOT
superseding — Worker 3's race-condition fix (which is still correct and
still holds); this is a second, independent bug that Worker 3's fix did not
and could not address, found while re-exercising that exact code path.

**Repro (before fix, captured via real network-request logs):** From
League > Settings tab (`/league/{id}/league?tab=settings`), clicking
"Duplicate profile" fired `POST .../profiles/{id}/duplicate` (200) — which
correctly creates AND server-side-activates the new profile
(`desktop_facade.py`'s `duplicate_redraft_profile` calls
`set_active_profile` internally) — but was IMMEDIATELY followed by an
unwanted `POST .../profiles/{id}/activate` (200) for the **OLD, source**
profile ID, silently reverting the active pointer back to the original
profile. The UI's own success message still claimed "Profile duplicated and
activated," which was now false. Confirmed via the real `active_profile.json`
file on disk (pointed at the old profile) and a hard reload (chooser showed
the OLD profile as ACTIVE, the new copy present but inactive).

**Root cause (INSPECTED CODE):** `LeagueSettingsTab` is rendered inside
`LeagueScopedPage` (`RedraftApp.tsx`, route `/league/:leagueKey/league`),
which has its own effect (added for legitimate deep-link/bookmark support)
that re-activates whatever profile the URL's `leagueKey` names whenever it
differs from the currently active profile. `duplicateRedraftProfile`
activates the NEW profile server-side, but `LeagueSettingsTab` never
navigates — the URL still names the OLD profile — so `LeagueScopedPage`
saw a mismatch and "corrected" it by re-activating the OLD profile, a
moment after the duplicate's own activation. This is a structurally
different bug from Worker 3's sweep-vs-activate race (no Attention Center
sweep involved at all); Worker 3's `serializeActiveProfileCall` wrapping
was necessary but not sufficient here.

**Fix** (`desktop/apps/redraft/src/league.tsx`, `LeagueSettingsTab`):
added `useNavigate` and, on a successful duplicate, navigate to the new
profile's own URL (`/league/{newProfileId}/league?tab=settings`,
`replace: true`) so `leagueKey` stays in sync with the real active profile
and `LeagueScopedPage`'s effect has nothing left to "correct."

**Verified fixed, live, after an `npm run build` (see the `vite preview`
environment note above — the fix did not take effect until rebuilt):**
`POST .../duplicate` (200) with no follow-up unwanted activate call; URL
correctly changed to the new profile's own path; sidebar/active-context
correctly showed the new "…Copy" profile as ACTIVE; survived a hard reload.

**Residual, NOT fixed here (documented, not chased further):** the
structurally identical route `/league/:leagueKey/profile` (`ProfilePage`
rendered inside `LeagueScopedPage`) has the same latent exposure for its
own `create`/`duplicate`/`importSleeper` — but that URL is not reachable
from any in-app link (the sidebar's "Manage Leagues" nav item always uses
the unscoped `/profile`; grepped for `leagueKey}/profile` template-string
construction anywhere in `desktop/apps/redraft/src` — zero hits), so it is
a dormant deep-link/bookmark-only edge case, not a mainline owner flow.
Fixing it would mean threading the same navigate-on-success pattern into
`profile.tsx`'s shared `ProfilePage`, which is used both scoped and
unscoped — a slightly larger, more invasive change than this pass's "small
and clearly scoped" bar. Flagged for a future worker, not urgent.

### Tests added

**None added for the Manage Leagues fix specifically** — deliberate,
documented decision, not an oversight. INSPECTED: this workspace's
`vitest.config.ts` (`desktop/vitest.config.ts`) sets
`environment: "node"` and `include: ["packages/**/*.test.ts",
"apps/**/*.test.ts"]` — no jsdom/happy-dom, no `@testing-library/react` in
either `package.json`, and the include pattern only picks up `.test.ts`
files, never `.test.tsx`. Confirmed via `find`: **zero** `.test.tsx` files
exist anywhere in `desktop/apps/redraft/src`. This fix lives entirely
inside a React component's event handler (`useNavigate()` + a hook-based
effect elsewhere in `RedraftApp.tsx`) — there is no established pattern in
this codebase for unit-testing that kind of interaction (contrast Worker
2's fix, which lived in a pure function in `league-context.ts` and so was
directly testable in `league-context.test.ts`, or Worker 3's fix, whose
race-condition logic lived in `attention-center.ts`'s pure queue and so was
directly testable there). Writing a synthetic "does calling navigate get
invoked" test without React Testing Library would not meaningfully exercise
the real regression (the interaction between two separate React components'
effects) and risks a false sense of coverage. Verified instead via live
Chrome MCP with real network-request evidence (documented above, both
before and after the fix) — the same standard this whole cycle has used for
comparable React-interaction bugs where no unit-test infrastructure exists.
Existing suites re-run clean after the change: `npx vitest run apps/redraft`
(desktop workspace) -> 430/430 passed, 19/19 files, zero regressions;
`npm run typecheck` (desktop workspace, `apps/dynasty` + `apps/redraft`) ->
clean.

### Cleanup

An unrelated file, `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/
frontend_bench_results.json`, was regenerated as a side effect of running
the full `apps/redraft` vitest suite (same live-timing-benchmark test
Worker 3 already flagged); reverted via `git checkout --` before committing,
not part of this pass's actual change. Untracked smoke-run log files from
earlier workers (`*_smoke_std{out,err}*.log`) remain in the worktree root,
still harmless scratch output, not part of the repo.

### Final HEAD

One commit on top of `66177c27` — see `git log -1` in this worktree.

### Files changed

- `desktop/apps/redraft/src/league.tsx`
- `docs/codex/dogfood_v1/LEDGER.md` (this entry)

### Running processes status at end

Unchanged from start — confirmed via `Get-NetTCPConnection` before handoff:
Redraft backend PID 20368 (18742) / frontend PID 17016 (1422); Dynasty
backend PID 12852 (18741) / frontend PID 5288 (1421). No process restart
was needed (the frontend fix required only `npm run build`, not a process
restart, per the `vite preview` note above). Active Redraft profile at
handoff: Fantasy Gamers (a real league, matching the pattern prior workers
used — no disposable test profile left as the active pointer).

### Open issues for next worker (Worker 6 — CLOSURE MODE)

This is the last dogfooding pass. **Worker 6 should shift into closure
mode**: final regression, restart the dev-server pair if anything requires
it (it shouldn't, given this pass's changes are frontend-build-only), a
real verification pass, then push, then the final structured report to the
owner. Specific carry-forward items:

1. The frontend Sleeper-live-status / chooser-routing gap for Fantasy
   Gamers (Worker 2/3/4, re-confirmed again in this pass from a third
   surface — Manage Leagues' own "Open workspace" link) is still open,
   still not fixed, still correctly worked around by navigating directly to
   `/#/league/{id}/home` for any live testing. Real, if minor, remaining
   friction — worth closing eventually, not blocking.
2. The residual `/league/:leagueKey/profile` deep-link exposure to the same
   class of bug this pass fixed for the Settings tab (see "Residual, NOT
   fixed here" above) — dormant, no in-app link reaches it, low priority.
3. Remember the `vite preview`-not-`vite dev` environment fact (see the top
   of this entry) if Worker 6's closure verification involves ANY frontend
   source change — `npm run build` in `desktop/apps/redraft` (or
   `desktop/apps/dynasty` for that app) is required before a browser reload
   will show it; the running preview process does not hot-reload.
4. Untracked smoke-run log files (`*_smoke_std{out,err}*.log`,
   `dynasty_smoke_std{out,err}.log`, `redraft_smoke_stderr2.log`,
   `redraft_smoke_stdout2.log`) are still present in the worktree root from
   earlier workers — still harmless scratch output, safe to delete once
   servers are stopped for good as part of closure.
5. No other genuine, reproducible bug was found across History/Manage
   Leagues/Data Health/Draft Room/Cheat Sheet/Dynasty this pass beyond the
   one fixed above — every "unavailable"/empty state encountered (KHA/
   403N18th Decision History, KHA/403N18th ESPN Data Health cards, Cheat
   Sheet's already-disclosed no-print-stylesheet gap) was honestly labeled
   with a real, specific, correct reason.
