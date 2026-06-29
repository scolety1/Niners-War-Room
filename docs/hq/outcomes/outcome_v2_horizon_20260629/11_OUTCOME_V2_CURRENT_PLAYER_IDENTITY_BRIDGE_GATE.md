# Outcome V2 Current Player Identity Bridge Gate

Date: 2026-06-29

## Verdict

`BLOCKED_NO_APPROVED_COMPACT_GSIS_BRIDGE`

Normal Outcome V2 remains blocked from current-player display. The gate found diagnostic evidence that many current Dynasty Rankings players can be name/position matched to historical Outcome labels, but it did not find an approved compact bridge from current board player IDs to GSIS/NFL player IDs.

This report is for Normal Outcome V2 only. Rookie Outcome remains a separate blocked/R&D lane and is not promoted here.

## Inputs Audited

- Current Dynasty Rankings board:
  `C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest\full_player_board_value_review_rows.csv`
- Existing committed identity audit:
  `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv`
- Historical Outcome V2 season labels:
  `C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels\outcome_v2_season_outcome_labels.csv`

No shared-data source was committed. No current-player display artifact was created.

## Generated Review-Only Audit Artifacts

Generated under:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge\`

Files:

- `outcome_v2_current_identity_bridge_audit.csv`
- `outcome_v2_current_identity_bridge_summary.csv`
- `outcome_v2_current_identity_bridge_manifest.csv`

These files are local review artifacts only and must remain untracked.

## Audit Results

| Metric | Value |
| --- | ---: |
| Current board rows | 240 |
| QB/RB/WR/TE eligible rows | 232 |
| Approved GSIS bridge rows | 0 |
| Diagnostic name/position historical matches | 187 |
| Rows left as `Not enough information` | 232 |
| Rookie/prospect-like rows excluded from Normal Outcome V2 | 43 |
| Current display artifact created | no |

The existing identity audit has an `nflverse_id_or_gsis` column, but the audited file contains zero nonblank values for that field. Therefore it cannot serve as the approved current-board-to-GSIS bridge.

## Diagnostic Matches Are Not Approval

The audit intentionally reports name/position historical matches separately from approved bridge rows.

Example diagnostic-only matches include current-board players such as Puka Nacua, Jaxon Smith-Njigba, Bijan Robinson, Jonathan Taylor, Jahmyr Gibbs, Ja'Marr Chase, Amon-Ra St. Brown, Trey McBride, De'Von Achane, and George Pickens. These matches are useful for review, but they are not safe enough to power display probabilities because they are not an approved deterministic identity bridge.

The gate therefore does not create:

- `outcome_v2_current_player_display.csv`
- app-facing Outcome V2 columns
- Rankings Outcome Lens integration
- current-player probabilities

## Rookie / Prospect Boundary

Rows that look like current draft/prospect-only players without NFL historical labels are marked out of scope for Normal Outcome V2. They belong to Rookie Outcome, which remains blocked until CFBD identity approvals and draft capital gates are solved.

Normal Outcome V2 does not use:

- CFBD
- draft capital
- scouting notes
- ADP
- market value
- DynastyProcess
- rookie/prospect college production

## Current Feature / As-Of Blocker

Even after an approved GSIS bridge exists, a current display artifact still needs an explicit as-of feature definition.

The current board is 2026-pre-draft context. Historical factual NFL features in the validated Outcome V2 path top out at 2024. A future lane must define whether current-player features are:

- latest complete 2024 NFL season facts,
- a specific 2025/2026 factual stat snapshot if approved,
- or unavailable, in which case the display must say `Not enough information`.

No current-player feature snapshot was promoted in this gate.

## Guardrails Preserved

This gate did not change:

- Dynasty Rank
- Candidate Rank
- tiers
- frozen board
- pinned snapshot
- latest_candidate
- latest_approved
- model logic
- source-truth gates
- hidden sort
- trade value
- pick value
- Live Draft
- Mock Draft
- Rankings app code

All outputs remain:

- `model_input_allowed=no`
- `training_allowed=no`
- `app_wiring_allowed=no`

## Required Next Step

Build or approve a compact deterministic identity bridge with at least:

- current board `player_id`
- current board `player_name`
- position
- team
- Sleeper/internal ID
- GSIS/NFL player ID
- match method
- match confidence
- manual review status
- rookie/prospect exclusion status

Only after that bridge passes can a future gate evaluate current feature/as-of coverage. Current-player Outcome V2 display probabilities remain blocked until both gates pass.
