from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RD_ROOT = ROOT / "docs" / "hq" / "rookie_outcomes" / "rookie_outcome_rd_20260629"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_rookie_outcome_rd_required_docs_exist_and_block_build() -> None:
    required = [
        "00_ROOKIE_OUTCOME_REPO_INVENTORY.md",
        "01_CFBD_IDENTITY_PRODUCTION_READINESS_AUDIT.md",
        "02_ROOKIE_OUTCOME_TARGET_LABEL_SPEC.md",
        "03_DRAFT_CAPITAL_NFL_ENTRY_AUDIT.md",
        "04_HISTORICAL_ROOKIE_LABEL_AVAILABILITY_AUDIT.md",
        "05_ROOKIE_FEATURE_POLICY_AUDIT.md",
        "06_ROOKIE_OUTCOME_FEASIBILITY_DECISION.md",
        "README.md",
    ]

    for name in required:
        assert (RD_ROOT / name).exists(), name

    decision = _text(RD_ROOT / "06_ROOKIE_OUTCOME_FEASIBILITY_DECISION.md")
    assert "`BLOCKED_NEEDS_CFBD_APPROVAL`" in decision
    assert "active rookie T6/T12/T24/T36 probabilities" in decision
    assert "Separate Rankings integration gate" in decision


def test_cfbd_readiness_matrix_keeps_all_rows_review_only() -> None:
    rows = _rows(RD_ROOT / "rookie_cfbd_readiness_matrix.csv")

    assert len(rows) == 213
    assert {row["review_only"].lower() for row in rows} == {"true"}
    assert {row["approved_by_human"].lower() for row in rows} == {"false"}
    assert {row["model_use_allowed"].lower() for row in rows} == {"false"}
    assert {row["training_allowed"].lower() for row in rows} == {"false"}
    assert {
        "BLOCKED_NEEDS_HUMAN_APPROVAL",
        "BLOCKED_NEEDS_IDENTITY_CONFIDENCE",
        "BLOCKED_AMBIGUOUS_IDENTITY",
    }.issuperset({row["rookie_outcome_ready_status"] for row in rows})


def test_draft_capital_matrix_blocks_model_and_training_use() -> None:
    rows = _rows(RD_ROOT / "rookie_draft_capital_availability_matrix.csv")

    assert rows
    assert {row["approved_for_model_use"].lower() for row in rows} == {"false"}
    assert {row["training_allowed"].lower() for row in rows} == {"false"}
    assert {row["review_only"].lower() for row in rows} == {"true"}
    assert any(row["availability_status"] == "partial_local_only" for row in rows)
    assert any("local_exports" in row["blocked_reason"] for row in rows)


def test_feature_policy_matrix_keeps_features_blocked_or_review_only() -> None:
    rows = _rows(RD_ROOT / "rookie_feature_policy_matrix.csv")

    statuses = {row["policy_status"] for row in rows}
    assert statuses <= {"review_only", "blocked", "blocked_for_model"}
    assert not any(status in {"allowed_now", "approved"} for status in statuses)
    assert any(row["feature_family"] == "market_adp_dynastyprocess" for row in rows)


def test_missing_data_policy_is_not_zero_or_clean() -> None:
    spec = _text(RD_ROOT / "02_ROOKIE_OUTCOME_TARGET_LABEL_SPEC.md")

    assert "Missing means `Not enough information`." in spec
    assert "0%" in spec
    assert "healthy" in spec
    assert "clean" in spec


def test_no_rookie_outcome_artifact_or_rankings_integration_created() -> None:
    forbidden_artifacts = [
        RD_ROOT / "rookie_outcome_probabilities.csv",
        RD_ROOT / "rookie_outcome_display.csv",
        RD_ROOT / "rookie_outcome_model_scores.csv",
    ]

    for path in forbidden_artifacts:
        assert not path.exists(), path

    rankings_page = ROOT / "app" / "pages" / "20_rankings_v2.py"
    if rankings_page.exists():
        text = rankings_page.read_text(encoding="utf-8")
        assert "rookie_outcome_rd_20260629" not in text
        assert "rookie_outcome_probabilities" not in text
