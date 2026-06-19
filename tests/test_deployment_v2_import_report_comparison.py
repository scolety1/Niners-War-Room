from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from zipfile import ZipFile

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "compare_deployment_v2_import_report.py"
)
SPEC = importlib.util.spec_from_file_location("compare_deployment_v2_import_report", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
compare_helper = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = compare_helper
SPEC.loader.exec_module(compare_helper)


def _report_text(head_full: str = "abc123", head_short: str = "abc123") -> str:
    return f"""# Deployment V2 Import Check

- Repo path: C:\\NWR\\Niners-War-Room-deploy-v2
- Expected branch: work/deployment-v2-discovery
- Current branch: work/deployment-v2-discovery
- HEAD full: {head_full}
- HEAD short: {head_short}
- Commit subject: Imported branch
- Dirty files exist: False
- Untracked files exist: False
- Diff check passed: True
- Verdict: GREEN
"""


def _current_state(
    *,
    branch: str = "work/deployment-v2-discovery",
    head_full: str = "abc123",
    report_head_is_ancestor: bool | None = None,
    status_short: str = "",
    diff_check_output: str = "",
) -> object:
    return compare_helper.CurrentState(
        repo_path=Path("C:/NWR/Niners-War-Room-deploy-v2"),
        branch=branch,
        head_full=head_full,
        head_short=head_full[:7],
        commit_subject="Current branch",
        status_short=status_short,
        diff_check_output=diff_check_output,
        report_head_is_ancestor=report_head_is_ancestor,
    )


def test_reads_deployment_v2_report_from_zip(tmp_path: Path) -> None:
    zip_path = tmp_path / "import_check.zip"
    with ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr("05_DEPLOYMENT_V2.md", _report_text())

    report, error = compare_helper.read_deployment_report(zip_path)

    assert error is None
    assert report is not None
    assert report.expected_branch == "work/deployment-v2-discovery"
    assert report.verdict == "GREEN"


def test_missing_report_returns_yellow_result(tmp_path: Path) -> None:
    zip_path = tmp_path / "import_check.zip"
    with ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr("00_MASTER_SUMMARY.md", "No Deployment V2 report")

    report, error = compare_helper.read_deployment_report(zip_path)
    result = compare_helper.compare(report, _current_state(), error)

    assert result.verdict == "YELLOW"
    assert "missing 05_DEPLOYMENT_V2.md" in result.messages[0]


def test_missing_zip_path_returns_yellow_result(tmp_path: Path) -> None:
    zip_path = tmp_path / "missing.zip"

    report, error = compare_helper.read_deployment_report(zip_path)
    result = compare_helper.compare(report, _current_state(), error)

    assert result.verdict == "YELLOW"
    assert "zip file missing:" in result.messages[0]


def test_invalid_zip_returns_yellow_result(tmp_path: Path) -> None:
    zip_path = tmp_path / "invalid.zip"
    zip_path.write_text("not a zip fixture\n", encoding="utf-8")

    report, error = compare_helper.read_deployment_report(zip_path)
    result = compare_helper.compare(report, _current_state(), error)

    assert result.verdict == "YELLOW"
    assert "invalid zip file:" in result.messages[0]


def test_report_without_head_line_returns_yellow_result(tmp_path: Path) -> None:
    zip_path = tmp_path / "import_check.zip"
    text = _report_text().replace("- HEAD full: abc123\n", "")
    with ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr("05_DEPLOYMENT_V2.md", text)

    report, error = compare_helper.read_deployment_report(zip_path)
    result = compare_helper.compare(report, _current_state(), error)

    assert result.verdict == "YELLOW"
    assert "missing HEAD full" in result.messages[0]


def test_clean_descendant_of_green_report_is_green() -> None:
    report = compare_helper.ImportReport(
        repo_path=r"C:\NWR\Niners-War-Room-deploy-v2",
        expected_branch="work/deployment-v2-discovery",
        current_branch="work/deployment-v2-discovery",
        head_full="abc123",
        head_short="abc123",
        commit_subject="Imported branch",
        dirty_files_exist="False",
        untracked_files_exist="False",
        diff_check_passed="True",
        verdict="GREEN",
    )

    result = compare_helper.compare(
        report,
        _current_state(head_full="def456", report_head_is_ancestor=True),
        None,
    )

    assert result.verdict == "GREEN"
    assert "current HEAD is a clean descendant of import report HEAD" in result.messages


def test_branch_mismatch_is_red() -> None:
    report = compare_helper.ImportReport(
        repo_path=r"C:\NWR\Niners-War-Room-deploy-v2",
        expected_branch="work/deployment-v2-discovery",
        current_branch="work/deployment-v2-discovery",
        head_full="abc123",
        head_short="abc123",
        commit_subject="Imported branch",
        dirty_files_exist="False",
        untracked_files_exist="False",
        diff_check_passed="True",
        verdict="GREEN",
    )

    result = compare_helper.compare(report, _current_state(branch="main"), None)

    assert result.verdict == "RED"
    assert "branch mismatch: current main, expected work/deployment-v2-discovery" in result.messages


def test_report_head_not_ancestor_is_red() -> None:
    report = compare_helper.ImportReport(
        repo_path=r"C:\NWR\Niners-War-Room-deploy-v2",
        expected_branch="work/deployment-v2-discovery",
        current_branch="work/deployment-v2-discovery",
        head_full="abc123",
        head_short="abc123",
        commit_subject="Imported branch",
        dirty_files_exist="False",
        untracked_files_exist="False",
        diff_check_passed="True",
        verdict="GREEN",
    )

    result = compare_helper.compare(
        report,
        _current_state(head_full="def456", report_head_is_ancestor=False),
        None,
    )

    assert result.verdict == "RED"
    assert "current HEAD does not match or descend from import report HEAD" in result.messages


def test_dirty_current_checkout_is_red() -> None:
    report = compare_helper.ImportReport(
        repo_path=r"C:\NWR\Niners-War-Room-deploy-v2",
        expected_branch="work/deployment-v2-discovery",
        current_branch="work/deployment-v2-discovery",
        head_full="abc123",
        head_short="abc123",
        commit_subject="Imported branch",
        dirty_files_exist="False",
        untracked_files_exist="False",
        diff_check_passed="True",
        verdict="GREEN",
    )

    result = compare_helper.compare(
        report,
        _current_state(status_short=" M docs/example.md"),
        None,
    )

    assert result.verdict == "RED"
    assert "current git status is not clean" in result.messages
