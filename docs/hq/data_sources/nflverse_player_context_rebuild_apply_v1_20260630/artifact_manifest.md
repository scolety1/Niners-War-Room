# NFLVerse Player Context Rebuild Apply V1

Generated: 2026-06-30

Base HQ HEAD: `d7f62011815e8e826edb5e027e4d38db8ef4ac01`

## Purpose

Consume the approved identity-to-NWR binding packet and apply safe review/display-only identity bindings to the tracked NFLVerse player context display artifact.

## Inputs

| Input | Rows | SHA256 |
| --- | ---: | --- |
| `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/approved_identity_nwr_binding_matrix.csv` | 43 | `e49a6331ed7b21727f85bab2baa12e0955200229b4dc2589e92a1511ec8e581d` |
| `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_overlay_non_approved_rows.csv` | 11 | `2c7a2c4df57ff9582cccfed2a8dcd7ad6a854f0d7cf3209e4196ce8c98838c14` |
| `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv` | 294 | rebuilt in this lane |
| `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_join_health.csv` | 15 | rebuilt in this lane |
| `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_schema_manifest.csv` | 51 | updated metadata only |

## Outputs

| Output | Rows/Status |
| --- | --- |
| `player_context_rebuild_delta.csv` | 41 applied rows |
| `remaining_gated_rows.csv` | 13 gated rows |
| `rebuild_apply_summary.md` | summary and verdict |
| `rebuilt_player_context_guardrail_report.md` | guardrail proof |
| `app_lane_handoff.md` | app-lane consumption instructions |

## Result

- Display artifact rebuilt: yes
- Previously safe display rows: 240
- Newly activated bound rows: 41
- New safe display rows: 281
- Remaining gated rows: 13
