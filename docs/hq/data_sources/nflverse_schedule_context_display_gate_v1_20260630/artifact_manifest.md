# NFLVerse Schedule Context Display Gate V1 Manifest

Generated: 2026-06-30

Verdict: `YELLOW_SCHEDULE_CONTEXT_PARTIAL_LANE_GATING`

## Purpose

This packet centralizes the source-policy/display gate for NFLVerse schedule context. It tells future app lanes where schedule context may be displayed and where it must remain gated.

## Inputs Reviewed

- `docs/hq/data_sources/nflverse_dataset_level_refresh_health_20260630/`
- `docs/hq/data_sources/nflverse_player_context_display_20260630/`
- `docs/hq/data_sources/nflverse_player_context_hardening_20260630/`
- `docs/hq/data_sources/nflverse_player_context_schedule_audit_20260630/`
- `src/services/nflverse_refresh_health_service.py`
- `src/services/nflverse_player_context_display_service.py`
- `src/services/nflverse_player_context_hardening_service.py`
- Merged app-lane docs that mention schedule/opponent/bye gating.

## Outputs

- `artifact_manifest.md`
- `schedule_context_display_gate_summary.md`
- `schedule_context_lane_policy_matrix.csv`
- `schedule_context_field_policy.csv`
- `schedule_context_join_rules.md`
- `schedule_context_missingness_policy.md`
- `merge_safety_report.md`

## Scope

Docs/CSV source-policy only. No app pages, model logic, ranking logic, source truth, protected artifacts, raw shared data, or latest pointers are changed.
