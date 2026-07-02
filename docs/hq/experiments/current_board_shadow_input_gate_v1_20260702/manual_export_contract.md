# Manual Export Contract

Manual export is not required for this gate because a safe review-only export was generated.

If Tim wants a direct raw app-source baseline later, use this contract:

1. Start from a clean worktree or a read-only copy.
2. Confirm `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` exists and is the intended approved current board.
3. Export only the safe fields listed in `required_baseline_export_schema.csv`.
4. Write the resulting file outside the repo, for example:

   `C:\NWR_REVIEW\current_board_shadow_input_gate_v1_20260702\current_board_baseline_shadow_input_review_only.csv`

5. Do not copy raw `local_exports` into git.
6. Do not include candidate formula outputs, market/ADP/vendor/projection fields as source truth, hidden sort fields, recommendations, production approval flags, or app wiring flags.
7. Record row count and checksum before any later static side-by-side shadow packet.

Current generated export from this gate:

- Rows: `370`
- SHA256: `85bca72a67860260eb03e5907087c3fe7e7e521fb69779bd3264e747d5908952`
