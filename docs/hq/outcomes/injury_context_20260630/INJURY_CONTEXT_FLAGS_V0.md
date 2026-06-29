# Injury Context Flags V0

## Executive verdict

`GREEN_ARTIFACT_ONLY`

Injury Context Flags V0 builds review-only injury and availability caveats from the approved
`nflreadpy.load_injuries` source gate and joins them to the Outcome V2 current-player display
artifact without changing any Outcome V2 probability, Dynasty Rank, tier, hidden sort, trade
value, pick value, or app behavior.

The app display gate is `ARTIFACT_ONLY_NO_APP_DISPLAY`. Rankings and Player Compare were not
changed in this lane.

## Source data

Raw review-only injury context:

`C:\NWR_SHARED_DATA\injury_context\nflreadpy_injuries_review_only_2012_2025.csv`

Source gate:

`APPROVE_INJURY_CONTEXT_REVIEW_ONLY`

Coverage from the generated V0 summary:

| Metric | Value |
| --- | ---: |
| Raw injury rows | 76,469 |
| Season-level injury summary rows | 19,005 |
| Current display rows | 240 |
| Players with any injury context | 224 |
| Players with 2025 injury context | 201 |
| Players with prior out/doubtful context | 92 |
| Missing current feature coverage rows | 5 |
| Rookie/prospect out of scope rows | 43 |

Generated shared-data outputs:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\injury_context_flags_v0\injury_context_flags_v0.csv`

`C:\NWR_SHARED_DATA\outcome_v2_horizon\injury_context_flags_v0\injury_context_flags_v0_manifest.csv`

`C:\NWR_SHARED_DATA\outcome_v2_horizon\injury_context_flags_v0\injury_context_flags_v0_coverage_summary.csv`

Committed compact enhanced review artifact:

`docs/hq/outcomes/outcome_v2_horizon_20260630/outcome_v2_current_player_display_with_injury_context.csv`

Enhanced artifact SHA256:

`63569e3758ab20e74eef30c1723afc72c80b5f6174f66d9a4015c24f0f44723e`

## Fields used

The V0 service uses factual injury report fields only:

- `season`
- `week`
- `team`
- `gsis_id`
- `position`
- `full_name`
- `report_status`
- `practice_status`
- injury detail fields as raw context only

The service also uses the already approved Outcome V2 current display artifact and extended
historical season labels to describe feature coverage and last materially active season.

## Fields not used

V0 does not use:

- ADP
- market values
- DynastyProcess
- projections
- analyst ranks
- trade values
- CFBD
- vendor injury feeds
- Gmail
- hidden rank adjustments
- medical comeback assumptions

## Flag definitions

`injury_context_available`:
Whether the player has any review-only injury context row in the approved injury source.

`prior_season_injury_context_available`:
Whether the player has a 2025 injury context row for the 2026-pre-draft Outcome V2 context.

`prior_season_injury_report_weeks`:
Distinct 2025 report weeks present in the review-only injury source.

`prior_season_out_or_doubtful_weeks`:
Distinct 2025 report weeks where report status is out or doubtful. This is a review flag only.

`limited_recent_sample`:
Whether the current Outcome V2 row has missing 2025 feature coverage or the most recent material
football activity predates 2025. This is not a health label.

`last_materially_active_season`:
Most recent season with enough factual football activity to support feature context. V0 uses
season labels and the approved 2025 feature coverage status. This must not be renamed to
last healthy season.

`seasons_since_material_activity`:
Distance from the 2026-pre-draft context to the last materially active season.

`availability_caveat`:
Plain-language review caveat. Missing injury context is explicitly not clean health.

`not_enough_information_reason`:
Plain-language explanation for rows where Outcome V2 remains unavailable or caveated.

## Missing-feature player examples

| Player | V0 caveat |
| --- | --- |
| Brandon Aiyuk | No approved 2025 Outcome V2 feature row. Last materially active season: 2023. Missing injury context is not clean health. |
| Joe Mixon | No approved 2025 Outcome V2 feature row. Last materially active season: 2024. Missing injury context is not clean health. |
| Tank Dell | No approved 2025 Outcome V2 feature row. Last materially active season: 2024. Missing injury context is not clean health. |
| Jonathon Brooks | No approved 2025 Outcome V2 feature row. Last materially active season is Not enough information. Missing injury context is not clean health. |
| MarShawn Lloyd | No approved 2025 Outcome V2 feature row. Review-only injury context shows 3 report weeks and 3 out/doubtful weeks in 2025. This is not a medical projection. |

## Allowed use

- Review-only injury and availability caveats.
- Display context in future gated UI work if the UI language remains non-medical and display-only.
- Better `Not enough information` explanations for Outcome V2 missing-feature rows.

## Blocked use

- Injury-risk score.
- Comeback or recovery probability.
- Medical projection.
- Rank adjustment.
- Hidden sort.
- Model input.
- Source truth.
- Trade or pick value.
- Start/sit or waiver recommendations.

## App display gate

Decision: `ARTIFACT_ONLY_NO_APP_DISPLAY`

Reason: V0 safely creates a compact enhanced review artifact, but app runtime integration is a
separate product decision. The existing Rankings Outcome Lens continues to use the approved
Outcome V2 display artifact. No app files were touched in this lane.

## Guardrails

- Existing Outcome V2 probability columns are byte-for-byte preserved in the enhanced artifact.
- Rookies/prospects remain out of scope.
- Missing feature rows remain `Not enough information`, not zero.
- Missing injury context is not interpreted as clean health.
- Injury context flags are marked review-only.
- `injury_used_as_model_input=false`.
- `medical_projection_made=false`.
- No raw `C:\NWR_SHARED_DATA` files are committed.

## Human review checklist

- Confirm the non-medical wording is acceptable before any app display lane.
- Confirm Player Compare or Rankings Outcome Lens is the right surface before UI work.
- Keep injury context in a data review/caveat area, not Clean Board.
- Do not let injury context drive sort, rank, model value, trade value, or pick value.
