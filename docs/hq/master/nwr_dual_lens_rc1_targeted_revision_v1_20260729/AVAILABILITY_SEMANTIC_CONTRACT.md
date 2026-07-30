# Availability semantic contract

`EXPECTED_GAMES_FRACTION` is a continuous expectation in [0,1].
`EXPECTED_GAMES_PLAYED` is that fraction times target-season length. They are
evaluated with MAE, RMSE, residuals, and linear calibration diagnostics.

`P(GAMES_PLAYED >= 8)` is a distinct chronological binary probability trained
against `availability_8plus_actual`. It alone receives Brier, binary log loss,
ECE, calibration slope/intercept, event-count, position, and season tests.
Neither output may silently substitute for the other. Win Now gates require
both semantic families to be valid.
