# Candidate Shadow Rank Calculation Contract

Candidate: `wr_boundary_breakout_sensitivity_guard`

Current status: `DO_NOT_CALCULATE_RANKS_FROM_THIS_PARTIAL_EXPORT`

Required before rank calculation:

- Every row intended for candidate scoring must have non-null `prior_nwr_points`.
- QB rows intended for guard evaluation must have non-null `prior_games`.
- `prior_nwr_ppg` must be safely available if any future candidate variant uses it.
- Missing values must not be converted to zero.

Allowed later, after a successful feature input gate:

- Calculate review-only candidate scores outside app/runtime paths.
- Join candidate shadow scores back to the approved baseline input by `stable_player_id`.
- Produce static CSV/HTML review artifacts only.

Blocked:

- App wiring, live preview, hidden sort, recommendations, production ranking logic, source-truth promotion, and production formula updates.
