# NFLVerse Player Context Remaining Identity Review Packet

Generated: 2026-06-30

Base HQ HEAD: `096acd4e2d37edb03d3b7091803e2f2f7343204e`

## Purpose

Review the 13 remaining gated NFLVerse player-context identity rows after the display artifact rebuild. This packet is review-only and does not approve identities, rebuild artifacts, or wire app behavior.

## Inputs

| Input | Rows | SHA256 |
| --- | ---: | --- |
| `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv` | 294 | `129461e3972d6d378e4a4d00e1fb962ffa37d1a4732ad340af2ba90394c6ad94` |
| `docs/hq/data_sources/nflverse_player_context_rebuild_apply_v1_20260630/remaining_gated_rows.csv` | 13 | `4d69f61a4ea79c8d33daa1ce4a502a2a022efef1852b7bb88435ad341134e449` |
| `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/approved_identity_nwr_binding_matrix.csv` | 43 | `e49a6331ed7b21727f85bab2baa12e0955200229b4dc2589e92a1511ec8e581d` |
| `docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/unbound_or_ambiguous_identity_rows.csv` | 2 | `f4575b9efa1426dd7295d40101c5a86a7e8e361199986fb7425aeb81110178b2` |
| `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_overlay_non_approved_rows.csv` | 11 | `2c7a2c4df57ff9582cccfed2a8dcd7ad6a854f0d7cf3209e4196ce8c98838c14` |
| `docs/hq/data_sources/nflverse_player_context_identity_hardening_v1_20260630/nflverse_player_context_identity_review_packet_v1.csv` | 54 | `4e98b7d9958aba0c8a40cdc6382e1c0b83b9529c88f8d3f0fdbffa51bccbe528` |
| `docs/hq/data_sources/current_context/sleeper_player_status_context_sample_or_current_v1.csv` | 143 | `3f04331279e6ed8e137ef4fd4ba12abbe12f72b597cce95219c06de26b8be66f` |
| `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv` | 1139 | `8a6d0ba3e4008552cc26481249037556976d7b84bb93f231407684b4cf9f34bb` |

## Outputs

| Output | Rows/Status |
| --- | --- |
| `remaining_identity_review_matrix.csv` | 13 rows |
| `human_decision_sheet_for_remaining_rows.csv` | 13 rows, all pending |
| `remaining_identity_review_summary.md` | review summary |
| `unresolved_blocker_report.md` | blocker categories |
| `guardrail_report.md` | guardrail proof |
| `next_action_prompt.md` | prompt for future human review/binding lane |
