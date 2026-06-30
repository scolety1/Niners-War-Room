# Next Lane Prompt If Human Approvals Are Provided

You are Codex working in Niners War Room Data Hygiene.

Task: Apply explicitly approved NFLVerse player-context identity decisions as a review-only overlay.

Inputs:
- `docs/hq/data_sources/nflverse_player_context_human_identity_review_20260630/human_identity_decision_review.csv`
- current tracked player context display artifact
- current identity hardening packet

Rules:
- Only rows with `human_decision=APPROVE_REVIEW_ONLY` and `approved_by_human=true` may enter an approved overlay.
- Do not accept Codex recommendations as approvals.
- Do not accept name-only or fuzzy approval evidence.
- Keep every overlay row `review_only=true`.
- Keep model/training/source-truth/rank/hidden-sort/trade/pick flags false.
- Do not rebuild the player context artifact until overlay validation passes.
- Do not change app pages or model/rank/source-truth behavior.

Expected outputs:
- approved overlay CSV if and only if explicit approvals exist
- apply-readiness report
- guardrail report
- tests/checks proving no pending/rejected/blocked rows were applied
