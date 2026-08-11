from __future__ import annotations

from pathlib import Path

from src.services.development_lab_review_upgrade_service import (
    artifact_manifest_rows,
    candidate_review_panel_rows,
    current_stats_review_improvement_rows,
    dataset_browser_rows,
    guardrail_ledger_rows,
    lab_status_board_rows,
    next_lane_idea_rows,
)


def test_review_upgrade_dataset_browser_uses_tracked_artifact_summaries() -> None:
    rows = dataset_browser_rows()
    by_dataset = {row["Dataset"]: row for row in rows}

    assert by_dataset["NFLVerse Core Usage Review Dataset V1"]["Rows"] == "76804"
    assert by_dataset["NFLVerse Core Usage Review Dataset V1"]["Fields"] == "40"
    assert by_dataset["NFLVerse Core Usage Review Dataset V1"]["Feature seasons"] == "2024;2025"
    assert by_dataset["Red-zone sidecar"]["Rows"] == "6424"
    assert by_dataset["Historical Tuning V3 substrate"]["Rows"] == "5518"
    assert by_dataset["Source Contract V1"]["Rows"] == "18 allowed / 4 null-fenced / 11 blocked"
    assert {row["Safe use"] for row in rows}
    assert all(row["Source path"].startswith("docs/hq/") for row in rows)


def test_candidate_review_panel_keeps_usage_opportunity_volume_on_hold() -> None:
    rows = candidate_review_panel_rows()
    by_item = {row["Review item"]: row for row in rows}

    assert by_item["Current candidate"]["Value"] == "usage_opportunity_volume"
    assert by_item["Current candidate"]["Status"] == "HOLD"
    assert by_item["Useful rescue variant"]["Value"] == "qb_guard_soft_blend"
    assert by_item["Partial refinement variant"]["Value"] == "rb_wr_cutline_safe_blend"
    assert by_item["Targeted redesign variant"]["Value"] == (
        "wr_boundary_breakout_sensitivity_guard"
    )
    assert by_item["Targeted redesign variant"]["Status"] == (
        "TARGETED_REDESIGN_FOR_HUMAN_REVIEW_ONLY"
    )
    assert by_item["Production approval"]["Value"] == "Not approved"
    assert by_item["Known risks"]["Status"] == "5 remaining cutline rows"


def test_guardrail_ledger_blocks_fields_and_production_behavior() -> None:
    text = "\n".join(str(row) for row in guardrail_ledger_rows())

    assert "Routes, TPRR, YPRR" in text
    assert "ambiguous rz_att" in text
    assert "source truth" in text
    assert "hidden sort" in text
    assert "default app behavior" in text


def test_current_stats_options_are_descriptive_review_only() -> None:
    rows = current_stats_review_improvement_rows()
    labels = {row["Review-only improvement"] for row in rows}

    assert "Player usage trend summaries" in labels
    assert "Opportunity and touch context" in labels
    assert "Snap share context where fenced" in labels
    assert "First-down scoring context" in labels
    assert "Red-zone context as sidecar only" in labels
    assert {row["Allowed output"] for row in rows} == {"Descriptive summary only"}
    assert all("No automatic decision" in row["Blocked output"] for row in rows)


def test_next_lane_panel_is_ideas_only() -> None:
    rows = next_lane_idea_rows()
    allowed_guardrail_starts = (
        "No auto action",
        "Descriptive context only",
        "Sidecar only",
        "Fixed review definitions only",
    )

    assert rows
    assert {row["Status"] for row in rows} == {"IDEA_ONLY"}
    assert all(
        row["Guardrail"].startswith(allowed_guardrail_starts)
        or row["Guardrail"].startswith("Human review only")
        for row in rows
    )


def test_research_tools_page_wires_review_cockpit_sections() -> None:
    text = Path("app/pages/35_development_lab_v1.py").read_text(encoding="utf-8")

    assert "Research Status Board" in text
    assert "Dataset Browser" in text
    assert "Candidate Review Panel" in text
    assert "Guardrail Ledger" in text
    assert "What Can Be Improved With Current Stats" in text
    assert "Next-Lane Ideas" in text
    assert "render_review_upgrade_status_board" in text
    assert "render_review_upgrade_dataset_browser" in text
    assert "render_review_upgrade_candidate_panel" in text


def test_review_upgrade_app_text_avoids_active_decision_language() -> None:
    paths = [
        Path("app/components/development_lab.py"),
        Path("app/pages/35_development_lab_v1.py"),
        Path("src/services/development_lab_review_upgrade_service.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    text = text.replace("not a model score", "ngs quarantine label")

    blocked_phrase_parts = (
        ("valu", "ation"),
        ("model ", "score"),
        ("hidden ", "decision logic"),
        ("production", "-approved"),
        ("source-truth ", "promotion"),
        ("candidate formula output ", "wired"),
    )
    for blocked_phrase in ("".join(parts) for parts in blocked_phrase_parts):
        assert blocked_phrase not in text
    assert "review-only" in text
    assert "display-only" in text


def test_artifact_manifest_rows_are_tracked_docs_only() -> None:
    rows = artifact_manifest_rows()
    status = lab_status_board_rows()

    assert rows
    assert all(row["Tracked"] == "yes" for row in rows)
    assert all(row["Path"].startswith("docs/hq/") for row in rows)
    assert any(row["Artifact"] == "Targeted Redesign V1" for row in rows)
    assert any(row["Area"] == "Guardrail status" for row in status)
