from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "print_deployment_v2_operator_transcript.py"
)
SPEC = importlib.util.spec_from_file_location(
    "print_deployment_v2_operator_transcript",
    MODULE_PATH,
)
assert SPEC is not None
assert SPEC.loader is not None
transcript = importlib.util.module_from_spec(SPEC)
scripts_dir = str(Path(__file__).resolve().parents[1] / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)
sys.modules[SPEC.name] = transcript
SPEC.loader.exec_module(transcript)


def test_transcript_includes_required_sections(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        transcript,
        "run_readiness_checks",
        lambda _repo, _python, _zip=None, _baseline=None: [
            SimpleNamespace(name="branch", status="GREEN", detail="work/deployment-v2-discovery"),
            SimpleNamespace(name="head", status="GREEN", detail="abc123 Test"),
            SimpleNamespace(name="status", status="GREEN", detail="clean"),
            SimpleNamespace(name="diff_check", status="GREEN", detail="clean"),
            SimpleNamespace(name="local_only_guard", status="GREEN", detail="passed"),
            SimpleNamespace(name="local_only_guard_report", status="GREEN", detail="verdict=GREEN"),
            SimpleNamespace(
                name="import_report_comparison",
                status="SKIPPED",
                detail="no import zip supplied",
            ),
            SimpleNamespace(name="baseline_ancestry", status="SKIPPED", detail="no baseline supplied"),
            SimpleNamespace(name="docs_consistency_audit", status="GREEN", detail="docs ok"),
        ],
    )
    monkeypatch.setattr(
        transcript,
        "audit_docs",
        lambda _docs: [SimpleNamespace(status="GREEN", check="docs_consistency", detail="ok")],
    )

    output = transcript.build_transcript(tmp_path, sys.executable)

    assert "LANE: Deployment V2" in output
    assert "READINESS RUNNER: GREEN" in output
    assert "BASELINE ANCESTRY: SKIPPED - no baseline supplied" in output
    assert "DOCS CONSISTENCY: GREEN" in output
    assert "HOSTED DEPLOYMENT: BLOCKED" in output
    assert "FINAL VERDICT: GREEN" in output


def test_transcript_output_path_is_optional_temp_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(transcript, "build_transcript", lambda *_args: "FINAL VERDICT: GREEN\n")
    output_path = tmp_path / "transcript.txt"

    result = transcript.main(["--repo", str(tmp_path), "--output", str(output_path)])

    assert result == 0
    assert output_path.read_text(encoding="utf-8") == "FINAL VERDICT: GREEN\n"


def test_transcript_json_report_shape(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        transcript,
        "run_readiness_checks",
        lambda _repo, _python, _zip=None, _baseline=None: [
            SimpleNamespace(name="branch", status="GREEN", detail="work/deployment-v2-discovery"),
            SimpleNamespace(name="head", status="GREEN", detail="abc123 Test"),
            SimpleNamespace(name="status", status="GREEN", detail="clean"),
            SimpleNamespace(name="diff_check", status="GREEN", detail="clean"),
            SimpleNamespace(name="local_only_guard", status="GREEN", detail="passed"),
            SimpleNamespace(name="local_only_guard_report", status="GREEN", detail="verdict=GREEN"),
            SimpleNamespace(name="import_report_comparison", status="SKIPPED", detail="no zip"),
            SimpleNamespace(name="baseline_ancestry", status="GREEN", detail="baseline ok"),
            SimpleNamespace(name="docs_consistency_audit", status="GREEN", detail="docs ok"),
        ],
    )
    monkeypatch.setattr(
        transcript,
        "audit_docs",
        lambda _docs: [SimpleNamespace(status="GREEN", check="docs_consistency", detail="ok")],
    )

    report = transcript.build_transcript_report(tmp_path, sys.executable)

    assert report["lane"] == "Deployment V2"
    assert report["final_verdict"] == "GREEN"
    assert report["branch"]["detail"] == "work/deployment-v2-discovery"
    assert report["baseline_ancestry"]["status"] == "GREEN"
    assert report["hosted_deployment"] == "BLOCKED"


def test_transcript_passes_baseline_to_readiness(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, str | None] = {}

    def fake_readiness(_repo, _python, _zip=None, _baseline=None):
        captured["baseline"] = _baseline
        return [
            SimpleNamespace(name="branch", status="GREEN", detail="work/deployment-v2-discovery"),
            SimpleNamespace(name="head", status="GREEN", detail="abc123 Test"),
            SimpleNamespace(name="status", status="GREEN", detail="clean"),
            SimpleNamespace(name="diff_check", status="GREEN", detail="clean"),
            SimpleNamespace(name="local_only_guard", status="GREEN", detail="passed"),
            SimpleNamespace(name="local_only_guard_report", status="GREEN", detail="verdict=GREEN"),
            SimpleNamespace(name="baseline_ancestry", status="GREEN", detail="baseline ok"),
        ]

    monkeypatch.setattr(transcript, "run_readiness_checks", fake_readiness)
    monkeypatch.setattr(
        transcript,
        "audit_docs",
        lambda _docs: [SimpleNamespace(status="GREEN", check="docs_consistency", detail="ok")],
    )

    output = transcript.build_transcript(tmp_path, sys.executable, baseline="base123")

    assert captured["baseline"] == "base123"
    assert "BASELINE ANCESTRY: GREEN - baseline ok" in output


def test_transcript_json_cli_output_is_parseable(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(
        transcript,
        "build_transcript_report",
        lambda *_args: {
            "lane": "Deployment V2",
            "final_verdict": "GREEN",
            "branch": {"status": "GREEN"},
            "head": {"status": "GREEN"},
            "remaining_blockers": ["hosted target"],
        },
    )

    result = transcript.main(["--repo", str(tmp_path), "--json"])

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["lane"] == "Deployment V2"
    assert output["final_verdict"] == "GREEN"


def test_transcript_prints_to_stdout_by_default(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(
        transcript,
        "build_transcript",
        lambda *_args: (
            "LANE: Deployment V2\n"
            "BRANCH: GREEN - work/deployment-v2-discovery\n"
            "HEAD: GREEN - abc123 Test\n"
            "REMAINING HOSTED BLOCKERS:\n"
            "- hosted target\n"
            "FINAL VERDICT: GREEN\n"
        ),
    )

    result = transcript.main(["--repo", str(tmp_path)])

    assert result == 0
    output = capsys.readouterr().out
    assert "BRANCH: GREEN - work/deployment-v2-discovery" in output
    assert "HEAD: GREEN - abc123 Test" in output
    assert "FINAL VERDICT: GREEN" in output
    assert not any(tmp_path.iterdir())
