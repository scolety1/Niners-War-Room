# Candidate Feature Input Decision

Decision: `PARTIAL_CANDIDATE_FEATURE_INPUT_NEEDS_REVIEW`

Safe to use now:

- Stable ID exact joins from `stable_player_id` to `player_id_sleeper`.
- Completed 2025 REG factual usage sums for the available primary features.
- Missing rows and blocked features are explicitly null/blank and labeled `Not enough information`.

Not safe yet:

- Candidate rank calculation.
- Candidate score calculation.
- Production formula use.
- App/rank/runtime wiring.

Required before rank calculation:

1. Admit a safe source for `prior_nwr_points`.
2. Admit a safe source for `prior_nwr_ppg`.
3. Admit a safe source for `prior_games`.
4. Re-run this gate and require `candidate_feature_ready_rows > 0`.
