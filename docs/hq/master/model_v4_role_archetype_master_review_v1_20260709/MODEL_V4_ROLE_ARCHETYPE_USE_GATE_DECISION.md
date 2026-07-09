# Model v4 Role Archetype Use-Gate Decision

## Maximum Allowed Use

`REVIEW_ONLY_GUARDRAIL_CONTEXT`

## Allowed Uses

- Evidence-only reference
- Review-only component signal tests
- Review-only miss taxonomy
- Review-only sparse-history and low-games guardrail context
- Review-only PYF false-positive / false-negative analysis
- Future Formula Gauntlet slice reporting after Formula Gauntlet is otherwise cleared by Master HQ

## Blocked Uses

- Formula weights
- Direct ranking boosts
- Direct ranking penalties
- Production model input
- Hidden sort logic
- Recommendation logic
- Player-level confidence score
- Exact Model v4 replay support
- Production approval
- Source promotion

## Decision

Role archetypes may travel forward as labeled review slices and guardrail context only. Any future use must keep PYF as the anchor baseline and report sparse-history, low-games, prior-decline, breakout, and collapse harm cases.
