from __future__ import annotations

import ast
from pathlib import Path

PAGE = Path("app/pages/05_rankings.py")


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


def _constant_list(name: str) -> list[str]:
    tree = ast.parse(_page_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = ast.literal_eval(node.value)
                    return list(value)
    raise AssertionError(f"{name} not found")


def test_dynasty_rankings_default_columns_are_product_first() -> None:
    assert _constant_list("DEFAULT_DYNASTY_COLUMNS") == [
        "Rank",
        "Player",
        "Pos",
        "Age",
        "Team",
        "NWR Dynasty Score",
        "Trust",
        "Warnings",
        "Market Rank",
        "NWR vs Market",
        "League Rank",
        "NWR vs League",
        "Status",
        "Data Needed",
    ]


def test_my_team_is_badge_and_highlight_not_separate_column() -> None:
    text = _page_text()

    assert '"My Team"' not in _constant_list("DEFAULT_DYNASTY_COLUMNS")
    assert "[MY TEAM]" in text
    assert "background-color: #fff8e6" in text


def test_flex_filter_excludes_qb_and_includes_rb_wr_te() -> None:
    text = _page_text()

    assert 'FLEX_POSITIONS = {"RB", "WR", "TE"}' in text
    assert "FLEX means RB + WR + TE only. QB is excluded" in text


def test_outcome_columns_are_present_without_fake_percentages() -> None:
    text = _page_text()

    for label in (
        "T6 2026",
        "T12 2026",
        "T48 2026",
        "T6 2027",
        "T48 2027",
        "T6 5Y",
        "T48 5Y",
    ):
        assert label in text
    assert "Outcome percentage model in development" in text
    assert "display_row[outcome_column] = \"—\"" in text


def test_market_and_league_context_are_display_only() -> None:
    text = _page_text()

    assert "Market Rank" in text
    assert "League Rank" in text
    assert "NWR vs Market" in text
    assert "NWR vs League" in text
    assert "display-only and never used in private NWR Dynasty Score" in text
    assert "dynasty_startup_adp" in text
    assert "league_rank" in text


def test_needs_data_language_replaces_manual_review_copy() -> None:
    text = _page_text()

    assert "Needs Data / No Private Score" in text
    assert "No Private Score" in text
    assert "Manual Review" not in text
    assert "No private NWR Dynasty Score is available." in text


def test_trust_and_status_are_split_for_scored_warning_rows() -> None:
    text = _page_text()

    assert "Scored + Warnings" in text
    assert "Capped Score" in text
    assert "Manual decision required" in text
    assert 'return "No Private Score"' in text
    assert 'statuses.append("NEEDS DATA")' not in text


def test_kickers_are_hidden_by_default_with_opt_in_toggle() -> None:
    text = _page_text()

    assert "Include K" in text
    assert "value=False" in text
    assert 'filtered["position"].astype(str).str.upper() != "K"' in text


def test_rankings_cache_keys_include_full_board_value_export() -> None:
    text = _page_text()

    assert "DEFAULT_FULL_PLAYER_BOARD_ROWS" in text
    assert "FULL_BOARD_VALUE_ROWS = REPO_ROOT / DEFAULT_FULL_PLAYER_BOARD_ROWS" in text
    assert "current_value_fingerprint" in text
    assert "path_fingerprint(FULL_BOARD_VALUE_ROWS)" in text
    assert "current_value_path=current_value_path" in text


def test_rankings_summary_counts_total_scores_and_hidden_kickers() -> None:
    text = _page_text()

    assert 'summary_cols[0].metric("Active players shown", len(default_visible_frame))' in text
    assert (
        'summary_cols[1].metric("NWR scored", '
        'int(formula_frame["nwr_rank"].astype(bool).sum()))'
    ) in text
    assert 'formula_frame[NWR_SCORE_COLUMN].map(_score_value).isna().sum()' in text


def test_rankings_detail_uses_shared_card_for_legacy_disclosure() -> None:
    text = _page_text()

    assert "build_player_detail_card_payload(row.to_dict(), context=\"rankings\")" in text
    assert "render_player_detail_card(payload)" in text
    assert "Legacy active-pack score:" not in text
    assert "Advanced source receipts and raw warnings" not in text
