# NFLVerse Player Context Identity Review Methodology

This methodology classifies the 54 current `NEED_IDENTITY_REVIEW` player-context rows without approving any identity for model, training, source-truth, rank, hidden-sort, trade, or pick-value use.

## Evidence Dimensions

Each row is reviewed using tracked evidence where available:

- stable player ID
- player name and normalized player name
- position
- team
- season/year or timeline context
- draft year / draft team if available
- roster timeline if available
- college / school if already available in tracked artifacts
- Sleeper/NWR/NFL/GSIS/PFR IDs where available
- duplicate/same-name risk
- wrong-position risk
- wrong-team/timeline risk
- many-to-one or one-to-many ID risk

## Conservative Rules

- Unique stable ID evidence beats name-only evidence.
- Name-only evidence is never enough for an approval recommendation when ambiguity exists.
- Position mismatch requires block or human review.
- Team/timeline mismatch requires block or human review.
- Many-to-one or one-to-many joins require block or human review.
- Missing source data stays `Not enough information`.
- `approved_by_human=false` for every row in this lane.
- `review_only=true`, `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false` for every row.

## Decision Meanings

- `RECOMMEND_APPROVE_REVIEW_ONLY`: tracked review artifacts found a unique local identity candidate, but a human must still accept or reject the recommendation before any active artifact is rewritten.
- `RECOMMEND_KEEP_BLOCKED`: no exact approved local identity candidate is available in tracked artifacts.
- `RECOMMEND_REJECT_WRONG_IDENTITY`: candidate evidence indicates the proposed identity is wrong.
- `RECOMMEND_NEEDS_MORE_INFO`: available evidence is too thin to classify safely.
- `RECOMMEND_HUMAN_REVIEW`: candidate evidence exists, but team/timeline/source evidence is incomplete or ambiguous.
