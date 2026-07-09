# Formula Data Mart Remaining Upgrade Sweep V1 Report

## Verdict

`GREEN_REMAINING_DATA_UPGRADES_PRIORITIZED_WITH_EXECUTABLE_NEXT_LANE`

## Clear Answer

The remaining useful data upgrades are now prioritized with an accuracy-first filter. Red-zone exact receipts are the highest near-term formula-accuracy target, but the next lane must be a gated review-only pilot that stops if source/as-of proof fails.

## Targets Reviewed

- `red_zone_exact_receipts`: 234 candidate artifacts ledgered
- `shadow_model_v2_metrics`: 80 candidate artifacts ledgered
- `historical_checkpoint_review_score`: 123 candidate artifacts ledgered
- `historical_position_specific_review_score`: 141 candidate artifacts ledgered
- `age_lifecycle_sidecars`: 509 candidate artifacts ledgered
- `point_in_time_injury_availability_gates`: 80 candidate artifacts ledgered
- `point_in_time_market_adp_gates`: 80 candidate artifacts ledgered

## Explicitly De-Scoped

- `route_yprr_tprr`
- `return_scoring_receipts`
- `broad_pfr_feature_promotion`
- `pff_elusive_rating`
- `nwr_elusive_proxy_review_only`
- `super_advanced_data_not_currently_source_accurate`

## Highest-Value Available Upgrade

`age_lifecycle_sidecars` are the most executable currently available upgrade because candidate partial/current artifacts exist and the next step is freeze/validation rather than value regeneration.

## Highest-Priority Missing Upgrade

`red_zone_exact_receipts` remain the highest-priority missing feature by likely formula value, but require source-gate/as-of proof before regeneration.

## Next Executable Target

`Model v4 Red Zone Exact Receipt Regeneration Pilot V1`, with a mandatory source/as-of gate and stop condition before value generation if unsafe.

## Accuracy-Priority Filter

- `DIRECT_FORMULA_ACCURACY_PRIORITY`, `FORMULA_GAUNTLET_READINESS_PRIORITY`, `RANKING_INTEGRATION_PRIORITY`, and `PARK_FOR_LATER` are included in the target matrix and priority ranking.
- Red-zone is prioritized for near-term formula accuracy.
- Shadow metrics, return scoring, route/YPRR/TPRR, broad PFR expansion, PFF-style elusive/proxy naming, and unsupported advanced data are parked or de-scoped unless a later approved lane proves direct near-term value.

## Gates Preserved

- Formula Gauntlet remains blocked.
- Exact Model v4 replay remains blocked.
- Production/model-use remains blocked.
- Rankings integration remains blocked.
- No source was promoted.
