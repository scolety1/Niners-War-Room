from __future__ import annotations

from pathlib import Path

from src.services.mock_draft_template_renderer import (
    TEMPLATE_ROLE_TO_SCHEMA_KEY,
    render_all_blank_templates,
    render_blank_template,
    template_has_source_contamination,
)


def test_every_required_role_has_template() -> None:
    templates = render_all_blank_templates()

    assert tuple(templates) == tuple(TEMPLATE_ROLE_TO_SCHEMA_KEY)


def test_templates_include_required_columns() -> None:
    template = render_blank_template("pick_order")

    assert "overall_pick" in template.headers
    assert "current_owner" in template.headers
    assert template.csv_text.startswith("current_owner")


def test_private_value_template_has_no_market_columns() -> None:
    assert not template_has_source_contamination("nwr_private_values")


def test_market_context_template_has_no_private_score_columns() -> None:
    assert not template_has_source_contamination("market_context")


def test_renderer_writes_no_files(tmp_path: Path) -> None:
    before = set(tmp_path.iterdir())

    template = render_blank_template("rookie_input")

    assert template.no_files_written is True
    assert set(tmp_path.iterdir()) == before


def test_template_output_is_deterministic() -> None:
    assert render_blank_template("team_needs").csv_text == render_blank_template(
        "team_needs"
    ).csv_text
