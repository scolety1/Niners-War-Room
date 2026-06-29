# Outcome V2 Current Identity Bridge Gate

Date: 2026-06-29

## Verdict

`GREEN_IDENTITY_BRIDGE_BUILT`

Normal Outcome V2 now has a compact review-only current-board-to-GSIS identity bridge for the current Dynasty Rankings board. This resolves the prior `YELLOW_IDENTITY_BRIDGE_BLOCKED` condition for identity only.

This does not create current-player probabilities, app-facing Outcome V2 columns, Rankings integration, model inputs, hidden sort fields, source-truth promotion, trade value, pick value, or rookie outcome probabilities.

## Branch / Base

- Worktree: `C:\NWR\Niners-War-Room-outcome-v2-current-identity-bridge-20260630`
- Branch: `work/outcome-v2-current-identity-bridge-20260630`
- Base source: current `origin/work/hq-parallel-control`
- Base HEAD observed: `3ee9570163b3117029de1dc4a88d4494b8e15b75`
- Outcome V2 finish-columns work carried forward by cherry-pick:
  - historical label factory
  - validation/calibration
  - prior blocked identity gate

## Sources Used

Current board:

`C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`

Identity source:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context\20260621_pre_backtest_scoring_aligned_v1\player_roster_display_context.csv`

Identity source pointer:

`C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context\latest_candidate.json`

Historical label crosscheck:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels\outcome_v2_season_outcome_labels.csv`

## Source Policy Status

The roster identity source is `approval_status=candidate` and `approval_scope=display_stat_context_review_only`.

Allowed uses include:

- `display_stat_context_only`
- `source_audit`
- `identity_crosscheck`
- `future_latest_candidate_review`

Forbidden uses include:

- `private_value`
- `veteran_private_values`
- `hidden_sort`
- `hidden_rank`
- `draft_recommendation`
- `final_draft_decision`
- `model_training`
- `simulation`
- `production_deployment`
- `latest_approved`

Therefore the bridge is review-only/display-only and can support the next Outcome V2 current feature gate. It cannot be used as source truth, model input, rank input, hidden sort, trade value, pick value, or app-facing probability output by itself.

## Bridge Results

| Metric | Value |
| --- | ---: |
| Current board rows | 240 |
| Bridge rows, QB/RB/WR/TE only | 232 |
| Veteran/non-rookie rows | 189 |
| Matched exact rows | 189 |
| Matched high-confidence multi-key rows | 0 |
| Missing GSIS rows | 0 |
| Ambiguous rows | 0 |
| Rookie/prospect out-of-scope rows | 43 |
| High-confidence coverage of veteran/non-rookie rows | 100.0% |

All 189 veteran/non-rookie bridge rows used direct deterministic `current_board.player_id = roster.sleeper_id -> gsis_id`.

No name-only matches were promoted. No fuzzy matches were promoted. No ambiguous rows were silently matched.

## Rookie / Prospect Handling

The bridge found identity rows for 43 rookie/prospect-like players, but marks them `out_of_scope_rookie_or_prospect` for Normal Outcome V2. The out-of-scope status is based on current board high Sleeper-like IDs and roster metadata such as `rookie_year=2025` and `years_exp=0`.

Rookie Outcome remains separate. This bridge does not use CFBD, draft capital, scouting notes, market data, ADP, projections, DynastyProcess, or college production.

## Generated Review-Only Artifacts

Generated under:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge\`

Files:

- `outcome_v2_current_identity_bridge.csv`
- `outcome_v2_current_identity_bridge_audit.csv`
- `outcome_v2_current_identity_bridge_manifest.csv`

These generated shared-data artifacts are not committed.

Manifest summary:

| Artifact | Rows | SHA256 |
| --- | ---: | --- |
| `outcome_v2_current_identity_bridge.csv` | 232 | `523869cef08612d1d784744d2c213d3d8178a26c72cba0c5025992495083a253` |
| `outcome_v2_current_identity_bridge_audit.csv` | 19 | `3e63c4f52232bd96eee2e1a7d5fbffa7ec96c597623482d69c417cd2d5ed4bcb` |

## Match Methods

Accepted:

- `direct_sleeper_id_to_gsis`
- `deterministic_name_position_team`, only when direct ID is unavailable, exact normalized name/position/team identify one GSIS candidate, and no competing candidate exists

Blocked:

- name-only
- name plus position only
- ambiguous duplicate Sleeper IDs
- ambiguous duplicate name/position/team rows
- missing GSIS
- fuzzy matches

## Unresolved High-Value Players

No veteran/non-rookie high-value players are missing GSIS IDs or ambiguous in this bridge.

High-ranked rookie/prospect rows remain out of scope for Normal Outcome V2, including examples such as Tetairoa McMillan, Emeka Egbuka, Ashton Jeanty, Tyler Warren, and Harold Fannin. Those rows require Rookie Outcome gates, not Normal Outcome V2.

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
- hidden sort fields
- rookie/prospect outcome probabilities
- trade valuation
- pick valuation

Blocked sources not used:

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

## Next Gate

Proceed to the Outcome V2 current-player temporal/as-of feature gate.

The next gate still must decide whether safe current-player factual feature coverage exists. The identity bridge alone does not authorize probability generation or Rankings integration.
