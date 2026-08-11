from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANKINGS_PAGE = ROOT / "app" / "pages" / "20_final_board_v1.py"
COMPARE_PAGE = ROOT / "app" / "pages" / "22_player_compare_v1.py"
NAVIGATION = ROOT / "app" / "navigation.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_source(path: Path, name: str) -> str:
    source = _source(path)
    tree = ast.parse(source)
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(matches) == 1
    return ast.get_source_segment(source, matches[0]) or ""


def test_rankings_v3_lens_is_compact_named_and_sort_independent() -> None:
    page = _source(RANKINGS_PAGE)
    function = _function_source(RANKINGS_PAGE, "_render_outcome_v3_compact_lens")

    assert '"Outcome V3 position"' in function
    assert '"Outcome V3 threshold"' in function
    assert "rankings_outcome_v3_rows(" in function
    assert 'rows["Horizon"].drop_duplicates().astype(str).tolist()' in function
    assert "2026, 2027, 2028" not in function
    assert "Two Qualifying Seasons Within 3 Years" not in function
    assert '"Calibration status"' in function
    assert '"Historical sample"' in function
    assert '"Missing-state explanation"' in function
    assert "rank_use_allowed" not in function
    assert "sort_values(" not in function
    assert "_sort_player_board(" not in function
    assert (
        "if preset == VIEW_PRESET_OUTCOME_CONTEXT:\n"
        "    _render_outcome_v3_compact_lens(filtered_board)"
    ) in page
    assert "_render_outcome_lens_status(unified_board)" not in page


def test_player_compare_v3_is_expanded_and_keeps_legacy_compatibility() -> None:
    page = _source(COMPARE_PAGE)
    function = _function_source(COMPARE_PAGE, "_render_outcome_v3_compare")

    assert "player_compare_outcome_v3_rows(compare_frame, artifact.frame)" in function
    assert 'rows["Horizon"].drop_duplicates().astype(str).tolist()' in function
    assert "2026, 2027, 2028" not in function
    assert "Exact player_id joins only" in function
    assert '"Calibration status"' in function
    assert '"Historical sample"' in function
    assert '"Confidence"' in function
    assert '"Missing-state explanation"' in function
    assert "_render_outcome_v3_compare(compare)" in page
    assert '"Legacy Outcome compatibility context"' in page
    assert "_render_position_aware_outcome_compare(" in page


def test_outcome_v3_ui_exposes_version_and_distinct_missing_states() -> None:
    combined = _source(RANKINGS_PAGE) + _source(COMPARE_PAGE)

    assert combined.count("NWR_OUTCOME_COLUMNS_V3_RC1") >= 2
    assert "Wrong-position is N/A" in combined
    assert "Not enough information" in combined
    assert "blocked or insufficient applicable evidence" in combined


def test_outcome_v3_routes_resolve_without_new_aliases_or_route_replacement() -> None:
    navigation = _source(NAVIGATION)

    assert 'url_path="rankings"' in navigation
    assert 'file_path="pages/20_final_board_v1.py"' in navigation
    assert 'url_path="player-compare"' in navigation
    assert 'file_path="pages/22_player_compare_v1.py"' in navigation


def test_outcome_v3_render_functions_have_no_durable_write_path() -> None:
    combined = "\n".join(
        [
            _function_source(RANKINGS_PAGE, "_render_outcome_v3_compact_lens"),
            _function_source(COMPARE_PAGE, "_render_outcome_v3_compare"),
        ]
    )
    forbidden = (
        "write_text(",
        "write_bytes(",
        "to_csv(",
        "to_json(",
        "mkdir(",
        "unlink(",
        "replace(",
        "latest_candidate",
        "latest_approved",
    )
    for token in forbidden:
        assert token not in combined
