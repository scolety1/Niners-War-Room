from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack

MODEL_APPLIED_PACK_MANIFEST_FILE = "model_applied_pack_manifest.json"


@dataclass(frozen=True)
class DataPackCatalogEntry:
    name: str
    path: Path
    source_group: str
    snapshot_date: str | None
    error_count: int
    warning_count: int
    roster_count: int
    pick_count: int
    applied_pack_status: str
    applied_pack_reason: str
    applied_row_count: int

    @property
    def status_label(self) -> str:
        if self.applied_pack_status:
            return f"{self.name} | applied {self.applied_pack_status}"
        if self.error_count:
            return f"{self.name} | {self.error_count} errors"
        if self.warning_count:
            return f"{self.name} | {self.warning_count} warnings"
        return f"{self.name} | ready"


def discover_data_packs(
    *,
    project_root: str | Path,
    default_data_pack: str | Path,
    generated_root: str | Path = "local_exports/data_packs",
    include_samples: bool = False,
) -> list[DataPackCatalogEntry]:
    root = Path(project_root)
    candidates = _candidate_dirs(root / generated_root)
    default_path = _resolve_path(root, default_data_pack)
    if default_path.exists() and default_path not in candidates:
        candidates.insert(0, default_path)
    if include_samples or not candidates:
        for candidate in _candidate_dirs(root / "sample_data"):
            if candidate not in candidates:
                candidates.append(candidate)

    entries = [_catalog_entry(path, root, default_path) for path in candidates]
    return sorted(entries, key=_catalog_sort_key)


def catalog_rows(entries: list[DataPackCatalogEntry]) -> list[dict[str, object]]:
    return [
        {
            "name": entry.name,
            "source": entry.source_group,
            "snapshot": entry.snapshot_date or "",
            "rosters": entry.roster_count,
            "picks": entry.pick_count,
            "errors": entry.error_count,
            "warnings": entry.warning_count,
            "applied_pack_status": entry.applied_pack_status,
            "applied_rows": entry.applied_row_count or "",
            "applied_pack_reason": entry.applied_pack_reason,
            "path": str(entry.path),
        }
        for entry in entries
    ]


def applied_pack_notice_for_path(
    entries: list[DataPackCatalogEntry],
    selected_path: str | Path,
) -> dict[str, object] | None:
    selected = _entry_for_path(entries, selected_path)
    if selected is None or not selected.applied_pack_status:
        return None
    return {
        "applied_pack_status": selected.applied_pack_status,
        "applied_rows": selected.applied_row_count,
        "reason": selected.applied_pack_reason,
        "next_action": _applied_pack_next_action(selected.applied_pack_status),
        "path": str(selected.path),
    }


def _candidate_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "fact_rosters.csv").exists()
    ]


def _catalog_entry(
    path: Path,
    project_root: Path,
    default_path: Path,
) -> DataPackCatalogEntry:
    try:
        validated = validate_data_pack(path)
        error_count = sum(1 for issue in validated.issues if issue.severity == "error")
        warning_count = sum(
            1 for issue in validated.issues if issue.severity == "warning"
        )
        roster_count = len(validated.rows_by_table.get("rosters", []))
        model_output_count = len(validated.rows_by_table.get("model_outputs", []))
        pick_count = len(validated.rows_by_table.get("future_picks", []))
        snapshot_date = validated.snapshot_date
    except Exception:
        error_count = 1
        warning_count = 0
        roster_count = 0
        model_output_count = 0
        pick_count = 0
        snapshot_date = None
    applied_status, applied_reason, applied_row_count = _applied_pack_admission(
        path,
        error_count,
        warning_count,
        model_output_count,
    )

    return DataPackCatalogEntry(
        name=path.name,
        path=path,
        source_group=_source_group(path, project_root, default_path),
        snapshot_date=snapshot_date,
        error_count=error_count,
        warning_count=warning_count,
        roster_count=roster_count,
        pick_count=pick_count,
        applied_pack_status=applied_status,
        applied_pack_reason=applied_reason,
        applied_row_count=applied_row_count,
    )


def _source_group(path: Path, project_root: Path, default_path: Path) -> str:
    if path.resolve() == default_path.resolve():
        return "default"
    try:
        relative = path.resolve().relative_to((project_root / "local_exports").resolve())
    except ValueError:
        return "sample"
    return str(relative.parts[0]) if relative.parts else "generated"


def _catalog_sort_key(entry: DataPackCatalogEntry) -> tuple[int, str, str]:
    source_order = {"default": 0, "data_packs": 1, "generated": 1, "sample": 2}
    return (
        source_order.get(entry.source_group, 3),
        entry.snapshot_date or "",
        entry.name,
    )


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _applied_pack_admission(
    path: Path,
    error_count: int,
    warning_count: int,
    model_output_count: int,
) -> tuple[str, str, int]:
    manifest_path = path / MODEL_APPLIED_PACK_MANIFEST_FILE
    if not manifest_path.exists():
        return "", "", 0
    manifest = _read_json(manifest_path)
    applied_row_count = _int_or_zero(manifest.get("applied_row_count", 0))
    if error_count:
        return "blocked", "Generated applied pack has validation errors.", applied_row_count
    if model_output_count <= 0:
        return "blocked", "Generated applied pack has no model output rows.", applied_row_count
    if applied_row_count <= 0:
        return (
            "blocked",
            "Generated applied pack reports zero applied model rows.",
            applied_row_count,
        )
    if warning_count:
        return "review", "Generated applied pack has data-pack warnings.", applied_row_count
    return "ready", "Generated applied pack passed admission.", applied_row_count


def _read_json(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _int_or_zero(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _entry_for_path(
    entries: list[DataPackCatalogEntry],
    selected_path: str | Path,
) -> DataPackCatalogEntry | None:
    path = Path(selected_path)
    for entry in entries:
        try:
            if entry.path.resolve() == path.resolve():
                return entry
        except OSError:
            if str(entry.path) == str(path):
                return entry
    return None


def _applied_pack_next_action(status: str) -> str:
    if status == "ready":
        return "Open Import Review for final admission before draft-day use."
    if status == "review":
        return "Review pack health warnings before relying on this generated pack."
    return "Do not use this generated pack until it is regenerated or fixed."
