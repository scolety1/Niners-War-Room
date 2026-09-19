# Sunday Decision Sheet — Fantasy Gamers

**Refreshed by Worker 3 (connection/update pass, 2026-09-19 ~5:00 PM Mountain)**
against the real, live, running Redraft app (final HEAD after this pass —
see `docs/codex/connection_update_20260919/LEDGER.md` Worker 3 section),
real browser session, GET-only Sleeper + FantasyPros calls throughout. All
figures below are LIVE OBSERVATION from this refresh unless marked
otherwise. This sheet supersedes the version prepared by Worker 6 (prior
Sunday Readiness cycle) — in particular, section 2's "+11.7" lineup-swap
figure and section 3's "+2.3"-framed pickup were both re-pulled fresh
this pass, not carried over.

## 1. League / owner / capture

- **League:** Fantasy Gamers — Sleeper `1312983576827920384`, 10-team PPR,
  1QB. **Owner:** scolety (`user 1000507609050337280`), roster 9, team
  "Brown Town & Big Mike."
- **Season / week:** 2026 regular season, **real live provider week = 2**
  (fresh `GET https://api.sleeper.app/v1/state/nfl` this pass). League is
  `IN_SEASON`, real record 1-0 (#1 of 10 by points for, 157.0 PF, 152.8 PA),
  opponent this week "shittin and tuten," current in-progress score 0.0-0.0
  at capture time (Sunday slate not yet started).
- **Capture time (this pass, live):** weekly projections SLEEPER, Week 2,
  updated **Sep 19, 4:56-4:58 PM Mountain** (shown live in-app). This is a
  fresh pull from ~24 hours after Worker 6's original capture and a few
  hours after Worker 2's own live verification of the missing-projection
  fix — all three captures independently agree the underlying Sleeper data
  is genuinely current, not stale.
- **Readiness verdict: READY**, with the missing-projection honesty fix
  (this pass's dispatching cycle, commit `ac67ade3`) now confirmed live in
  production. Full weekly lineup, waiver, FAAB/priority, and K/DST tooling
  all loaded correctly and returned real, live, non-error results this
  pass.

## 2. Lineup — current vs. proposed (RE-PULLED FRESH, real roster drift from the prior sheet)

**Real recommended change (1), live right now:** Start **Marvin Harrison**
(WR, ARI) over **Zay Flowers** (WR, BAL) — flagged **LOW CONFIDENCE — CLOSE
CALL**. **EXPECTED IMPACT: Unknown — missing projection.** In-app copy,
verbatim: *"Zay Flowers's weekly projection is missing this week — the
point swing from this change is unknown, not a confirmed gain."*

This is the corrected, honest presentation from Worker 2's fix
(`_swap_reasons` / `deltaBasis`), reconfirmed live by this pass, not the
fabricated **"+11.7"** figure the prior (Worker 6) version of this sheet
reported. Two real, disclosed facts about why the specific player name
changed since the prior sheet: (a) **Michael Pittman** — the player named
in the owner's original bug report and in the prior sheet's own swap-in
slot — is now ALSO showing a missing projection this week (`"—"` in the
bench table below) and is no longer the app's top recommendation; (b) the
real Sleeper roster/lineup genuinely changed in the ~24 hours since the
prior capture (an honest, disclosed drift, not a discrepancy in the fix).
Zay Flowers himself has been missing a weekly projection continuously
across all three captures this cycle (Worker 6's original, Worker 2's
verification, and this pass) — the same real, persistent Sleeper data gap
each time, not a new or intermittent issue.

**Proposed starting lineup (projected total 115.0 pts, live Week 2 data):**

| Slot | Player | Pos/Team | Proj pts | Note |
|---|---|---|---|---|
| QB | Caleb Williams | CHI · QB | 17.8 | Close call vs. Trevor Lawrence (bench), gap 1.4 pts |
| RB | Jonathan Taylor | IND · RB | 18.7 | OK |
| RB | De'Von Achane | MIA · RB | 16.8 | OK |
| WR | Chris Olave | NO · WR | 15.5 | OK |
| WR | **Marvin Harrison** | ARI · WR | 9.2 | Recommended swap-in, close call vs. Carnell Tate (bench), gap 0.8 pts |
| TE | Kyle Pitts | ATL · TE | 10.0 | OK |
| K | Ka'imi Fairbairn | HOU · K | 7.3 | OK (see K/DST section) |
| DST | NE D/ST | NE · DST | 8.7 | OK (see K/DST section) |
| FLEX | Travis Etienne | NO · RB | 11.0 | OK |

**Bench (6 players, real live pull):** Trevor Lawrence (QB, 16.4 — real
close-call backup, 1.4 behind Caleb Williams), Carnell Tate (WR, 8.5 —
real close-call FLEX/WR2 alternative, 0.8 behind Marvin Harrison), Kenny
Gainwell (RB, 7.9), Wan'Dale Robinson (WR, 7.7), **Michael Pittman (WR,
missing projection — shown as "—", not silently dropped)**, **Zay Flowers
(WR, missing projection — shown as "—", not silently dropped)**.

- No reserve/taxi players and no locked-unavailable players on this roster
  this week (Sleeper `reserve: None`), reconfirmed this pass.

## 3. Waivers / pickups — REASSESSED this pass (owner-directed judgment check)

**What the app's current, real, live Improve Team → Targets (THIS_WEEK
mode) surface actually shows right now, top of list:**

| Rank | Move | THIS WEEK gain | REST OF SEASON net vs. dropping Marvin Harrison |
|---|---|---|---|
| 1 | ADD Xavier Worthy / DROP Marvin Harrison | +0.6 pts (becomes starter) | **-0.7** |
| 2 | ADD Brock Purdy / DROP Marvin Harrison | +0.5 pts (becomes starter) | **-1.7** |
| 3 | ADD Malik Washington / DROP Marvin Harrison | +0.0 pts (becomes starter) | **-0.6** |
| 4 | ADD Dalton Schultz / DROP Marvin Harrison | (not fully captured — same pattern) | — |

**Honest reassessment, per the owner's explicit instruction not to repeat
a move solely because of a small weekly modeled gain:**

- Every real, current top-ranked THIS_WEEK target requires dropping
  **Marvin Harrison** for a genuinely trivial weekly lineup gain — **+0.6,
  +0.5, and +0.0 projected points**, respectively. These are not
  meaningful gains; they are noise-level.
- The app's own REST_OF_SEASON view — checked directly this pass, not
  assumed — shows a **NEGATIVE** "net vs. dropping Marvin Harrison" for
  every one of them (-0.7, -1.7, -0.6). Marvin Harrison's own real
  standalone rest-of-season value (checked directly via the Players/
  Rankings surface: overall rank #132, WR54, 125.8 ROS projected points)
  carries a **value-over-replacement of 0.0** — i.e. he is himself already
  at replacement level, and every one of these "targets" is real, live,
  computed by the app's own model to be WORSE than replacement level for
  this roster. This is not a fabricated or assumed conclusion; it is
  read directly off the same live figures the app itself displays.
- **Verdict: HOLD Marvin Harrison.** No real waiver target currently
  available to this team offers a genuine, net-positive rest-of-season
  trade versus keeping him. The correct honest framing is that **this
  week's small usable-lineup gain does not justify the drop** — this
  replaces the prior sheet's "ADD Brock Purdy / DROP Marvin Harrison...
  +2.3 pts" framing, which is no longer the real current top target (the
  roster and free-agent pool have moved on in the ~24 hours since) and,
  more importantly, would have been the exact "chase the biggest weekly
  number" pattern the owner asked this pass to check for. On today's real
  numbers, doing so would be a real, disclosed net value LOSS on a
  rest-of-season basis for a trivial in-week gain.
- This is a genuine, evidence-based judgment call, not a code change — the
  underlying THIS_WEEK/REST_OF_SEASON split and the "net vs. dropping"
  field were already correctly computed and displayed by the app before
  this pass; the prior decision sheet simply hadn't surfaced the honest
  net-negative framing explicitly. No ranking/valuation code was touched
  this pass (out of scope, per the hard boundary).
- No genuinely useful RB/WR/TE alternative showed a real, worthwhile
  weekly gain this session; the rest of the THIS_WEEK-ranked list is the
  same trivial-gain pattern.
- Acquisition mechanics (unchanged from the prior sheet, reconfirmed): this
  is **not** a FAAB league — real Sleeper `waiver_type` reports rolling
  **waiver priority**. Recheck current priority/claims live in-app before
  Sunday if a claim is still wanted despite the honest HOLD recommendation
  above.

## 4. Kicker and DST — reconfirmed live, same real result as the prior sheet

- **Current K: Ka'imi Fairbairn** (HOU), real FantasyPros consensus rank
  **#4** for Week 2. Real, available alternatives (Eddy Pineiro #3, Cairo
  Santos #5, Tyler Bass #9) — small, marginal upgrade at best, KEEP is
  defensible.
- **Current DST: New England D/ST**, real FantasyPros consensus rank
  **#8** for Week 2. Real, available upgrade: San Francisco 49ers (#3).
  Same judgment as the prior sheet: a defensible KEEP given DST streaming's
  low predictive reliability, not a forced move.
- K/DST Streamer confirmed working live for this (Sleeper) league this
  pass — no regression from Worker 2's fix, no backend error, real
  FantasyPros ECR data returned on refresh.

## 5. Contingencies

- No live questionable/practice-report/injury-status feed exists in this
  app (unchanged this pass). No player on this roster is currently shown
  as a sourced OUT/questionable exclusion.
- Real close calls to re-plan around if a starter is downgraded: Trevor
  Lawrence (QB bench, 1.4 behind Caleb Williams) and Carnell Tate (WR
  bench, 0.8 behind Marvin Harrison's WR slot).
- No games in this matchup week had kicked off as of this pass's capture
  time (Sep 19, ~5:00 PM Mountain, day before the Sunday slate).

## 6. Recheck before kickoff / cannot conclude

- **Saturday/Sunday readiness cannot establish the final inactive list —
  recheck before each relevant game's inactive announcement and roster
  lock.** No live injury/practice-report feed exists in this app.
- **Zay Flowers's projection has now been missing across three independent
  captures over ~24 hours (Worker 6, Worker 2, this pass) — this looks
  like a real, persistent Sleeper data gap for this player specifically,
  not a transient blip.** Recheck in-app before kickoff; if it resolves,
  the Start/Sit recommendation may change back to a real, known-delta
  comparison instead of the current honest "unknown" framing.
- Recheck the live NWR Week 2 lineup/streamer/waiver views again shortly
  before kickoff — a fresh in-app refresh picks up any late Saturday/
  Sunday-morning changes.
- Waiver claims: confirm the league's actual real waiver-processing day/
  time on Sleeper directly.
- No real trade action was taken or recommended here (out of scope).
