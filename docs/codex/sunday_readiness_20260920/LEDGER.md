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

---

## Worker 2 — Fix W1-W4: current-week and legal Start/Sit (2026-09-18,
~7:26-7:55 PM Mountain)

Time check: started ~7:26 PM Mountain, finished this entry ~7:55 PM.
**~16h05m remained to the Saturday noon deadline when this pass finished.**
No deadline risk.

### W1 — current-week initialization — INSPECTED CODE + ACTUAL TEST RESULT
+ LIVE OBSERVATION

Root cause confirmed exactly as the brief's audit described: Start/Sit
(`in-season.tsx` `LineupPage`, real line was 346 in this HEAD, not 339 --
the file had grown slightly since the audited SHA) and Improve Team
(`improve-team.tsx`, waiver week L92 and streamer week L149) each
hardcoded `useState(1)`, independent of Weekly Home's own already-correct
`LeagueWorkspaceContext.currentWeek` mechanism.

Fix: extracted Weekly Home's inline logic into two new shared hooks in
`weekly-shared.tsx` -- `useProviderWeek` (thin wrapper over the existing
`useLeagueWorkspaceContext`) and `useWeekSelection` (the manual-override
state machine, `week` stays `null`, never a fabricated `1`, until the real
provider week resolves or the owner picks one). `WeeklyHomePage` itself
was refactored onto these same two hooks (pure refactor, byte-identical
resolved `week`, same `?? 1` display fallback preserved at that one call
site -- confirmed via the existing weekly-shared/in-season test suites,
unchanged pass count). `LineupPage`, and Improve Team's waiver week AND
streamer week, now reuse the exact same mechanism, with NO `?? 1`
fallback -- each loader gates on `week != null`, and an honest
"Loading..." banner is shown while unresolved. Manual overrides remain
explicit, per-surface, and reset on league switch (unchanged behavior).

**LIVE OBSERVATION (real browser, real Fantasy Gamers league, real
provider week = 2):** Start/Sit's "NFL WEEK (AUTO)" field showed `2`
immediately, correct on first render, title read "Start / Sit — THIS WEEK
(Week 2)". Improve Team's Targets/Add-Drop THIS_WEEK mode and the
Streamers tab both showed "NFL WEEK: 2" as well. No flash of "1" observed,
no console errors. Verified via a real Chrome MCP session against the
rebuilt+restarted dev pair (see below).

### W2 — locks, reserve/taxi, injury-status distinctness — INSPECTED CODE
+ ACTUAL TEST RESULT + LIVE OBSERVATION

**Reserve/taxi:** `build_roster_candidates` (`weekly_lineup_optimizer_
service.py`) now accepts `reserve_sleeper_player_ids`/
`taxi_sleeper_player_ids` (Sleeper's own real roster `reserve`/`taxi`
arrays, threaded from the facade's own already-fetched `own_roster`
mapping -- no second fetch) and tags each `RosterCandidate` with
`is_reserve`/`is_taxi`. `optimize_weekly_lineup` hard-excludes both from
the normal eligible/greedy pool into a new `reserve` bucket, before any
point comparison happens -- a reserve player can never win an
unconditional START regardless of his projection. Real activation (not
built this pass -- out of narrow scope) would be a separate, conditional
transaction; this fix only prevents the illegal default.

**Lock/kickoff:** a new, narrowly-scoped module,
`src/services/weekly_game_lock_service.py`, does a real, live
`nflreadpy.load_schedules(seasons=[season])` pull (confirmed live this
pass, real Week 2 2026 data: Thursday BUF@DET already locked as of this
pass's real wall-clock time, Sunday games not yet locked) and computes
which teams' real games have already kicked off, using nflverse's real
`gameday`+`gametime` columns (Eastern Time convention, confirmed via a
real spot-check). Deliberately does **not** touch, extend, or depend on
`injury_availability_context_service.py`'s own separate, still-gated
next-game/opponent/bye display -- this module answers only "has this
team's game already started," nothing else, and is wired only into the
weekly lineup optimizer, not any injury/availability surface. A fetch
failure degrades honestly to an empty locked-team set (`sourceStatus:
"UNAVAILABLE"`), never a guessed lock state. `optimize_weekly_lineup`
PINS an already-locked current starter into a real eligible slot
regardless of point comparison (phase 1, before the normal greedy runs),
and hard-excludes an already-locked bench player (not already starting)
from being newly started, into a new `locked_unavailable` bucket.

**Injury-status distinctness:** the existing `_status_for`/`ZERO_VALUE_
KINDS` hard-exclusion (SEASON_OUT/NOT_WITH_TEAM/ADMINISTRATIVE_EXEMPT)
was left untouched -- confirmed by re-reading `player_availability_status_
service.py` this pass that this manual-override list is genuinely the
ONLY real current-season status source in this codebase (no live
injury/practice-report feed exists anywhere), so "questionable" cannot be
honestly sourced/displayed this pass -- not attempted, not fabricated.
What WAS newly added and is real: RESERVE (Sleeper's own roster field) and
LOCKED (real kickoff-derived) are now genuinely distinct, sourced facts
from UNRESOLVED_IDENTITY (a new, distinct status -- see W3) and from the
existing SEASON_OUT/NOT_WITH_TEAM/ADMINISTRATIVE_EXEMPT excludes. All five
now render as visually/semantically distinct buckets in the API response
and the Start/Sit UI (`reserve`, `lockedUnavailable`, `excluded`,
`starters[].status`), never collapsed into one "zero" bucket.

**Real facade wiring:** `desktop_facade.py`'s `redraft_weekly_lineup` now
calls `compute_weekly_game_lock(season=selected.season, week=week)` and
passes `own_roster.get("reserve")`/`.get("taxi")` and the real player
catalog (`players/nfl`, already fetched for this same request) into
`build_roster_candidates`. New response fields: `reserve`,
`lockedUnavailable`, `unresolvedIdentityStarterCount`, `gameLock`.

### W3 — missing-projection rows, unprojected count, unmatched identity —
INSPECTED CODE + ACTUAL TEST RESULT + LIVE OBSERVATION

Confirmed the exact real gap: `build_roster_candidates` previously
`continue`d past any roster/starter id with NO row in `weekly_projection_
service`'s output (Sleeper's weekly-projection endpoint simply has no
entry for some real rostered players some weeks) -- silently dropped, not
even counted. Fixed: such a player is now kept
(`identity_match="UNMATCHED_NO_PROJECTION_ROW"`, resolved name/position/
team from the real Sleeper player catalog when supplied, never
fabricated). A real required starting slot that ends up EMPTY now
increments `unprojected_starter_count` (previously always 0 for an empty
slot). The facade's confidence gate now also checks a new
`unresolved_identity_starter_count` (previously any unmatched-but-pointed
starter fell through to a falsely NOMINAL confidence).

**Real, live, follow-up finding caught only by testing this fix against
real data (Fantasy Gamers' real Week 2 roster):** a naive
`identity_match != "MATCHED"` check flagged K and DST as
"UNRESOLVED_IDENTITY" on EVERY real request, because NWR's governed
ranking has ZERO K/DST rows BY DESIGN (matching an already-established
distinction elsewhere in this codebase, `waiver_engine_service.py`'s own
`_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS`) -- not a real identity failure.
Left unfixed, this would have made confidence permanently LOW for nearly
every real league (any league starting a K or DST). Fixed with the same
carve-out (`_OUT_OF_RANKED_MODEL_SCOPE_POSITIONS = {"K", "DST"}`, defined
locally in `weekly_lineup_optimizer_service.py` to avoid a cross-service
import for two literal strings). Re-verified live after the fix: Fantasy
Gamers' real K (Ka'imi Fairbairn) and DST (NE D/ST) both show `status:
"OK"`, `unresolvedIdentityStarterCount: 0`, `confidenceState: "NOMINAL"`.

### W4 — swap-set correctness, Already-optimal derivation — INSPECTED CODE
+ ACTUAL TEST RESULT + LIVE OBSERVATION

Replaced the old per-slot-type `_swap_reasons` heuristic (which searched
the WHOLE bench independently for each new starter's slot type, causing
both the duplicate-sit bug and the disappearing-FLEX-swap bug) with a
real before/after starter-ID-set diff: `newly_started_ids = after - before`,
`benched_pool = before - after` (each real former starter used at most
once, removed from the pool once matched), same-slot-type preferred for
the pairing, falling back to whichever real former starter is still
unaccounted for otherwise (the exact FLEX-rearrangement case). "Already
optimal" is now structurally correct: it is exactly the case where
`newly_started_ids` is empty (no real membership change in the starting
SET), never just "the old heuristic happened to emit nothing."

**Real, live proof:** Fantasy Gamers' real Week 2 lineup showed exactly 1
real, correctly-computed swap ("START Michael Pittman over Zay Flowers,
+11.7 projected"), rendered correctly in the browser's "Recommended
changes" panel.

### A second real bug found + fixed while verifying live (not in the
original W1-W4 list) — INSPECTED CODE + ACTUAL TEST RESULT + LIVE
OBSERVATION

The new `gameLock.kickoffUtcByTeam` field, first shipped as a
`dict[team_code, kickoff_iso]`, was silently corrupted by the shared
desktop API camelCase JSON-key transform (`camel_case_key` in
`src/application/contracts.py`), which treats EVERY dict key as a schema
field name and lowercases its first character -- "BUF" became "bUF" in
the real live API response, confirmed by a real curl against the running
backend. This is the SAME already-documented hazard this codebase has hit
before (see `desktop_facade.py`'s own K/DST `positions`-flattening
comments) -- fixed the same established way: `kickoffUtcByTeam` is now a
flat list of `{team, kickoffUtc}` objects, not a dict keyed by team code.
Regression test added (`test_to_dict_kickoff_map_is_a_flat_list_not_a_
team_keyed_dict`). Re-verified live after the fix: real team codes
(`ARI`, `ATL`, `BAL`, ...) now render correctly.

### The 5 regression fixtures — ACTUAL TEST RESULT (failing-before,
documented in each test's own comment against the pre-fix source;
passing-after, actually run)

All 5 written exactly as the brief specified, plus 3 extra sub-case tests
(catalog-name-resolution for a missing-projection player, locked-bench
exclusion, and the K/DST carve-out), in
`tests/test_weekly_lineup_optimizer_service.py`:

1. `test_regression_fixture_1_duplicate_sits_produces_one_correct_swap_set`
   -- A=10/B=9 starting, C=20/D=19 bench, 2 RB slots. PASSES: started set
   {C,D}, total 39.0, exactly one swap per real displaced player (A and B
   each named once, never duplicated), summed displayed deltas = 20.0
   (real total gain), matching the brief's exact numbers.
2. `test_regression_fixture_2_flex_rearrangement_no_longer_disappears` --
   RB10/WR20/WR5(FLEX) starting, RB15 bench, RB/WR/FLEX slots. PASSES:
   started set {WR20,RB15,RB10}, total 45.0, >=1 real swap emitted
   (RB15 over WR5), never "Already optimal."
3. `test_regression_fixture_3_missing_starter_counts_as_unprojected_not_
   silently_dropped` -- a starter id with zero rows anywhere in
   `projection_rows`. PASSES: candidate is kept (not silently dropped),
   slot status EMPTY, `unprojected_starter_count == 1` (was 0 before the
   fix).
4. `test_regression_fixture_4_unmatched_identity_not_promoted_to_ok` -- an
   UNMATCHED RB with 10 projected points, only candidate for 1 RB slot.
   PASSES: `status == "UNRESOLVED_IDENTITY"`, never `"OK"`,
   `unresolved_identity_starter_count == 1`, points still counted
   (10.0) -- a status-label fix, not a silent zeroing.
5. `test_regression_fixture_5a/5b/5c_...` -- 5a: a 20-pt reserve candidate
   does NOT beat a 10-pt active starter (reserve excluded from normal
   selection). 5b: a 10-pt LOCKED starter is NOT swapped for a 20-pt bench
   candidate (locked starters pinned). 5c: a locked, non-starting bench
   player is NOT newly started even as the only candidate for an open slot
   (slot stays real, visible EMPTY). All PASS.

### TESTS — ACTUAL TEST RESULT

- `tests/test_weekly_lineup_optimizer_service.py`: **7 -> 16 tests, all
  pass** (7 pre-existing unchanged + 1 K/DST-carve-out regression + 8 new
  fixture/sub-case regressions).
- New `tests/test_weekly_game_lock_service.py`: **4 tests, all pass**
  (real kickoff-lock computation, fetch-failure honesty, missing-gametime
  honesty, the camelCase flat-list regression).
- Full brief-listed backend suite re-run after every change (262 tests
  total across `test_weekly_lineup_optimizer_service`,
  `test_weekly_game_lock_service`, `test_weekly_projection_service`,
  `test_weekly_projection_provider_service`,
  `test_fantasypros_kdst_consensus_service`,
  `test_redraft_waivers_ir_reserve_drop_exclusion_fix`,
  `test_redraft_waivers_faab_context_fix`,
  `test_redraft_waivers_open_slot_and_same_context_fix`,
  `test_weekly_home_single_snapshot`, `test_weekly_home_sleeper_fetch_
  caching`, `test_desktop_facade_architecture_wiring`,
  `test_player_availability_status_consumer_consistency`,
  `test_dynasty_sleeper_league_service`, `test_dynasty_league_import_
  facade_wiring`, `test_boundary_property_reliability_pack_v1`,
  `test_prospective_outcome_ingestion_orchestrator_v1_service`): **262
  passed, 0 failed.**
- Frontend: `npm run typecheck` (both apps) -- clean, 0 errors. Full
  `npx vitest run` (desktop workspace, all 30 test files): **492 passed,
  0 failed** (up from the pre-existing baseline by the new/modified
  assertions in `weekly-shared.test.ts`; no other file's test count
  changed).
- A benign, unrelated side effect of running the full vitest suite
  (`docs/codex/prospective_outcomes_v1/multi_league_scale_v1/frontend_
  bench_results.json`, a perf-benchmark's own timing-noise output file)
  was reverted with `git checkout --` before committing -- not a real
  change, not part of this pass.

### LIVE VERIFICATION -- LIVE OBSERVATION

Restarted the Redraft dev pair TWICE this pass (once after the initial
W1-W4 code changes, once more after the K/DST-carve-out + camelCase-map
fixes) -- the pre-existing PIDs (31352/16376, confirmed pre-HEAD-code by
Worker 1) were stopped, a real `npm run build` was run for
`desktop/apps/redraft`, and a fresh backend+`vite preview` pair was
started on the same ports (18742/1422). Also ran the repo's own
`desktop/scripts/nwr_release_gate_smoke.ps1 -Mode redraft -KeepRunning
-SleeperLeagueId 1312983576827920384 -SleeperUsername scolety` once (real
`check:resources` PASS, real `cargo check` PASS, real production build,
real read-only Sleeper before/after byte-diff -- IDENTICAL, 0 writes
confirmed, all surface-smoke endpoints 200 including `weekly_lineup_week1`
and `weekly_home_actions_week1`).

Real Chrome MCP browser session against the rebuilt+restarted app,
active profile Fantasy Gamers:
- Start/Sit (`#/league/941b.../lineup`): "NFL WEEK (AUTO)" showed `2`
  immediately; title "Start / Sit — THIS WEEK (Week 2)"; "1 CHANGE vs.
  Sleeper's current starters" -- "Start Michael Pittman over Zay Flowers,
  +11.7 projected points," correctly rendered; all 9 starters showed
  status OK (including K/DST, post-carve-out-fix); bench showed 6 real
  players. No console errors.
- Improve Team Targets tab, THIS_WEEK mode: "NFL WEEK" auto-populated to
  `2`; "LIVE · Weekly projections: SLEEPER · Week 2."
- Improve Team Streamers tab: "NFL WEEK" also auto-populated to `2`.
- Confirmed via the real "Switch league" dropdown that Las Vegas
  Enginerds is genuinely NOT a Redraft profile (only 5: 10-team 1QB
  Standard, KHA, 403 N 18th, Fantasy Gamers, Isolation Check Local) --
  matches Worker 1's finding exactly; making Enginerds usable in Redraft
  is brief section 4, explicitly out of this Worker's scope, not
  attempted.
- Zero writes: every live call this pass was a plain GET (schedules,
  Sleeper league/rosters/users/players/projections) or a read against the
  local backend's own read-only endpoints; the smoke script's own
  before/after Sleeper byte-diff independently confirms zero writes.

### SCHEDULE/LOCK DATA -- INSPECTED CODE + LIVE OBSERVATION

`nflreadpy.load_schedules(seasons=[season])` real columns confirmed this
pass (not assumed): `game_id`, `home_team`, `away_team`, `gameday` (date),
`gametime` (Eastern Time local kickoff, e.g. "13:00"), `weekday`,
`game_type`. Real live pull, real Week 2 2026 data, real spot-check:
Thursday's BUF@DET game (2026-09-17 20:15 ET) correctly computed as
already-locked as of this pass's real wall-clock time; Sunday's games
(2026-09-20) correctly computed as not yet locked. `injury_availability_
context_service.py`'s own separate next-game/opponent/bye gate was
deliberately left untouched -- not opened, not needed for this narrow
lock-state requirement.

### REDRAFT PROCESSES STATUS

Currently running (as of this entry): backend on port 18742, `vite
preview` on port 1422, both serving this pass's final HEAD (verified via
a fresh `npm run build` + restart, not just a process check). Dynasty's
backend/frontend were NOT touched this pass (per this Worker's own scope
-- Redraft only); still the pre-HEAD processes Worker 1 flagged, still
need a restart before any worker relies on Dynasty's live HEAD parity.

### FILES CHANGED

- `src/services/weekly_lineup_optimizer_service.py` (rewritten: reserve/
  taxi/lock inputs, missing-projection-row retention, K/DST identity
  carve-out, diff-based swap reasons).
- `src/services/weekly_game_lock_service.py` (new).
- `src/application/desktop_facade.py` (`redraft_weekly_lineup`: game-lock
  call, reserve/taxi/catalog wiring, confidence gate, new response
  fields).
- `desktop/apps/redraft/src/weekly-shared.tsx` (`useProviderWeek`/
  `useWeekSelection` hooks, `statusTone` UNRESOLVED_IDENTITY fix).
- `desktop/apps/redraft/src/in-season.tsx` (`WeeklyHomePage` refactored
  onto the shared hooks; `LineupPage` W1 fix + reserve/locked-unavailable
  panels).
- `desktop/apps/redraft/src/improve-team.tsx` (waiver week + streamer
  week W1 fix).
- `desktop/packages/contracts/src/index.ts` (new `WeeklyLineupCoverageEntry`/
  `WeeklyGameLockInfo` types, `WeeklyLineupResult` additive fields).
- `tests/test_weekly_lineup_optimizer_service.py` (9 new tests).
- `tests/test_weekly_game_lock_service.py` (new, 4 tests).
- `desktop/apps/redraft/src/weekly-shared.test.ts` (1 new assertion).

### OPEN ISSUES FOR WORKER 3 (W5-W7: waivers/streamers/K-DST scoring)

1. **The real `waiver_type` FAAB-detection bug Worker 1 flagged is still
   unfixed** (`desktop_facade.py` checks `raw_waiver_type == 1`; strong
   third-party evidence says real Sleeper FAAB is `waiver_type == 2` --
   backwards for both Fantasy Gamers (`waiver_type=1`) and Enginerds
   (`waiver_type=2`) specifically). Not touched this pass (out of W1-W4
   scope) -- needs a deliberate, verified decision before/alongside W5/W7.
2. **W5 (THIS_WEEK sort authority) and W7 (K/DST league-specific scoring)
   are untouched** -- this pass only fixed the LINEUP optimizer's own
   internal correctness; `waiver_engine_service.py`'s season-based sort
   and `weekly_projection_service.py`'s provider-points-only K/DST scoring
   are real, separate, already-diagnosed gaps for Worker 3.
3. **`redraft_weekly_lineup`'s new `unresolvedIdentityStarterCount` /
   `reserve` / `lockedUnavailable` fields are additive-only in the
   `WeeklyLineupResult` contract** (`?:` optional) -- any NEW consumer
   Worker 3 builds (e.g. a THIS_WEEK waiver evaluation that calls into
   this same lineup optimizer per the brief's W5 fix) should read them,
   not silently ignore them, per the same distinctness principle this
   pass established.
4. **This pass's live verification used Fantasy Gamers only** (real
   browser session). Enginerds is NOT a Redraft profile at all yet
   (confirmed live this pass) -- Worker 3/4 building Enginerds' Redraft
   weekly-decision surface (brief section 4) will need to exercise this
   same lineup-optimizer path fresh against Enginerds' real non-PPR,
   no-DST scoring once that profile exists; not verified this pass.
5. **`weekly_game_lock_service.py` is new and only consumed by
   `redraft_weekly_lineup` so far** -- if Worker 3's W5 THIS_WEEK
   evaluation needs lock state too (the brief asks for "the same inputs
   and locks" as Start/Sit), reuse this same module/result rather than
   building a second kickoff lookup.
6. **KHA and 403 N 18th remain BLOCKED** for any current-state Sunday
   tool (unchanged from Worker 1 -- no ESPN client exists). Not this
   Worker's concern, re-confirmed only incidentally via the live "Switch
   league" dropdown screenshot.

---

## Worker 3 -- Fix W5-W7: pickups and streamers that can help now
(2026-09-18, ~7:58-8:43 PM Mountain)

Time check: started ~7:58 PM Mountain (~16h02m remaining), finished this
entry ~8:43 PM (~15h17m remaining). No deadline risk.

### CRITICAL FIRST TASK -- FAAB `waiver_type` verification -- INSPECTED CODE
+ LIVE OBSERVATION (WebFetch/WebSearch, real, this pass)

Independently re-verified Worker 1's flag before touching any code, per the
brief's explicit instruction not to flip the check on unverified third-party
claims alone:

- **Sleeper's own official docs (`docs.sleeper.com`) do not document
  `waiver_type` at all** -- confirmed fresh via a real `WebFetch` this pass
  (not just cited from Worker 1).
- **Independent source 1 (third-party code, re-confirmed):**
  `github.com/jdguggs10/flaim` PR #294 defines `SLEEPER_WAIVER_TYPE_FAAB = 2`
  with an explicit comment: "0 = rolling waivers, 1 = reverse standings,
  2 = FAAB (undocumented community convention)."
- **Independent source 2 (NEW this pass, not in Worker 1's citation):**
  Sleeper's own real, public support article ("What types of waivers do you
  support?", `support.sleeper.com/en/articles/1876041`) lists the three real
  waiver systems in this exact order -- Rolling Waivers ("the default
  setting"), Reverse Standings, then FAAB Bidding -- independently matching
  the third-party enum's 0/1/2 ordering. Two independent sources converging
  on the same three-way ordering is real corroboration, though neither
  alone is an explicit official "waiver_type: 2 = FAAB" statement -- this is
  high-confidence verified evidence, not absolute certainty.
- **Verdict: the code WAS backwards.** Fixed `desktop_facade.py`'s
  `is_faab_league = raw_waiver_type == 1` to `== 2`. Real consequence for
  both actual leagues: Fantasy Gamers (`waiver_type=1`, real reverse-
  standings-priority, NOT FAAB) was wrongly computed as FAAB before this
  fix; Enginerds (`waiver_type=2`, real FAAB) was wrongly computed as NOT
  FAAB. Both now correct.
- **LIVE OBSERVATION, this pass:** a real `redraft_waivers(mode="THIS_WEEK")`
  call against the real running Fantasy Gamers league returned
  `"isFaabLeague": false` (previously would have been `true`) -- confirmed
  directly, not just unit-tested.
- Updated 6 pre-existing test fixtures across `test_redraft_waivers_faab_
  context_fix.py` and `test_redraft_waivers_decision_trace_completeness_
  fix.py` that had encoded the same backwards assumption (`waiver_type: 1`
  meaning FAAB); added a new regression test
  (`test_faab_context_treats_reverse_standings_waiver_type_as_non_faab_too`)
  locking in the corrected 3-value enum.

### W5 -- wrong weekly authority -- INSPECTED CODE + ACTUAL TEST RESULT +
LIVE OBSERVATION

Root cause confirmed exactly as the brief described:
`waiver_engine_service.rank_waiver_candidates`'s THIS_WEEK sort key was
`(marginal_utility is None, -marginal_utility, weekly_points is None,
-weekly_points)` -- season utility primary, weekly points only a tiebreak.
`becomes_starter` on `WaiverCandidate` was always `marginal_roster_
utility_v2`'s own season-long flag, never recomputed from any real weekly
lineup evaluation, while the frontend (`AddDropDetail`, `explainWaiverTarget`)
claimed it reflected "this week."

**Fix:** new `weekly_lineup_optimizer_service.simulate_this_week_add_drop`
(+ `ThisWeekAddDropImpact`) evaluates one real candidate acquisition (paired
with the SAME real weakest-drop candidate the ROS Add/Drop pairing already
computes, or no drop when a real open non-reserve slot exists) by calling
the UNMODIFIED `optimize_weekly_lineup` (W2-W4's own fixed optimizer) TWICE
-- once against the roster as-is, once against the roster after the
hypothetical transaction -- and diffing `projected_total`. `desktop_facade.
py`'s `redraft_waivers` THIS_WEEK branch now builds the owner's real roster
candidates (same `build_roster_candidates` call shape as `redraft_weekly_
lineup`, reusing `weekly_game_lock_service.compute_weekly_game_lock` for
locks -- not re-derived) and runs this evaluation for a real, disclosed,
bounded shortlist (top 60 free agents by raw weekly points -- raw points
used ONLY to pick which candidates get a real full evaluation, never as the
final ranking signal). `rank_waiver_candidates` gained an optional
`this_week_impact_by_sleeper_id` map: when supplied, THIS_WEEK sorts
PRIMARILY by real `.gain`, falling back to the old utility-based order for
any candidate outside the evaluated shortlist (never a fabricated gain).
`WaiverCandidate` gained `this_week_lineup_gain` / `this_week_becomes_
starter` / `this_week_evaluated` -- the season-long `becomes_starter` field
is preserved unchanged for REST_OF_SEASON. The facade's `_candidate_payload`
now emits `becomesStarter` = the real weekly-evaluated flag (or `null`,
never silently defaulted) in THIS_WEEK mode, plus a new `becomesStarterBasis`
field consumers can check. Frontend (`in-season.tsx`'s `AddDropDetail`,
`improve-team.tsx`'s real `addColumns` -- see live-verification note below
-- and `improve-team-explain.ts`'s `explainWaiverTarget`) updated to read
`becomesStarterBasis` and never treat a `null` `becomesStarter` as a false
"would not start."

**A real, live-caught bug in my own first pass, found only by browser-
verifying, not just unit-testing:** I initially edited `addColumns`/
`AddDropDetail`-adjacent text in `in-season.tsx`'s `WaiversPage` -- but that
page is explicitly documented in its own comments as "an unrouted legacy
fallback (superseded by Improve Team's FAAB tab)." The REAL, routed surface
the owner uses is `improve-team.tsx`'s own separate `addColumns`/caption
text, which I had NOT yet fixed. Caught this by live-browsing the actual
Improve Team page and seeing the old "MARGINAL UTILITY" column label /
season-utility-scrambled row order still rendering despite my backend fix
being live and correct. Fixed `improve-team.tsx`'s real `addColumns` (added
a "This week usable gain" column, relabeled "Marginal utility" ->
"Season utility (long-term)" in THIS_WEEK mode, fixed the `becomesStarter`
Yes/No/Unknown rendering) and `improve-team-explain.ts`'s `explainWaiverTarget`
(the real Targets-tab card generator -- same null-treated-as-false bug,
now fixed with the same three-way basis check). Kept the `in-season.tsx`
edits too (harmless, consistent, still dead code).

**Preserved, LEDGER-relevant, HARD BOUNDARY respected:** `marginal_roster_
utility_v2` itself and its weights were never touched -- `simulate_this_
week_add_drop` only calls the pre-existing, unmodified `optimize_weekly_
lineup`.

### W6 -- streamer downgrade bug -- INSPECTED CODE + ACTUAL TEST RESULT +
LIVE OBSERVATION

Root cause confirmed exactly as the brief described: `desktop_facade.py`'s
`redraft_kdst_streamer` picked `top_action = add_action or (actions[0] if
actions else None)` -- ALWAYS preferring the best-ECR unrostered ("ADD")
row over the owner's own better-ranked starter, regardless of relative
merit. **Fix:** since `sleeper_streamer_actions`' own output is already
ECR-sorted ascending, `top_action` is now the FIRST row whose
`recommendation` is genuinely actionable (`START` / `HOLD` / `ADD` --
`ROSTERED_ELSEWHERE`, an opponent's real roster, correctly still excluded,
unchanged). This makes KEEP CURRENT (`START`) a genuinely reachable primary
result whenever the owner's own starter really is the best real, accessible
option -- verified by a dedicated regression test constructing exactly the
brief's fixture (owned ECR1 vs free ECR10) and asserting `START`/
`YOUR_STARTER` wins, plus a companion test proving a genuine upgrade still
recommends `ADD` (no overcorrection), plus a test proving an opponent's
best-ECR row is never primary.

**Second real bug in the same function, also fixed:** `redraft_weekly_home_
actions`' own STREAMER action-board loop independently re-derived "first ADD
row" from the flat `positions` list (a SEPARATE manifestation of the same
downgrade bug, since it never checked ownership either) -- fixed by having
it reuse `redraft_kdst_streamer`'s own already-corrected `decisionEnvelopes[]
.decisionEnvelope.primaryRecommendation` instead of re-deriving. Updated
2 existing tests in `test_weekly_home_single_snapshot.py` whose fixtures
had `decisionEnvelopes: []` (never realistic) while `positions` carried the
real payload -- now the reverse, matching what this loop actually reads.

**Position-configuration enforcement (also W7-adjacent, "never recommend a
DST pickup for Enginerds"):** `redraft_kdst_streamer` never checked
`selected.roster.k`/`selected.roster.dst` at all before this pass -- it
always queried and offered both K and DST regardless of real league roster
shape. Fixed: a position with `0` real roster slots is skipped entirely
(FantasyPros consensus for that position is never even requested), and the
decision envelope honestly reports "This league has no {position} roster
slot" rather than a generic "no candidates" message. **Verified via a
dedicated test** (`test_never_recommends_a_dst_pickup_for_a_league_with_no_
dst_slot`) that DST consensus is literally never called when `roster.dst
== 0`. Las Vegas Enginerds itself is NOT YET a Redraft profile (Worker 2
reconfirmed this live), so this guard could not be live-verified against
Enginerds directly this pass -- **Worker 4, when building the Enginerds
Redraft surface, should live-verify this guard fires for Enginerds' real
`roster.dst == 0`** once that profile exists.

**3 existing tests broke and were fixed, not papered over:** `test_kdst_
streamer_returns_a_real_decision_envelope_per_position` (`test_decision_
envelope_consumer_migration.py`), `test_kdst_streamer_response_carries_
trace_ids_and_league_snapshot_id` (`test_desktop_facade_architecture_
wiring.py`), and `test_redraft_kdst_streamer_records_a_decision_trace_for_
k_and_dst` (`test_desktop_application_api.py`) all built their synthetic
profile from a builtin preset whose `RosterSettings` defaults to `k=0,
dst=0` -- a real, previously-invisible gap the position-config fix exposed.
Fixed by explicitly setting `roster=replace(profile.roster, k=1, dst=1)`
in each fixture (matching a real K/DST-using league's actual shape, e.g.
Fantasy Gamers' real `k=1, dst=1`), not by weakening the new guard.

**Frontend:** `improve-team-explain.ts`'s `STREAMER_VERB` map changed
`START: "START"` -> `START: "KEEP"` so a real keep-current recommendation
reads as one in the UI headline ("KEEP Ka'imi Fairbairn (K)", not "START").

### W7 -- K/DST scoring not custom -- INSPECTED CODE + ACTUAL TEST RESULT +
LIVE OBSERVATION

Root cause confirmed exactly as the brief described:
`weekly_projection_service._score_row` used `raw.get("pts_ppr")` for every
K/DST row, unconditionally -- the league's real per-tier scoring settings
were never read at all for weekly K/DST scoring (contrast: `redraft_engine_
v1_service.ScoringSettings`, the SEASON-LONG governed formula, has no K/DST
stat-based scoring concept whatsoever by design -- it expects a governed
point override -- so this weekly gap was a separate, narrower, genuinely
new lane, not a duplicate of the frozen season model; the HARD BOUNDARY
against touching `ScoringSettings`/`score_projection`/`marginal_roster_
utility_v2` was respected throughout).

**Real raw-data investigation this pass (LIVE OBSERVATION, a real `GET
projections/nfl/regular/2026/2` pull, ~9400 players, and a real `GET
players/nfl` pull):** confirmed Sleeper's real weekly-projection payload
DOES carry real per-tier kicker fields (`fgm_0_19`, `fgm_20_29`,
`fgm_30_39`, `fgm_40_49`, `xpm`, `xpmiss`) and real DST fields (`sack`,
`int`, `fum_rec`, `ff`, `safe`, `blk_kick`, `def_td`, and real `pts_allow_*`
tier buckets) -- confirmed this is genuinely computable, not just a
disclosed gap. Also confirmed, by scanning EVERY key across the entire real
payload (not one row): there is NO raw 50-59/60+ yard field-goal breakout
anywhere in the payload -- a real, structural, permanent gap for any league
scoring that tier (Enginerds' real `fgm_50p: 4.0`, Fantasy Gamers' real
`fgm_50_59`/`fgm_60p`), never approximated by subtraction.

**Fix:** new `weekly_projection_service._score_kdst_from_raw_sleeper_
scoring` computes a real dot product of the league's own raw `scoring_
settings` map (fetched fresh from `GET league/{id}`, the SAME top-level
`scoring_settings` field, sibling to `settings` -- confirmed via a real
live pull this pass, not assumed nested) against this row's real raw stat
values, for every known K/DST category. A real, nonzero-weighted category
with no raw support is disclosed (`unsupported_scoring_categories`), never
silently dropped or approximated -- labeled `NWR_LEAGUE_SCORING_KDST_
WEEKLY_PARTIAL` (vs. `..._KDST_WEEKLY` when fully exact, vs. unchanged
`SLEEPER_PROVIDER_SCORING` when the league map is unavailable/has no real
overlap at all). **A real design bug caught and fixed before it shipped:**
Sleeper's real DST payload only ever emits the ONE `pts_allow_*`/`yds_
allow_*` bucket a team's projection actually lands in (e.g. `pts_allow_
21_27: 1.0` alone, no sibling keys) -- a naive per-key check would have
flagged every OTHER real bucket as "unsupported" on every real DST row,
pure false-positive noise. Fixed with family-aware matching
(`_DST_MUTUALLY_EXCLUSIVE_FAMILIES`): once ANY real bucket in a family is
confirmed present, every other same-family bucket is a real, honest zero,
not a gap.

`RosterCandidate` (optimizer), `WeeklyLineupResult`'s starter/bench JSON,
and the API response gained `scoringContext`/`unsupportedScoringCategories`
per player, plus a new top-level `nonExactScoringInTotal` flag on `redraft_
weekly_lineup`'s response (real, true only when a starter that actually
contributed to `projectedTotal` was scored non-exactly). Frontend (`in-
season.tsx`'s `LineupPage`) shows a real disclosure caption when true, and
a `title` tooltip with the real scoring context per starter.

**LIVE OBSERVATION, this pass, against real Fantasy Gamers Week 2 data**
(via both a direct authenticated API call and the real rendered browser
page): `nonExactScoringInTotal: true`; Ka'imi Fairbairn (K) scored `7.27`
under `NWR_LEAGUE_SCORING_KDST_WEEKLY_PARTIAL`, real disclosed gaps
`['fgm_0_19', 'fgm_50_59', 'fgm_60p', 'fgmiss']` (his real raw projection
row that week genuinely omitted the `fgm_0_19` key entirely, not just
valued it zero -- a real, live-confirmed nuance, not a bug); NE D/ST scored
`8.62` under the same partial label, real disclosed gap `['safe']`. The
Start/Sit page's real disclosure banner rendered live: "This total includes
at least one player scored by generic provider points or a partial
league-scoring match...".

### The 3 mandatory regression fixtures -- ACTUAL TEST RESULT

1. **Fixture 6 (downgrade streamer):** `tests/test_redraft_kdst_streamer_
   keep_current_fix.py::test_regression_fixture_6_owned_ecr1_starter_beats_
   a_free_ecr10_kicker_keep_current_wins` -- owned K at real ECR1, free K
   at real ECR10. PASSES: primary recommendation is `START`/`YOUR_STARTER`
   (Owned Kicker), not the worse-ranked `ADD`. 3 companion tests also pass
   (genuine-upgrade-still-works, opponent-never-primary, no-DST-slot
   enforcement).
2. **Fixture 7 (wrong weekly authority):** `tests/test_waiver_engine_
   service.py`'s `test_regression_fixture_7a/7b/7c_*` -- utility 180.0 vs
   60.0 (same qualitative shape as the brief's "10 vs 9"), weekly points
   1.0 vs 20.0 exactly as specified. 7a documents the honest pre-fix
   fallback ordering (utility-primary, still reachable when no real impact
   map is supplied). 7b PASSES the real fix: with a real impact map
   supplied (gain 0.5 vs 15.0), the lower-season-utility/higher-weekly-
   points candidate now sorts first, and `this_week_becomes_starter` is
   shown to be genuinely independent of (and different from) the unchanged
   season `becomes_starter` flag for the same candidate. 7c PASSES: a
   candidate outside the impact map reports `this_week_evaluated=False`/
   `this_week_becomes_starter=None`, never silently defaulted.
3. **Fixture 8 (kicker scoring boundary):** `tests/test_weekly_projection_
   service.py`'s `test_regression_fixture_8a/8b/8c/8d_*` -- 8a documents
   the honest pre-fix fallback (raw provider 9.0 regardless of league
   weights, when no league scoring map supplied). 8b PASSES the exact
   brief number: three made 20-29-yard goals at Enginerds' real captured
   2.0/each tier score exactly `6.0`, with the real, disclosed
   `fgm_50p` gap (never silently dropped). 8c PASSES: a fully-supported
   kicker (Fantasy Gamers-style, no 50+ tier configured at all) reports the
   EXACT (not partial) label with zero unsupported categories. 8d PASSES:
   the same real fix applied to DST (sack/int/pts_allow_7_13), including
   the family-aware points-allowed-tier fix.

### LIVE VERIFICATION -- LIVE OBSERVATION

Rebuilt Redraft frontend twice (`npm run build --workspace @nwr/redraft-
desktop`) and restarted the backend with real startup credentials
(`nwr-desktop-development-token-only-000000000000`, matching the frontend's
own real dev-default, piped via stdin the same way `nwr_release_gate_smoke.
ps1` does) after the W1-W4-era PIDs Worker 2 left running were stopped.
Real Chrome MCP session against the rebuilt+restarted app, active profile
Fantasy Gamers, real Week 2:

- Start/Sit: real `nonExactScoringInTotal` disclosure banner rendered;
  real K/DST partial-scoring context confirmed via a direct authenticated
  API call (see W7 above); zero console errors.
- Improve Team -> Targets (THIS_WEEK): "ADD Brock Purdy / DROP Marvin
  Harrison" now the real #1 target, "THIS WEEK: Projected to become a
  starter this week (real legal-lineup gain: 2.3 pts)." -- matches the
  direct API call's `thisWeekLineupGain: 2.34` exactly.
- Improve Team -> Add/Drop (THIS_WEEK): real "SEASON UTILITY (LONG-TERM)"
  and "THIS WEEK USABLE GAIN" columns rendered; row order genuinely
  gain-sorted (2.3, 1.0, 0.7, 0.5, 0.2, 0.1, 0.0...), NOT utility-sorted
  (utility column itself jumbled: -1.7, -8.1, 5.4, --, 5.5, 0.0, 5.6...);
  "BECOMES STARTER" correctly Yes/No per real gain>0; Add/Drop detail
  drawer text matches the table exactly. **A real bug in my own first
  implementation pass was caught here** (see W5 above -- initially fixed
  the wrong, unrouted `in-season.tsx` page instead of the real routed
  `improve-team.tsx`) and corrected before this entry was written.
- Improve Team -> Streamers (THIS_WEEK): real "ADD San Francisco 49ers
  (DST)" / "ADD Eddy Pineiro (K)" primary cards rendered (genuine upgrades
  over the owner's real, lower-ranked current K/DST this specific week --
  a live case of the owner's OWN starter beating all options did not occur
  naturally in this week's real data, so KEEP/START-as-primary was
  verified by dedicated unit test, not a live screenshot, this pass);
  "Brandon Aubrey ... ROSTERED ELSEWHERE" confirmed correctly excluded
  from any primary/ADD selection.
- Zero console errors across the whole session (checked via `read_console_
  messages`, `onlyErrors: true`, after page loads/interactions).
- Zero writes: every call this pass was a plain GET (Sleeper rosters/
  players/state/league, FantasyPros consensus) or a read against the
  backend's own read-only endpoints; every response carried
  `"writeBehavior": "NO_SLEEPER_WRITES"` (or the K/DST-specific
  `NO_SLEEPER_WRITES_NO_FANTASYPROS_WRITES`).

### TESTS -- ACTUAL TEST RESULT

- Brief-listed suite (`test_weekly_lineup_optimizer_service`, `test_weekly_
  projection_service`, `test_weekly_projection_provider_service`, `test_
  fantasypros_kdst_consensus_service`, `test_redraft_waivers_ir_reserve_
  drop_exclusion_fix`, `test_redraft_waivers_faab_context_fix`, `test_
  redraft_waivers_open_slot_and_same_context_fix`) plus this pass's own
  additions/touched files (`test_waiver_engine_service`, new `test_redraft_
  kdst_streamer_keep_current_fix`, `test_weekly_home_single_snapshot`,
  `test_weekly_home_sleeper_fetch_caching`, `test_decision_envelope_
  consumer_migration`, `test_desktop_facade_architecture_wiring`, `test_
  redraft_waivers_decision_trace_completeness_fix`, `test_redraft_waivers_
  unmatched_identity_rationale_fix`, `test_dynasty_sleeper_league_service`,
  `test_dynasty_league_import_facade_wiring`, `test_desktop_application_
  api`): **235 passed, 4 failed** -- the failures are the SAME 4 pre-
  existing, HEAD-baseline failures confirmed via a real `git stash`/re-run
  comparison this pass (`test_dynasty_facade_composes_real_governed_
  workflows`, `test_desktop_rookie_veteran_bridge_is_source_separated_and_
  trade_aware`, `test_redraft_bootstrap_seeds_once_and_matches_desktop_
  contract`, `test_facade_has_no_streamlit_or_app_component_dependency`),
  unrelated to this pass's changes, not waived without evidence.
- Frontend: `npm run typecheck` (both apps) -- clean, 0 errors, checked
  after every meaningful edit round. Full `npx vitest run`: **493 passed,
  0 failed** (up from Worker 2's 492 baseline by 1 new regression test in
  `improve-team-explain.test.ts`).
- `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/frontend_bench_
  results.json`'s own benign perf-timing-noise churn (same known side
  effect Worker 2 also hit) was reverted with `git checkout --` before
  finishing -- not a real change.

### REDRAFT PROCESSES STATUS

Restarted twice this pass (once for the backend/first frontend build, once
more after catching and fixing the `improve-team.tsx` bug found during live
verification): backend on port 18742 (fresh PID, real startup credentials),
`vite preview` on port 1422, both confirmed serving this pass's final HEAD
via a live browser session immediately before this entry was written.
Dynasty's dev pair was NOT touched this pass (out of scope; still whatever
state Worker 1/2 left it in -- see their own entries).

### FILES CHANGED

- `src/application/desktop_facade.py` (FAAB `waiver_type` fix; W5 THIS_WEEK
  impact-evaluation wiring in `redraft_waivers`, moved `drop_candidates`
  computation earlier for reuse; W6 `top_action`/position-config fix and
  Weekly Home STREAMER-loop fix in `redraft_kdst_streamer`/`redraft_
  weekly_home_actions`; W7 `sleeper_scoring_settings` wiring in both
  `redraft_weekly_lineup` and `redraft_waivers`, new `nonExactScoringInTotal`
  / per-player `scoringContext` response fields).
- `src/services/waiver_engine_service.py` (W5: `this_week_impact_by_sleeper_
  id` param + new sort key on `rank_waiver_candidates`; new `WaiverCandidate`
  fields).
- `src/services/weekly_lineup_optimizer_service.py` (W5: new `simulate_
  this_week_add_drop`/`ThisWeekAddDropImpact`; W7: `scoring_context`/
  `unsupported_scoring_categories` threaded onto `RosterCandidate`).
- `src/services/weekly_projection_service.py` (W7: new `_score_kdst_from_
  raw_sleeper_scoring`, `_KICKER_KNOWN_SCORING_CATEGORIES`, `_DST_KNOWN_
  SCORING_CATEGORIES`, `_DST_MUTUALLY_EXCLUSIVE_FAMILIES`; `_score_row`/
  `build_weekly_projection_rows` gained `sleeper_scoring_settings` param;
  `WeeklyProjectionRow` gained `unsupported_scoring_categories`).
- `desktop/packages/contracts/src/index.ts` (new optional fields on
  `WeeklyLineupSlotPlayer`/`WeeklyLineupBenchPlayer`/`WeeklyLineupResult`/
  `WaiverAddCandidate`).
- `desktop/apps/redraft/src/improve-team.tsx` (real, routed `addColumns`
  W5 fix; THIS_WEEK caption text fix).
- `desktop/apps/redraft/src/improve-team-explain.ts` (`explainWaiverTarget`
  W5 null-safety fix; `STREAMER_VERB` W6 KEEP label).
- `desktop/apps/redraft/src/in-season.tsx` (`AddDropDetail` W5 null-safety
  fix; `LineupPage` W7 disclosure banner + per-player scoring-context
  tooltip; legacy/unrouted `WaiversPage`'s `addColumns`/caption kept
  consistent though dead code).
- `tests/test_redraft_waivers_faab_context_fix.py`,
  `tests/test_redraft_waivers_decision_trace_completeness_fix.py` (waiver_
  type 1->2 fixture corrections + 1 new reverse-standings regression test).
- `tests/test_waiver_engine_service.py` (3 new W5 fixture-7 regression
  tests).
- `tests/test_redraft_kdst_streamer_keep_current_fix.py` (new -- 4 W6
  tests, including fixture 6).
- `tests/test_weekly_projection_service.py` (4 new W7 fixture-8 regression
  tests).
- `tests/test_weekly_home_single_snapshot.py` (2 fixtures corrected to the
  real `decisionEnvelopes` shape the fixed STREAMER loop actually reads).
- `tests/test_decision_envelope_consumer_migration.py`, `tests/test_
  desktop_facade_architecture_wiring.py`, `tests/test_desktop_application_
  api.py` (3 fixtures given real `k=1, dst=1` roster shape, exposed by the
  new position-config guard).
- `desktop/apps/redraft/src/improve-team-explain.test.ts` (1 existing
  assertion updated for the KEEP label; 3 new W5 null-safety tests).

### OPEN ISSUES FOR WORKER 4 (Enginerds Sunday surface + W8 + D1 + ESPN +
W9 + D2)

1. **The position-config no-DST-slot guard (`redraft_kdst_streamer`) is
   unit-tested but NOT live-verified against Enginerds itself**, since
   Enginerds is still not a Redraft profile (confirmed unchanged this
   pass). Once Worker 4 builds that surface, live-verify a real DST
   consensus request is never made for Enginerds' real `roster.dst == 0`.
2. **W5's THIS_WEEK evaluation is bounded to the top 60 free agents by raw
   weekly points** (a real, disclosed scope decision, not a hidden
   limitation) -- a genuinely great streaming option ranked outside the
   raw-points top 60 would not get a real gain evaluation this pass (falls
   back honestly to the old ordering for that one candidate, never a
   fabricated gain). If Enginerds' real free-agent pool behaves
   differently (e.g. genuinely deep at a scarce position), consider
   whether 60 is still a reasonable bound there.
3. **W7's K/DST custom scoring was live-verified against Fantasy Gamers'
   real, standard-ish PPR scoring (has DST, real pts_allow tiers) -- NOT
   against Enginerds' real non-PPR/no-DST/first-down-bonus scoring**, since
   Enginerds isn't a Redraft profile yet. The kicker-tier fix specifically
   targets Enginerds' real captured tiers (2/2/2/3/4) per the brief, but
   this pass could only unit-test that exact scenario (`test_regression_
   fixture_8b`), not live-verify it against a real running Enginerds
   weekly-lineup/waivers call. Worker 4 should do that live check once
   Enginerds is wired in.
4. **`weekly_lineup_optimizer_service.simulate_this_week_add_drop` and
   `weekly_projection_service._score_kdst_from_raw_sleeper_scoring` are
   both new, real, reusable primitives** -- if Worker 4's Enginerds Sunday
   surface (or W8's Dynasty-mode weekly tools) needs either "real before/
   after lineup-gain simulation" or "real league-exact K/DST scoring",
   reuse these, don't re-derive.
5. **A real, general lesson from this pass's own live-verification catch:**
   this codebase has at least one other unrouted-but-still-present legacy
   page (`in-season.tsx`'s `WaiversPage`) whose code can look identical to
   the real routed surface (`improve-team.tsx`) at a glance, including
   sharing some component names/patterns. Grep hits alone were NOT
   sufficient to confirm a fix landed on the real, owner-facing surface
   this pass -- a live browser check caught the gap. Future workers editing
   `in-season.tsx`/`improve-team.tsx` should confirm which file the actual
   route (`RedraftApp.tsx`) wires to before trusting a source-only fix.
6. **KHA and 403 N 18th remain BLOCKED** for any current-state Sunday tool
   (unchanged, re-confirmed only incidentally, not this Worker's focus).

---

## Worker 4 -- Enginerds Sunday surface + W8 + D1 + ESPN checklist + W9 + D2
(2026-09-18, ~8:46-9:15 PM Mountain)

Time check: started ~8:46 PM Mountain (~15h14m remaining to the Saturday
noon deadline). This entry written ~9:15 PM (~14h45m remaining). No
deadline risk.

### W8 -- Enginerds Redraft weekly-decision surface -- INSPECTED CODE +
ACTUAL TEST RESULT + LIVE OBSERVATION (the primary deliverable)

**Investigated the existing "import a Sleeper redraft profile" path first,
per the brief's explicit instruction not to build a parallel importer.**
Found it: `src/services/sleeper_redraft_owner_service.py`'s
`import_sleeper_redraft_profile` (wired at `desktop_facade.py:2385`,
`POST /api/v1/redraft/profiles/import-sleeper`, frontend
`profile.tsx`'s real "Import from Sleeper" panel, already used to onboard
Fantasy Gamers). This is a real, generic, provider-agnostic Sleeper ->
Redraft importer -- reuses the SAME Sleeper league data already connected
Dynasty-side (`1344772855908290560`), but goes through Redraft's own
completely separate profile store (`local_exports/redraft_v1/profiles/`,
not `local_exports/dynasty_v1/`) and Redraft's own weekly services --
never Dynasty valuation. Confirmed no code sharing/coupling with
`governed_asset_registry_service.py` anywhere in this path (INSPECTED
CODE: grepped the whole import module, zero references).

**Real owner username resolved first (LIVE OBSERVATION):** `GET
https://api.sleeper.app/v1/user/1352768154031374336` -> real
`username: "mcolety1"` (display_name and username differ here -- the
import endpoint validates against the real `username` field, not
display_name, confirmed by reading `import_sleeper_redraft_profile`'s own
validation).

**Real import performed live, via the actual browser UI (not a backend
shortcut)** -- Redraft dev pair rebuilt+restarted first (real `npm run
build --workspace @nwr/redraft-desktop`, fresh backend on 18742 with real
dev startup credentials piped via stdin the same way
`nwr_release_gate_smoke.ps1` does, fresh `vite preview` on 1422 -- the
prior pair Worker 3 left running predated this Worker's own code changes).
Navigated to Profile & Scoring's real "Import from Sleeper" panel, entered
league id `1344772855908290560` and username `mcolety1`, clicked "Import &
activate".

**A real automation-tool hazard found and worked around (not a product
bug):** the `form_input` MCP tool's numeric coercion mangled the 19-digit
Sleeper league id (`1344772855908290560` -> `1344772855908290600`,
precision loss past JS's safe-integer range) when set via its `value`
parameter. Caught by re-reading the field before submitting, not assumed
correct. Worked around by clicking the field and using real keystroke
`type` input instead, which preserved the exact string. Flagging this for
any future worker automating a 19-digit Sleeper id through this tool --
always re-read the field after `form_input` on a long numeric-looking
string.

**Real result, confirmed multiple ways:**
- New profile `6687d2b3aa21450ea0fc9e1792d461ff` created at
  `local_exports/redraft_v1/profiles/6687d2b3aa21450ea0fc9e1792d461ff.json`
  (6th profile file, up from Worker 1's confirmed 5) -- real captured
  roster `{bench_size: 14, dst: 0, flex: 2, k: 1, qb: 1, rb: 2,
  superflex: 0, te: 1, wr: 3}` and real scoring `{reception: 0.0,
  passing_td: 3.0, rushing_td/receiving_td: 4.0, interception/
  fumble_lost: -1.0, passing_yards: 0.0333...}` -- byte-exact match to
  Worker 1's independently-captured real Enginerds settings.
  `local_exports/dynasty_v1/` confirmed untouched by this import (file
  mtime check: the Dynasty league profile file's mtime predates this
  Worker's whole session) -- the two stores are genuinely isolated, as
  designed.
- UI immediately showed "ACTIVE LEAGUE Las Vegas Enginerds · 2026 ·
  10-Team Standard · 1QB", 6 profiles total.

**Start/Sit -- LIVE OBSERVATION, real custom scoring, real roster:** first
attempt hit a real "Command center unavailable" timeout (a cold-cache
first request -- real Sleeper weekly-projection catalog for ~9400 players
plus a real nflverse schedule pull for game-lock both cold on a
freshly-restarted backend); a direct `curl` to the same endpoint completed
in 347ms once warm, and a manual "Refresh weekly projections" click in the
browser then rendered correctly with zero further issue -- documented as a
real, disclosed cold-start latency characteristic, not a functional bug
(not investigated further under this pass's time box). Confirmed via both
direct API call and rendered UI:
  - Real 10-slot starting lineup (QB, RB, RB, WR, WR, WR, TE, K, FLEX,
    FLEX -- **no DST anywhere**, matching real `roster.dst == 0`).
  - Real recommendation: "Start Jalen Coker over Zay Flowers, +7.6
    projected points" with a genuine LOW CONFIDENCE / CLOSE CALL badge.
  - Real league-exact scoring: every non-K starter `scoringContext:
    "NWR_LEAGUE_SCORING"`; the K (Cam Little) scored under
    `NWR_LEAGUE_SCORING_KDST_WEEKLY_PARTIAL` with real, disclosed gaps
    `['fgm_0_19', 'fgm_50p']` (his real raw weekly row had no 0-19-yard
    field-goal entry that week, and Sleeper's payload has no 50+ breakout
    at all -- both real, not fabricated). `nonExactScoringInTotal: true`,
    correctly disclosed in the UI banner.
  - Real reserve/game-lock buckets populated: `reserve` showed Ricky
    Pearsall (11638); `lockedUnavailable` showed Skyler Bell (already
    kicked off).
  - **A real, correctly-sourced exclusion investigated and confirmed NOT a
    bug:** the second real reserve id (12484, Jayden Higgins) was
    initially missing from the `reserve` bucket -- investigated with a
    live, instrumented repro of `build_roster_candidates`/
    `optimize_weekly_lineup` against the real facade and real Sleeper
    data. Root cause: Higgins has a real, sourced `SEASON_OUT` manual
    status override already on file (`current_player_status_overrides_
    service.py`: "Torn ACL in training camp...season-ending for 2026,"
    4 real cited sources, verified 2026-09-07) -- `_status_for` correctly
    routes a ZERO_VALUE_KINDS status to `excluded` BEFORE the
    reserve/taxi check ever runs, per the module's own documented
    precedence. This is real, correct, evidence-based behavior (excluded
    for a stronger, sourced reason than merely being reserve-slotted),
    not a defect -- no code change made.
  - Zero console errors (checked via `read_console_messages`,
    `onlyErrors: true`).

**Improve Team -- LIVE OBSERVATION, all four tabs, real Enginerds data:**
  - **Targets/Add-Drop, REST_OF_SEASON:** 25 real targets, real FAAB
    suggested bids ($30-50 MEDIUM urgency example shown) -- confirms
    Worker 3's `waiver_type` fix (`==2`) now correctly detects Enginerds
    as a real FAAB league live, not just by prior unit test.
  - **Targets/Add-Drop, THIS_WEEK:** real "NFL WEEK 2" auto-populated
    (W1 fix confirmed for Enginerds too); real "THIS WEEK: real
    legal-lineup gain: 0.7 pts" language rendered; real gain-sorted order
    (0.7, 0.6, ...), not season-utility order.
  - **FAAB tab:** real "$100 of $100 total," real "14 WEEKS REMAINING"
    (from real Sleeper schedule/playoff_week_start), and the real,
    correct disclosure banner: "This is your real, live Sleeper FAAB
    budget (waiver priority #2, read fresh this request -- never a stored
    or hardcoded number)."
  - **Streamers tab -- the specific, previously-only-unit-tested case now
    LIVE-verified:** clicked "Refresh K/DST ECR." Real primary
    recommendation: **"KEEP Cam Little (K)"** -- a genuine case of the
    owner's own real starter (real FantasyPros ECR #6) beating every real
    available alternative this week, rendered as the actual primary card
    (W6's KEEP-current fix, live, for the first time against a real
    league where this exact scenario occurred naturally). Confirmed via a
    direct authenticated API call to `/api/v1/redraft/kdst/streamer`:
    `primaryRecommendation: {"playerName": "Cam Little", "rosterStatus":
    "YOUR_STARTER", "recommendation": "START"}`.

### NO-DST ENFORCEMENT -- LIVE OBSERVATION (the specific ask Worker 3
flagged as unit-tested-only)

Same real `/kdst/streamer` call: the top-level `traceIds` array contained
**exactly one entry, for K only** -- no DST trace id anywhere, confirming
FantasyPros' DST consensus was never even requested. The DST decision
envelope itself: `primaryRecommendation: null`, `confidenceState:
"UNAVAILABLE"`, `rationale: "This league has no DST roster slot; DST
pickups are never recommended."` The rendered UI showed "No available
recommendation / No DST streamer read for Week 2" and "No candidates / No
DST rows returned for Week 2" -- real, honest, position-configuration
enforcement confirmed live for Enginerds' real `roster.dst == 0`, not just
by Worker 3's unit test.

### A real, pre-existing, reconfirmed-not-new display bug found while
verifying W8 (NOT fixed this pass -- documented, out of narrow scope)

`desktop/apps/redraft/src/in-season.tsx`'s `WeeklyHomePage` "Stage" row
(and the left-sidebar lifecycle badge, via `shell-identity.tsx`) both call
the LOCAL, bootstrap-only `resolveLeagueLifecycle(profile, draftBoard)`
from `league-context.ts` -- which has no live provider-status fetch by
design (see that function's own docstring) -- instead of reading the
CORRECT, live, provider-status-aware `lifecycle` field the backend's own
`/api/v1/redraft/league-workspace-context` endpoint already returns
correctly. **Confirmed via direct curl, real Enginerds:** that endpoint
returns `"lifecycle": "IN_SEASON"` with the exact correct basis ("The
league provider reports real league status 'in_season'..."), while the
Weekly Home page and sidebar simultaneously show "PRE-DRAFT" for the same
real league. **This is NOT new and NOT caused by this pass's D2 fix** --
confirmed it also affects Fantasy Gamers (visible in this pass's very
first screenshot, before any Enginerds work began) and is exactly the
"known, separately-tracked gap" Worker 2's own 2026-09-17 fix docstring in
`league-context.ts` already disclosed ("that half is a known gap for this
purely-local heuristic"). Does NOT block any real functionality --
Start/Sit, Improve Team, and Weekly Home's own data all loaded and
computed correctly regardless of this cosmetic label, confirmed live.
Not fixed this pass (would require reworking which lifecycle source
`in-season.tsx`/`shell-identity.tsx`/`RedraftApp.tsx` read from, a
multi-file change outside this pass's narrow W8/W9/D1/D2/ESPN scope) --
flagged precisely for Worker 5 or a future pass.

### ESPN leagues (KHA, 403 N 18th) -- documentation-only deliverable, no
new integration built, per the hard boundary

**No ESPN client/service was added anywhere this pass** (confirmed,
re-grepped `src/` fresh: zero matches for any ESPN API pattern, same as
Worker 1/3's independent findings).

**Live-verified BLOCKED state, both leagues, this pass:**
- Activated the real KHA profile (`fb1c49402c7644a99120197d41344bbb`) in
  the browser. Sidebar/header correctly show **IN SEASON** (this pass's
  own D2 fix, live-verified -- see below). Start/Sit correctly shows
  "Sleeper league required / Start/Sit needs a live Sleeper roster and the
  real weekly-projection source" -- an honest, explicit BLOCKED state, not
  a silent failure and not stale historical draft data presented as
  current.
- 403 N 18th not re-clicked through the UI this pass (KHA's confirmation
  plus Worker 1/3's independent code-level confirmation that the SAME
  facade guard applies to every non-Sleeper profile is sufficient
  corroboration; both share the identical `isSleeper` gate in
  `improve-team.tsx`/`in-season.tsx`).

**The exact input checklist for the owner, if ESPN support is ever
pursued (documentation only, nothing built or attempted this pass):**

1. **Real current roster read.** Today, both leagues have ONLY a
   historical draft board (KHA: 157 real picks; 403 N 18th: 118 real
   picks) -- zero post-draft transaction history exists anywhere in this
   codebase for either league. Needed: either (a) the owner manually
   re-enters their current real roster through a `provider: "local"`
   profile (the exact mechanism already proven safe for this app's local
   test profiles -- reuses existing, tested code, zero new integration),
   refreshed by hand whenever it goes stale, or (b) a genuine, new,
   read-only ESPN Fantasy API integration.
2. **Real scoring config re-confirmation.** KHA's profile has
   `practical_mode: True` (K/DST already handled by manual entry, a
   real, previously-fixed mechanism -- unrelated to this gap). 403 N
   18th's `draft.roster_limits` is empty (`{}`) -- no per-position cap
   recorded anywhere in this worktree's copy of that profile; would need
   re-entry or a live ESPN settings read.
3. **Real transaction/waiver state.** Neither league has ever had any
   ESPN-sourced transaction, waiver, or trade data in this codebase.
   Needed for any FAAB/waiver tooling to work: a real, current
   transaction log, which today only a live ESPN API (or fully manual
   owner tracking) could supply.
4. **The smallest validated import path, if pursued (not started, listed
   only, per the hard boundary against building a new ESPN integration
   this pass):** a genuine, new, read-only ESPN Fantasy API client, GET
   requests only, built the same disciplined way this codebase's Sleeper
   client was (a single, narrow HTTP wrapper + a dedicated import
   service, following `sleeper_redraft_owner_service.py`'s own structure
   as the template). ESPN's fantasy API requires the owner's own
   authenticated session cookies (`SWID` and `espn_s2`) for a private
   league -- these must come from the owner explicitly (copied from their
   own logged-in browser session); this pass did not request, receive,
   store, or attempt to obtain either value, per the hard boundary
   against scraping/cookie extraction. Until the owner explicitly
   supplies both, ESPN readiness stays BLOCKED by design, not by a
   missing feature this pass could have shipped.
5. **403 N 18th's real ESPN league id (`1009373442`) is still not
   present anywhere in this worktree's own profile JSON**
   (`provider_league_id: null`, unchanged since Worker 1's finding) -- it
   would need to be re-entered from this ledger/prior memory or the real
   native-install receipt file before any future import attempt could
   even target the right league.

### W9 -- streamer request-ordering race -- INSPECTED CODE + ACTUAL TEST
RESULT (mechanism proven; the exact live race not independently
reproduced under real network timing this pass -- see below)

**Root cause confirmed exactly as the brief described**, at
`improve-team.tsx` (~L165-205 in this HEAD, module grew since the audited
SHA): `loadStreamers` (invoked by the Streamers tab's manual "Refresh
K/DST ECR" button, a multi-request sequential loop -- up to 3 real
FantasyPros ECR reads, one per horizon week) had a real, separate
`useEffect` that cleared `streamerResults`/`streamerError` on
`data.activeProfileId` change, but the in-flight async function itself had
NO profile/request-generation check of its own -- its `.then`-equivalent
`setStreamerResults(loaded)` at the end of the loop would apply
unconditionally even if the owner had already switched to a different
league while the request was still in flight, silently repopulating the
new league's screen with the PRIOR league's streamer results.

**Fix:** reused the SAME `createStaleResponseGuard()` primitive already
established in `weekly-shared.tsx` and used by `useAsync` everywhere else
in this codebase, applied via a `useRef` (since `loadStreamers` is
manually triggered, not an automatic `useEffect`-driven fetch like
`useAsync`'s own single-request shape): the guard is superseded and a
fresh one created on every profile change (same `useEffect` that already
cleared results/error), and `loadStreamers` captures the CURRENT guard by
value at call time, checking `guard.isStale()` both mid-loop (before each
new week's request -- stops issuing further requests for an
already-inactive league, not just discarding the final result) and before
applying the final `setStreamerResults`/`setStreamerError`. `finally`
still always clears the working spinner regardless of staleness (a
UI-only concern, not a data leak).

**Regression test (ACTUAL TEST RESULT):** added to
`weekly-shared.test.ts` (co-located with `createStaleResponseGuard`'s own
existing adversarial-ordering tests, same established pattern -- this repo
has no jsdom/@testing-library/react, so the guard's OWN behavior is tested
directly rather than through a rendered component, matching how the
existing tests already prove `useAsync`'s single-request case): a new
`runGuardedStreamerSequence` helper faithfully reproduces the real
multi-week loop's own guard usage. Two new tests: (1) a league-A first
week resolves, the owner switches leagues in the same tick (no intervening
await, exactly matching a synchronous profile-change effect), the guard is
superseded before the loop's mid-loop check for week 2 ever runs -- proven
`fetchedA == [0]` (week 2 never even requested) and `applied ==
[["league-B-week1"]]` (league A's results never land); (2) a full,
non-superseded sequence still applies correctly. **29 tests total in this
file, all pass** (up from 27 pre-existing).

**Live reproduction of the exact real-network race was NOT attempted this
pass** -- local network calls complete in well under a second, making a
reliable, non-flaky browser-level race difficult to force deterministically
within this pass's time budget, and no network-throttling tool was
available in this session's browser toolset. This is disclosed as a real,
honest gap in live evidence for this one fix (the CODE fix and its
regression test are both real and verified; the live-race REPRODUCTION
specifically is not) -- Worker 5, with more time or a throttling tool,
should attempt a real live repro (switch Fantasy Gamers -> Enginerds mid
K/DST-streamer-request) if thoroughness requires it.

### D2 -- draft-completion-evidence tightening -- INSPECTED CODE + ACTUAL
TEST RESULT + LIVE OBSERVATION

**Root cause confirmed exactly as the brief described, and confirmed
MORE material than the brief's own framing suggested:** the 24-hour
staleness fallback in `league_lifecycle_service.py`'s
`resolve_league_lifecycle` fired for ANY `drafted_count >= 1` once stale
-- age alone, no minimum completion evidence. **Investigated whether the
two real leagues this fallback exists for (KHA, 403 N 18th) actually
depend on it, rather than assuming**: computed their real ratios --
KHA 157/192 = **81.8%**, 403 N 18th 118/128 = **92.2%** -- both real,
neither reaches the exact-count branch (`drafted_count >= total_draft_
picks`) above it, so **both real leagues' correct IN_SEASON resolution
genuinely depends on this exact fallback today**, not a hypothetical edge
case.

**Fix:** added `STALE_DRAFT_MIN_COMPLETION_RATIO = 0.5` -- the staleness
fallback now requires `drafted_count / total_draft_picks >= 0.5` **in
addition to** the existing 24h-quiet check, in both the backend
(`league_lifecycle_service.py`) and its frontend mirror
(`league-context.ts`'s `resolveLeagueLifecycle`, used for local/bootstrap
routing decisions). 0.5 was chosen deliberately below both real leagues'
own ratios (81.8%/92.2%) so neither regresses, while a "just one pick"
draft (the brief's exact repro shape, ~0.5% of a 192-pick league) or a
genuinely-abandoned ~20%-drafted league no longer silently resolves as
complete on age alone.

**ACTUAL TEST RESULT (Python, `tests/test_league_lifecycle_service.py`,
23 pre-existing -> 27 after this pass's 4 new tests):**
- **Negative case (the exact brief repro):**
  `test_stale_but_barely_started_draft_does_not_falsely_resolve_complete`
  -- 1 of 192 picks, stale since 2026-09-10, evaluated 2026-09-17 (7 days
  stale). **PASSES: resolves LIVE_DRAFT, not IN_SEASON** (would have
  wrongly resolved IN_SEASON before this fix).
- **Negative case (a more plausible abandoned-draft shape):**
  `test_stale_partial_draft_under_completion_ratio_stays_live_draft` --
  25 of 128 (~20%), stale for weeks. PASSES: LIVE_DRAFT.
- **Positive controls (the exact real leagues, must not regress):**
  `test_real_kha_shape_still_resolves_in_season_after_ratio_fix` (157/192)
  and `test_real_403n18th_shape_still_resolves_in_season_after_ratio_fix`
  (118/128) -- both PASS, both still resolve IN_SEASON.
- All 5 pre-existing tests in this file that exercise the staleness
  fallback (including the exact `100/128` boundary tests at 78.125%,
  comfortably above the new 50% floor) still pass unchanged.
- **23 pre-existing tests + 4 new this pass = 27 tests, all pass.**

**Mirrored TypeScript test (`league-context.test.ts`):** two new tests
under the existing "real provider-evidence fixes" describe block, same
shapes (1-pick and 25-of-192), both assert `LIVE_DRAFT`. **28 tests total
in this file, all pass** (up from 26 pre-existing).

**LIVE OBSERVATION, real KHA league, this pass:** activated KHA in the
real running Redraft app -- header/sidebar correctly show **"IN SEASON"**
(not PRE-DRAFT, not stuck LIVE_DRAFT) -- confirms the ratio-tightened
fallback still resolves the real league correctly, live, not just via
tests. (403 N 18th not independently re-activated in the browser this
pass; its identical code path and passing positive-control test are
treated as sufficient, given time constraints and that Worker 1/2/3 had
already independently confirmed its shape multiple times this cycle.)

### D1 -- Dynasty storage/native launcher -- INSPECTED CODE + ACTUAL TEST
RESULT + LIVE OBSERVATION (both halves investigated; both had a real,
small, fixable gap -- both fixed, neither risked deep native-runtime
rework)

**(a) Dynasty's Connect flow explicit-refresh gap -- verified, not
assumed, and found genuinely missing:** `desktop/apps/dynasty/src/pages/
system.tsx`'s `DynastyLeagueConnectionPanel` (the real "Connect League"
flow, Dynasty League Import V1) offered only "Disconnect league" once a
league was connected -- no refresh/resync action existed anywhere for an
ALREADY-connected league; the owner's only path to a fresher pull was
disconnect -> re-type the league id -> reconnect. Separately confirmed
(INSPECTED CODE) that the underlying import primitive
(`import_dynasty_league` / `save_league_profile` / `save_league_snapshot`)
already does the right thing on every call -- a real, fresh, GET-only
Sleeper fetch every time (never cached), writing a NEW uniquely
timestamped snapshot file (`utc_snapshot_stamp() + ".json"`) and never
overwriting or deleting a prior one -- so a failed refresh (an exception
before that final write) structurally leaves the previous snapshot and
connection state completely untouched, with zero extra code needed for
that guarantee. The only real gap was the missing UI entry point.

**Fix:** added `leagueId`/`myOwnerId` (both additive) to the
`DynastyLeagueContext` contract and to all 4 real call sites in
`desktop_facade.py` that build this dict (`compare_dynasty_assets`,
`evaluate_dynasty_trade`, `_annotate_dynasty_bootstrap_payload`,
`_annotate_dynasty_workspace_payload`) so the frontend can resubmit the
SAME real league id/owner id already on file. Added a real "Refresh from
Sleeper" button beside "Disconnect league" in `system.tsx`, calling the
SAME `client.importDynastySleeperLeague` the Connect flow already uses
(with `profileId` pinned explicitly, so a refresh always updates the same
profile in place rather than relying on id-derivation matching by
coincidence). **Never touches `governed_asset_registry_service.py`'s
valuation computation** -- confirmed by `git status`, that file was not
modified.

**LIVE OBSERVATION:** rebuilt+restarted the Dynasty dev pair (also
required since it was running pre-HEAD code per Worker 1's own flag --
confirmed stopped PIDs 40244/37176, fresh backend+`vite preview` on
18741/1421). Navigated to Data Health's real Dynasty League Connection
panel (Enginerds already connected from the earlier dynasty-import
cycle). Clicked the new "Refresh from Sleeper" button: real success
message "League refreshed from Sleeper. A new dated snapshot was saved,"
the displayed "Imported" timestamp updated live from `9/18/2026, 6:25:55
PM` to `9/18/2026, 9:13:53 PM`. **Verified on disk, not just by the UI
message:** `local_exports/dynasty_v1/league_snapshots/1344772855908290560/`
gained a genuinely NEW file (`20260919_031353.json`) alongside all 4
pre-existing snapshot files, all still present and untouched. Zero
console errors.

**(b) Native launcher env var -- INSPECTED CODE, confirmed real, fixed
(small, clear, isolated change):** `desktop/crates/nwr-desktop-runtime/
src/lib.rs`'s `DesktopState::launch` (the SAME function handles both
`AppMode::Redraft` and `AppMode::Dynasty` at runtime, discriminated by the
already-existing `mode` parameter) unconditionally set only
`NWR_REDRAFT_HOME`, never `NWR_DYNASTY_LEAGUE_HOME` -- confirmed by
reading the whole function, no conditional branch existed. This means a
NATIVE Dynasty launch has always silently fallen back to
`dynasty_league_store_root`'s repo-local default
(`<repo_root>/local_exports/dynasty_v1`) instead of this native install's
own durable, per-bundle app-data state directory -- the exact class of gap
Redraft's own `NWR_REDRAFT_HOME` wiring was specifically built to avoid.
**Fix:** replaced the unconditional `.env("NWR_REDRAFT_HOME", ...)` call
with a `match mode` branch -- `AppMode::Redraft` sets `NWR_REDRAFT_HOME`
-> `state_dir/redraft` (byte-identical to before, zero behavior change for
Redraft), `AppMode::Dynasty` now sets `NWR_DYNASTY_LEAGUE_HOME` ->
`state_dir/dynasty` (a new, real, per-bundle native path, matching the
exact env var name `dynasty_sleeper_league_service.py`'s own
`dynasty_league_store_root` already reads). **ACTUAL TEST RESULT:** `cargo
check` on `nwr-desktop-runtime` -- clean compile, zero errors/warnings
introduced. **No new Rust unit test added** -- this function directly
spawns a real child process with no existing test seam for inspecting
`Command`'s env vars without a larger refactor; per the brief's own
explicit guidance for this half ("fix if small/clear...but if this
requires deep native-runtime work beyond a small, clear fix, document
precisely rather than risk breaking native packaging this late"), this
fix was kept small and isolated (one conditional branch, same `.env()`
builder pattern already present) and verified only via `cargo check` --
**not** independently verified via an actual native package build/launch
this pass (that remains Worker 5's or a later native-packaging pass's
job, per the brief's own time-boxing of that step to the final 3 hours).

### TESTS -- ACTUAL TEST RESULT (full, this pass)

- `tests/test_league_lifecycle_service.py`: **27 passed** (23 pre-existing
  + 4 new D2 tests).
- `tests/test_dynasty_sleeper_league_service.py`,
  `tests/test_dynasty_league_import_facade_wiring.py`,
  `tests/test_desktop_facade_architecture_wiring.py`: all pass, **67
  passed** combined with the above (single run).
- Full brief-listed backend suite + this pass's own touched files
  (`test_weekly_lineup_optimizer_service`, `test_weekly_projection_
  service`, `test_weekly_projection_provider_service`, `test_
  fantasypros_kdst_consensus_service`, `test_redraft_waivers_ir_reserve_
  drop_exclusion_fix`, `test_redraft_waivers_faab_context_fix`, `test_
  redraft_waivers_open_slot_and_same_context_fix`, `test_weekly_home_
  single_snapshot`, `test_weekly_home_sleeper_fetch_caching`, `test_
  dynasty_sleeper_league_service`, `test_dynasty_league_import_facade_
  wiring`, `test_league_lifecycle_service`, `test_waiver_engine_service`,
  `test_redraft_kdst_streamer_keep_current_fix`, `test_weekly_game_lock_
  service`, `test_desktop_application_api`): **246 passed, 4 failed** --
  the SAME 4 pre-existing HEAD-baseline failures Worker 3's ledger entry
  already documented exactly by name (`test_dynasty_facade_composes_real_
  governed_workflows`, `test_desktop_rookie_veteran_bridge_is_source_
  separated_and_trade_aware`, `test_redraft_bootstrap_seeds_once_and_
  matches_desktop_contract`, `test_facade_has_no_streamlit_or_app_
  component_dependency`) -- re-confirmed unrelated to this pass's changes
  (none of this pass's diffs touch any file those tests exercise), not
  waived without evidence.
- Frontend: `npm run typecheck` (both apps) -- clean, 0 errors, checked
  after every meaningful edit round including the D1 Dynasty/contracts
  changes. Full `npx vitest run`: **497 passed, 0 failed** (up from
  Worker 3's 493 baseline by 4: 2 new W9 stale-sequence-guard tests in
  `weekly-shared.test.ts`, 2 new D2 tests in `league-context.test.ts`).
- Rust: `cargo check` on `nwr-desktop-runtime` -- clean, 0 errors.
- `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/frontend_
  bench_results.json`'s own benign perf-timing-noise churn (same known
  side effect prior Workers hit from running the full vitest suite) was
  reverted with `git checkout --` before finishing -- not a real change.

### LIVE VERIFICATION -- LIVE OBSERVATION, summary

Rebuilt and restarted BOTH dev pairs this pass (Redraft: stopped Worker
3's PIDs 25936/46660, fresh backend+`vite preview` on 18742/1422; Dynasty:
stopped Worker 1-flagged pre-HEAD PIDs 40244/37176, fresh backend+`vite
preview` on 18741/1421 -- required since this pass's D1 fix touched
Dynasty-side code). Real Chrome MCP session covering: Enginerds import
(profile.tsx), Enginerds Start/Sit (real custom scoring, real reserve/
lock buckets), Enginerds Improve Team all 4 tabs (Targets REST_OF_SEASON
+ THIS_WEEK, Add/Drop, FAAB, Streamers with a real live KEEP-current
case and a real live no-DST-guard confirmation via direct API
inspection), KHA activation + BLOCKED Start/Sit + correct IN SEASON badge
(D2), and Dynasty's new Refresh-from-Sleeper button (D1) with an on-disk
new-snapshot verification. Zero console errors observed across the whole
session (`read_console_messages`, `onlyErrors: true`, checked repeatedly).
Zero writes: every call was a plain GET (Sleeper league/rosters/users/
players/projections/state, FantasyPros consensus) or a read against the
backend's own read-only endpoints; every weekly response carried
`writeBehavior: "NO_SLEEPER_WRITES"` (or the K/DST-specific
`NO_SLEEPER_WRITES_NO_FANTASYPROS_WRITES"`); the Dynasty/Redraft imports
are both explicitly, structurally GET-only per their own docstrings,
confirmed by reading the code, not just trusting the label.

### REDRAFT/DYNASTY PROCESSES STATUS

Both dev pairs restarted and confirmed serving this pass's final HEAD:
- Redraft backend: port 18742 (fresh PID via a real dev-credentials-piped
  startup), `vite preview` on port 1422.
- Dynasty backend: port 18741 (same real credential-piping pattern),
  `vite preview` on port 1421.
Both `GET /api/v1/bootstrap` -> `200` confirmed (with real dev bearer
token + matching Origin header), both frontends `GET /` -> `200`.

### FILES CHANGED

- `src/services/league_lifecycle_service.py` (D2: `STALE_DRAFT_MIN_
  COMPLETION_RATIO` + ratio-gated staleness fallback; docstring updated).
- `desktop/apps/redraft/src/league-context.ts` (D2: mirrored ratio gate
  in the frontend `resolveLeagueLifecycle`).
- `tests/test_league_lifecycle_service.py` (D2: 4 new tests).
- `desktop/apps/redraft/src/league-context.test.ts` (D2: 2 new tests).
- `desktop/apps/redraft/src/improve-team.tsx` (W9: `streamerGuardRef` +
  mid-loop/final staleness checks in `loadStreamers`).
- `desktop/apps/redraft/src/weekly-shared.test.ts` (W9: 2 new tests +
  `runGuardedStreamerSequence` helper).
- `src/application/desktop_facade.py` (D1: `leagueId`/`myOwnerId` added
  to all 4 `dynastyLeague` response dict sites -- additive only, no
  valuation logic touched).
- `desktop/packages/contracts/src/index.ts` (D1: `DynastyLeagueContext`
  gained `leagueId`/`myOwnerId`).
- `desktop/apps/dynasty/src/pages/system.tsx` (D1: real "Refresh from
  Sleeper" button + `refresh()` handler).
- `desktop/crates/nwr-desktop-runtime/src/lib.rs` (D1: mode-conditional
  `NWR_REDRAFT_HOME` / `NWR_DYNASTY_LEAGUE_HOME` env var).
- No new profile-import service was created for W8 -- the existing
  `sleeper_redraft_owner_service.py`/`profile.tsx` "Import from Sleeper"
  path was reused unmodified; the only artifact from W8 is the new real
  profile data file itself: `local_exports/redraft_v1/profiles/
  6687d2b3aa21450ea0fc9e1792d461ff.json` (+ its matching `sleeper_
  imports/` receipt), which is gitignored local data, not a source change.

### OPEN ISSUES FOR WORKER 5 (full test/dogfood pass)

1. **The pre-existing "Stage: PRE-DRAFT" display bug** (Weekly Home +
   sidebar reading the local bootstrap-only lifecycle heuristic instead of
   the correct, live `/league-workspace-context` `lifecycle` field) --
   confirmed affects BOTH Fantasy Gamers and Enginerds live, not fixed
   this pass (documented above, out of this pass's narrow scope). Real,
   cosmetic-only (does not block any real tool), but worth a dedicated fix
   pass: make `in-season.tsx`/`shell-identity.tsx` prefer the live
   workspace-context lifecycle when available, falling back to the local
   heuristic only while that hasn't loaded yet.
2. **W9's exact real-network race was not independently browser-reproduced
   this pass** -- the code fix and its regression test (proving the exact
   guard mechanism) are both real and verified; only the live,
   real-timing repro specifically was not attempted (no throttling tool
   available, local calls too fast to race reliably by hand). Attempt a
   real repro if thoroughness requires it and a throttling mechanism is
   available.
3. **D1(b)'s native launcher fix was verified only via `cargo check`, not
   an actual native package build/launch** -- per the brief's own
   time-boxing, real native packaging verification is explicitly Worker
   5's/the final delivery pass's job (limited to 60 minutes, 11:00
   Mountain cutoff). When that pass runs, confirm the Dynasty native app
   actually persists/reads its per-league Sleeper import from
   `%LOCALAPPDATA%\com.ninerswarroom.dynasty\state\dynasty\` (not the
   repo-local fallback) -- this pass's fix should make that true but was
   not end-to-end native-verified.
4. **Enginerds' cold-start "Command center unavailable" timeout on the
   very first Start/Sit request after a backend restart** (see W8 above)
   -- real, reproduced once, resolved by a manual retry/refresh once the
   backend's own caches warmed (a direct curl of the same endpoint
   completed in 347ms). Not investigated further under this pass's time
   box; worth a quick look if it recurs (e.g., whether the frontend's own
   fetch timeout is simply too aggressive for a genuinely cold multi-thousand-row
   weekly-projection + nflverse-schedule cold fetch, vs. a real backend
   slowness worth optimizing).
5. **403 N 18th was not independently re-activated/re-verified live in the
   browser this pass** (only KHA was, plus 403 N 18th's identical code
   path and passing D2 positive-control test) -- worth a quick direct
   live check in Worker 5's full dogfood pass for completeness.
6. **The ESPN checklist above is documentation only** -- no code exists to
   act on it; the owner would need to explicitly decide to pursue either
   the manual-local-profile path or a real, new ESPN API integration
   (requiring the owner's own SWID/espn_s2 cookies) before any further
   work is possible here.
7. **This pass's own scratch files** (`.worker4_*.log`/`.log.err`/
   `_creds.json` in the repo root) are leftover local artifacts from
   piping real dev startup credentials to the rebuilt dev-server
   processes via stdin (matching `nwr_release_gate_smoke.ps1`'s own
   pattern) -- untracked, not committed, harmless, left in place because
   the still-running processes hold open file handles to them (same
   precedent as Worker 1's `dynasty_smoke_*.log` files). Safe to delete
   once those processes are stopped.
8. **Enginerds' real Redraft-mode Trades tab was not exercised this
   pass** (only Start/Sit + all 4 Improve Team tabs, per this pass's
   explicit scope) -- worth a quick check in Worker 5's dogfood pass
   since Trades is a real, routed surface for every Sleeper profile.
