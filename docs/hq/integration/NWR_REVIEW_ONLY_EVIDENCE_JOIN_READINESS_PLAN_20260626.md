# NWR Review-Only Evidence Join Readiness Plan

Date: 2026-06-26

Verdict: GREEN

## Purpose

This plan defines how CFBD, NFL Usage, Unified Universe, and supporting evidence lanes may eventually relate to each other without integrating them into rankings, Drafting Mode, Player Compare, Trading Lab, or model features now.

Created artifacts:

- `docs/hq/integration/evidence_join_readiness_matrix_v1_20260626.csv`
- `docs/hq/integration/evidence_integration_backlog_v1_20260626.csv`

## Current Decision

No decision-page evidence integration is allowed now.

Allowed now:

- Unified Universe Review remains an inspection surface.
- NFL Usage Evidence Review remains an inspection surface.
- Evidence Integration Review summarizes committed registry status.
- Settings/Data Health may later summarize status, not player decision evidence.
- Model Evaluation Harness may later evaluate evidence buckets, not tune ranks.

Blocked now:

- Dynasty Rankings evidence integration.
- Drafting Mode evidence integration.
- Player Compare evidence integration.
- Trading Lab evidence integration.
- Production model input.
- Training use.
- Hidden sorting from evidence fields.

## Surface-Level Findings

| Surface | Status | Reason |
| --- | --- | --- |
| Unified Universe Review | Future review-only join candidate | Identity and age blockers remain. |
| NFL Usage Evidence Review | Already safe as separate review surface | It reads committed summaries only. |
| Evidence Integration Review | Safe as status summary | It reads the registry, not raw player evidence. |
| Settings/Data Health | Future status summary candidate | Should show health, not decision evidence. |
| Dynasty Rankings | Blocked | Full dynasty behavior must remain stable; unified wiring not approved. |
| Drafting Mode | Blocked | On-clock decisions must not consume review-only evidence. |
| Player Compare | Blocked | Decision summary must not use unapproved evidence. |
| Trading Lab | Blocked | Trade decisions must not use unapproved usage/CFBD evidence. |
| Model Evaluation Harness | Future evaluation candidate | No active model feature consumption. |

## Evidence-Lane Rules

- CFBD remains review-only until human approval.
- NFL Usage model-candidate language does not mean active model input.
- Unified Universe app-wiring remains blocked.
- Proxy/LOW historical evidence remains sensitivity-only.
- True routes, TPRR, and YPRR remain licensed-data gaps unless a safe source is approved.
- RotoWire live collection remains blocked.

## Recommended Next Gates

1. CFBD human review gate.
2. Unified Universe source-quality gate.
3. NFL Usage model integration gate.
4. Evidence review-page UI gate.
5. Settings/Data Health status-summary gate.

## Phase 4 Result

Phase 4 is GREEN if the matrix and backlog validate and continue to keep all decision-page wiring and model input disabled.
