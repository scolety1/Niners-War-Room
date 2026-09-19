# NWR Connection/Update Pass (2026-09-19, pre-Sunday) — LEDGER

Worker 1. Branch `upgrade/nwr-prospective-outcomes-v1-20260914`, worktree
`C:\NWR\prospective-outcomes-v1`. Starting HEAD `0ef017bfddc90b5be1e51256f69c9dcdfac498ee`
(clean, matched origin at pass start). This ledger is new for this pass; do not
conflate with `docs/codex/sunday_readiness_20260920/LEDGER.md` (the prior,
separate cycle this pass builds on and cites below).

### Methodology key

- **INSPECTED CODE** — read directly from the repo or a local file, this pass.
- **ACTUAL TEST RESULT** — a real command/script run, this pass.
- **LIVE OBSERVATION** — a real running process/API hit/filesystem read,
  observed directly this pass.
- **INFERENCE** — a conclusion drawn from the above, explicitly labeled, never
  presented as settled fact.

---

## 1. Can this process/session/machine reach Flaim? — LIVE OBSERVATION + INSPECTED CODE

**Answer: NO. Flaim is not reachable from this process.** This is a confirmed,
exhaustive negative, not an inconclusive result. Evidence, each independently
checked this pass:

1. **This session's own tool list has no Flaim MCP tool** (already established
   by the coordinating session via `ListAgents`/`ToolSearch` before this
   worker was dispatched; not re-litigated here).
2. **No Flaim environment variable, credential, or ESPN cookie anywhere in
   this process's environment.** `env | grep -iE "flaim|espn|swid"` → empty.
3. **No Flaim installation anywhere on this machine's standard install
   surfaces.** Checked and empty: `AppData\Local`, `AppData\Roaming`,
   `Program Files`, `Program Files (x86)`, global `npm ls -g`, `pip list`,
   `which flaim` (not on PATH), Windows installed-programs registry
   (`HKLM`/`HKCU` `...\Uninstall\*`, filtered for `*flaim*` — zero matches).
4. **No Flaim-named local process or HTTP service.** `Get-Process` filtered
   for `*flaim*` — zero matches. Every non-NWR listening port on this machine
   was individually identified by owning process
   (`Get-CimInstance Win32_Process -Filter "ProcessId=<pid>"`): all belong to
   unrelated local tooling on this same machine — `node.exe` serving a
   separate project (`Colety Labs Assessement/canonical/colety-labs`), the
   `Orca`/`TSF_ORCA` harness that hosts this and other agent sessions,
   `SignalRgbService.exe` (RGB peripheral software), and an unrelated
   benchmark process (`sablewake-benchmark`). None is Flaim.
5. **No Flaim-related file anywhere under this session's own Claude config**
   (`~/.claude*`, `%APPDATA%\Claude*`, `%LOCALAPPDATA%\Claude*` searched
   recursively for `*flaim*` — zero matches; no `.mcp.json` or Flaim server
   entry in this repo or in the global `~/.claude.json`).
6. **A genuinely thorough, full home-directory filename search**
   (`find /c/Users -iname "*flaim*"`, ~4 minutes, every file/directory under
   `C:\Users` by name) returned exactly two categories of real hit, both
   informational, neither reachable by this process:
   - This repo's own historical research-closeout documents (see section 3
     below) — already-known, read as text docs, not executable.
   - **One real, substantive find:**
     `C:\Users\codex-agent\.codex\plugins\cache\openai-curated-remote\
     app-69a8f78087e081919e52cacacf00ff36\3.0.0\skills\flaim-fantasy\SKILL.md`
     — a cached plugin skill belonging to **OpenAI's Codex CLI** (a different
     coding-agent product, `.codex/plugins/cache/...`), not to Claude Code or
     this NWR codebase/session. This machine happens to also run other agent
     sessions/tools (confirmed by the port-ownership check above), and one of
     them evidently has Codex's Flaim skill cached locally. **This session has
     no access to Codex's plugin runtime, no MCP tool wired to it, and no
     credential for it.** Reading the cached `SKILL.md` as a text file (which
     this pass did, for informational purposes only, treating its content as
     data/documentation, not as instructions to execute) is not the same as
     this process being able to invoke Flaim.

**What Flaim actually IS, per that real, local evidence (not fabricated):**
Flaim is a real, external, third-party fantasy-sports **MCP service**
(`flaim.app`). A user signs up and connects their fantasy platforms there; it
then exposes ~10 read-only MCP tools (`get_user_session`, `get_league_info`,
`get_roster`, `get_standings`, `get_matchups`, `get_free_agents`,
`get_players`, `get_transactions`, `get_draft`, `get_ancient_history`) plus
one narrowly-bounded write tool, `refresh_leagues`, which only updates
Flaim's own connected-league registry and **cannot** write to ESPN/Yahoo/
Sleeper (`SKILL.md`'s own explicit provider-write boundary, quoted directly:
"Flaim cannot change provider state... User permission does not change this
boundary."). It supports ESPN (auth: user-provided `SWID`/`espn_s2` session
cookies, captured via a Flaim-provided Chrome extension), Yahoo (OAuth 2.0),
and Sleeper (public API, username only, no password) across football,
baseball, basketball, and hockey (Sleeper: football/basketball only). It is
"officially available in ChatGPT's Plugin Store and Claude's Connector
Directory" (`SKILL.md`'s own words) — i.e., a consumer-product connector
surface for `claude.ai`/ChatGPT chat clients, not something wired into this
NWR desktop codebase, this Claude Code CLI session, or any NWR backend
service.

**Exact setup that would be needed for THIS NWR codebase/process to reach
Flaim's real ESPN/Sleeper data** (documented per the owner's task 3
instruction, not attempted):
- The owner (or whoever holds the flaim.app account) would need to either
  (a) expose Flaim's MCP server to this Claude Code session specifically —
  which is a `claude.ai`/Claude Code MCP-connector configuration step done
  outside this repo, in Claude's own settings, using the owner's own
  flaim.app account — or (b) if Flaim exposes a documented HTTP/REST API
  independent of MCP (not confirmed either way by anything found on this
  machine; the only real evidence found is the MCP tool-contract `SKILL.md`),
  a new, explicit, owner-authorized HTTP client would need to be built in
  this codebase, entirely analogous to the existing `SleeperClient`-style
  read-only wrapper, with its own auth flow.
- Either path requires the owner's own flaim.app credentials/session, which
  this pass correctly did not request and does not have.
- **Separately, and more fundamentally:** this repo already ran a real,
  documented HQ-level research/governance cycle on Flaim
  (`docs/hq/master/fantasy_plugin_research_canonicalization_closeout_v1_20260711/`,
  see section 3) that reached a **formal, still-standing verdict**: Flaim's
  own adapter path is `BLOCKED` for production, manual-consultation-only is
  `PERMITTED_WITH_CAVEATS_AND_TERMS`, and
  `docs/hq/master/.../PROVIDER_CHANGE_REENTRY_GATE.md` explicitly states "No
  immediate Flaim rerun is authorized" absent one of eight named reentry
  triggers (e.g., corrected add/drop filtering, explicit trade-side mapping,
  provider source-as-of/version fields, written persistent-use rights — none
  of which this pass found evidence of having occurred). **This pass did not
  build any Flaim adapter or client — correctly, per both the task
  instruction and this repo's own pre-existing governance gate — and flags
  that any future Flaim integration work should re-read that closeout
  packet first, since it is a real, deliberate, still-binding decision, not
  an oversight.**

## 2. Flaim read-only pull of KHA/403N18th — NOT ATTEMPTED (correctly)

Since Flaim is confirmed unreachable from this process (section 1), step 2 of
the task (pull current ESPN data via Flaim) does not apply. No attempt was
made to reach Flaim, request its credentials, or simulate its output.

## 3. Real prior HQ research on Flaim found in this repo — INSPECTED CODE

Not previously surfaced in the Sunday Readiness cycle's own investigation
(that cycle only checked for an ESPN *client*, correctly found none, and did
not search for "Flaim" by name). This pass found a real, dated, already-closed
HQ research packet directly on point:
`docs/hq/master/fantasy_plugin_research_canonicalization_closeout_v1_20260711/`.

Key facts, read directly from that packet this pass:
- **Verdict:** `GREEN_FANTASY_PLUGIN_RESEARCH_SANITIZED_AND_CLOSED_MANUAL_ONLY`;
  overall research verdict
  `YELLOW_PLUGIN_RESEARCH_USEFUL_WITH_SCORING_AND_GOVERNANCE_CAVEATS`.
- **Flaim classification:** `USEFUL_MANUALLY_NOT_READY_FOR_ADAPTER`. "One 2026
  Sleeper league connected successfully" during that audit (`SANITIZED_
  EXECUTIVE_VERDICT.md`) — i.e., the one real connection test on record in
  this repo was Sleeper, not ESPN; this does not prove or disprove Flaim's
  real ESPN capability today (the `SKILL.md` found in section 1 does claim
  ESPN support), it only means this repo's own prior test evidence is
  Sleeper-only.
- Real named weaknesses found in that audit: standings materially
  misrepresented, add/drop normalization materially unsafe, exact trade-side
  reconstruction unsafe, free-agent retrieval capped/incomplete, FLEX
  eligibility and keeper/dynasty/playoff semantics incomplete, most records
  lacking a provider as-of/version field.
- **Production external influence: `0%`. Flaim adapter: `BLOCKED`.** Manual
  consultation only, under a real, specific list of permitted uses (explicit
  league settings, lineup-slot counts, roster-membership snapshots,
  provider-ID-based ownership review, tentative matchup context, individual
  player-identity lookup) and a real, specific list of prohibited
  authoritative uses (standings rank, season phase, playoff status, complete
  free-agent pool, add/drop direction, exact trade sides, transaction-window
  completeness, "current freshness without a source-as-of field," production
  source truth) — `MANUAL_PLUGIN_OPERATING_GUIDE.md`.
- **Reentry is explicitly gated**, not permanently closed: `PROVIDER_CHANGE_
  REENTRY_GATE.md` lists 8 concrete triggers that would reopen a narrow,
  re-scoped test (not full production integration) — none confirmed present
  this pass.
- This packet's source commit (`work/fantasy-plugin-accuracy-gate-v1-20260711`)
  was reviewed read-only and never merged/pushed; 54 restricted raw-receipt
  files (real provider responses from the original test) were deliberately
  excluded from canonical HQ for privacy. This pass located but **did not
  open** the original, unsanitized worktree
  (`C:\Users\codex-agent\Documents\Niners War Room\Niners-War-Room-fantasy-
  plugin-accuracy-gate-v1-20260711\...\raw_receipts\flaim`) — correctly, per
  the existing privacy boundary; its existence is noted only as further
  independent confirmation that a real Flaim connection test genuinely
  happened once, in July, not as a source consulted this pass.
- A separate, single live reference to Flaim already exists in production
  code: `src/application/desktop_facade.py` line ~3753, a comment citing
  `github.com/jdguggs10/flaim` PR #294 as third-party corroboration for the
  real Sleeper `waiver_type` FAAB-detection convention (this is the same
  still-open bug the Sunday Readiness cycle flagged for Worker 3/a later
  worker — see section 6). This is a documentation citation only, not a code
  dependency on Flaim.

**Conclusion for the owner:** this codebase's relationship with Flaim is not
"never evaluated" — it was evaluated once, formally, found genuinely useful
only as a manual, non-authoritative human consultation aid, and explicitly
blocked from any adapter/production role pending a documented reentry
trigger. Today's owner-supplied "Flaim shows these 4 leagues" report is, on
present evidence, most likely describing Flaim/ChatGPT's own separate UI (per
the coordinating session's own framing) — this pass found no mechanism by
which that information could have reached or originated from this NWR
codebase.

## 4. Fantasy Gamers refresh (Sleeper, existing working connection) — LIVE OBSERVATION

Real, fresh, GET-only Sleeper API calls this pass (`state/nfl`, `league/
1312983576827920384`, `.../rosters`, `.../users`), independent of and
reconfirming the Sunday Readiness cycle's own capture from the prior evening.

- Current provider week (real, live `state/nfl`): **week 2, regular season,
  2026** — unchanged from the prior cycle's own live check, re-confirmed
  fresh rather than assumed.
- League: `Fantasy Gamers`, `status: in_season`, `season: 2026`,
  `total_rosters: 10`. `waiver_budget: 100`, `waiver_type: 1`,
  `trade_deadline: 12`, `playoff_teams: 6`, `playoff_week_start: 15`,
  `reserve_slots: 2`. `roster_positions`: QB, RB, RB, WR, WR, TE, FLEX, K,
  DEF, BN×6 (has a DST slot).
- **Owner/roster mapping — reconfirmed live, MATCHES the owner's table
  exactly:** `owner_id 1000507609050337280` → `roster_id 9` →
  `display_name "scolety"` → team name "Brown Town & Big Mike". The owner's
  table says "Roster 9" for Fantasy Gamers — **confirmed correct.**
- Real roster 9 (fresh pull, this pass): 15 rostered (14 players + "NE"
  DST), 9 starters, `reserve: None`, `taxi: None`, record `1-0`,
  `fpts: 156.96`, `ppts: 156.96` (still an exact match — optimal lineup
  started), `waiver_position: 6`, `waiver_budget_used: 0`, `total_moves: 0`.
  **Identical to the Sunday Readiness cycle's own capture from ~21 hours
  earlier** — a real, disclosed fact, not a stale-data concern: it means no
  roster moves have happened in this league since that capture, verified by
  a fresh call, not assumed from the old one.
- **Zero-writes verification (real, this pass):** fetched `rosters` twice
  (before/after this section's other work), structural Python-object
  equality check on the parsed JSON — **`True`, identical**, confirming no
  write occurred as a side effect of this pass's own reads.

## 5. Las Vegas Enginerds refresh (Sleeper, existing working connection) — LIVE OBSERVATION

Same method, real fresh GET-only calls this pass (`league/
1344772855908290560`, `.../rosters`, `.../users`).

- League: `Las Vegas Enginerds`, `status: in_season`, `season: 2026`,
  `total_rosters: 10`. `waiver_budget: 100`, `waiver_type: 2`,
  `trade_deadline: 99` (none set), `playoff_teams: 4`,
  `playoff_week_start: 16`, `reserve_slots: 2`, `pick_trading: 1`.
  `roster_positions`: QB, RB, RB, WR, WR, WR, TE, FLEX, FLEX, K, BN×14 (24
  slots, confirmed still no DST/DEF slot).
- **Owner/roster mapping — reconfirmed live, MATCHES the owner's table:**
  `owner_id 1352768154031374336` → `roster_id 7` → `display_name "mcolety1"`
  → team name "Niners". The owner's table says "Niners — verify existing
  roster-7 mapping" — **verified correct via this pass's own fresh call, not
  a cached assumption.** `co_owners: ["1000507609050337280"]` (the same
  Sleeper user_id that owns Fantasy Gamers roster 9) still present,
  unchanged, consistent with the prior cycle.
- Real roster 7 (fresh pull, this pass): 28 rostered players, 10 starters,
  `reserve: ["11638", "12484"]` (2, matches `reserve_slots: 2`), `taxi: null`.
  Record `1-0`, `fpts: 108.10`, `ppts: 144.70` (same real actual-vs-optimal
  gap as the prior cycle found), `waiver_position: 2`,
  `waiver_budget_used: 0`, `total_moves: 0`. Identical to the prior cycle's
  capture — same interpretation as Fantasy Gamers above: reconfirmed
  unchanged via a fresh call, not assumed.
- **Zero-writes verification:** same before/after structural-equality method
  as Fantasy Gamers — **`True`, identical.**

Note: as the prior cycle already established and this pass did not
re-litigate, Las Vegas Enginerds is not currently a Redraft profile in this
worktree (Dynasty-only import exists); making it usable in Redraft's own
weekly tools remains out of this pass's scope.

## 6. KHA league ID reconciliation (`1298250946`) — INSPECTED CODE, UNDETERMINED (correctly)

**Existing profile, inspected fresh this pass:**
`local_exports/redraft_v1/profiles/fb1c49402c7644a99120197d41344bbb.json` —
`provider: "espn"`, **`provider_league_id: null`**, `league_name: "2026 KHA
High Stakes League"`, `team_count: 16`, `created_at_utc: 2026-09-02T03:52:58Z`,
`updated_at_utc: 2026-09-02T04:01:25Z`. Unchanged since the Sunday Readiness
cycle's own read.

**Also checked this pass (not checked by the prior cycle): the real native
AppData install's own KHA-related receipt files**, since the analogous
403 N 18th receipt (see below) is the one place this codebase has ever
recorded an ESPN league ID for that other league:
- `%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\projections\2026\
  archive_2026_09_02_kha_draft_day_approval\
  DRAFT_DAY_AUTHORIZATION_kha_20260902_expired.json` — a real, expired
  draft-day freshness-bypass receipt for KHA's 2026-09-02 draft.
  `effective_scope: "2026 KHA High Stakes League draft only (2026-09-02,
  ESPN, 16-team, full PPR)"` — **no numeric ESPN league ID anywhere in this
  file.**
- Contrast: the equivalent 403 N 18th receipt
  (`state/redraft/projections/2026/DRAFT_DAY_AUTHORIZATION.json`) DOES
  contain the numeric ID inline: `effective_scope: "403 N 18th and friends
  real draft only (2026-09-07 8:00 PM MDT, ESPN leagueId 1009373442,
  8-team, full PPR)"`.
- A repo-wide + native-install-wide grep for `1298250946` and for `kha`
  found **zero machine-readable occurrence of the numeric ID `1298250946`
  anywhere in this worktree or the real native install**, and no
  KHA-specific hit beyond incidental substring matches inside binary
  browser-cache files (`EBWebView/.../Cache_Data/*`, confirmed by manual
  inspection of the match list to be cache noise, not real data).

**Conclusion: genuinely UNDETERMINED, and correctly left that way.** This
codebase has **never**, at any point, recorded any ESPN league ID for KHA —
not in the profile JSON, not in either draft-day authorization receipt, not
anywhere else searched. There is therefore no existing stored ID for
`1298250946` to be compared against, confirmed to match, or found to
conflict with. This pass cannot determine, from anything available in this
codebase, whether `1298250946` is the same real KHA league now correctly
identified for the first time, or a genuinely different league object on
ESPN's side (e.g., a fresh 2026 league created separately from whatever ESPN
league the owner drafted the 2026-09-02 KHA draft in). No ESPN read access
exists anywhere in this codebase (reconfirmed fresh this pass: `grep -rniE
"class.*Espn|espn_service|EspnClient|espn\.com/apis|fantasy\.espn" src/` →
zero matches, same as the prior cycle found) and Flaim is unreachable
(section 1), so there is no live-data path available this pass to resolve
this independently either.

**Per the hard requirement: the existing KHA profile
(`fb1c49402c7644a99120197d41344bbb.json`) was NOT modified, its
`provider_league_id` was NOT set to `1298250946` or anything else, and no
merge/overwrite of any kind was performed.** `1298250946` is recorded here,
in this ledger, as a documented, unverified data point only, for a future
worker or the owner to resolve deliberately (e.g., by the owner confirming
directly in their own ESPN account whether the KHA league URL/ID matches, or
via a future authorized Flaim/ESPN read once one becomes reachable).

## 7. 403 N 18th — INSPECTED CODE, reconfirmed, no change

Existing profile `local_exports/redraft_v1/profiles/
4b4a990faf124ce7a5d612537ba5943b.json`: `provider: "espn"`,
`provider_league_id: null` (same known gap as the prior cycle documented —
the real ID lives only in the native-install receipt file, not in the
profile JSON itself). The owner's new table states ESPN league ID
`1009373442` for "403 N 18th and friends," Team 5, "Spencer's Smart Team."
**This exactly matches the ID already on record** in
`DRAFT_DAY_AUTHORIZATION.json` (`ESPN leagueId 1009373442`, quoted in full in
section 6 above) — i.e., unlike KHA, this is a real, independent
confirmation that the owner-supplied ID for 403 N 18th is consistent with
this codebase's own prior record, not a new or conflicting data point.
Profile itself was not modified (still no ESPN client exists to refresh it
against). No team/owner-slot data ("Team 5 — Spencer's Smart Team") exists
anywhere in this codebase to cross-check against — not attempted, not
fabricated.

## 8. Do the existing profiles actually consume current data? — INSPECTED CODE

Per the owner's explicit instruction ("profile visibility alone is
insufficient"), this was checked directly, not assumed:

- **Fantasy Gamers and Las Vegas Enginerds (Sleeper):** YES, genuinely
  current. Both leagues' weekly tools (Start/Sit, Improve Team, Weekly Home)
  call live Sleeper endpoints on every request (per the Sunday Readiness
  cycle's own code-level verification, re-confirmed structurally unchanged
  this pass since no application code was touched) — this is real, live
  per-request data, not a cached snapshot. Sections 4-5 above independently
  reconfirm the underlying Sleeper data itself is live and current as of
  this pass.
- **KHA and 403 N 18th (ESPN):** NO — confirmed, not merely repeated from the
  prior cycle. Both profiles' only "current" data is the historical draft
  board and (for 403 N 18th) `prospective_decision_log`/`nwr_pure_
  experiments` NWR-internal activity — genuinely no post-draft roster,
  transaction, or standings data from ESPN exists anywhere for either
  league, confirmed by direct inspection this pass of both profiles' full
  key sets and the native-install receipt files (section 6-7). The app's own
  weekly surfaces already self-report "Sleeper league required" for both —
  an honest, correct, pre-existing refusal, unchanged this pass.

## FILES CHANGED THIS PASS

- `docs/codex/connection_update_20260919/LEDGER.md` (new — this file).

No application code, test, config, or profile file was modified. No writes
were made to any Sleeper or ESPN endpoint (every call was a plain GET,
confirmed zero-writes via before/after structural diff for both refreshed
leagues). No existing profile was recreated, overwritten, or merged. The
worktree's pre-existing untracked scratch files from Worker 6 of the prior
cycle (`.worker6_*`, `local_exports.backup-20260918T230905Z/`) were left
exactly as found — not touched, not committed.

## OPEN ISSUES FOR NEXT WORKER

1. **The real `waiver_type` FAAB-detection bug already flagged by the prior
   cycle is STILL unfixed** (`desktop_facade.py` ~L3736 checks
   `raw_waiver_type == 1`; strong, now-doubly-corroborated evidence — the
   prior cycle's own third-party citation plus this pass's independent
   discovery of the same `github.com/jdguggs10/flaim` PR #294 citation
   already live in that exact code comment — says real Sleeper FAAB is
   `waiver_type == 2`, backwards for both real leagues on record). This is
   the "missing-projection arithmetic bug" area the dispatching brief
   mentioned as Worker 2's target — **verify whether this specific
   waiver_type check is the bug in question, or whether a separate,
   different missing-projection arithmetic issue exists elsewhere** (this
   pass did not locate a second, distinct "missing projection" arithmetic
   bug beyond what the Sunday Readiness cycle's Worker 2 already fixed in
   `weekly_lineup_optimizer_service.py` W3 — re-check the owner's exact
   report before assuming which bug is meant).
2. **KHA league-ID reconciliation remains genuinely open** — `1298250946` is
   documented (section 6) but unverified against anything in this codebase.
   Do not set it into the existing profile's `provider_league_id` without a
   deliberate, owner-confirmed decision (or a future working ESPN/Flaim read
   path that can check it directly).
3. **Flaim adapter work remains explicitly BLOCKED by this repo's own prior
   governance decision** (section 3) pending one of 8 named reentry
   triggers. Do not build a live Flaim/ESPN client this pass or reflexively
   in a future pass without first re-reading `docs/hq/master/
   fantasy_plugin_research_canonicalization_closeout_v1_20260711/` in full
   and confirming a real trigger exists.
4. **KHA and 403 N 18th remain BLOCKED for any current-state Sunday tool** —
   unchanged, reconfirmed independently this pass via a fresh `grep` for any
   ESPN client in `src/` (zero matches) and via direct inspection of both
   profiles' full data (section 8).
5. Whether the owner's "visible in NWR" phrasing refers to Flaim's own UI
   (flaim.app) or a `claude.ai`/ChatGPT chat surface where Flaim is
   connected as an MCP connector could not be determined from this process
   — this pass found the real, local evidence for what Flaim IS (section 1)
   but has no way to inspect the owner's own claude.ai/ChatGPT account
   configuration. Worth a direct, one-line question to the owner rather than
   further investigation from this side, if a future worker needs certainty
   on this point.

---

## Worker 2 (2026-09-19) — owner-reported missing-projection-treated-as-zero bug, fixed end to end

Separate, precisely-scoped bug fix. Unrelated to Flaim/ESPN (Worker 1,
above) — existing profiles, branch, and worktree untouched otherwise.

### 9. The exact bug — INSPECTED CODE, confirmed exactly as reported

`src/services/weekly_lineup_optimizer_service.py`, `_swap_reasons` (line
612 pre-fix): `delta = round((slot.player.projected_points or 0.0) -
(bumped.projected_points or 0.0), 2)`. The guard a few lines above only
ensures the NEW starter (`slot.player`) has a real projection; the
DISPLACED player (`bumped`) can legitimately have `projected_points =
None` (no real weekly-projection row at all this week — not the same as a
real, known 0.0) and still fell through `bumped.projected_points or 0.0`,
silently substituting 0.0 and fabricating a delta equal to the new
starter's own raw points, presented as a real, known point swing. Exactly
the owner's report.

### 10. Fix — INSPECTED CODE / ACTUAL TEST RESULT

`SwapReason.projected_delta` is now `float | None`, with a new parallel
`delta_basis: str` field (`"KNOWN"` | `"UNKNOWN_MISSING_BENCH_PROJECTION"`).
When `bumped.projected_points is None`, `_swap_reasons` now sets
`projected_delta=None`, `delta_basis="UNKNOWN_MISSING_BENCH_PROJECTION"`,
and an honest summary ("`{bumped}`'s projection is missing this week;
point swing unknown") instead of a fabricated `+X.X`. A real, known 0.0
projection (e.g. a kicker in a bad-weather week) still produces a real,
`"KNOWN"`-basis numeric delta — the fix distinguishes missing from zero,
not just "never show a number here."

### 11. Upstream chain — INSPECTED CODE / ACTUAL TEST RESULT, all four areas checked

- **Recommendations**: Start/Sit's `primaryRecommendation`/swap ordering
  (`desktop_facade.py::redraft_weekly_lineup`) is NOT delta-sorted — it
  follows `_SLOT_ORDER` iteration order, unchanged. No fabricated-high-delta
  promotion risk existed here; verified by reading the code, not assumed.
- **Confidence**: real, previously-undisclosed gap found and fixed. Neither
  `unprojected_starter_count` nor `unresolved_identity_starter_count` ever
  saw a swap's displaced player (he's no longer a starter after
  optimization, by definition), so Start/Sit could report NOMINAL
  confidence while its own TOP recommendation rested on a fabricated point
  swing. Pulled the whole confidence-gate decision out into a new, small,
  pure, independently-tested function, `_start_sit_confidence` (module
  level, `desktop_facade.py`, just above `class DesktopBackendFacade`), and
  added one more branch: the FIRST swap in `swaps_vs_current` (the same one
  surfaced as `primaryRecommendation`) having `delta_basis != "KNOWN"` now
  forces `LOW` confidence with an explicit basis string. 7 new unit tests
  in `tests/test_start_sit_confidence_missing_projection.py` cover every
  branch/priority ordering, including the missing-vs-zero distinction.
- **Totals**: `optimize_weekly_lineup`'s own `total` computation (lines
  ~386-417) verified CORRECT, not assumed — it already excludes any starter
  with `projected_points is None` from `projected_total` (tracks him via
  `unprojected_count` instead), so it never had the "missing as zero" bug.
  Documented this verification directly in `simulate_this_week_add_drop`'s
  own docstring (see next section) since both totals it diffs depend on it.
- **UI**: `desktop/packages/contracts/src/index.ts`'s `WeeklyLineupSwap`
  type updated (`projectedDelta: number | null`, new `deltaBasis` field).
  `desktop/apps/redraft/src/lineup-explain.ts` (`explainLineupSwap`, the
  Start/Sit page's own explain layer) now branches on `deltaBasis` BEFORE
  the close-call branch and returns an honest "Unknown -- missing
  projection" impact string with `tone="warning"`/`confidence="LOW"` —
  never calls `formatSigned(null)`. `desktop/apps/redraft/src/home-action-
  explain.ts` (Weekly Home's action-card layer) was ALSO checked and fixed:
  its existing `Number.isFinite(swap.projectedDelta)` guard happened to
  already degrade `expectedImpact` to `null` correctly for a `null` delta
  (a real but incidental JS-semantics coincidence, not a designed fix) —
  but `why`/`confidence` did not, and would have kept implying a confirmed
  "outscore" comparison; fixed explicitly using the real `deltaBasis` field.
- **Traces**: the Start/Sit decision-trace record
  (`_record_decision_trace_safe`'s `alternatives` list, and the
  `swap_rows`/`primaryRecommendation` the owner-facing
  `DecisionResultEnvelope` also carries) now include `projectedDelta`/
  `deltaBasis` on every swap row, so a missing-projection swap's honest
  uncertainty is preserved in Decision History rather than only fixed in
  the live response.

### 12. `simulate_this_week_add_drop` / waiver engine — INSPECTED CODE, verified correct (not fabricated, one documented residual risk)

Explicitly re-derived rather than assumed. `gain = after.total -
baseline.total` is a fair, symmetric diff of two already-honest totals
(section 11's Totals finding) — never fabricated. The one real remaining
risk checked: could the ADD CANDIDATE itself have `projected_points is
None` and still become a starter, silently OMITTING (not fabricating, but
also not disclosing) his own real contribution from `after.total`? The
ONE real call site
(`desktop_facade.py`'s THIS_WEEK waiver evaluation, ~line 4025-4033)
pre-filters its shortlist to `row.projected_points is not None` BEFORE
ever building an `add_candidate` — confirmed by direct inspection, not
assumed — so this risk does not currently occur in production. Documented
both the verification and the residual risk directly in
`simulate_this_week_add_drop`'s own docstring for a future caller.
`waiver_engine_service.py`'s `sort_key` (`gain = -(candidate.
this_week_lineup_gain or 0.0)`) was checked for the same pattern: verified
the `or 0.0` never actually fires in practice (`gain_missing`, using
`this_week_evaluated` — not this value — already sorts every
non-evaluated candidate last before this tiebreaker is consulted, and
`this_week_lineup_gain` is always a real float, never `None`, whenever
`this_week_evaluated` is `True`) — documented inline as a verified-safe
defensive fallback, not a live bug, no behavior change made.

### 13. Regression tests — ACTUAL TEST RESULT

New/updated, all passing:
- `tests/test_weekly_lineup_optimizer_service.py`: 3 new tests —
  `test_swap_with_real_known_zero_bumped_projection_produces_a_real_numeric_delta`
  (real 0.0 kicker → real `"KNOWN"` delta 9.0),
  `test_swap_with_missing_bumped_projection_is_honestly_unknown_not_fabricated_zero`
  (missing → `None`/`"UNKNOWN_MISSING_BENCH_PROJECTION"`, no fabricated
  12.0), and
  `test_owner_reported_zay_flowers_shaped_case_reproduced_and_fixed` (the
  exact real-world shape, asserts `"+11.7"` never appears).
- `tests/test_start_sit_confidence_missing_projection.py` (new file): 7
  tests covering `_start_sit_confidence`'s every branch and priority
  ordering, including that a `"KNOWN"` delta never trips the new branch.
- `desktop/apps/redraft/src/lineup-explain.test.ts` / `home-action-
  explain.test.ts`: 1 new test each, both asserting no `"+11.7"`/`"+\d"`
  leaks through and the honest unknown state renders instead.
- `makeSwap()` test fixtures and one existing inline test-fixture object
  updated to carry `deltaBasis: "KNOWN"` (required field now).

### 14. Live verification — LIVE OBSERVATION

Rebuilt (`npm run build:redraft`) and restarted both Redraft dev processes
(python `scripts/run_nwr_desktop_api.py` on 127.0.0.1:18742, `vite
preview` on 127.0.0.1:1422) with the fix, replacing Worker 6's stale
pre-fix processes (old pids 43364/49760; new pids 44000/11932 — new log
files `.worker2_backend.log`/`.worker2_preview.log`, old `.worker6_*.log`
files left untouched). Confirmed via Chrome MCP against the REAL, LIVE
Fantasy Gamers and Las Vegas Enginerds Sleeper leagues (both still have a
real, currently-missing Zay Flowers weekly projection, Week 2, as of
2026-09-19 ~4:47 PM):

- **Fantasy Gamers Start/Sit** now shows "Start Marvin Harrison over Zay
  Flowers" · badge "LOW CONFIDENCE — CLOSE CALL" · "Zay Flowers's weekly
  projection is missing this week -- the point swing from this change is
  unknown, not a confirmed gain." · "EXPECTED IMPACT: Unknown -- missing
  projection." No fabricated number anywhere. Note: the real-world
  replacement player is now "Marvin Harrison" rather than the "Michael
  Pittman" named in the owner's original report — an honest, expected
  drift (Sleeper rosters/lineups genuinely change hour to hour), not a
  discrepancy in the fix itself; the underlying mechanism (Zay Flowers
  still missing a projection, correctly handled) is the same.
- **Las Vegas Enginerds Start/Sit** now shows "Start Jalen Coker over Zay
  Flowers" — an EXACT name match to the owner's original report — same
  honest "LOW CONFIDENCE — CLOSE CALL" / "Unknown -- missing projection"
  presentation, no fabricated `+7.6`.

Both leagues' real, live decision sheets are DEMONSTRABLY no longer
producing the fabricated numbers the owner reported. `git status` on
`local_exports/` confirmed zero profile/roster writes from this
verification pass (read-only Start/Sit view only).

### 15. Test results — ACTUAL TEST RESULT

- Targeted Python suites (`test_weekly_lineup_optimizer_service.py`,
  `test_start_sit_confidence_missing_projection.py`,
  `test_waiver_engine_service.py`, `test_desktop_facade_architecture_
  wiring.py`, `test_player_availability_status_consumer_consistency.py`,
  `test_weekly_home_single_snapshot.py`,
  `test_weekly_home_sleeper_fetch_caching.py`,
  `test_decision_envelope_service.py`,
  `test_boundary_property_reliability_pack_v1.py`,
  `test_prospective_outcome_ingestion_orchestrator_v1_service.py`): **206
  passed, 0 failed.**
- `tests/test_desktop_application_api.py`: **4 failed, 46 passed** —
  confirmed PRE-EXISTING and unrelated to this fix by running it BEFORE
  (via `git stash`) and after this pass's changes: byte-identical failure
  set both times (`test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_facade_has_no_streamlit_or_app_component_dependency`). Differs
  from this same worktree's own documented Draft Upgrade HQ 5-failure
  baseline (a different worktree/branch) — not re-litigated here, just
  independently confirmed pre-existing via the stash A/B test, which is
  the rigorous bar this pass used.
- Full desktop vitest suite (`npm run test` in `desktop/`): **30 files,
  503 tests, all passed** (both before and after, run twice for
  confirmation).
- `npm run typecheck` (`tsc -b` for both dynasty + redraft): clean, zero
  errors.
- Note: `docs/codex/prospective_outcomes_v1/multi_league_scale_v1/
  frontend_bench_results.json` gets regenerated (timing-noise diff only,
  no content/shape change) by the full `npm run test` run in `desktop/` —
  reverted with `git checkout --` both times after confirming it was
  benchmark-timing noise, not a real change; not part of this commit.

### 16. Files changed this pass

- `src/services/weekly_lineup_optimizer_service.py` — the core fix
  (`SwapReason`, `_swap_reasons`), plus a verification-documenting
  docstring addition to `simulate_this_week_add_drop`.
- `src/services/waiver_engine_service.py` — verification-documenting
  comment only, no behavior change.
- `src/application/desktop_facade.py` — new `_start_sit_confidence`
  function (confidence-gate fix, extracted for testability), swap payload/
  trace/envelope now carry `deltaBasis`/`projectedDelta` honestly.
- `desktop/packages/contracts/src/index.ts` — `WeeklyLineupSwap` type.
- `desktop/apps/redraft/src/lineup-explain.ts` — Start/Sit explain layer.
- `desktop/apps/redraft/src/home-action-explain.ts` — Weekly Home explain
  layer.
- `tests/test_weekly_lineup_optimizer_service.py` — 3 new regression
  tests.
- `tests/test_start_sit_confidence_missing_projection.py` — new file, 7
  tests.
- `desktop/apps/redraft/src/lineup-explain.test.ts` /
  `home-action-explain.test.ts` — new tests + fixture updates.
- This ledger.

### OPEN ISSUES FOR WORKER 3

1. Verify ESPN status for Start/Sit, Improve Team, K/DST streaming for
   both ESPN leagues (KHA, 403 N 18th) — per Worker 1's findings (sections
   6-8 above), this is almost certainly still BLOCKED (no ESPN client
   exists anywhere in `src/`, both profiles have no post-draft ESPN data)
   — but verify precisely against current code, don't just cite Worker 1.
2. Refresh the Sunday decision sheets for Fantasy Gamers and Las Vegas
   Enginerds now that this fix is live — the sheets that originally showed
   the fabricated "+11.7"/"+7.6" numbers need to be regenerated so they
   show the corrected, honest output (see section 14 above for exactly
   what the corrected live output now looks like for each league).
3. Reassess the Purdy/Harrison waiver suggestion mentioned in the
   dispatching brief — not investigated this pass (out of this pass's
   precise scope), needs its own direct look.
4. Run the full test suite and push (this pass deliberately did NOT push,
   per instructions — Worker 3 is the one that pushes once everything is
   verified). `git log -1` before pushing should show this pass's commit
   on top of Worker 1's.
5. Both Redraft dev processes (backend :18742 pid 44000, preview :1422 pid
   11932) were left RUNNING with this pass's fix already live — no restart
   needed before continuing manual verification, unless further code
   changes require a rebuild.
