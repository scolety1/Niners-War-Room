# Gauntlet Diversity Audit Source Trace

## Inputs

- Full Review-Only Formula Gauntlet Candidate Arena V1: `C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709`
- Prior Gauntlet commit: `8f57c3b758606204f39787c7ff86e69ee514ed39`
- Medium Review-Only Formula Pilot V1: `C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709\docs\hq\model\medium_review_only_formula_pilot_v1_20260709`
- Small Review-Only Formula Pilot V1: `C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709\docs\hq\model\small_review_only_formula_pilot_v1_20260709`

## Method

The audit read the prior Gauntlet registry, scorecard, position, slice, stability, and outlier artifacts. It imported the prior Gauntlet runner to reconstruct review-only rank vectors for correlation clustering. No candidate definitions were changed.

## Safety

This lane did not run champion refinement, did not tune, did not optimize weights, did not change rankings, did not change app/runtime/model behavior, did not promote sources, and did not push or merge.
