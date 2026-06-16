# Drop Decision Phase 5AK Dynasty Rankings Evidence-Gap Audit - 2026-06-15

## Classification

Overall: YELLOW

Phase 5A human-review usability: GREEN

Actual drop-decision evidence quality: YELLOW

The Phase 5A Decision Board and human-review packet remain usable as human-review context. The main evidence-quality caveat is that the local Dynasty Rankings / full-board bridge is incomplete: the app-configured full-board review export is missing locally, so Dynasty Rankings can identify the 240-player universe but cannot currently provide connected private-score context from the expected full-board artifact.

This audit does not open Phase 5B and does not create, imply, sort, or rank any drop recommendation.

## Lane Proof

- Repo: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision`
- Branch: `work/drop-decision-day-review`
- HEAD: `7f614a0087f803869a46ea5ecd04444eefe17c2d`
- Remote branch: `7f614a0087f803869a46ea5ecd04444eefe17c2d`
- Local/remote match at audit start: yes

## Dynasty And Full-Board Context Found

| Artifact or source | Status | Rows | Allowed use notes |
| --- | --- | ---: | --- |
| `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv` | present, ignored, untracked | 80 | `review_only_current_value_checkpoint`; not final ranking or roster recommendation. |
| `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv` | present, ignored, untracked | 371 | Unified review-only asset context; not promoted rankings. |
| active data pack `model_outputs.csv` | present under ignored local data pack | 240 | Identity universe for local app review; not a Phase 5B recommendation source. |
| Rankings app service context | present in code | 240 live rows from active pack | Market, league, ADP, consensus, projection, startup, and trade-calculator context are display-only. |

The Rankings page and services explicitly frame market and league context as display-only. The app page text says market and league ranks are never used in private value. The service also marks legacy active-pack scores as comparison-only and reports zero market, league-rank, or legacy active-pack scores used in full-board private value generation.

## Missing Full-Board Context

Two expected full-board review artifacts are missing locally:

| Missing artifact | Expected role | Expected row count |
| --- | --- | ---: |
| `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv` | App-configured full-board private review rows for Dynasty Rankings | 240 |
| `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv` | Full-board current-value checkpoint source feeding the full-board export | 232 QB/RB/WR/TE rows |

No regeneration was attempted in this audit.

No-write service check:

- With the app-configured missing full-board path, the Rankings service builds 240 identity rows, but 0 rows have a primary private score and 240 rows require manual review.
- With the narrower current-value checkpoint file, the service builds 240 identity rows, 71 rows have a primary private score, and 169 rows remain missing current-player score context.

This means the Decision Board artifacts are usable for Phase 5A, but Dynasty Rankings are not fully connected enough to serve as a complete board-wide evidence QA layer until the canonical full-board exports are present.

## Cross-Artifact Coverage Summary

Required Phase 5A artifacts are present, ignored, and untracked:

| Artifact | Rows | Coverage note |
| --- | ---: | --- |
| `june15_decision_board_review_rows.csv` | 105 | Review-only Decision Board rows. |
| `human_decision_review_summary.csv` | 14 | Human review packet summary. |
| `pick_review_cards.csv` | 5 | Pick review questions only. |
| `roster_pressure_review_cards.csv` | 24 | Covers all 24 roster rows. |
| `trade_review_cards.csv` | 26 | Trade/external context cards; not one-per-roster by design. |
| `rookie_manual_scout_queue.csv` | 94 | Rookie manual scouting questions only. |
| `veteran_risk_review_cards.csv` | 30 | Veteran risk questions; not one-per-roster by design. |
| `roster_opportunity_cost_rows.csv` | 24 | Covers all 24 roster rows. |
| `cut_keep_pressure_review_rows.csv` | 24 | Covers all 24 roster rows. |
| `trade_away_candidate_review_rows.csv` | 24 | Covers all 24 roster rows. |
| `niners_roster_state_review.csv` | 24 | Baseline Niners roster state. |
| `player_age_2026.csv` | 275 | Local review-only age context. |

Roster-family consistency is GREEN:

- roster state rows: 24
- pressure rows: 24
- opportunity-cost rows: 24
- trade-away rows: 24
- missing roster names across those four artifacts: 0
- extra roster names across those four artifacts: 0

Decision Board roster context consistency is GREEN:

- `roster_pressure_trade_context` rows: 24
- coverage in pressure rows: 24 of 24
- coverage in opportunity-cost rows: 24 of 24
- coverage in trade-away rows: 24 of 24
- coverage in roster-pressure cards: 24 of 24

## Identity And Schema Findings

No duplicate keys or blank required names were found in the core 24-row roster family. Decision Board `decision_key` values are unique and nonblank. The repeated `entity_label` values in the Decision Board are expected because the board includes multiple context families, not one row per entity.

Two exact-name mismatches should be reviewed before using dynasty-asset context as a strict identity check:

| Neutral gap type | Roster label | Matching dynasty-asset display label found |
| --- | --- | --- |
| suffix / display-name mismatch | Brian Thomas | Brian Thomas Jr. |
| suffix / display-name mismatch | Oronde Gadsden | Oronde Gadsden II |

These are data-quality identity issues only. They are not roster-action guidance.

## Review-Only And Forbidden Output Shape

The required artifacts carry review-only `allowed_use` / `blocked_use` framing where expected:

- Decision Board: `review_only_june15_decision_context_not_final_action`
- Decision Board blocked use: `do_not_use_as_final_cut_keep_trade_or_draft_recommendation`
- current value: `review_only_current_value_checkpoint`
- roster opportunity cost: `review_only_roster_opportunity_cost_not_cut_keep_recommendation`
- cut/keep pressure: `review_only_cut_keep_pressure_not_final_decision`
- trade-away context: `review_only_trade_away_context_not_recommendation`
- human prep cards: `review_only_human_decision_prep_not_final_action`

No forbidden final recommendation, probability, outcome-band, app-readable recommendation, final-action, or ranked-drop output shape was detected in the audited headers.

## Age Caveat Status

Age artifact status is GREEN for Phase 5A caveat visibility:

- `player_age_2026.csv` rows: 275
- `allowed_use`: `local_review_only`
- `warning_flags`: `source_updated_2026_06_04;source_provided_age_not_dob_derived`
- blank `age_total_months`: 0

Age values remain source-provided strings as of the June 4, 2026 source update date. They were not recalculated in this audit.

## HQ Data Requests

Main HQ should provide or authorize regeneration of the canonical local full-board exports before treating Dynasty Rankings as a complete evidence-quality cross-check for Drop Decision review:

### Request 1 - Full Player Board Review Rows

- Name: canonical full player board value review rows
- Expected path: `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`
- Expected row count: 240 active-pack rows
- Required columns include: `player_id`, `canonical_player_key`, `player_name`, `normalized_player_name`, `position`, `nfl_team`, `nwr_rank`, `nwr_dynasty_score`, `score_status`, `trust_status`, `pool_status`, `is_my_team`, `league_rank`, `market_rank`, `source_path`, `source_column`, `allowed_use`, `blocked_use`, `warning_flags`, `data_needed`
- Allowed use: Phase 5A evidence-quality review and display-only Dynasty Rankings QA
- Forbidden use: final/implied drop recommendations, candidate sorting/ranking for drop decisions, probabilities, outcome bands, app-readable recommendation outputs, or promoted artifacts

### Request 2 - Full-Board Current-Value Checkpoint Rows

- Name: full-board current-player value checkpoint rows
- Expected path: `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv`
- Expected row count: 232 QB/RB/WR/TE active-board rows
- Required columns include: player identity, position, team, checkpoint/private review score, confidence fields, source path/column, allowed use, blocked use, warning flags, and checkpoint version
- Allowed use: local review-only prerequisite for the full player board review rows
- Forbidden use: market/ranking/projection/private formula shortcuts, final roster-action recommendations, probabilities, bands, or promoted outputs

### Request 3 - Identity Alias Confirmation

- Name: suffix/display-name alias confirmation
- Needed for: roster labels `Brian Thomas` and `Oronde Gadsden`
- Expected resolution: confirm whether these should map to `Brian Thomas Jr.` and `Oronde Gadsden II` in dynasty-asset context
- Allowed use: identity QA only
- Forbidden use: roster-action guidance

## Phase 5A Safe-Use Reminder

The Decision Board remains a human-review context board, not an action list. Use it to inspect receipts, warning flags, missing context, roster pressure, opportunity cost, and manual-review questions. Do not use it to name a final cut, drop, keep, trade, or draft decision.

Phase 5B remains blocked until Main HQ separately authorizes it with explicit gates and stop rules.

## Conclusion

Phase 5A can continue for human review. Actual drop-decision evidence quality remains YELLOW because the canonical full-board Dynasty Rankings bridge is missing locally and two roster/dynasty-asset display labels need identity confirmation.

No final or implied recommendation, candidate sorting/ranking, probabilities, bands, app-readable recommendation output, promoted artifact, external-source use, rookie framework edit, commit, push, deploy, merge, or staging occurred in this audit.
