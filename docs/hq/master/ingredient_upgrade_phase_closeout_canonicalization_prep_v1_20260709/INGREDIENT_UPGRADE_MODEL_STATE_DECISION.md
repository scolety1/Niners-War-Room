# Ingredient Upgrade Model State Decision

## Decision

The current NWR review-only formula and ingredient phase is closed.

## Answers

- Review-only ranking simulation justified: no
- Production/model-use justified: no
- Rankings integration justified: no
- More same-ingredient formula tuning justified: no
- Another data lane justified immediately: no, not without user review
- Canonicalization before more model work: yes

## Rationale

The best full-history result is `0.758`, only about `+0.003` over the prior `0.755` review-only plateau. The best broad-window result is `0.763`, but it is a 2014-2025 subset and remains review-only. The best partial-window result is `0.790`, but it is limited to 2022-2025 and cannot be used as a full-history plateau claim.

The phase found useful context and several guardrails, but no candidate is approved as a production formula, direct ranking input, hidden sort, recommendation rule, or rankings integration path.

## Current Allowed Use

- Review-only evidence and diagnostics
- Review-only ingredient status tracking
- Review-only future design input
- Guardrail and context interpretation
- Canonicalization planning

## Current Blocked Use

- Production/model-use
- Rankings integration
- App/runtime behavior changes
- Direct ranking boosts or penalties
- Hidden sort logic
- Recommendation logic
- Review-only ranking simulation without explicit future approval
- More same-ingredient formula tuning
