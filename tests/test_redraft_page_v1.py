from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
REDRAFT_PAGE = REPO_ROOT / "app" / "pages" / "52_redraft_v1.py"
COMPARE_PAGE = REPO_ROOT / "app" / "pages" / "22_player_compare_v1.py"
COCKPIT_PAGE = REPO_ROOT / "app" / "pages" / "21_live_draft_room_v1.py"


def test_redraft_page_open_with_no_profiles_is_read_only(tmp_path, monkeypatch) -> None:
    store = tmp_path / "redraft-store"
    monkeypatch.setenv("NWR_REDRAFT_HOME", str(store))
    app = AppTest.from_file(REDRAFT_PAGE).run(timeout=40)
    assert not app.exception
    assert any("No redraft profiles exist yet" in item.value for item in app.info)
    assert any("REDRAFT - CURRENT SEASON" in item.value for item in app.warning)
    assert not store.exists()


def test_redraft_page_exposes_required_review_only_surfaces() -> None:
    text = REDRAFT_PAGE.read_text(encoding="utf-8")
    for label in (
        "League Profile",
        "Rankings",
        "Tiers",
        "Position Rankings",
        "Draft Board",
        "Cheat Sheet",
        "Data Health",
        "REDRAFT_AUTHORITY_LABEL",
        "DYNASTY_AUTHORITY_LABEL",
    ):
        assert label in text
    assert "st.download_button" in text
    assert "Confirm permanent delete" in text
    assert "Install approved projection snapshot" in text
    assert "Independent approval receipt" in text
    assert "Restore archived profile" in text
    assert "Projection SHA256" in text
    assert "Stable identity uniqueness" in text
    assert "nwr-redraft-page" in text
    assert 'div[data-testid="stAlert"] p' in text
    assert "Undo last pick" in text
    assert 'columns + ["Rookie", "Evidence", "Source"]' in text


def test_compare_and_cockpit_use_explicit_redraft_context_without_replacing_dynasty() -> None:
    compare = COMPARE_PAGE.read_text(encoding="utf-8")
    cockpit = COCKPIT_PAGE.read_text(encoding="utf-8")
    assert "DYNASTY - LONG TERM" in compare
    assert "REDRAFT - CURRENT SEASON" in compare
    assert "Dynasty comparison remains available and unchanged" in compare
    assert "redraft_compare_pool_rows" in compare
    assert "BLOCKED_2026_ROOKIES.csv" in compare
    assert 'compare_universe.errors and comparison_context == "DYNASTY - LONG TERM"' in compare
    assert "Top remaining by redraft rank" in cockpit
    assert "No automatic best-pick authority" in cockpit
    assert "separate from the dynasty draft workflow" in cockpit
