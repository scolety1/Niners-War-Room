from pathlib import Path

DECISION_PAGE_PATHS = (
    Path("app/pages/02_team.py"),
    Path("app/pages/03_war_board.py"),
    Path("app/pages/04_trade_central.py"),
    Path("app/pages/05_rankings.py"),
    Path("app/pages/06_draft_board.py"),
    Path("app/pages/06_league_intel.py"),
)
MAIN_MODEL_PAGE_PATHS = (
    Path("app/pages/04_trade_central.py"),
    Path("app/pages/05_rankings.py"),
    Path("app/pages/06_draft_board.py"),
    Path("app/pages/07_model_lab.py"),
    Path("app/pages/08_june15_review.py"),
)
REQUIRED_REVIEW_ONLY_BANNER = (
    "Review-only surface. This page does not make automatic trade, cut, keep, "
    "or draft recommendations."
)


def test_decision_pages_render_one_primary_trust_banner() -> None:
    for page_path in DECISION_PAGE_PATHS:
        page_text = page_path.read_text(encoding="utf-8")

        assert page_text.count("render_page_trust_banner(") == 1, page_path
        assert "render_trust_status(" not in page_text, page_path
        assert "render_model_recalibration_banner(" not in page_text, page_path


def test_page_trust_banner_keeps_review_only_details_collapsible() -> None:
    component_text = Path("app/components/trust_status.py").read_text(encoding="utf-8")
    normalized_component_text = component_text.replace('"\n    "', "")

    assert "REVIEW_ONLY_SURFACE_BANNER" in component_text
    assert REQUIRED_REVIEW_ONLY_BANNER in normalized_component_text
    assert 'details_label: str = "Why review-only?"' in component_text
    assert "compact: bool = False" in component_text
    assert "Rankings are review-only until calibration gates pass." in component_text
    assert "with st.expander(details_label):" in component_text


def test_main_model_pages_show_required_review_only_banner() -> None:
    for page_path in MAIN_MODEL_PAGE_PATHS:
        page_text = page_path.read_text(encoding="utf-8")

        assert (
            "render_page_trust_banner(" in page_text
            or "REVIEW_ONLY_SURFACE_BANNER" in page_text
            or REQUIRED_REVIEW_ONLY_BANNER in page_text
        ), page_path


def test_war_board_keeps_filters_collapsed_for_small_windows() -> None:
    page_text = Path("app/pages/03_war_board.py").read_text(encoding="utf-8")

    assert 'with st.expander("Filters", expanded=False):' in page_text
    assert "compact=True" in page_text
    assert 'with st.expander("Advanced: score source audit"):' in page_text
    assert "Review board for ranking inspection and model debugging." not in page_text
    assert ".block-container { padding-top: 1.4rem; }" in page_text


def test_my_team_uses_war_board_value_language() -> None:
    page_text = Path("app/pages/02_team.py").read_text(encoding="utf-8")

    assert "`Model Value`" in page_text
    assert "`Model vs Market`" in page_text
    assert "Top Positive Drivers" in page_text
    assert "Top Negative Drivers" in page_text
    assert "Young Bridge Contribution" in page_text
    assert "Model vs Market" in page_text
    assert '"team": "Fantasy Team"' in page_text
    assert "Model Value Drivers" not in page_text
    assert "Stats Value Drivers" not in page_text
    assert "Market Edge:" not in page_text
