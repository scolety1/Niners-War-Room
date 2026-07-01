# NWR NFLVerse Usage Validation Report V1

Verdict: `YELLOW_CORE_USAGE_REVIEW_DATASET_BUILT_REVIEW_ONLY`

## Dataset Counts

- Core player-week rows: 76804
- Seasons: 2024;2025
- Week range: 1 to 22
- Positions observed: C;CB;DB;DE;DL;DT;FB;FS;G;ILB;K;LB;LS;MLB;NT;Not enough information;OL;OLB;OT;P;QB;RB;S;SAF;TE;WR
- Sleeper ID joined rows: 72140
- Snap joined rows: 71600
- Red-zone sidecar rows: 6424

## Validation Results

- Row counts by season/week/position are written to `nwr_nflverse_usage_row_count_report_v1.csv`.
- Field coverage is encoded in `nwr_nflverse_usage_review_dataset_schema_v1.csv` and `nwr_nflverse_usage_field_map_v1.csv`.
- No current roster, injury, depth, schedule, next-game, opponent, bye, route, TPRR, or YPRR fields are included.
- `rz_att` is not normalized into the red-zone sidecar; only `rz_att_blocked_present` records that the ambiguous field was present in source rows.
- `touches` and `opportunities` are null-preserving and require both source components to be known.
- Missing values were not forced to zero.
- Snap counts are review-only and joined by name/team/opponent/week with caveats; missing snaps remain `Not enough information`.

## Local Source Receipts

- Player stats SHA256: `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- Snap counts SHA256: `b16c952551b0b5c2344ed31136da2369d77687a6e72ed02502bf47a999c01054`
- ff_playerids SHA256: `ee80d08294d80e86c3d1e08edd870dad3e868a5e37215fe511e980f8bd82c9f4`
- PBP SHA256: `26a85fac7dc0c01a6cf2cc32cdd4d9d82a9224f60cd9e24275b7d9058f447c2d`

Raw sources were not copied into git.
