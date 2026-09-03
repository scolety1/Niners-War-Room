# QB replacement-depth CHALLENGER — mechanism-only proof

Follows up on `QB_MARGINAL_VALUE_CHALLENGER_STATUS_20260903.md`, which
explains why a *real, backtested* QB replacement-baseline challenger
cannot be built this pass (no lawful access to real per-QB projected-points
magnitude — the governed 2026 projection snapshot is still expired). This
is the narrower thing that **is** honest to build without that data.

## What it does

`scripts/run_qb_replacement_depth_mechanism_challenger_v1.py` calls the
real, unmodified `calculate_replacement_levels()` from
`src/services/redraft_engine_v1_service.py` — not a reimplementation, not
a copy; the same function `generate_rankings()` calls in production —
twice, against a disclosed, clearly-synthetic 40-QB points ladder (380
points down to 185 in flat 5-point steps; NOT real projection data, no
real player's name is used):

- **CHAMPION**: `profile.draft.roster_limits = {"QB": 2}` (the real
  configured KHA/default depth the audit found) → depth `16 × 2 = 32`.
- **CHALLENGER**: `profile.draft.roster_limits = {"QB": 1}` (matching the
  starter-count-aware baseline the audit found already exists elsewhere in
  the codebase, `model_v4_replacement_vorp_core_service.py`'s
  `configured_replacement_rank`) → depth `16 × 1 = 16`.

A deliberately isolated roster shape (QB-only starters/bench, zero
required RB/WR/TE/K/DST) keeps the demonstration from being diluted by any
other position's replacement math — disclosed in the script itself as not
a realistic league configuration, chosen only to isolate the mechanism.

## Real result (from the real function, on the disclosed synthetic ladder)

| | CHAMPION (depth 32) | CHALLENGER (depth 16) |
|---|---|---|
| Rostered QBs | 32 | 16 |
| Replacement points | **220.0** (synthetic QB #33) | **300.0** (synthetic QB #17) |
| Top QB's value-over-replacement | 160.0 | **80.0** |

Every one of the 40 synthetic QBs' value-over-replacement is lower under
the CHALLENGER than the CHAMPION (`tests/test_qb_replacement_depth_mechanism_challenger.py::test_every_qbs_value_over_replacement_shrinks_under_the_challenger`).
Full 40-row table: `docs/codex/QB_REPLACEMENT_DEPTH_MECHANISM_CHALLENGER.csv`.

This mechanically confirms the audit's predicted fix direction: a
shallower configured QB depth pulls the replacement baseline closer to
the starters, shrinking every QB's computed edge relative to positions
whose baseline didn't change — without touching a single line of
`calculate_replacement_levels()` or `_position_roster_limit()` itself, only
the `profile.draft.roster_limits` input already designed to be
configurable.

## What this is not

- **Not a backtest.** It says nothing about whether depth 16 (vs. 32, vs.
  something else) produces *better* real draft-round predictions — that
  question needs real projected-points magnitude and the same
  `backtest_against_real_outcomes`-style evaluation the rookie challenger
  used, which is exactly what `QB_MARGINAL_VALUE_CHALLENGER_STATUS_20260903.md`
  says is blocked.
- **Not registered** in `champion_challenger_registry_service.py` and
  **not promotable** — there is no real-outcome evidence yet to justify a
  promotion decision.
- **Not a production change.** `redraft_engine_v1_service.py` is
  unmodified; the live `generate_rankings()` path still uses whatever
  `roster_limits` each real profile is configured with today.

## What is ready the moment real data exists

Swap `synthetic_qb_pool()` for a real `(ProjectionPlayer, points)` pool
built from a lawfully-current projection snapshot, keep the CHAMPION/
CHALLENGER profile pair exactly as built here, and run the same
`backtest_against_real_outcomes`-style comparison the rookie challenger
used against the real 21-QB KHA draft-round evidence already gathered in
`QB_MARGINAL_VALUE_AND_ROOKIE_CALIBRATION_AUDIT_20260903.md`.
