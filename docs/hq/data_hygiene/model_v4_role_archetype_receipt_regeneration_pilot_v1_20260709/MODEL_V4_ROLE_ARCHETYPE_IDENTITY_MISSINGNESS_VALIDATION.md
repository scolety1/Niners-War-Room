# Model v4 Role Archetype Identity / Missingness Validation

## Result

`PASS`

- Duplicate keys: `0`
- Position coverage: `{'QB': 754, 'RB': 1429, 'TE': 1211, 'WR': 2124}`
- Sparse/low-games rows: `1453`
- Identity key: `player_id_gsis` carried as both `player_id` and `canonical_player_key`.
- Missingness classification distinguishes `source_present_nonzero`, `source_present_true_zero`, and `unknown_source_value` for the primary position-specific volume input.