from __future__ import annotations

import csv
import hashlib
import shutil
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SOURCE_PROJECT_ROOT = Path("C:/Users/codex-agent/Documents/New project")
KAGGLE_ZIP_PATH = Path("C:/Users/codex-agent/Downloads/nfl-draft-2026.zip")
DEFAULT_SNAPSHOT_ROOT = (
    PROJECT_ROOT / "local_exports" / "model_v4" / "prospect_sources" / "latest"
)
DEFAULT_DOC_PATH = PROJECT_ROOT / "docs" / "model_v4" / "PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.md"
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "docs" / "model_v4" / "PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv"
)

SNAPSHOT_VERSION = "model_v4_phase_10d_prospect_source_snapshot_0.1.0"

MANIFEST_HEADER = (
    "snapshot_version",
    "snapshot_generated_at_utc",
    "source_group",
    "source_name",
    "source_type",
    "source_path",
    "source_relative_path",
    "snapshot_path",
    "snapshot_relative_path",
    "file_name",
    "extension",
    "bytes",
    "sha256",
    "csv_rows",
    "csv_columns",
    "license_note",
    "source_status",
    "model_lane_allowed",
    "allowed_use",
    "notes",
)


@dataclass(frozen=True)
class SourceSpec:
    source_group: str
    source_name: str
    source_type: str
    pattern: str
    license_note: str
    source_status: str
    model_lane_allowed: str
    allowed_use: str
    notes: str


SOURCE_SPECS = (
    SourceSpec(
        "cfbd",
        "CollegeFootballData processed tables",
        "processed_csv",
        "data/college_football_data/processed/*.csv",
        "CFBD API export; verify source terms before redistribution.",
        "source_limited_local_snapshot",
        "prospect_historical_evidence_staged",
        "review_only",
        "Processed prospect/team/market-share evidence from separate rookie package.",
    ),
    SourceSpec(
        "cfbd",
        "CollegeFootballData raw manifests",
        "source_manifest",
        "data/college_football_data/raw/cfbd_manifest_*.csv",
        "CFBD API export manifest; verify source terms before redistribution.",
        "source_limited_local_snapshot",
        "source_manifest_only",
        "audit_only",
        "Preserves original CFBD extraction manifest metadata.",
    ),
    SourceSpec(
        "rotowire_cfb",
        "RotoWire CFB processed tables",
        "processed_csv",
        "data/rotowire/processed/rotowire_cfb*.csv",
        "User-provided RotoWire subscription export; do not redistribute.",
        "licensed_user_export_local_only",
        "prospect_college_evidence_staged",
        "review_only",
        "CFB production, targets, team context, and injury evidence.",
    ),
    SourceSpec(
        "rotowire_context",
        "RotoWire workouts/depth/rookie/NFL injury processed tables",
        "processed_csv",
        "data/rotowire/processed/rotowire_*.csv",
        "User-provided RotoWire subscription export; do not redistribute.",
        "licensed_user_export_local_only",
        "prospect_context_staged",
        "review_only",
        "Landing spot, workout, rookie ranking, and injury context only.",
    ),
    SourceSpec(
        "fantasypros",
        "FantasyPros processed ADP",
        "processed_csv",
        "data/fantasypros/processed/*.csv",
        "User-provided FantasyPros export; market/sanity context only.",
        "user_export_local_snapshot",
        "market_context_only",
        "context_only",
        "Do not blend into private football value.",
    ),
    SourceSpec(
        "market",
        "Rookie ADP and watchlist processed tables",
        "processed_csv",
        "data/market/processed/*.csv",
        "User-provided market/context data; market/sanity context only.",
        "user_export_local_snapshot",
        "market_context_only",
        "context_only",
        "Do not blend into private football value.",
    ),
    SourceSpec(
        "third_party_combine",
        "Third-party combine/pro-day processed/raw files",
        "third_party_file",
        "data/third_party/nfl_draft_data/**/*",
        "License not found in downloaded repository files; do not redistribute.",
        "source_limited_license_unresolved",
        "prospect_athletic_context_staged",
        "review_only",
        "Source-limited combine/pro-day context requiring license review.",
    ),
)


def main() -> None:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    snapshot_root = DEFAULT_SNAPSHOT_ROOT
    snapshot_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    seen_sources: set[Path] = set()
    for spec in SOURCE_SPECS:
        for source_path in sorted(SOURCE_PROJECT_ROOT.glob(spec.pattern)):
            if not source_path.is_file() or source_path in seen_sources:
                continue
            seen_sources.add(source_path)
            rows.append(_copy_source_file(source_path, spec, snapshot_root, generated_at))

    if KAGGLE_ZIP_PATH.exists():
        rows.extend(_snapshot_kaggle_zip(KAGGLE_ZIP_PATH, snapshot_root, generated_at))

    rows = sorted(
        rows,
        key=lambda row: (
            str(row["source_group"]),
            str(row["source_relative_path"]),
            str(row["snapshot_relative_path"]),
        ),
    )
    _write_csv(DEFAULT_MANIFEST_PATH, rows)
    _write_markdown(DEFAULT_DOC_PATH, rows, snapshot_root, generated_at)
    print(f"snapshot_root={snapshot_root}")
    print(f"manifest={DEFAULT_MANIFEST_PATH}")
    print(f"doc={DEFAULT_DOC_PATH}")
    print(f"files={len(rows)}")
    print(f"bytes={sum(int(row['bytes']) for row in rows)}")


def _copy_source_file(
    source_path: Path,
    spec: SourceSpec,
    snapshot_root: Path,
    generated_at: str,
) -> dict[str, object]:
    relative = source_path.relative_to(SOURCE_PROJECT_ROOT).as_posix()
    snapshot_path = snapshot_root / "files" / "source_project" / relative
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, snapshot_path)
    return _manifest_row(
        generated_at=generated_at,
        source_group=spec.source_group,
        source_name=spec.source_name,
        source_type=spec.source_type,
        source_path=source_path,
        source_relative_path=relative,
        snapshot_path=snapshot_path,
        snapshot_root=snapshot_root,
        license_note=spec.license_note,
        source_status=spec.source_status,
        model_lane_allowed=spec.model_lane_allowed,
        allowed_use=spec.allowed_use,
        notes=spec.notes,
    )


def _snapshot_kaggle_zip(
    zip_path: Path,
    snapshot_root: Path,
    generated_at: str,
) -> list[dict[str, object]]:
    rows = []
    zip_snapshot = snapshot_root / "files" / "kaggle_nfl_draft" / zip_path.name
    zip_snapshot.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(zip_path, zip_snapshot)
    license_note = (
        "Kaggle page was user-reported as CC0 Public Domain; "
        "verify before redistribution."
    )
    rows.append(
        _manifest_row(
            generated_at=generated_at,
            source_group="kaggle_nfl_draft",
            source_name="Kaggle NFL Draft 2026 archive",
            source_type="raw_zip",
            source_path=zip_path,
            source_relative_path=zip_path.name,
            snapshot_path=zip_snapshot,
            snapshot_root=snapshot_root,
            license_note=license_note,
            source_status="source_limited_user_download",
            model_lane_allowed="draft_context_staged",
            allowed_use="review_only",
            notes="Original downloaded archive copied unchanged.",
        )
    )

    extract_root = snapshot_root / "files" / "kaggle_nfl_draft" / "extracted"
    with zipfile.ZipFile(zip_path) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            if info.is_dir():
                continue
            target = extract_root / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            rows.append(
                _manifest_row(
                    generated_at=generated_at,
                    source_group="kaggle_nfl_draft",
                    source_name="Kaggle NFL Draft 2026 extracted file",
                    source_type="raw_archive_member",
                    source_path=zip_path,
                    source_relative_path=f"{zip_path.name}!{info.filename}",
                    snapshot_path=target,
                    snapshot_root=snapshot_root,
                    license_note=license_note,
                    source_status="source_limited_user_download",
                    model_lane_allowed="draft_context_staged",
                    allowed_use="review_only",
                    notes="Extracted for future inspection; not blended into formulas.",
                )
            )
    return rows


def _manifest_row(
    *,
    generated_at: str,
    source_group: str,
    source_name: str,
    source_type: str,
    source_path: Path,
    source_relative_path: str,
    snapshot_path: Path,
    snapshot_root: Path,
    license_note: str,
    source_status: str,
    model_lane_allowed: str,
    allowed_use: str,
    notes: str,
) -> dict[str, object]:
    csv_rows, csv_columns = _csv_profile(snapshot_path)
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "snapshot_generated_at_utc": generated_at,
        "source_group": source_group,
        "source_name": source_name,
        "source_type": source_type,
        "source_path": str(source_path),
        "source_relative_path": source_relative_path,
        "snapshot_path": str(snapshot_path),
        "snapshot_relative_path": snapshot_path.relative_to(snapshot_root).as_posix(),
        "file_name": snapshot_path.name,
        "extension": snapshot_path.suffix.lower(),
        "bytes": snapshot_path.stat().st_size,
        "sha256": _sha256(snapshot_path),
        "csv_rows": csv_rows,
        "csv_columns": csv_columns,
        "license_note": license_note,
        "source_status": source_status,
        "model_lane_allowed": model_lane_allowed,
        "allowed_use": allowed_use,
        "notes": notes,
    }


def _csv_profile(path: Path) -> tuple[int | str, int | str]:
    if path.suffix.lower() != ".csv":
        return "", ""
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
            rows = sum(1 for _ in reader)
    except UnicodeDecodeError:
        return "", ""
    return rows, len(header)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(
    path: Path,
    rows: list[dict[str, object]],
    snapshot_root: Path,
    generated_at: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    by_group: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_group.setdefault(str(row["source_group"]), []).append(row)

    group_lines = []
    for group, group_rows in sorted(by_group.items()):
        total_bytes = sum(int(row["bytes"]) for row in group_rows)
        source_limited = sum(
            1
            for row in group_rows
            if "limited" in str(row["source_status"])
            or "unresolved" in str(row["source_status"])
        )
        group_lines.append(
            f"| {group} | {len(group_rows)} | {total_bytes:,} | {source_limited} |"
        )

    source_limited_rows = [
        row
        for row in rows
        if "limited" in str(row["source_status"])
        or "unresolved" in str(row["source_status"])
    ]
    limited_lines = [
        (
            f"- `{row['source_group']}` / `{row['file_name']}`: "
            f"{row['source_status']} - {row['license_note']}"
        )
        for row in source_limited_rows[:25]
    ]
    if len(source_limited_rows) > 25:
        limited_lines.append(f"- ...and {len(source_limited_rows) - 25} more in the CSV.")

    markdown = f"""# Phase 10D Prospect Source Snapshot

Generated: {generated_at}

## Scope

Phase 10D snapshots the separate rookie/prospect package into the main Model v4
source system. This is a source-governance phase only.

No formula weights, rankings, My Team, War Board, app promotion state, or
readiness gates were changed.

## Snapshot Location

- Snapshot root: `{snapshot_root}`
- Manifest CSV: `docs/model_v4/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv`

## Source Groups

| Source group | Files | Bytes | Source-limited files |
| --- | ---: | ---: | ---: |
{chr(10).join(group_lines)}

## Included Source Lanes

- CFBD processed player/team/market-share/recruiting/draft tables.
- CFBD raw extraction manifests.
- RotoWire CFB stats, targets, advanced team stats, and CFB injury tables.
- RotoWire workouts, NFL depth chart, rookie ranking, and NFL injury context tables.
- FantasyPros ADP and rookie/market ADP context.
- Kaggle NFL Draft 2026 archive and extracted files.
- Third-party combine/pro-day raw and processed files.

## Guardrails

- These files are staged as source evidence/context only.
- Market, ADP, ranking, and watchlist files remain context-only.
- RotoWire exports are local subscription exports and must not be redistributed.
- Third-party combine/pro-day files are source-limited because no license was
  found in the downloaded repository files.
- Kaggle license was user-reported as CC0 Public Domain; verify before
  redistribution.
- No prospect data is blended into Model v4 formulas in this phase.

## Source-Limited Notes

{chr(10).join(limited_lines) if limited_lines else "- None."}

## Next Step

Use this snapshot for an identity/data-health audit before any prospect feature
table or formula integration. The safe next phase is to reconcile player names
and IDs across CFBD, RotoWire, FantasyPros/ADP, Kaggle draft data, and combine
sources without scoring them.
"""
    path.write_text(markdown, encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    main()
