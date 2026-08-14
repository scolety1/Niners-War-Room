from __future__ import annotations

from pathlib import Path

from src.services.rookie_draft_eligibility_service import (
    load_rookie_draft_eligibility_overlay,
)
from src.services.rookie_owner_experience_service import (
    load_owner_rookie_board,
    rookie_component_rows,
)


def test_named_owner_cases_explain_rank_score_and_identity_without_mutation() -> None:
    eligibility = load_rookie_draft_eligibility_overlay()
    board = load_owner_rookie_board(eligibility_rows=eligibility.rows)
    by_name = {row["player_name"]: row for row in board.to_dict("records")}

    carnell = by_name["Carnell Tate"]
    assert carnell["Rank"] == "8"
    assert "NFL draft capital is one component" in carnell["Why this rank"]
    assert "Admitted component context" in carnell["Why this rank"]
    assert carnell["Unified Research"] == "Research neighborhood 1"
    assert carnell["NWR Expected"] == "Research neighborhood 1"
    assert carnell["Blocked / pending reason"] == ""

    kc = by_name["KC Concepcion"]
    assert float(kc["Review Score"]) > float(kc["Board Score"])
    assert "Board Score" in kc["Why this rank"]
    assert "Review Score" in kc["Why this rank"]
    assert "confidence cap is 0.84" in kc["Why this rank"]
    assert "Missing components" in kc["Why this rank"]

    stribling = by_name["De'Zhaun Stribling"]
    assert stribling["Rank"] == "—"
    assert stribling["Live Player ID"] == "00-0041035"
    assert stribling["NFL Team"] == "SF"
    assert stribling["Draft Eligibility"] == "Draft eligible"
    assert stribling["Score Status"].startswith("No admitted Rookie Review score")
    assert stribling["Selectable"] is True
    assert stribling["Model Score Eligible"] is False
    assert "no replacement score or rank was invented" in stribling["Blocked / pending reason"]

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
    assert "NWR Rookie Score" in page
    assert "College Production" in page
    assert "Unified Research" in page
    assert '"Warnings / pending",' in page
    assert "Warnings and advanced model details" in page
    assert page.index("Warnings and advanced model details") > page.index('"Confidence",')
    assert "first_round_board_context_review" not in page
