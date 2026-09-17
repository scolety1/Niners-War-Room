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
