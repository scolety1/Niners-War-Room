# Model v4.3.6 Mature Replay Miss-Pattern Report

## Scope

Primary analysis is limited to mature 2021-2023 rows where `Fantasy-Relevant Replay Pool == True` and outcome maturity is `three_year_window_available`.

No formula weights were changed.

## Dataset

- Mature fantasy-relevant rows: 128
- Strict starter outcomes: 32
- Difference-maker outcomes: 22
- Pattern rows emitted: 104

## Pattern Summary

| Pattern | Rows | Primary Read | Examples |
|---|---:|---|---|
| day_three_rb_hits_worth_preserving | 4 | late RB upside should not be fully suppressed | Rhamondre Stevenson, Kyren Williams, Dameon Pierce, Chase Brown |
| first_round_wr_underranks | 6 | possible Round 1 WR floor issue | Jaylen Waddle, Chris Olave, Jameson Williams, Jordan Addison, Jaxon Smith-Njigba, Quentin Johnston |
| high_ranked_misses | 24 | review examples before candidate tuning | Kadarius Toney, Rondale Moore, Rashod Bateman, D'Wayne Eskridge, Trey Sermon, Kene Nwangwu |
| high_ranked_usable_but_not_starter | 14 | hit definition matters; broad usable is not starter value | Devonta Smith, Javonte Williams, Elijah Moore, Trey Lance, Jahan Dotson, Christian Watson |
| late_capital_production_false_positives | 5 | possible production/team-share overpromotion; test before tuning | Calvin Austin III, Khalil Shakir, Isaiah Spiller, Israel Abanikanda, Evan Hull |
| low_evidence_overpromotion | 15 | confidence caps should be reviewed before formula weights | Devonta Smith, Kadarius Toney, Rondale Moore, Javonte Williams, Rashod Bateman, Elijah Moore |
| low_ranked_difference_makers | 9 | review examples before candidate tuning | Amon-Ra St. Brown, Justin Fields, Brian Robinson Jr., James Cook, Jaxon Smith-Njigba, Bryce Young |
| low_ranked_strict_starter_hits | 14 | review examples before candidate tuning | Amon-Ra St. Brown, Justin Fields, Mac Jones, Rhamondre Stevenson, Brian Robinson Jr., Trey McBride |
| qb_overpromotion | 1 | 1QB QB discipline requires review | Trey Lance |
| qb_underpromotion | 4 | 1QB QB discipline requires review | Justin Fields, Mac Jones, Bryce Young, C.J. Stroud |
| te_overpromotion | 5 | TE cap/exception logic requires review | Kyle Pitts, Pat Freiermuth, Hunter Long, Tommy Tremble, Tre' McKitty |
| te_underpromotion | 3 | TE cap/exception logic requires review | Trey McBride, Sam LaPorta, Tucker Kraft |

## Interpretation

This report is a diagnostic layer, not a formula change. Rows marked `formula_candidate` are candidates for later shadow tests only. Rows marked `data_candidate` should be investigated for source coverage or confidence-cap behavior before component weights are changed.

## Guardrails

- Outcomes remain display-only.
- 2024 and 2025 are excluded from primary miss-pattern analysis.
- No market, ADP, projection, ranking, mock, or big-board fields are used.
- Active rankings, My Team, War Board, readiness gates, and app promotion are unchanged.
