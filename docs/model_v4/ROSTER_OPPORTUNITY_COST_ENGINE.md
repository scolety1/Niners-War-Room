# Roster Cut Opportunity-Cost Engine

## Scope

This review-only engine translates Niners roster players into internal startup slots, nearby rookies, and rookie pick-equivalent context. It does not create cut, keep, trade, or draft recommendations.

## Label Counts

| Label | Rows |
|---|---:|
| expensive_to_cut | 2 |
| replaceable_depth | 2 |
| rookie_pick_equivalent_uncertain | 19 |
| trade_context_before_cut_review | 1 |

## Guardrails

- Review-only outputs only.
- No My Team, War Board, active rankings, app promotion, or readiness gates changed.
- Rookie pick equivalents are context, not exact market prices.
- Pick equivalents are anchored to owned Niners picks, not the whole market curve.
- Missing, floor, ceiling, or distant pick baselines are marked uncertain.
- ADP, market rankings, projections, mock drafts, and consensus are not used.
