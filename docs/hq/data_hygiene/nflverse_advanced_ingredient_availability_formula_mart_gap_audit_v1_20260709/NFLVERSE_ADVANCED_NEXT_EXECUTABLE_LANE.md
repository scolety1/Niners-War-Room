# nflverse Advanced Next Executable Lane

## Recommendation

`ffopportunity Expected Fantasy Points Formula Mart Sidecar V1`

## Why

The local `ep_weekly` parquet cache is an actual tabular source, not just a design packet. It carries player-week expected fantasy opportunity fields for `2021-2024`, includes `player_id`, `season`, `week`, `position`, and has direct Formula Data Mart value as an opportunity-quality sidecar.

## Required Guardrails

- Review-only sidecar only.
- Aggregate only closed-season N values for lagged N+1 tests.
- Validate player identity joins to Formula Mart `player_id`.
- Validate missingness by season/position.
- Do not use same-season/current/future context.
- Do not promote production/model-use.
- Do not change rankings or app/runtime behavior.
