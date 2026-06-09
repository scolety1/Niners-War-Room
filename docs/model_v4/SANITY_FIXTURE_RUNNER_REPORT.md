# Model v4 Sanity Fixture Runner Report

Created: 2026-05-16

This is the initial Phase 2C runner report for
`docs/model_v4/SANITY_FIXTURE_CONTRACT.csv`.

## Current Status

| Metric | Count |
| --- | ---: |
| Fixtures loaded | 29 |
| Schema issues | 0 |
| Missing truth-set players | 0 |
| Ready with v4 model output coverage | 0 |
| Review findings | 0 |
| Blocked missing input | 0 |
| Not applicable yet | 29 |

## Interpretation

The fixture contract is structurally ready. Every fixture references either
players in `TRUTH_SET_PLAYER_UNIVERSE.csv` or an approved dynamic selector such
as `Any truth-set player with missing market`.

No fixture is being evaluated for pass/fail yet because final Model v4 preview
outputs and receipts do not exist. The runner correctly returns
`not_applicable_yet` instead of pretending that legacy rankings can satisfy
Model v4 fixtures.

## Readiness Boundary

The fixture runner cannot unlock any readiness label. Its readiness label remains
`Review Only`, and `decision_ready_unlocked` is always false.

## Next Step

Once Model v4 preview outputs and receipts exist, rerun the fixture runner with a
model-output CSV. Fixtures with complete player coverage will move to `ready`.
Any explicit fixture disagreement should be recorded as `review`, not as an
automatic build blocker.

