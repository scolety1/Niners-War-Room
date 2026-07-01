from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from src.services.nflverse_player_stats_compact_sidecar_derivation_service import (
    ReceiptMismatchError,
    build_compact_sidecar_derivation_packet,
)


def test_compact_derivation_validates_receipt_and_excludes_quarantined_fields(
    tmp_path: Path,
) -> None:
    source = tmp_path / "player_stats_weekly.csv"
    _write_csv(
        source,
        [
            {
                "player_id": "00-safe",
                "player_name": "Safe Player",
                "player_display_name": "Safe Player",
                "position": "WR",
                "team": "SF",
                "season": "2025",
                "week": "1",
                "passing_first_downs": "0",
                "rushing_first_downs": "1",
                "receiving_first_downs": "2",
                "fantasy_points_ppr": "99.9",
            },
            {
                "player_id": "00-review",
                "player_name": "Review Player",
                "player_display_name": "Review Player",
                "position": "RB",
                "team": "SEA",
                "season": "2025",
                "week": "1",
                "passing_first_downs": "1",
                "rushing_first_downs": "1",
                "receiving_first_downs": "1",
                "fantasy_points_ppr": "88.8",
            },
        ],
    )
    seasonal = tmp_path / "player_stats_seasonal.csv"
    _write_csv(
        seasonal,
        [
            {
                "player_id": "00-safe",
                "player_name": "Safe Player",
                "player_display_name": "Safe Player",
                "position": "WR",
                "recent_team": "SF",
                "season": "2025",
                "passing_first_downs": "3",
                "rushing_first_downs": "4",
                "receiving_first_downs": "5",
            }
        ],
    )
    receipt = tmp_path / "receipt.csv"
    _write_csv(
        receipt,
        [
            _receipt_row("player_stats_weekly", source, 2),
            _receipt_row("player_stats_seasonal", seasonal, 1),
        ],
    )
    schema = tmp_path / "schema.csv"
    _write_csv(
        schema,
        [
            _schema_row("passing_first_downs", True),
            _schema_row("rushing_first_downs", True),
            _schema_row("receiving_first_downs", True),
            _schema_row("fantasy_points_ppr", False),
        ],
    )
    player_context = tmp_path / "player_context.csv"
    _write_csv(
        player_context,
        [
            {
                "nwr_player_id": "123",
                "nflverse_gsis_id": "00-safe",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
            },
            {
                "nwr_player_id": "456",
                "nflverse_gsis_id": "00-review",
                "identity_join_status": "NEED_IDENTITY_REVIEW",
                "review_required": "true",
            },
        ],
    )

    out = tmp_path / "out"
    result = build_compact_sidecar_derivation_packet(
        output_root=out,
        receipt_path=receipt,
        schema_path=schema,
        player_context_path=player_context,
    )

    assert result.verdict == "GREEN_COMPACT_SIDECAR_DERIVATION_READY_REVIEW_ONLY"
    candidate_rows = _read_csv(out / "compact_player_stats_sidecar_candidate.csv")
    assert len(candidate_rows) == 2
    assert {row["stat_name"] for row in candidate_rows} == {
        "rushing_first_downs",
        "receiving_first_downs",
    }
    assert {row["nwr_player_id"] for row in candidate_rows} == {"123"}
    assert all(row["sidecar_review_allowed"] == "true" for row in candidate_rows)
    for row in candidate_rows:
        assert row["label_truth_allowed"] == "false"
        assert row["model_use_allowed"] == "false"
        assert row["training_allowed"] == "false"
        assert row["source_truth_allowed"] == "false"
        assert row["source_as_of"] == "Not enough information"
        assert "fantasy_points_ppr" not in row["stat_name"]

    coverage_rows = _read_csv(out / "derivation_coverage_matrix.csv")
    weekly_coverage = {
        row["source_dataset"]: row for row in coverage_rows
    }["player_stats_weekly"]
    assert weekly_coverage["quarantined_fields_excluded"] == "fantasy_points_ppr"
    assert weekly_coverage["rows_derived"] == "2"
    seasonal_coverage = {
        row["source_dataset"]: row for row in coverage_rows
    }["player_stats_seasonal"]
    assert seasonal_coverage["rows_derived"] == "0"
    assert seasonal_coverage["sidecar_builder_allowed"] == "false"


def test_compact_derivation_rejects_receipt_sha_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "player_stats_weekly.csv"
    _write_csv(
        source,
        [
            {
                "player_id": "00-safe",
                "player_name": "Safe Player",
                "player_display_name": "Safe Player",
                "position": "WR",
                "team": "SF",
                "season": "2025",
                "week": "1",
                "passing_first_downs": "1",
                "rushing_first_downs": "0",
                "receiving_first_downs": "0",
            }
        ],
    )
    receipt = tmp_path / "receipt.csv"
    row = _receipt_row("player_stats_weekly", source, 1)
    row["notes"] = row["notes"].replace(_sha256(source), "0" * 64)
    _write_csv(receipt, [row])
    schema = tmp_path / "schema.csv"
    _write_csv(
        schema,
        [
            _schema_row("passing_first_downs", True),
            _schema_row("rushing_first_downs", True),
            _schema_row("receiving_first_downs", True),
        ],
    )
    player_context = tmp_path / "player_context.csv"
    _write_csv(
        player_context,
        [
            {
                "nwr_player_id": "123",
                "nflverse_gsis_id": "00-safe",
                "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                "review_required": "false",
            }
        ],
    )

    with pytest.raises(ReceiptMismatchError):
        build_compact_sidecar_derivation_packet(
            output_root=tmp_path / "out",
            receipt_path=receipt,
            schema_path=schema,
            player_context_path=player_context,
        )


def _receipt_row(source_dataset: str, source_artifact: Path, row_count: int) -> dict[str, str]:
    return {
        "receipt_row_id": f"{source_dataset}__test",
        "source_dataset": source_dataset,
        "source_artifact": str(source_artifact),
        "season": "2025",
        "week": "1",
        "row_count": str(row_count),
        "positions_covered": "position column present",
        "id_columns_present": "player_id|player_name|position|team",
        "stat_columns_present": "passing_first_downs|rushing_first_downs|receiving_first_downs",
        "timestamp_or_asof_present": "source_asof_timestamp=Not enough information",
        "review_use_allowed": "true",
        "label_truth_allowed": "false",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "sidecar_builder_allowed": "true",
        "blocker_reason": "No blocker for test receipt",
        "notes": (
            f"local-only raw snapshot; sha256={_sha256(source_artifact)}; "
            "quarantined_fields=fantasy_points_ppr"
        ),
    }


def _schema_row(field_name: str, allowed_for_review: bool) -> dict[str, str]:
    return {
        "field_name": field_name,
        "field_type_or_example": "present",
        "source_dataset": "player_stats_weekly",
        "required_for_sidecar": "true",
        "allowed_for_review": "true" if allowed_for_review else "false",
        "label_truth_allowed": "false",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "missingness_rule": "Missing data remains Not enough information.",
        "notes": "test schema row",
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
