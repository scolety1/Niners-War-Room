from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sleeper_adp_display_context_v0.py"
SPEC = importlib.util.spec_from_file_location("sleeper_adp_display_context_v0", MODULE_PATH)
assert SPEC is not None
ADP = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["sleeper_adp_display_context_v0"] = ADP
SPEC.loader.exec_module(ADP)


def test_normalize_extracts_adp_fields_and_preferred_rule() -> None:
    rows = ADP.normalize_payload(
        payload=_payload(),
        season=2026,
        collected_at="2026-06-21T00:00:00+00:00",
    )

    assert len(rows) == 4
    by_name = {row["player_name"]: row for row in rows}
    assert by_name["Drake Maye"]["adp_dynasty_std"] == "48.5"
    assert by_name["Drake Maye"]["preferred_adp_for_nwr"] == "48.5"
    assert (
        by_name["Drake Maye"]["preferred_adp_reason"]
        == "adp_dynasty_std_primary_dynasty_non_ppr"
    )
    assert by_name["Jaylen Warren"]["preferred_adp_for_nwr"] == "71"
    assert by_name["Jaylen Warren"]["preferred_adp_reason"] == "adp_dynasty_fallback"
    assert by_name["Alec Pierce"]["preferred_adp_for_nwr"] == "143"
    assert by_name["Alec Pierce"]["preferred_adp_reason"] == "adp_std_fallback_non_ppr"
    assert by_name["Last Resort"]["preferred_adp_for_nwr"] == "199"
    assert (
        by_name["Last Resort"]["preferred_adp_reason"]
        == "adp_ppr_last_resort_display_only"
    )
    assert by_name["Alec Pierce"]["normalized_player_name"] == "alec pierce"


def test_candidate_write_creates_latest_candidate_only(tmp_path: Path) -> None:
    result = ADP.run_sleeper_adp_display_context(
        season=2026,
        positions=["QB", "RB", "WR"],
        output_root=tmp_path / "lane_exchange",
        report_root=tmp_path / "reports",
        write_candidate=True,
        snapshot_label="candidate",
        input_json=_write_payload(tmp_path / "payload.json"),
    )

    assert result.candidate_path is not None
    assert result.latest_candidate_path is not None
    assert result.sha256 is not None
    assert result.candidate_path.exists()
    assert result.latest_candidate_path.exists()
    assert not (result.latest_candidate_path.parent / "latest_approved.json").exists()

    manifest_path = result.candidate_path / "manifest.json"
    data_path = result.candidate_path / ADP.DATA_FILE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pointer = json.loads(result.latest_candidate_path.read_text(encoding="utf-8"))

    assert manifest["approval_status"] == "candidate"
    assert pointer["approval_status"] == "candidate"
    assert manifest["source_risk"] == "YELLOW_UNDOCUMENTED_ENDPOINT"
    assert pointer["source_risk"] == "YELLOW_UNDOCUMENTED_ENDPOINT"
    assert "private_value" in manifest["blocked_use"]
    assert "hidden_sort" in manifest["blocked_use"]
    assert "recommendations" in manifest["blocked_use"]
    assert "decision_driving_simulations" in manifest["blocked_use"]
    assert manifest["contains_private_value"] is False
    assert manifest["contains_market_data"] is True
    assert manifest["contains_adp"] is True
    assert manifest["not_latest_approved"] is True
    assert manifest["row_count"] == len(result.rows)
    assert manifest["sha256"] == hashlib.sha256(data_path.read_bytes()).hexdigest()
    assert pointer["sha256"] == manifest["sha256"]


def test_candidate_schema_has_no_private_value_or_hidden_sort_fields() -> None:
    fields = set(ADP.CANDIDATE_FIELDS)

    assert "nwr_private_value" not in fields
    assert "private_value" not in fields
    assert "hidden_sort" not in fields
    assert "rank" not in fields
    assert "ranking" not in fields
    assert "recommendation" not in fields
    assert "pts_ppr" not in fields
    assert "pts_std" not in fields
    assert "fantasy_points" not in fields
    ADP._validate_candidate_fields()


def test_report_only_writes_no_candidate(tmp_path: Path) -> None:
    result = ADP.run_sleeper_adp_display_context(
        season=2026,
        positions=["QB"],
        output_root=tmp_path / "lane_exchange",
        report_root=tmp_path / "reports",
        write_candidate=False,
        snapshot_label="report_only",
        input_json=_write_payload(tmp_path / "payload.json"),
    )

    assert result.report_path.exists()
    assert result.candidate_path is None
    assert result.latest_candidate_path is None
    assert not (tmp_path / "lane_exchange").exists()


def _write_payload(path: Path) -> Path:
    path.write_text(json.dumps(_payload()), encoding="utf-8")
    return path


def _payload() -> list[dict[str, Any]]:
    return [
        {
            "player_id": "11111",
            "season": "2026",
            "updated_at": 1780000000,
            "last_modified": 1780000001,
            "team": "NE",
            "player": {
                "first_name": "Drake",
                "last_name": "Maye",
                "position": "QB",
                "team": "NE",
            },
            "stats": {
                "adp_dynasty_std": 48.5,
                "adp_dynasty": 50.2,
                "adp_std": 62.8,
                "adp_ppr": 65.0,
                "pts_ppr": 200.0,
            },
        },
        {
            "player_id": "22222",
            "season": "2026",
            "team": "PIT",
            "player": {
                "first_name": "Jaylen",
                "last_name": "Warren",
                "fantasy_positions": ["RB"],
            },
            "stats": {
                "adp_dynasty": "71.0",
                "adp_std": "80",
            },
        },
        {
            "player_id": "33333",
            "season": "2026",
            "team": "IND",
            "player": {
                "full_name": "Alec Pierce",
                "position": "WR",
            },
            "stats": {
                "adp_std": 143,
                "adp_2qb": 160,
                "adp_rookie": 31,
            },
        },
        {
            "player_id": "44444",
            "season": "2026",
            "team": "FA",
            "player": {
                "full_name": "Last Resort",
                "position": "WR",
            },
            "stats": {
                "adp_ppr": 199,
            },
        },
    ]
