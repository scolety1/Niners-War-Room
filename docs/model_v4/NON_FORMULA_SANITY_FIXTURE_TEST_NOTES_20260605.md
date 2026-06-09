# Non-Formula Sanity Fixture Test Notes

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: document which R21 fixture expectations were safe to automate in R22
without tuning formulas or forcing new football opinions.

## Automated In R22

The focused tests in `tests/test_non_formula_sanity_fixtures.py` automate only
source, warning, blocked-use, fail-closed, and broad ordering behavior that is
already true in local review outputs:

- Current-player elite anchors remain above obvious depth/source-gap rows, with
  current-player checkpoint allowed/blocked-use fields intact.
- Keenan Allen and Darius Slayton legacy active-pack scores remain
  comparison-only through the Player Board resolver.
- Daniel Sobkowicz remains a watchlist/data-incomplete rookie row with final
  pick use blocked.
- Owned-pick ladder rows preserve admitted ordinal ordering for scored picks,
  while `2026 5.04` stays manual-only with no exact baseline.
- Pick Decision Lab rows keep internal-neighbor and no-exact-equivalence
  guardrails.
- Decision Board rows keep review-only allowed use, final-action blocked use,
  and source receipt/component traceability.

## Intentionally Not Automated Yet

These R21 ideas should remain report/manual-review items until a human approves
which football opinions should become hard tests:

- Exact elite tier score cutoffs.
- Exact rank slots for current players, rookies, QBs, TEs, or picks.
- Cross-position RB/WR/TE/QB order preferences beyond obvious source-safety
  relationships.
- Whether Trey McBride should or should not be the highest current-player score
  in a no-premium TE format.
- Whether top 1QB rows should be closer to or farther from elite RB/WR rows.
- Whether aging veteran scores are too high or too low after visible warnings.
- Any market, ADP, projection, consensus, startup, or trade-calculator
  relationship.

## Non-Goals

- Do not tune formulas from these tests.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, startup, or
  trade-calculator logic to private value.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, generated outputs, or user-entered draft state.
