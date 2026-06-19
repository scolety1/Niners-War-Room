from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_readiness_report import render_readiness_report
from src.services.mock_draft_readiness_service import build_mock_draft_readiness_report


def test_yellow_real_readiness_renders_missing_inputs() -> None:
    report = build_mock_draft_readiness_report()

    rendered = render_readiness_report(report)

    assert "Overall readiness: YELLOW" in rendered
    assert "Real input readiness: YELLOW" in rendered
    assert "Frozen rookie input" in rendered


def test_fixture_green_and_market_separation_are_clear() -> None:
    rendered = render_readiness_report(build_mock_draft_readiness_report())

    assert "Fixture readiness: GREEN" in rendered
    assert "ADP/market separation: GREEN" in rendered
    assert "No simulations run: yes" in rendered


def test_report_does_not_create_draft_output_language() -> None:
    rendered = render_readiness_report(build_mock_draft_readiness_report()).lower()

    assert "recommendation" not in rendered
    assert "ranking" not in rendered
    assert "sorted draft" not in rendered


def test_renderer_does_not_write_files(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())

    render_readiness_report(build_mock_draft_readiness_report())

    assert set(tmp_path.iterdir()) == before
