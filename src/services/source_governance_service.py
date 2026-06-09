from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.veteran_model_schema_service import build_veteran_schema_report


@dataclass(frozen=True)
class SourceGovernanceBoard:
    data_pack_sources: list[dict[str, object]]
    veteran_sources: list[dict[str, object]]
    audit_notes: list[dict[str, object]]
    manual_overrides: list[dict[str, object]]
    issue_rows: list[dict[str, object]]
    override_template_rows: list[dict[str, object]]


def build_source_governance_board(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path,
) -> SourceGovernanceBoard:
    validated = validate_data_pack(data_pack_path)
    report = build_veteran_schema_report(veteran_model_dir)
    return SourceGovernanceBoard(
        data_pack_sources=[
            {
                "file": row.get("file_name"),
                "source": row.get("source_name"),
                "type": row.get("source_type"),
                "review": row.get("review_status"),
                "pulled_at": row.get("pulled_at"),
                "notes": row.get("notes"),
            }
            for row in validated.rows_by_table.get("metadata_sources", [])
        ],
        veteran_sources=[
            {
                "source_key": source.source_key,
                "source_name": source.source_name,
                "source_type": source.source_type,
                "source_family": source.source_family,
                "source_domain": source.source_domain,
                "authority_tier": source.authority_tier,
                "priority_rank": source.priority_rank,
                "required_for_modes": source.required_for_modes,
                "freshness_window_hours": source.freshness_window_hours,
                "scoring_context": source.scoring_context,
                "is_active": source.is_active,
                "source_date": source.source_date,
                "retrieved_at": source.retrieved_at,
                "reliability_score": source.reliability_score,
                "local_path": source.local_path,
                "parser_version": source.parser_version,
                "notes": source.notes,
            }
            for source in report.sources
        ],
        audit_notes=[
            {
                "note_id": note.note_id,
                "player_id": note.player_id,
                "feature_name": note.feature_name,
                "note_scope": note.note_scope,
                "affects_score": note.affects_score,
                "source_key": note.source_key,
                "note_text": note.note_text,
                "created_at": note.created_at,
            }
            for note in report.audit_notes
        ],
        manual_overrides=[
            {
                "override_id": override.override_id,
                "player_id": override.player_id,
                "feature_name": override.feature_name,
                "target_field": override.target_field,
                "old_value": override.old_value,
                "override_value": override.override_value,
                "override_type": override.override_type,
                "reason_code": override.reason_code,
                "source_key": override.source_key,
                "status": override.status,
                "review_status": override.review_status,
                "requested_by": override.requested_by,
                "approved_by": override.approved_by,
                "self_approved": override.self_approved,
                "override_reason": override.override_reason,
                "provenance": override.provenance,
                "created_at": override.created_at,
            }
            for override in report.manual_overrides
        ],
        issue_rows=[
            {
                "severity": issue.severity,
                "file": issue.file_name,
                "entity": issue.entity_id,
                "field": issue.field_name,
                "issue": issue.issue,
                "fix": issue.suggested_fix,
            }
            for issue in report.issues
        ],
        override_template_rows=[
            {
                "override_id": "override_player_feature_01",
                "season": "2026",
                "player_id": "",
                "position": "WR",
                "feature_name": "",
                "target_field": "normalized_score",
                "old_value": "50.0",
                "override_value": "50.0",
                "override_type": "data_correction",
                "reason_code": "other",
                "source_key": "manual_fixture_2026",
                "override_reason": "",
                "provenance": "",
                "requested_by": "",
                "approved_by": "",
                "self_approved": "true",
                "review_status": "approved",
                "status": "active",
                "created_at": "2026-05-05T00:00:00-06:00",
            }
        ],
    )
