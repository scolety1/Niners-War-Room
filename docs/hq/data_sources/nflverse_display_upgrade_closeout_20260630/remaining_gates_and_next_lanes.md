# Remaining Gates And Next Lanes

## Recommended Next Lane

1. NFLVerse Player Context Human Identity Decision Review

Purpose: review the 54 pending identity rows and decide whether any recommendations
should be explicitly approved for review-only display.

Important: this next lane should not apply an overlay unless explicit human decisions
are provided. It should not set `approved_by_human=true` by inference.

## Later Lanes

2. Identity Apply Overlay Lane

Only after a human-reviewed decision sheet exists with explicit approvals. This lane may
produce a review-only approved overlay for rows marked `APPROVE_REVIEW_ONLY` and
`approved_by_human=true`.

3. Outcome / Rookie Outcome Feature Policy Gate

Only after the display wave is stable. This lane should classify NFLVerse context as
candidate features or blocked fields. It must not train, tune, or activate probabilities.

4. Injury / Availability Schedule Policy

Only if schedule fields are needed in Injury / Availability. This is riskier because
schedule context can imply health or availability. Default posture remains gated.

## Not Recommended Now

- New app display lanes, unless a specific bug is found.
- Model activation lanes.
- Rookie Gate G activation.
- UDFA modeling.
- Any market/ADP/DynastyProcess rank/model integration.
