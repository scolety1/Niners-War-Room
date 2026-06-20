from pathlib import Path

from src.trading_lab.trade_lab_component import (
    PROVENANCE_STATUS_LABELS,
    trade_lab_sections,
)


def test_page_route_file_exists() -> None:
    assert Path("app/pages/11_trade_lab.py").exists()


def test_component_exports_expected_sections() -> None:
    section_names = {section.name for section in trade_lab_sections()}

    for expected in (
        "Header",
        "Left control panel",
        "Center results",
        "Right context panel",
        "Training Mode",
        "Review queue placeholder",
    ):
        assert expected in section_names


def test_fixture_only_status_labels_exist() -> None:
    assert "Fixture demo value" in PROVENANCE_STATUS_LABELS
    assert "Manual review required" in PROVENANCE_STATUS_LABELS


def test_current_page_has_no_real_integration_claims() -> None:
    page_text = Path("app/pages/11_trade_lab.py").read_text(encoding="utf-8").lower()

    for blocked in (
        "real nwr integration wired",
        "public fantasy source wired",
        "saved review queue wired",
    ):
        assert blocked not in page_text
