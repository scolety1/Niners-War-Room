from __future__ import annotations

import csv
from pathlib import Path

REGISTRY_PATH = Path("docs/hq/integration/evidence_status_registry_v1_20260626.csv")
REQUIRED_COLUMNS = {
    "evidence_lane",
    "artifact_root",
    "current_status",
    "review_only",
    "model_input_allowed",
    "app_wiring_allowed",
    "training_allowed",
    "approved_by_human",
    "source_truth_allowed",
    "display_only_allowed",
    "raw_data_tracked",
    "known_blockers",
    "next_gate",
    "last_known_commit",
    "notes",
}
VALID_STATUS = {"GREEN", "YELLOW", "RED", "BLOCKED", "REVIEW_ONLY", "REVIEW_REQUIRED"}
FORBIDDEN_YES_FLAGS = {
    "model_input_allowed",
    "app_wiring_allowed",
    "training_allowed",
    "raw_data_tracked",
}


def _registry_rows() -> list[dict[str, str]]:
    with REGISTRY_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_evidence_status_registry_loads_and_has_required_columns() -> None:
    rows = _registry_rows()

    assert len(rows) >= 15
    assert REQUIRED_COLUMNS.issubset(rows[0])


def test_evidence_status_registry_artifact_roots_exist() -> None:
    rows = _registry_rows()

    missing = [row["artifact_root"] for row in rows if not Path(row["artifact_root"]).exists()]
    assert missing == []


def test_evidence_status_registry_keeps_forbidden_flags_closed() -> None:
    rows = _registry_rows()

    for row in rows:
        assert row["current_status"] in VALID_STATUS
        for column in FORBIDDEN_YES_FLAGS:
            assert row[column].lower() == "no", (row["evidence_lane"], column, row[column])


def test_evidence_status_registry_keeps_specific_lanes_conservative() -> None:
    rows = {row["evidence_lane"]: row for row in _registry_rows()}

    for lane in (
        "CFBD Identity Matching V1",
        "NFL Usage Evidence Layer V0",
        "Unified Player Universe Review V1",
        "RotoWire Usage Lane",
        "Historical Drop Lists / Proxy Evidence",
        "Model Evaluation Harness V0",
    ):
        assert rows[lane]["model_input_allowed"] == "no"
        assert rows[lane]["training_allowed"] == "no"
        assert rows[lane]["app_wiring_allowed"] == "no"
