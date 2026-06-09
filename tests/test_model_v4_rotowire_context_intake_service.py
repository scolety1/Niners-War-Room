import json
from pathlib import Path

from src.services.model_v4_rotowire_context_intake_service import (
    build_rotowire_context_intake,
    write_rotowire_context_intake_outputs,
)


def test_rotowire_context_intake_covers_context_sources() -> None:
    result = build_rotowire_context_intake()

    assert len(result.validation_rows) == 23
    assert result.summary["model_scores_changed"] is False
    assert "projections" in str(result.summary["source_families"])
    assert "market_context" in str(result.summary["source_families"])


def test_rotowire_context_intake_labels_lanes_and_statuses() -> None:
    result = build_rotowire_context_intake()

    achane_projection = next(
        row
        for row in result.clean_rows
        if row["source_family"] == "projections"
        and row["entity_name"] == "De'Von Achane"
    )
    projection_metrics = json.loads(str(achane_projection["metrics_json"]))
    assert achane_projection["model_lane"] == "projection_context"
    assert achane_projection["allowed_use"] == "review_only"
    assert projection_metrics["rushing_yds"] == 1070
    assert projection_metrics["receiving_rec"] == 56

    aiyuk_depth = next(
        row
        for row in result.clean_rows
        if row["source_family"] == "depth_charts"
        and row["entity_name"] == "Brandon Aiyuk"
    )
    depth_metrics = json.loads(str(aiyuk_depth["metrics_json"]))
    assert aiyuk_depth["allowed_use"] == "context_only"
    assert depth_metrics["listed_status"] == "Reserve-DNR"
    assert depth_metrics["depth_rank"] == 8

    adp = next(
        row
        for row in result.clean_rows
        if row["source_family"] == "market_context"
        and row["entity_name"] == "De'Von Achane"
    )
    assert adp["model_lane"] == "market_context"
    assert adp["allowed_use"] == "context_only"


def test_rotowire_context_intake_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_context_intake()
    paths = write_rotowire_context_intake_outputs(tmp_path, result)

    assert paths["clean"].exists()
    assert paths["validation"].exists()
    assert paths["summary"].exists()
    assert "raw_projection_stats_context" in paths["clean"].read_text(encoding="utf-8")
