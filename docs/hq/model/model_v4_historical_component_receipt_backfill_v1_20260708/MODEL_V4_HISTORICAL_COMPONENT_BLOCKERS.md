# Model v4 Historical Component Blockers

## Ranked Blockers

1. **checkpoint_review_score exact historical rows missing**
   - Evidence: No season-by-season `current_player_value_full_board_review_rows.csv` equivalent exists.
   - Impact: Blocks exact `nwr_dynasty_score` and exact rank replay.

2. **position_specific_review_score component receipts missing**
   - Evidence: Current component rows exist only for current board; historical normalized component scores/weights are absent.
   - Impact: Blocks exact QB/RB/WR/TE component score replay.

3. **lifecycle, age, role archetype, confidence cap history missing**
   - Evidence: Current lifecycle age adapter reproduced 2026 board, but historical age/role/confidence receipts are not available.
   - Impact: Blocks exact checkpoint replay and old-pocket QB guardrail history.

4. **route/YPRR/TPRR/red-zone exact receipts missing**
   - Evidence: Partial V3 panel has targets/yards/air-yard/YAC overlap but not true route denominators or exact current scoring transforms.
   - Impact: Blocks exact WR/TE route role and efficiency components.

5. **return scoring and shadow sidecars missing**
   - Evidence: `shadow_model_v2_metrics.csv` and historical return-scoring receipts remain absent.
   - Impact: Blocks exact shadow/guardrail and return component replay if required.

6. **source admission remains review-only**
   - Evidence: The current board remains candidate/review-only, and the partial panel is not model/training/source-truth approved.
   - Impact: Blocks production accuracy claims and source promotion.

## Cold-Water Accuracy Caveat

Production Rankings Backtest V1 found useful signal, but the current-formula-family proxy did not beat simple prior-year finish overall. This lane does not change that evidence and does not claim production accuracy.

## Shadow / Sidecar Caveats

- `shadow_model_v2_metrics.csv` remains missing for exact shadow/guardrail historical replay if required.
- The exact original `veteran_player_inputs.csv` age sidecar remains absent.
- The current-board age adapter reproduced the current board exactly, but this does not prove historical age/lifecycle validity.
