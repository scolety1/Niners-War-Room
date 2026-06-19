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


def test_guard_report_json_shape_for_clean_local_tree(tmp_path: Path) -> None:
    package_json = tmp_path / "package.json"
    package_json.write_text(
        json.dumps({"scripts": {"local": "streamlit run app/main.py"}}),
        encoding="utf-8",
    )

    report = guard.build_report(tmp_path)
    json_report = guard.report_to_json_dict(report)

    assert json_report["verdict"] == "GREEN"
    assert json_report["checked_path_count"] == 1
    assert json_report["blocked_surface_count"] == 0
    assert json_report["reason_summary"] == {}
    assert json_report["violations"] == []
    assert "command_surface_files" in json_report["checked_categories"]


def test_guard_report_json_shape_for_blocked_surface(tmp_path: Path) -> None:
    (tmp_path / "Procfile").write_text("not a real deployment fixture\n", encoding="utf-8")

    report = guard.build_report(tmp_path)
    json_report = guard.report_to_json_dict(report)

    assert json_report["verdict"] == "RED"
    assert json_report["blocked_surface_count"] == 1
    assert json_report["reason_summary"] == {
        "hosted/container/platform manifest is present": 1
    }
    assert json_report["violations"] == [
        {
            "path": "Procfile",
            "reason": "hosted/container/platform manifest is present",
        }
    ]
