# Medium Formula Pilot Stop Conditions

The future medium pilot must stop if:

- The review-only Formula Data Mart cannot be assembled.
- The PYF baseline cannot be reproduced.
- Candidate count differs from the contract.
- Candidate definitions drift after results are seen.
- Leakage/as-of checks fail.
- Source/use-gate status is ambiguous or blocked.
- Required candidate fields are missing and no predeclared fallback exists.
- Formulas require blocked inputs.
- Metrics cannot be calculated consistently.
- Outputs imply production use, ranking integration, source promotion, or production accuracy.
- Role archetype becomes a formula weight, direct boost, direct penalty, hidden sort, or ranking input.
- Age/lifecycle becomes a formula weight, direct boost, direct penalty, hidden sort, or ranking input.
- Confidence cap becomes a player confidence score or formula feature.
- PFR, red zone, injury, market, route, return, or current/future context is used outside explicitly allowed review-safe scope.

If any stop condition is triggered, the future lane must report the blocker and preserve all current gates.
