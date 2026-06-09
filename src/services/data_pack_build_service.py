from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.data.csv_schemas import CSV_SCHEMAS, REQUIRED_V1_FILES
from src.models.pick_values import PickValueConfig, pick_value
from src.services.lve_rank_merge_service import RANK_PROVENANCE, canonical_name
from src.services.veteran_model_service import (
    generated_model_output_rows,
    run_veteran_model_from_dir,
)

DEFAULT_DATA_PACK_OUTPUT_ROOT = Path("local_exports/data_packs")


@dataclass(frozen=True)
class DataPackBuildResult:
    output_dir: Path
    files: dict[str, Path]
    counts: dict[str, int]
    warnings: tuple[str, ...]


def build_data_pack_from_refresh(
    *,
    sleeper_output_dir: str | Path,
    merged_rank_output_dir: str | Path | None = None,
    veteran_model_input_dir: str | Path | None = None,
    output_root: str | Path = DEFAULT_DATA_PACK_OUTPUT_ROOT,
    data_pack_name: str | None = None,
) -> DataPackBuildResult:
    sleeper_dir = Path(sleeper_output_dir)
    merged_dir = Path(merged_rank_output_dir) if merged_rank_output_dir else None
    warnings: list[str] = []
    roster_source = _resolve_roster_source(sleeper_dir, merged_dir, warnings)
    roster_rows = _read_csv(roster_source)
    pick_rows = _read_csv(sleeper_dir / "sleeper_future_picks.csv")
    league_settings = _read_csv(sleeper_dir / "sleeper_league_settings.csv")
    snapshot_date = _first_value(roster_rows, "snapshot_date") or _snapshot_from_dir(sleeper_dir)
    season = _first_value(roster_rows, "season") or _setting_value(league_settings, "season")
    league_id = _setting_value(league_settings, "league_id") or _league_id_from_dir(sleeper_dir)

    pack_name = data_pack_name or f"{sleeper_dir.name}_data_pack"
    output_dir = Path(output_root) / pack_name
    output_dir.mkdir(parents=True, exist_ok=True)
    computed_at = datetime.now(UTC).isoformat()
    model_rows = _model_output_rows(
        roster_rows=roster_rows,
        snapshot_date=snapshot_date,
        veteran_model_input_dir=Path(veteran_model_input_dir) if veteran_model_input_dir else None,
        computed_at=computed_at,
        warnings=warnings,
    )

    table_rows = {
        "dim_players.csv": _player_rows(roster_rows, snapshot_date),
        "fact_rosters.csv": _roster_rows(roster_rows, league_id),
        "fact_official_rankings.csv": _ranking_rows(roster_rows, snapshot_date),
        "fact_future_picks.csv": _future_pick_rows(pick_rows),
        "fact_pick_values.csv": _pick_value_rows(pick_rows, snapshot_date, season),
        "model_outputs.csv": model_rows,
        "metadata_sources.csv": _metadata_rows(
            snapshot_date=snapshot_date,
            pack_name=pack_name,
            sleeper_dir=sleeper_dir,
            merged_dir=merged_dir,
            roster_source=roster_source,
            has_scored_model_outputs=_has_scored_model_outputs(model_rows),
        ),
    }
    files = {file_name: output_dir / file_name for file_name in REQUIRED_V1_FILES}
    for file_name, rows in table_rows.items():
        _write_schema_csv(files[file_name], file_name, rows)

    return DataPackBuildResult(
        output_dir=output_dir,
        files=files,
        counts={name: _row_count(path) for name, path in files.items()},
        warnings=tuple(warnings),
    )


def find_latest_rank_merge_for_snapshot(
    *,
    sleeper_output_dir: str | Path,
    merged_output_root: str | Path,
) -> Path | None:
    root = Path(merged_output_root)
    snapshot_name = Path(sleeper_output_dir).name
    expected_name = f"{snapshot_name}_pdf_ranks"
    expected_path = root / expected_name
    if (expected_path / "sleeper_rosters_with_pdf_ranks.csv").exists():
        return expected_path
    if not root.exists():
        return None
    candidates = [
        path
        for path in root.iterdir()
        if path.is_dir()
        and path.name.startswith(snapshot_name)
        and (path / "sleeper_rosters_with_pdf_ranks.csv").exists()
    ]
    return max(candidates, key=lambda path: path.name) if candidates else None


def data_pack_status_rows(result: DataPackBuildResult) -> list[dict[str, object]]:
    return [
        {
            "file": file_name,
            "rows": result.counts.get(file_name, 0),
            "output_path": str(path),
        }
        for file_name, path in result.files.items()
    ]


def _resolve_roster_source(
    sleeper_dir: Path,
    merged_dir: Path | None,
    warnings: list[str],
) -> Path:
    if merged_dir is not None:
        merged_rosters = merged_dir / "sleeper_rosters_with_pdf_ranks.csv"
        if merged_rosters.exists():
            return merged_rosters
        warnings.append(f"Merged roster file is missing: {merged_rosters}")
    warnings.append("Using raw Sleeper rosters with blank league ranks.")
    return sleeper_dir / "sleeper_rosters.csv"


def _player_rows(
    roster_rows: list[dict[str, str]],
    snapshot_date: str,
) -> list[dict[str, object]]:
    rows = []
    for row in sorted(roster_rows, key=lambda item: item.get("player_id", "")):
        rows.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "merge_name": canonical_name(row.get("player_name", "")),
                "position": row.get("position", ""),
                "nfl_team": row.get("nfl_team", ""),
                "sleeper_id": row.get("player_id", ""),
                "active_flag": 1,
                "created_at": snapshot_date,
                "updated_at": snapshot_date,
            }
        )
    return _unique_by(rows, "player_id")


def _roster_rows(
    roster_rows: list[dict[str, str]],
    league_id: str,
) -> list[dict[str, object]]:
    rows = []
    for row in roster_rows:
        rows.append(
            {
                "snapshot_date": row.get("snapshot_date", ""),
                "season": row.get("season", ""),
                "league_id": league_id,
                "team_id": row.get("team_id", ""),
                "team_name": row.get("team_name", ""),
                "owner_name": row.get("owner_name", ""),
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "nfl_team": row.get("nfl_team", ""),
                "roster_status": row.get("roster_status", "rostered"),
                "league_rank": row.get("league_rank", ""),
                "official_rank": row.get("league_rank", ""),
                "source": row.get("source", "sleeper_api"),
            }
        )
    return rows


def _ranking_rows(
    roster_rows: list[dict[str, str]],
    snapshot_date: str,
) -> list[dict[str, object]]:
    rows = []
    for row in roster_rows:
        league_rank = row.get("league_rank", "")
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "season": row.get("season", ""),
                "player_id": row.get("player_id", ""),
                "source": row.get("paper_source", "") or row.get("source", ""),
                "rank_source_name": RANK_PROVENANCE if league_rank else "",
                "rank_source_date": "2026-02-27" if league_rank else "",
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "nfl_team": row.get("nfl_team", ""),
                "league_rank": league_rank,
                "official_rank": league_rank,
                "is_rank_placeholder": 1 if league_rank == "400" else 0,
            }
        )
    return rows


def _future_pick_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    return [dict(row) for row in rows]


def _pick_value_rows(
    pick_rows: list[dict[str, str]],
    snapshot_date: str,
    season: str,
) -> list[dict[str, object]]:
    current_year = int(season) if season else 2026
    config = PickValueConfig(current_pick_year=current_year)
    rows = []
    for row in pick_rows:
        certainty = _pick_certainty(row.get("certainty", "known"))
        value = pick_value(
            int(row["pick_year"]),
            int(row["round"]),
            int(row["slot"]),
            certainty=certainty,
            config=config,
        )
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "pick_year": value.pick_year,
                "pick_label": row.get("pick_label") or value.pick_label,
                "round": value.round,
                "slot": value.slot,
                "overall_pick": row.get("overall_pick") or value.overall_pick,
                "base_value_1000": round(value.base_value_1000, 1),
                "future_discount": round(value.future_discount, 3),
                "certainty_adjustment": round(value.certainty_adjustment, 3),
                "declaration_adjustment": round(value.declaration_adjustment, 1),
                "final_pick_value": round(value.final_pick_value, 1),
                "bucket": value.bucket,
                "source": "phase_10_data_pack_builder",
            }
        )
    return rows


def _neutral_model_output_rows(
    roster_rows: list[dict[str, str]],
    snapshot_date: str,
) -> list[dict[str, object]]:
    rows = []
    for row in roster_rows:
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "private_score": 50,
                "market_score": 50,
                "war_score": 50,
                "keeper_score": 50,
                "drop_candidate_score": 50,
                "confidence_score": 0.25,
                "risk_level": "needs_model",
                "recommendation": "review",
                "notes": "Neutral placeholder generated from refreshed Sleeper data.",
            }
        )
    return rows


def _model_output_rows(
    *,
    roster_rows: list[dict[str, str]],
    snapshot_date: str,
    veteran_model_input_dir: Path | None,
    computed_at: str,
    warnings: list[str],
) -> list[dict[str, object]]:
    if veteran_model_input_dir is None:
        return _neutral_model_output_rows(roster_rows, snapshot_date)
    try:
        run = run_veteran_model_from_dir(veteran_model_input_dir)
    except ValueError as exc:
        warnings.append(f"Veteran model inputs are not scoreable: {exc}")
        return _neutral_model_output_rows(roster_rows, snapshot_date)

    scores_by_player = {score.player_id: score for score in run.scores}
    rows: list[dict[str, object]] = []
    for roster_row in roster_rows:
        player_id = roster_row.get("player_id", "")
        score = scores_by_player.get(player_id)
        if score is None:
            neutral = _neutral_model_output_rows([roster_row], snapshot_date)[0]
            neutral["notes"] = "Neutral placeholder: veteran model input missing for this player."
            rows.append(neutral)
            continue
        generated = generated_model_output_rows(
            [score],
            snapshot_date=snapshot_date,
            computed_at=computed_at,
        )[0]
        generated["player_name"] = roster_row.get("player_name", "")
        generated["position"] = roster_row.get("position", "")
        rows.append(generated)
    return rows


def _has_scored_model_outputs(rows: list[dict[str, object]]) -> bool:
    return bool(rows) and all(row.get("model_version") for row in rows)


def _metadata_rows(
    *,
    snapshot_date: str,
    pack_name: str,
    sleeper_dir: Path,
    merged_dir: Path | None,
    roster_source: Path,
    has_scored_model_outputs: bool,
) -> list[dict[str, object]]:
    imported_at = datetime.now(UTC).isoformat()
    rows = []
    for file_name in REQUIRED_V1_FILES:
        source_description = str(roster_source if file_name == "fact_rosters.csv" else sleeper_dir)
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "data_pack_name": pack_name,
                "file_name": file_name,
                "source_name": "Sleeper refresh workflow",
                "source_type": "generated_local_csv",
                "source_url_or_description": source_description,
                "pulled_at": imported_at,
                "imported_at": imported_at,
                "review_status": "needs_review",
                "notes": _metadata_note(file_name, merged_dir, has_scored_model_outputs),
            }
        )
    return rows


def _metadata_note(
    file_name: str,
    merged_dir: Path | None,
    has_scored_model_outputs: bool,
) -> str:
    if file_name == "fact_rosters.csv" and merged_dir is not None:
        return "Sleeper roster ownership with PDF league ranks merged."
    if file_name == "model_outputs.csv":
        if has_scored_model_outputs:
            return "Scored by veteran_lve model from local normalized inputs."
        return "Neutral placeholders only; replace with scored model outputs."
    return "Generated by Phase 10 data-pack builder."


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_schema_csv(
    path: Path,
    file_name: str,
    rows: list[dict[str, object]],
) -> None:
    schema = CSV_SCHEMAS[file_name]
    fieldnames = list(schema.all_columns)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _row_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def _first_value(rows: list[dict[str, str]], key: str) -> str:
    for row in rows:
        value = row.get(key, "")
        if value:
            return value
    return ""


def _setting_value(rows: list[dict[str, str]], key: str) -> str:
    for row in rows:
        if row.get("setting_key") == key:
            return row.get("setting_value", "")
    return ""


def _snapshot_from_dir(path: Path) -> str:
    parts = path.name.split("_", 1)
    return parts[1] if len(parts) > 1 else path.name


def _league_id_from_dir(path: Path) -> str:
    return path.name.split("_", 1)[0]


def _pick_certainty(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"known", "projected", "estimated", "unknown"}:
        return normalized
    if normalized in {"sleeper_current_owner", "sleeper_api_traded_picks"}:
        return "known"
    return "unknown"


def _unique_by(
    rows: list[dict[str, object]],
    key: str,
) -> list[dict[str, object]]:
    seen: set[str] = set()
    unique_rows = []
    for row in rows:
        value = str(row.get(key, ""))
        if value in seen:
            continue
        seen.add(value)
        unique_rows.append(row)
    return unique_rows
