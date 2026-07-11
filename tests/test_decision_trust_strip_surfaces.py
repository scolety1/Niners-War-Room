from __future__ import annotations

from pathlib import Path

PAGES = {
    "Dynasty Rankings": Path("app/pages/20_final_board_v1.py"),
    "Player Compare": Path("app/pages/22_player_compare_v1.py"),
    "Trading Lab": Path("app/pages/23_trading_lab_v1.py"),
}


def test_all_three_surfaces_render_the_shared_display_only_component() -> None:
    for surface, path in PAGES.items():
        text = path.read_text(encoding="utf-8")
        assert "render_decision_trust_strips" in text, surface
        assert "build_decision_trust_strip" in text or "build_rankings_dataset_trust_strip" in text


def test_trading_lab_remains_manual_without_value_or_recommendation_generation() -> None:
    text = PAGES["Trading Lab"].read_text(encoding="utf-8")
    assert "MANUAL_PLANNER_WARNING" in text
    assert "No trade valuation" in text
    assert "No package value" in text
    assert "render_decision_trust_strips" in text


def test_component_uses_keyboard_accessible_disclosure_and_text_states() -> None:
    text = Path("app/components/decision_trust_strip.py").read_text(encoding="utf-8")
    assert "st.expander(" in text
    assert '"State": STATE_LABELS[field.state]' in text
    assert "never by color alone" in text
    assert "st.dataframe(" in text


def test_adapter_has_no_frozen_comparator_or_source_registry_dependency() -> None:
    text = Path("src/services/decision_trust_strip_service.py").read_text(encoding="utf-8")
    forbidden = (
        "PROSPECTIVE_2026_BASELINE_FREEZE",
        "GAUNTLET_081",
        "PYF",
        "source_registry_service",
        "identity_audit_service",
        "market_baseline_freshness_status",
    )
    assert all(token not in text for token in forbidden)
