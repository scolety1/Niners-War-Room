from __future__ import annotations

import ast
from pathlib import Path

HOME_PAGE = Path("app/pages/46_draft_cockpit_default_root.py")


def test_default_home_is_read_only_orientation_not_a_runtime_alias() -> None:
    text = HOME_PAGE.read_text(encoding="utf-8")
    ast.parse(text, filename=str(HOME_PAGE))

    assert '"Niners War Room"' in text
    assert '"Dynasty Rankings"' in text
    assert '"Player Compare"' in text
    assert '"Trading Lab"' in text
    assert '"Draft Cockpit"' in text
    assert '"/rankings"' in text
    assert '"/player-compare"' in text
    assert '"/trading-lab"' in text
    assert '"/draft-cockpit"' in text
    assert '"/settings-data-health"' in text
    assert "accepted dynasty board stays read-only" in text
    assert "runpy.run_path" not in text
    assert "21_live_draft_room_v1.py" not in text


def test_default_home_explains_state_boundaries_without_model_changes() -> None:
    text = HOME_PAGE.read_text(encoding="utf-8")

    assert "Opening them does not change the canonical board." in text
    assert "Draft Cockpit changes local session state only through its controls." in text
    assert "Refresh and recovery actions remain in Admin" in text
    assert "score" not in text.lower().replace("first-down scoring", "")
    assert "formula" not in text.lower()
    assert "provider" not in text.lower()
