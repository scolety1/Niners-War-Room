from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.services.draft_day_player_context_service import (
    AS_OF_LABEL,
    DISPLAY_STATUS,
    draft_day_player_context_for_player,
)


def test_context_service_returns_unavailable_when_artifact_is_missing(tmp_path: Path) -> None:
    result = draft_day_player_context_for_player(
        "9493",
        artifact_path=tmp_path / "missing.csv",
        schema_path=tmp_path / "missing_schema.csv",
    )

    assert result.status == "unavailable"
    assert result.message == "Not enough information"
    assert result.sections[0].rows[1] == ("Status", "Not enough information")


def test_context_service_returns_display_only_cards_for_safe_identity_row() -> None:
    result = draft_day_player_context_for_player("9493")

    assert result.available
    assert result.source == "NFLVerse player context display artifact"
    assert result.as_of == AS_OF_LABEL
    assert {section.title for section in result.sections} >= {
        "Identity / Status",
        "Availability Context",
        "Role / Depth Context",
        "Production / Activity Context",
        "Draft Capital Context",
        "Contract Context",
        "Schedule Context",
    }
    identity_rows = dict(result.sections[0].rows)
    assert identity_rows["NWR player id"] == "9493"
    assert identity_rows["Display status"] == DISPLAY_STATUS
    assert identity_rows["Source"] == "NFLVerse player context display artifact"
    assert identity_rows["As of"] == AS_OF_LABEL


def test_identity_review_row_does_not_expose_nflverse_details() -> None:
    artifact = pd.read_csv(
        "docs/hq/data_sources/nflverse_player_context_display_20260630/"
        "nflverse_player_context_display_artifact.csv",
        dtype=str,
    ).fillna("")
    review_row = artifact.loc[
        artifact["identity_join_status"].eq("NEED_IDENTITY_REVIEW")
    ].iloc[0]

    result = draft_day_player_context_for_player(review_row["nwr_player_id"])

    assert result.status == "needs_identity_review"
    assert result.message == "Needs identity review"
    rows = dict(result.sections[0].rows)
    assert rows["Identity status"] == "Needs identity review"
    assert "NFLVerse GSIS id" not in rows
    assert "Roster status" not in rows


def test_schedule_context_remains_unavailable() -> None:
    result = draft_day_player_context_for_player("9493")

    schedule = next(section for section in result.sections if section.title == "Schedule Context")
    rows = dict(schedule.rows)
    assert rows["Next game"] == "Not enough information"
    assert rows["Opponent"] == "Not enough information"
    assert rows["Bye"] == "Not enough information"
    assert rows["Reason"] == "Current artifact has no current/future safe schedule rows."


def test_context_service_does_not_mutate_runtime_json(tmp_path: Path) -> None:
    runtime_state = tmp_path / "draft_state.json"
    runtime_state.write_text(json.dumps({"assignments": [], "events": []}), encoding="utf-8")
    before = runtime_state.read_text(encoding="utf-8")

    result = draft_day_player_context_for_player("9493")

    assert result.available
    assert runtime_state.read_text(encoding="utf-8") == before


def test_missing_values_are_not_interpreted_as_negative_evidence() -> None:
    result = draft_day_player_context_for_player("9493")
    text = "\n".join(
        value
        for section in result.sections
        for _label, value in section.rows
    ).lower()

    assert "healthy" not in text
    assert "no-role" not in text
    assert "zero" not in text
    assert "udfa" not in text
    assert "injury risk" not in text
