from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("page", "heading"),
    (
        ("36_roster_weakness_tracker_v1.py", "Roster Planner"),
        ("37_future_pick_planning_v1.py", "Future Pick Planner"),
        ("38_keeper_deadline_prep_v1.py", "Keeper Deadline Prep"),
        ("39_drop_deadline_prep_v1.py", "Drop Deadline Prep"),
        ("40_trade_deadline_prep_v1.py", "Trade Deadline Prep"),
        ("41_upcoming_draft_prep_v1.py", "Upcoming Draft Prep"),
    ),
)
def test_graduated_tool_opens_without_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    page: str,
    heading: str,
) -> None:
    state_root = tmp_path / "planning-state"
    monkeypatch.setenv("NWR_DEVELOPMENT_LAB_STATE_ROOT", str(state_root))

    page_path = ROOT / "app" / "pages" / page
    app = AppTest.from_file(str(page_path)).run(timeout=40)

    assert not app.exception
    assert f'page_header(\n    "{heading}"' in page_path.read_text(encoding="utf-8")
    assert not state_root.exists()


def test_deadline_checklist_is_interactive_and_does_not_save_implicitly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_root = tmp_path / "planning-state"
    monkeypatch.setenv("NWR_DEVELOPMENT_LAB_STATE_ROOT", str(state_root))
    page_path = ROOT / "app" / "pages" / "40_trade_deadline_prep_v1.py"

    app = AppTest.from_file(str(page_path)).run(timeout=40)
    assert not app.exception
    assert app.checkbox[0].label == "Confirm league trade deadline"

    app.checkbox[0].check().run(timeout=40)

    assert not app.exception
    assert app.checkbox[0].value is True
    assert not state_root.exists()
