from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

MODEL_INPUT_ALLOWED = "no"
APP_WIRING_ALLOWED = "no"
TRAINING_ALLOWED = "no"
APPROVAL_STATUS = "review_only_historical_labels"
SCORING_MODE_EXACT = "exact_verified_first_downs"
NOT_ENOUGH_INFORMATION = "Not enough information"

SHARED_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels")
HISTORICAL_EXPANSION_ROOT = Path(
    r"C:\NWR_SHARED_DATA\nfl_usage_cache\target_backtest\historical_expansion"
)
PLAYER_SEASON_PANEL_PATH = (
    HISTORICAL_EXPANSION_ROOT / "panels" / "player_season_core_usage_panel.csv"
)
PLAYER_WEEK_PANEL_PATH = HISTORICAL_EXPANSION_ROOT / "panels" / "player_week_core_usage_panel.csv"
TARGET_LABELS_PATH = HISTORICAL_EXPANSION_ROOT / "nfl_usage_expanded_target_labels_v0.csv"
JOINED_PANEL_PATH = (
    HISTORICAL_EXPANSION_ROOT / "nfl_usage_expanded_target_backtest_joined_panel_v0.csv"
)

SEASON_OUTCOME_FILENAME = "outcome_v2_season_outcome_labels.csv"
ANCHOR_HORIZON_FILENAME = "outcome_v2_anchor_horizon_labels.csv"
MANIFEST_FILENAME = "outcome_v2_historical_label_manifest.csv"
VALIDATION_FILENAME = "outcome_v2_historical_label_validation_summary.csv"

SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
THRESHOLDS = (6, 12, 24, 36)
POSITION_THRESHOLDS: dict[str, tuple[int, ...]] = {
    "QB": (6, 12),
    "RB": (6, 12, 24, 36),
    "WR": (6, 12, 24, 36),
    "TE": (6, 12),
}

BLOCKED_SOURCE_TOKENS = (
    "adp",
    "market",
    "dynastyprocess",
    "cfbd",
    "gmail",
    "rotowire",
    "fantasypros",
    "projection",
    "analyst",
    "trade_value",
    "true_routes",
    "tprr",
    "yprr",
    "lane_exchange",
)


@dataclass(frozen=True)
class OutcomeV2HistoricalLabelBuildResult:
    output_root: Path
    season_label_path: Path
    anchor_label_path: Path
    manifest_path: Path
    validation_path: Path
    season_rows: int
    anchor_rows: int
    validation_status: str


def required_source_paths() -> dict[str, Path]:
    return {
        "player_season_panel": PLAYER_SEASON_PANEL_PATH,
        "player_week_panel": PLAYER_WEEK_PANEL_PATH,
        "target_labels": TARGET_LABELS_PATH,
        "joined_panel": JOINED_PANEL_PATH,
    }


def validate_source_paths(source_paths: dict[str, Path] | None = None) -> list[dict[str, Any]]:
    paths = source_paths or required_source_paths()
    rows: list[dict[str, Any]] = []
    for name, path in paths.items():
        status = "exists_readable" if path.exists() and path.is_file() else "missing"
        rows.append(
            {
                "source_name": name,
                "path": str(path),
                "status": status,
                "blocked_source_scan": _blocked_source_status(path),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    return rows


def load_review_only_sources(
    source_paths: dict[str, Path] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    paths = source_paths or required_source_paths()
    source_report = validate_source_paths(paths)
    missing = [row["path"] for row in source_report if row["status"] != "exists_readable"]
    if missing:
        raise FileNotFoundError(f"Missing required Outcome V2 label source files: {missing}")
    blocked = [row["path"] for row in source_report if row["blocked_source_scan"] != "pass"]
    if blocked:
        raise ValueError(f"Blocked source path detected for Outcome V2 label factory: {blocked}")
    return (
        pd.read_csv(paths["player_season_panel"]),
        pd.read_csv(paths["player_week_panel"]),
        pd.read_csv(paths["target_labels"]),
        pd.read_csv(paths["joined_panel"]),
    )


def build_season_outcome_labels(target_labels: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        target_labels,
        {
            "target_season",
            "player_id",
            "player_name",
            "position",
            "recent_team",
            "next_season_nwr_points",
            "next_season_games",
            "next_season_position_rank",
        },
        "target_labels",
    )
    frame = target_labels.copy()
    frame["position"] = frame["position"].astype(str).str.upper()
    frame = frame[frame["position"].isin(SUPPORTED_POSITIONS)].copy()
    frame["season"] = pd.to_numeric(frame["target_season"], errors="coerce").astype("Int64")
    frame["position_finish"] = pd.to_numeric(
        frame["next_season_position_rank"],
        errors="coerce",
    ).astype("Int64")
    frame["games_played"] = pd.to_numeric(
        frame["next_season_games"],
        errors="coerce",
    ).astype("Int64")
    frame["fantasy_points"] = pd.to_numeric(frame["next_season_nwr_points"], errors="coerce")
    frame["team"] = frame["recent_team"].fillna("").astype(str)
    frame["scoring_mode"] = SCORING_MODE_EXACT
    frame["availability_context"] = frame["games_played"].apply(_availability_context)
    frame["data_quality_status"] = "review_only_factual_outcome"

    for threshold in THRESHOLDS:
        frame[f"top_{threshold}_hit"] = frame.apply(
            lambda row, threshold=threshold: _threshold_result(
                row["position"],
                row["position_finish"],
                threshold,
            ),
            axis=1,
        )

    out = frame[
        [
            "player_id",
            "player_name",
            "position",
            "season",
            "team",
            "scoring_mode",
            "fantasy_points",
            "position_finish",
            "games_played",
            "availability_context",
            "top_6_hit",
            "top_12_hit",
            "top_24_hit",
            "top_36_hit",
            "data_quality_status",
        ]
    ].copy()
    out["approval_status"] = APPROVAL_STATUS
    out["model_input_allowed"] = MODEL_INPUT_ALLOWED
    out["training_allowed"] = TRAINING_ALLOWED
    out["app_wiring_allowed"] = APP_WIRING_ALLOWED
    return out.sort_values(["season", "position", "position_finish", "player_name"]).reset_index(
        drop=True
    )


def build_anchor_horizon_labels(
    anchor_panel: pd.DataFrame,
    season_labels: pd.DataFrame,
) -> pd.DataFrame:
    _require_columns(
        anchor_panel,
        {"season", "player_id", "player_name", "position", "team"},
        "anchor_panel",
    )
    _require_columns(
        season_labels,
        {
            "season",
            "player_id",
            "position",
            "top_6_hit",
            "top_12_hit",
            "top_24_hit",
            "top_36_hit",
        },
        "season_labels",
    )
    anchors = anchor_panel.copy()
    anchors["position"] = anchors["position"].astype(str).str.upper()
    anchors = anchors[anchors["position"].isin(SUPPORTED_POSITIONS)].copy()
    anchors["anchor_season"] = pd.to_numeric(anchors["season"], errors="coerce").astype("Int64")
    anchors = anchors.dropna(subset=["anchor_season", "player_id"]).drop_duplicates(
        ["player_id", "anchor_season"],
    )

    labels = season_labels.copy()
    labels["season"] = pd.to_numeric(labels["season"], errors="coerce").astype("Int64")
    max_target_season = int(labels["season"].dropna().max())
    label_index = {
        (str(row.player_id), int(row.season)): row
        for row in labels.itertuples(index=False)
        if pd.notna(row.season)
    }

    rows: list[dict[str, Any]] = []
    for anchor in anchors.itertuples(index=False):
        player_id = str(anchor.player_id)
        anchor_season = int(anchor.anchor_season)
        position = str(anchor.position).upper()
        row: dict[str, Any] = {
            "player_id": player_id,
            "player_name": str(anchor.player_name),
            "position": position,
            "anchor_season": anchor_season,
            "team": str(anchor.team),
            "this_year_window_complete": _single_window_complete(
                label_index,
                player_id,
                position,
                anchor_season + 1,
                max_target_season,
            ),
            "next_year_window_complete": _single_window_complete(
                label_index,
                player_id,
                position,
                anchor_season + 2,
                max_target_season,
            ),
            "within_5y_window_complete": _multi_window_complete(
                label_index,
                player_id,
                position,
                range(anchor_season + 1, anchor_season + 6),
                max_target_season,
            ),
        }
        for threshold in THRESHOLDS:
            row[f"this_year_top_{threshold}_hit"] = _single_horizon_result(
                label_index,
                player_id,
                position,
                anchor_season + 1,
                threshold,
                max_target_season,
            )
            row[f"next_year_top_{threshold}_hit"] = _single_horizon_result(
                label_index,
                player_id,
                position,
                anchor_season + 2,
                threshold,
                max_target_season,
            )
            row[f"within_5y_top_{threshold}_hit"] = _within_horizon_result(
                label_index,
                player_id,
                position,
                range(anchor_season + 1, anchor_season + 6),
                threshold,
                max_target_season,
            )
        row["censoring_status"] = _censoring_status(row)
        row["approval_status"] = APPROVAL_STATUS
        row["model_input_allowed"] = MODEL_INPUT_ALLOWED
        row["training_allowed"] = TRAINING_ALLOWED
        row["app_wiring_allowed"] = APP_WIRING_ALLOWED
        rows.append(row)

    columns = [
        "player_id",
        "player_name",
        "position",
        "anchor_season",
        "team",
        "this_year_top_6_hit",
        "this_year_top_12_hit",
        "this_year_top_24_hit",
        "this_year_top_36_hit",
        "next_year_top_6_hit",
        "next_year_top_12_hit",
        "next_year_top_24_hit",
        "next_year_top_36_hit",
        "within_5y_top_6_hit",
        "within_5y_top_12_hit",
        "within_5y_top_24_hit",
        "within_5y_top_36_hit",
        "this_year_window_complete",
        "next_year_window_complete",
        "within_5y_window_complete",
        "censoring_status",
        "approval_status",
        "model_input_allowed",
        "training_allowed",
        "app_wiring_allowed",
    ]
    out = pd.DataFrame(rows, columns=columns)
    return out.sort_values(["anchor_season", "position", "player_name"]).reset_index(drop=True)


def validation_summary_rows(
    source_counts: dict[str, int],
    season_labels: pd.DataFrame,
    anchor_labels: pd.DataFrame,
    source_paths: dict[str, Path] | None = None,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    paths = source_paths or required_source_paths()
    for source_name, path in paths.items():
        rows.append(_metric(f"source_path_{source_name}", str(path)))
        rows.append(_metric(f"source_exists_{source_name}", str(path.exists()).lower()))
    for source_name, count in source_counts.items():
        rows.append(_metric(f"input_rows_{source_name}", count))

    season_values = pd.to_numeric(season_labels["season"], errors="coerce").dropna().astype(int)
    anchor_values = (
        pd.to_numeric(anchor_labels["anchor_season"], errors="coerce").dropna().astype(int)
    )
    rows.extend(
        [
            _metric("season_label_rows", len(season_labels)),
            _metric("anchor_horizon_rows", len(anchor_labels)),
            _metric("season_label_seasons", _season_range_text(season_values)),
            _metric("anchor_seasons", _season_range_text(anchor_values)),
            _metric(
                "complete_this_year_windows",
                int(anchor_labels["this_year_window_complete"].sum()),
            ),
            _metric(
                "complete_next_year_windows",
                int(anchor_labels["next_year_window_complete"].sum()),
            ),
            _metric(
                "complete_within_5y_windows",
                int(anchor_labels["within_5y_window_complete"].sum()),
            ),
            _metric(
                "right_censored_rows",
                int(anchor_labels["censoring_status"].str.contains("right_censored").sum()),
            ),
            _metric(
                "missing_target_data_rows",
                int(anchor_labels["censoring_status"].str.contains("missing_target_data").sum()),
            ),
        ]
    )

    for mode, count in season_labels["scoring_mode"].value_counts(dropna=False).items():
        rows.append(_metric(f"scoring_mode_count_{mode}", int(count)))
    for context, count in season_labels["availability_context"].value_counts(dropna=False).items():
        rows.append(_metric(f"availability_context_count_{context}", int(count)))
    for position in SUPPORTED_POSITIONS:
        position_rows = season_labels[season_labels["position"] == position]
        rows.append(_metric(f"season_rows_{position}", len(position_rows)))
        for threshold in THRESHOLDS:
            col = f"top_{threshold}_hit"
            applicable = position_rows[position_rows[col].isin({"hit", "miss"})]
            hit_count = int((applicable[col] == "hit").sum())
            total = len(applicable)
            rate = hit_count / total if total else 0.0
            rows.append(_metric(f"hit_rate_{position}_top_{threshold}", f"{rate:.6f}"))
            rows.append(_metric(f"hit_count_{position}_top_{threshold}", hit_count))
            rows.append(_metric(f"applicable_count_{position}_top_{threshold}", total))
    rows.append(_metric("blocked_source_scan", "pass"))
    rows.append(_metric("model_input_allowed", MODEL_INPUT_ALLOWED))
    rows.append(_metric("training_allowed", TRAINING_ALLOWED))
    rows.append(_metric("app_wiring_allowed", APP_WIRING_ALLOWED))
    rows.append(
        _metric(
            "data_quality_caveat",
            "Review-only factual labels; censored/missing windows are not treated as misses.",
        )
    )
    return rows


def write_historical_label_artifacts(
    output_root: Path = SHARED_OUTPUT_ROOT,
    source_paths: dict[str, Path] | None = None,
) -> OutcomeV2HistoricalLabelBuildResult:
    paths = source_paths or required_source_paths()
    player_season, player_week, target_labels, joined_panel = load_review_only_sources(paths)
    season_labels = build_season_outcome_labels(target_labels)
    anchor_labels = build_anchor_horizon_labels(player_season, season_labels)
    source_counts = {
        "player_season_panel": len(player_season),
        "player_week_panel": len(player_week),
        "target_labels": len(target_labels),
        "joined_panel": len(joined_panel),
    }
    validation = pd.DataFrame(
        validation_summary_rows(source_counts, season_labels, anchor_labels, paths)
    )

    output_root.mkdir(parents=True, exist_ok=True)
    season_path = output_root / SEASON_OUTCOME_FILENAME
    anchor_path = output_root / ANCHOR_HORIZON_FILENAME
    validation_path = output_root / VALIDATION_FILENAME
    manifest_path = output_root / MANIFEST_FILENAME

    season_labels.to_csv(season_path, index=False)
    anchor_labels.to_csv(anchor_path, index=False)
    validation.to_csv(validation_path, index=False)
    manifest = pd.DataFrame(
        _manifest_rows(
            {
                "season_outcome_labels": season_path,
                "anchor_horizon_labels": anchor_path,
                "validation_summary": validation_path,
            },
            source_paths=paths,
        )
    )
    manifest.to_csv(manifest_path, index=False)
    validation_status = "GREEN_REVIEW_ONLY_LABELS_BUILT"
    return OutcomeV2HistoricalLabelBuildResult(
        output_root=output_root,
        season_label_path=season_path,
        anchor_label_path=anchor_path,
        manifest_path=manifest_path,
        validation_path=validation_path,
        season_rows=len(season_labels),
        anchor_rows=len(anchor_labels),
        validation_status=validation_status,
    )


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _threshold_result(position: str, position_finish: Any, threshold: int) -> str:
    position = str(position).upper()
    if threshold not in POSITION_THRESHOLDS.get(position, ()):
        return "not_applicable"
    if pd.isna(position_finish):
        return NOT_ENOUGH_INFORMATION
    return "hit" if int(position_finish) <= threshold else "miss"


def _single_window_complete(
    label_index: dict[tuple[str, int], Any],
    player_id: str,
    position: str,
    target_season: int,
    max_target_season: int,
) -> bool:
    return (
        _target_row(label_index, player_id, position, target_season, max_target_season)
        is not None
    )


def _multi_window_complete(
    label_index: dict[tuple[str, int], Any],
    player_id: str,
    position: str,
    target_seasons: range,
    max_target_season: int,
) -> bool:
    return all(
        _target_row(label_index, player_id, position, season, max_target_season) is not None
        for season in target_seasons
    )


def _single_horizon_result(
    label_index: dict[tuple[str, int], Any],
    player_id: str,
    position: str,
    target_season: int,
    threshold: int,
    max_target_season: int,
) -> str:
    if threshold not in POSITION_THRESHOLDS.get(position, ()):
        return "not_applicable"
    row = _target_row(label_index, player_id, position, target_season, max_target_season)
    if row is None:
        return NOT_ENOUGH_INFORMATION
    return str(getattr(row, f"top_{threshold}_hit"))


def _within_horizon_result(
    label_index: dict[tuple[str, int], Any],
    player_id: str,
    position: str,
    target_seasons: range,
    threshold: int,
    max_target_season: int,
) -> str:
    if threshold not in POSITION_THRESHOLDS.get(position, ()):
        return "not_applicable"
    rows = [
        _target_row(label_index, player_id, position, season, max_target_season)
        for season in target_seasons
    ]
    if any(row is None for row in rows):
        return NOT_ENOUGH_INFORMATION
    return "hit" if any(getattr(row, f"top_{threshold}_hit") == "hit" for row in rows) else "miss"


def _target_row(
    label_index: dict[tuple[str, int], Any],
    player_id: str,
    position: str,
    target_season: int,
    max_target_season: int,
) -> Any | None:
    if target_season > max_target_season:
        return None
    row = label_index.get((player_id, target_season))
    if row is None:
        return None
    if str(row.position).upper() != position:
        return None
    return row


def _censoring_status(row: dict[str, Any]) -> str:
    incomplete = [
        name
        for name in (
            "this_year_window_complete",
            "next_year_window_complete",
            "within_5y_window_complete",
        )
        if not row[name]
    ]
    if not incomplete:
        return "complete"
    has_missing = any(
        value == NOT_ENOUGH_INFORMATION
        for key, value in row.items()
        if key.endswith("_hit") and "within_5y" not in key
    )
    if not row["within_5y_window_complete"]:
        if has_missing:
            return "right_censored_or_missing_target_data_not_fabricated"
        return "right_censored_future_window"
    return "missing_target_data_not_fabricated"


def _availability_context(games_played: Any) -> str:
    if pd.isna(games_played):
        return NOT_ENOUGH_INFORMATION
    games = int(games_played)
    if games <= 0:
        return NOT_ENOUGH_INFORMATION
    if games <= 4:
        return "limited_availability_1_to_4_games"
    if games <= 8:
        return "limited_availability_5_to_8_games"
    if games <= 13:
        return "partial_availability_9_to_13_games"
    return "available_14_plus_games"


def _blocked_source_status(path: Path) -> str:
    normalized = str(path).lower().replace("\\", "/")
    return "blocked" if any(token in normalized for token in BLOCKED_SOURCE_TOKENS) else "pass"


def _metric(name: str, value: Any) -> dict[str, str]:
    return {"metric": name, "value": str(value)}


def _season_range_text(values: pd.Series) -> str:
    if values.empty:
        return ""
    unique = sorted(values.unique().tolist())
    return f"{min(unique)}-{max(unique)} ({';'.join(str(value) for value in unique)})"


def _manifest_rows(
    artifacts: dict[str, Path],
    source_paths: dict[str, Path],
) -> list[dict[str, Any]]:
    created_at = datetime.now(UTC).isoformat()
    rows: list[dict[str, Any]] = []
    for artifact_name, path in artifacts.items():
        rows.append(
            {
                "artifact_name": artifact_name,
                "path": str(path),
                "row_count": _csv_row_count(path),
                "sha256": _sha256(path),
                "created_at": created_at,
                "approval_status": APPROVAL_STATUS,
                "model_input_allowed": MODEL_INPUT_ALLOWED,
                "training_allowed": TRAINING_ALLOWED,
                "app_wiring_allowed": APP_WIRING_ALLOWED,
                "source_paths": ";".join(str(source_path) for source_path in source_paths.values()),
                "notes": (
                    "Review-only historical factual labels; not app-facing, not model training."
                ),
            }
        )
    return rows


def _csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _line in handle) - 1, 0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
