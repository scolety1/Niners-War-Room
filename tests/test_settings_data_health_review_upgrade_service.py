from __future__ import annotations

from pathlib import Path

from src.services.settings_data_health_review_upgrade_service import (
    artifact_health_board_rows,
    blocked_today_rows,
    dataset_availability_rows,
    guardrail_status_rows,
    safe_use_today_rows,
    source_contract_summary_rows,
)


def test_artifact_health_board_indexes_current_review_artifacts() -> None:
    rows = artifact_health_board_rows()
    by_name = {row["Artifact"]: row for row in rows}

    assert by_name["NFLVerse Core Usage Review Dataset V1"]["Rows / counts"] == "76804"
    assert by_name["Red-zone sidecar"]["Rows / counts"] == "6424"
    assert by_name["Historical Tuning V3 substrate"]["Rows / counts"] == "5518"
    assert by_name["Historical Tuning Source Contract V1"]["Rows / counts"] == (
        "18 allowed / 4 null-fenced / 11 blocked"
    )
    assert by_name["Shadow Review Gate V1"]["Rows / counts"] == (
        "GO_SHADOW_REVIEW_PACKET_REVIEW_ONLY"
    )
    assert by_name["Evidence Review Hub V1"]["Phase status"] == "MERGED_OR_TRACKED"
    assert {row["Production flag"] for row in rows} == {"production blocked"}


def test_source_contract_summary_preserves_allowed_null_fenced_and_blocked_counts() -> None:
    rows = source_contract_summary_rows()
    by_area = {row["Contract area"]: row for row in rows}

    assert by_area["Allowed review-only features"]["Count"] == "18"
    assert by_area["Null-fenced optional features"]["Count"] == "4"
    assert by_area["Blocked feature families"]["Count"] == "11"
    assert by_area["Current-only context"]["Status"] == "BLOCKED_FOR_HISTORICAL_FEATURES"
    assert by_area["Market/vendor/projection/rank fields"]["Status"] == "SOURCE_TRUTH_BLOCKED"


def test_dataset_availability_is_review_only_and_keeps_shadow_packet_static() -> None:
    rows = dataset_availability_rows()
    by_dataset = {row["Dataset"]: row for row in rows}

    assert by_dataset["Core Usage Dataset V1"]["Status"] == "MERGED_REVIEW_ONLY"
    assert by_dataset["Red-zone sidecar"]["Status"] == "MERGED_REVIEW_ONLY_SIDECAR"
    assert by_dataset["Historical V3 substrate"]["Rows / counts"] == "5518"
    assert by_dataset["Shadow review gate"]["Status"] == "GO_REVIEW_ONLY_PACKET"
    assert {row["Use"] for row in rows} == {"review-only/status display"}


def test_guardrails_and_blocked_lists_keep_production_closed() -> None:
    guardrails = "\n".join(str(row) for row in guardrail_status_rows())
    blocked = "\n".join(str(row) for row in blocked_today_rows())
    safe = "\n".join(str(row) for row in safe_use_today_rows())

    assert "Production formula changes" in guardrails
    assert "Model training/tuning" in guardrails
    assert "Routes/TPRR/YPRR/route proxies" in guardrails
    assert "Ambiguous rz_att" in guardrails
    assert "Production formula promotion" in blocked
    assert "Shadow app/live-preview wiring" in blocked
    assert "SAFE_REVIEW_IF_STATIC" in safe
    assert "production" not in safe.lower().replace("no production decisions", "")


def test_settings_page_wires_review_only_sections() -> None:
    text = Path("app/pages/28_settings_data_health_v1.py").read_text(encoding="utf-8")

    assert "Review-Only Source And Artifact Health" in text
    assert "Artifact Health Board" in text
    assert "Source Contract Summary" in text
    assert "Dataset Availability" in text
    assert "Guardrail Status" in text
    assert "What Can Safely Be Used Today?" in text
    assert "What Is Still Blocked?" in text
    assert "artifact_health_board_rows" in text
