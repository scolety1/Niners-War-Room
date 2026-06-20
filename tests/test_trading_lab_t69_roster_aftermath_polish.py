from src.trading_lab.trade_roster_effects import (
    ROSTER_AFTERMATH_POLISH_LABELS,
    ROSTER_INTEGRATION_STATUS,
    roster_aftermath_why_this_matters,
)


def test_keeper_drop_position_rookie_mock_labels_exist() -> None:
    labels = " ".join(ROSTER_AFTERMATH_POLISH_LABELS)

    for expected in (
        "Keeper core impact",
        "Drop pressure impact",
        "Position depth impact",
        "Rookie/mock context placeholder",
    ):
        assert expected in labels


def test_why_this_matters_explanation_exists() -> None:
    explanation = roster_aftermath_why_this_matters()

    assert "Why this matters" in explanation
    assert "keeper" in explanation.lower()
    assert "future cuts" in explanation.lower()


def test_real_integration_placeholder_exists() -> None:
    assert "not wired yet" in ROSTER_INTEGRATION_STATUS


def test_no_real_lane_import_claims() -> None:
    text = " ".join((*ROSTER_AFTERMATH_POLISH_LABELS, roster_aftermath_why_this_matters()))

    for blocked in ("Outcome import", "Rookie import", "Mock Draft import", "Drop Decision import"):
        assert blocked not in text
