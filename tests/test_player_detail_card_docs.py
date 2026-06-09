from __future__ import annotations

from pathlib import Path

DOC_ROOT = Path("docs/model_v4")

CURRENT_STATE = DOC_ROOT / "PLAYER_DETAIL_CURRENT_STATE_AUDIT_20260609.md"
SOURCE_CONTRACT = DOC_ROOT / "PLAYER_DETAIL_CARD_SOURCE_CONTRACT_20260609.md"
UX_SPEC = DOC_ROOT / "PLAYER_DETAIL_CARD_UX_SPEC_20260609.md"
IMPLEMENTATION_PLAN = DOC_ROOT / "PLAYER_DETAIL_CARD_IMPLEMENTATION_PLAN_20260609.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_player_detail_design_docs_exist() -> None:
    for path in (CURRENT_STATE, SOURCE_CONTRACT, UX_SPEC, IMPLEMENTATION_PLAN):
        assert path.exists()


def test_specs_cover_all_required_pages() -> None:
    combined = "\n".join(
        _text(path) for path in (CURRENT_STATE, SOURCE_CONTRACT, UX_SPEC, IMPLEMENTATION_PLAN)
    )

    for label in ("Rankings", "Draft Prep", "Live Draft Room", "Roster Decisions"):
        assert label in combined


def test_specs_preserve_sentinels_and_blocked_use_language() -> None:
    combined = "\n".join(_text(path) for path in (SOURCE_CONTRACT, UX_SPEC, IMPLEMENTATION_PLAN))

    for phrase in (
        "Keenan Allen legacy active-pack `private_score = 82.4` remains comparison-only",
        "Darius Slayton legacy active-pack `private_score = 78.88` remains comparison-only",
        "`2026 5.04` remains no-baseline/manual watchlist/no exact equivalence",
        (
            "Market, league, ADP, startup, consensus, projections, trade calculators, "
            "and legacy scores cannot affect"
        ),
        "RotoWire is source/status/context only",
    ):
        assert phrase in combined


def test_specs_keep_receipts_advanced_and_forbid_final_recommendations() -> None:
    combined = "\n".join(_text(path) for path in (SOURCE_CONTRACT, UX_SPEC, IMPLEMENTATION_PLAN))

    assert "collapsed by default" in combined
    assert "Advanced source receipts" in combined

    for forbidden in (
        "Draft this player",
        "Target",
        "Buy",
        "Sell",
        "Cut",
        "Defer",
        "Trade for",
    ):
        assert forbidden in combined
    assert "must not render final draft/roster/trade recommendations" in combined


def test_implementation_plan_does_not_create_skeleton_yet() -> None:
    text = _text(IMPLEMENTATION_PLAN)

    assert "No component skeleton is created in this task." in text
    assert "Wire Rankings first" in text
    assert "Wire Draft Prep" in text
    assert "Wire Live Draft Room" in text
