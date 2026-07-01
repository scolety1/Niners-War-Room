# Full Sidecar Builder Formula Handoff

## Builder may include

- Direct safe scoring fields listed as `safe_for_observed_row_sidecar=true` in `scoring_formula_component_matrix.csv`.
- Composite `fumbles_lost` from the three lost-fumble fields.
- Composite `return_yards` from kickoff and punt return yards.
- Composite `return_or_special_touchdowns` from `special_teams_tds`, counted once.

## Builder must exclude

- `fantasy_points` and `fantasy_points_ppr`.
- EPA/CPOE/share-style fields.
- Headshot/display fields.
- Market, ADP, DynastyProcess, projections, analyst ranks, trade values, or pick values.
- Any model/rank/source-truth fields.

## Builder must preserve

- `label_truth_allowed=false`.
- `model_use_allowed=false`.
- `training_allowed=false`.
- `source_truth_allowed=false`.
- Missing rows as `Not enough information` unless a later zero-row gate proves otherwise.

## Next gate

Run an observed-row full sidecar builder. A separate zero-row completeness gate is still required for full season scoring parity from missing rows.
