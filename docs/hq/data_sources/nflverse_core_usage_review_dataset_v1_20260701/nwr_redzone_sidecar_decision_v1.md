# Red-Zone Sidecar Decision V1

Decision: `YELLOW_REDZONE_SIDECAR_CREATED_REVIEW_ONLY_WITH_SEMANTICS_CAVEATS`

A sparse review-only sidecar was created at `nwr_player_week_redzone_sidecar_v1.parquet` from Sleeper public weekly stats for 2024-2025 regular-season weeks 1-18.

Candidate mappings:

- `rec_rz_tgt` -> `red_zone_targets`
- `rush_rz_att` -> `red_zone_carries`
- `pass_rz_att` -> `red_zone_pass_attempts`

Rules preserved:

- `rz_att` remains blocked/ambiguous and is not normalized.
- Missing sparse Sleeper keys remain `Not enough information`, not zero.
- PBP-derived `yardline_100 <= 20` counts were joined where GSIS crosswalks made review-only validation feasible.
- The sidecar is not source truth, not a model feature table, and not app wiring.

Sidecar rows: 6424
