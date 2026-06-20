from src.trading_lab.trade_lab_ui import TRAINING_SCORING_DIMENSIONS, training_scenarios


def test_at_least_three_scenarios_exist() -> None:
    assert len(training_scenarios()) >= 3


def test_each_scenario_has_choices() -> None:
    for scenario in training_scenarios():
        assert len(scenario.choices) == 4
        assert all(choice for choice in scenario.choices)


def test_scoring_dimensions_exist() -> None:
    assert TRAINING_SCORING_DIMENSIONS
    assert all(
        scenario.scoring_dimensions == TRAINING_SCORING_DIMENSIONS
        for scenario in training_scenarios()
    )


def test_learning_note_exists() -> None:
    assert all(scenario.learning_note for scenario in training_scenarios())
    assert any("Learn" in scenario.learning_note for scenario in training_scenarios())


def test_no_real_data_or_automatic_decisioning() -> None:
    text = repr(training_scenarios()).lower()

    for blocked in ("real data is wired", "automatic decisioning", "auto-submit", "submit trade"):
        assert blocked not in text
