# Player Compare UI integration

The Outcome/Horizon tab gains the expanded Outcome V3 comparison. For every
selected player's applicable threshold family it shows 2026, 2027, 2028,
Within 3 Years, Within 5 Years, and Two Qualifying Seasons Within 3 Years,
including probability, calibration status, historical sample, confidence,
evidence state, and missing-state explanation.

The adapter joins only exact `player_id`. An unsupported or unidentified player
is `Not enough information`; there is no name fallback. Existing V1/V2
comparison routes and aliases remain available below the V3 surface. Release:
`NWR_OUTCOME_COLUMNS_V3_RC1`.
