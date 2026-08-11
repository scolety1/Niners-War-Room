from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("page", "heading"),
    (
        ("49_personal_board_v1.py", "Personal Board"),
        ("50_decision_journal_v1.py", "Decision Tracker"),
        ("51_saved_scenarios_v1.py", "Scenario Playground"),
    ),
)
def test_workspace_page_open_is_read_only_and_has_one_h1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    page: str,
    heading: str,
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setenv("NWR_PERSONAL_WORKSPACE_ROOT", str(workspace))
    at = AppTest.from_file(str(ROOT / "app/pages" / page)).run(timeout=40)
    assert not at.exception
    page_source = (ROOT / "app/pages" / page).read_text(encoding="utf-8")
    assert f'page_header(\n    "{heading}"' in page_source
    assert "st.title(" not in page_source
    assert not workspace.exists()


def test_workspace_pages_keep_canonical_and_personal_labels_distinct() -> None:
    personal = (ROOT / "app/pages/49_personal_board_v1.py").read_text(encoding="utf-8")
    journal = (ROOT / "app/pages/50_decision_journal_v1.py").read_text(encoding="utf-8")
    scenarios = (ROOT / "app/pages/51_saved_scenarios_v1.py").read_text(encoding="utf-8")
    assert "My Tier" in personal and "My Rank" in personal and "My Tags" in personal
    assert "Source Rank" in personal and "Canonical read-only" in personal
    assert "Immutable source snapshot" in journal and "No fabricated result" in journal
    assert "No automatic verdict" in scenarios
    prohibited = ("automatic trade winner", "accept recommendation", "hidden combined score")
    assert all(term not in (personal + journal + scenarios).casefold() for term in prohibited)
