from __future__ import annotations

from pathlib import Path

POSITION_FORMULA_PROPOSAL_PATH = Path(
    "docs/model_v4/POSITION_FORMULA_PROPOSAL.md"
)

POSITIONS = ("RB", "WR", "QB", "TE")
REQUIRED_COMPONENTS = (
    "production",
    "first-down scoring fit",
    "usage/opportunity",
    "snap/proxy role",
    "projection",
    "age/dropoff",
    "injury/context confidence effect",
    "young-player prior",
)


def test_model_v4_position_formula_proposal_exists() -> None:
    assert POSITION_FORMULA_PROPOSAL_PATH.exists()


def test_model_v4_position_formula_proposal_covers_each_position() -> None:
    text = _proposal_text()

    for position in POSITIONS:
        section = _position_section(text, position)
        assert "### Goal" in section
        assert "### Proposed Dynasty Asset Components" in section
        assert "### Formula Intent" in section
        assert "### Expected Sanity Fixture Behavior" in section
        assert "### Formula Risks" in section
        normalized = _normalized(section).lower()
        for component in REQUIRED_COMPONENTS:
            assert component in normalized


def test_model_v4_position_formula_proposal_defines_cross_position_logic() -> None:
    text = _proposal_text()

    assert "### 10-Team 1QB Suppression" in text
    assert "### No-TE-Premium Suppression" in text
    assert "### RB Fragility And Workload Risk" in text
    assert "### WR Target Earning And Stability" in text
    assert "### Young-Player Bridge Decay" in text


def test_model_v4_position_formula_proposal_stays_review_only() -> None:
    text = _proposal_text()
    normalized = _normalized(text)

    assert "not final weights" in normalized
    assert "not manual ranking overrides" in normalized
    assert "not exact final rankings" in normalized
    assert "No formula code is written." in text
    assert "Active rankings remain untouched." in text


def test_model_v4_position_formula_proposal_lists_major_risks() -> None:
    text = _proposal_text()

    for risk in (
        "RB volume overcorrection",
        "WR route-data gap",
        "Young prior overreach",
        "Aging veteran overvaluation",
        "QB inflation",
        "TE inflation",
        "Projection false certainty",
        "Market contamination",
        "League-rank contamination",
        "Hidden defaults",
    ):
        assert risk in text


def _proposal_text() -> str:
    return POSITION_FORMULA_PROPOSAL_PATH.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _position_section(text: str, position: str) -> str:
    start_marker = f"## {position} Proposal"
    start = text.index(start_marker)
    next_start = text.find("\n## ", start + len(start_marker))
    if next_start == -1:
        next_start = len(text)
    return text[start:next_start]
