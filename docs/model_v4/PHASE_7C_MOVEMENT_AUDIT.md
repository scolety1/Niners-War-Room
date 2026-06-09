# Phase 6 Movement Audit

This report compares the post-formula-patch v4 review-only preview against a reconstructed Phase 5 checkpoint baseline. The reconstructed baseline uses the archived 0.1.0 config and current Phase 5 repaired source rows, while preserving old behavior for QB/TE suppression components. It does not promote app rankings or unlock readiness.

## Summary

- review_status: review_only
- phase5_baseline: local_exports\model_v4\phase5_checkpoint_reconstructed\v4_preview_outputs.csv
- phase6_preview: local_exports\model_v4\review_only_latest\v4_preview_outputs.csv
- rows: 80
- meaningful_movement_rows: 68
- large_movement_rows: 10
- medium_movement_rows: 33
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

- WR production/projection weighting patch: 37
- TE suppression patch: 11
- confidence/missing-data patch: 11
- no material movement: 10
- QB suppression patch: 6
- RB/WR balance formula patch: 5

## Meaningful Movements

| player | position | audit_groups | phase5_rank | phase6_rank | rank_delta | phase5_dynasty_asset_value | phase6_dynasty_asset_value | value_delta | movement_magnitude | movement_cause | receipt_backed_explanation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Saquon Barkley | RB | elite_rb | 1 | 2 | 1 | 78.23 | 76.23 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Derrick Henry | RB | aging_veteran | 5 | 4 | -1 | 73.22 | 71.22 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Kyren Williams | RB | elite_rb | 8 | 5 | -3 | 70.58 | 70.58 | 0.00 | small | RB/WR balance formula patch | Player rank moved mostly because other RB/WR values changed under the Phase 6 balance patch; own component scores were materially stable. |
| Josh Jacobs | RB | aging_veteran | 6 | 6 | 0 | 72.01 | 70.01 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Jonathan Taylor | RB | elite_rb | 7 | 7 | 0 | 71.91 | 69.91 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| De'Von Achane | RB | niners_roster\|young_bridge | 12 | 9 | -3 | 63.66 | 63.66 | 0.00 | small | RB/WR balance formula patch | Player rank moved mostly because other RB/WR values changed under the Phase 6 balance patch; own component scores were materially stable. |
| James Cook | RB | elite_rb | 13 | 10 | -3 | 63.65 | 61.65 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Chase Brown | RB | niners_roster\|young_bridge | 14 | 11 | -3 | 60.90 | 60.90 | 0.00 | small | RB/WR balance formula patch | Player rank moved mostly because other RB/WR values changed under the Phase 6 balance patch; own component scores were materially stable. |
| Amon-Ra St. Brown | WR | elite_wr | 19 | 12 | -7 | 57.93 | 59.48 | 1.55 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.36, usage -1.69, snap -0.88, projection +6.49. |
| Trey McBride | TE | te | 11 | 13 | 2 | 63.68 | 58.96 | -4.72 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +4.08. |
| Breece Hall | RB | elite_rb | 15 | 14 | -1 | 60.70 | 58.70 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Justin Jefferson | WR | elite_wr | 23 | 15 | -8 | 56.63 | 57.50 | 0.87 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.59, usage -1.49, snap -0.93, projection +5.88. |
| Drake London | WR | elite_wr | 16 | 16 | 0 | 60.09 | 57.41 | -2.68 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.17, usage -1.54, snap -0.90, projection +0.00. |
| Brock Bowers | TE | young_bridge\|te | 26 | 17 | -9 | 53.13 | 57.25 | 4.12 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +4.12. |
| Malik Nabers | WR | young_bridge | 27 | 18 | -9 | 52.84 | 53.45 | 0.61 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.98, usage -1.63, snap -0.91, projection +5.13. |
| Jaxon Smith-Njigba | WR | elite_wr\|young_bridge | 31 | 19 | -12 | 50.76 | 53.38 | 2.62 | large | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.88, usage -1.25, snap -0.86, projection +6.61. |
| Garrett Wilson | WR | elite_wr | 24 | 20 | -4 | 55.91 | 53.28 | -2.63 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.83, usage -1.41, snap -0.96, projection +0.00. |
| CeeDee Lamb | WR | elite_wr | 32 | 21 | -11 | 50.51 | 52.47 | 1.96 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.99, usage -1.30, snap -0.80, projection +6.05. |
| David Montgomery | RB | niners_roster | 29 | 22 | -7 | 52.15 | 52.15 | 0.00 | medium | RB/WR balance formula patch | Player rank moved mostly because other RB/WR values changed under the Phase 6 balance patch; own component scores were materially stable. |
| Puka Nacua | WR | elite_wr\|young_bridge | 37 | 23 | -14 | 47.64 | 51.48 | 3.83 | large | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.59, usage -1.24, snap -0.70, projection +7.37. |
| Terry McLaurin | WR | aging_veteran | 25 | 24 | -1 | 54.43 | 51.45 | -2.98 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.14, usage -1.37, snap -0.80, projection +0.00. |
| Brian Thomas Jr. | WR | niners_roster\|young_bridge | 30 | 25 | -5 | 51.68 | 50.94 | -0.74 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -2.31, usage -1.39, snap -0.79, projection +3.75. |
| Kenneth Walker III | RB | elite_rb | 28 | 26 | -2 | 52.54 | 50.54 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| George Kittle | TE | te | 21 | 27 | 6 | 57.45 | 49.71 | -7.74 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +0.92. |
| Tee Higgins | WR | other | 39 | 28 | -11 | 47.27 | 47.61 | 0.34 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.73, usage -1.55, snap -0.79, projection +4.42. |
| Davante Adams | WR | aging_veteran | 33 | 29 | -4 | 50.46 | 46.72 | -3.73 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.84, usage -1.73, snap -0.92, projection +0.00. |
| Nico Collins | WR | elite_wr | 34 | 30 | -4 | 49.19 | 46.59 | -2.60 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.71, usage -1.20, snap -0.66, projection +0.00. |
| Josh Allen | QB | qb | 17 | 31 | 14 | 59.34 | 46.16 | -13.18 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +3.28. |
| Mike Evans | WR | aging_veteran | 36 | 32 | -4 | 48.13 | 44.92 | -3.22 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.93, usage -1.28, snap -0.72, projection +0.00. |
| Jerry Jeudy | WR | niners_roster | 42 | 33 | -9 | 45.81 | 44.80 | -1.00 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.85, usage -1.17, snap -0.90, projection +2.92. |
| Lamar Jackson | QB | niners_roster\|qb | 22 | 34 | 12 | 57.32 | 44.76 | -12.56 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +3.28. |
| Tyreek Hill | WR | aging_veteran | 41 | 35 | -6 | 46.58 | 43.51 | -3.07 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.67, usage -1.20, snap -0.80, projection +0.00. |
| Xavier Worthy | WR | niners_roster\|young_bridge | 44 | 36 | -8 | 43.16 | 43.28 | 0.12 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.47, usage -1.38, snap -0.64, projection +3.61. |
| Jakobi Meyers | WR | niners_roster | 45 | 37 | -8 | 42.83 | 42.73 | -0.10 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.61, usage -1.12, snap -0.92, projection +3.55. |
| Travis Kelce | TE | te | 35 | 38 | 3 | 49.12 | 42.14 | -6.98 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +0.73. |
| George Pickens | WR | other | 43 | 39 | -4 | 44.75 | 42.07 | -2.68 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.34, usage -1.09, snap -0.80, projection +0.00. |
| Mark Andrews | TE | te | 40 | 40 | 0 | 47.10 | 41.04 | -6.06 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.30. |
| Jalen Hurts | QB | qb | 4 | 41 | 37 | 73.81 | 40.29 | -33.52 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +3.28. |
| Sam LaPorta | TE | young_bridge\|te | 52 | 42 | -10 | 37.59 | 39.23 | 1.64 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.64. |
| Jaylen Waddle | WR | other | 46 | 43 | -3 | 41.20 | 38.76 | -2.43 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.11, usage -0.84, snap -0.79, projection +0.00. |
| Quentin Johnston | WR | niners_roster\|young_bridge | 53 | 44 | -9 | 37.45 | 37.98 | 0.53 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.38, usage -0.81, snap -0.71, projection +3.43. |
| Wan'Dale Robinson | WR | niners_roster | 51 | 45 | -6 | 37.60 | 37.85 | 0.24 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.12, usage -1.09, snap -0.76, projection +3.21. |
| Jayden Daniels | QB | young_bridge\|qb | 38 | 46 | 8 | 47.46 | 37.61 | -9.85 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +3.28. |
| Keenan Allen | WR | aging_veteran | 48 | 47 | -1 | 40.92 | 37.55 | -3.38 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.35, usage -1.16, snap -0.87, projection +0.00. |
| Ladd McConkey | WR | young_bridge | 47 | 48 | 1 | 41.03 | 37.54 | -3.50 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.91, usage -0.86, snap -0.73, projection +0.00. |
| Marvin Harrison Jr. | WR | young_bridge | 49 | 49 | 0 | 38.86 | 35.56 | -3.30 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.59, usage -0.92, snap -0.79, projection +0.00. |
| Romeo Doubs | WR | niners_roster | 55 | 50 | -5 | 34.61 | 35.53 | 0.92 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.01, usage -0.72, snap -0.77, projection +3.43. |
| Cooper Kupp | WR | aging_veteran | 54 | 51 | -3 | 37.19 | 33.89 | -3.30 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.28, usage -0.90, snap -0.81, projection +0.00. |
| Christian McCaffrey | RB | elite_rb | 56 | 52 | -4 | 32.78 | 32.78 | 0.00 | small | RB/WR balance formula patch | Player rank moved mostly because other RB/WR values changed under the Phase 6 balance patch; own component scores were materially stable. |
| Ricky Pearsall | WR | niners_roster\|young_bridge | 60 | 53 | -7 | 31.20 | 32.74 | 1.53 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.75, usage -0.55, snap -0.67, projection +3.51. |
| T.J. Hockenson | TE | niners_roster\|te | 62 | 54 | -8 | 30.26 | 31.64 | 1.38 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.38. |
| Joe Burrow | QB | qb | 10 | 55 | 45 | 63.95 | 31.41 | -32.54 | large | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Jake Ferguson | TE | niners_roster\|te | 63 | 56 | -7 | 29.44 | 30.76 | 1.32 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.32. |
| Brock Purdy | QB | qb | 18 | 57 | 39 | 57.94 | 30.50 | -27.45 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +2.05. |
| Jalen Coker | WR | niners_roster\|young_bridge | 64 | 58 | -6 | 29.17 | 30.23 | 1.05 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.75, usage -0.49, snap -0.66, projection +2.96. |
| Brenton Strange | TE | niners_roster\|young_bridge\|te | 66 | 59 | -7 | 28.32 | 29.64 | 1.31 | medium | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +1.31. |
| Tank Dell | WR | young_bridge | 58 | 60 | 2 | 31.72 | 29.26 | -2.46 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -1.11, usage -0.67, snap -0.69, projection +0.00. |
| Daniel Jones | QB | niners_roster\|qb | 50 | 61 | 11 | 38.09 | 29.20 | -8.88 | large | QB suppression patch | QB value moved because the 1QB suppression component is now emitted; receipt contribution delta is +2.05. |
| Stefon Diggs | WR | aging_veteran | 57 | 62 | 5 | 31.87 | 28.93 | -2.94 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.89, usage -0.58, snap -0.78, projection +0.00. |
| Amari Cooper | WR | other | 59 | 63 | 4 | 31.34 | 28.47 | -2.87 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.94, usage -0.58, snap -0.64, projection +0.00. |
| Chris Olave | WR | other | 61 | 64 | 3 | 30.38 | 28.09 | -2.29 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.58, usage -0.46, snap -0.62, projection +0.00. |
| Patrick Mahomes | QB | qb | 20 | 65 | 45 | 57.51 | 27.89 | -29.61 | large | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Brandon Aiyuk | WR | niners_roster | 65 | 67 | 2 | 28.72 | 26.07 | -2.65 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.50, usage -0.51, snap -0.76, projection +0.00. |
| Darrell Henderson | RB | other | 68 | 68 | 0 | 24.97 | 22.97 | -2.00 | small | confidence/missing-data patch | Value/trust moved because missing evidence now keeps its warning and applies the Phase 6 uncertainty penalty when value is evidence-adjusted. |
| Luther Burden | WR | niners_roster\|young_bridge | 72 | 69 | -3 | 18.28 | 22.44 | 4.15 | medium | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production +0.00, usage +0.00, snap +0.00, projection +4.15. |
| Jayden Higgins | WR | niners_roster\|young_bridge | 73 | 71 | -2 | 17.25 | 20.04 | 2.79 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production +0.00, usage +0.00, snap +0.00, projection +2.79. |
| Hollywood Brown | WR | other | 70 | 73 | 3 | 18.91 | 16.42 | -2.49 | small | WR production/projection weighting patch | WR value moved because production, usage, snap, and projection weights changed; receipt contribution deltas are production -0.12, usage -0.32, snap -0.34, projection +0.00. |
| Kenyon Sadiq | TE | young_bridge\|te | 80 | 76 | -4 | 0.00 | 0.80 | 0.80 | small | TE suppression patch | TE value moved because the no-premium TE suppression component is now emitted; receipt contribution delta is +0.80. |

## Remaining Suspicious Rankings

No unexpected movement rows were detected by the Phase 6 audit.

## Named Group Coverage

| audit_group | row_count | meaningful_rows | largest_abs_value_delta |
| --- | --- | --- | --- |
| niners_roster | 24 | 20 | 12.56 |
| elite_rb | 9 | 7 | 2.00 |
| elite_wr | 9 | 8 | 3.83 |
| aging_veteran | 9 | 9 | 3.73 |
| young_bridge | 30 | 20 | 9.85 |
| qb | 9 | 8 | 33.52 |
| te | 11 | 10 | 7.74 |

## Guardrails

- v4 remains review-only.
- Active War Board/My Team rankings were not promoted.
- Readiness gates remain locked.
- Movement cause labels are audit metadata, not formula tuning.
