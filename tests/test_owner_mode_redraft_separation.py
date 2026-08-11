from __future__ import annotations

from pathlib import Path

from src.services.redraft_engine_v1_service import redraft_store_root

ROOT = Path(__file__).resolve().parents[1]


def test_dynasty_and_redraft_have_separate_launchers_titles_and_navigation() -> None:
    dynasty_main = (ROOT / "app/main.py").read_text(encoding="utf-8")
    redraft_main = (ROOT / "app/main_redraft.py").read_text(encoding="utf-8")
    launcher = (ROOT / "scripts/start_redraft_app.ps1").read_text(encoding="utf-8")
    redraft_page = (ROOT / "app/pages/52_redraft_v1.py").read_text(encoding="utf-8")

    assert 'page_title=f"{APP_NAME} - Dynasty"' in dynasty_main.replace("\N{EM DASH}", "-")
    assert 'page_title="Niners War Room - Redraft"' in redraft_main.replace("\N{EM DASH}", "-")
    assert "app/main_redraft.py" in launcher
    assert "--server.port $Port" in launcher
    assert 'title="Redraft War Room"' in redraft_main
    assert '"Niners War Room - Redraft"' in redraft_page
    assert "Finished V1 dynasty ranks" in redraft_page


def test_redraft_persistence_uses_its_own_namespace(tmp_path: Path) -> None:
    assert redraft_store_root(tmp_path) == tmp_path / "local_exports" / "redraft_v1"
