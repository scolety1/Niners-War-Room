# Guardrail Summary

Verdict: `GREEN_REVIEW_ONLY_HUB_GUARDRAILS`

## Confirmed

- No production formula changes.
- No model training or tuning.
- No normal app default behavior changes.
- No ranking logic changes.
- No hidden sort.
- No source-truth promotion.
- No production config changes.
- No runtime behavior changes outside the clearly labeled review-only hub UI.
- No candidate formula output is wired into normal rankings, draft, trade, or player-compare behavior.
- No raw/shared/cache/local export/secrets files are tracked.

## Blocked Fields

- Routes
- TPRR
- YPRR
- Ambiguous `rz_att`
- Unapproved joins
- Current-only context as historical formula input

## Null-Fenced Features

Source Contract V1 keeps null-fenced fields explicit. Missing data remains missing and is not converted into zero, role, priority, or action.

## Hub Policy

Evidence Review Hub is a status/navigation page only. It can link evidence together for review, but it cannot promote evidence, approve shadow review, or change normal product behavior.
