# K/DST Direct-Model Research Baseline — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 9. RESEARCH ONLY --
never promoted, never wired into any live recommendation path. Real, permanent, reproducible
script: `docs/codex/nwr_kdst_direct_model_research_v1_20260908/run_kdst_direct_model_research.py`.

## Real, disclosed target formulas

Neither Kicker nor DST scoring is computed by nflverse itself (verified: `fantasy_points` is
0.0 for every real K row in this repo's snapshot; no DST/DEF row exists in the player-level
stats tables at all). Built explicit, disclosed, standard formulas:

- **Kicker** (per real game): 3 pts/FG make (0-39yd), 4 pts (40-49yd), 5 pts (50+yd), 1
  pt/PAT make.
- **DST** (per real team-week): 1 pt/sack, 2 pts/INT, 2 pts/fumble recovery, 6 pts/defensive
  TD, 2 pts/safety, plus a real points-allowed tier bonus (0: +10, 1-6: +7, 7-13: +4, 14-20:
  +1, 21-27: 0, 28-34: -1, 35+: -4) using the real opponent score from nflverse's own
  schedule (`nfl.load_schedules`, cached locally as `schedules_2017_2025_cache.parquet`).

## Real data sources

- Kicker features: `player_stats_weekly` (2017-2025), real distance-bucketed FG makes
  (`fg_made_0_19` ... `fg_made_60_`), real PAT makes/attempts.
- DST features: the same weekly table's real individual-defensive-player events (sacks, INT,
  fumble recoveries [own+opponent], defensive TDs, safeties), summed to real team-week
  totals, joined against the real schedule's real opponent score for points-allowed.

## A real methodology self-correction (disclosed, not hidden)

The first version of this script regressed each season's real fantasy points on that SAME
season's own concurrent event counts -- since the target is a deterministic linear function
of exactly those counts, this produced a trivially near-perfect (Pearson 0.999) but
meaningless result: it wasn't testing prediction, only recovering the scoring formula itself.
Corrected to the genuine, real predictive framing this project's persistence-projection
paradigm already uses elsewhere: features are the same real player/team's PRIOR-season
aggregates, predicting that NEXT season's real total -- a real "given what happened last year,
what happens next year" question.

## Real, honest walk-forward results (2019-2025, real prior-season-present pairs only)

```
KICKER (n=214 real player-seasons):
  Direct-model MAE: 31.92   |   Naive prior-year-persistence baseline MAE: 35.55
  Direct model beats naive baseline on MAE: YES
  Pearson correlation: 0.239   |   Spearman rank correlation: 0.198 (baseline: 0.250)

DST (n=222 real team-seasons):
  Direct-model MAE: 25.44   |   Naive prior-year-persistence baseline MAE: 30.37
  Direct model beats naive baseline on MAE: YES
  Pearson correlation: 0.139   |   Spearman rank correlation: 0.107 (baseline: 0.217)
```

**Stability**: both real, low, consistent per-season MAE variance (K std 2.90, DST std 2.85
across 7 real seasons) -- the weak signal is consistently weak, not erratic.

## Honest interpretation

Both real direct models edge out a naive "repeat last year's total" baseline on average
absolute error, but **both are worse rankers than the naive baseline** (lower real Spearman
correlation) -- meaning the direct model's real practical value for DRAFT ORDERING (which is
what actually matters for a fantasy tool) is genuinely weak, arguably slightly negative
relative to the simplest possible alternative. This matches the well-known, real, broad
finding in fantasy football analytics that Kicker and DST scoring are unusually hard to
predict year-over-year (high real variance, small real sample sizes, heavy real dependence on
matchup/weather/game-script factors not modeled here).

**Real missing features, disclosed**: no red-zone-opportunity proxy for kickers (team scoring
drives), no opponent/strength-of-schedule adjustment, no weather/dome context, no coaching-
staff/kicker-leg-strength signal, no real yards-allowed for DST (only points-allowed), no
pass-rush-scheme continuity signal. Any of these could plausibly improve the real result, but
building them out is a genuinely separate, larger research effort.

## Disposition: NOT promising enough to promote

Per the directive's own explicit instruction ("If weak, say so — Ballers remains a valid
fallback"): **this real research baseline is not promoted.** Ballers/UDK (Section 7-8) remains
the real, valid, owner-facing K/DST source. This script and its real results are preserved as
a versioned research artifact for a future session to build on (more features, richer models)
rather than discarded.

## Status

Section 9: **DONE.** Real baselines built, real chronological evaluation run, real weak result
honestly reported, correctly not promoted.
