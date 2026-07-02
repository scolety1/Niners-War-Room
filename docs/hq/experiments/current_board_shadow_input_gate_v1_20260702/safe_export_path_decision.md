# Safe Export Path Decision

Decision: `SAFE_EXPORT_GENERATED_REVIEW_ONLY`

Generated local-only export:

`C:\NWR_REVIEW\current_board_shadow_input_gate_v1_20260702\current_board_baseline_shadow_input_review_only.csv`

Checksum:

`85bca72a67860260eb03e5907087c3fe7e7e521fb69779bd3264e747d5908952`

Regeneration command:

```powershell
python docs\hq\experiments\current_board_shadow_input_gate_v1_20260702\build_current_board_shadow_input_gate_v1.py
```

Why local-only:

- The generated file is a review-only baseline input derived from a tracked review artifact.
- Keeping the full export outside the repo avoids introducing a new source-of-truth-looking board file.
- The repo tracks a sample, schema, row-count report, and checksum.
