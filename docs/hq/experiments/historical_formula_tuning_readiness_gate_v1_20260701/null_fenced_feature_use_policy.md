# Null-Fenced Feature Use Policy

The first future candidate formula search must exclude null-fenced optional features from the primary candidate set.

Null-fenced features:

- `prior_receiving_air_yards`
- `prior_receiving_yards_after_catch`
- `prior_offensive_snaps`
- `prior_offense_pct`

Allowed handling:

- Preserve nulls exactly as emitted by V3.
- Do not fill missing values with zero.
- Do not mean-fill, model-impute, or rank-impute in the primary pass.
- Use these fields only in separately reported sensitivity-only ablations after primary candidates are evaluated.
- Report rows excluded or retained for each optional-feature ablation.

Blocked handling:

- No zero fill for source-missing rows.
- No route proxy interpretation.
- No current depth, role, injury, or schedule inference.
- No production formula or ranking use.
