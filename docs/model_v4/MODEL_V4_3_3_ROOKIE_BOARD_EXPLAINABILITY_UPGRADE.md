# Model v4.3.3 Rookie Board Explainability Upgrade

## Goal

Make the Draft Room prospect board understandable enough for human review after the rookie formula balance repair.

This is a UI/explainability upgrade only. It does not change active rankings, My Team, War Board, readiness gates, app promotion, or final recommendations.

## What Changed

The Draft Room rookie board now surfaces the main formula components directly in the prospect table:

- overall rookie rank
- player, position, NFL team, and college
- final league-format score
- production score
- College Team Share score
- NFL Draft Pick Signal
- athletic score
- recruiting score
- age score
- confidence cap
- evidence availability
- Trust Level
- draft round and overall pick
- model edge or source warning label
- short "why this rank" text

The UI labels were renamed for human review:

- Market Share is shown as College Team Share.
- Draft Capital is shown as NFL Draft Pick Signal.
- Evidence Status is shown as Trust Level.
- Manual Scout Source Review is shown as Needs Human Review.

## Filters

The Draft Room rookie analyzer now supports filters for:

- pick window
- position
- board band
- Trust Level
- NFL team
- draft round, including No draft capital
- warning type

Warning filters use specific warning codes rather than only filtering to any warning.

## Player Drilldown

Each player can be opened in a detail section with:

- component breakdown
- source receipts
- warning summary
- draft capital rows
- workout profile
- depth chart context
- market context in a separate non-scoring tab

Market, ADP, ranking, and projection context remains labeled as non-scoring and does not drive private football value.

## Guardrails

- No final rookie recommendations were created.
- No active rankings were changed.
- My Team and War Board were not mutated.
- The Draft Room remains review-only.
- Market/projection/ranking/ADP fields remain context-only.

## Review Notes

The board should now make unusual outputs easier to inspect. For example, a player with a high model score despite weaker NFL Draft Pick Signal can be reviewed through the component table, warning label, receipts, and non-scoring context without hiding the model edge.
