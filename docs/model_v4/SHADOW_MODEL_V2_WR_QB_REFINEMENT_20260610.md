# Shadow Model V2 WR/QB Refinement - 2026-06-10

This is a shadow-only refinement. No production scoring changes are made.

## Source-Safe Fields Used

- Current rows: NWR score, position review score, VORP points, review scoring points, first-down points, role archetype, lifecycle modifier, confidence cap, available component weight, warning flags.
- Historical rows: historical replay score, draft round, overall pick, pre-draft production/team-share/draft-capital/athletic fields, evidence availability, confidence cap.
- Blocked: ADP, market rank, public rankings, consensus, projections, trade calculators, RotoWire rankings/projections, prior draft history, legacy active-pack private_score, roster tags.

## Summary

| Experiment | Classification | Recommendation | Historical vs baseline | Historical vs v1 |
|---|---|---|---|---|
| `production_baseline` | baseline | baseline_only | top36 hit 0.222 vs 0.222; bust 0.491 vs 0.491 | baseline |
| `wr_v1_reference` | v1_reference_only | do_not_promote_v1_reference | top36 hit 0.222 vs 0.222; bust 0.491 vs 0.491 | v1 reference row |
| `wr_proof_lane_v2` | candidate_promising_for_human_review | eligible_for_tiny_production_patch_proposal_after_review | top36 hit 0.222 vs 0.222; bust 0.491 vs 0.491 | top36 hit 0.222 vs 0.222; bust 0.491 vs 0.491 |
| `qb_v1_reference` | v1_reference_only | do_not_promote_v1_reference | top36 hit 0.241 vs 0.222; bust 0.463 vs 0.491 | v1 reference row |
| `qb_floor_horizon_v2` | candidate_promising_for_human_review | eligible_for_tiny_production_patch_proposal_after_review | top36 hit 0.241 vs 0.222; bust 0.472 vs 0.491 | top36 hit 0.241 vs 0.241; bust 0.472 vs 0.463 |
| `wr_qb_combined_v2` | candidate_promising_for_human_review | eligible_for_tiny_production_patch_proposal_after_review | top36 hit 0.241 vs 0.222; bust 0.472 vs 0.491 | compared separately to WR v1 and QB v1; no v1 combined was promoted |

## V1 Failure Diagnosis

| Lane | Player | Base | V1 | V2 | V1 class | V2 class | Diagnosis |
|---|---|---:|---:|---:|---|---|---|
| QB lane | CeeDee Lamb | 23 | 23 | 23 | stable | stable | movement requires human review. |
| WR lane | CeeDee Lamb | 23 | 19 | 20 | intended_improvement | intended_improvement | v2 preserves the useful v1 movement with a tighter receipt gate. |
| QB lane | Justin Jefferson | 25 | 25 | 25 | stable | stable | movement requires human review. |
| WR lane | Justin Jefferson | 25 | 22 | 22 | intended_improvement | intended_improvement | v2 preserves the useful v1 movement with a tighter receipt gate. |
| QB lane | Jaylen Waddle | 33 | 33 | 33 | stable | stable | movement requires human review. |
| WR lane | Jaylen Waddle | 33 | 30 | 33 | intended_improvement | stable | v2 avoids forcing movement when source-safe evidence is not strong enough. |
| QB lane | Ja'Marr Chase | 6 | 6 | 6 | stable | stable | movement requires human review. |
| WR lane | Ja'Marr Chase | 6 | 3 | 6 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | Amon-Ra St. Brown | 7 | 7 | 7 | stable | stable | movement requires human review. |
| WR lane | Amon-Ra St. Brown | 7 | 6 | 7 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | Puka Nacua | 1 | 1 | 1 | stable | stable | movement requires human review. |
| WR lane | Puka Nacua | 1 | 1 | 1 | stable | stable | already high; v2 leaves score stable and keeps evidence explanation separate. |
| QB lane | Jaxon Smith-Njigba | 2 | 2 | 2 | stable | stable | movement requires human review. |
| WR lane | Jaxon Smith-Njigba | 2 | 2 | 2 | stable | stable | already high; v2 leaves score stable and keeps evidence explanation separate. |
| QB lane | Drake London | 20 | 20 | 20 | stable | stable | movement requires human review. |
| WR lane | Drake London | 20 | 17 | 19 | acceptable_side_effect | intended_improvement | movement requires human review. |
| QB lane | Nico Collins | 16 | 16 | 16 | stable | stable | movement requires human review. |
| WR lane | Nico Collins | 16 | 13 | 16 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | DeVonta Smith | 27 | 27 | 27 | stable | stable | movement requires human review. |
| WR lane | DeVonta Smith | 27 | 23 | 25 | acceptable_side_effect | intended_improvement | movement requires human review. |
| QB lane | Jameson Williams | 24 | 24 | 24 | stable | stable | movement requires human review. |
| WR lane | Jameson Williams | 24 | 16 | 26 | false_positive | acceptable_side_effect | v2 tightens the v1 false-positive gate. |
| QB lane | Stefon Diggs | 61 | 66 | 62 | acceptable_side_effect | acceptable_side_effect | movement requires human review. |
| WR lane | Stefon Diggs | 61 | 45 | 61 | false_positive | stable | v2 tightens the v1 false-positive gate. |
| QB lane | Davante Adams | 48 | 51 | 48 | acceptable_side_effect | stable | movement requires human review. |
| WR lane | Davante Adams | 48 | 39 | 48 | false_positive | stable | v2 tightens the v1 false-positive gate. |
| QB lane | Josh Allen | 19 | 19 | 19 | stable | stable | movement requires human review. |
| WR lane | Josh Allen | 19 | 24 | 21 | acceptable_side_effect | acceptable_side_effect | movement requires human review. |
| QB lane | Patrick Mahomes | 84 | 63 | 68 | intended_improvement | intended_improvement | v2 preserves the useful v1 movement with a tighter receipt gate. |
| WR lane | Patrick Mahomes | 84 | 84 | 84 | stable | stable | movement requires human review. |
| QB lane | Lamar Jackson | 144 | 102 | 144 | intended_improvement | stable | v2 avoids forcing movement when source-safe evidence is not strong enough. |
| WR lane | Lamar Jackson | 144 | 144 | 144 | stable | stable | movement requires human review. |
| QB lane | Jalen Hurts | 64 | 49 | 50 | needs_more_data | intended_improvement | movement requires human review. |
| WR lane | Jalen Hurts | 64 | 64 | 64 | stable | stable | movement requires human review. |
| QB lane | Joe Burrow | 199 | 199 | 199 | stable | stable | movement requires human review. |
| WR lane | Joe Burrow | 199 | 199 | 199 | stable | stable | movement requires human review. |
| QB lane | Jayden Daniels | 180 | 180 | 180 | stable | stable | movement requires human review. |
| WR lane | Jayden Daniels | 180 | 180 | 180 | stable | stable | movement requires human review. |
| QB lane | Dak Prescott | 70 | 48 | 71 | needs_more_data | acceptable_side_effect | movement requires human review. |
| WR lane | Dak Prescott | 70 | 70 | 70 | stable | stable | movement requires human review. |
| QB lane | Jared Goff | 102 | 62 | 102 | false_positive | stable | v2 tightens the v1 false-positive gate. |
| WR lane | Jared Goff | 102 | 102 | 102 | stable | stable | movement requires human review. |
| QB lane | Baker Mayfield | 131 | 100 | 131 | false_positive | stable | v2 tightens the v1 false-positive gate. |
| WR lane | Baker Mayfield | 131 | 131 | 131 | stable | stable | movement requires human review. |
| QB lane | Jaxson Dart | 139 | 101 | 139 | false_positive | stable | v2 tightens the v1 false-positive gate. |
| WR lane | Jaxson Dart | 139 | 139 | 139 | stable | stable | movement requires human review. |
| QB lane | Drake Maye | 21 | 21 | 21 | stable | stable | movement requires human review. |
| WR lane | Drake Maye | 21 | 26 | 23 | acceptable_side_effect | acceptable_side_effect | movement requires human review. |
| QB lane | Trevor Lawrence | 26 | 26 | 26 | stable | stable | movement requires human review. |
| WR lane | Trevor Lawrence | 26 | 29 | 28 | acceptable_side_effect | acceptable_side_effect | movement requires human review. |
| QB lane | Chase Brown | 22 | 22 | 22 | stable | stable | movement requires human review. |
| WR lane | Chase Brown | 22 | 27 | 24 | acceptable_side_effect | acceptable_side_effect | movement requires human review. |
| QB lane | Trey McBride | 8 | 8 | 8 | stable | stable | movement requires human review. |
| WR lane | Trey McBride | 8 | 10 | 8 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | Brock Bowers | 46 | 46 | 46 | stable | stable | movement requires human review. |
| WR lane | Brock Bowers | 46 | 48 | 46 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | Bijan Robinson | 3 | 3 | 3 | stable | stable | movement requires human review. |
| WR lane | Bijan Robinson | 3 | 4 | 3 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | Jahmyr Gibbs | 5 | 5 | 5 | stable | stable | movement requires human review. |
| WR lane | Jahmyr Gibbs | 5 | 7 | 5 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | De'Von Achane | 9 | 9 | 9 | stable | stable | movement requires human review. |
| WR lane | De'Von Achane | 9 | 11 | 9 | acceptable_side_effect | stable | movement requires human review. |
| QB lane | Breece Hall | 31 | 31 | 31 | stable | stable | movement requires human review. |
| WR lane | Breece Hall | 31 | 32 | 31 | acceptable_side_effect | stable | movement requires human review. |

## Metrics Snapshot

| Experiment | Position | Window | Hit rate | Bust rate | Moved >12 | QB >24 | WR >24 |
|---|---|---|---:|---:|---:|---:|---:|
| `production_baseline` | ALL | top_12 | 0.361 | 0.222 | 0 | 0 | 0 |
| `production_baseline` | ALL | top_24 | 0.264 | 0.389 | 0 | 0 | 0 |
| `production_baseline` | ALL | top_36 | 0.222 | 0.491 | 0 | 0 | 0 |
| `production_baseline` | QB | top_12 | 0.5 | 0.0 | 0 | 0 | 0 |
| `production_baseline` | QB | top_24 | 0.75 | 0.0 | 0 | 0 | 0 |
| `production_baseline` | QB | top_36 | 0.8 | 0.0 | 0 | 0 | 0 |
| `production_baseline` | RB | top_12 | 0.615 | 0.077 | 0 | 0 | 0 |
| `production_baseline` | RB | top_24 | 0.333 | 0.37 | 0 | 0 | 0 |
| `production_baseline` | RB | top_36 | 0.324 | 0.382 | 0 | 0 | 0 |
| `production_baseline` | WR | top_12 | 0.19 | 0.333 | 0 | 0 | 0 |
| `production_baseline` | WR | top_24 | 0.175 | 0.45 | 0 | 0 | 0 |
| `production_baseline` | WR | top_36 | 0.133 | 0.583 | 0 | 0 | 0 |
| `production_baseline` | TE | top_12 |  |  | 0 | 0 | 0 |
| `production_baseline` | TE | top_24 | 0.0 | 0.0 | 0 | 0 | 0 |
| `production_baseline` | TE | top_36 | 0.111 | 0.556 | 0 | 0 | 0 |
| `wr_v1_reference` | ALL | top_12 | 0.361 | 0.25 | 1 | 0 | 0 |
| `wr_v1_reference` | ALL | top_24 | 0.264 | 0.403 | 1 | 0 | 0 |
| `wr_v1_reference` | ALL | top_36 | 0.222 | 0.491 | 1 | 0 | 0 |
| `wr_v1_reference` | QB | top_12 | 0.0 | 0.0 | 1 | 0 | 0 |
| `wr_v1_reference` | QB | top_24 | 0.75 | 0.0 | 1 | 0 | 0 |
| `wr_v1_reference` | QB | top_36 | 0.8 | 0.0 | 1 | 0 | 0 |
| `wr_v1_reference` | RB | top_12 | 0.667 | 0.083 | 1 | 0 | 0 |
| `wr_v1_reference` | RB | top_24 | 0.375 | 0.333 | 1 | 0 | 0 |
| `wr_v1_reference` | RB | top_36 | 0.324 | 0.382 | 1 | 0 | 0 |
| `wr_v1_reference` | WR | top_12 | 0.217 | 0.348 | 1 | 0 | 0 |
| `wr_v1_reference` | WR | top_24 | 0.163 | 0.488 | 1 | 0 | 0 |
| `wr_v1_reference` | WR | top_36 | 0.133 | 0.583 | 1 | 0 | 0 |
| `wr_v1_reference` | TE | top_12 |  |  | 1 | 0 | 0 |
| `wr_v1_reference` | TE | top_24 | 0.0 | 0.0 | 1 | 0 | 0 |
| `wr_v1_reference` | TE | top_36 | 0.111 | 0.556 | 1 | 0 | 0 |
| `wr_proof_lane_v2` | ALL | top_12 | 0.361 | 0.222 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | ALL | top_24 | 0.264 | 0.389 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | ALL | top_36 | 0.222 | 0.491 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | QB | top_12 | 0.5 | 0.0 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | QB | top_24 | 0.75 | 0.0 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | QB | top_36 | 0.8 | 0.0 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | RB | top_12 | 0.615 | 0.077 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | RB | top_24 | 0.333 | 0.37 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | RB | top_36 | 0.324 | 0.382 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | WR | top_12 | 0.19 | 0.333 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | WR | top_24 | 0.175 | 0.45 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | WR | top_36 | 0.133 | 0.583 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | TE | top_12 |  |  | 0 | 0 | 0 |
| `wr_proof_lane_v2` | TE | top_24 | 0.0 | 0.0 | 0 | 0 | 0 |
| `wr_proof_lane_v2` | TE | top_36 | 0.111 | 0.556 | 0 | 0 | 0 |
| `qb_v1_reference` | ALL | top_12 | 0.333 | 0.222 | 7 | 4 | 0 |
| `qb_v1_reference` | ALL | top_24 | 0.264 | 0.389 | 7 | 4 | 0 |
| `qb_v1_reference` | ALL | top_36 | 0.241 | 0.463 | 7 | 4 | 0 |
| `qb_v1_reference` | QB | top_12 | 0.0 | 0.0 | 7 | 4 | 0 |
| `qb_v1_reference` | QB | top_24 | 0.75 | 0.0 | 7 | 4 | 0 |
| `qb_v1_reference` | QB | top_36 | 0.75 | 0.0 | 7 | 4 | 0 |
| `qb_v1_reference` | RB | top_12 | 0.615 | 0.077 | 7 | 4 | 0 |
| `qb_v1_reference` | RB | top_24 | 0.333 | 0.37 | 7 | 4 | 0 |
| `qb_v1_reference` | RB | top_36 | 0.333 | 0.364 | 7 | 4 | 0 |
| `qb_v1_reference` | WR | top_12 | 0.182 | 0.318 | 7 | 4 | 0 |
| `qb_v1_reference` | WR | top_24 | 0.175 | 0.45 | 7 | 4 | 0 |
| `qb_v1_reference` | WR | top_36 | 0.138 | 0.569 | 7 | 4 | 0 |
| `qb_v1_reference` | TE | top_12 |  |  | 7 | 4 | 0 |
| `qb_v1_reference` | TE | top_24 | 0.0 | 0.0 | 7 | 4 | 0 |
| `qb_v1_reference` | TE | top_36 | 0.111 | 0.556 | 7 | 4 | 0 |
| `qb_floor_horizon_v2` | ALL | top_12 | 0.361 | 0.222 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | ALL | top_24 | 0.292 | 0.375 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | ALL | top_36 | 0.241 | 0.472 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | QB | top_12 | 0.5 | 0.0 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | QB | top_24 | 0.833 | 0.0 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | QB | top_36 | 0.857 | 0.0 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | RB | top_12 | 0.615 | 0.077 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | RB | top_24 | 0.333 | 0.37 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | RB | top_36 | 0.333 | 0.364 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | WR | top_12 | 0.19 | 0.333 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | WR | top_24 | 0.179 | 0.436 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | WR | top_36 | 0.136 | 0.576 | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | TE | top_12 |  |  | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | TE | top_24 |  |  | 2 | 0 | 0 |
| `qb_floor_horizon_v2` | TE | top_36 | 0.111 | 0.556 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | ALL | top_12 | 0.361 | 0.222 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | ALL | top_24 | 0.292 | 0.375 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | ALL | top_36 | 0.241 | 0.472 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | QB | top_12 | 0.5 | 0.0 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | QB | top_24 | 0.833 | 0.0 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | QB | top_36 | 0.857 | 0.0 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | RB | top_12 | 0.615 | 0.077 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | RB | top_24 | 0.333 | 0.37 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | RB | top_36 | 0.333 | 0.364 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | WR | top_12 | 0.19 | 0.333 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | WR | top_24 | 0.179 | 0.436 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | WR | top_36 | 0.136 | 0.576 | 2 | 0 | 0 |
| `wr_qb_combined_v2` | TE | top_12 |  |  | 2 | 0 | 0 |
| `wr_qb_combined_v2` | TE | top_24 |  |  | 2 | 0 | 0 |
| `wr_qb_combined_v2` | TE | top_36 | 0.111 | 0.556 | 2 | 0 | 0 |