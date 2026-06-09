# Model v4.6 Pick Equivalent Field Cleanup

## Goal

Patch the non-blocking v4.5 audit concern that Cut Cost rows had long pick-equivalent strings when 2026 5.04 was manual-only.

## Changes

- Kept `rookie_pick_equivalent` as the short human-facing pick context.
- Added `pick_baseline_status`.
- Added `pick_equivalent_confidence`.
- Added `pick_equivalent_warning`.
- Updated the June 15 Cut Cost display to show those fields separately.
- Regenerated roster opportunity cost outputs.

## 2026 5.04 Handling

The 2026 5.04 pick remains `manual_only_no_exact_model_baseline`.

That status now appears in `pick_baseline_status` and `pick_equivalent_warning`, not inside the main `rookie_pick_equivalent` display string.

## Safety

No synthetic 5.04 baseline was created. Missing baseline evidence remains missing, and exact cut/trade/draft equivalence remains blocked when the model does not have an admitted baseline.

This patch does not change formulas, scores, active rankings, My Team, War Board, readiness gates, app promotion, or final recommendations.
