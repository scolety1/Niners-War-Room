# Dynasty target contract

At decision season `t`, H1/H2/H3 mean exact-ID NWR VOR in seasons `t`,
`t+1`, and `t+2`. A horizon model may train on an anchor only when
`anchor + (horizon-1) < decision origin`; this ensures the full outcome was
observable. Missing future player-season rows are censored unknown and never
converted to a miss or zero.

D1 combines horizon VOR with one prior-OOF-selected discount schedule from the
fixed SHORT, BALANCED, or PATIENT set. D2 multiplies H2/H3 contributions by
separately predicted above-replacement retention. D3 caps the horizon at three
years, uses one of three position-specific inflection profiles, limits future
age drag to 20%, caps productive-veteran drag at 5%, caps low-games positive
future contribution, and grants no youth bonus. Evaluation uses complete
2018–2023 H1/H2/H3 targets plus retention, starter/elite retention, collapse,
calibration, position, season, age, and games cohorts.
