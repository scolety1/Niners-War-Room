from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_representative_fixture_renders_compact_and_expanded_disclosures() -> None:
    fixture = Path("tests/fixtures/decision_trust_strip_fixture.py")
    at = AppTest.from_file(str(fixture)).run(timeout=20)
    assert not at.exception
    assert len(at.expander) == 7
    assert all("Evidence details" in expander.label for expander in at.expander)
    assert any("Valid / current" in caption.value for caption in at.caption)
    assert any("Stale" in caption.value for caption in at.caption)
    assert any("Missing" in caption.value for caption in at.caption)
    assert any("Gated" in caption.value for caption in at.caption)
    assert any("Unavailable" in caption.value for caption in at.caption)
    assert any("Identity exception" in caption.value for caption in at.caption)
