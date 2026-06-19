from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_deployment_v2_docs_consistency.py"
)
SPEC = importlib.util.spec_from_file_location("audit_deployment_v2_docs_consistency", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


BASE_DOC = """# Deployment V2 Test

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command exists.

Normal operator app path is C:\\NWR\\Niners-War-Room-outcome.

Normal operator branch is main.

Deployment V2 checkout is not the operator app path.
"""


def _write_doc(docs_dir: Path, text: str) -> None:
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "DEPLOYMENT_V2_TEST.md").write_text(text, encoding="utf-8")


def _statuses(findings: list[object]) -> dict[str, str]:
    return {finding.check: finding.status for finding in findings}


def test_current_path_docs_pass(tmp_path: Path) -> None:
    _write_doc(tmp_path, BASE_DOC)

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "GREEN"


def test_missing_hosted_blocked_language_is_red(tmp_path: Path) -> None:
    _write_doc(tmp_path, BASE_DOC.replace("Hosted deployment remains blocked.\n\n", ""))

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "RED"
    assert _statuses(findings)["hosted_blocked"] == "RED"


def test_missing_local_only_language_is_red(tmp_path: Path) -> None:
    _write_doc(tmp_path, BASE_DOC.replace("V1 remains `local_only`.\n\n", ""))

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "RED"
    assert _statuses(findings)["local_only"] == "RED"


def test_missing_no_deploy_command_language_is_red(tmp_path: Path) -> None:
    _write_doc(tmp_path, BASE_DOC.replace("No deploy command exists.\n\n", ""))

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "RED"
    assert _statuses(findings)["no_deploy_command"] == "RED"


def test_current_operator_path_mismatch_is_red(tmp_path: Path) -> None:
    _write_doc(
        tmp_path,
        BASE_DOC.replace(
            r"C:\NWR\Niners-War-Room-outcome",
            r"C:\Somewhere\Else",
        ),
    )

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "RED"
    assert _statuses(findings)["current_operator_path"] == "RED"


def test_missing_normal_operator_branch_language_is_red(tmp_path: Path) -> None:
    _write_doc(tmp_path, BASE_DOC.replace("Normal operator branch is main.\n\n", ""))

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "RED"
    assert _statuses(findings)["normal_operator_branch"] == "RED"


def test_legacy_vacation_path_with_current_path_is_note(tmp_path: Path) -> None:
    _write_doc(
        tmp_path,
        BASE_DOC
        + "\nHistorical path: C:\\Users\\smcol\\Documents\\Vacation\\Niners-War-Room-outcome.\n",
    )

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "GREEN"
    assert _statuses(findings)["legacy_operator_path_note"] == "NOTE"


def test_deploy_ready_language_is_red(tmp_path: Path) -> None:
    _write_doc(tmp_path, BASE_DOC + "\nHosted deployment is ready for operators.\n")

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "RED"
    assert _statuses(findings)["hosted_ready_language"] == "RED"


def test_hosted_enabled_language_is_red(tmp_path: Path) -> None:
    _write_doc(tmp_path, BASE_DOC + "\nHosting is enabled for operators.\n")

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "RED"
    assert _statuses(findings)["hosted_ready_language"] == "RED"


def test_blocked_example_hosted_ready_language_is_allowed(tmp_path: Path) -> None:
    _write_doc(
        tmp_path,
        BASE_DOC
        + "\nForbidden example: hosted deployment ready language remains blocked.\n",
    )

    findings = audit.audit_docs(tmp_path)

    assert audit.verdict(findings) == "GREEN"


def test_json_output_groups_required_missing_notes_and_blocked_language(tmp_path: Path) -> None:
    _write_doc(
        tmp_path,
        BASE_DOC.replace("No deploy command exists.\n\n", "")
        + "\nHosted deployment is ready for operators.\n"
        + "\nHistorical path: C:\\Users\\smcol\\Documents\\Vacation\\Niners-War-Room-outcome.\n",
    )

    report = audit.findings_to_dict(audit.audit_docs(tmp_path))

    assert report["verdict"] == "RED"
    assert {item["check"] for item in report["required_phrases"]} >= {
        "local_only",
        "hosted_blocked",
        "no_deploy_command",
    }
    assert report["missing_phrases"] == [
        {
            "status": "RED",
            "check": "no_deploy_command",
            "detail": "missing required docs language: deploy command",
        }
    ]
    assert report["blocked_language_hits"][0]["check"] == "hosted_ready_language"
    assert report["historical_path_notes"][0]["check"] == "legacy_operator_path_note"
    assert report["notes"][0]["status"] == "NOTE"
