from __future__ import annotations

from pathlib import Path


def test_war_board_exposes_v4_shadow_without_replacing_active_board() -> None:
    page_text = Path("app/pages/03_war_board.py").read_text(encoding="utf-8")

    assert "V4 Shadow War Board" in page_text
    assert "MODEL_V4_SHADOW_WAR_BOARD_BANNER" in page_text
    assert "build_model_v4_shadow_war_board_rows" in page_text
    assert "render_model_v4_shadow_receipt_drilldown" in page_text
    assert "war_board_v4_shadow_table" in page_text
    assert "V4 Shadow Receipt Drilldown" in page_text
    assert "Old vs V4 Comparison" in page_text
    assert "MODEL_V4_OLD_VS_V4_BANNER" in page_text
    assert "build_model_v4_old_vs_v4_comparison_rows" in page_text
    assert "war_board_v4_old_vs_v4_table" in page_text
    assert "V4 Promotion Blockers" in page_text
    assert "MODEL_V4_PROMOTION_BLOCKERS_BANNER" in page_text
    assert "build_model_v4_promotion_blocker_rows" in page_text
    assert "build_model_v4_promotion_blocker_summary_rows" in page_text
    assert "war_board_v4_promotion_blocker_summary_table" in page_text
    assert "war_board_v4_promotion_blockers_" in page_text
    assert "Niners roster" in page_text
    assert "Large movement only" in page_text
    assert "_load_board(active_data_pack" in page_text
    assert "build_war_board(active_data_pack)" in page_text
    assert "Active rankings remain on the current War " in page_text
    assert "Board above." in page_text
    assert 'selection_mode="single-row"' in page_text
