from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_local_only_surface_guard.py"
)
SPEC = importlib.util.spec_from_file_location("validate_local_only_surface_guard", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


def test_current_repository_has_no_deploy_surface() -> None:
    root = Path(__file__).resolve().parents[1]

    assert guard.scan_repository(root) == []


def test_local_streamlit_command_is_not_a_deploy_surface(tmp_path: Path) -> None:
    package_json = tmp_path / "package.json"
    package_json.write_text(
        json.dumps({"scripts": {"local": "streamlit run app/main.py"}}),
        encoding="utf-8",
    )

    assert guard.scan_repository(tmp_path) == []


def test_guard_flags_container_manifest_and_deploy_command(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"deploy": "vercel --prod"}}),
        encoding="utf-8",
    )

    violations = guard.scan_repository(tmp_path)
    reasons = {violation.reason for violation in violations}
    paths = {violation.path.as_posix() for violation in violations}

    assert "Dockerfile" in paths
    assert "package.json" in paths
    assert "hosted/container/platform manifest is present" in reasons
    assert "package.json deploy script exists: deploy" in reasons
