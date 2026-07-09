# Age / Lifecycle Harm Review

Age/lifecycle creates useful review-only context, but it can create false confidence if used as a
direct ranking rule.

Main harm modes:

- Older elite producers can remain startable, so old age must not become an automatic penalty.
- Young players with no prior production can remain non-startable, so youth must not become an automatic boost.
- Position age curves differ; QB late-career windows behave differently than RB/WR/TE windows.
- Sparse-history and low-games rows can confound age buckets.
- Missing DOB/draft-year rows are small but must remain unknown rather than zero-filled.

Use-gate decision:

- Allowed: review-only component signal tests, guardrail context, formula-family design context.
- Blocked: production/model-use, formula weights, direct ranking inputs, hidden sort logic, exact replay,
  and Formula Gauntlet tournament clearance.
