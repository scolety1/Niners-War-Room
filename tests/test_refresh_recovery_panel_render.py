from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_recovery_panel_renders_keyboard_disclosure_and_all_states():
    at = AppTest.from_file(
        str(Path("tests/fixtures/refresh_recovery_panel_fixture.py"))
    ).run(timeout=20)
    assert not at.exception
    assert len(at.expander) == 1
    assert "Passive guidance only" in at.expander[0].caption[0].value
    text = at.dataframe[0].value.to_string()
    for label in (
        "REFRESH_SUCCESS",
        "PARTIAL_SUCCESS",
        "STALE_RETAINED_DATA",
        "SOURCE_SKIPPED",
        "SOURCE_UNAVAILABLE",
        "SOURCE_GATED",
        "REFRESH_FAILED",
        "NOT_ENOUGH_INFORMATION",
    ):
        assert label in text
    assert "AVAILABLE_ACTION" in text
    assert "UNAVAILABLE_ACTION" in text
