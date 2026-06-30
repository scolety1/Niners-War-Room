# NFLVerse Availability Denominator Display Artifact V1 Manifest

Generated: 2026-06-30
Verdict: YELLOW_PARTIAL_DENOMINATOR_ARTIFACT_READY

## Artifact Grain

Primary grain: one row per tracked current NWR player per season anchor.

Season anchors: 2024 and 2025, because the approved local player-context snapshot has regular-season weekly rosters, schedules, snap counts, and weekly player stats for those seasons. Identity-review rows are retained at the same grain but expose no denominator detail.

## Outputs

- availability_denominator_display_artifact.csv
- availability_denominator_join_health.csv
- availability_denominator_schema_manifest.csv
- availability_denominator_source_gate.md
- availability_denominator_build_report.md
- availability_denominator_guardrail_report.md
- next_integration_plan.md

## Source Inputs

- docs\hq\data_sources\nflverse_player_context_display_20260630\nflverse_player_context_display_artifact.csv
- docs\hq\data_sources\nflverse_dataset_level_refresh_health_20260630\nflverse_dataset_registry_v1.csv
- docs\hq\data_sources\nflverse_dataset_level_refresh_health_20260630\nflverse_dataset_coverage_matrix_v1.csv
- docs\hq\injury_availability_context\injury_availability_display_context_safe_upgrade_20260630\nflverse_availability_field_map.csv
- Approved local-only snapshot: C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630

## Scope

This artifact is display-only and review-only. It is not an injury-risk, medical, model, ranking, hidden-sort, recommendation, trade-value, or pick-value artifact.
