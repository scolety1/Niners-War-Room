# Excluded Or Optional Feature Report

## Excluded optional fields

- `air yards share`
- `true routes run`
- `TPRR`
- `YPRR`
- `direct return touchdown subtype`

## Reasoning

- Route metrics are optional and do not block the main phase. True routes, TPRR, and YPRR need an admitted rights-cleared source and denominator policy.
- Do not create fake route proxies from participation data.
- Share-style fields such as `air_yards_share` are quarantined in the player_stats source admission/runner policy and are not needed for the first lagged usage builder.
- Direct return touchdown subtype is unavailable and irrelevant to this usage phase; `special_teams_tds` must not be substituted.
- Vendor/rank/projection/market fields remain blocked as source truth and model input.
