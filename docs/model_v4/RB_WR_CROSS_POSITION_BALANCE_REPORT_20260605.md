# RB/WR Cross-Position Balance Report

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: compare RB and WR current-player checkpoint distributions before any
formula work. This report is evidence only. It does not tune RB/WR balance,
change formulas, change generated outputs, or make trade, cut, keep, draft,
buy, sell, defer, target, or start/sit recommendations.

## Source

- Source path:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
- Score column: `checkpoint_review_score`
- Lineage: `review_v4_current_player`
- Allowed use: `review_only_current_value_checkpoint`
- Blocked use: `do_not_use_as_final_ranking_or_roster_recommendation`

## Distribution Summary

| Position | Rows | Numeric Scores | Blank Scores | Max | Min | Mean | Median | Top 10 Overall | Top 25 Overall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RB | 19 | 18 | 1 | 82.8329 | 3.0698 | 53.6926 | 59.6777 | 4 | 11 |
| WR | 41 | 39 | 2 | 83.0486 | 16.2148 | 41.3714 | 32.3993 | 4 | 9 |

## Score Bands

| Position | 80+ | 60-79.99 | 40-59.99 | 20-39.99 | Under 20 | Blank |
|---|---:|---:|---:|---:|---:|---:|
| RB | 2 | 7 | 5 | 2 | 2 | 1 |
| WR | 2 | 3 | 11 | 22 | 1 | 2 |

## Warning Rates

| Position | Capped Review Required | Identity/Team Warnings | RB Age Warnings | Low-Evidence Warnings | Partial/First-Down Warnings |
|---|---:|---:|---:|---:|---:|
| RB | 8 | 3 | 8 | 4 | 7 |
| WR | 18 | 11 | 0 | 5 | 18 |

## Top RB Examples

| File Row | Player | Score | Confidence Cap | Confidence Status | Review Notes |
|---:|---|---:|---:|---|---|
| 3 | Christian McCaffrey | 82.8329 | 0.88 | usable_with_confidence_cap | Top RB; RB age-cliff warning. |
| 4 | Jonathan Taylor | 80.1465 | 0.88 | usable_with_confidence_cap | Top RB; RB age-window warning. |
| 5 | Bijan Robinson | 79.9939 | 0.88 | usable_with_confidence_cap | Young RB anchor. |
| 7 | Jahmyr Gibbs | 73.9972 | 0.88 | usable_with_confidence_cap | Young RB anchor. |
| 12 | De'Von Achane | 66.6696 | 0.88 | usable_with_confidence_cap | High-score RB with source-review warnings. |
| 9 | Derrick Henry | 66.2156 | 0.88 | usable_with_confidence_cap | Aging RB with age-cliff warning. |
| 11 | James Cook | 63.7724 | 0.88 | usable_with_confidence_cap | Top-25 RB/WR balance check. |
| 13 | Kyren Williams | 61.1255 | 0.82 | capped_review_required | Capped review required. |
| 14 | Saquon Barkley | 60.8166 | 0.88 | usable_with_confidence_cap | Aging RB with age-cliff warning. |
| 17 | Josh Jacobs | 58.5387 | 0.88 | usable_with_confidence_cap | RB age-window warning. |

## Top WR Examples

| File Row | Player | Score | Confidence Cap | Confidence Status | Review Notes |
|---:|---|---:|---:|---|---|
| 1 | Puka Nacua | 83.0486 | 0.88 | usable_with_confidence_cap | Top WR anchor. |
| 2 | Jaxon Smith-Njigba | 82.8713 | 0.88 | usable_with_confidence_cap | Top WR anchor. |
| 6 | Ja'Marr Chase | 74.1258 | 0.88 | usable_with_confidence_cap | Elite WR anchor. |
| 8 | Amon-Ra St. Brown | 68.5918 | 0.82 | capped_review_required | Top WR with capped review required. |
| 10 | George Pickens | 62.9783 | 0.8 | capped_review_required | Top WR with identity/team review warning. |
| 15 | Nico Collins | 59.7382 | 0.88 | usable_with_confidence_cap | High WR bridge row. |
| 16 | Chris Olave | 59.4933 | 0.88 | usable_with_confidence_cap | High WR bridge row. |
| 19 | Davante Adams | 57.5485 | 0.88 | usable_with_confidence_cap | Aging productive WR review row. |
| 20 | Drake London | 57.2578 | 0.88 | usable_with_confidence_cap | Young WR review row. |
| 21 | CeeDee Lamb | 56.2217 | 0.88 | usable_with_confidence_cap | Elite-name WR lower than top tier; human-review prompt. |

## Balance Observations

- RB and WR each place 4 players in the top 10 numeric current-player scores.
- RB places 11 players in the top 25, while WR places 9 players in the top 25.
- RB median score is `59.6777`; WR median score is `32.3993`.
- RB scores are more concentrated in the 60+ bands, while WR has a wider lower
  and middle distribution.
- RB age warnings appear on 8 RB rows and should be reviewed in the later
  veteran age-window audit.
- WR identity/team warnings appear on 11 WR rows and should be reviewed in the
  later injury/status/source-risk audits.
- These observations are balance prompts only. They do not prove the RB/WR
  relationship is correct or incorrect.

## Named Human-Review Prompts

- `Christian McCaffrey`, `Derrick Henry`, `Saquon Barkley`, and `Josh Jacobs`
  are high RB rows with age-window or age-cliff warnings.
- `Bijan Robinson`, `Jahmyr Gibbs`, `Breece Hall`, and `Kenneth Walker III` are
  young-RB balance anchors for later human review.
- `CeeDee Lamb`, `Justin Jefferson`, `Garrett Wilson`, and `Malik Nabers` sit
  below several RBs and should be reviewed as named WR sanity checks.
- `Ashton Jeanty`, `Kaleb Johnson`, `Jeremiyah Love`, `Luther Burden`,
  `Carnell Tate`, and `Jordyn Tyson` expose low-evidence or blank-score rows
  that should not be interpreted as confident RB/WR balance signals.

## Non-Goals

- Do not tune RB/WR formulas from this report.
- Do not change model weights, age curves, VORP, replacement formulas,
  confidence caps, or startup-slot conversion.
- Do not add market, ADP, rankings, projections, consensus, startup, or
  trade-calculator logic to private value.
- Do not use this report as a final ranking or roster recommendation.
