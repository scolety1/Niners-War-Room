# Small Formula Pilot Input Use Gate

| Input | Allowed In Pilot? | Allowed Role | Blocked Role | Required Caveat |
| --- | --- | --- | --- | --- |
| PYF / prior-year points | Yes | Mandatory anchor baseline and comparator | Production winner by itself | Must be reproduced before variant interpretation |
| Two-year prior production | Yes if present and review-safe | Fixed-weight review-only comparison | Tuned weight input | Must compare to PYF |
| Three-year prior production | Yes if present and review-safe | Fixed-weight review-only comparison | Tuned weight input | Must compare to PYF |
| Role archetype | Yes | Miss taxonomy, guardrail context, slice reporting | Formula weight, direct ranking boost/penalty, hidden sort | Review-only only |
| Age/lifecycle | Yes | Formula-family context, diagnostic slice, guarded variant context | Direct production input, automatic boost/penalty, hidden sort | Review-only only |
| Confidence cap | Limited | Caution/coverage context | Formula feature or player confidence score | Weak signal, not ranking confidence |
| Sparse-history flag | Yes | Guardrail slice and harm review | Automatic penalty | Must report breakout harm |
| Low-games flag | Yes | Guardrail slice and harm review | Automatic penalty | Must report false-negative harm |
| Red zone partial receipts | No for this pilot | Parked context only | Same-season prediction or full historical replay input | Partial 2024-2025 only, caveated |
| Route/YPRR/TPRR | No | None | Candidate input | Source recovery blocked |
| Return scoring | No | None | Candidate input | De-scoped, low priority for current league |
| Broad PFR features | No | None | Candidate input | Not approved |
| PFR RB broken tackles | No for this pilot | Parked review hypothesis | Broad production feature | Narrow future RB-only hypothesis |
| PFF Elusive Rating | No | None | Candidate input | Blocked |
| `nwr_elusive_proxy_review_only` | No | None | Candidate input | Blocked |
| Current ADP/market | No unless separately historical/as-of gated | None in this pilot | Candidate input | Point-in-time gate not cleared |
| Injury/availability | No unless separately historical/as-of gated | None in this pilot | Candidate input | Point-in-time gate not cleared |

All allowed inputs remain review-only. None are admitted for production/model-use or rankings integration by this contract.
