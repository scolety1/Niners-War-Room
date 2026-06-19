from src.trading_lab.trade_lab_ui import (
    MODE_CONTEXTS,
    PROHIBITED_DEMO_TERMS,
    TRADE_LAB_MODES,
    mode_context_for,
    packages_for_mode,
)


def test_all_modes_are_available() -> None:
    assert set(TRADE_LAB_MODES) == set(MODE_CONTEXTS)


def test_mode_labels_are_fantasy_football_oriented() -> None:
    for mode in TRADE_LAB_MODES:
        assert "Trade" in mode or mode in {
            "Upgrade Position",
            "Consolidate Depth",
            "Pick Conversion",
            "Training Mode",
        }
        assert any(
            word in mode
            for word in ("Player", "Position", "Depth", "Pick", "Mode", "Fit", "Pressure")
        )


def test_each_mode_maps_to_a_user_question() -> None:
    for mode in TRADE_LAB_MODES:
        context = mode_context_for(mode)

        assert context.user_question.endswith("?")
        assert context.explanation
        assert context.relevant_controls
        assert context.warning_examples


def test_each_mode_can_return_fake_package_or_context_data() -> None:
    for mode in TRADE_LAB_MODES:
        packages = packages_for_mode(mode)

        assert packages
        assert all(package.give or package.get for package in packages)


def test_no_blocked_integration_appears_as_active_feature() -> None:
    text = " ".join(
        [
            " ".join(TRADE_LAB_MODES),
            " ".join(context.explanation for context in MODE_CONTEXTS.values()),
            " ".join(" ".join(context.warning_examples) for context in MODE_CONTEXTS.values()),
        ]
    ).lower()

    for term in (*PROHIBITED_DEMO_TERMS, "fetch", "real integration", "auto-submit"):
        assert term not in text
