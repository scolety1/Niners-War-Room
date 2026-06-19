from src.trading_lab.trade_lab_component import (
    CENTER_SECTION_LABELS,
    DESKTOP_SECTION_LABELS,
    FAKE_DATA_DISCLAIMER,
    SCORE_LABELS,
    trade_lab_label_text,
)


def test_primary_sections_exist() -> None:
    assert "Build the trade" in DESKTOP_SECTION_LABELS
    assert "Review candidate packages" in DESKTOP_SECTION_LABELS
    assert "Understand roster aftermath" in DESKTOP_SECTION_LABELS
    assert "Review board" in CENTER_SECTION_LABELS


def test_score_labels_exist() -> None:
    assert SCORE_LABELS == (
        "NWR Gain",
        "Market Fairness",
        "Opponent Fit",
        "Roster Impact",
        "Keeper/Drop Impact",
        "Risk",
        "Verdict",
    )


def test_fake_data_disclaimer_exists() -> None:
    assert "fake in-memory examples only" in FAKE_DATA_DISCLAIMER
    assert "not wired yet" in FAKE_DATA_DISCLAIMER


def test_no_old_wall_street_active_product_language() -> None:
    text = trade_lab_label_text().lower()

    for term in ("stock", "broker", "crypto", "equity", "order execution"):
        assert term not in text


def test_desktop_copy_is_fantasy_trade_oriented() -> None:
    text = trade_lab_label_text()

    assert "Trade Lab" in text
    assert "NWR Gain" in text
    assert "Market Fairness" in text
    assert "Roster Impact" in text
    assert "Keeper/Drop Impact" in text
