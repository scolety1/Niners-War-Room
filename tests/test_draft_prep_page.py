from __future__ import annotations

import ast
from pathlib import Path

PAGE = Path("app/pages/06_draft_board.py")
NAVIGATION = Path("app/navigation.py")


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


def _constant_tuple(name: str) -> tuple[str, ...]:
    tree = ast.parse(_page_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = ast.literal_eval(node.value)
                    return tuple(value)
    raise AssertionError(f"{name} not found")


def test_draft_prep_page_is_product_first() -> None:
    text = _page_text()

    assert 'st.title("Draft Prep")' in text
    assert "Scouting prep mode:" in text
    assert "Final legal draft pool" in text
    assert "pending dropped-player data" in text
    assert "Best Options Right Now" not in text
    assert "Mock Save / Load" not in text


def test_draft_prep_uses_scouting_pool_and_readiness_outputs() -> None:
    text = _page_text()

    assert "scouting_prep_pool_review_rows.csv" in text
    assert "draftable_pool_source_readiness.csv" in text
    assert "prior_league_draft_behavior_summary.csv" in text
    assert "prior_league_draft_history_review_rows.csv" in text
    assert "Confirmed legal pool not ready; scouting prep pool available." in text


def test_draft_prep_wires_shared_player_detail_card() -> None:
    text = _page_text()

    assert "from app.components.player_detail_card import render_player_detail_card" in text
    assert (
        "from src.services.player_detail_card_service import "
        "build_player_detail_card_payload"
    ) in text
    assert '"Scouting player detail"' in text
    assert "Player Detail Card:" in text
    assert 'build_player_detail_card_payload(detail_row.to_dict(), context="draft_prep")' in text
    assert "render_player_detail_card(payload)" in text


def test_owned_pick_cards_include_no_baseline_504() -> None:
    text = _page_text()

    assert _constant_tuple("OWNED_PICK_LABELS") == (
        "2026 1.03",
        "2026 1.04",
        "2026 2.04",
        "2026 2.08",
        "2026 5.04",
    )
    assert "No Baseline" in text
    assert "Manual late-round watchlist; no exact equivalence." in text
    assert "no admitted exact baseline" in text


def test_scouting_pool_table_uses_conservative_columns() -> None:
    assert ast.literal_eval(
        next(
            node.value
            for node in ast.parse(_page_text()).body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id == "SCOUTING_PREP_COLUMNS"
        )
    ) == [
        "Player",
        "Pos",
        "NFL Team",
        "Source Type",
        "Draftable Status",
        "NWR Draft Value / Rookie Score",
        "Trust",
        "Warnings",
        "Data Needed",
        "Pick Window / Fit Band",
        "Context Notes",
    ]


def test_legal_status_and_history_are_context_only() -> None:
    text = _page_text()

    assert "Free-Agent/Veteran Preview" in text
    assert "Rookie Scouting Prep" in text
    assert "Scouting Only / Legal Pool Pending" in text
    assert "prior draft history, and spreadsheet highlights are context-only" in text
    assert "do not alter NWR Draft Value or private player value" in text
    assert "Yellow spreadsheet context means must review at cost" in text
    assert "not a final" in text
    assert "selection instruction" in text


def test_live_tools_are_collapsed_and_decision_board_not_referenced() -> None:
    text = _page_text()

    assert "Live Draft Room tools moved" in text
    assert "Open Live Draft Room" in text
    assert "does not mutate draft state" in text
    assert "Decision Board" not in text


def test_flex_filter_excludes_qb() -> None:
    text = _page_text()

    assert 'FLEX_POSITIONS = {"RB", "WR", "TE"}' in text
    assert "FLEX means RB + WR + TE only. QB is excluded." in text


def test_visible_navigation_uses_draft_prep_label() -> None:
    text = NAVIGATION.read_text(encoding="utf-8")

    assert 'title="Draft Prep"' in text
    assert 'url_path="draft-room"' in text
    assert 'title="Live Draft Room"' in text
    assert 'url_path="live-draft-room"' in text


def test_draft_prep_avoids_forbidden_recommendation_copy() -> None:
    text = _page_text().lower()

    for forbidden in (
        "draft this player",
        "target this player",
        "must draft no matter what",
        "trade for",
        "sell",
        "cut",
        "defer",
    ):
        assert forbidden not in text
