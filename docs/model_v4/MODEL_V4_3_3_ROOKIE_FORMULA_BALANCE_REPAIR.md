# Model v4.3.3 Rookie Formula Balance Repair

Date: 2026-05-25

## Goal

Repair rookie formula balance without tuning to consensus rankings. The board may
remain weird when the evidence supports a real edge, but source-shape errors
should be visible and constrained.

## What Changed

The Sprint 12/13 prospect value layer now applies explicit review-only football
guardrails after the component score is calculated:

- first-round draft-capital anchor
- day-three skepticism unless production/athletic evidence is exceptional
- no-premium TE cap
- 1QB QB scarcity cap for non-premium QB profiles
- visible explanation labels for weirdness and source warnings

The model still uses admitted evidence only:

- college production
- college team share
- factual NFL draft capital
- workout/athletic prior
- recruiting prior
- age lifecycle
- confidence cap

It still blocks market, ADP, ranking, mock draft, big-board, and projection data
from private football value.

## Guardrail Labels

| Label | Meaning | Allowed use |
|---|---|---|
| `model_edge_weirdness` | The model is intentionally allowing a non-consensus edge because production/athletic evidence is exceptional. | Human review |
| `source_shape_warning` | Missing or shape-limited source data may be distorting the score. | Human caution |
| `draft_capital_anchor_warning` | Draft capital constrained an otherwise distorted production-driven score. | Human review |
| `no_premium_te_cap_warning` | TE value was capped because the league has no TE premium. | Human review |

## Design Principles

This is not a consensus-tuning patch. The model does not attempt to match Mike
Clay, ADP, RotoWire ranks, or any public board. The patch only encodes football
priors that are independent of rankings:

- NFL draft capital is real team-investment evidence.
- Day-three players need unusually strong evidence to beat first-round profiles.
- TEs need extra discipline in a no-premium format.
- QBs need extra discipline in a 10-team 1QB format.
- Missing evidence creates warnings, not fake zeros.

## Named Sanity Review

| Player | Result |
|---|---|
| Jeremiyah Love | Remains the top RB/overall rookie profile. |
| Carnell Tate | Receives a first-round draft-capital anchor because college team-share data is unusually weak. |
| Jordyn Tyson | Remains strong on production/share/draft capital, with missing athletic evidence visible. |
| Makai Lemon | Remains high because the evidence stack is broadly strong. |
| KC Concepcion | Draft-capital alias now resolves through the admitted normalized player name. |
| Omar Cooper | Retains first-round/late-first draft-capital evidence but weak share context remains visible. |
| Jadarian Price | Retains late-first draft-capital evidence; missing athletic component remains visible. |
| Kenyon Sadiq | First-round TE capital is admitted, but no-premium TE discipline remains. |
| Denzel Boston | Second-round capital and production evidence remain visible. |
| Skyler Bell | Still ranks unusually high, but now explicitly carries `model_edge_weirdness` because his day-three profile is allowed only as an exceptional-production case. |
| Eli Stowers | Capped by no-premium TE discipline. |
| Max Klare | Capped by no-premium TE discipline. |
| Fernando Mendoza | Preserves QB1 draft-capital evidence, but 1QB format still limits how much QB value can dominate. |

## Outputs Regenerated

- `local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv`
- `local_exports/model_v4/prospect_value/latest/prospect_value_component_rows.csv`
- `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- `local_exports/model_v4/rookie_draft_review/latest/rookie_pick_candidate_review_rows.csv`
- `local_exports/model_v4/june15_decision_board/latest/june15_decision_board_review_rows.csv`

## Review-Only Status

No active rankings changed. My Team, War Board, readiness gates, and app
promotion remain unchanged.
