# Next Lane Prompt For Approved Overlay Apply / Rebuild

You are Codex working in Niners War Room Data Hygiene.

Task: Apply the explicitly approved NFLVerse player-context identity overlay to rebuild the tracked player context artifact, only if safe.

Inputs:
- `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_approved_overlay_v1.csv`
- `docs/hq/data_sources/nflverse_player_context_human_identity_review_20260630/human_identity_decision_review.csv`
- current tracked player context display artifact
- current identity hardening packet

Rules:
- Only overlay rows with `human_decision=APPROVE_REVIEW_ONLY` and `approved_by_human=true` may be considered.
- Bind approved identities to current NWR player rows without ambiguity before rebuilding any artifact.
- Do not accept name-only or fuzzy joins.
- Keep every applied row `review_only=true` and `display_only=true`.
- Keep model/training/source-truth/rank/hidden-sort/trade/pick flags false.
- Do not change app pages or model/rank/source-truth behavior.

Expected outputs:
- join-key validation report
- rebuilt player context artifact only if binding is safe
- guardrail report
- tests/checks proving no pending/rejected/blocked rows were applied
