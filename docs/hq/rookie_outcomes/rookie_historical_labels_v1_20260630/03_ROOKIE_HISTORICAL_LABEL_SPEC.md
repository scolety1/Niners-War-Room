# Rookie Historical Label Spec V1 - 2026-06-30

## Threshold Map

- QB: T6, T12
- RB: T6, T12, T24, T36
- WR: T6, T12, T24, T36
- TE: T6, T12

## Horizon Labels

- `rookie_year_top_6/12/24/36`
- `year_2_top_6/12/24/36`
- `first_3y_top_6/12/24/36`
- `first_5y_top_6/12/24/36`

## Definitions

- Rookie year is NFL season equal to approved rookie class/draft year.
- Year 2 is rookie class year plus one.
- First 3 years hits if the player reaches the threshold at least once from rookie year through year 3.
- First 5 years hits if the player reaches the threshold at least once from rookie year through year 5.

## Censoring

- Recent classes without full windows are `right_censored`.
- Incomplete future windows must not be counted as misses.
- Missing labels must be `Not enough information`, never `0%`.

## Scoring

- Prefer `exact_verified_first_downs` from factual NFL player-season data.
- If exact scoring is unavailable, keep approximation modes separate.
- Do not silently zero-fill missing scoring components unless source policy approves it.

## Status

This spec is ready for a future build, but no label artifact was generated
because the draft-class/identity bridge is blocked.
