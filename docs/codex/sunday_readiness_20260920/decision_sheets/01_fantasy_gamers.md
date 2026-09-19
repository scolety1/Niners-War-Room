# Sunday Decision Sheet — Fantasy Gamers

Prepared by Worker 6 (closure pass), live-verified this session against the
final-HEAD Redraft app (`1149b89d`), real browser session, GET-only Sleeper
calls throughout. All figures below are LIVE OBSERVATION from that session
unless marked otherwise.

## 1. League / owner / capture

- **League:** Fantasy Gamers — Sleeper `1312983576827920384`, 10-team PPR,
  1QB. **Owner:** scolety (`user 1000507609050337280`), roster 9, team
  "Brown Town & Big Mike."
- **Season / week:** 2026 regular season, **real live provider week = 2**
  (fresh `GET https://api.sleeper.app/v1/state/nfl` this session:
  `{"week":2,"season_type":"regular","season":"2026", ...}`). League is
  `IN_SEASON`, record 1-0 (#1 of 10 by points for, 157.0 real Sleeper PF).
- **Scoring basis:** Sleeper's real, full PPR scoring map (`rec: 1.0`,
  `pass_td: 4.0`, `pass_yd: 0.04`, `pass_int: -2.0`, `rush_td`/`rec_td:
  6.0`, `fum_lost: -2.0`), real DST points-allowed tiers, real kicker
  tiers `fgm_0_19: 3.0` … `fgm_60p: 6.0`. Roster has a real DST slot
  (`QB, RB, RB, WR, WR, TE, FLEX, K, DEF, BN x6`).
- **Capture times (this session, live):**
  - Weekly projections: SLEEPER, Week 2, updated **Sep 18, 9:50 PM**
    Mountain (shown LIVE in-app, cached server-side).
  - Roster/starters/waiver state: read live from the app's real Sleeper
    calls during this same session (~9:47–9:55 PM Mountain, Sep 18).
  - Profile record last updated: `2026-09-19T01:46:52+00:00` (= **Sep 18,
    7:46 PM Mountain**).
- **Readiness verdict: READY.** Full weekly lineup, waiver, FAAB/priority,
  and K/DST tooling all loaded correctly and returned real, live,
  non-error results this session. See "what cannot yet be concluded"
  (section 6) for the honest limits within that READY verdict.

## 2. Lineup — current vs. proposed

**Real recommended change (1):** Start **Michael Pittman** (WR, PIT) over
**Zay Flowers** (WR, BAL) — **+11.7 projected points**, status OK (not a
close call).

**Proposed starting lineup (projected total 116.3 pts, live Week 2 data):**

| Slot | Player | Pos/Team | Proj pts | Note |
|---|---|---|---|---|
| QB | Caleb Williams | CHI · QB | 16.7 | Close call vs. Trevor Lawrence (bench), gap 0.3 pts |
| RB | Jonathan Taylor | IND · RB | 18.7 | OK |
| RB | De'Von Achane | MIA · RB | 16.8 | OK |
| WR | Chris Olave | NO · WR | 15.5 | OK |
| WR | **Michael Pittman** | PIT · WR | 11.7 | Recommended swap-in, OK |
| TE | Kyle Pitts | ATL · TE | 10.0 | OK |
| K | Ka'imi Fairbairn | HOU · K | 7.3 | OK (see K/DST section) |
| DST | NE D/ST | NE · DST | 8.6 | OK (see K/DST section) |
| FLEX | Travis Etienne | NO · RB | 11.0 | Close call vs. Marvin Harrison (bench), gap 1.7 pts |

**Strongest bench alternative / close calls:**
- Trevor Lawrence (QB, bench) — 16.4 proj pts, only 0.3 behind starter
  Caleb Williams. Genuine close call; if Caleb Williams is downgraded to
  OUT/doubtful before kickoff, Lawrence is the real backup play (recheck
  status first — see section 6).
- Marvin Harrison (WR, bench) — 9.2 proj pts, 1.7 behind Travis Etienne's
  FLEX slot; a real but not urgent alternative.
- Other bench: Carnell Tate (WR, 8.5), Kenny Gainwell (RB, 7.9), Wan'Dale
  Robinson (WR, 7.7), Zay Flowers (WR, missing projection this week — real
  Sleeper weekly-projection gap, retained and shown, not dropped).
- No reserve/taxi players and no locked-unavailable players on this roster
  this week (Sleeper `reserve: None`, confirmed both by this session's
  live pull and this cycle's own W1 findings).

## 3. Waivers / pickups

**Top genuinely useful pickup this week (real legal-lineup gain, not raw
points):** **ADD Brock Purdy (QB) / DROP Marvin Harrison** — real,
simulated before/after lineup gain **+2.3 pts**, "Projected to become a
starter this week." This is the #1 THIS_WEEK target by real usable gain,
confirmed live this session (matches this cycle's own earlier unit/live
verification of the same evaluator).
- Long-term cost: real REST_OF_SEASON view shows Marvin Harrison still has
  real standalone value; dropping him is a real, disclosed opportunity
  cost, not free. Season-utility context is shown separately in-app
  ("Season utility (long-term)") — review before committing.
- Required drop: Marvin Harrison (WR), per the app's own paired
  evaluation; no open non-reserve slot exists that avoids a drop.
- Acquisition method: **this is NOT a FAAB league** — real Sleeper
  `waiver_type` reports rolling **waiver priority**, this team's real
  current priority is **#6 of 10** (live, this session). No dollar bid
  applies; claims process in priority order on the league's normal waiver
  schedule (recheck Sleeper's own transaction/waiver-clear day before
  assuming a specific day this week).
- No genuinely useful RB/WR/TE alternative showed comparable real weekly
  gain this session; the rest of the THIS_WEEK-ranked list drops off
  quickly after this one target.

## 4. Kicker and DST

- **Current K: Ka'imi Fairbairn** (HOU), real FantasyPros consensus rank
  **#4** for Week 2.
- **Real top alternative: Eddy Pineiro** (SF, FantasyPros **#3**,
  genuinely **AVAILABLE** in this league) — primary recommendation is
  **ADD**, a real, marginal upgrade (one rank spot), not a blowout. Two
  more real, available alternatives: Cairo Santos (CHI, #5, AVAILABLE),
  Tyler Bass (BUF, #9, AVAILABLE). (Brandon Aubrey #1, Cameron Dicker #2,
  Cam Little #6, Tyler Loop #7, Jason Myers #8 are all real but rostered
  elsewhere in this league — not acquirable, correctly excluded from any
  primary recommendation.)
- Rationale is FantasyPros' external Week 2 consensus rank only — no
  opponent/weather/kickoff-specific numeric adjustment is computed by this
  app; treat the rank gap (#4 vs. #3) as small and not a must-make move.
- **Current DST: New England D/ST**, real FantasyPros consensus rank
  **#8** for Week 2.
- **Real top alternative: San Francisco 49ers** (FantasyPros **#3**,
  genuinely AVAILABLE) — primary recommendation is **ADD**, a real,
  larger rank-gap upgrade than the kicker case. Second real, available
  alternative: **Kansas City Chiefs** (#10, AVAILABLE) — actually a real
  downgrade in rank versus New England, not a genuine alternative, shown
  only because it is available. (Philadelphia #1, Tampa Bay #2, Seattle
  #4, Baltimore #5, LA Chargers #6, LA Rams #7, Houston #9 are all real
  but rostered elsewhere — not acquirable.)
- KEEP New England is a defensible call given real DST streaming's low
  predictive reliability and the smallish rank gap to the only real
  meaningfully-better available option (SF, 5 spots better); this is a
  judgment call for the owner, not a forced move.

## 5. Contingencies

- No live questionable/practice-report/injury-status feed exists in this
  app (confirmed, no change this pass — see Worker 2's ledger finding:
  the only real current-season status source is a small, sourced manual
  override list, not a live injury feed). **No player on this roster is
  currently shown as a sourced OUT/questionable exclusion this week** —
  do not read that as a clean bill of health; it means this app has no
  live signal either way for any player not already on the manual
  override list.
- Real close calls to re-plan around if a start-quality player is
  downgraded before kickoff: Trevor Lawrence (QB bench, 0.3 pts behind
  Caleb Williams) and Marvin Harrison (WR bench, 1.7 pts behind Travis
  Etienne's FLEX slot) are the real, legal, same-slot-eligible backups.
- FLEX flexibility: Travis Etienne (RB) currently holds FLEX; Marvin
  Harrison (WR) is the real bench alternative if a swap is wanted —
  either is legal in this league's FLEX slot.
- No games in this matchup week had kicked off as of this session's real
  capture time (Sep 18, ~9:50 PM Mountain, before any Week 2 Sunday game);
  no locked-starter conflicts exist yet for this specific roster.

## 6. Recheck before kickoff / cannot conclude

- **Saturday readiness cannot establish Sunday's final inactive list —
  recheck before each relevant game's inactive announcement and roster
  lock.** This app has no live injury/practice-report feed; Sleeper's own
  app or a live injury wire is the real source for Sunday-morning
  inactives.
- Recheck the live NWR Week 2 lineup/streamer/waiver views once more
  shortly before kickoff — projections shown here were captured **Sep 18,
  ~9:47–9:55 PM Mountain**, roughly 12-14 hours before the Sunday slate;
  a fresh in-app refresh (all three tools have a live "Refresh" action)
  picks up any late Saturday/Sunday-morning changes to Sleeper's own
  weekly-projection feed.
- Waiver claims: if this team intends to claim Brock Purdy or a K/DST
  option, confirm the league's actual real waiver-processing day/time on
  Sleeper directly — this app reports current priority and gain, not the
  league's specific clear schedule.
- No real trade action was taken or recommended here (out of scope; the
  Trades tab remains available separately, unaffected by this sheet).
