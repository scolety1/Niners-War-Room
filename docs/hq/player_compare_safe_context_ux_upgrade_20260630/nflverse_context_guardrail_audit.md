# Player Compare NFLVerse Context Guardrail Audit

Date: 2026-06-30

## Source Controls

- Player Compare reads only tracked repo artifacts from
  `docs/hq/data_sources/nflverse_player_context_display_20260630/`.
- Player Compare joins only by `nwr_player_id`.
- Player-level context displays only for rows where
  `identity_join_status=SAFE_NOW_DISPLAY_ONLY` and `review_required=false`.
- Every displayed field must be `SAFE_NOW_DISPLAY_ONLY` in the schema manifest.
- Schema manifest flags must keep model, training, source truth, rank logic,
  hidden sort, trade value, and pick value usage set to false.

## Identity Controls

- `NEED_IDENTITY_REVIEW` rows display only `Needs identity review`.
- Detailed NFLVerse context fields are suppressed for identity-review rows.
- Identity proposal rows are not consumed because they are proposals only.

## Missing Data Controls

- Missing values display as `Not enough information`.
- Missing injury is not healthy.
- Missing depth is not no-role.
- Missing snaps is not zero.
- Missing draft capital is not confirmed UDFA.
- Missing data is not treated as safe, clean, bad, or neutral.

## Explicit Non-Use

This pass does not add or change:

- model score
- hidden sort
- player recommendation logic
- better-player verdict
- market/ADP/DynastyProcess decision logic
- injury-risk score
- medical projection
- comeback projection
- trade valuation
- pick valuation
- Dynasty Rank / Final Board Rank / Candidate Rank
- tiers
- Frozen Final Draft Board V1
- latest_candidate/latest_approved
- model/rank/source-truth gates
- Live Draft / Mock Draft behavior

## Schedule Context

- Next game / opponent / bye context is display-only for safe rows only.
- The same identity, schema, model, source-truth, rank, hidden-sort, trade
  value, and pick value guards apply to schedule fields.
- Missing schedule context remains `Not enough information`.

## Deferred

- `ff_rankings` remains blocked by source policy.
- Identity proposal rows remain manual review only.

## Verdict

`GREEN_PLAYER_COMPARE_NFLVERSE_CONTEXT_READY`

The activated context is factual, display-only, and review-safe for Player
Compare.
