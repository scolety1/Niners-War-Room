# Rookie Historical Opportunity Feature Gauntlet V1

Verdict: `GREEN_NWR_ROOKIE_FEATURE_GAUNTLET_COMPLETE_NO_FAMILY_PROMOTED`

This is `RESEARCH_ONLY_NOT_CANONICAL_NOT_PRODUCTION`. It neither tunes Model V4 nor scores/reranks 2026.

## Coverage

- Exact governed drafted identities: 1115
- Research rows: 1115
- Draft classes: 2012–2025
- Positions: QB|RB|TE|WR
- Sources: immutable CFBD REST v2 and nflverse draft, players, weekly stats, and combine feasibility receipt

## Decisions

- T01 QB: `RETAIN_FEATURE_FAMILY_REVIEW_ONLY`
- T02 RB: `REJECT_FEATURE_FAMILY_NOT_INCREMENTAL`
- T03 WR: `REJECT_FEATURE_FAMILY_NOT_INCREMENTAL`
- T04 TE: `REJECT_FEATURE_FAMILY_NOT_INCREMENTAL`
- T05 QB|RB|WR|TE: `BLOCK_FEATURE_FAMILY_SOURCE_OR_IDENTITY`
- T06 QB: `REJECT_FEATURE_FAMILY_NOT_INCREMENTAL`
- T06 RB: `REJECT_FEATURE_FAMILY_NOT_INCREMENTAL`
- T06 WR: `REJECT_FEATURE_FAMILY_NOT_INCREMENTAL`
- T06 TE: `REJECT_FEATURE_FAMILY_NOT_INCREMENTAL`
- T07 QB: `BLOCK_FEATURE_FAMILY_SOURCE_OR_IDENTITY`
- T09 WR: `BLOCK_FEATURE_FAMILY_SOURCE_OR_IDENTITY`

T01 is lower-fidelity and cannot pass its full gate. T05, T07, and T09 stop at
the source/semantic gate. Every modeled comparison uses earlier-class fitting,
training-only normalization, explicit missingness, and identical test rows.
Promotion, if any, authorizes only a later model gauntlet—not a formula change.
