# Temporal Availability Contract

- Draft capital is available only after the applicable NFL draft selection.
- Combine measurements are available only after the applicable combine event.
- Weekly statistics and snaps are available only after the game.
- Weekly roster, depth-chart, injury, and practice fields are available only after
  their recorded week/date/report timestamp.
- Seasonal totals are available only after the completed regular season.
- Historical participation is treated as season-end publication and is used only
  for later-season outcomes.
- Mutable present-day player fields are current-only.

All model folds satisfy feature season/date strictly before the target boundary.
The temporal validator fails closed on future snaps, depth charts, injuries,
college season totals, post-draft evidence, and present-day-as-historical fields.
