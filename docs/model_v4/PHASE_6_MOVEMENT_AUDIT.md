# Phase 6 Movement Audit

This report compares the post-formula-patch v4 review-only preview against a reconstructed Phase 5 checkpoint baseline. The reconstructed baseline uses the archived 0.1.0 config and current Phase 5 repaired source rows, while preserving old behavior for QB/TE suppression components. It does not promote app rankings or unlock readiness.

## Summary

- review_status: review_only
- phase5_baseline: local_exports\model_v4\phase5_checkpoint_reconstructed\v4_preview_outputs.csv
- phase6_preview: local_exports\model_v4\review_only_latest\v4_preview_outputs.csv
- rows: 80
- meaningful_movement_rows: 63
- large_movement_rows: 6
- medium_movement_rows: 25
- unexpected_movement_rows: 0
- niners_roster_rows: 24
- elite_rb_rows: 9
- elite_wr_rows: 9
- aging_veteran_rows: 9
- young_bridge_rows: 30
- qb_rows: 9
- te_rows: 11
- active_rankings_promoted: False
- decision_ready_unlocked: False

## Cause Counts

- WR production/projection weighting patch: 34
- no material movement: 16
- TE suppression patch: 11
- QB suppression patch: 9
- confidence/missing-data patch: 8
- RB/WR balance formula patch: 2

## Meaningful Movements

| player | position | audit_groups | phase5_rank | phase6_rank | rank_delta | phase5_dynasty_asset_value | phase6_dynasty_asset_value | value_delta | movement_magnitude | movement_cause | receipt_backed_explanation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Saquon Barkley | RB | elite_rb | 1 | 2 | 1 | 78.23 | 76.23 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Derrick Henry | RB | aging_veteran | 5 | 4 | -1 | 73.22 | 71.22 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Kyren Williams | RB | elite_rb | 8 | 5 | -3 | 70.58 | 70.58 | 0.00 | small | RB/WR balance formula patch | Player rank moved mostly because other RB/WR values changed under the Phase 6 balance patch; own component scores were materially stable. |
| Josh Jacobs | RB | aging_veteran | 6 | 6 | 0 | 72.01 | 70.01 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Jonathan Taylor | RB | elite_rb | 7 | 7 | 0 | 71.91 | 69.91 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Josh Allen | QB | qb | 17 | 8 | -9 | 59.34 | 69.24 | 9.90 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +9.90. |
| Lamar Jackson | QB | niners_roster\|qb | 22 | 10 | -12 | 57.32 | 67.22 | 9.90 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +9.90. |
| Jalen Hurts | QB | qb | 4 | 11 | 7 | 73.81 | 66.78 | -7.03 | medium | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +9.90. |
| James Cook | RB | elite_rb | 13 | 13 | 0 | 63.65 | 61.65 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Amon-Ra St. Brown | WR | elite_wr | 19 | 15 | -4 | 57.93 | 59.48 | 1.55 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.36, usage -1.69, snap -0.88, projection +6.49. |
| Trey McBride | TE | te | 11 | 16 | 5 | 63.68 | 58.96 | -4.72 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +4.08. |
| Breece Hall | RB | elite_rb | 15 | 17 | 2 | 60.70 | 58.70 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Justin Jefferson | WR | elite_wr | 23 | 18 | -5 | 56.63 | 57.50 | 0.87 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.59, usage -1.49, snap -0.93, projection +5.88. |
| Drake London | WR | elite_wr | 16 | 19 | 3 | 60.09 | 57.41 | -2.68 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.17, usage -1.54, snap -0.90, projection +0.00. |
| Jayden Daniels | QB | young_bridge\|qb | 38 | 20 | -18 | 47.46 | 57.36 | 9.90 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +9.90. |
| Brock Bowers | TE | young_bridge\|te | 26 | 21 | -5 | 53.13 | 57.25 | 4.12 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +4.12. |
| Malik Nabers | WR | young_bridge | 27 | 22 | -5 | 52.84 | 53.45 | 0.61 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.98, usage -1.63, snap -0.91, projection +5.13. |
| Jaxon Smith-Njigba | WR | elite_wr\|young_bridge | 31 | 23 | -8 | 50.76 | 53.38 | 2.62 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.88, usage -1.25, snap -0.86, projection +6.61. |
| Garrett Wilson | WR | elite_wr | 24 | 24 | 0 | 55.91 | 53.28 | -2.63 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.83, usage -1.41, snap -0.96, projection +0.00. |
| CeeDee Lamb | WR | elite_wr | 32 | 25 | -7 | 50.51 | 52.47 | 1.96 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.99, usage -1.30, snap -0.80, projection +6.05. |
| David Montgomery | RB | niners_roster | 29 | 26 | -3 | 52.15 | 52.15 | 0.00 | small | RB/WR balance formula patch | Player rank moved mostly because other RB/WR values changed under the Phase 6 balance patch; own component scores were materially stable. |
| Puka Nacua | WR | elite_wr\|young_bridge | 37 | 27 | -10 | 47.64 | 51.48 | 3.83 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.59, usage -1.24, snap -0.70, projection +7.37. |
| Terry McLaurin | WR | aging_veteran | 25 | 28 | 3 | 54.43 | 51.45 | -2.98 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.14, usage -1.37, snap -0.80, projection +0.00. |
| Kenneth Walker III | RB | elite_rb | 28 | 30 | 2 | 52.54 | 50.54 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Joe Burrow | QB | qb | 10 | 31 | 21 | 63.95 | 50.36 | -13.59 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +2.88. |
| George Kittle | TE | te | 21 | 32 | 11 | 57.45 | 49.71 | -7.74 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +0.92. |
| Tee Higgins | WR | other | 39 | 33 | -6 | 47.27 | 47.61 | 0.34 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.73, usage -1.55, snap -0.79, projection +4.42. |
| Davante Adams | WR | aging_veteran | 33 | 34 | 1 | 50.46 | 46.72 | -3.73 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.84, usage -1.73, snap -0.92, projection +0.00. |
| Nico Collins | WR | elite_wr | 34 | 35 | 1 | 49.19 | 46.59 | -2.60 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.71, usage -1.20, snap -0.66, projection +0.00. |
| Brock Purdy | QB | qb | 18 | 36 | 18 | 57.94 | 45.71 | -12.24 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +2.88. |
| Patrick Mahomes | QB | qb | 20 | 37 | 17 | 57.51 | 45.37 | -12.14 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +2.88. |
| Mike Evans | WR | aging_veteran | 36 | 38 | 2 | 48.13 | 44.92 | -3.22 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.93, usage -1.28, snap -0.72, projection +0.00. |
| Jerry Jeudy | WR | niners_roster | 42 | 39 | -3 | 45.81 | 44.80 | -1.00 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.85, usage -1.17, snap -0.90, projection +2.92. |
| Tyreek Hill | WR | aging_veteran | 41 | 40 | -1 | 46.58 | 43.51 | -3.07 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.67, usage -1.20, snap -0.80, projection +0.00. |
| Xavier Worthy | WR | niners_roster\|young_bridge | 44 | 41 | -3 | 43.16 | 43.28 | 0.12 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.47, usage -1.38, snap -0.64, projection +3.61. |
| Jakobi Meyers | WR | niners_roster | 45 | 42 | -3 | 42.83 | 42.73 | -0.10 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.61, usage -1.12, snap -0.92, projection +3.55. |
| Travis Kelce | TE | te | 35 | 43 | 8 | 49.12 | 42.14 | -6.98 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +0.73. |
| George Pickens | WR | other | 43 | 44 | 1 | 44.75 | 42.07 | -2.68 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.34, usage -1.09, snap -0.80, projection +0.00. |
| Daniel Jones | QB | niners_roster\|qb | 50 | 45 | -5 | 38.09 | 42.05 | 3.96 | medium | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +3.96. |
| Mark Andrews | TE | te | 40 | 46 | 6 | 47.10 | 41.04 | -6.06 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.30. |
| Sam LaPorta | TE | young_bridge\|te | 52 | 47 | -5 | 37.59 | 39.23 | 1.64 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.64. |
| Jaylen Waddle | WR | other | 46 | 48 | 2 | 41.20 | 38.76 | -2.43 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.11, usage -0.84, snap -0.79, projection +0.00. |
| Quentin Johnston | WR | niners_roster\|young_bridge | 53 | 49 | -4 | 37.45 | 37.98 | 0.53 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.38, usage -0.81, snap -0.71, projection +3.43. |
| Keenan Allen | WR | aging_veteran | 48 | 51 | 3 | 40.92 | 37.55 | -3.38 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.35, usage -1.16, snap -0.87, projection +0.00. |
| Ladd McConkey | WR | young_bridge | 47 | 52 | 5 | 41.03 | 37.54 | -3.50 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.91, usage -0.86, snap -0.73, projection +0.00. |
| Marvin Harrison Jr. | WR | young_bridge | 49 | 53 | 4 | 38.86 | 35.56 | -3.30 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.59, usage -0.92, snap -0.79, projection +0.00. |
| Cooper Kupp | WR | aging_veteran | 54 | 55 | 1 | 37.19 | 33.89 | -3.30 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.28, usage -0.90, snap -0.81, projection +0.00. |
| Ricky Pearsall | WR | niners_roster\|young_bridge | 60 | 57 | -3 | 31.20 | 32.74 | 1.53 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.75, usage -0.55, snap -0.67, projection +3.51. |
| T.J. Hockenson | TE | niners_roster\|te | 62 | 58 | -4 | 30.26 | 31.64 | 1.38 | small | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.38. |
| Jake Ferguson | TE | niners_roster\|te | 63 | 59 | -4 | 29.44 | 30.76 | 1.32 | small | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.32. |
| Jalen Coker | WR | niners_roster\|young_bridge | 64 | 60 | -4 | 29.17 | 30.23 | 1.05 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.75, usage -0.49, snap -0.66, projection +2.96. |
| Brenton Strange | TE | niners_roster\|young_bridge\|te | 66 | 61 | -5 | 28.32 | 29.64 | 1.31 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.31. |
| Tank Dell | WR | young_bridge | 58 | 62 | 4 | 31.72 | 29.26 | -2.46 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.11, usage -0.67, snap -0.69, projection +0.00. |
| Stefon Diggs | WR | aging_veteran | 57 | 63 | 6 | 31.87 | 28.93 | -2.94 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.89, usage -0.58, snap -0.78, projection +0.00. |
| Amari Cooper | WR | other | 59 | 64 | 5 | 31.34 | 28.47 | -2.87 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.94, usage -0.58, snap -0.64, projection +0.00. |
| Chris Olave | WR | other | 61 | 65 | 4 | 30.38 | 28.09 | -2.29 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.58, usage -0.46, snap -0.62, projection +0.00. |
| Brandon Aiyuk | WR | niners_roster | 65 | 67 | 2 | 28.72 | 26.07 | -2.65 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.50, usage -0.51, snap -0.76, projection +0.00. |
| Darrell Henderson | RB | other | 68 | 68 | 0 | 24.97 | 22.97 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Luther Burden | WR | niners_roster\|young_bridge | 72 | 69 | -3 | 18.28 | 22.44 | 4.15 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production +0.00, usage +0.00, snap +0.00, projection +4.15. |
| Jayden Higgins | WR | niners_roster\|young_bridge | 73 | 71 | -2 | 17.25 | 20.04 | 2.79 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production +0.00, usage +0.00, snap +0.00, projection +2.79. |
| Hollywood Brown | WR | other | 70 | 73 | 3 | 18.91 | 16.42 | -2.49 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.12, usage -0.32, snap -0.34, projection +0.00. |
| Fernando Mendoza | QB | young_bridge\|qb | 76 | 76 | 0 | 0.00 | 1.44 | 1.44 | small | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +1.44. |
| Kenyon Sadiq | TE | young_bridge\|te | 80 | 77 | -3 | 0.00 | 0.80 | 0.80 | small | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +0.80. |

## Remaining Suspicious Rankings

No unexpected movement rows were detected by the Phase 6 audit.

## Named Group Coverage

| audit_group | row_count | meaningful_rows | largest_abs_value_delta |
| --- | --- | --- | --- |
| niners_roster | 24 | 15 | 9.90 |
| elite_rb | 9 | 6 | 2.00 |
| elite_wr | 9 | 8 | 3.83 |
| aging_veteran | 9 | 9 | 3.73 |
| young_bridge | 30 | 18 | 9.90 |
| qb | 9 | 9 | 13.59 |
| te | 11 | 10 | 7.74 |

## Guardrails

- v4 remains review-only.
- Active War Board/My Team rankings were not promoted.
- Readiness gates remain locked.
- Movement cause labels are audit metadata, not formula tuning.
