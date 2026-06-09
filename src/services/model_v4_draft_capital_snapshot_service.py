from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Any

from src.services.model_v4_player_identity_crosswalk_service import normalize_identity_name

SOURCE_DRAFT_RESULTS = Path(
    "local_exports/model_v4/prospect_sources/latest/files/kaggle_nfl_draft/extracted/solution.csv"
)
DEFAULT_DRAFT_CAPITAL_OUTPUT = Path(
    "local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026.csv"
)
DEFAULT_DRAFT_CAPITAL_MANIFEST = Path(
    "local_exports/model_v4/draft_capital/latest/rookie_draft_capital_2026_manifest.csv"
)
DEFAULT_DRAFT_CAPITAL_RAW_COPY = Path(
    "local_exports/model_v4/draft_capital/latest/raw/solution_2026_draft_results.csv"
)
DEFAULT_DRAFT_CAPITAL_DOC = Path("docs/model_v4/ROOKIE_DRAFT_CAPITAL_2026_SNAPSHOT.md")

COLLECTED_AT_UTC = "2026-05-25T23:45:00+00:00"

DRAFT_CAPITAL_HEADER = (
    "source",
    "source_file",
    "collected_at_utc",
    "draft_year",
    "round",
    "overall_pick",
    "draft_day",
    "player",
    "normalized_player_name",
    "source_status",
    "allowed_use",
)

MANIFEST_HEADER = (
    "collected_at_utc",
    "source",
    "source_path",
    "raw_copy_path",
    "processed_path",
    "rows",
    "source_status",
    "allowed_use",
)


def build_2026_draft_capital_rows(
    *,
    source_path: str | Path = SOURCE_DRAFT_RESULTS,
    raw_copy_path: str | Path = DEFAULT_DRAFT_CAPITAL_RAW_COPY,
) -> tuple[dict[str, str], ...]:
    source = Path(source_path)
    raw_copy = Path(raw_copy_path)
    if not source.exists():
        raise FileNotFoundError(source)
    raw_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, raw_copy)

    rows: list[dict[str, str]] = []
    with raw_copy.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            pick = _int(row.get("pick"))
            player = _clean(row.get("player_name"))
            if not pick or not player:
                continue
            rows.append(
                {
                    "source": "Kaggle NFL Draft 2026 user download",
                    "source_file": str(raw_copy),
                    "collected_at_utc": COLLECTED_AT_UTC,
                    "draft_year": "2026",
                    "round": str(((pick - 1) // 32) + 1),
                    "overall_pick": str(pick),
                    "draft_day": _clean(row.get("day")),
                    "player": player,
                    "normalized_player_name": normalize_identity_name(player),
                    "source_status": "user_download_factual_draft_result_local_only",
                    "allowed_use": "prospect_prior_draft_capital_after_identity_validation",
                }
            )
    return tuple(rows)


def write_2026_draft_capital_snapshot(
    *,
    output_path: str | Path = DEFAULT_DRAFT_CAPITAL_OUTPUT,
    manifest_path: str | Path = DEFAULT_DRAFT_CAPITAL_MANIFEST,
    doc_path: str | Path = DEFAULT_DRAFT_CAPITAL_DOC,
    rows: tuple[dict[str, str], ...] | None = None,
) -> tuple[Path, Path, Path]:
    output = Path(output_path)
    manifest = Path(manifest_path)
    doc = Path(doc_path)
    rows = rows or build_2026_draft_capital_rows()

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    doc.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(output, DRAFT_CAPITAL_HEADER, rows)
    _write_csv(
        manifest,
        MANIFEST_HEADER,
        (
            {
                "collected_at_utc": COLLECTED_AT_UTC,
                "source": "Kaggle NFL Draft 2026 user download",
                "source_path": str(SOURCE_DRAFT_RESULTS),
                "raw_copy_path": str(DEFAULT_DRAFT_CAPITAL_RAW_COPY),
                "processed_path": str(output),
                "rows": str(len(rows)),
                "source_status": "user_download_factual_draft_result_local_only",
                "allowed_use": "prospect_prior_draft_capital_after_identity_validation",
            },
        ),
    )
    doc.write_text(_doc(rows, output, manifest), encoding="utf-8")
    return output, manifest, doc


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: tuple[dict[str, Any], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _doc(rows: tuple[dict[str, str], ...], output: Path, manifest: Path) -> str:
    offensive_rows = [row for row in rows if _int(row.get("overall_pick"))]
    return (
        "# Rookie Draft Capital 2026 Snapshot\n\n"
        "This snapshot admits the locally frozen 2026 draft result pick order as "
        "factual prospect-prior draft-capital evidence. It is not a mock draft, ADP, "
        "ranking, or market source.\n\n"
        f"- Rows: {len(rows)}\n"
        f"- Output: `{output}`\n"
        f"- Manifest: `{manifest}`\n"
        f"- Collected at UTC: `{COLLECTED_AT_UTC}`\n"
        f"- First pick: `{offensive_rows[0]['player'] if offensive_rows else ''}`\n\n"
        "Allowed use: draft round and overall pick as prospect-prior evidence after "
        "identity validation. Blocked use: market context, final recommendation, or "
        "generic ranking leakage.\n"
    )


def _clean(value: object) -> str:
    return str(value or "").strip()


def _int(value: object) -> int:
    try:
        return int(float(str(value or "").strip()))
    except ValueError:
        return 0
