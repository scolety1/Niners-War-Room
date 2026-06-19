from src.trading_lab.trade_lab_component import RIGHT_CONTEXT_LABELS
from src.trading_lab.trade_lab_ui import generate_fake_trade_packages


def test_roster_aftermath_fields_exist() -> None:
    aftermath = generate_fake_trade_packages()[0].roster_aftermath

    assert aftermath.summary
    assert aftermath.keeper_core_before
    assert aftermath.keeper_core_after
    assert aftermath.drop_pressure_before
    assert aftermath.drop_pressure_after
    assert aftermath.positional_depth_before
    assert aftermath.positional_depth_after
    assert aftermath.roster_risk_notes


def test_keeper_and_drop_pressure_labels_appear() -> None:
    assert "Keeper impact" in RIGHT_CONTEXT_LABELS
    assert "Keeper core before" in RIGHT_CONTEXT_LABELS
    assert "Keeper core after" in RIGHT_CONTEXT_LABELS
    assert "Drop pressure before" in RIGHT_CONTEXT_LABELS
    assert "Drop pressure after" in RIGHT_CONTEXT_LABELS


def test_rookie_and_mock_placeholders_appear() -> None:
    aftermath = generate_fake_trade_packages()[0].roster_aftermath

    assert "Rookie/mock draft context" in RIGHT_CONTEXT_LABELS
    assert "Mock draft context placeholder" in RIGHT_CONTEXT_LABELS
    assert "not wired yet" in aftermath.mock_draft_placeholder


def test_placeholders_say_real_integrations_are_not_wired() -> None:
    aftermath = generate_fake_trade_packages()[0].roster_aftermath

    assert "not wired yet" in aftermath.needs_real_integration_note
    assert "Real roster integrations" in aftermath.needs_real_integration_note


def test_no_real_data_import_or_fetch_language() -> None:
    text = repr(generate_fake_trade_packages()).lower()

    for blocked in ("import real", "fetch", "data/", "local_exports", ".csv"):
        assert blocked not in text
