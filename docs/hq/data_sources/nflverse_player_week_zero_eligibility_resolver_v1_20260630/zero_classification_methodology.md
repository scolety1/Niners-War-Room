# Zero Classification Methodology

## Classification Order

1. Identity-gated rows are `IDENTITY_GATED` and cannot expose safe zero.
2. Existing player_stats rows with any nonzero audited scoring component are `OBSERVED_NONZERO_STATS`.
3. Existing player_stats rows with all audited scoring components explicitly numeric zero are `OBSERVED_EXPLICIT_ZERO_STATS`.
4. Missing player_stats rows are never zero by default.
5. Missing player_stats rows become `ROSTERED_ACTIVE_NO_STATS_SAFE_ZERO` only when all of these are true:
   - safe NWR/NFLVerse identity;
   - approved weekly roster row exists;
   - weekly roster status is `ACT`;
   - team has a scheduled game that week;
   - player_stats source has coverage for that team-season-week;
   - no injury report `Out` blocker applies;
   - snap-count evidence proves participation.
6. Bye/no team game, injury out, inactive roster status, not rostered, unknown team/schedule, missing source coverage, and unresolved active/no-snap cases stay not-zero or `Not enough information`.

## Components Used For Existing player_stats Rows

The audited component set excludes `special_teams_tds`. No direct return touchdown field was found. Missing direct return TD remains a scoring-component blocker for later parity, but not for zero eligibility classification.
