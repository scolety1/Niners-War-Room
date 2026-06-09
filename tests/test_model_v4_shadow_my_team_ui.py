from __future__ import annotations

from pathlib import Path


def test_my_team_exposes_v4_shadow_without_replacing_active_board() -> None:
    page_text = Path("app/pages/02_team.py").read_text(encoding="utf-8")

    assert "V4 Shadow My Team" in page_text
    assert "MODEL_V4_SHADOW_MY_TEAM_BANNER" in page_text
    assert "build_model_v4_shadow_my_team_rows" in page_text
    assert "render_model_v4_shadow_receipt_drilldown" in page_text
    assert "team_v4_shadow_my_team_table" in page_text
    assert "V4 Shadow Receipt Drilldown" in page_text
    assert "_load_board(" in page_text
    assert "build_team_command_board(active_data_pack)" in page_text
    assert "does not replace active My Team" in page_text
    assert "Advanced: V4 shadow My Team join audit" in page_text
    assert 'selection_mode="single-row"' in page_text
