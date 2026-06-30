# Rookie Outcome UDFA Handoff Update

This pilot reviewed 2514 `likely_udfa_needs_review` rows from the entry-status hygiene packet.

## What Rookie Outcome May Do

- Continue drafted-only Outcome review.
- Use this packet for blocker reporting and source-policy planning.
- Use `confirmed_udfa_patch_proposal.csv` only as a review-only proposal artifact.

## What Rookie Outcome May Not Do

- Treat `likely_udfa_needs_review` as clean UDFA.
- Train on UDFAs or combined drafted/UDFA populations.
- Treat `confirmed_udfa_candidate` as training-approved or model-approved.
- Set `model_use_allowed=true` or `training_allowed=true`.
- Wire Gate F, Gate G, Rankings, Live Draft Room, or current-player rookie outcome columns.

## Status After This Lane

- `likely_udfa_needs_review` remains blocked unless promoted later by approved policy and human review.
- `confirmed_udfa_candidate` rows are not training-approved.
- `confirmed_udfa` remains not model-approved unless a later approval gate explicitly changes model-use and training flags.
- Combined drafted + UDFA modeling remains blocked unless a future gate approves it.
- Gate F/G/Rankings wiring remains blocked.
