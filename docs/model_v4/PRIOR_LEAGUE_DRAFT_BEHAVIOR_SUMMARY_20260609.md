# Prior League Draft Behavior Summary - 2026-06-09

## Outputs
- CSV: `local_exports/model_v4/draft_prep/latest/prior_league_draft_behavior_summary.csv`

## Summary
- Round 1 rows with usable player-type context are mixed, but the PDF rows often lack position/player-type evidence.
- First-round rookie rows counted from structured sheets: 9.
- First-round veteran/free-agent rows counted from structured sheets: 1.
- Total Round 1 context rows: 82.
- Low-confidence PDF transcription rows needing verification: 23.

## What history supports
- Draft Prep should show expected league range as context because prior sheets/PDFs are pick-order oriented.
- Historical behavior supports a mixed-pool mindset: rookies plus veterans/free agents, especially in early rounds.
- Position tendencies by round can be summarized when position exists, but older PDF rows need verification before strong claims.
- QBs/TEs should be visible as league-history context, not used to modify private value.

## 2025 product lesson
- The 2025 workbook is a better UI/product reference than the current audit cockpit.
- It naturally separates expected/mock board from a user-ranked review board and includes notes, cost, draft capital, age, and actual drafted-at context.
- Draft Prep should translate that into pick cards and candidate windows, not another raw rookie ranking table.

## Guardrail
- This summary is historical behavior context only and is blocked from private scoring.
