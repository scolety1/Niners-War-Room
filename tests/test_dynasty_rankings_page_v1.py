from __future__ import annotations

import ast
from pathlib import Path

PAGE = Path("app/pages/20_final_board_v1.py")


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


def test_rankings_full_view_position_filter_defaults_to_fantasy_positions() -> None:
    text = _page_text()

    assert _constant_tuple("BASE_POSITION_FILTERS") == ("QB", "RB", "WR", "TE")
    assert "default_positions = position_values" in text
    assert 'position != "K"' not in text


def test_rankings_full_view_sort_options_do_not_foreground_draft_board_rank() -> None:
    text = _page_text()

    assert 'if view_mode == FULL_DYNASTY_VIEW:' in text
    assert 'return ["Dynasty Rank", "Position Rank", "Age", "Player"]' in text
    assert '"Candidate Rank (Review-Only)"' in text
    assert 'if sort_by == "Position Rank" and view_mode != FULL_DYNASTY_VIEW:' in text


def test_rankings_full_view_source_filter_keeps_frozen_board_optional() -> None:
    text = _page_text()

    assert 'options = ["All", "Rookies / prospects", "Veterans", "Full Dynasty source"]' in text
    assert "if view_mode != FULL_DYNASTY_VIEW:" in text
    assert 'options.append("Frozen Baseline only")' in text
