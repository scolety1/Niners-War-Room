# NWR Sunday Readiness Overnight (2026-09-20 decisions) — LEDGER

Governing brief: `NWR_Sunday_Readiness_Overnight_2026-09-18.md` (owner's
Downloads folder). Deadline: Saturday September 19, 2026, 12:00 noon
America/Denver. This ledger is new for this cycle; do not conflate with
`docs/codex/dynasty_league_import_v1/LEDGER.md` or
`docs/codex/dogfood_v1/LEDGER.md` (prior, separate cycles this one builds on).

### Methodology key (per brief's own standard)

- **INSPECTED CODE** — read directly from the repo, this pass.
- **ACTUAL TEST RESULT** — a real pytest/vitest/script run, this pass.
- **LIVE OBSERVATION** — a real running process/API hit/filesystem read,
  observed directly this pass.
- **INFERENCE** — a conclusion drawn from the above, explicitly labeled,
  never presented as settled fact.

---

## Worker 1 — Establish recoverable state and trustworthy inputs (2026-09-18, ~7:15–7:35 PM Mountain)

### 0. Branch/HEAD verification — LIVE OBSERVATION

`git log -1` in `C:\NWR\prospective-outcomes-v1`: HEAD =
`3ea72fbcaeb9a82c23c8d9d260b040c697d8603d`, committed
`2026-09-18 18:31:43 -0600`. **Exact match to the brief's audited
checkpoint** — HEAD has not advanced. `git status --short`: clean except 3
untracked, harmless items (`dynasty_smoke_stderr.log`,
`dynasty_smoke_stdout.log` — leftover scratch logs from the prior Dynasty
cycle; `local_exports.backup-20260918T230905Z/` — an existing, gitignored
backup, see Backups below). No dirty work to preserve, no reset performed,
nothing discarded.

Current time at start of this pass: **Friday Sept 18, 2026, ~7:15–7:22 PM
Mountain (MDT, UTC-6)**, confirmed twice (`date`, PowerShell
`Get-Date`/`Get-TimeZone`). **~16h40m remain to the Saturday noon deadline.**
No deadline risk at this point in the cycle.

### 1. Data roots — LIVE OBSERVATION (re-verified fresh, not cited from memory)

All 4 dev-server processes from the prior cycle are **still running,
confirmed alive via `Get-NetTCPConnection`/`Get-CimInstance Win32_Process`,
not assumed**:

| App | Port | PID | Process start | Command line |
|---|---|---|---|---|
| Redraft backend | 18742 | 31352 | 2026-09-17 17:55:35 | `python scripts/run_nwr_desktop_api.py --host 127.0.0.1 --port 18742 --mode redraft --repo-root C:\NWR\prospective-outcomes-v1` |
| Redraft frontend | 1422 | 16376 | 2026-09-17 17:55:33 | `node .../vite.js preview --port 1422 --strictPort` |
| Dynasty backend | 18741 | 40244 | 2026-09-18 18:18:10 | `python scripts/run_nwr_desktop_api.py --port 18741 --mode dynasty --repo-root C:\NWR\prospective-outcomes-v1` |
| Dynasty frontend | 1421 | 37176 | 2026-09-18 17:54:32 | `node .../vite.js preview --port 1421 --strictPort` |

Health: `GET /api/v1/bootstrap` → `401` on both backends (the established
healthy-contract response, not a crash); `GET /` → `200` on both frontends.

**Root resolution (INSPECTED CODE, confirmed by the command lines above —
neither backend was launched with `--redraft-root`/`--dynasty-root` nor an
`NWR_REDRAFT_HOME`/`NWR_DYNASTY_LEAGUE_HOME` env override visible in its own
command line):**
- `redraft_store_root()` (`src/services/redraft_engine_v1_service.py`) and
  `dynasty_league_store_root()` (`src/services/dynasty_sleeper_league_service.py`)
  both fall back to `<repo_root>/local_exports/{redraft_v1,dynasty_v1}` when
  `NWR_REDRAFT_HOME`/`NWR_DYNASTY_LEAGUE_HOME` are unset. `--repo-root` on
  both processes is this worktree, `C:\NWR\prospective-outcomes-v1`.
- **Confirmed empirically, not just by code reading:** this worktree's
  `local_exports/redraft_v1/profiles/` holds exactly 5 real profile files
  and `local_exports/dynasty_v1/` holds a real, very recently updated
  (`2026-09-19T00:25:55Z` = `2026-09-18 18:25:55` Mountain, ~50 minutes
  before this check) Enginerds league profile — i.e., these two running dev
  backends are demonstrably reading/writing this worktree's own
  `local_exports/`, not any AppData path.
- This shell's own `env | grep -i NWR` shows no `NWR_REDRAFT_HOME`/
  `NWR_DYNASTY_LEAGUE_HOME` set — consistent, though not proof of the
  already-running processes' own environment (Windows doesn't expose a
  running process's env block without extra tooling; the empirical
  local_exports evidence above is the stronger proof).

**Native app state roots (LIVE OBSERVATION, read-only, distinct from the
browser-preview roots above):**
- `%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\profiles\` — real,
  7 files: Fantasy Gamers (older copy, `4c5f0476...`, stale since
  2026-08-14), KHA real (`fb1c4976...`), KHA TEST/PRACTICE variants, 403 N
  18th real (`4b4a990f...`, plus one dated backup file
  `4b4a990f....pre_provider_fix_backup_20260908.json`), and **"Tester"**
  (`eafa580e...`). **`active_profile.json` in this real native install still
  points at `eafa580e...` ("Tester")** — confirmed still true this pass, a
  real, standing, not-yet-fixed gap (also flagged by the prior dogfood
  cycle; out of this pass's scope to fix, re-confirmed only).
- `%LOCALAPPDATA%\com.ninerswarroom.dynasty\state\` — confirmed still only
  `runtime.json`, no per-league profile store structure of any kind. This
  independently reconfirms (fresh, this pass) that Dynasty's real native
  install has never held a per-league Sleeper import — everything Dynasty-
  side found in this cycle lives only in this worktree's
  `local_exports/dynasty_v1/`.
- These native roots are **separate from, and were NOT touched by,** either
  running dev-server pair this pass.

**Real, actionable gap found this pass (new, not in the brief's own W/D
list): both backend dev processes are running code from BEFORE the current
HEAD.** Redraft backend/frontend (PID 31352/16376) started 2026-09-17
17:55, predating three same-day commits on 2026-09-18 (`b2c11c80`,
`684c2b98`, `3ea72fbc`) that modified the SHARED `src/application/
desktop_facade.py` (+406/-lines) and `src/desktop_api/server.py`
(+59/-lines) — additive/Dynasty-mode-gated changes per the Dynasty cycle's
own byte-identical-when-omitted regression tests, so Redraft's own live
behavior should be unaffected, but the running process is not literally
serving HEAD's code. More materially: **the Dynasty backend (PID 40244)
started 2026-09-18 18:18:10 — 13 minutes BEFORE the final commit `3ea72fbc`
(18:31:43) landed** — so the currently-running Dynasty backend does not yet
serve `3ea72fbc`'s own Compare/Trade-Decision-Lab ownership wiring. The
Dynasty frontend's built `dist/index.html` is timestamped 2026-09-18 18:22 —
also ~9 minutes before `3ea72fbc` landed, so the served Dynasty UI bundle
predates that commit's frontend changes too. **Action for the next worker
that needs to exercise Dynasty's ownership-in-Compare/Trade-Lab feature live:
restart the Dynasty backend and rebuild+restart the Dynasty frontend first**
— do not assume the currently-running Dynasty instance reflects HEAD.
Redraft's own dev pair does not need a restart for this pass's purposes
(the new code is inert for Redraft/mode-gated), but any worker relying on
exact HEAD-parity for `desktop_facade.py` behavior should restart it too
before deep-diving.

### 2. Backups — LIVE OBSERVATION, verified intact, no new backup needed

No writes were made to any owner data this pass (read-only investigation
only: local filesystem reads, 6 real GET-only Sleeper API calls, no
Sleeper/ESPN writes, no repo file writes outside this ledger). Per the
brief's own instruction, a fresh backup is only required before touching
something — nothing was touched, so none was made. Existing backups,
verified intact:

- **`C:\NWR\prospective-outcomes-v1\local_exports.backup-20260918T230905Z\`**
  (from the Dynasty League Import V1 cycle, Part D of that ledger). **Byte-
  verified this pass:** `diff -rq --exclude=dynasty_v1 --exclude="*.backup-*"
  local_exports local_exports.backup-20260918T230905Z` → **zero
  differences** — every file outside the new, intentional `dynasty_v1/`
  subtree is still byte-identical to this backup. (Apparent file-count
  mismatch in an earlier raw `find` pass — 103 vs 114 — was traced to an
  inconsistent `--exclude` between the two `find` invocations, not a real
  discrepancy; the `diff -rq` comparison, which applied the same excludes to
  both sides, is the authoritative check and found nothing.)
- **`C:\NWR\prospective-outcomes-v1\local_exports\redraft_v1.backup-20260917T224444Z\`**
  (from the dogfood cycle, pre-KHA/403N18th-recovery snapshot). Still
  present, untouched, nested inside `local_exports/` (gitignored, same as
  before).
- **`%LOCALAPPDATA%\com.ninerswarroom.redraft.backup-20260916T140835Z\`**
  (real native-install snapshot, dogfood cycle). Still present. The real
  native install itself was read-only inspected this pass (see above), never
  written to, so this backup did not need refreshing.
- No backup exists for `%LOCALAPPDATA%\com.ninerswarroom.dynasty\` — correct
  and sufficient, since that directory holds no per-league data to protect
  (only `logs/` and `state/runtime.json`).

**Conclusion: all real owner data (Fantasy Gamers, KHA, 403 N 18th profiles
and draft boards, Enginerds Dynasty import) is backed up or was never
written to this pass. No demo/test profile was added to any real store this
pass** (the two pre-existing local test profiles, "10-team 1QB Standard" and
"Isolation Check Local," were left exactly as found, not touched, not
duplicated).

### 3. Real current-provider snapshot — LIVE OBSERVATION (real GET-only Sleeper calls, zero writes)

**Zero-writes method:** every call below was a plain `curl -s
https://api.sleeper.app/v1/...` (GET only, no body, no auth header, no
write-capable endpoint ever addressed) or a read of an already-persisted
local JSON file. No Sleeper/ESPN write endpoint was called anywhere in this
pass.

**Current provider week/season — real, confirmed, not assumed:**
`GET https://api.sleeper.app/v1/state/nfl` →
```
{"week":2,"season_type":"regular","season":"2026","leg":2,
 "league_season":"2026","previous_season":"2025",
 "season_start_date":"2026-09-09","display_week":2,
 "league_create_season":"2026","season_has_scores":true}
```
**Real confirmed current week = 2, regular season, 2026.** Matches the
brief's expectation ("Week 2 is expected") but this is a live-confirmed
fact, not an assumption carried over from the brief.

---

#### LEAGUE 1 — Fantasy Gamers (Sleeper `1312983576827920384`)

Real, fresh `GET league/{id}`, `.../rosters`, `.../users` this pass.

- League: `name: "Fantasy Gamers"`, `status: "in_season"`, `season: "2026"`,
  `total_rosters: 10`.
- **Settings, real and non-PPR-adjacent details worth flagging:**
  `waiver_budget: 100`, `waiver_type: 1`, `trade_deadline: 12` (week 12),
  `playoff_teams: 6`, `playoff_week_start: 15`, `pick_trading: 0`,
  `max_keepers: 1`, `reserve_slots: 2`, `taxi_slots: 0`.
- `roster_positions`: `QB, RB, RB, WR, WR, TE, FLEX, K, DEF, BN x6` (15
  slots total) — **has a DST slot** (contrast with Enginerds, which does
  not).
- `scoring_settings` (real, full map, PPR: `rec: 1.0`; `pass_td: 4.0`,
  `pass_yd: 0.04` (1/25yd), `pass_int: -2.0`, `rush_td`/`rec_td`: `6.0`,
  `fum_lost: -2.0`, real DST points-allowed tiers
  `pts_allow_0: 10.0` … `pts_allow_35p: -4.0`, real kicker tiers
  `fgm_0_19: 3.0` … `fgm_60p: 6.0`). Full map captured in scratch output
  this pass; not reproduced in full here to keep this entry readable, but
  every field above came from the real response, not a paraphrase.
- **Owner/roster reconciliation — real, confirmed MATCH, no discrepancy
  found:** `owner_id 1000507609050337280` → `roster_id 9` →
  `display_name "scolety"` → `metadata.team_name "Brown Town & Big Mike"`.
  This is an **exact match** to the brief's stated owner ID and roster
  number. (The brief flagged a risk that "earlier cycles used a different
  owner mapping" — no such conflicting mapping was found anywhere in this
  worktree's persisted profile data; the profile's own `draft.draft_slot: 9`
  field is also consistent with roster 9, though that field is a separate,
  local draft-position concept, not itself the owner/roster join key.)
- **Real roster 9 (this pass, live):** 15 rostered IDs (14 players + `"NE"`
  DST), `starters` = 9 IDs (matches the 9 starting slots above), `reserve:
  None`, `taxi: None`, record `1-0`, `fpts: 156.96`, `ppts: 156.96` (exact
  match — this team started its optimal lineup in week 1), `waiver_position:
  6`, `waiver_budget_used: 0`, `total_moves: 0`.
- **Real finding worth flagging prominently for whichever worker fixes
  W5/W7 (FAAB/waiver handling):** `desktop_facade.py` L3560 hardcodes
  `is_faab_league = raw_waiver_type == 1`. Fantasy Gamers' real
  `waiver_type` is **1**; Enginerds' real `waiver_type` is **2** (see below).
  Cross-referenced against third-party, independently-published evidence
  (a real GitHub PR, `jdguggs10/flaim#294`, which defines a named
  `SLEEPER_WAIVER_TYPE_FAAB = 2` constant and states "Sleeper sends a
  default `waiver_budget: 100` on rolling-waiver leagues too, so the
  budget's presence is not a FAAB signal") — **the commonly-documented real
  Sleeper convention is `waiver_type == 2` = FAAB, not `1`.** Sleeper's own
  official docs (`docs.sleeper.com`) do not enumerate this field at all, so
  this is corroborated third-party evidence, not an officially documented
  fact — flagged as **high-confidence, not certain**. If correct, this
  codebase's FAAB detection is currently backwards for these exact two real
  leagues: Fantasy Gamers (`waiver_type=1`, likely NOT actually a FAAB
  league) would be wrongly treated as FAAB, while Enginerds (`waiver_type=2`,
  likely the genuinely FAAB one) would be wrongly treated as NOT FAAB by
  this exact check — the opposite of what's needed. **Not fixed this pass**
  (explicitly out of Worker 1's scope) — flagged for whoever owns W5/W7.

#### LEAGUE 2 — Las Vegas Enginerds (Sleeper `1344772855908290560`)

Real, fresh `GET league/{id}`, `.../rosters`, `.../users` this pass
(independent of, and reconfirming, the Dynasty League Import V1 cycle's own
capture from ~50 minutes earlier the same evening — that prior capture and
this pass's fresh capture agree exactly).

- League: `name: "Las Vegas Enginerds"`, `status: "in_season"`,
  `season: "2026"`, `total_rosters: 10`. `waiver_type: 2`, `waiver_budget:
  100`, `trade_deadline: 99` (none), `playoff_teams: 4`,
  `playoff_week_start: 16`, `pick_trading: 1`, `max_keepers: 1`,
  `reserve_slots: 2`, `taxi_slots: 0`.
- `roster_positions`: `QB, RB, RB, WR, WR, WR, TE, FLEX, FLEX, K, BN x14`
  (24 slots) — **confirmed, again, no DST/DEF slot anywhere.**
- **Full real scoring map, read again per the brief's explicit instruction
  ("this summary is not a replacement scoring specification"), verbatim
  from the live response and cross-checked against the persisted
  `local_exports/dynasty_v1/league_profiles/1344772855908290560.json`
  (updated 2026-09-19T00:25:55Z, ~50 min prior) — the two agree exactly:**
  `rec: 0.0` (non-PPR), `rec_fd`/`rush_fd: 0.4` (first-down bonuses),
  `pass_td: 3.0`, `rush_td`/`rec_td: 4.0`, `pass_yd`/`rush_yd`/`rec_yd:
  0.0333.../0.1/0.1`, `pass_int`/`fum_lost: -1.0`, `pass_2pt`/`rush_2pt`/
  `rec_2pt: 2.0` (all three 2pt-conversion types scored, real and
  confirmed), kicker tiers `fgm_0_19`/`fgm_20_29`/`fgm_30_39: 2.0`,
  `fgm_40_49: 3.0`, `fgm_50p: 4.0` (with a redundant, always-zero
  `fgm_50_59: 0.0` field — real, not a bug, just an unused duplicate key),
  all `pts_allow_*` fields `0.0` (consistent with no DST slot — genuinely
  unused, not a gap). `xpm: 1.0`.
- **Owner/roster reconciliation — real, confirmed MATCH:** `owner_id
  1352768154031374336` → `roster_id 7` → `display_name "mcolety1"` →
  `metadata.team_name "Niners"`. Exact match to the brief. Real, disclosed,
  not previously flagged-as-new-but-independently-reconfirmed fact:
  `co_owners: ["1000507609050337280"]` on this same roster — the exact same
  Sleeper user_id that owns Fantasy Gamers' roster 9 also has co-owner
  access to this Enginerds roster (display_name there: `"scolety"`, no team
  name set). Irrelevant to a read-only pass, flagged for awareness only.
- **Real roster 7 (fresh, this pass):** 28 rostered players, `starters`: 10
  IDs, `reserve: ["11638","12484"]` (2, matches `reserve_slots: 2`),
  `taxi: null`. Record `1-0`, `fpts: 108.10`, `ppts: 144.70` (real gap
  between actual and optimal-lineup points — a genuine real signal that the
  owner's actual week-1 lineup left points on the table), `waiver_position:
  2`, `waiver_budget_used: 0`, `total_moves: 0`.
- Per the reconciliation above, `waiver_type: 2` here is (per the same
  third-party cross-reference) the more likely real-FAAB league of the two —
  the opposite of what this codebase's current `== 1` check would conclude.

#### LEAGUE 3 — KHA High Stakes (ESPN, existing profile `fb1c49402c7644a99120197d41344bbb`)

**INSPECTED CODE + LIVE OBSERVATION.** `grep -rniE
"class.*Espn|espn_service|EspnClient|espn\.com/apis|fantasy\.espn"
src/` → **zero matches anywhere in `src/`.** Confirmed, fresh, this pass:
**no ESPN API client or service exists in this codebase at all** — this is
not new (the dogfood cycle found the same thing) but is independently
reconfirmed rather than cited.

- Local profile (`local_exports/redraft_v1/profiles/fb1c4940....json`,
  unchanged since 2026-09-02T04:01:25Z): `provider: "espn"`,
  `provider_league_id: null`, `team_count: 16`, `practical_mode: True`
  (K/DST handled via manual entry outside the draft pool, an existing,
  unrelated fix from an earlier cycle — confirmed still in effect).
  `draft.rounds: 12`, `draft.roster_limits: {QB:2, RB:6, WR:6, TE:3, K:2,
  DST:2}`.
- **What exists:** a complete, real 157-pick historical draft board
  (`draft_boards/fb1c4940....json`), a `manual_assets` file (draft-time
  rookie/board augmentation only — confirmed by inspection, it is NOT a
  current-roster or transaction-tracking mechanism; every entry is a
  player-pool-availability annotation, not an ownership record), and
  `owner_test_instrumentation` event logs. Native AppData copy
  (`%LOCALAPPDATA%\com.ninerswarroom.redraft\...\fb1c4940....json`) is
  identical (same profile, previously copied into this worktree by the
  dogfood cycle).
- **What is genuinely missing, confirmed this pass, not inferred:** any
  post-draft transaction history (adds/drops/trades/waivers), any current
  roster snapshot distinct from the draft board, any live opponent-roster
  visibility, any current scoring/acquisition-rules re-confirmation from a
  live source, and any mechanism in this codebase to obtain any of the
  above for ESPN short of manual owner entry (no ESPN API integration
  exists; scraping/cookies/passwords are explicitly disallowed by the hard
  boundary). **Historical draft picks are the only current data this league
  has anywhere in this codebase** — matching the brief's own framing exactly
  ("Historical picks are not a current roster").
- **Smallest validated path, if the owner wants this closed (not started
  this pass, listed only):** either (a) a manual/local current-roster entry
  path reusing the existing `provider: "local"` profile mechanism already
  proven safe for test profiles, with the owner hand-entering their real
  current KHA roster, or (b) a genuine, new, owner-authorized read-only ESPN
  Fantasy API integration (requires the owner's own `SWID`/`espn_s2`
  cookies, which the owner would have to supply explicitly — not something
  this pass can obtain, and not attempted). Neither exists today.
- **Verdict inputs for the decision-sheet author:** lineup/pickup readiness
  for KHA must be marked **BLOCKED** — confirmed, live, this pass, that the
  app's own Weekly Home/Start-Sit/Improve Team/Trades surfaces already
  self-report "Sleeper league required" for KHA (an honest, pre-existing
  refusal, not a new fix) rather than fabricating advice from the stale
  draft board. This is a real capability gap, not a bug to silently paper
  over.

#### LEAGUE 4 — 403 N 18th and friends (ESPN `1009373442`, existing profile `4b4a990faf124ce7a5d612537ba5943b`)

Same investigation class as KHA, same conclusion, real league-specific
details below.

- Local profile: `provider: "espn"`, `provider_league_id: null` (the field
  itself is null — the real ESPN league ID `1009373442` is documented only
  in a separate dated receipt file,
  `state/redraft/projections/2026/DRAFT_DAY_AUTHORIZATION.json`, inside the
  **real native AppData install** — confirmed present there by the dogfood
  cycle; **not copied into this worktree** (correctly — it was never in the
  dogfood cycle's own copy list), so this worktree's own profile does not
  carry the ID anywhere machine-readable. Real, standing gap: the ID is only
  recoverable today from that one native-install receipt file or from this
  project's own memory/ledger record, not from the worktree's profile JSON
  itself.). `team_count: 8`, `practical_mode: True`, `draft.rounds: 16`,
  `draft.roster_limits: {}` (empty — no per-position cap recorded).
- **What exists:** a complete, real 118-pick historical draft board, a
  `manual_assets` file (same draft-time-only nature as KHA's), plus (unlike
  KHA) a real `prospective_decision_log/` (72 lines),
  `nwr_pure_experiments/` corrections+decisions, an ADP provider-cache
  league-selection entry, and an ADP snapshot file — i.e., this league has
  more post-draft NWR-internal activity recorded (decision logs, ADP
  refreshes) than KHA does, but **still zero post-draft roster/transaction
  data from ESPN itself.**
- **What is genuinely missing:** identical list to KHA — no post-draft
  transaction history, no current roster snapshot, no live opponent
  visibility, no ESPN API integration anywhere in this codebase.
- **Verdict inputs:** same as KHA — lineup/pickup readiness must be marked
  **BLOCKED**; the app already self-reports "Sleeper league required"
  live for this league's weekly tools (confirmed by the dogfood cycle,
  consistent with this pass's own code-level finding that no ESPN client
  exists to have changed that since).

### 4. Schedule/kickoff/postponement data source — INSPECTED CODE

- `grep -rn "import_schedules|nflverse_schedules"` across `src/` →
  `nflverse_schedules` is a real, already-registered nflverse dataset,
  consumed by exactly two files: `nflverse_refresh_health_service.py`
  (columns explicitly checked there: `game_id`, `home_team`, `away_team`,
  `game_type` — a real, live nflreadpy `import_schedules()` pull) and
  `injury_availability_context_service.py`.
- **`injury_availability_context_service.py` explicitly, deliberately gates
  this data OFF from any live display today** (read directly, lines
  ~161-174): status is `SAFE_NOW_DISPLAY_ONLY` but **only** for
  "regular-season denominator support" (i.e., counting games played, for
  historical rate-stat context) — the module's own text says verbatim: **"Do
  not display next game, opponent, bye, or schedule-derived health"** and
  **"Schedule context needs a separate lane-specific activation review
  before next-game/opponent/bye appears in Injury/Availability."**
- **`grep` for `kickoff|game_id|gameday|home_team|away_team` in
  `src/application/desktop_facade.py` → zero matches.** Confirmed, live,
  this pass: the shared facade that serves Start/Sit, Improve Team, and
  weekly lineup decisions has **no wiring to any schedule/kickoff source at
  all**, consistent with and elaborating on the brief's own W2 finding ("no
  ...game lock, or kickoff inputs").
- **Real, actionable conclusion for whoever fixes W1-W4:** the raw data
  source (`nflreadpy.import_schedules`, real, live, already proven reachable
  by `nflverse_refresh_health_service.py`) **already exists and is reachable
  in this codebase** — this is not a "no data source available" gap, it is
  a "data source exists, is explicitly gated off, and has never been wired
  into any live weekly-decision surface" gap. Whether the raw `import_schedules()`
  output carries true kickoff-time (not just date) and postponement/reschedule
  fields was **not independently re-verified this pass** (this pass confirmed
  only the columns this codebase's own code explicitly checks:
  `game_id`/`home_team`/`away_team`/`game_type`, plus `gameday` by nflverse's
  well-known standard schema) — flagged as a real, disclosed unknown for
  the worker who wires this in to verify directly (e.g., a real
  `import_schedules()` pull and column inspection) before building lock
  logic on top of it.

### 5. Capture-time convention — INSPECTED CODE, confirmed, not newly invented

- The dominant, established pattern across this codebase is a
  `*_as_of`/`*_at_utc` field stamped with `datetime.now(UTC).isoformat()`
  **at the moment of the real fetch**, injectable via an optional parameter
  for tests but defaulting to real wall-clock time in production code.
  Concretely, in `weekly_projection_service.py`: `fetched_at: str | None =
  None` parameter, `as_of = fetched_at or datetime.now(UTC).isoformat()`,
  stored as `source_as_of` on every returned row. The module's own docstring
  is explicit that this is a **capture-time** stamp, not a provider-
  published freshness time, because the underlying Sleeper endpoint exposes
  no freshness field of its own — "Callers MUST treat a fetch failure as
  'unavailable this week,' never as a reason to reuse a stale prior week's
  numbers."
- The same pattern recurs as `created_at_utc`/`updated_at_utc` on every
  persisted profile (Redraft `local_exports/redraft_v1/profiles/*.json`) and
  league profile/snapshot (Dynasty `local_exports/dynasty_v1/...`) — e.g.
  the Enginerds Dynasty profile's real `updated_at_utc:
  "2026-09-19T00:25:55+00:00"` observed this pass is exactly this
  convention: the moment the import ran, not any Sleeper-side timestamp
  (Sleeper does not expose one for league/roster state).
- **Confirmed: this is the existing, established convention this pass
  should assume for any new capture-time display work** — no new scheme
  invented, matches what this cycle's own Dynasty pass already used.

---

### Files changed this pass

- `docs/codex/sunday_readiness_20260920/LEDGER.md` (new — this file).

No application code, test, or config file was modified. No new backup was
required (nothing was touched); existing backups were verified intact (see
above). No repo data files were written. Six real, GET-only Sleeper API
calls were made (`state/nfl`; `league/{fg_id}`, `.../rosters`, `.../users`
for Fantasy Gamers; `league/{lve_id}`, `.../rosters`, `.../users` for
Enginerds) — all read-only by construction (plain `curl`, no body, no write
verb). Zero ESPN calls were made (no ESPN client exists to call). Zero
scraping, credential extraction, or cookie access was attempted for either
ESPN league.

### Open issues for Worker 2 (fixes W1 — current-week initialization — and W2-W4)

1. **Restart the Dynasty backend + rebuild/restart the Dynasty frontend
   before relying on its live HTTP API or rendered UI to reflect HEAD**
   (`3ea72fbc`) — the running Dynasty backend (PID 40244) started 13 minutes
   before that commit landed, and the served frontend `dist/` predates it by
   ~9 minutes. Redraft's own dev pair does not need this for correctness
   (new code is inert there) but is also running pre-HEAD code technically.
2. **W1 fix target confirmed live and reachable:** Start/Sit
   (`desktop/apps/redraft/src/in-season.tsx` L339) and Improve Team
   (`improve-team.tsx` L89) both need the real provider-week (confirmed this
   pass: **2**, from a real `state/nfl` call) threaded through instead of a
   hardcoded `1`. Weekly Home's existing provider-week logic (already
   correct, per the brief) is the pattern to reuse.
3. **The real waiver_type/FAAB semantics finding above (Fantasy Gamers
   `waiver_type=1`, Enginerds `waiver_type=2`, `desktop_facade.py:3560`
   checks `== 1`) needs a deliberate decision** before or alongside any
   W5/W7 FAAB work — verify against a definitive source (or empirically,
   e.g. checking whether either league's real Sleeper UI shows a FAAB bid
   box) before changing the check, since this pass's evidence is strong
   third-party corroboration, not an official Sleeper doc citation.
4. **Schedule/kickoff data**: `nflreadpy.import_schedules()` is real, live,
   and already reachable in this codebase (via
   `nflverse_refresh_health_service.py`'s pattern) but has never been pulled
   fresh and column-inspected specifically for `gametime`/postponement
   fields by this pass — do that before wiring W2's game-lock/kickoff
   requirement, don't assume the schema without checking.
5. **KHA and 403 N 18th are BLOCKED for any current-state Sunday tool**,
   confirmed both at the code level (no ESPN client exists anywhere in
   `src/`) and at the live-app level (both already self-report "Sleeper
   league required" for Weekly Home/Start-Sit/Improve Team/Trades — an
   existing, correct, honest refusal, not something to build around or
   silently override). Decision sheets for these two leagues should be
   written as BLOCKED with the exact reason, not attempted.
6. **403 N 18th's real ESPN league ID (`1009373442`) is not present
   anywhere in this worktree's own profile JSON** (`provider_league_id:
   null`) — it is only documented in a receipt file inside the real native
   AppData install, not copied here. If any worker needs it programmatically
   from within this worktree, it is not currently available without either
   reading the native AppData install directly (read-only) or hardcoding the
   value from this ledger/prior memory.
7. **Real native install's `active_profile.json` still points at "Tester,"
   not a real league** — reconfirmed unchanged this pass. Not this cycle's
   Worker 1 to fix (never touches real AppData), but relevant context for
   whoever eventually packages/tests the native app in step 5 of the brief.
8. Both leagues' real current provider week is **2** — do not hardcode it
   even though it matches the brief's own expectation; the live `state/nfl`
   call above is the authoritative source and should be re-checked again
   closer to Sunday if this cycle runs long, since `week`/`display_week`
   will change as games are played.
