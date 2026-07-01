# Full Scoring Parity Rerun Summary

## Verdict

`YELLOW_FULL_SCORING_PARITY_PARTIAL_GLOBAL_ZERO_OR_RETURN_SPECIAL_BLOCKERS`

The observed-row full scoring sidecar can support review-only component overlap against same-season 2024 `season_outcome` labels for deterministic player-season matches. Full/global scoring parity remains blocked.

## Accounting

| Metric | Count |
| --- | ---: |
| Sidecar rows | `90,092` |
| Nonzero component rows | `54,986` |
| Explicit observed-zero rows | `35,106` |
| Coverage matrix rows | `23` |
| Label rows | `119,040` |
| Deterministic matched player-seasons | `186` |
| Matched label rows emitted | `2,976` |
| Matched same-season outcome rows | `744` |
| Matched anchor-horizon rows | `2,232` |
| Matched player-week count | `2,796` |

## Result

Observed-row scoring review is available for matched 2024 player-seasons, but `parity_ready=false` throughout because global scoring parity needs complete zero-row policy and return/special touchdown subtype parity. Anchor-horizon labels remain a label-window mismatch for same-season scoring comparison.
