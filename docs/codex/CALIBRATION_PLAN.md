# Calibration Plan

## Historical Checks
V1 may lack league history. If unavailable, document that limitation and use known-case sanity checks instead of pretending the model is calibrated.

## Sanity Checks
Official top-five rules must use official rank only. QB values must be discounted in 1-QB, 3-point passing TD format unless rushing/start-path changes the profile. Rank 400 must never be treated as confident.

## Calibration Metrics
Track rank stability, label stability, false drop flags, confidence distribution, and whether heavy-drop/high-risk labels match manual review.

## Failure Modes
The model may overrate market rank, underrate league politics, overreact to missing data, treat uncertain rookies as precise, or hide value inside one blended score.

## Tuning Rules
Change weights only with fixture updates, expected-output notes, and clear reason. Do not tune by eyeballing one favorite player.
