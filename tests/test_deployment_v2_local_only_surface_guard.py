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


def test_guard_flags_ci_workflow_in_temp_fixture(tmp_path: Path) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "validation.yml").write_text("inert workflow fixture\n", encoding="utf-8")

    violations = guard.scan_repository(tmp_path)

    assert [(violation.path.as_posix(), violation.reason) for violation in violations] == [
        (".github/workflows/validation.yml", "CI/CD workflow file is present")
    ]


def test_guard_flags_forbidden_path_segment_in_temp_fixture(tmp_path: Path) -> None:
    path = tmp_path / "notes" / "k8s" / "readme.txt"
    path.parent.mkdir(parents=True)
    path.write_text("inert forbidden path segment fixture\n", encoding="utf-8")

    violations = guard.scan_repository(tmp_path)

    assert [(violation.path.as_posix(), violation.reason) for violation in violations] == [
        ("notes/k8s/readme.txt", "hosted/container path segment is present: k8s")
    ]


def test_guard_flags_public_tunnel_marker_only_in_command_surface(tmp_path: Path) -> None:
    package_json = tmp_path / "package.json"
    package_json.write_text(
        json.dumps({"scripts": {"validation": "echo inert ngrok marker"}}),
        encoding="utf-8",
    )

    violations = guard.scan_repository(tmp_path)

    assert [(violation.path.as_posix(), violation.reason) for violation in violations] == [
        (
            "package.json",
            "package.json script uses deploy-oriented command: validation",
        )
    ]


def test_guard_flags_hosted_smoke_marker_only_in_command_surface(tmp_path: Path) -> None:
    taskfile = tmp_path / "Taskfile.yml"
    taskfile.write_text(
        "tasks:\n  validation:\n    cmds:\n      - echo inert hosted smoke marker\n",
        encoding="utf-8",
    )

    violations = guard.scan_repository(tmp_path)

    assert [(violation.path.as_posix(), violation.reason) for violation in violations] == [
        (
            "Taskfile.yml",
            r"deploy-oriented command pattern found: \bhosted\s+smoke\b",
        )
    ]


def test_guard_flags_public_route_marker_only_in_command_surface(tmp_path: Path) -> None:
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        "validation:\n\t@echo inert public port and hosted route markers\n",
        encoding="utf-8",
    )

    violations = guard.scan_repository(tmp_path)
    reasons = {violation.reason for violation in violations}

    assert {violation.path.as_posix() for violation in violations} == {"Makefile"}
    assert r"deploy-oriented command pattern found: \bpublic\s+port\b" in reasons
    assert r"deploy-oriented command pattern found: \bhosted\s+route\b" in reasons


def test_guard_skips_local_only_artifact_dirs(tmp_path: Path) -> None:
    for directory_name in ("data", "local_exports", ".venv"):
        path = tmp_path / directory_name / "Dockerfile"
        path.parent.mkdir(parents=True)
        path.write_text("inert skipped-dir fixture\n", encoding="utf-8")

    assert guard.scan_repository(tmp_path) == []


def test_guard_cli_root_option_scans_temp_fixture(tmp_path: Path, capsys) -> None:
    (tmp_path / "render.yaml").write_text("inert platform fixture\n", encoding="utf-8")

    result = guard.main(["--root", str(tmp_path), "--report", "json"])
    output = json.loads(capsys.readouterr().out)

    assert result == 1
    assert output["verdict"] == "RED"
    assert output["violations"] == [
        {
            "path": "render.yaml",
            "reason": "hosted/container/platform manifest is present",
        }
    ]


def test_guard_positional_root_remains_supported(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("ordinary local-only notes\n", encoding="utf-8")

    assert guard.main([str(tmp_path)]) == 0


def test_docs_can_describe_forbidden_surfaces_without_false_positive(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "blocked_surfaces.md").write_text(
        (
            "This note mentions Dockerfile, CI/CD, ngrok, public port, hosted smoke, "
            "and hosted routing as blocked text.\n"
        ),
        encoding="utf-8",
    )

    assert guard.scan_repository(tmp_path) == []


def test_guard_pattern_manifest_categories_have_temp_fixture_coverage(tmp_path: Path) -> None:
    fixtures = {
        "deploy_command": ("Makefile", "deploy:\n\t@echo inert validation marker\n"),
        "platform_config": ("fly.toml", "inert platform fixture\n"),
        "secret_credential": (
            "tox.ini",
            "[testenv]\ndescription = credential marker only\n",
        ),
        "production_runtime": (
            "pyproject.toml",
            "[tool.validation]\nmessage = \"production runtime marker only\"\n",
        ),
        "generated_artifact": (
            "Taskfile.yml",
            "tasks:\n  validation:\n    cmds:\n      - echo generated artifact marker only\n",
        ),
        "generated_path": (
            "notes/kubernetes/readme.txt",
            "inert hosted path segment marker only\n",
        ),
    }

    for directory, (relative_path, content) in fixtures.items():
        fixture_root = tmp_path / directory
        path = fixture_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        assert guard.scan_repository(fixture_root), f"{directory} should be covered"
