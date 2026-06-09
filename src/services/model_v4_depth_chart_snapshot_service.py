from __future__ import annotations

import csv
from pathlib import Path

SOURCE_DEPTH_CHARTS = Path(
    "local_exports/model_v4/prospect_sources/latest/files/source_project/data/"
    "rotowire/processed/rotowire_upcoming_depth_charts.csv"
)
DEFAULT_DEPTH_CHART_OUTPUT = Path(
    "local_exports/model_v4/depth_charts/latest/rotowire_upcoming_depth_charts_may22.csv"
)
DEFAULT_DEPTH_CHART_DOC = Path("docs/model_v4/ROTOWIRE_DEPTH_CHART_MAY22_SNAPSHOT.md")

MAY22_COLLECTED_AT_UTC = "2026-05-22T06:00:00+00:00"
MAY22_SOURCE_FILE = "user_paste_rotowire_depth_charts_may22_20260522"


def build_may22_depth_chart_rows(
    *,
    source_path: str | Path = SOURCE_DEPTH_CHARTS,
) -> tuple[dict[str, str], ...]:
    source = Path(source_path)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        rows = tuple(csv.DictReader(handle))
    output: list[dict[str, str]] = []
    for row in rows:
        updated = dict(row)
        updated["collected_at_utc"] = MAY22_COLLECTED_AT_UTC
        updated["source_file"] = MAY22_SOURCE_FILE
        output.append(updated)
    return tuple(output)


def write_may22_depth_chart_snapshot(
    *,
    output_path: str | Path = DEFAULT_DEPTH_CHART_OUTPUT,
    doc_path: str | Path = DEFAULT_DEPTH_CHART_DOC,
    rows: tuple[dict[str, str], ...] | None = None,
) -> tuple[Path, Path]:
    rows = rows or build_may22_depth_chart_rows()
    output = Path(output_path)
    doc = Path(doc_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = tuple(rows[0].keys()) if rows else ()
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    doc.write_text(_doc(rows, output), encoding="utf-8")
    return output, doc


def _doc(rows: tuple[dict[str, str], ...], output: Path) -> str:
    teams = {row.get("team", "") for row in rows if row.get("team")}
    return (
        "# RotoWire Depth Chart May 22 Snapshot\n\n"
        "This snapshot records the user-provided May 22, 2026 RotoWire all-team "
        "depth-chart paste as a current role/context source. The existing parsed "
        "RotoWire depth-chart rows matched the pasted structure, so this snapshot "
        "preserves row structure while updating the source timestamp and source-file "
        "label.\n\n"
        f"- Rows: {len(rows)}\n"
        f"- Teams: {len(teams)}\n"
        f"- Output: `{output}`\n"
        f"- Collected at UTC: `{MAY22_COLLECTED_AT_UTC}`\n\n"
        "Allowed use: current depth-rank, room-crowding, injury/status, and roster-fit "
        "context. Blocked use: depth chart as standalone talent evaluation or final "
        "draft/trade recommendation.\n"
    )
