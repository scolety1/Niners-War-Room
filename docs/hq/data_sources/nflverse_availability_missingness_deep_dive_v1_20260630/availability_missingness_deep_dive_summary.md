# Availability Missingness Deep-Dive Summary

Verdict: `YELLOW_AVAILABILITY_DEEP_DIVE_READY_HEALTH_INFERENCE_BLOCKED`

## Base

- Control branch: `origin/work/hq-parallel-control`
- Base HEAD after fetch: `9dafea81b3316a02f8a051762b9d53dc84791fc7`

## Evidence Inputs

- Model candidate readiness matrix rows: `21`
- Experiment-approved rows in readiness matrix: `0`
- Denominator display artifact rows: `588`
- Denominator `SAFE_NOW_DISPLAY_ONLY` rows: `437`
- Denominator `NEED_SOURCE_FIELDS` rows: `43`
- Denominator `NEED_IDENTITY_APPROVAL` rows: `108`
- Player context display artifact rows: `294`
- Player context identity-safe rows: `281`
- Player context identity-gated rows: `13`

## Core Finding

Availability denominator data is useful as display/review context where a prior
display lane already allows safe rows. It is not safe for experiment, model,
training, source-truth, rank, hidden-sort, recommendation, trade-value, or
pick-value use.

`games_missed_while_rostered` remains fully blocked. The tracked artifacts show
`0` safe values and `588` `Not enough information` values for that field. Current
evidence cannot distinguish a missed game from missing snap data, missing stat
data, missing roster data, schedule/bye handling, inactive ambiguity, source
coverage gaps, or injury-report absence.

## Field Matrix Result

- Fields audited: `15`
- Fields display-capable with caveats: `14`
- Fields blocked from display value: `1`
- Fields safe for experiment now: `0`
- Fields safe for model now: `0`
- Fields safe for training now: `0`
- Fields safe for source truth now: `0`
- Fields safe for health inference now: `0`
- Fields that safely represent absence now: `0`

## Standing Rules

- Missing injury data is not healthy.
- Missing roster data is not clean, active, inactive, off-roster, or safe.
- Missing snap data is not zero usage.
- Missing stat data is not zero production.
- Missing roster/snap/stat data is not missed-game evidence.
- Identity recommendations are not approved joins.
- Identity-review rows expose no denominator detail.

## Recommendation

Keep existing display-only denominator context for supported rows. Do not move
any availability field into experiment or modeling until a future point-in-time
replay lane proves source as-of timing, identity safety, label interaction,
missingness, and censoring behavior.
