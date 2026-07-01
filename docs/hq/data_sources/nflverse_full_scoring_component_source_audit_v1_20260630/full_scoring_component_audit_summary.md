# Full Scoring Component Audit Summary

Verdict: `YELLOW_FULL_SCORING_COMPONENT_SOURCE_AUDIT_BLOCKED_FIELD_OR_ZERO_GAPS`

## Executive Summary

The admitted NFLVerse `player_stats` source contains most raw scoring columns needed by NWR 1QB non-PPR first-down scoring, and those raw columns are review-allowed in the row-level source-admission schema. The prior compact sidecar is still insufficient for full parity because it intentionally emits only nonzero first-down component rows.

A future full scoring sidecar builder is partially unblocked at the field level for observed NFLVerse player-week rows. It is not fully unblocked for Outcome parity because missing player-week rows cannot be blindly converted to zero, and special/return touchdown mapping needs an explicit source-alignment rule before recomputing full scores.

## Source Facts

- Admitted weekly source: `player_stats_weekly`
- Weekly rows: `76804`
- Weekly SHA: `a38c47ea830e6929e8de31d822496862d13873d13689ff90d2e50dac854901ba`
- Admitted seasonal source: `player_stats_seasonal`
- Seasonal rows: `42419`
- Seasonal SHA: `57f76cfeee3211885f6d05504cc61b6529d023d5eb15a60ae21cc81c21c07b59`
- Source seasons: `2024-2025`
- Source weeks: `1-22`
- Existing compact sidecar rows: `13628`
- Existing compact sidecar fields: `passing_first_downs`, `rushing_first_downs`, `receiving_first_downs`

## Decision

Field coverage is strong enough to design a future observed-row full component sidecar builder, but this audit does not approve full scoring parity yet. The next builder must:

- emit all required scoring components for source-observed player-week rows;
- include explicit zero component rows only when the source row exists and the component value is explicitly numeric zero;
- never infer a missing source row as zero production;
- exclude quarantined fields;
- keep all label truth, model, training, and source-truth flags false;
- document special/return touchdown mapping before any full score recompute.

## Approval Boundary

`label_truth_allowed=false`, `model_use_allowed=false`, `training_allowed=false`, and `source_truth_allowed=false` remain closed for every audited component.
