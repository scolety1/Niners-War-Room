from __future__ import annotations

from pathlib import Path

FORMULA_LANE_ARCHITECTURE_PATH = Path(
    "docs/model_v4/FORMULA_LANE_ARCHITECTURE.md"
)

REQUIRED_LANES = (
    "Dynasty Asset Value",
    "Roster Decision Value",
    "Required Top-Five Release Pain",
    "Trade / Market Context",
    "Draft Value",
    "Confidence",
)


def test_model_v4_formula_lane_architecture_exists() -> None:
    assert FORMULA_LANE_ARCHITECTURE_PATH.exists()


def test_model_v4_formula_lane_architecture_defines_all_lanes() -> None:
    text = _architecture_text()

    for lane in REQUIRED_LANES:
        assert f"## Lane: {lane}" in text
        section = _lane_section(text, lane)
        assert "### Purpose" in section
        assert "### Allowed Inputs" in section
        assert "### Forbidden Inputs" in section
        assert "### Output Fields" in section
        assert "### Receipt Requirements" in section
        assert "### Sanity Fixtures That Apply" in section


def test_dynasty_asset_value_excludes_market_league_rank_and_draft_availability() -> None:
    section = _lane_section(_architecture_text(), "Dynasty Asset Value")
    normalized = _normalized(section)

    assert "- league rank" in section
    assert "- trade market or liquidity" in section
    assert "- draftable-player availability" in section
    assert "Market context and league-rank rule context may appear beside the score" in normalized
    assert "never as private-value contributions" in normalized


def test_required_top_five_release_lane_is_rule_context_only() -> None:
    section = _lane_section(_architecture_text(), "Required Top-Five Release Pain")

    assert "locked Niners Roster's League-Rank Top Five candidate pool" in section
    assert "players outside the locked top-five candidate pool" in section
    assert "league rank as player quality" in section
    assert "easy non-top-five cuts as the required release answer" in section


def test_trade_market_context_cannot_change_private_value() -> None:
    section = _lane_section(_architecture_text(), "Trade / Market Context")
    normalized = _normalized(section)

    assert "opportunity discovery" in normalized
    assert "not for changing private football value" in normalized
    assert "market as Dynasty Asset Value contribution" in section
    assert "private value changes from market changes" in section
    assert "Missing market values must display as missing" in normalized


def test_draft_value_stays_separate_from_rostered_player_value() -> None:
    section = _lane_section(_architecture_text(), "Draft Value")

    assert "Rank only actual draftable players" in section
    assert "separate from rostered-player value" in section
    assert "protected roster players unless manually added" in section
    assert "fixture/demo draft pools as normal data" in section


def test_global_separation_rules_are_explicit() -> None:
    text = _architecture_text()

    assert "League rank cannot affect Dynasty Asset Value." in text
    assert "Market cannot affect private football value." in text
    assert "Required top-five release logic is roster-rule context only." in text
    assert "Draftable-player logic stays separate from rostered-player value." in text
    assert "No lane can unlock decision-ready status until the formal gates pass." in text


def _architecture_text() -> str:
    return FORMULA_LANE_ARCHITECTURE_PATH.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _lane_section(text: str, lane: str) -> str:
    start_marker = f"## Lane: {lane}"
    start = text.index(start_marker)
    next_start = text.find("\n## Lane: ", start + len(start_marker))
    if next_start == -1:
        next_start = text.find("\n## Phase 3A Exit Criteria", start)
    if next_start == -1:
        next_start = len(text)
    return text[start:next_start]
