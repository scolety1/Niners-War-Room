from __future__ import annotations

import csv
from pathlib import Path

from src.services.mock_draft_input_schema_validator_service import SCHEMA_COLUMNS

TEMPLATE_ROOT = Path("docs/model_v4/mock_draft_input_templates_20260617")

TEMPLATE_TO_SCHEMA = {
    "post_drop_rosters_template.csv": "post_drop_rosters",
    "post_drop_draft_order_template.csv": "draft_order",
    "team_managers_template.csv": "team_managers",
    "dropped_veterans_template.csv": "dropped_veterans",
    "behavior_only_adp_market_template.csv": "market_timing",
    "nwr_veteran_value_guidance_template.csv": "nwr_veteran_guidance",
}


def test_mock_draft_input_template_headers_cover_schema_requirements() -> None:
    for template_name, schema_name in TEMPLATE_TO_SCHEMA.items():
        path = TEMPLATE_ROOT / template_name
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            headers = set(next(reader))
        assert SCHEMA_COLUMNS[schema_name].issubset(headers), template_name


def test_behavior_only_market_template_excludes_blocked_value_fields() -> None:
    path = TEMPLATE_ROOT / "behavior_only_adp_market_template.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        headers = set(next(csv.reader(handle)))
    blocked = {
        "stats_model_value",
        "model_value",
        "draft_value",
        "nwr_draft_value",
        "nwr_dynasty_score",
        "nwr_quality_score",
        "quality_score",
        "war_score",
        "hidden_sort_key",
        "outcome_probability",
        "outcome_band",
    }
    assert headers.isdisjoint(blocked)
