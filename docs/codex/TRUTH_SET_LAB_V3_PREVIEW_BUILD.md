# Truth Set Lab v3 Preview Build

Generated: 2026-05-15

## Purpose

Truth Set Lab v3 builds a review-only model preview using only structured free-data sources. It does not overwrite active rankings, active data packs, or decision gates.

## Inputs Used

- Native nflverse player production and real rushing/receiving first downs.
- Usage derived from nflverse play-by-play.
- nflverse snap counts as snap share only.
- Recomputed LVE projection points from raw projected stat columns where valid.
- Young-player bridge prior where factual draft-capital fields are available.
- Sourced injury context only.
- Sourced market context only, for trade/liquidity context.

## Inputs Rejected Or Quarantined

- Rejected agent production CSV.
- Rejected role/usage CSV.
- Supplied non-LVE projection points.
- Fake route values: routes run, route participation, TPRR, and YPRR remain unavailable from the structured free/public source stack and are held neutral with review warnings.

## Latest Preview

Preview folder:

`local_exports/nflverse_model_previews/truth_set_lab_v3_preview_20260515T084344`

Generated files:

- `stats_first_veteran_model_preview_outputs.csv`
- `stats_first_feature_contributions.csv`
- `stats_first_normalized_features.csv`
- `truth_set_v3_source_coverage.csv`
- `truth_set_v3_rejected_field_log.csv`
- `truth_set_v3_movement_vs_v2.csv`
- `truth_set_v3_preview_summary.csv`
- `truth_set_v3_preview_summary.json`
- `truth_set_v3_preview_manifest.json`

## Summary

- Review status: review-only
- Active outputs overwritten: false
- Truth-set players: 40
- Normalized rows: 1039
- Truth-set rows overlayed: 40
- Native production rows applied: 35
- Derived usage rows applied: 35
- Snap-share rows applied: 35
- Projection recompute rows applied: 37
- Young bridge rows applied: 20
- Sourced injury context rows: 7
- Sourced market context rows: 5
- Route rows quarantined: 40
- Rejected field log rows: 160
- Large movement vs v2 rows: 5

## Notes

This preview intentionally keeps route/participation unavailable rather than treating snap share as a route proxy. That is the correct conservative behavior for free/public data. The next audit should focus on the five large v2 movement rows and any high-value players with missing projection, production, usage, or snap coverage.
