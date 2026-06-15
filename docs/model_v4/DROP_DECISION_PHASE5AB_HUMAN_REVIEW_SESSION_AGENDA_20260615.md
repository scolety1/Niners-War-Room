# Drop Decision Phase 5AB Human Review Session Agenda - 2026-06-15

## Purpose

This agenda prepares Main HQ for a human review session using the committed Phase 5A artifacts. It is discussion-only context. It does not create, imply, or authorize a final drop, cut, keep, trade, or draft recommendation.

Phase 5B recommendation-mode remains closed.

## Session Rules

- Use artifacts as receipts and question prompts only.
- Keep the Decision Board open as human-review context, not as an action list.
- Do not sort or rank drop candidates during this session.
- Do not ask Codex to name the final drop, cut, keep, trade, or draft decision.
- Do not create probabilities, outcome bands, app-readable recommendation outputs, or promoted artifacts.
- Keep `data/` and `local_exports/` local-only and uncommitted.

## Artifacts To Open

Use the committed handoff first:

- `docs/model_v4/DROP_DECISION_PHASE5A_HUMAN_REVIEW_READY_HANDOFF_20260615.md`

Then inspect local review artifacts by category:

| Category | Artifact | Rows | Session use |
|---|---|---:|---|
| Decision context | `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv` | 105 | Review questions, sources, and next-review steps. |
| Prep summary | `local_exports/model_v4/human_decision_review_prep/latest/human_decision_review_summary.csv` | 14 | Confirm review packet shape and output counts. |
| Pick context | `local_exports/model_v4/human_decision_review_prep/latest/pick_review_cards.csv` | 5 | Discuss pick-context questions only. |
| Roster pressure | `local_exports/model_v4/human_decision_review_prep/latest/roster_pressure_review_cards.csv` | 24 | Discuss pressure evidence only. |
| External context | `local_exports/model_v4/human_decision_review_prep/latest/trade_review_cards.csv` | 26 | Discuss external/trade context without trade calls. |
| Rookie scouting | `local_exports/model_v4/human_decision_review_prep/latest/rookie_manual_scout_queue.csv` | 94 | Identify manual scouting questions only. |
| Veteran risk | `local_exports/model_v4/human_decision_review_prep/latest/veteran_risk_review_cards.csv` | 30 | Inspect veteran risk questions only. |
| Opportunity cost | `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv` | 24 | Discuss opportunity-cost context without drop guidance. |
| Age caveat | `local_exports/model_v4/prospect_age/latest/player_age_2026.csv` | 275 | Keep age provenance visible; do not recalculate. |

## Manual Questions For Main HQ

Use these as neutral discussion prompts:

- Which artifact rows need source receipt inspection before any later decision-support step?
- Which rows have warning flags that require human context or source review?
- Are any review cards missing enough context that they should be excluded from later recommendation-mode consideration?
- Are pick-context questions, roster-pressure questions, and opportunity-cost questions internally consistent?
- Are rookie/manual scouting caveats sufficiently visible before any later Phase 5B discussion?
- Are external asset context rows being treated as context only, with no buy/sell instruction?
- Are veteran-risk rows being treated as questions only, with no release instruction?
- Does any artifact conflict with Main HQ's known league rules, roster constraints, or manual notes?

## Caveats To Keep Visible

- The age source is user/source-provided as of June 4, 2026.
- Age values are source-provided age strings, not DOB-derived values.
- Do not recalculate ages to today.
- Do not use DOBs, public rankings, projections, ADP, trade calculators, RotoWire values/outlooks/rankings/projections, external sources, or same-season final stats to alter the age artifact.
- Age coverage is partial against prospect value rows.
- Review-band fields are human-review labels only, not outcome bands or recommendation outputs.
- Local artifacts in `local_exports/` are ignored local review artifacts, not committed/promoted outputs.

## If Artifacts Conflict

When artifacts disagree or appear incomplete:

1. Pause the review item.
2. Identify the exact artifact path and row key involved.
3. Check the receipt pointer, source path, allowed use, blocked use, and warning flags.
4. Ask Codex for a metadata-only provenance audit of the conflicting row or artifact.
5. Do not ask for a recommendation or ranking until Main HQ separately authorizes a later mode.

## Safe Follow-Up Prompts

If a data issue appears, Main HQ can ask:

```text
Audit this Phase 5A artifact row for schema, provenance, allowed_use, blocked_use, receipt pointer, and warning flags only. Do not rank candidates, create recommendations, probabilities, bands, or final/implied drop guidance.
```

If a refresh is needed, Main HQ can ask:

```text
Run a Phase 5A metadata-only refresh/validation for the affected artifact. Restore tracked docs drift. Do not commit, push, deploy, promote artifacts, or create recommendation outputs.
```

## Closeout

At the end of the session, Main HQ should decide only whether to:

- stay Phase 5A-only,
- request a Phase 5B plan-only prompt, or
- separately authorize a future Phase 5B decision-support run with explicit gates.

This agenda produces no final or implied drop recommendation.
