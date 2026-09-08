# Next-Draft Final Blocker Closure — Section 9: Next-Draft Full Mock Battery V1

**Context:** Follow-up directive "NWR NEXT-DRAFT FINAL BLOCKER CLOSURE", section 9. Real,
current owner league profiles (read-only inspection of
`AppData\Local\com.ninerswarroom.redraft\state\redraft\profiles\*.json`): "403 N 18th and
friends" is 8-team 1QB (already drafted, 2026-09-07); **"Fantasy Gamers" (Sleeper, 10-team
1QB) is the real, next-draft-relevant league** (per the project's own prior-recorded schedule
finding, drafts 2026-09-09) -- so the 10-team 1QB case gets two real slots/seeds, per the
directive's own instruction.

## Methodology

Isolated, in-memory, dynamically-dated synthetic fixture -- never real owner data. The real
owner projection snapshot is itself still blocked by the section-1 freshness gate (an owner
authorization this session cannot self-issue), so it cannot legitimately drive a real ranking
right now; using it would either silently misrepresent "blocked" as "ready" or require
self-issuing an authorization, both explicitly prohibited. Matches the same real, disclosed
choice section 2's own runtime-acceptance walkthrough already made ("test-only fixture,
dynamically-dated, never real owner data").

Re-runs, and extends, the prior class-time session's own `NWR_MULTI_LEAGUE_FINAL_BATTERY_V1`
methodology: `run_complete_mock()` (the same real, private, in-memory simulation function that
battery used) for roster composition / legal completion / K-DST timing / hoarding flags, PLUS
(closing that battery's own explicitly disclosed gap) real `build_live_decision_bundle()` calls
-- 3 real samples per case, each a genuinely later draft state (one real owner pick plus real
CPU advancement between samples, using the same private `_advance_cpu`/`_select_asset`/
`_record_pick` functions `run_complete_mock` itself is built from) -- for DecisionBundle
latency, DQ coverage, and tie frequency. No disk writes; no real profile, board, or projection
file touched.

Synthetic universe: 40 QB / 130 RB / 150 WR / 55 TE (comfortably above the largest real case's
304 total picks), K/DST from the same 32-team manual-asset pattern the latency script (section
7) used, a rookie flag on a real, distributed ~1-in-7 fraction of the pool (not just the bottom
of it).

## Results

```
Case                 Slot/seed        Legal complete   K rd  DST rd  Rookies  Hoarding
8-team 1QB            8 / 20260908     Yes (128/128)    15    16      5       RB=9
10-team 1QB            5 / 20260908     Yes (160/160)    15    16      1       RB=9
10-team 1QB            9 / 20260909     Yes (160/160)    15    16      3       RB=9
12-team 1QB            6 / 20260908     Yes (192/192)    15    16      2       RB=9
16-team 1QB (19 rds)   9 / 20260908     Yes (304/304)    18    19      2       RB=8, WR=6
12-team Superflex      6 / 20260908     Yes (216/216)    17    18      2       QB=3, RB=10
```

**All 6 cases completed legally** -- every case reached its exact expected pick count
(team_count x rounds). K/DST timing again scales correctly with real round count in every case
(15/16 for 16-round leagues, 18/19 for the 19-round 16-team league, 17/18 for the 18-round
Superflex league), independently reconfirming the prior battery's own finding a second time.

```
Case                 DecisionBundle latency (3 real samples)   Mean    DQ coverage   Tied
8-team 1QB             0.767s / 1.156s / 0.907s                 0.94s   276/288 96%    0/48
10-team 1QB (slot 5)   2.013s / 1.785s / 1.731s                 1.84s   276/288 96%    0/48
10-team 1QB (slot 9)   1.627s / 2.158s / 1.381s                 1.72s   276/288 96%    0/48
12-team 1QB            2.385s / 2.076s / 2.059s                 2.17s   276/288 96%    0/48
16-team 1QB (19 rds)   3.391s / 3.245s / 2.946s                 3.19s   276/288 96%    0/48
12-team Superflex      2.646s / 2.347s / 2.319s                 2.44s   276/288 96%    0/48
```

**DecisionBundle latency scales with team_count/candidate pool** (0.94s at 8-team up to 3.19s
at 16-team) -- real and expected (more comparable-league simulation and more roster-legal
candidates as the league grows), but **not directly comparable to section 7's own 5.8-6.95s
FAST-preset production figure**: this harness runs a smaller `simulate_comparable_leagues`
population (`trials=20` vs production's real, larger FAST-preset trial count) and a smaller
synthetic universe than the real ~530-row admitted pool. Disclosed, not conflated -- section
7's own number remains the accepted next-draft latency figure; this battery's numbers are a
real, independent, direction-of-scaling data point, not a replacement measurement.

**DQ coverage (evaluated metric/candidate pairs) is 276/288 (95.8%) in every single case,
identically.** Traced precisely, not assumed: the missing 12/288 per case is 100% `playerScore`
returning `MISSING_INPUT` for exactly the K/DST manual-asset candidates in each sampled bundle
(directly confirmed by printing each candidate's `playerScore` status: every `MISSING_INPUT`
candidate was `manual:K:*` or `manual:DST:*`, every skill-position candidate was `EVALUATED`).
This is the real, permanent, already-established project-wide design boundary (K/DST are never
NWR-scored -- the same boundary section 5's own 403 14th-pick finding already documented) doing
exactly what it is supposed to do, not a new gap this battery discovered.

**Tied candidates: 0/48 in every case.** Disclosed limitation of this battery's own synthetic
fixture (matches the prior battery's own precedent of disclosing synthetic-fixture artifacts):
the fixture's ranking is a smooth, strictly monotonic `500 - rank` function with no clustering,
so a genuine `pick_score_tied_no_spread` tie is very unlikely to occur here regardless of the
real engine's behavior. This does not claim the real admitted universe has zero ties -- the
real, already-documented close-call/tie evidence (Pick Score 50pt gap vs RAV/Team-Score 0 gap)
lives in prior findings and is not re-measured or contradicted by this synthetic battery.

## Hoarding flags, explained (mirrors the prior battery's own finding)

`RB=9` recurs across every 1QB case -- the same real, already-disclosed artifact of a
simplified synthetic candidate pool with no real bye-week/injury/team differentiation (the
prior battery's own precedent finding, re-confirmed here under this section's own independently
built fixture). `QB=3` for the Superflex case is the same real, legitimate roster-construction
allowance (`QB1 + Superflex slot + one real backup`) already explained and accepted in the
prior battery -- not a defect either time.

## Disposition

No code change -- battery/documentation only. All 6 legal-completion/K-DST-timing questions:
**yes, 6/6**, independently reconfirming the prior battery a second time under a freshly built
fixture. All 3 previously-disclosed-as-not-measured questions (DecisionBundle latency, DQ
coverage, tie frequency) are now measured, with the exact root cause of the one non-trivial
finding (K/DST MISSING_INPUT playerScore) traced to a real, already-accepted design boundary,
not a new defect.

## Status

Section 9: **DONE.**
