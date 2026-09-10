# Part 3 -- Live Re-Verification Pass (after Part 2's disclosed rendering gap)

Scope decision, disclosed up front: Part 2 (`NWR_V2_CONFIRMATION_PART2_PRODUCT_CONTINUATION_V1.md`) ended
without starting a dev-server/Chrome stack at all ("Lane E... not independently re-rendered this pass").
This pass's highest-value contribution is closing exactly that gap with real, fresh, rendered evidence,
plus the two specific data-source checks the governing directive named explicitly (FFA weekly granularity,
`nflreadpy` access) that no prior pass had run as a literal, evidenced check. No in-season capability was
built this pass either -- three consecutive passes on this branch have now independently reached the same
BLOCKED verdict on weekly projections via different evidence each time (absence checks, diff-scope checks,
and now schema/API checks); re-attempting a full build was judged lower value than deepening verification
rigor and closing disclosed gaps, consistent with the directive's own permission to scope down honestly.

## 1. Weekly-projection data-source audit (directive section 12, done for the first time as a literal check)

- **FFA archive** (`C:\NWR_HISTORICAL_DATA\FFA_OFFICIAL\`): every season folder 2012-2026, both
  `raw_stats` and `projections`, confirmed **season-level only** by two independent signals: (a) every
  filed filename carries `_wk0` before organization (duplicates folder preserves the original names,
  e.g. `2026_projections_EXACTDUP_projections_2026_wk0 (2).csv`); (b) the real 2026 projections file's own
  header row has no week column at all: `player,position,team,bye_week,points,sd_pts,dropoff,floor,
  ceiling,points_vor,floor_vor,ceiling_vor,rank,floor_rank,ceiling_rank,position_rank,tier,age,adp,aav,
  uncertainty,experience` -- a single full-season point total per player, not 18 weekly rows. **Confirmed:
  FFA has no weekly granularity anywhere in the archive, for any season including 2026.**
- **`nflreadpy` network access**: confirmed live and working this pass --
  `nflreadpy.load_schedules(seasons=[2025])` returned a real 285-row x 46-column DataFrame (one row per
  game). This is real, usable data for schedule/opponent/matchup/SoS-type inputs (the DST/K streamer and a
  future Trade/Compare "schedule" lens could consume it), but it is **not** a source of per-player weekly
  *point projections* -- schedules tell you who plays whom, not how many fantasy points a player is
  forecast to score in a given week.
- **Season-timing note, newly made explicit this pass**: today is 2026-09-09 and Week 1 of the 2026 NFL
  season has not been played yet (the Fantasy Gamers draft itself is today). This means even the
  "real trailing-performance data becomes available after games are played" path the directive names for
  DST/K streamers has **zero 2026 weeks to trail on yet** -- not a new blocker, just a reason the existing
  DST/K streamers correctly lean on preseason FantasyPros consensus ECR rather than trailing stats right
  now, and will have real trailing data to add starting after Week 1 is actually played.
- **Verdict, now evidenced rather than inferred**: the weekly-player-point-projection gap is real,
  confirmed via direct schema/API inspection this pass (not just absence-of-file checks as in prior
  passes). No governed weekly-projection model exists in this repo, in the FFA archive, or via
  `nflreadpy` (which provides real games/rosters/stats, not forward point forecasts). Start/Sit, Waivers'
  weekly-value component, and FAAB's weekly-value component remain correctly BLOCKED on this exact,
  now-triple-confirmed gap.

## 2. Live rendered re-verification (closes Part 2 Lane E's and the retry-queue report's disclosed gap)

Backend + frontend launched sequentially in this worktree (never the owner's real AppData install,
confirmed by the fresh isolated-store state below), verified via `curl` before touching the browser, and
cleanly killed afterward (`Get-NetTCPConnection` confirmed both ports free post-shutdown, no orphaned
process).

Found this worktree's isolated `local_exports` already carrying the retry-queue report's own three QA
profiles from that prior pass (QA League A/B/C, all `provider: local`) -- reused rather than recreated.

Driven live via Chrome MCP, zero console errors/warnings across the entire session:

- **League Chooser**: renders all 3 real local profiles; the ACTIVE badge and "Open workspace" links work.
- **League title -> chooser return path**: exists and works, but is NOT the sidebar's top-left
  "Niners War Room" brand text (that text is inert, not a link -- confirmed via `read_page`/`find`, it has
  no `onClick`/`href`). The real return-to-chooser affordance is the **active league name inside the
  content header** (`<Link to="/leagues">`, `title="Open league chooser"`), which works correctly. This is
  a minor labeling mismatch against the directive's literal "top-left" phrasing, not a missing capability
  -- a working escape/debug path exists, just not exactly where that one sentence describes it.
- **Rapid league-switch stress test** (A -> C -> B, directive section 15's substitute for
  Fantasy-Gamers/403/Tester since those are the owner's real leagues and out of bounds for this worktree):
  header league name/format, Draft Setup's team-count (10/12/12) and slot grid (1-10 / 1-12 / 1-12), and
  the position-filter row (SFLX chip appears only for the Superflex league) all updated correctly on every
  switch with **no stale leak observed** and **zero console errors** across the whole sequence.
- **Weekly Home, Free Agents, Compare, K/DST Streamer, global search palette**: all render cleanly and
  **honestly disclose** their real blocked/empty states rather than fabricating data -- "PROJECTIONS
  BLOCKED" / "Governed 2026 projection snapshot is missing" (Weekly Home), "Sleeper league required --
  ESPN and local profiles have no live roster source" (Free Agents, correct for these `provider: local`
  QA profiles), "Two players required" / empty player dropdowns (Compare, correct since no governed
  ranking pool is loaded in this isolated store), "No matching action" for a global player-name search
  (correct, same empty-pool reason), and K/DST Streamer's own explicit disclaimer ("NWR does not
  calculate a K/DST score or combine ECR with Redraft projections").
- **Still not reached, same reason as every prior pass**: in-draft/board-level rendering (`Start Draft`
  would fail on the same missing governed-2026-projection-snapshot gate). This pass did not attempt to
  install a projection snapshot into this worktree's default store (same owner-approval-gate reasoning as
  the retry-queue report).

**RENDERED ACCEPTANCE this pass: PASS at every pre-draft layer reachable without governed 2026 projection
data (Chooser, league-switch stress test, Weekly Home, Free Agents, Compare, K/DST Streamer, global
search) -- zero console errors throughout. In-draft/board rendering not reached, same disclosed,
unchanged blocker as every prior pass on this branch.**

## 3. Sleeper resync regression -- re-run fresh, not assumed (directive section 18)

Read `resync_sleeper_redraft_profile` in `src/services/sleeper_redraft_owner_service.py` end-to-end: the
`roster_limits` merge fix found 2+ passes ago is still in place --
`merged_roster_limits = {**existing.draft.roster_limits, **template.draft.roster_limits}` (K/DST refreshed
from the real Sleeper roster settings; any other owner-entered position maximum is preserved, not
discarded). `tests/test_sleeper_redraft_owner_service.py::test_resync_preserves_owner_entered_roster_limits_while_refreshing_kdst`
covers exactly this regression by name. Ran the full file fresh this pass: **8/8 passed.** Confirmed
still fixed, not just assumed from memory.

## 4. Trade Analysis -- location confirmed, not attempted (unchanged scope decision)

Confirmed real trade infrastructure exists at `src/services/draft_day_trade_lab_service.py`,
`trade_decision_assistant_service.py`, `trade_roster_negotiation_service.py`, `trade_service.py`,
`trade_brief_export_service.py`, and two model-v4-sprint trade-review services -- all real, all currently
wired into the Dynasty app only. Wiring any of this into the Redraft league workspace remains the correct
next-increment recommendation from Part 2, unchanged and not attempted this pass either (same reasoning:
a genuine multi-file cross-app integration, not a verification task, and this pass's remaining budget was
prioritized toward closing the disclosed rendering gap and running the two named data-source checks
instead).

## 5. Net effect on the Part 2 inventory table

No row in Part 2's Lane A capability table changes status this pass. What changes is evidentiary strength:
Weekly/ROS Projections' BLOCKED verdict is now backed by a direct FFA-schema check and a live
`nflreadpy` call (not just file-absence checks); Sleeper Resync's WORKING verdict is now backed by a fresh
8/8 test run; League Chooser / League Context Switch / Free Agents / Compare / K-DST-Streamer are now
backed by a fresh live-rendered pass with zero console errors, not carried forward from an older dated
pass as Part 2 explicitly flagged it was doing.

