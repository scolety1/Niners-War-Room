# K/DST Prospective Benchmark V1 -- Real Preliminary Results (Work Unit 17)

Design: `docs/codex/prospective_outcomes_v1/KDST_PROSPECTIVE_BENCHMARK_V1.md`
(written first). Raw output:
`docs/codex/prospective_outcomes_v1/kdst_prospective_benchmark_v1/
week_01_2026.json`, produced by `scripts/run_kdst_prospective_benchmark_
v1.py` (real, reproducible, read-only). `fantasypros_kdst_consensus_
service.py` and every other recommendation-logic module were NOT modified
by this pass.

**`PRELIMINARY`, n=1 real week (Week 1 2026).** Current real NFL week is
2 as of this pass; Week 1 is the only real, fully-complete week. No
conclusion below is treated as validated, and no model/recommendation
logic was tuned from it, per the owner's standing instruction.

## Real Week 1 2026 data (Fantasy Gamers league, owner `scolety`, roster 9)

### K

| Arm | Real player | Real actual points |
|---|---|---|
| NWR_RECOMMENDATION | Cam Little (JAX, unrostered, ECR 3) | **12.0** |
| PROVIDER_CONSENSUS (naive ECR 1) | Brandon Aubrey (DAL) | 1.0 |
| RAW_PROJECTION (highest real Sleeper `pts_ppr` projection, unrostered) | Matt Gay (LV) | 10.0 |
| REPLACEMENT_LEVEL (owner's real, already-rostered K) | Ka'imi Fairbairn (HOU) | 9.0 |

Real, useful finding: NWR's roster-availability filter did real, visible
work this week -- naive ECR rank-1/2 (Aubrey, Dicker) were REAL, actually-
rostered kickers elsewhere in the league; NWR correctly skipped to rank-3
(Cam Little), who happened to have the best real outcome of all four arms
this week (12.0, beating even the raw-projection arm's own pick, 10.0).

### DST

| Arm | Real player | Real actual points |
|---|---|---|
| NWR_RECOMMENDATION | Jacksonville Jaguars (naive ECR 1) | **15.0** |
| PROVIDER_CONSENSUS (naive ECR 1) | Jacksonville Jaguars | 15.0 (identical pick) |
| RAW_PROJECTION | Las Vegas Raiders | 15.0 |
| REPLACEMENT_LEVEL (owner's real, already-rostered DST) | New England Patriots | 6.0 |

Real, disclosed consequence of the identity-matching defect (see below):
NWR_RECOMMENDATION and PROVIDER_CONSENSUS picked the IDENTICAL real team
this week -- not because they are the same method by design (they
legitimately differ for K, see above), but because the roster-availability
filter that should differentiate them never actually fires for DST.

## The real, mechanical DST identity-matching defect (found, documented, NOT fixed)

Live-verified again while populating this real week (independently of the
earlier discovery during design): a real query against all 10 real DST
rows this league actually rosters showed every one reported
`rosterStatus: "AVAILABLE"` via `sleeper_streamer_actions` -- including
the owner's own real, started DST (`"NE"`). Root cause: Sleeper's own
`players/nfl` catalog gives DST entries `first_name`/`last_name` only,
never `full_name`/`search_full_name`, so `_identity()` returns
`("", "", "")` for every real DST roster entry inside that one function.
K is unaffected (K catalog entries DO carry `full_name`; live-verified the
owner's own real K resolved correctly to `"YOUR_STARTER"`). Per the hard
boundary ("measure them, don't modify them"), **this was NOT fixed** --
flagged in the design doc and here for a future worker explicitly
authorized to touch `fantasypros_kdst_consensus_service.py`.

A second, smaller, real provider-convention difference was also found and
handled ONLY inside this benchmark's own join code (not the production
service): FantasyPros uses team code `"JAC"` for Jacksonville; Sleeper
uses `"JAX"`. Every other real team code checked matched exactly.

## Honest interpretation

- **This is one real week.** Nothing here is a validated finding about
  NWR's real K/DST performance across a season. The K result (NWR's real
  pick out-performing naive consensus by 11 real points, and out-
  performing even the raw-projection pick) is a single, real, favorable
  data point -- NOT evidence NWR is "better," just one week where the
  roster-availability filter mattered and the outcome happened to favor
  it.
- **The DST identity defect is the one real, mechanical, systemic finding
  from this pass** -- it is validated by direct code inspection AND by
  live behavior (every real DST in the league showing as falsely
  "available"), not merely a one-week anecdote. It does not, by itself,
  meet the bar for "recommend a challenger" (the hard rule is about the
  RECOMMENDATION method/model, and per the owner's directive this is
  scoped as measurement, not a mandate to fix); it is documented here and
  in the design doc as a real, concrete, ALREADY-VALIDATED defect for
  the next worker who is authorized to touch that file.
- No challenger is proposed for either K or DST from this pass's real
  outcome data (n=1 week is explicitly too small, per the owner's
  standing instruction).

## Open items for a future worker

- Populate additional real weeks as the 2026 season progresses (the
  scaffolding -- `kdst_prospective_benchmark_v1_service.py` and the runner
  script -- is real and reusable; re-run with `WEEK` advanced once a new
  week is complete).
- Fix (in a pass explicitly authorized to touch production K/DST
  recommendation logic) the DST `full_name` gap in `sleeper_streamer_
  actions`, matching the fallback pattern already present in
  `resolve_roster_canonical_ids`/`sleeper_free_agent_pool`/`weekly_
  projection_service.build_weekly_projection_rows`.
- This pass's own benchmark join code resolves a Sleeper id for the
  NWR_RECOMMENDATION/PROVIDER_CONSENSUS K arms by exact real-name match
  against the players catalog -- a small, disclosed, benchmark-local
  join (not the production identity system) that could in principle
  collide on a duplicate real name; not observed this pass (both real
  names matched exactly once).
