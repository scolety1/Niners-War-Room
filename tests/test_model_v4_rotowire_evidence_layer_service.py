import json
from pathlib import Path

from src.services.model_v4_rotowire_evidence_layer_service import (
    build_rotowire_evidence_layer,
    write_rotowire_evidence_layer_outputs,
)


def test_rotowire_evidence_layer_covers_truth_set() -> None:
    result = build_rotowire_evidence_layer()

    assert len(result.coverage_rows) == 80
    assert len(result.evidence_rows) == 640
    assert result.summary["model_scores_changed"] is False


def test_rotowire_evidence_layer_keeps_context_lanes_separate() -> None:
    result = build_rotowire_evidence_layer()
    rows = {
        (row["player_name"], row["component"]): row
        for row in result.evidence_rows
    }

    achane_market = rows[("De'Von Achane", "market_context")]
    assert achane_market["allowed_use"] == "context_only"
    assert achane_market["confidence_impact"] == "no_private_value_impact"

    aiyuk_injury = rows[("Brandon Aiyuk", "injury_context")]
    metrics = json.loads(str(aiyuk_injury["key_metrics_json"]))
    assert aiyuk_injury["source_status"] == "sourced_injury_context"
    assert metrics["status"] == "Reserve-DNR"

    jsn_route = rows[("Jaxon Smith-Njigba", "licensed_route_evidence")]
    route_metrics = json.loads(str(jsn_route["key_metrics_json"]))
    assert jsn_route["source_status"] == "imported_route_data"
    assert "routes_run_tprr" in route_metrics


def test_rotowire_evidence_layer_marks_qb_role_usage_not_applicable() -> None:
    result = build_rotowire_evidence_layer()
    rows = {
        (row["player_name"], row["component"]): row
        for row in result.evidence_rows
    }
    coverage = {row["player_name"]: row for row in result.coverage_rows}

    allen_role = rows[("Josh Allen", "role_usage")]
    assert allen_role["source_status"] == "not_applicable"
    assert allen_role["confidence_impact"] == "not_required_for_qb"
    assert allen_role["warning"] == "not_applicable_for_qb"
    assert coverage["Josh Allen"]["overall_coverage_status"] == "covered"


def test_rotowire_evidence_layer_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_evidence_layer()
    paths = write_rotowire_evidence_layer_outputs(tmp_path, result)

    assert paths["evidence"].exists()
    assert paths["coverage"].exists()
    assert paths["summary"].exists()
    assert "De'Von Achane" in paths["evidence"].read_text(encoding="utf-8")
