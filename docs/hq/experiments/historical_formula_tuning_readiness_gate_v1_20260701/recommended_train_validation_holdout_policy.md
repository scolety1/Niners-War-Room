# Recommended Train / Validation / Holdout Policy

Use a fixed season split:

- Train: feature seasons 2012-2020, target seasons 2013-2021, 3,716 rows.
- Validation: feature seasons 2021-2022, target seasons 2022-2023, 912 rows.
- Holdout: feature seasons 2023-2024, target seasons 2024-2025, 890 rows.

Rules:

- Candidate families must be declared before looking at holdout results.
- Holdout can be evaluated once per candidate packet.
- Aggregate metrics cannot override position-level failures.
- A candidate must be stable across validation and holdout for points, PPG, position finish, and position-specific hit-rate metrics.
- Any change to split policy requires a new readiness gate or HQ approval.
- No target-season fields may be used as features.
