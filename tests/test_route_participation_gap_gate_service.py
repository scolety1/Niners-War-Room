from __future__ import annotations

import csv
from pathlib import Path

from src.services.route_participation_gap_gate_service import (
    build_route_participation_gap_gate_report,
    write_route_participation_gap_gate_report,
)


def test_route_participation_gap_gate_labels_missing_proxy_and_paid_materiality(
    tmp_path: Path,
) -> None:
    model_dir = _model_dir(tmp_path)

    report = build_route_participation_gap_gate_report(model_dir)
    row = _player_row(report.rows, "Route Gap WR")
    top_50 = _area_row(report.area_rows, "Top 50 overall")
    wr_te = _area_row(report.area_rows, "WR/TE top 30")

    assert row["route_participation_status"] == "unavailable_free_public"
    assert row["route_source_status"] == "unavailable_free_public"
    assert row["paid_data_materiality"] == "high"
    assert "routes_run" in str(row["paid_data_fields"])
    assert top_50["status"] == "review"
    assert top_50["gap_count"] >= 1
    assert wr_te["paid_data_material_count"] == 3


def test_route_participation_gap_gate_labels_imported_and_neutral_defaults(
    tmp_path: Path,
) -> None:
    model_dir = _model_dir(tmp_path)

    report = build_route_participation_gap_gate_report(model_dir)
    imported = _player_row(report.rows, "Route Known WR")
    neutral = _player_row(report.rows, "Neutral TE")

    assert imported["route_participation_status"] == "proxy_only_snap_target"
    assert imported["paid_data_materiality"] == "high"
    assert neutral["route_participation_status"] == "missing_paid_or_charted_data"
    assert neutral["paid_data_materiality"] == "high"


def test_route_participation_gap_gate_tracks_niners_and_rb_receiving_slices(
    tmp_path: Path,
) -> None:
    model_dir = _model_dir(tmp_path)

    report = build_route_participation_gap_gate_report(model_dir)
    niners = _area_row(report.area_rows, "Niners roster")
    rb_receiving = _area_row(report.area_rows, "RB receiving-role players")

    assert niners["player_count"] == 1
    assert niners["priority_players"] == "Route Gap WR"
    assert rb_receiving["player_count"] == 1
    assert rb_receiving["paid_data_material_count"] == 1


def test_route_participation_gap_gate_writes_reports(tmp_path: Path) -> None:
    model_dir = _model_dir(tmp_path)
    report = build_route_participation_gap_gate_report(model_dir)

    paths = write_route_participation_gap_gate_report(tmp_path / "out", report)

    assert paths["players"].exists()
    assert paths["areas"].exists()
    assert paths["summary"].exists()


def _model_dir(tmp_path: Path) -> Path:
    root = tmp_path / "model"
    _write_csv(
        root / "stats_first_normalized_features.csv",
        (
            "player_id",
            "player_name",
            "position",
            "team",
            "route_role",
            "target_earning_stability",
            "role_security",
            "workload_earning",
            "confidence",
            "warnings",
        ),
        [
            {
                "player_id": "wr_gap",
                "player_name": "Route Gap WR",
                "position": "WR",
                "team": "SF",
                "route_role": "50",
                "target_earning_stability": "50",
                "role_security": "70",
                "workload_earning": "40",
                "confidence": "66",
                "warnings": "missing_participation_proxy",
            },
            {
                "player_id": "wr_known",
                "player_name": "Route Known WR",
                "position": "WR",
                "team": "DET",
                "route_role": "88",
                "target_earning_stability": "82",
                "role_security": "86",
                "workload_earning": "52",
                "confidence": "86",
                "warnings": "",
            },
            {
                "player_id": "te_neutral",
                "player_name": "Neutral TE",
                "position": "TE",
                "team": "JAX",
                "route_role": "50",
                "target_earning_stability": "50",
                "role_security": "50",
                "workload_earning": "50",
                "confidence": "52",
                "warnings": "missing_role_usage_features",
            },
            {
                "player_id": "rb_proxy",
                "player_name": "Receiving RB",
                "position": "RB",
                "team": "MIA",
                "route_role": "50",
                "target_earning_stability": "47",
                "role_security": "75",
                "workload_earning": "74",
                "confidence": "70",
                "warnings": "missing_participation_proxy",
            },
        ],
    )
    _write_csv(
        root / "stats_first_veteran_model_preview_outputs.csv",
        (
            "player_id",
            "player_name",
            "position",
            "team",
            "overall_rank",
            "position_rank_label",
            "confidence_score",
            "warning_reasons",
        ),
        [
            {
                "player_id": "wr_gap",
                "player_name": "Route Gap WR",
                "position": "WR",
                "team": "SF",
                "overall_rank": "7",
                "position_rank_label": "WR5",
                "confidence_score": "66",
                "warning_reasons": "missing_participation_proxy",
            },
            {
                "player_id": "wr_known",
                "player_name": "Route Known WR",
                "position": "WR",
                "team": "DET",
                "overall_rank": "8",
                "position_rank_label": "WR6",
                "confidence_score": "86",
                "warning_reasons": "",
            },
            {
                "player_id": "te_neutral",
                "player_name": "Neutral TE",
                "position": "TE",
                "team": "JAX",
                "overall_rank": "22",
                "position_rank_label": "TE2",
                "confidence_score": "52",
                "warning_reasons": "missing_role_usage_features",
            },
            {
                "player_id": "rb_proxy",
                "player_name": "Receiving RB",
                "position": "RB",
                "team": "MIA",
                "overall_rank": "41",
                "position_rank_label": "RB12",
                "confidence_score": "70",
                "warning_reasons": "missing_participation_proxy",
            },
        ],
    )
    _write_csv(
        root / "veteran_player_inputs.csv",
        ("player_id", "team_name"),
        [{"player_id": "sleeper_wr_gap", "team_name": "Niners"}],
    )
    _write_csv(
        root / "sleeper_nflverse_identity_bridge.csv",
        ("sleeper_id", "matched_gsis_id", "bridge_gsis_id"),
        [
            {
                "sleeper_id": "sleeper_wr_gap",
                "matched_gsis_id": "wr_gap",
                "bridge_gsis_id": "wr_gap",
            }
        ],
    )
    return root


def _player_row(rows: tuple[dict[str, object], ...], player: str) -> dict[str, object]:
    return next(row for row in rows if row["player_name"] == player)


def _area_row(rows: tuple[dict[str, object], ...], area: str) -> dict[str, object]:
    return next(row for row in rows if row["area"] == area)


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
