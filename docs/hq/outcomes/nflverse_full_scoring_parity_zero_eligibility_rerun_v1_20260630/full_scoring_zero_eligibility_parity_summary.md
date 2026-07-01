# Full Scoring Zero Eligibility Parity Summary

## Verdict

`YELLOW_ZERO_ELIGIBILITY_PARITY_IMPROVED_REMAINING_BLOCKERS`

Zero eligibility improves review evidence for matched player-seasons with rostered-active safe-zero weeks, but it does not make full/global scoring parity ready.

## Required accounting

| Metric | Count |
| --- | ---: |
| Sidecar rows | `90,092` |
| Nonzero component rows | `54,986` |
| Explicit observed-zero rows | `35,106` |
| Coverage matrix rows | `23` |
| Outcome label rows | `119,040` |
| Zero eligibility total rows | `10,252` |
| Zero eligibility parity subset rows | `6,222` |
| Safe zero total | `223` |
| OBSERVED_NONZERO_STATS | `5,999` |
| OBSERVED_EXPLICIT_ZERO_STATS | `135` |
| ROSTERED_ACTIVE_NO_STATS_SAFE_ZERO | `88` |
| NOT_ENOUGH_INFORMATION | `51` |
| IDENTITY_GATED | `44` |

## Prior vs rerun

| Metric | Prior observed-row parity | Zero-eligibility rerun |
| --- | ---: | ---: |
| Deterministic matched player-seasons | `186` | `176` |
| Matched label rows | `2,976` | `2,816` |
| Same-season matched rows | `744` | `704` |
| Anchor-horizon matched rows | `2,232` | `2,112` |
| Matched player-seasons with rostered-active safe-zero weeks | `Not enough information` | `23` |
| Rostered-active safe-zero weeks inside matched rows | `0` | `38` |

Zero eligibility did not increase matched player-season count or matched label-row count. It did add safe-zero evidence for `23` matched player-seasons. Ten prior matched player-seasons are outside the zero-eligibility parity subset and are not carried forward.

## Decision

Experiment readiness: `EXPERIMENT_NOT_READY`.

Full parity remains blocked by incomplete global zero coverage, excluded non-parity zero statuses, and label-window mismatch for anchor-horizon labels.
