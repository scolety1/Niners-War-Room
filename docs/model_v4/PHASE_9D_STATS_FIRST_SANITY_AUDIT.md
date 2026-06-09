# Phase 9D Stats-First Sanity Audit

## Summary

- Audit rows: 74
- Layer players: 1390
- Component evidence rows: 33442
- Unavailable rows: 2742
- Source warning rows: 238
- Issue counts: {"formula_context_needed": 6, "no_issue": 18, "source_limitation": 50}

## Guardrails

- Overall guardrail status: passes
- Projection rows used for core value: 0
- Route metrics used: False
- Market value used: False
- League rank used: False
- Active rankings overwritten: False

## Deep-History Check

- Top deep-history-only audit row: Tom Brady (5.2502, deep_history_only_not_boosted)

Deep-history-only players are not treated as current assets if their latest evidence ends in 2022 or earlier and their value remains below the review threshold of 15.0.

## Interpretation

- This is a stats-evidence layer, not a final dynasty ranking.
- High QB rows are expected here; the final v4 formula still has to apply 10-team 1QB suppression.
- Route metrics remain unavailable unless a licensed structured source is added.
- 2026 imported projections are comparison-only and do not drive this layer.
- Market value and league-rank rule context do not drive this layer.
- Component evidence rows may show per-season deep-history evidence, while player rows collapse 2022-and-older evidence into one deep-history bucket.

## Review Rows

| Group | Player | Issue | Finding | Next action |
| --- | --- | --- | --- | --- |
| qb_controls | Josh Allen | formula_context_needed | QB historical production can score highly in this evidence layer. | Final v4 formula must apply 10-team 1QB positional suppression and receipts. |
| qb_controls | Lamar Jackson | formula_context_needed | QB historical production can score highly in this evidence layer. | Final v4 formula must apply 10-team 1QB positional suppression and receipts. |
| qb_controls | Jalen Hurts | formula_context_needed | QB historical production can score highly in this evidence layer. | Final v4 formula must apply 10-team 1QB positional suppression and receipts. |
| qb_controls | Patrick Mahomes | formula_context_needed | QB historical production can score highly in this evidence layer. | Final v4 formula must apply 10-team 1QB positional suppression and receipts. |
| qb_controls | Jared Goff | formula_context_needed | QB historical production can score highly in this evidence layer. | Final v4 formula must apply 10-team 1QB positional suppression and receipts. |
| qb_controls | Matthew Stafford | formula_context_needed | QB historical production can score highly in this evidence layer. | Final v4 formula must apply 10-team 1QB positional suppression and receipts. |
