from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.navigation import ALL_NAVIGATION_PAGES, NavigationPageSpec
from tests.ui_contract_harness import (
    ImportedSymbol,
    assert_page_header_title,
    assert_routes_resolve_to,
    module_string_literals,
    replace_only_imported_call_argument,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"
CANONICAL_PLAYER_BOARD_FILE = "pages/20_final_board_v1.py"
PLAYER_BOARD_ROUTES = ("/rankings", "/player-board")
PAGE_HEADER = ImportedSymbol("app.components.ui_framework", "page_header")
CURRENT_PLAYER_BOARD_LABELS = frozenset(
    {
        "Dynasty Rankings",
        "Dynasty Review",
        "Market Context",
        "Ranking Context",
        "Search player",
        "Position",
        "Player type",
        "Sort by",
        "Advanced filters",
        "Review needed",
        "Board evidence trust",
    }
)


def _routes_with_target(route: str, file_path: str) -> tuple[NavigationPageSpec, ...]:
    route_name = route.strip("/")
    assert sum(spec.url_path == route_name for spec in ALL_NAVIGATION_PAGES) == 1
    return tuple(
        replace(spec, file_path=file_path) if spec.url_path == route_name else spec
        for spec in ALL_NAVIGATION_PAGES
    )


def _assert_player_board_contract(
    *,
    routes: tuple[NavigationPageSpec, ...] = ALL_NAVIGATION_PAGES,
    source_overrides: dict[str, str] | None = None,
) -> None:
    resolved_routes = assert_routes_resolve_to(
        PLAYER_BOARD_ROUTES,
        CANONICAL_PLAYER_BOARD_FILE,
        routes=routes,
        repo_root=ROOT,
        source_overrides=source_overrides,
    )
    for resolved in resolved_routes:
        assert_page_header_title(resolved, "Dynasty Rankings")
        missing_labels = CURRENT_PLAYER_BOARD_LABELS - module_string_literals(resolved)
        assert not missing_labels, (
            f"route {resolved.route} is missing current Player Board labels: "
            f"{sorted(missing_labels)}"
        )


def test_player_board_ux_smoke_checklist_covers_source_routing_sentinels() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv",
        "checkpoint_review_score",
        "legacy_active_pack_score",
        "review_v4_current_player",
        "Keenan Allen",
        "41.6097",
        "82.4",
        "Darius Slayton",
        "78.88",
        "fail-closed",
        "Score Source File",
        "Score Column",
        "Score Lineage",
        "Trust Cap",
        "Warnings",
    ]

    for term in required_terms:
        assert term in text


def test_player_board_ux_smoke_checklist_covers_manual_filter_and_display_only_flows() -> None:
    text = REPORT.read_text(encoding="utf-8")

    required_terms = [
        "Position filter",
        "Owner filter",
        "Min Model Value",
        "Show audit-watch warnings only",
        "Search by player",
        "Inspect player",
        "Market Context (Read-Only)",
        "display-only",
        "Formula Components",
        "Advanced: raw formula fields",
        "Audit Watchlist",
        "TE No-Premium Review",
        "Evidence Capture Worksheet",
    ]

    for term in required_terms:
        assert term in text


def test_player_board_ux_smoke_checklist_preserves_review_only_guardrails() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "Do not tune formulas from this checklist." in text
    assert "Do not use this checklist as proof the model is ready for money decisions." in text
    assert "does not tune formulas, change generated outputs" in text
    assert "must not issue final trade, cut, keep" in text
    assert "Do not edit active rankings" in text
    assert "My Team, War Board" in text


def test_player_board_page_contains_ui_labels_referenced_by_checklist() -> None:
    _assert_player_board_contract()


def test_player_board_negative_control_rejects_wrong_player_board_route() -> None:
    routes = _routes_with_target("/player-board", "pages/05_rankings.py")

    with pytest.raises(AssertionError, match=r"route /player-board resolved to"):
        _assert_player_board_contract(routes=routes)


def test_player_board_negative_control_rejects_wrong_rankings_route() -> None:
    routes = _routes_with_target("/rankings", "pages/05_rankings.py")

    with pytest.raises(AssertionError, match=r"route /rankings resolved to"):
        _assert_player_board_contract(routes=routes)


def test_player_board_negative_control_rejects_missing_routed_title() -> None:
    page_path = ROOT / "app" / CANONICAL_PLAYER_BOARD_FILE
    source = page_path.read_text(encoding="utf-8")
    without_title = replace_only_imported_call_argument(
        source,
        page_path,
        PAGE_HEADER,
        0,
        repr("Removed Rankings Title"),
    )

    with pytest.raises(AssertionError, match="page_header title"):
        _assert_player_board_contract(
            source_overrides={CANONICAL_PLAYER_BOARD_FILE: without_title}
        )


def test_player_board_negative_control_rejects_title_only_in_unrelated_file() -> None:
    page_path = ROOT / "app" / CANONICAL_PLAYER_BOARD_FILE
    source = page_path.read_text(encoding="utf-8")
    without_title = replace_only_imported_call_argument(
        source,
        page_path,
        PAGE_HEADER,
        0,
        repr("Removed Rankings Title"),
    )
    unrelated_source = 'UNRELATED_TITLE = "Dynasty Rankings"\n'

    with pytest.raises(AssertionError, match="page_header title"):
        _assert_player_board_contract(
            source_overrides={
                CANONICAL_PLAYER_BOARD_FILE: without_title,
                "pages/05_rankings.py": unrelated_source,
            }
        )


@pytest.mark.parametrize("missing_route", PLAYER_BOARD_ROUTES)
def test_player_board_negative_control_rejects_missing_route_alias(
    missing_route: str,
) -> None:
    route_name = missing_route.strip("/")
    routes = tuple(spec for spec in ALL_NAVIGATION_PAGES if spec.url_path != route_name)

    with pytest.raises(AssertionError, match=rf"route {missing_route} is not declared"):
        _assert_player_board_contract(routes=routes)


def test_refinement_queue_marks_r18_done_with_audit_note() -> None:
    queue = QUEUE.read_text(encoding="utf-8")

    assert "| R18 | Player Board UX smoke checklist |" in queue
    r18_line = next(line for line in queue.splitlines() if line.startswith("| R18 |"))
    assert "| Done |" in r18_line
    assert "PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md" in r18_line
    assert "filters, score disclosure, warnings, named-player traceability" in r18_line
