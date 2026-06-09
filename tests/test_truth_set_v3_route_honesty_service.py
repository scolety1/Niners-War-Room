from __future__ import annotations

import csv
from pathlib import Path

from src.services.truth_set_v3_route_honesty_service import (
    ROUTE_HONESTY_HEADER,
    route_honesty_rows,
    write_route_honesty_outputs,
)


def test_true_route_fields_are_unavailable_or_missing_not_real_evidence() -> None:
    rows = {str(row["field_name"]): row for row in route_honesty_rows()}

    assert rows["routes_run"]["source_status"] == "unavailable_free_public"
    assert rows["route_participation"]["source_status"] == "unavailable_free_public"
    assert rows["targets_per_route_run"]["source_status"] == "missing_paid_or_charted_data"
    assert rows["yards_per_route_run"]["source_status"] == "missing_paid_or_charted_data"
    assert all(
        row["can_score_as_real_evidence"] is False
        for field, row in rows.items()
        if field != "snap_target_route_proxy"
    )


def test_snap_target_proxy_is_labeled_proxy_only() -> None:
    row = next(
        row
        for row in route_honesty_rows()
        if row["field_name"] == "snap_target_route_proxy"
    )

    assert row["source_status"] == "proxy_only_snap_target"
    assert row["can_score_as_real_evidence"] is False
    assert "snap_share" in str(row["allowed_proxy_fields"])


def test_route_honesty_output_uses_stable_header(tmp_path: Path) -> None:
    paths = write_route_honesty_outputs(tmp_path)

    with paths["rows"].open(newline="", encoding="utf-8") as handle:
        assert tuple(next(csv.reader(handle))) == ROUTE_HONESTY_HEADER
