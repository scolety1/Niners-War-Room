from __future__ import annotations

from pathlib import Path

import pandas as pd

OVERLAY_ROOT = Path("local_exports/model_v4/rookie_research_overlay/latest")


def test_rookie_research_overlay_is_review_only_context() -> None:
    overlay = pd.read_csv(OVERLAY_ROOT / "rookie_research_overlay_rows.csv")

    assert not overlay.empty
    assert set(overlay["allowed_use"]) == {
        "review_only_research_context_not_formula_input"
    }
    assert set(overlay["blocked_use"]) == {
        "do_not_use_as_private_value_or_final_pick_recommendation"
    }
    assert {"Jeremiyah Love", "Carnell Tate", "Jordyn Tyson"}.issubset(
        set(overlay["player"])
    )


def test_rookie_research_pick_notes_cover_niners_picks() -> None:
    pick_notes = pd.read_csv(OVERLAY_ROOT / "rookie_research_pick_fit_rows.csv")

    assert {"2026 1.03", "2026 1.04", "2026 2.04", "2026 2.08", "2026 5.04"}.issubset(
        set(pick_notes["pick_label"])
    )
    assert set(pick_notes["allowed_use"]) == {
        "review_only_research_context_not_formula_input"
    }
    assert "final_pick_recommendation" in pick_notes["blocked_use"].str.cat(sep="|")
