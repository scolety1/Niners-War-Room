# User Judgment Worksheet

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: provide a tomorrow worksheet for human judgment. This is a manual review artifact. It is not a model output, not a final ranking, not a formula tuning packet, and not a trade, cut, keep, draft, buy, sell, defer, target, or start/sit recommendation.

Use this worksheet to write down what the model showed, what warnings were
visible, what your football prior was before accepting the model's view, whether
you agree or disagree, and what risk you would attach to any real-money or
league-impact action.

CSV worksheet:

- `docs/model_v4/USER_JUDGMENT_WORKSHEET_20260605.csv`

## How To Use

1. Open the app or the source report for the row.
2. Read the model value, source report, warning context, and risk note.
3. Fill in `human_prior_before_model` before letting the model change your mind.
4. Fill in `agreement_with_model` as agree, disagree, partial, or unsure.
5. Fill in `disagreement_reason` when your football prior differs.
6. Fill in `final_human_decision` only after you decide. This field is yours,
   not the model's.
7. Fill in `follow_up_notes` with source, scouting, league context, or audit
   questions.

## Worksheet Columns

| Column | Meaning |
|---|---|
| `worksheet_id` | Stable row id for tomorrow review. |
| `review_group` | Why the row is included. |
| `subject_type` | Current player, rookie, pick, external asset, or sentinel. |
| `subject` | Player, pick, or surface under review. |
| `position` | Position where applicable. |
| `surface` | Primary app/report surface to inspect. |
| `model_says` | Evidence-only summary of the model context. |
| `source_report` | Report that supports the row. |
| `warning_context` | Warning or guardrail to keep visible. |
| `money_action_risk` | Why this row is risky for real decisions. |
| `human_prior_before_model` | Blank field for your prior. |
| `agreement_with_model` | Blank field for agree/disagree/partial/unsure. |
| `disagreement_reason` | Blank field for your reasoning. |
| `final_human_decision` | Blank field for your actual decision, if any. |
| `follow_up_notes` | Blank field for audit or scouting notes. |

## Included Review Groups

- Source-safety sentinels.
- Blank primary-score rows.
- QB 1QB context.
- TE no-premium context.
- RB/WR balance prompts.
- Veteran age/status prompts.
- Young-player evidence prompts.
- Rookie board and watchlist prompts.
- Pick-neighborhood prompts.
- External Asset and Decision Board framing prompts.

## Guardrails

- Do not tune formulas from this worksheet.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not import market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic into private value.
- Do not mutate generated outputs, active rankings, My Team, War Board,
  readiness gates, app promotion, active data packs, or user-entered draft
  state.
- Do not treat any row as a final recommendation.
- Market, ADP, rankings, projections, consensus, startup, and external context
  stay display-only.

## Suggested Review Order

1. Source-safety sentinels and blank primary-score rows.
2. `2026 5.04` manual-only pick handling.
3. QB and TE format-context rows.
4. RB/WR and veteran/age rows.
5. Young-player and rookie-source rows.
6. Pick-neighborhood and External Asset/Decision Board framing rows.
7. Formula candidates only as proposal-only notes after the above are complete.
