from __future__ import annotations

from pathlib import Path

import pytest

from app.components.player_compare_accessibility import (
    PLAYER_COMPARE_COMPACT_BREAKPOINT_PX,
    PLAYER_COMPARE_MIN_TOUCH_TARGET_PX,
    PLAYER_COMPARE_NOT_SELECTED,
    PLAYER_COMPARE_REGION_ORDER,
    selected_player_context_rows,
)
from src.services.decision_trust_strip_service import (
    FIELD_ORDER,
    GATED,
    IDENTITY_EXCEPTION,
    MISSING,
    NOT_ENOUGH_INFORMATION,
    SOURCE_EXCEPTION,
    STALE,
    UNAVAILABLE,
    build_decision_trust_strip,
    state_from_existing_status,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "pages" / "22_player_compare_v1.py"
HELPER = ROOT / "app" / "components" / "player_compare_accessibility.py"
UI_FRAMEWORK = ROOT / "app" / "components" / "ui_framework.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _runtime_page_text() -> str:
    page = _text(PAGE)
    return page[page.index("render_player_compare_accessibility_frame()") :]


def test_accessible_selector_labels_and_slot_text_are_explicit() -> None:
    page = _runtime_page_text()
    helper = _text(HELPER)

    assert '"Player A selector"' in page
    assert '"Player B selector"' in page
    assert '"Optional extra players"' in page
    assert "Player A and Player B are named in text" in helper
    assert "Comparison-slot identity never depends" in helper
    assert '"on color alone."' in helper


def test_semantic_heading_and_region_order_follow_the_accessibility_contract() -> None:
    page = _runtime_page_text()
    helper = _text(HELPER)
    framework = _text(UI_FRAMEWORK)

    assert '<h1 class="nwr-title">{title}</h1>' in framework
    assert "nwr-player-compare-sr-only" not in helper
    assert PLAYER_COMPARE_REGION_ORDER == (
        "Player Compare",
        "Choose players",
        "Selected-player context",
        "Visible Context Summary",
        "Evidence caveats and trust context",
        "Secondary comparison details",
    )
    choose = page.index('st.markdown("## Choose players")')
    selectors = page.index("selector_cols = st.columns(2)")
    selected_context = page.index("render_selected_player_context(")
    primary = page.index("_render_visible_context_summary(compare)")
    trust_heading = page.index('st.markdown("## Evidence caveats and trust context")')
    trust = page.index("render_decision_trust_strips(", trust_heading)
    secondary = page.index('st.markdown("## Secondary comparison details")')
    tabs = page.index("detail_tabs = st.tabs(")

    assert (
        choose
        < selectors
        < selected_context
        < primary
        < trust_heading
        < trust
        < secondary
        < tabs
    )


def test_compact_stacking_is_page_scoped_and_preserves_desktop_columns() -> None:
    helper = _text(HELPER)

    assert PLAYER_COMPARE_COMPACT_BREAKPOINT_PX == 900
    assert "body:has(#nwr-player-compare-page)" in helper
    assert "@media (max-width: {PLAYER_COMPARE_COMPACT_BREAKPOINT_PX}px)" in helper
    assert 'div[data-testid="stHorizontalBlock"]' in helper
    assert "flex-wrap: wrap" in helper
    assert 'div[data-testid="stColumn"]' in helper
    assert "flex: 1 1 100% !important" in helper
    assert "width: 100% !important" in helper
    assert helper.index("@media (max-width:") < helper.index("flex: 1 1 100% !important")


def test_dense_tables_keep_native_engine_and_bounded_internal_containment() -> None:
    page = _text(PAGE)
    helper = _text(HELPER)

    assert page.count("st.dataframe(") >= 10
    assert 'div[data-testid="stDataFrame"]' in helper
    assert "max-width: 100%" in helper
    assert "min-width: 0" in helper
    for replacement_engine in ("aggrid", "AgGrid", "Tabulator", "react-table"):
        assert replacement_engine not in page
        assert replacement_engine not in helper


def test_compact_touch_targets_cover_primary_controls_tables_tabs_and_disclosures() -> None:
    helper = _text(HELPER)

    assert PLAYER_COMPARE_MIN_TOUCH_TARGET_PX == 44
    assert 'div[data-testid="stSelectbox"] [role="combobox"]' in helper
    assert 'div[data-testid="stMultiSelect"] [role="combobox"]' in helper
    assert 'div[data-testid="stDataFrame"] button' in helper
    assert 'div[data-testid="stTabs"] [role="tab"]' in helper
    assert "details summary" in helper
    assert "min-height: {PLAYER_COMPARE_MIN_TOUCH_TARGET_PX}px" in helper
    assert "min-width: {PLAYER_COMPARE_MIN_TOUCH_TARGET_PX}px" in helper


def test_metric_tab_and_disclosure_text_wrap_without_clipping_contract() -> None:
    helper = _text(HELPER)

    assert 'div[data-testid="stMetricValue"] p' in helper
    assert 'div[data-testid="stTabs"] button p' in helper
    assert "details summary p" in helper
    assert "white-space: normal !important" in helper
    assert "overflow: visible !important" in helper
    assert "text-overflow: clip !important" in helper
    assert "overflow-wrap: anywhere" in helper


def test_keyboard_controls_remain_native_and_receive_visible_focus() -> None:
    page = _text(PAGE)
    helper = _text(HELPER)

    assert "selector_cols[0].selectbox(" in page
    assert "selector_cols[1].selectbox(" in page
    assert "st.multiselect(" in page
    assert "st.expander(" in page
    assert "st.tabs(" in page
    assert "button:focus-visible" in helper
    assert '[role="combobox"]:focus-visible' in helper
    assert '[role="tab"]:focus-visible' in helper
    assert "details summary:focus-visible" in helper
    assert "onmouseover" not in page.lower()
    assert "onmouseover" not in helper.lower()


@pytest.mark.parametrize(
    ("player_a", "player_b", "expected_states", "expected_players"),
    [
        ("Alpha", "Bravo", ("Selected", "Selected"), ("Alpha", "Bravo")),
        ("Alpha", "", ("Selected", "Not selected"), ("Alpha", PLAYER_COMPARE_NOT_SELECTED)),
        ("", "Bravo", ("Not selected", "Selected"), (PLAYER_COMPARE_NOT_SELECTED, "Bravo")),
        (
            "",
            "",
            ("Not selected", "Not selected"),
            (PLAYER_COMPARE_NOT_SELECTED, PLAYER_COMPARE_NOT_SELECTED),
        ),
    ],
)
def test_empty_and_partial_selection_context_is_unambiguous(
    player_a: str,
    player_b: str,
    expected_states: tuple[str, str],
    expected_players: tuple[str, str],
) -> None:
    rows = selected_player_context_rows(player_a, player_b)

    assert tuple(row.slot for row in rows) == ("Player A", "Player B")
    assert tuple(row.state for row in rows) == expected_states
    assert tuple(row.player for row in rows) == expected_players


def test_long_display_text_is_preserved_without_abbreviation_or_identity_fallback() -> None:
    long_name = "Synthetic Long Display Label — Wide Receiver — Identity Review Required"

    rows = selected_player_context_rows(long_name, "Synthetic Player B", ["Synthetic Player C"])

    assert rows[0].player == long_name
    assert rows[0].slot == "Player A"
    assert rows[2].slot == "Optional player 1"
    assert "fallback" not in _text(HELPER).lower()


@pytest.mark.parametrize(
    ("value", "field", "expected"),
    [
        ("YELLOW_STALE", "as_of_freshness", STALE),
        ("Missing evidence: 2", "missingness_completeness", MISSING),
        ("Gated; not admitted", "evidence_source", GATED),
        ("Unavailable", "evidence_source", UNAVAILABLE),
        ("identity review required", "identity_join", IDENTITY_EXCEPTION),
        ("source caveat: partial receipt", "evidence_source", SOURCE_EXCEPTION),
        ("Not enough information", "material_caveats", NOT_ENOUGH_INFORMATION),
    ],
)
def test_missing_gated_unavailable_identity_and_source_states_remain_distinct(
    value: str,
    field: str,
    expected: str,
) -> None:
    assert state_from_existing_status(value, field=field) == expected


def test_trust_strip_semantics_and_per_player_construction_are_preserved() -> None:
    page = _runtime_page_text()
    strip = build_decision_trust_strip(
        {
            "source_status": "Gated; not admitted",
            "freshness_status": "YELLOW_STALE",
            "identity_join_status": "identity review required",
            "missing_evidence": "Missing evidence: 2",
            "warnings": "source caveat: partial receipt",
        },
        surface="Player Compare",
        entity_label="Synthetic Fixture Player",
        receipt_label="Existing comparison detail and diagnostic disclosures",
        receipt_available=True,
    )

    assert tuple(field.key for field in strip.fields) == FIELD_ORDER
    assert "for row in compare.to_dict(\"records\")" in page
    assert 'surface="Player Compare"' in page
    assert 'heading="Selected-player evidence trust"' in page


def test_selection_population_order_and_duplicate_exclusion_source_contract_is_unchanged() -> None:
    page = _runtime_page_text()

    assert 'compare_pool["player"].astype(str).tolist()' in page
    assert "_non_duplicate_options(players, {player_a})" in page
    assert "_non_duplicate_options(players, {player_a, player_b})" in page
    assert "selected = [player_a, player_b, *extra_players]" in page
    assert 'compare_pool["player"].astype(str).isin(selected)' in page
    assert "compare.sort_values(\"_selection_order\", kind=\"stable\")" in page


def test_desktop_behavior_keeps_two_selector_columns_and_four_summary_metrics() -> None:
    page = _text(PAGE)

    assert "selector_cols = st.columns(2)" in page
    assert "cols = st.columns(4)" in page
    assert "reason_col, flag_col = st.columns(2)" in page
