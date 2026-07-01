# Next Phase Handoff

Recommended next phase: `Historical Formula Candidate Search V1`.

Conditions:

- It must be review-only.
- It must rerun a frozen V3 baseline first.
- It must use the fixed train/validation/holdout split from this gate.
- It must use only the allowed candidate formula families from this packet.
- It must exclude null-fenced optional features from the primary pass.
- It must stop on any guardrail failure.

Do not run another substrate expansion unless the candidate-search readiness or execution gate identifies a concrete missing source artifact. Do not start production tuning, app wiring, ranking changes, recommendations, or source-truth promotion.
