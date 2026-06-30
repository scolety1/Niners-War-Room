# Schedule Context Missingness Policy

## Required Missing Value

No current/future schedule row means:

`Not enough information`

This is the only approved missing display value for unavailable schedule context.

## No Inference From Missing Data

Missing schedule data must not mean:

- favorable matchup
- neutral matchup
- difficult matchup
- healthy
- rested
- no game
- zero games
- no opponent
- no bye
- clean availability

## Bye Context

Bye context is a factual team schedule display field only. It is not an injury signal, availability signal, rest score, matchup advantage, projection, recommendation, or rank input.

## Opponent Context

Opponent context is the next scheduled opponent only. It must not be transformed into opponent difficulty, schedule strength, start/sit, projected points, playoff odds, probability, hidden sort, trade value, or pick value.

## Stale Schedule Data

If the tracked artifact does not contain current/future schedule context for a safe row, the lane must display `Not enough information` until Data Hygiene creates a refreshed tracked artifact and a source-policy gate admits it.
