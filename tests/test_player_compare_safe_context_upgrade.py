from __future__ import annotations

from pathlib import Path

from src.services.player_compare_decision_service import (
    MARKET_DISPLAY_ONLY_NOTE,
    NFLVERSE_WAIT_STATUS,
    NOT_ENOUGH_INFORMATION,
    build_player_compare_decision_summary,
    nflverse_spec_panel_rows,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "pages" / "22_player_compare_v1.py"
NAV = ROOT / "app" / "navigation.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _player(name: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "player": name,
        "position": "WR",
        "dynasty_asset_rank": "",
        "cross_asset_candidate_rank": "",
        "final_board_rank": "",
        "age": "",
        "outcome_applicable_summary": NOT_ENOUGH_INFORMATION,
        "available_pool_adp_range": NOT_ENOUGH_INFORMATION,
    }
    row.update(overrides)
    return row


def test_player_compare_route_and_visible_context_copy_are_present() -> None:
    page = _read(PAGE)
    nav = _read(NAV)

    assert 'url_path="player-compare"' in nav
    assert 'file_path="pages/22_player_compare_v1.py"' in nav
    assert "Visible Context Summary" in page
    assert "Visible-context read" in page
    assert "Evidence coverage" in page
    assert "Player Compare shows visible context only" in page
    assert "Decision Summary" not in page
    assert 'metric("Lean"' not in page
    assert 'metric("Confidence"' not in page


def test_page_renames_judgment_like_plain_language_fields() -> None:
    page = _read(PAGE)

    required = [
        "Stability evidence",
        "Ceiling evidence",
        "Roster-window context",
        "Main review flags",
    ]
    for term in required:
        assert term in page

    forbidden = [
        "Safer profile",
        "Upside profile",
        "Timing / window",
        "Main risk",
    ]
    for term in forbidden:
        assert term not in page


def test_cross_position_and_multi_player_outputs_do_not_recommend() -> None:
    cross = build_player_compare_decision_summary(
        _player("Wideout", position="WR", dynasty_asset_rank="1"),
        _player("Runner", position="RB", dynasty_asset_rank="40"),
    )
    multi = build_player_compare_decision_summary(
        _player("Player A", dynasty_asset_rank="1"),
        _player("Player B", dynasty_asset_rank="2"),
        [_player("Player C", dynasty_asset_rank="3"), _player("Player D", dynasty_asset_rank="4")],
    )

    assert cross.visible_context_read == "Different positions / roster-fit decision"
    assert "final ranking or recommendation" in multi.multi_player_note
    combined = " ".join(
        [
            cross.visible_context_read,
            *cross.context_bullets,
            multi.visible_context_read,
            *multi.context_bullets,
        ]
    )
    assert "Prefer " not in combined
    assert "Winner" not in combined
    assert "Better asset" not in combined


def test_missing_data_and_missing_injury_context_copy_stay_neutral() -> None:
    page = _read(PAGE)
    summary = build_player_compare_decision_summary(_player("A"), _player("B"))

    assert summary.visible_context_read == NOT_ENOUGH_INFORMATION
    assert NOT_ENOUGH_INFORMATION in " ".join(summary.open_review_flags)
    assert "No approved injury context available does not mean clean health." in page
    assert "healthy" not in page.lower()
    assert "clean health" in page


def test_market_context_is_separate_and_not_a_top_flag() -> None:
    page = _read(PAGE)
    summary = build_player_compare_decision_summary(
        _player("Player A", available_pool_adp_range="Early"),
        _player("Player B", available_pool_adp_range="Late"),
    )

    assert "Market timing context" in page
    assert "MARKET_DISPLAY_ONLY_NOTE" in page
    assert summary.display_only_market_note == MARKET_DISPLAY_ONLY_NOTE
    assert not any("market" in flag.lower() for flag in summary.open_review_flags)
    assert "no market match" not in page
    assert "current_pick_value" not in page


def test_injury_language_blocks_medical_projection_and_risk_scoring() -> None:
    page = _read(PAGE)
    normalized_page = " ".join(page.split())

    assert "No medical projection or injury-risk score is made." in page
    assert "It does not project recovery, estimate" in normalized_page
    assert "injury risk, or change rankings." in normalized_page
    assert "Missing injury context does not mean clean health." in normalized_page
    for forbidden in ("injury-prone", "comeback odds", "recovery projection"):
        assert forbidden not in page


def test_identity_fallback_and_nflverse_panels_are_disabled_spec_only() -> None:
    page = _read(PAGE)
    rows = nflverse_spec_panel_rows()

    assert "Name + position fallback" in page
    assert "not treated as deterministic identity truth" in page
    assert "Ambiguous name + position fallback" in page
    assert "NFLVerse Specs / Disabled" in page
    assert {row["Status"] for row in rows} == {NFLVERSE_WAIT_STATUS}
    assert "Spec-only / disabled until the NFLVerse refresh-health lane lands" in page


def test_player_compare_lane_does_not_touch_protected_paths() -> None:
    changed_allowed = {
        "app/pages/22_player_compare_v1.py",
        "src/services/player_compare_decision_service.py",
        "tests/test_player_compare_decision_service.py",
        "tests/test_original_doc_remaining_ux_tools.py",
        "tests/test_player_compare_safe_context_upgrade.py",
        "docs/hq/player_compare_safe_context_ux_upgrade_20260630/manifest.md",
        "docs/hq/player_compare_safe_context_ux_upgrade_20260630/player_compare_change_classification.csv",
        "docs/hq/player_compare_safe_context_ux_upgrade_20260630/dataset_dependency_matrix.csv",
        "docs/hq/player_compare_safe_context_ux_upgrade_20260630/player_compare_safe_context_ux_upgrade_summary.md",
        "docs/hq/player_compare_safe_context_ux_upgrade_20260630/guardrail_report.md",
        "docs/hq/player_compare_safe_context_ux_upgrade_20260630/test_report.md",
    }
    assert changed_allowed
