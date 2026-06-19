from src.trading_lab.trade_lab_ui import (
    TRAINING_MODE_DISCLAIMER,
    TRAINING_SCORING_DIMENSIONS,
    training_scenarios,
)


def test_training_scenarios_exist() -> None:
    scenarios = training_scenarios()

    assert len(scenarios) >= 3
    assert any("Trade for" in scenario.scenario_prompt for scenario in scenarios)
    assert any("Trade away" in scenario.scenario_prompt for scenario in scenarios)
    assert any("drop pressure" in scenario.scenario_prompt.lower() for scenario in scenarios)


def test_choices_exist() -> None:
    for scenario in training_scenarios():
        assert len(scenario.choices) == 4
        assert all(choice for choice in scenario.choices)


def test_scoring_dimensions_exist() -> None:
    assert TRAINING_SCORING_DIMENSIONS == (
        "NWR value",
        "market realism",
        "opponent fit",
        "roster impact",
        "negotiation quality",
    )
    assert all(
        scenario.scoring_dimensions == TRAINING_SCORING_DIMENSIONS
        for scenario in training_scenarios()
    )


def test_fake_training_disclaimer_exists() -> None:
    assert "Training only" in TRAINING_MODE_DISCLAIMER
    assert "fake scenario" in TRAINING_MODE_DISCLAIMER


def test_no_real_data_or_automatic_decisioning() -> None:
    text = repr(training_scenarios()).lower()

    for blocked in ("real data", "auto-accept", "auto-submit", "automatic decisioning"):
        assert blocked not in text
