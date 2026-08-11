from __future__ import annotations

from pathlib import Path

from src.services.player_compare_owner_summary_service import build_owner_compare_summary


def _row(name: str, rank: int, probability: float) -> dict[str, object]:
    return {
        "player": name,
        "compare_asset_type": "Current Player",
        "position": "WR",
        "age": "24",
        "research_rank": str(rank),
        "research_tier": "High-end dynasty neighborhood",
        "research_outlook_3y": "Strong 3Y band",
        "research_outlook_5y": "Strong 5Y band",
        "research_ceiling_signal": "Upper WR tier",
        "research_downside_signal": "Starter tier",
        "research_confidence": "0.80",
        "outcome_signals": (f"WR T24 2026: {probability:.1f}%",),
    }


def test_compare_summary_answers_horizons_and_uses_bands_not_fake_ranges() -> None:
    summary = build_owner_compare_summary(
        [_row("Player A", 10, 62.0), _row("Player B", 25, 48.0)]
    )

    assert [lean.horizon for lean in summary.leans] == [
        "Short term",
        "Medium term",
        "Long term",
    ]
    assert all(lean.preferred == "Player A" for lean in summary.leans)
    assert summary.ranges[0]["Floor"] == "Starter tier"
    assert summary.ranges[0]["NWR Expected"] == "High-end dynasty neighborhood"
    assert summary.ranges[0]["Ceiling"] == "Upper WR tier"
    assert summary.ranges[0]["Range authority"] == "Research context beside Finished V1"
    assert summary.notes[0]["Player"] == "Player A"
    assert summary.notes[0]["Advantages"]


def test_dynasty_compare_has_no_mode_switch_and_leads_with_owner_question() -> None:
    page = (
        Path(__file__).resolve().parents[1] / "app/pages/22_player_compare_v1.py"
    ).read_text(encoding="utf-8")
    assert 'st.markdown("## Who does NWR prefer?")' in page
    assert "Redraft comparisons live in the separate Redraft app" in page
    assert '("DYNASTY - LONG TERM", "REDRAFT - CURRENT SEASON")' not in page


def test_compare_formats_numeric_research_values_for_owners() -> None:
    first = _row("Player A", 10, 62.0)
    first.update(
        {
            "research_outlook_3y": "172.180723",
            "research_outlook_5y": "241.727007",
            "research_ceiling_signal": "0.634846",
        }
    )
    summary = build_owner_compare_summary([first, _row("Player B", 25, 48.0)])

    assert "172.2 research-index points" in summary.leans[1].reason
    assert "241.7 research-index points" in summary.leans[2].reason
    assert any("63.5%" in value for value in summary.notes[0]["Advantages"])
    assert "0.634846" not in " ".join(summary.notes[0]["Advantages"])
