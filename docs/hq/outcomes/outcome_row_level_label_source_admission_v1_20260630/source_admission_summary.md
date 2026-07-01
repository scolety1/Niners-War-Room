# Outcome Row-Level Label Source Admission Summary

## Executive verdict

`GREEN_OUTCOME_ROW_LEVEL_LABEL_SOURCE_ADMITTED_REVIEW_ONLY`

The lane inspected the known local/shared generated Outcome label candidates and admitted the broadest Veteran Outcome V2 row-level sources for compact tracked review use:

- `outcome_v2_extended_season_outcome_labels.csv`
- `outcome_v2_extended_anchor_horizon_labels.csv`

The compact artifact is directly derived from those validated row-level files. It keeps label rows review-only and does not create probabilities, model inputs, training approval, app wiring, or source-truth approval.

## Compact artifact result

| Metric | Value |
| --- | ---: |
| Source season rows | 7,440 |
| Source anchor rows | 7,440 |
| Compact label rows | 119,040 |
| Positions | QB, RB, WR, TE |
| Season coverage | 2012-2024 |
| Scoring mode | exact_verified_first_downs |
| Compact artifact SHA256 | `7c011459fae2874db3203d99cff4c25405319048a14f7f0e3e73ad1c369d533e` |

## Source decision

The older 2019-2024 sources were validated as row-level review-only candidates but were not included in the compact artifact because the 2012-2024 extended sources supersede them. Rookie historical labels are acknowledged but left to the Rookie Outcome lane. The NFL usage target-backtest source is a source-generation input, not the final admitted Outcome V2 row-level label artifact.
