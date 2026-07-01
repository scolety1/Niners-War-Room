# Season Anchor Policy

## Required Anchor Shape

The Core Usage Review Dataset V1 builder must use this shape:

- Feature season: completed season N.
- Target season: season N+1.
- Prediction anchor: a documented pre-season or pre-target-window date for season N+1.
- Feature as-of date: after season N has ended and before the N+1 prediction anchor.

Any row that cannot prove this relationship must remain `Not enough information` or be excluded from the review feature table.

## Allowed Timing

Allowed:

- Final season N factual usage totals after all season N source data is complete.
- Aggregates from season N weekly rows only.
- Draft/combine static context if the event occurred before the N+1 anchor.
- Typed red-zone opportunity fields after source semantics are documented.

Not allowed:

- Target season N+1 weekly rows.
- Current roster, injury, depth, schedule, next-game, opponent, bye, or availability fields unless a separate point-in-time snapshot gate proves historical availability.
- Current display artifacts as model-feature proof.
- Missing-as-zero assumptions.

## Season Close Rule

The builder must document the close condition used for season N. If the source includes postseason weeks, the builder must explicitly choose whether the dataset is regular-season-only or full-season and keep that choice consistent across sources.

## Null Rule

Preserve nulls. Missing values remain `Not enough information`. A zero may be emitted only when source semantics prove the source returned explicit numeric zero or a separate zero-eligibility gate proves true zero production.
