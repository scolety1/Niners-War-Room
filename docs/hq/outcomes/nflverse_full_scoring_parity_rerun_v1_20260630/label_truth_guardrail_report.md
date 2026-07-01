# Label Truth Guardrail Report

This rerun does not promote label truth.

- `label_truth_allowed=false` in all generated CSV rows.
- `model_use_allowed=false` in all generated CSV rows.
- `training_allowed=false` in all generated CSV rows.
- `source_truth_allowed=false` in all generated CSV rows.
- Existing Outcome labels remain evaluation targets, not input features.
- NFLVerse sidecar rows remain comparison substrate only.
- No probabilities, model experiment, rank change, app wiring, or source-truth approval is created.
