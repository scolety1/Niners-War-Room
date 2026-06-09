# Rookie Research Overlay - 2026-05-22

## Purpose

This overlay preserves the latest rookie Deep Research reports as review-only context for the Draft Room rookie analyzer. It does not change private football value, pick baselines, active rankings, My Team, War Board, or readiness gates.

## Inputs

- `C:/Users/codex-agent/Downloads/deep-research-report (7).md`
- `C:/Users/codex-agent/Downloads/deep-research-report (8).md`
- user-pasted 2026 rookie-class research in the thread

## What Changed

Added review-only overlay CSVs:

- `local_exports/model_v4/rookie_research_overlay/latest/rookie_research_overlay_rows.csv`
- `local_exports/model_v4/rookie_research_overlay/latest/rookie_research_pick_fit_rows.csv`

These rows are visible in the Draft Room as external research context. They are explicitly blocked from private-value formula input and final pick recommendation use.

## Main Research Shape

The reports agree that the top of the class should be treated as a leverage zone, not a smooth ranking list:

- Jeremiyah Love is the cleanest anchor.
- Carnell Tate, Jordyn Tyson, Jadarian Price, and Makai Lemon are the main early-first decision cluster.
- QB and TE should slide in a 10-team 1QB no-TE-premium league unless price becomes favorable.
- Kenyon Sadiq is the TE exception, but still price-sensitive.
- Eli Stowers, Chris Bell, Ty Simpson, Mike Washington Jr., Chris Brazzell II, and Justin Joly are price-sensitive leverage names depending on pick range.

## Review Flags Created

The overlay intentionally surfaces conflicts rather than resolving them:

- Mike Washington Jr. has split research signals: athletic-hype warning versus RB arbitrage.
- Emmett Johnson has split signals: pasted report likes him; markdown reports are more cautious at price.
- Jonah Coleman is format-interesting but price-sensitive.
- Sadiq is a legitimate prospect but easy to overpay for in no-premium scoring.
- Mendoza is the best QB, but 1QB replacement depth caps urgency.

## Safety

Allowed use: `review_only_research_context_not_formula_input`

Blocked use: `do_not_use_as_private_value_or_final_pick_recommendation`

The research is a human-review layer. It can tell us where to scout harder or question the model, but it cannot silently become player evidence.
