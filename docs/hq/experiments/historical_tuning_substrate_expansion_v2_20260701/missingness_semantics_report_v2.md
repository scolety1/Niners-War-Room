# Missingness Semantics Report V2

V2 does not perform new missing-to-zero conversion.

The expanded Backtest V1 source still carries legacy zero-fill semantics. V2 reduces that risk by replacing optional-source encoded zeros with null for:

- `prior_offensive_snaps` and `prior_offense_pct` where `snap_pct_missing=1`: `811` rows
- `prior_receiving_air_yards` and `prior_receiving_yards_after_catch` where `air_yards_missing=1`: `663` rows

Core seasonal stat fields remain source-recorded review-only values from the Backtest V1 output. They are not production-approved and need a future source-semantics audit before any tuning lane treats zero values as explicit absence.
