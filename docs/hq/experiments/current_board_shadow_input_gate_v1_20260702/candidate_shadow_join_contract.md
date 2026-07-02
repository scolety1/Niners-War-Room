# Candidate Shadow Join Contract

Later static comparison target: `wr_boundary_breakout_sensitivity_guard`

Join keys for a future static side-by-side packet:

- Primary: `stable_player_id`
- Audit support: `player_name`, `position`, `team`

Baseline-side fields:

- `current_baseline_rank`
- `current_baseline_position_rank`
- `current_baseline_tier_bucket`
- `warning_flags`

Candidate-side fields to add later, only after a candidate feature input gate:

- `selected_candidate_shadow_score`
- `selected_candidate_shadow_rank`
- `selected_candidate_shadow_position_rank`
- `rank_delta`
- `position_rank_delta`
- `movement_bucket`
- `review_only_label`

Rules:

- Candidate rows must not overwrite baseline ranks.
- Candidate outputs must remain outside app/runtime paths.
- Missing candidate feature rows must stay missing or be labeled not-enough-information; do not convert missing values to zero.
- Non-QB/RB/WR/TE baseline rows stay baseline-only unless a future source gate explicitly admits a candidate feature path for them.
- This join may only produce static review artifacts.
