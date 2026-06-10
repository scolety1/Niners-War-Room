# Shadow Model Tournament - 2026-06-10

This is a shadow/evaluation tournament only. No production Rankings, Draft Prep, Live Draft Room, data pack, or Decision Board output is promoted or overwritten.

## Guardrails

- No ADP, market rank, public rankings, consensus, projections, trade calculators, RotoWire rankings/projections, prior draft history, or legacy active-pack private_score are used as scoring inputs.
- Team/roster tags are display-only.
- Legal draft pool remains pending.
- Outcome percentages remain in development.

## Experiment Summary

| Experiment | Classification | Historical result | Pattern read | Failure mode |
|---|---|---|---|---|
| `production_baseline` | baseline | Baseline top-24 strict hit rate 0.264 and bust rate 0.389. | Baseline pattern counts only. | Baseline only. |
| `established_wr_proof_lane` | needs_more_review | Top-24 strict hit rate 0.264 vs baseline 0.264; bust rate 0.403 vs baseline 0.389. | Tests first-round WR underrank family (6 rows). | May overprotect WRs if current private VORP/review points reflect one-year spikes rather than durable proof. |
| `rb_dynasty_horizon` | reject_too_much_current_board_disruption | Top-24 strict hit rate 0.264 vs baseline 0.264; bust rate 0.389 vs baseline 0.389. | Tests late-capital RB false positives (5) while preserving day-three RB hit family (4). | May suppress real late-RB hits if role/receiving path is genuine. |
| `te_no_premium_exception_gate` | needs_more_data | Top-24 strict hit rate 0.264 vs baseline 0.264; bust rate 0.389 vs baseline 0.389. | Tests TE over/underpromotion families (5 / 3). | May overcompress young elite TEs such as Brock Bowers if current VORP gap is small. |
| `elite_qb_floor_horizon` | needs_more_review | Top-24 strict hit rate 0.264 vs baseline 0.264; bust rate 0.389 vs baseline 0.389. | Tests QB over/underpromotion families (1 / 4). | May lift mediocre high-volume QBs unless floor gate is paired with better retained-value labels. |
| `missing_evidence_policy` | needs_more_review | Top-24 strict hit rate 0.264 vs baseline 0.264; bust rate 0.389 vs baseline 0.389. | Tests low-evidence overpromotion family (15 rows). | May be too blunt until missing-source reason is separated from missing-player-trait reason. |

## Required Historical Metrics

| Experiment | Position | Window | Strict hit rate | Bust rate | High misses | Low-hit capture |
|---|---|---|---:|---:|---:|---:|
| `production_baseline` | ALL | top_12 | 0.361 | 0.222 | 8 | 0 |
| `production_baseline` | ALL | top_24 | 0.264 | 0.389 | 28 | 0 |
| `production_baseline` | ALL | top_36 | 0.222 | 0.491 | 28 | 0 |
| `production_baseline` | QB | top_12 | 0.5 | 0.0 | 0 | 0 |
| `production_baseline` | QB | top_24 | 0.75 | 0.0 | 0 | 0 |
| `production_baseline` | QB | top_36 | 0.8 | 0.0 | 0 | 0 |
| `production_baseline` | RB | top_12 | 0.615 | 0.077 | 1 | 0 |
| `production_baseline` | RB | top_24 | 0.333 | 0.37 | 10 | 0 |
| `production_baseline` | RB | top_36 | 0.324 | 0.382 | 10 | 0 |
| `production_baseline` | WR | top_12 | 0.19 | 0.333 | 7 | 0 |
| `production_baseline` | WR | top_24 | 0.175 | 0.45 | 18 | 0 |
| `production_baseline` | WR | top_36 | 0.133 | 0.583 | 18 | 0 |
| `production_baseline` | TE | top_12 |  |  | 0 | 0 |
| `production_baseline` | TE | top_24 | 0.0 | 0.0 | 0 | 0 |
| `production_baseline` | TE | top_36 | 0.111 | 0.556 | 0 | 0 |
| `established_wr_proof_lane` | ALL | top_12 | 0.361 | 0.25 | 9 | 0 |
| `established_wr_proof_lane` | ALL | top_24 | 0.264 | 0.403 | 29 | 0 |
| `established_wr_proof_lane` | ALL | top_36 | 0.222 | 0.491 | 29 | 0 |
| `established_wr_proof_lane` | QB | top_12 | 0.0 | 0.0 | 0 | 0 |
| `established_wr_proof_lane` | QB | top_24 | 0.75 | 0.0 | 0 | 0 |
| `established_wr_proof_lane` | QB | top_36 | 0.8 | 0.0 | 0 | 0 |
| `established_wr_proof_lane` | RB | top_12 | 0.667 | 0.083 | 1 | 0 |
| `established_wr_proof_lane` | RB | top_24 | 0.375 | 0.333 | 8 | 0 |
| `established_wr_proof_lane` | RB | top_36 | 0.324 | 0.382 | 8 | 0 |
| `established_wr_proof_lane` | WR | top_12 | 0.217 | 0.348 | 8 | 0 |
| `established_wr_proof_lane` | WR | top_24 | 0.163 | 0.488 | 21 | 0 |
| `established_wr_proof_lane` | WR | top_36 | 0.133 | 0.583 | 21 | 0 |
| `established_wr_proof_lane` | TE | top_12 |  |  | 0 | 0 |
| `established_wr_proof_lane` | TE | top_24 | 0.0 | 0.0 | 0 | 0 |
| `established_wr_proof_lane` | TE | top_36 | 0.111 | 0.556 | 0 | 0 |
| `rb_dynasty_horizon` | ALL | top_12 | 0.361 | 0.222 | 8 | 1 |
| `rb_dynasty_horizon` | ALL | top_24 | 0.264 | 0.389 | 28 | 1 |
| `rb_dynasty_horizon` | ALL | top_36 | 0.231 | 0.481 | 28 | 1 |
| `rb_dynasty_horizon` | QB | top_12 | 0.5 | 0.0 | 0 | 1 |
| `rb_dynasty_horizon` | QB | top_24 | 0.75 | 0.0 | 0 | 1 |
| `rb_dynasty_horizon` | QB | top_36 | 0.833 | 0.0 | 0 | 1 |
| `rb_dynasty_horizon` | RB | top_12 | 0.615 | 0.077 | 1 | 0 |
| `rb_dynasty_horizon` | RB | top_24 | 0.429 | 0.238 | 5 | 0 |
| `rb_dynasty_horizon` | RB | top_36 | 0.333 | 0.364 | 5 | 0 |
| `rb_dynasty_horizon` | WR | top_12 | 0.19 | 0.333 | 7 | 0 |
| `rb_dynasty_horizon` | WR | top_24 | 0.152 | 0.5 | 23 | 0 |
| `rb_dynasty_horizon` | WR | top_36 | 0.133 | 0.583 | 23 | 0 |
| `rb_dynasty_horizon` | TE | top_12 |  |  | 0 | 0 |
| `rb_dynasty_horizon` | TE | top_24 | 0.0 | 0.0 | 0 | 0 |
| `rb_dynasty_horizon` | TE | top_36 | 0.111 | 0.556 | 0 | 0 |
| `te_no_premium_exception_gate` | ALL | top_12 | 0.361 | 0.222 | 8 | 1 |
| `te_no_premium_exception_gate` | ALL | top_24 | 0.264 | 0.389 | 28 | 1 |
| `te_no_premium_exception_gate` | ALL | top_36 | 0.231 | 0.481 | 28 | 1 |
| `te_no_premium_exception_gate` | QB | top_12 | 0.5 | 0.0 | 0 | 0 |
| `te_no_premium_exception_gate` | QB | top_24 | 0.75 | 0.0 | 0 | 0 |
| `te_no_premium_exception_gate` | QB | top_36 | 0.8 | 0.0 | 0 | 0 |
| `te_no_premium_exception_gate` | RB | top_12 | 0.615 | 0.077 | 1 | 1 |
| `te_no_premium_exception_gate` | RB | top_24 | 0.333 | 0.37 | 10 | 1 |
| `te_no_premium_exception_gate` | RB | top_36 | 0.343 | 0.371 | 10 | 1 |
| `te_no_premium_exception_gate` | WR | top_12 | 0.19 | 0.333 | 7 | 0 |
| `te_no_premium_exception_gate` | WR | top_24 | 0.175 | 0.45 | 18 | 0 |
| `te_no_premium_exception_gate` | WR | top_36 | 0.133 | 0.583 | 18 | 0 |
| `te_no_premium_exception_gate` | TE | top_12 |  |  | 0 | 0 |
| `te_no_premium_exception_gate` | TE | top_24 | 0.0 | 0.0 | 0 | 0 |
| `te_no_premium_exception_gate` | TE | top_36 | 0.125 | 0.5 | 0 | 0 |
| `elite_qb_floor_horizon` | ALL | top_12 | 0.333 | 0.222 | 8 | 2 |
| `elite_qb_floor_horizon` | ALL | top_24 | 0.264 | 0.389 | 28 | 2 |
| `elite_qb_floor_horizon` | ALL | top_36 | 0.241 | 0.463 | 28 | 2 |
| `elite_qb_floor_horizon` | QB | top_12 | 0.0 | 0.0 | 0 | 2 |
| `elite_qb_floor_horizon` | QB | top_24 | 0.75 | 0.0 | 0 | 2 |
| `elite_qb_floor_horizon` | QB | top_36 | 0.75 | 0.0 | 0 | 2 |
| `elite_qb_floor_horizon` | RB | top_12 | 0.615 | 0.077 | 1 | 0 |
| `elite_qb_floor_horizon` | RB | top_24 | 0.333 | 0.37 | 10 | 0 |
| `elite_qb_floor_horizon` | RB | top_36 | 0.333 | 0.364 | 10 | 0 |
| `elite_qb_floor_horizon` | WR | top_12 | 0.182 | 0.318 | 7 | 0 |
| `elite_qb_floor_horizon` | WR | top_24 | 0.175 | 0.45 | 18 | 0 |
| `elite_qb_floor_horizon` | WR | top_36 | 0.138 | 0.569 | 18 | 0 |
| `elite_qb_floor_horizon` | TE | top_12 |  |  | 0 | 0 |
| `elite_qb_floor_horizon` | TE | top_24 | 0.0 | 0.0 | 0 | 0 |
| `elite_qb_floor_horizon` | TE | top_36 | 0.111 | 0.556 | 0 | 0 |
| `missing_evidence_policy` | ALL | top_12 | 0.361 | 0.222 | 8 | 0 |
| `missing_evidence_policy` | ALL | top_24 | 0.264 | 0.389 | 28 | 0 |
| `missing_evidence_policy` | ALL | top_36 | 0.222 | 0.491 | 28 | 0 |
| `missing_evidence_policy` | QB | top_12 | 0.5 | 0.0 | 0 | 0 |
| `missing_evidence_policy` | QB | top_24 | 0.75 | 0.0 | 0 | 0 |
| `missing_evidence_policy` | QB | top_36 | 0.8 | 0.0 | 0 | 0 |
| `missing_evidence_policy` | RB | top_12 | 0.615 | 0.077 | 1 | 0 |
| `missing_evidence_policy` | RB | top_24 | 0.333 | 0.37 | 10 | 0 |
| `missing_evidence_policy` | RB | top_36 | 0.324 | 0.382 | 10 | 0 |
| `missing_evidence_policy` | WR | top_12 | 0.19 | 0.333 | 7 | 0 |
| `missing_evidence_policy` | WR | top_24 | 0.175 | 0.45 | 18 | 0 |
| `missing_evidence_policy` | WR | top_36 | 0.133 | 0.583 | 18 | 0 |
| `missing_evidence_policy` | TE | top_12 |  |  | 0 | 0 |
| `missing_evidence_policy` | TE | top_24 | 0.0 | 0.0 | 0 | 0 |
| `missing_evidence_policy` | TE | top_36 | 0.111 | 0.556 | 0 | 0 |

## Combined Shadow Model

No combined shadow model was created in this pass. The individual lanes did not produce enough support to justify combining them: WR proof, elite QB floor, and missing-evidence policy need more review; RB horizon was too disruptive; and the TE gate needs more data.

A combined model should wait for a second tournament after the individual lanes are tightened.