# Outcome V2 Current Feature / As-Of Gate

Date: 2026-06-29

## Verdict

`BLOCKED_TEMPORAL_ALIGNMENT`

The current-board-to-GSIS identity bridge is GREEN, but current-player Outcome V2 display artifacts are still blocked. The current Dynasty Rankings board is `2026-pre-draft`, while the approved/reviewed Outcome V2 historical feature and label path currently supports factual player-season labels through 2024.

Using 2024 as the current feature season would make `This Year` mean 2025, not the current 2026 draft-day context. That is temporally misaligned.

Using the available 2025 season-stats candidate would require source-policy promotion that this lane does not have.

## Current Board

Current board:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Observed as-of:

| Field | Value |
| --- | --- |
| `score_as_of_date` | `2026-pre-draft` |
| Rows | 240 |

## Identity Bridge Status

Identity bridge artifact:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge\outcome_v2_current_identity_bridge.csv`

| Metric | Value |
| --- | ---: |
| QB/RB/WR/TE bridge rows | 232 |
| Exact veteran/non-rookie matches | 189 |
| Missing GSIS | 0 |
| Ambiguous GSIS | 0 |
| Rookie/prospect out of scope | 43 |
| Veteran/non-rookie rows with historical labels | 188 |
| Veteran/non-rookie rows without historical label | 1 |

The single exact veteran/non-rookie row without historical Outcome V2 label coverage is J.J. McCarthy. That remains `Not enough information`, not a fabricated miss.

## Approved / Reviewed Feature Coverage

Extended historical labels:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\outcome_v2_extended_season_outcome_labels.csv`

| Metric | Value |
| --- | --- |
| Seasons covered | 2012-2024 |
| Scoring mode | `exact_verified_first_downs` |
| Review status | review-only historical labels |
| Model/rank/app wiring allowed | no |

These labels validate the historical probability fields. They do not by themselves define a safe current-player feature snapshot for a `2026-pre-draft` board.

## 2025 Feature Candidate Review

Potential 2025 season-stats context found:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\20260621_pre_backtest_scoring_aligned_v1\player_season_stats_display_context.csv`

Pointer:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_season_stats_display_context\latest_candidate.json`

Observed source policy:

| Field | Value |
| --- | --- |
| `approval_status` | `candidate` |
| `approval_scope` | `display_stat_context_review_only` |
| `live_use_allowed` | `false` |
| `source_timing_class` | `unknown_timing_yellow` |
| `forbidden_use` includes | `private_value`, `hidden_sort`, `hidden_rank`, `draft_recommendation`, `final_draft_decision`, `model_training`, `simulation`, `production_deployment`, `latest_approved` |

The candidate includes 2024 and 2025 season rows, but its manifest explicitly requires source freshness/as-of review before live use. It is not approved as Outcome V2 feature truth and was not used to generate current-player probabilities.

## Gate Questions

1. What season is the current Dynasty Rankings board representing?

`2026-pre-draft`.

2. What is the latest approved factual player-season feature data available?

The Outcome V2 historical label path is validated through 2024. The 2025 season-stats context is candidate/display-only and `unknown_timing_yellow`.

3. Is 2025 factual player-season data approved and available?

Available as a candidate display context, but not approved for Outcome V2 current-player feature generation.

4. If only 2024 is approved, can it support a 2025/2026 display artifact?

No. For a `2026-pre-draft` board, 2024 anchors are stale for `This Year` / `Next Year` naming. They would describe 2025/2026 windows from an old anchor, not the current 2026-pre-draft state.

5. Which current veterans have feature coverage?

The identity bridge finds 189 exact veteran/non-rookie GSIS matches. Of those, 188 have historical label coverage, but that coverage is still not temporally aligned to the current board.

6. Which players are rookies/prospects?

43 rows are marked `out_of_scope_rookie_or_prospect` for Normal Outcome V2.

7. Which validated fields can be generated without temporal leakage?

None for current-player display until Master approves a current/as-of feature snapshot. The historical validation fields are validated in principle, but no current-player feature source is approved for applying them.

## Decision

Primary decision:

`BLOCKED_TEMPORAL_ALIGNMENT`

Secondary blocker:

`BLOCKED_SOURCE_POLICY`

No current-player display artifact was created. No Rankings integration was attempted.

## Guardrails Preserved

This gate did not change:

- Rankings
- Outcome Lens
- Dynasty Rank
- tiers
- frozen board
- pinned snapshot/hash
- `latest_candidate`
- `latest_approved`
- model/rank/source-truth gates
- CFBD/NFL source gates
- Live Draft
- Mock Draft
- draft runtime state
- hosted deployment

This gate did not create:

- current-player probabilities
- app-facing Outcome V2 columns
- rookie/prospect outcome probabilities
- hidden sort fields
- trade value
- pick value

Blocked inputs not used:

- DynastyProcess
- ADP
- market values
- CFBD
- Gmail
- vendor/RotoWire/FantasyPros
- projections
- analyst ranks
- trade values
- true routes / TPRR / YPRR
- injury projections

## Required Next Step

Master needs to approve a current/as-of feature source before Outcome V2 can generate a current-player display artifact. The safest candidate to review is the 2025 season-stats context, but it must be promoted explicitly for Outcome V2 feature use with timing/freshness rules before this lane can proceed.
