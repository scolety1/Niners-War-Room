from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

from src.services.draft_day_app_v1_service import (
    EXPECTED_PINNED_MANIFEST_HASH,
    EXPECTED_ROW_COUNT,
    REPO_SAFE_FROZEN_BOARD_PATH,
    pinned_manifest_hash,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = REPO_ROOT / "docs" / "hq" / "audits" / "agent_audit_synthesis_20260626"


REQUIRED_AUDIT_FILES = {
    "00_START_HERE_CODEX.md",
    "01_HQ_AUDIT_SYNTHESIS.md",
    "02_CONSOLIDATED_CODEX_ACTION_MATRIX.csv",
    "03_LIVE_DRAFT_V2_REQUIREMENTS.md",
    "04_DATA_MODEL_GUARDRAILS.md",
    "05_CFBD_REVIEW_ONLY_SYNTHESIS.md",
    "06_ENGINEERING_QA_SECURITY_SYNTHESIS.md",
    "07_REJECT_DEFER_BLOCK_LIST.md",
    "08_VALIDATION_AND_SOURCE_INVENTORY.md",
    "09_CODEX_PROMPT_A_AUDIT_INTAKE_GUARDRAILS.md",
    "10_CODEX_PROMPT_B_LIVE_DRAFT_V2_RELIABILITY.md",
    "csv_parse_warnings.csv",
    "OUTPUT_MANIFEST.csv",
    "source_inventory_69_files.csv",
    "source_zip_manifest.csv",
    "NWR_AUDIT_INTAKE_GUARDRAIL_VALIDATION_20260626.md",
}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_audit_archive_required_files_exist() -> None:
    missing = [name for name in REQUIRED_AUDIT_FILES if not (AUDIT_DIR / name).is_file()]
    assert missing == []


def test_source_inventory_and_zip_manifest_preserved() -> None:
    source_inventory = _csv_rows(AUDIT_DIR / "source_inventory_69_files.csv")
    source_manifest = _csv_rows(AUDIT_DIR / "source_zip_manifest.csv")

    assert len(source_inventory) == 69
    assert len(source_manifest) == 6
    assert {row["uploaded_zip"] for row in source_manifest} == {
        "NWR_CFBD_AGENT3_FINAL_SYNTHESIS_CODEX_HANDOFF_20260626.zip",
        "NWR_CFBD_AGENT_2_CODEX_HANDOFF_20260626.zip",
        "NWR_CFBD_AGENT1_IDENTITY_VERIFICATION_CODEX_HANDOFF_20260626.zip",
        "NWR_AGENT_3_ENGINEERING_QA_SECURITY_ARCH_AUDIT_CODEX_HANDOFF_20260626.zip",
        "NWR_AGENT_2_MODEL_DATA_EVIDENCE_AUDIT_CODEX_HANDOFF_20260626.zip",
        "NWR_AGENT_1_APP_UX_LIVE_DRAFT_RELIABILITY_AUDIT_CODEX_HANDOFF_20260626.zip",
    }
    assert all(row["sha256"] for row in source_manifest)


def test_malformed_audit_csv_warnings_are_preserved() -> None:
    warnings = _csv_rows(AUDIT_DIR / "csv_parse_warnings.csv")

    assert len(warnings) >= 3
    assert all("," in row["field_counts"] for row in warnings)
    assert any("agent_audit_findings.csv" in row["relative_path"] for row in warnings)


def test_action_matrix_keeps_initial_tasks_safe_and_protected() -> None:
    rows = _csv_rows(AUDIT_DIR / "02_CONSOLIDATED_CODEX_ACTION_MATRIX.csv")
    by_id = {row["task_id"]: row for row in rows}

    assert by_id["INTAKE-01"]["safe_now"] == "YES"
    assert by_id["INTAKE-02"]["safe_now"] == "YES"
    assert by_id["GUARD-01"]["safe_now"] == "YES"
    protected_text = " ".join(row["do_not_touch"] for row in rows)
    for token in [
        "Frozen board",
        "final_board_rank",
        "Dynasty Rank",
        "latest_candidate",
        "latest_approved",
        "pinned snapshot",
    ]:
        assert token in protected_text


def test_cfbd_synthesis_preserves_final_review_only_counts() -> None:
    text = (AUDIT_DIR / "05_CFBD_REVIEW_ONLY_SYNTHESIS.md").read_text(encoding="utf-8")

    assert re.search(r"Rows reviewed:\s*\*\*15\*\*", text)
    assert re.search(r"APPROVE:\s*\*\*4\*\*", text)
    assert re.search(r"KEEP_BLOCKED:\s*\*\*8\*\*", text)
    assert re.search(r"NEEDS_MORE_INFO:\s*\*\*3\*\*", text)
    assert "`model_use_allowed=false`" in text
    assert "`training_allowed=false`" in text
    assert "`review_only=true`" in text
    assert "promote Agent APPROVE to human approval" in text
    assert "make CFBD production model input" in text


def test_guardrail_doc_blocks_missingness_coercion_and_forbidden_inputs() -> None:
    text = (AUDIT_DIR / "04_DATA_MODEL_GUARDRAILS.md").read_text(encoding="utf-8")

    assert "Missing values must not become zero/clean/average" in text
    assert "missing age => `Not enough information`" in text
    assert "missing injury/status => `Not enough information`, not healthy" in text
    assert "missing outcome => `Not enough information`, not zero probability" in text
    for blocked in [
        "DynastyProcess values",
        "ADP",
        "market rank/value/gap",
        "true routes",
        "TPRR",
        "YPRR",
        "CFBD review-only production fields",
        "NFL usage review-only fields before gate",
        "proxy drop labels",
    ]:
        assert blocked in text


def test_audit_archive_is_not_wired_into_app_or_services() -> None:
    code_files = [
        *list((REPO_ROOT / "app").rglob("*.py")),
        *list((REPO_ROOT / "src").rglob("*.py")),
    ]

    offenders = [
        path
        for path in code_files
        if "agent_audit_synthesis_20260626"
        in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == []


def test_no_raw_shared_local_secret_or_runtime_files_are_tracked() -> None:
    tracked = subprocess.check_output(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
    ).splitlines()

    forbidden_patterns = [
        "C:/NWR_SHARED_DATA",
        "C:\\NWR_SHARED_DATA",
        "C:/NWR_LOCAL_SECRETS",
        "C:\\NWR_LOCAL_SECRETS",
        "local_exports/",
        "runtime.json",
        "draft_runtime_state",
        "api_key",
        "cfbd_api_key",
    ]
    offenders = [
        path
        for path in tracked
        if any(pattern.lower() in path.lower() for pattern in forbidden_patterns)
    ]
    assert offenders == []


def test_frozen_board_row_count_and_pinned_hash_remain_unchanged() -> None:
    with REPO_SAFE_FROZEN_BOARD_PATH.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == EXPECTED_ROW_COUNT == 66
    assert pinned_manifest_hash() == EXPECTED_PINNED_MANIFEST_HASH
