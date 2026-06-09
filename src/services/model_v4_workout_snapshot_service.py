from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Any

INPUT_WORKOUT_FILES = {
    "QB": Path(r"C:\Users\codex-agent\Downloads\workout-stats-QB.csv"),
    "RB": Path(r"C:\Users\codex-agent\Downloads\workout-stats-RB.csv"),
    "WR": Path(r"C:\Users\codex-agent\Downloads\workout-stats-WR.csv"),
    "TE": Path(r"C:\Users\codex-agent\Downloads\workout-stats-TE.csv"),
}

DEFAULT_WORKOUT_OUTPUT = Path(
    "local_exports/model_v4/workouts/latest/rotowire_workout_stats_may25.csv"
)
DEFAULT_WORKOUT_MANIFEST = Path(
    "local_exports/model_v4/workouts/latest/rotowire_workout_stats_may25_manifest.csv"
)
DEFAULT_WORKOUT_RAW_DIR = Path("local_exports/model_v4/workouts/latest/raw")
DEFAULT_WORKOUT_DOC = Path("docs/model_v4/ROTOWIRE_WORKOUT_MAY25_SNAPSHOT.md")

MAY25_COLLECTED_AT_UTC = "2026-05-25T23:12:00+00:00"

NORMALIZED_COLUMNS = (
    "player",
    "team",
    "draft_year",
    "event",
    "height",
    "height_inches",
    "weight",
    "arm",
    "hand",
    "forty",
    "forty_pct",
    "shuttle",
    "shuttle_pct",
    "cone",
    "cone_pct",
    "vertical",
    "vertical_pct",
    "broad",
    "broad_pct",
    "bench",
    "bench_pct",
)

WORKOUT_FIELDS = (
    "source",
    "source_file",
    "collected_at_utc",
    "position",
    *NORMALIZED_COLUMNS,
)

MANIFEST_FIELDS = (
    "collected_at_utc",
    "source",
    "position",
    "source_path",
    "raw_copy_path",
    "processed_path",
    "rows",
    "source_status",
    "allowed_use",
)


def build_may25_workout_snapshot(
    *,
    input_files: dict[str, Path] | None = None,
    raw_dir: str | Path = DEFAULT_WORKOUT_RAW_DIR,
    processed_path: str | Path = DEFAULT_WORKOUT_OUTPUT,
) -> tuple[dict[str, str], ...]:
    input_files = input_files or INPUT_WORKOUT_FILES
    raw_root = Path(raw_dir)
    processed = Path(processed_path)
    raw_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for position, source_path in input_files.items():
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(source)
        raw_copy = raw_root / f"rotowire_workout_stats_{position}_may25.csv"
        shutil.copy2(source, raw_copy)
        rows.extend(_read_workout_csv(raw_copy, position, processed))
    return tuple(rows)


def write_may25_workout_snapshot(
    *,
    output_path: str | Path = DEFAULT_WORKOUT_OUTPUT,
    manifest_path: str | Path = DEFAULT_WORKOUT_MANIFEST,
    doc_path: str | Path = DEFAULT_WORKOUT_DOC,
    raw_dir: str | Path = DEFAULT_WORKOUT_RAW_DIR,
    input_files: dict[str, Path] | None = None,
    rows: tuple[dict[str, str], ...] | None = None,
) -> tuple[Path, Path, Path]:
    output = Path(output_path)
    manifest = Path(manifest_path)
    doc = Path(doc_path)
    rows = rows or build_may25_workout_snapshot(
        input_files=input_files,
        raw_dir=raw_dir,
        processed_path=output,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    doc.parent.mkdir(parents=True, exist_ok=True)

    _write_csv(output, WORKOUT_FIELDS, rows)
    _write_csv(manifest, MANIFEST_FIELDS, _manifest_rows(rows, output))
    doc.write_text(_doc(rows, output, manifest), encoding="utf-8")
    return output, manifest, doc


def _read_workout_csv(path: Path, position: str, processed_path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        header = next(reader, None)
        if not header:
            return []
        output: list[dict[str, str]] = []
        for raw in reader:
            if not raw or not clean(raw[0]):
                continue
            padded = raw + [""] * (len(header) - len(raw))
            row = dict(zip(header, padded, strict=False))
            output.append(
                {
                    "source": "RotoWire",
                    "source_file": str(path),
                    "collected_at_utc": MAY25_COLLECTED_AT_UTC,
                    "position": position,
                    "player": clean(row.get("Name")),
                    "team": clean(row.get("Team")),
                    "draft_year": clean(row.get("Date")),
                    "event": clean(row.get("Title")),
                    "height": clean(row.get("Height")),
                    "height_inches": height_to_inches(row.get("Height", "")),
                    "weight": clean(row.get("Weight")),
                    "arm": clean(row.get("Arm")),
                    "hand": clean(row.get("Hand")),
                    "forty": clean(row.get("40 Yard")),
                    "forty_pct": clean(padded[9] if len(padded) > 9 else ""),
                    "shuttle": clean(row.get("Shuttle")),
                    "shuttle_pct": clean(padded[11] if len(padded) > 11 else ""),
                    "cone": clean(row.get("Cone")),
                    "cone_pct": clean(padded[13] if len(padded) > 13 else ""),
                    "vertical": clean(row.get("Vertical")),
                    "vertical_pct": clean(padded[15] if len(padded) > 15 else ""),
                    "broad": clean(row.get("Broad")),
                    "broad_pct": clean(padded[17] if len(padded) > 17 else ""),
                    "bench": clean(row.get("Bench")),
                    "bench_pct": clean(padded[19] if len(padded) > 19 else ""),
                }
            )
    _ = processed_path
    return output


def clean(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip()
    if value in {"-", "--"}:
        return ""
    return value


def height_to_inches(value: str | None) -> str:
    value = clean(value)
    if not value or "-" not in value:
        return ""
    feet, inches = value.split("-", 1)
    try:
        return str(int(feet) * 12 + int(inches))
    except ValueError:
        return ""


def _manifest_rows(
    rows: tuple[dict[str, str], ...],
    processed_path: Path,
) -> tuple[dict[str, Any], ...]:
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["position"], row["source_file"])
        counts[key] = counts.get(key, 0) + 1
    return tuple(
        {
            "collected_at_utc": MAY25_COLLECTED_AT_UTC,
            "source": "RotoWire",
            "position": position,
            "source_path": source_file,
            "raw_copy_path": source_file,
            "processed_path": str(processed_path),
            "rows": row_count,
            "source_status": "licensed_user_export_local_only",
            "allowed_use": "prospect_prior_athletic_context_after_identity_validation",
        }
        for (position, source_file), row_count in sorted(counts.items())
    )


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: tuple[dict[str, Any], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _doc(rows: tuple[dict[str, str], ...], output: Path, manifest: Path) -> str:
    positions = sorted({row["position"] for row in rows})
    first_round_2026 = [
        row["player"]
        for row in rows
        if row.get("draft_year") == "2026" and row.get("event") in {"Combine", "Pro Day"}
    ][:12]
    return (
        "# RotoWire Workout May 25 Snapshot\n\n"
        "This snapshot records the user-provided May 25, 2026 RotoWire workout, "
        "combine, and pro-day exports for QB/RB/WR/TE. Raw user exports are copied "
        "under `local_exports/model_v4/workouts/latest/raw` so rebuilds do not rely "
        "on the Downloads folder.\n\n"
        f"- Rows: {len(rows)}\n"
        f"- Positions: {', '.join(positions)}\n"
        f"- Output: `{output}`\n"
        f"- Manifest: `{manifest}`\n"
        f"- Collected at UTC: `{MAY25_COLLECTED_AT_UTC}`\n"
        f"- Sample 2026 rows: {', '.join(first_round_2026)}\n\n"
        "Allowed use: prospect-prior athletic context after identity validation. "
        "Blocked use: market value, final draft recommendation, or standalone talent "
        "evaluation. Impossible zero placeholders are still repaired by the evidence "
        "matrix layer before formula-facing outputs are written.\n"
    )
