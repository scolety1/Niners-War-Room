# Next Binding Prompt

You are Codex working in Niners War Room Data Hygiene.

Task: Review the NFLVerse remaining-identity manual evidence packet and, only with explicit human approval decisions, prepare a review-only identity approval/binding lane.

Inputs:
- `docs/hq/data_sources/nflverse_remaining_identity_manual_evidence_review_20260630/manual_evidence_matrix.csv`
- `docs/hq/data_sources/nflverse_remaining_identity_manual_evidence_review_20260630/recommended_human_decision_sheet.csv`
- `docs/hq/data_sources/nflverse_remaining_identity_manual_evidence_review_20260630/binding_followup_candidates.csv`

Rules:
- Do not approve any row without explicit human approval evidence.
- Do not treat `RECOMMEND_APPROVE_REVIEW_ONLY_AFTER_HUMAN_CONFIRMATION` as approval.
- Do not treat `RECOMMEND_NWR_BINDING_REVIEW` as a safe join.
- Do not rebuild the player context artifact unless a later lane has explicit approved identities and safe NWR bindings.
- Keep model/training/source-truth/rank/hidden-sort/trade/pick flags false.
- Missing identity data remains `Not enough information`.

Expected starting points:
- Kentrel Bullock and Jamal Haynes need NWR binding review.
- Chip Trayanum may be considered for future explicit review-only approval after human confirmation.
- The other rows need more identity evidence or stay blocked.
