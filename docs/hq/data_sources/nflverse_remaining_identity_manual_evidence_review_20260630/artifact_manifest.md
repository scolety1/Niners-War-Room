# NFLVerse Remaining Identity Manual Evidence Review Manifest

- artifact: `nflverse_remaining_identity_manual_evidence_review_20260630`
- created_for: `Manual evidence review of the 13 remaining NFLVerse player-context identity gates`
- base_head: `c79f8ec915ef35199b8eadc4f91a2c05bbbe21a9`
- source_remaining_identity_review_matrix: `docs\hq\data_sources\nflverse_player_context_remaining_identity_review_20260630\remaining_identity_review_matrix.csv`
- source_remaining_identity_review_sha256: `949b4148f48d86eeff5a61e49770fdc278282c129bb38bd98d4b809d4e44e35f`
- source_human_decision_sheet: `docs\hq\data_sources\nflverse_player_context_remaining_identity_review_20260630\human_decision_sheet_for_remaining_rows.csv`
- source_human_decision_sheet_sha256: `efeb88caf82ee3412a36279fa9b799632266884359cd5967554fe32e376401d7`
- source_remaining_gated_rows: `docs\hq\data_sources\nflverse_player_context_rebuild_apply_v1_20260630\remaining_gated_rows.csv`
- source_remaining_gated_rows_sha256: `4d69f61a4ea79c8d33daa1ce4a502a2a022efef1852b7bb88435ad341134e449`
- source_display_artifact: `docs\hq\data_sources\nflverse_player_context_display_20260630\nflverse_player_context_display_artifact.csv`
- source_display_artifact_sha256: `129461e3972d6d378e4a4d00e1fb962ffa37d1a4732ad340af2ba90394c6ad94`
- rows_reviewed: `13`
- rows_with_user_manual_evidence: `8`
- approved_rows_created: `0`
- display_artifact_rebuilt: `false`
- app_behavior_changed: `false`

## Outputs
- `manual_evidence_matrix.csv`
- `recommended_human_decision_sheet.csv`
- `binding_followup_candidates.csv`
- `manual_evidence_review_summary.md`
- `guardrail_report.md`
- `next_binding_prompt.md`

This packet is review-only. It does not approve any identity, rebuild the player context artifact, or allow model/source-truth/rank use.
