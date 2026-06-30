# NFLVerse Approved Identity to NWR Player ID Binding Packet V1

Generated: 2026-06-30

Base HQ HEAD: `bb7146271c71c39a1d7f1d82fd40c65b4ce9d4d5`

## Purpose

Bind the human-approved, review-only NFLVerse identity overlay rows to safe NWR player IDs where tracked evidence supports the binding.

This packet is documentation/data-hygiene only. It does not rebuild the player context artifact, wire app pages, approve model use, or promote source truth.

## Inputs

| Input | Rows | SHA256 |
| --- | ---: | --- |
| `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_approved_overlay_v1.csv` | 43 | `8daf0c781b7d367b7ee789819b5d712d4636983c21330ece14c9fb88243a7e50` |
| `docs/hq/data_sources/nflverse_player_context_identity_approved_overlay_20260630/identity_overlay_non_approved_rows.csv` | 11 | `2c7a2c4df57ff9582cccfed2a8dcd7ad6a854f0d7cf3209e4196ce8c98838c14` |
| `docs/hq/data_sources/nflverse_player_context_identity_hardening_v1_20260630/nflverse_player_context_identity_review_packet_v1.csv` | 54 | `4e98b7d9958aba0c8a40cdc6382e1c0b83b9529c88f8d3f0fdbffa51bccbe528` |
| `docs/hq/data_sources/current_context/sleeper_player_status_context_sample_or_current_v1.csv` | 143 | `3f04331279e6ed8e137ef4fd4ba12abbe12f72b597cce95219c06de26b8be66f` |
| `docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv` | 1139 | `8a6d0ba3e4008552cc26481249037556976d7b84bb93f231407684b4cf9f34bb` |
| `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_display_artifact.csv` | 294 | `7deaf344c4d613b8902619a32855898f73b339d8dd603e9e2086a7766fb9d4dd` |

## Outputs

| Output | Rows/Status |
| --- | --- |
| `approved_identity_nwr_binding_matrix.csv` | 43 approved-overlay rows |
| `unbound_or_ambiguous_identity_rows.csv` | 2 rows |
| `approved_identity_nwr_binding_summary.md` | summary and verdict |
| `binding_methodology.md` | binding rules and caveats |
| `binding_guardrail_report.md` | guardrail proof |
| `next_rebuild_lane_prompt.md` | prompt for a later artifact rebuild lane |

## Validation Snapshot

- Approved source rows: 43
- Non-approved rows left unbound: 11
- Bound review-only rows: 41
- Unbound or ambiguous rows: 2
- Ambiguous blocked rows: 0
- Existing safe display rows proving NWR player ID equals Sleeper ID: 240 / 240
