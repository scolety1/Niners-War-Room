# Special / Return Touchdown Mapping Policy

## Decision

`special_teams_tds` may be counted exactly once as a composite 4-point special teams touchdown component for observed-row point-total parity.

It must not be mapped to both `return_td` and `special_td`.

## Rationale

The NWR scoring config has both `return_td_pt=4` and `special_td_pt=4`, while the audited NFLVerse field set does not expose a direct `return_tds` field or a separate `special_tds` field. The available field is `special_teams_tds`.

Because both NWR scoring roles carry the same 4-point value, `special_teams_tds` can support point-total parity only if counted once. It cannot support subtype parity between return touchdowns and other special teams touchdowns.

## Builder rule

A future full sidecar builder should create a normalized component such as `return_or_special_touchdowns` from `special_teams_tds` and apply the 4-point weight once.

## Blocked uses

- Do not populate both `return_td` and `special_td` from `special_teams_tds`.
- Do not infer return touchdown subtype from the composite field.
- Do not use the field for model input, training, source truth, or app probabilities.
