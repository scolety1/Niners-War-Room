# Current Board Candidate Feature Input Gate Summary

Decision: `PARTIAL_CANDIDATE_FEATURE_INPUT_NEEDS_REVIEW`

This gate generated a partial current-board candidate feature input for `wr_boundary_breakout_sensitivity_guard` using completed 2025 NFLVerse Core Usage Review Dataset facts where a stable ID join was available.

Key facts:

- Baseline input rows: `370`
- Baseline checksum: `85bca72a67860260eb03e5907087c3fe7e7e521fb69779bd3264e747d5908952`
- Feature anchor season: `2025`
- Prediction anchor: `2026_current_board_shadow_review`
- Exact feature joins: `245`
- Candidate-feature-ready rows: `0`
- 2025 raw usage rows / after exact dedup: `37078` / `18539`
- Outside export: `C:\NWR_REVIEW\current_board_candidate_feature_input_gate_v1_20260702\current_board_candidate_feature_input_review_only.csv`
- Outside export checksum: `163da41dedb5c4a05f16c00a8788ff3130db5d794894d400c5f111bf58af1235`

Why partial:

- `prior_nwr_points` and `prior_nwr_ppg` remain blocked because Core Usage Review Dataset V1 does not carry the full scoring components required to derive NWR scoring safely.
- `prior_games` remains blocked because weekly row counts have not been admitted as the source-contract games denominator.
- Therefore no current-board candidate ranks should be calculated from this export yet.
- Exact duplicate source rows were collapsed before aggregation; no fuzzy matching or missing-as-zero transformation was applied.
