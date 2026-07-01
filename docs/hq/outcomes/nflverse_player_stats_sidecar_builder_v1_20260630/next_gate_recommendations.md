# Next Gate Recommendations

## Immediate Next Step

Create an approved `NFLVerse Player Stats Source Row Runner / Tracking Gate`.

That gate should decide whether a runner may create a tracked or review-only generated row-level player_stats source artifact without violating raw/shared/cache restrictions.

## Required Future Evidence

- source manifest;
- row-level weekly or seasonal player_stats source rows;
- source/as-of timestamp;
- identity join status;
- schema validation;
- row counts by season, week, position, team, and stat family;
- missingness and censoring rules;
- explicit no-label-truth statement.

## After Source Rows Exist

Run `NFLVerse Player Stats Sidecar Builder V1` again to create:

- `player_stats_sidecar_artifact.csv`;
- coverage matrix with real sidecar rows;
- unmatched source row reports if feasible;
- identity and missingness summaries.

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
