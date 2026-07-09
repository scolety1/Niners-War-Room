# Model v4 Historical Replay Contract

## Status

`REVIEW_ONLY_CONTRACT_EXACT_REPLAY_BLOCKED_UNTIL_COMPONENT_RECEIPTS_EXIST`

## League Contract

- League: 10-team dynasty/keeper hybrid.
- Format: 1QB, non-PPR, first-down scoring.
- Starters: 1 QB, 2 RB, 3 WR, 1 TE, 2 FLEX, 1 K.
- FLEX eligibility: RB/WR/TE only.
- Kicker: de-emphasized and not meaningfully modeled by current Model v4 current-value chain.

## Decision Date

For target season `Y`, the replay decision date must be after the regular season `Y-1`
stats are complete and before target season `Y` current roster, injury, depth chart,
market, ADP, projection, or outcome information is used. The historical feature anchor
is therefore `feature_season = Y - 1`, and labels are `target_season = Y`.

## Valid Player Universe

Valid exact replay rows require all of the following:

- Position is QB/RB/WR/TE.
- Canonical identity is available at the historical decision date.
- Required Model v4 component inputs are present with source receipts.
- Required source receipts prove the evidence existed by the decision date.
- Target labels exist only as held-out evaluation labels, never as inputs.

The partial V3 panel is narrower: it only contains players with prior-season NFL
feature rows and next-season labels. It is not rookie-complete.

## Required Labels

- `next_nwr_points`
- `next_nwr_ppg`
- `next_position_finish`
- Position top-N labels: QB top 12, RB top 12/top 24, WR top 12/top 24/top 36, TE top 12.
- Startable label using NWR format cutoffs: QB10, RB30, WR40, TE12.

## Required Exact Inputs

Exact replay requires current Model v4 component names and receipts:

- Replacement/VORP: `review_scoring_points`, `positive_vorp_points`,
  `imported_first_down_points`, first-down source status, return scoring status.
- RB: `vorp_anchor`, `role_volume`, `first_down_high_value`,
  `receiving_utility`, `efficiency_context`.
- WR: `vorp_anchor`, `target_route_role`, `first_down_yardage`,
  `air_yard_role`, `efficiency_context`.
- QB: `vorp_anchor`, `rushing_separation`, `passing_volume_security`,
  `passing_production`, `regression_context`, discipline multiplier.
- TE: `vorp_anchor`, `route_target_role`, `first_down_yardage`,
  `yprr_target_efficiency`, `red_zone_secondary`, discipline multiplier.
- Checkpoint: `position_specific_review_score`, `lifecycle_modifier_review`,
  `confidence_cap`, `checkpoint_review_score`.
- Current displayed candidate layer, if it remains the board source:
  `wr_qb_v2_candidate_adjustment`, `candidate_reason_codes`,
  `old_pocket_qb_horizon_cap`, and their evidence receipts.

## Allowed Proxies

Allowed only for partial review lanes, never exact replay:

- V3 lagged factual fields such as prior NWR points, prior targets/carries,
  first downs, yards, passing stats, snap fields with null fences, and air-yard/YAC
  fields with null fences.
- Component names may be preserved as status columns, but proxy fields must not be
  relabeled as exact Model v4 component scores.

## Blocked Inputs

- Current ADP, market, projections, rankings, mock drafts, big boards, and consensus.
- Current roster/status/injury/depth-chart/schedule context.
- Target-season outcomes.
- Display-only Outcome V2 probabilities.
- NGS/PFR/CFBD/advanced metrics unless separately source-admitted and decision-date safe.
- Current-only age/role/lifecycle/confidence fields without historical receipts.

## Leakage Checks

- Every feature must have `feature_season = target_season - 1` or an earlier
  static-event timestamp.
- Every source must have an as-of receipt before the target-season decision anchor.
- Missing values must remain missing unless source semantics prove explicit zero.
- Identity joins must use approved IDs; name-only fallback is not allowed.

## Future Replay Metrics

The future replay lane should report MAE, RMSE, Spearman, Top-12/24/36 hit rates,
startable precision and recall, coverage by position and season, source/identity
coverage, baseline comparisons, and miss patterns by rookie/veteran, role change,
injury caveat, age band, and position.
