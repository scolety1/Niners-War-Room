from __future__ import annotations

from pathlib import Path

from app.navigation import ALL_NAVIGATION_PAGES
from src.services.unified_player_universe_review_page_service import (
    BLOCKER_TABLE_COLUMNS,
    CONSOLIDATION_TABLE_COLUMNS,
    REVIEW_TABLE_COLUMNS,
    filter_blockers,
    filter_review_table,
    load_unified_universe_review_data,
    table_columns,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE_PATH = REPO_ROOT / "app" / "pages" / "31_unified_universe_review_v1.py"


def test_review_page_service_loads_consolidated_artifact() -> None:
    data = load_unified_universe_review_data()

    assert len(data.consolidated) == 368
    assert len(data.blockers) == 310
    assert len(data.consolidation_decisions) == 15


def test_review_page_summary_counts_match_artifact() -> None:
    data = load_unified_universe_review_data()
    summary = data.summary

    assert summary["consolidated_row_count"] == 368
    assert summary["veteran_count"] == 240
    assert summary["rookie_prospect_count"] == 54
    assert summary["pdf_fa_count"] == 74
    assert summary["blocker_count"] == 310
    assert summary["review_needed_count"] == 248


def test_review_page_blocker_counts_load() -> None:
    data = load_unified_universe_review_data()
    missing_ids = filter_blockers(data.blockers, blocker_types=["MISSING_PLAYER_ID"])
    missing_ages = filter_blockers(data.blockers, blocker_types=["MISSING_AGE"])

    assert len(missing_ids) == 5
    assert len(missing_ages) == 42
    assert set(BLOCKER_TABLE_COLUMNS).issubset(data.blockers.columns)


def test_review_page_filters_do_not_drop_all_rows_unexpectedly() -> None:
    data = load_unified_universe_review_data()

    veterans = filter_review_table(data.consolidated, player_types=["VETERAN"])
    wide_receivers = filter_review_table(data.consolidated, positions=["WR"])
    pdf_layer = filter_review_table(
        data.consolidated,
        source_layers=["PDF Free-Agent Availability Layer"],
    )

    assert len(veterans) > 0
    assert len(wide_receivers) > 0
    assert len(pdf_layer) > 0


def test_review_page_gates_remain_no() -> None:
    data = load_unified_universe_review_data()

    assert data.consolidated["app_wiring_allowed"].eq("no").all()
    assert data.consolidated["model_input_allowed"].eq("no").all()
    assert data.summary["app_wiring_allowed"] == "no"
    assert data.summary["model_input_allowed"] == "no"


def test_missing_age_and_player_id_blockers_are_visible() -> None:
    data = load_unified_universe_review_data()

    assert data.summary["missing_player_id_count"] == 5
    assert data.summary["missing_age_count"] == 42
    assert data.blockers["blocker_type"].eq("MISSING_PLAYER_ID").any()
    assert data.blockers["blocker_type"].eq("MISSING_AGE").any()


def test_duplicate_consolidation_table_loads() -> None:
    data = load_unified_universe_review_data()

    assert set(CONSOLIDATION_TABLE_COLUMNS).issubset(data.consolidation_decisions.columns)
    assert data.consolidation_decisions["decision"].eq("CONSOLIDATE").all()
    assert data.consolidation_decisions["conflicts"].eq("").all()


def test_review_table_columns_are_available() -> None:
    data = load_unified_universe_review_data()
    display = table_columns(data.consolidated, REVIEW_TABLE_COLUMNS)

    assert list(display.columns) == REVIEW_TABLE_COLUMNS


def test_unified_universe_review_route_is_registered_hidden() -> None:
    specs = {spec.url_path: spec for spec in ALL_NAVIGATION_PAGES}

    assert "unified-universe-review" in specs
    assert specs["unified-universe-review"].file_path == "pages/31_unified_universe_review_v1.py"
    assert specs["unified-universe-review"].visible is False


def test_review_page_copy_preserves_review_only_guardrails() -> None:
    page_text = PAGE_PATH.read_text(encoding="utf-8")

    assert "Review-only. Not used by rankings, model, or Drafting Mode." in page_text
    assert "It does not change rankings." in page_text
    assert "It does not change model inputs." in page_text
    assert "It does not approve app wiring." in page_text
    assert "Market data remains display-only." in page_text
    assert "Missing Outcome means Not enough information, not low probability." in page_text
