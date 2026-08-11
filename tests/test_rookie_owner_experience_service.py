from __future__ import annotations

from pathlib import Path

from src.services.rookie_owner_experience_service import (
    load_owner_rookie_board,
    rookie_component_rows,
)


def test_named_owner_cases_explain_rank_score_and_identity_without_mutation() -> None:
    board = load_owner_rookie_board()
    by_name = {row["player_name"]: row for row in board.to_dict("records")}

    carnell = by_name["Carnell Tate"]
    assert carnell["Rank"] == "8"
    assert "NFL draft capital is one component" in carnell["Why this rank"]
    assert carnell["Blocked / pending reason"] == ""

    kc = by_name["KC Concepcion"]
    assert float(kc["Review Score"]) > float(kc["Board Score"])
    assert "Board Score" in kc["Why this rank"]
    assert "Review Score" in kc["Why this rank"]

    stribling = by_name["De'Zhaun Stribling"]
    assert stribling["Rank"] == "—"
    assert "00-0041035" in stribling["Blocked / pending reason"]
    assert "does not invent a score or rank" in stribling["Blocked / pending reason"]

    components = rookie_component_rows(carnell)
    assert set(components["Model effect"]) <= {
        "HELPED",
        "NEUTRAL",
        "HURT",
        "Unavailable",
    }


def test_rookie_page_puts_warnings_last_and_uses_owner_language() -> None:
    page = (
        Path(__file__).resolve().parents[1] / "app/pages/48_rookie_board_review_v1.py"
    ).read_text(encoding="utf-8")
    assert "Why is this rookie here?" in page
    assert "Rookie draft range" in page
    assert "Rookie Tier" in page
    assert "Warnings and advanced model details" in page
    assert page.index("Warnings and advanced model details") > page.index('"Confidence",')
    assert "first_round_board_context_review" not in page
