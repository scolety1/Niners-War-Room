# Model v4 Role Archetype Master Review V1 Report

## Verdict

`GREEN_ROLE_ARCHETYPE_ADMITTED_FOR_REVIEW_GUARDRAIL_CONTEXT`

## Clear Answer

Role archetype receipts are admitted for review-only component signal tests, miss taxonomy, guardrail context, and future Formula Gauntlet slice reporting after Formula Gauntlet is otherwise cleared. They are not admitted for formula weights, ranking inputs, exact Model v4 replay, production/model-use, hidden sort logic, source promotion, or production accuracy claims.

## Evidence Reviewed

- Role Archetype Receipt Regeneration Pilot V1 at commit `0462aaa4e01f1939afd1b63dc5fe55bdd4db68fc`
- Role Archetype Component Signal Test V1 at commit `5247d6f0c9bd9396c276553ced5289ef06bda773`
- Confidence Cap Component Signal Test V1 at commit `b548776c4343b7bd38cb63f84b51b0334fd8b352`
- Historical Receipt Regeneration Contract Planning V1 at commit `b2eb09a78a00f86f154a74cd0d40adaf28948aa2`
- Batch Canonicalization Review V1 at commit `c90661778e0513e988b8a593045609d4433059c9`

## Compliance Review

The role-archetype regeneration pilot complied with the approved one-family contract:

- regenerated only `role_archetype_receipts`
- wrote only to a review artifact path
- preserved review-only status
- used lagged prior-season context only
- used no future role, target outcome, current ADP, depth chart, or production ranking input
- produced `5,518` rows for `2013-2025`
- covered QB/RB/WR/TE
- duplicate keys: `0`
- leakage/as-of validation: pass
- identity/missingness validation: pass
- no source promotion
- no production/model-use claim

## Signal Review

The component signal test found useful review-only context:

- High-volume archetypes contained `468 / 572` PYF false positives, or `81.8%`.
- Low/sparse archetypes flagged `54 / 353` PYF false negatives, or `15.3%`.
- Sparse-history rows: `1,453`.
- Sparse-history startable rate: `3.3%`.
- Strong large-bucket rates included `wr_high_volume_target_volume=53.0%`, `rb_high_volume_touch_volume=47.9%`, and `qb_high_volume_passing_volume=41.2%`.
- Weak large-bucket rates included `te_sparse_history_low_games=1.2%`, `rb_low_volume_touch_volume=1.5%`, and `wr_low_volume_target_volume=1.6%`.

These findings make role archetypes useful for review-only miss taxonomy and guardrail reporting. They do not make them a model score.

## Admission Decision

Allowed:

- `EVIDENCE_ONLY`
- `REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`
- `REVIEW_ONLY_MISS_TAXONOMY`
- `REVIEW_ONLY_GUARDRAIL_CONTEXT`
- `REVIEW_ONLY_FORMULA_GAUNTLET_SLICE_REPORTING`

Not allowed:

- `REVIEW_ONLY_PARTIAL_REPLAY_SUPPORT`
- formula weights
- production/model-use
- ranking inputs
- hidden sort logic
- player-level confidence score
- exact Model v4 replay clearance

## System Clearance Impact

This review does not change overall system gates. Exact Model v4 replay remains blocked. Formula Gauntlet tournaments remain blocked. 100-candidate Gauntlet remains blocked. Champion refinement remains blocked. Rankings integration remains blocked. Production/model-use remains blocked.

## Recommendation

Recommended next action: `stop and batch canonicalization`.

The next execution lane should not be another test by default. First preserve this local review packet and the two preceding role-archetype packets in the next controlled canonicalization batch.
