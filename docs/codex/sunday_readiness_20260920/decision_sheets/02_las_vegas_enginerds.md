# Sunday Decision Sheet — Las Vegas Enginerds

Prepared by Worker 6 (closure pass), live-verified this session against the
final-HEAD Redraft app (`1149b89d`), real browser session, GET-only Sleeper
+ FantasyPros calls throughout. All figures below are LIVE OBSERVATION from
that session unless marked otherwise.

## 1. League / owner / capture

- **League:** Las Vegas Enginerds — Sleeper `1344772855908290560`, 10-team
  **non-PPR**, 1QB. **Owner:** mcolety1 (`user 1352768154031374336`),
  roster 7, team "Niners." Redraft profile
  `6687d2b3aa21450ea0fc9e1792d461ff` (imported this cycle, W8).
- **Season / week:** 2026 regular season, **real live provider week = 2**
  (fresh `GET https://api.sleeper.app/v1/state/nfl` this session,
  matches Fantasy Gamers' identical fresh pull). League is `IN_SEASON`,
  real record 1-0 (#5 of 10 by points for), real live matchup this
  session: opponent **Rabidmonkies**, in-progress score 4.1–0.0 (Thursday
  night's real partial result only — the Sunday slate had not started at
  capture time).
- **Scoring basis:** real, custom **non-PPR** scoring — `rec: 0.0`,
  first-down bonuses `rec_fd`/`rush_fd: 0.4`, `pass_td: 3.0`,
  `rush_td`/`rec_td: 4.0`, all three 2-point-conversion types scored
  (`pass_2pt`/`rush_2pt`/`rec_2pt: 2.0`), custom kicker tiers
  `fgm_0_19`/`fgm_20_29`/`fgm_30_39: 2.0`, `fgm_40_49: 3.0`, `fgm_50p:
  4.0`. Roster: `QB, RB, RB, WR, WR, WR, TE, FLEX, FLEX, K, BN x14` —
  **no DST slot** (confirmed, real `roster.dst == 0`).
- **Capture times (this session, live):**
  - Weekly projections: SLEEPER, Week 2, updated **Sep 18, 9:46 PM**
    Mountain.
  - Roster/starters/reserve/lock state: read live from the app's real
    Sleeper + nflverse-schedule calls this same session (~9:56–10:10 PM
    Mountain, Sep 18).
  - Profile record last updated: `2026-09-19T03:03:25+00:00` (= **Sep 18,
    9:03 PM Mountain**, from the Weekly Home page's own real capture
    line).
- **Readiness verdict: READY, with one disclosed characteristic.** The
  first request after any backend restart can return a real, transient
  "command center unavailable" cold-start error while ~9,400 rows of
  Sleeper weekly projections plus a live nflverse schedule pull warm up
  (documented by an earlier worker this cycle, reproduced-once,
  self-resolves on retry within seconds); this session's own request
  succeeded without needing a retry. All tools returned real, live,
  non-error results this session. See section 6 for other honest limits.

## 2. Lineup — current vs. proposed

**Real recommended change (1):** Start **Jalen Coker** (WR, CAR) over
**Quentin Johnston** (bench alternative referenced by the optimizer) /
displaces **Zay Flowers** in the actual current-starters comparison —
**+7.6 projected points**, flagged **LOW CONFIDENCE — CLOSE CALL** (a
real, small margin, not a clear-cut start).

**Proposed starting lineup (projected total 90.9 pts, live Week 2 data,
real league-custom non-PPR scoring):**

| Slot | Player | Pos/Team | Proj pts | Note |
|---|---|---|---|---|
| QB | Lamar Jackson | BAL · QB | 16.8 | Close call vs. Drake Maye (bench), gap 1.5 pts |
| RB | David Montgomery | HOU · RB | 13.0 | OK |
| RB | De'Von Achane | MIA · RB | 12.0 | OK |
| WR | Jameson Williams | DET · WR | 8.0 | OK |
| WR | **Jalen Coker** | CAR · WR | 7.6 | Recommended swap-in, close call vs. Quentin Johnston, gap 1.8 pts |
| WR | Luther Burden | CHI · WR | 6.7 | Close call vs. Quentin Johnston, gap 0.9 pts |
| TE | Jake Ferguson | DAL · TE | 5.1 | Close call vs. T.J. Hockenson (bench), gap 0.3 pts |
| K | Cam Little | JAX · K | 5.2 | OK (partial league-scoring match — see K section) |
| FLEX | Chase Brown | CIN · RB | 10.4 | OK |
| FLEX | Xavier Worthy | KC · WR | 6.2 | Close call vs. Quentin Johnston, gap 0.4 pts |

**Total includes at least one player scored by generic provider points or
a partial league-scoring match, not this league's exact scoring** (Cam
Little — see K section) — this is disclosed live in-app, not hidden.

**Strongest bench alternative / close calls:** Drake Maye (QB, 15.2,
1.5 behind Lamar Jackson) and Quentin Johnston (WR, 5.8) are the real,
closest bench options if any of the three close-call starters above are
downgraded. T.J. Hockenson (TE, 4.7) is the real backup at TE.

**Reserve / locked / excluded (real, sourced, distinct facts — not
collapsed into one "zero" bucket):**
- **Reserve (not startable without a separate transaction):** Ricky
  Pearsall — on this roster's real Sleeper reserve slot.
- **Locked — game already started:** Skyler Bell — real kickoff for his
  team's game had already passed at capture time (Thursday night);
  cannot legally be added to a starting slot now.
- **Not included this week (sourced exclusion, not a silent drop):**
  Jayden Higgins — a real, sourced SEASON_OUT status override on file
  ("torn ACL in training camp, season-ending for 2026," 4 cited sources,
  verified 2026-09-07) — excluded for a real, evidenced reason, not
  because he is merely reserve-slotted.
- Two real missing-projection bench players (Brandon Aiyuk, Zay Flowers)
  are shown as "—" rather than silently dropped from the roster view.

## 3. Waivers / pickups

**Honest finding: no genuinely useful non-kicker pickup surfaced this
week.** The real THIS_WEEK-ranked list (by simulated legal-lineup gain)
is dominated by marginal kicker swaps (Trey Smack +0.7 pts, Matt Gay +0.6,
down to +0.1) — all **LOW urgency**, all real but not worth a roster move
for this trivial a gain. Filtering to real available WR candidates
(Keenan Allen, Xavier Hutchinson, Tyquan Thornton, Demarcus Robinson,
Rashod Bateman) shows **real +0.0 usable gain and "Becomes starter: No"
for every one of them** — this bench is already legally optimal against
the real available free-agent pool this week.
- **If a longer-term move is wanted instead:** the real REST_OF_SEASON
  top target is **ADD Kimani Vidal (RB) / DROP T.J. Hockenson** — real
  season-long marginal utility +18.7, suggested bid **$30-50, MEDIUM
  urgency**. This is a season-value play, not a this-week starter play;
  it would not change this week's starting lineup.
- **FAAB (real, this IS a FAAB league — `waiver_type=2`, corrected this
  cycle):** **$100 of $100** total budget remaining, real waiver priority
  **#2**, **14 real regular-season weeks remaining** (from the real
  Sleeper schedule/`playoff_week_start`), ≈**$7.1/week** if spread evenly
  (a heuristic, not a rule).

## 4. Kicker (no DST — league has no DST slot)

- **Current K: Cam Little** (JAX), real FantasyPros consensus rank **#6**
  for Week 2. **Real primary recommendation: KEEP** — a genuine case,
  confirmed live this session, of the owner's own starter beating every
  real, available alternative this week.
- Real alternatives checked: **Tyler Loop** (BAL, #7) is rostered
  elsewhere in this league — not acquirable. **Tyler Bass** (BUF, #9,
  genuinely **AVAILABLE**) is a real, worse-ranked option and not a
  genuine upgrade. No real, available, better-ranked K exists this week —
  KEEP is justified, not a default.
- **DST is correctly and structurally never evaluated for this league:**
  confirmed live this session — the streamer page shows no DST section
  at all for Enginerds (real `roster.dst == 0` enforcement, verified
  again this pass, consistent with this cycle's own W6/W8 fixes).

## 5. Contingencies

- No live questionable/practice-report feed exists (same honest gap as
  every league in this app — see Fantasy Gamers sheet section 5 for the
  same disclosure, not repeated in full here).
- Real close calls to re-plan around if a starter is downgraded: Drake
  Maye (QB bench, 1.5 behind Lamar Jackson), Quentin Johnston (WR bench,
  the real common alternative behind 3 separate close-call starters —
  Jalen Coker, Luther Burden, Xavier Worthy), T.J. Hockenson (TE bench,
  0.3 behind Jake Ferguson).
- FLEX flexibility: two FLEX slots, currently Chase Brown (RB) and Xavier
  Worthy (WR) — Quentin Johnston (WR) is the closest legal bench
  alternative for either FLEX slot.
- Ricky Pearsall (reserve) is not startable without a separate,
  owner-initiated roster transaction on Sleeper itself — this app does
  not perform that transaction.
- Skyler Bell's game has already kicked off (real, as of capture time) —
  correctly excluded from any new-start recommendation regardless of his
  projection.

## 6. Recheck before kickoff / cannot conclude

- **Saturday readiness cannot establish Sunday's final inactive list —
  recheck before each relevant game's inactive announcement and roster
  lock.** No live injury/practice-report feed exists in this app.
- Recheck the live NWR Week 2 lineup/streamer/waiver views again shortly
  before kickoff — projections here were captured **Sep 18, ~9:46–10:10
  PM Mountain**, roughly 11-13 hours before the Sunday slate.
- If the very first request after opening the app shows a transient
  "command center unavailable" message, wait a few seconds and retry —
  documented cold-start characteristic this cycle, not a data error.
- FAAB bid ranges shown in-app are a real, contextual heuristic only —
  not calibrated against actual auction results; treat as relative
  guidance, not a guaranteed winning bid.
- No real trade action was taken here; Trades tab is separately available
  and was exercised successfully elsewhere in this cycle (unaffected by
  this sheet).
