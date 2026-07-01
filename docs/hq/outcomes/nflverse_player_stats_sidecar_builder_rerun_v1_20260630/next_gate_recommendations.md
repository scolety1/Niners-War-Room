# Next Gate Recommendations

## Immediate Next Gate

Create an approved `NFLVerse Player Stats Compact Sidecar Derivation Runner V1`.

That lane should explicitly approve a runner/service to:

- read only the two admitted receipt rows;
- verify the receipt SHA values against the local snapshot files;
- exclude all quarantined fields;
- emit a compact tracked review-only `player_stats_sidecar_artifact.csv`;
- keep every label truth, model, training, and source-truth flag false;
- avoid app/runtime dependencies on raw local files.

## Required Future Derivation Checks

- receipt row filtering: `review_use_allowed=true` and `sidecar_builder_allowed=true`;
- SHA verification;
- schema validation against the 119-row schema manifest;
- quarantined-field exclusion;
- missing-stat handling as `Not enough information`, not zero;
- identity join status;
- sidecar row count by dataset, season, week, position, and stat family;
- no label truth/model/training/source-truth promotion.

## After Compact Sidecar Exists

Run a label-parity validator lane to compute:

- matched players;
- unmatched existing labels;
- unmatched NFLVerse rows;
- identity match rate;
- scoring parity;
- censoring parity;
- mismatch categories.

## Still Blocked

- label truth promotion;
- model input use;
- training use;
- source-truth use;
- active current-player probabilities;
- active rookie probabilities;
- Rankings or app wiring;
- missing stats as zero;
- raw/shared/cache/local export tracking.
