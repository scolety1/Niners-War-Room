# Final UDFA Policy Pilot Recommendation

Verdict: `YELLOW`

## Decision

The UDFA issue is not fully fixed. This pilot found no row that satisfies the conservative `confirmed_udfa` standard using the currently approved/review-only artifacts.

## Counts

- likely UDFA rows reviewed: 2514
- confirmed UDFA candidates proposed: 0
- still blocked rows: 2514
- collision/name-risk rows routed away from clean likely status: 54
- free-agent/class-year ambiguity rows: 0
- source-policy-only likely review rows: 2460

## Modeling Status

- UDFA modeling may not proceed.
- Combined drafted + UDFA modeling may not proceed.
- Drafted-only Outcome review may proceed separately.
- No tuning, training, scoring, model output, app wiring, Gate F release, Gate G release, or Rankings wiring is approved.

## Remaining Blockers

1. No approved explicit historical UDFA/rookie-free-agent entry source.
2. Draft absence remains insufficient evidence.
3. NFL appearance/player_stats evidence remains candidate-only.
4. Identity collisions and missing NWR/CFBD bridges remain unresolved for many candidates.
5. Manual lookup policy and human approval workflow are not yet approved.

## Recommended Next Branch

`work/rookie-udfa-manual-evidence-review-workflow-v1-20260630`
