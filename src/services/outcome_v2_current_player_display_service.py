from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.nfl_usage_target_label_service import derive_nwr_points
from src.services.outcome_v2_current_feature_source_gate import (
    SEASON_STATS_POINTER_PATH,
    resolve_candidate_paths,
)

NOT_ENOUGH_INFORMATION = "Not enough information"
CURRENT_BOARD_PATH = Path(
    r"C:\NWR\Niners-War-Room\local_exports\model_v4\current_value\latest"
    r"\full_player_board_value_review_rows.csv"
)
IDENTITY_BRIDGE_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\current_identity_bridge"
    r"\outcome_v2_current_identity_bridge.csv"
)
VALIDATION_RESULTS_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended"
    r"\outcome_v2_probability_validation_results.csv"
)
MODEL_BUCKET_RATES_PATH = Path(
    r"C:\NWR_SHARED_DATA\outcome_v2_horizon\validation_extended"
    r"\outcome_v2_probability_model_bucket_rates.csv"
)
DISPLAY_ARTIFACT_PATH = Path(
    "docs/hq/outcomes/outcome_v2_horizon_20260630"
    "/outcome_v2_current_player_display.csv"
)

SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
MATCHED_IDENTITY_STATUSES = {"matched_exact", "matched_high_confidence"}
OUTCOME_V2_VERSION = "outcome_v2_current_player_display_20260630"
AS_OF_CONTEXT = "2026-pre-draft"
THIS_YEAR_DEFINITION = "2026 NFL season"
NEXT_YEAR_DEFINITION = "2027 NFL season"
WITHIN_5Y_DEFINITION = "at least once from 2026 through 2030"
DISPLAY_ONLY = "true"
FALSE_FLAG = "false"

BASE_COLUMNS = [
    "nwr_player_id",
    "sleeper_id",
    "gsis_id",
    "player_name",
    "position",
    "team",
    "eligibility_status",
    "identity_status",
    "feature_coverage_status",
    "scoring_mode",
    "outcome_v2_version",
    "as_of_context",
    "this_year_definition",
    "display_only",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "market_used_as_input",
    "dynastyprocess_used_as_input",
    "adp_used_as_input",
    "cfbd_used_as_input",
    "data_coverage_status",
    "availability_context_status",
    "caveat_summary",
    "validated_field_status",
]


@dataclass(frozen=True)
class CurrentPlayerDisplayArtifactResult:
    artifact_path: Path
    row_count: int
    eligible_probability_rows: int
    not_enough_information_rows: int
    rookie_out_of_scope_rows: int
    missing_feature_rows: int
    unsupported_position_rows: int
    included_fields: tuple[str, ...]
    blocked_fields: tuple[str, ...]
    sha256: str


def load_current_player_display_sources(
    *,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    season_stats_pointer_path: str | Path = SEASON_STATS_POINTER_PATH,
    identity_bridge_path: str | Path = IDENTITY_BRIDGE_PATH,
    validation_results_path: str | Path = VALIDATION_RESULTS_PATH,
    model_bucket_rates_path: str | Path = MODEL_BUCKET_RATES_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    stats_path, _manifest_path, _pointer = resolve_candidate_paths(season_stats_pointer_path)
    paths = [
        Path(current_board_path),
        stats_path,
        Path(identity_bridge_path),
        Path(validation_results_path),
        Path(model_bucket_rates_path),
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Outcome V2 display artifact inputs: {missing}")
    return (
        pd.read_csv(current_board_path, dtype=str),
        pd.read_csv(stats_path, dtype=str),
        pd.read_csv(identity_bridge_path, dtype=str),
        pd.read_csv(validation_results_path, dtype=str),
        pd.read_csv(model_bucket_rates_path, dtype=str),
    )


def build_current_player_display_artifact(
    current_board: pd.DataFrame,
    season_stats: pd.DataFrame,
    identity_bridge: pd.DataFrame,
    validation_results: pd.DataFrame,
    model_bucket_rates: pd.DataFrame,
) -> pd.DataFrame:
    _require_columns(
        current_board,
        {"player_id", "player_name", "position", "nfl_team"},
        "current_board",
    )
    _require_columns(
        identity_bridge,
        {
            "nwr_player_id",
            "sleeper_id",
            "gsis_id",
            "identity_status",
            "current_board_player_name",
            "current_board_position",
            "current_board_team",
        },
        "identity_bridge",
    )
    _require_columns(
        validation_results,
        {"field_id", "position", "threshold", "horizon", "validation_status"},
        "validation_results",
    )
    _require_columns(
        model_bucket_rates,
        {"field_id", "profile_bucket", "probability", "baseline_probability"},
        "model_bucket_rates",
    )

    board = _prepare_current_board(current_board)
    bridge = identity_bridge.copy().fillna("")
    feature_frame = build_current_feature_frame(season_stats)
    validated_fields = _validated_fields(validation_results)
    blocked_fields = _blocked_fields(validation_results)
    display_columns = [_display_name(field) for field in validated_fields]
    probability_lookup = _probability_lookup(model_bucket_rates)
    baseline_lookup = _baseline_lookup(validation_results)
    bridge_lookup = {
        str(row.nwr_player_id): row
        for row in bridge.itertuples(index=False)
    }
    feature_lookup = {
        str(row.player_id): row
        for row in feature_frame.itertuples(index=False)
    }

    rows: list[dict[str, Any]] = []
    for player in board.itertuples(index=False):
        bridge_row = bridge_lookup.get(str(player.nwr_player_id))
        feature_row = (
            feature_lookup.get(str(bridge_row.gsis_id))
            if bridge_row is not None and str(bridge_row.gsis_id)
            else None
        )
        out = _base_display_row(player, bridge_row, feature_row, blocked_fields)
        for column in display_columns:
            out[column] = NOT_ENOUGH_INFORMATION

        if _probability_eligible(player, bridge_row, feature_row):
            for field in validated_fields:
                if field["position"] != player.position:
                    continue
                display_name = _display_name(field)
                probability = _probability_for_field(
                    field=field,
                    feature_row=feature_row,
                    probability_lookup=probability_lookup,
                    baseline_lookup=baseline_lookup,
                )
                out[display_name] = (
                    _format_probability(probability)
                    if probability is not None
                    else NOT_ENOUGH_INFORMATION
                )
        rows.append(out)

    return pd.DataFrame(rows, columns=BASE_COLUMNS + display_columns)


def build_current_feature_frame(season_stats: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        season_stats,
        {"player_id", "player_display_name", "position", "recent_team", "season", "season_type"},
        "season_stats",
    )
    frame = season_stats.copy().fillna("")
    frame["position"] = frame["position"].astype(str).str.upper().str.strip()
    current = frame[
        frame["position"].isin(SUPPORTED_POSITIONS)
        & frame["season"].astype(str).eq("2025")
        & frame["season_type"].astype(str).eq("REG")
    ].copy()
    current["anchor_fantasy_points"] = derive_nwr_points(current)
    current["anchor_position_finish"] = (
        current.groupby(["season", "position"])["anchor_fantasy_points"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    current["anchor_games_played"] = (
        pd.to_numeric(current["games"], errors="coerce")
        if "games" in current.columns
        else pd.Series([pd.NA] * len(current), index=current.index)
    )
    return current[
        [
            "player_id",
            "player_display_name",
            "position",
            "recent_team",
            "anchor_fantasy_points",
            "anchor_position_finish",
            "anchor_games_played",
        ]
    ].copy()


def write_current_player_display_artifact(
    *,
    output_path: str | Path = DISPLAY_ARTIFACT_PATH,
    current_board_path: str | Path = CURRENT_BOARD_PATH,
    season_stats_pointer_path: str | Path = SEASON_STATS_POINTER_PATH,
    identity_bridge_path: str | Path = IDENTITY_BRIDGE_PATH,
    validation_results_path: str | Path = VALIDATION_RESULTS_PATH,
    model_bucket_rates_path: str | Path = MODEL_BUCKET_RATES_PATH,
) -> CurrentPlayerDisplayArtifactResult:
    (
        current_board,
        season_stats,
        identity_bridge,
        validation_results,
        model_bucket_rates,
    ) = load_current_player_display_sources(
        current_board_path=current_board_path,
        season_stats_pointer_path=season_stats_pointer_path,
        identity_bridge_path=identity_bridge_path,
        validation_results_path=validation_results_path,
        model_bucket_rates_path=model_bucket_rates_path,
    )
    artifact = build_current_player_display_artifact(
        current_board,
        season_stats,
        identity_bridge,
        validation_results,
        model_bucket_rates,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    artifact.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)
    return _result_for_artifact(path, artifact, validation_results)


def summarize_current_player_display_artifact(
    artifact: pd.DataFrame,
    validation_results: pd.DataFrame,
) -> CurrentPlayerDisplayArtifactResult:
    return _result_for_artifact(Path(""), artifact, validation_results)


def _base_display_row(
    player: Any,
    bridge_row: Any | None,
    feature_row: Any | None,
    blocked_fields: tuple[str, ...],
) -> dict[str, Any]:
    identity_status = _bridge_value(bridge_row, "identity_status")
    gsis_id = _bridge_value(bridge_row, "gsis_id")
    sleeper_id = _bridge_value(bridge_row, "sleeper_id") or str(player.nwr_player_id)
    eligibility_status = _eligibility_status(player, bridge_row, feature_row)
    feature_status = _feature_coverage_status(eligibility_status)
    has_feature = eligibility_status == "eligible_veteran_feature_covered"
    blocked_text = "|".join(blocked_fields) if blocked_fields else "none"
    return {
        "nwr_player_id": player.nwr_player_id,
        "sleeper_id": sleeper_id,
        "gsis_id": gsis_id,
        "player_name": player.player_name,
        "position": player.position,
        "team": player.team,
        "eligibility_status": eligibility_status,
        "identity_status": identity_status or _identity_status_for_missing(player),
        "feature_coverage_status": feature_status,
        "scoring_mode": (
            "partial_exact_first_down_scoring_missing_sack_fumbles_lost"
            if has_feature
            else NOT_ENOUGH_INFORMATION
        ),
        "outcome_v2_version": OUTCOME_V2_VERSION,
        "as_of_context": AS_OF_CONTEXT,
        "this_year_definition": THIS_YEAR_DEFINITION,
        "display_only": DISPLAY_ONLY,
        "model_use_allowed": FALSE_FLAG,
        "training_allowed": FALSE_FLAG,
        "source_truth_allowed": FALSE_FLAG,
        "market_used_as_input": FALSE_FLAG,
        "dynastyprocess_used_as_input": FALSE_FLAG,
        "adp_used_as_input": FALSE_FLAG,
        "cfbd_used_as_input": FALSE_FLAG,
        "data_coverage_status": "partial_2025_feature_source_approval",
        "availability_context_status": (
            "partial_availability_context_missing_games"
            if has_feature
            else NOT_ENOUGH_INFORMATION
        ),
        "caveat_summary": _caveat_summary(eligibility_status),
        "validated_field_status": (
            "validated_position_fields_only; blocked_fields="
            f"{blocked_text}; next_year={NEXT_YEAR_DEFINITION}; "
            f"within_5y={WITHIN_5Y_DEFINITION}"
        ),
    }


def _prepare_current_board(current_board: pd.DataFrame) -> pd.DataFrame:
    board = current_board.copy().fillna("")
    return pd.DataFrame(
        {
            "nwr_player_id": _text_series(board, "player_id"),
            "player_name": _text_series(board, "player_name"),
            "position": _text_series(board, "position").str.upper(),
            "team": _text_series(board, "nfl_team").str.upper(),
        }
    )


def _validated_fields(validation_results: pd.DataFrame) -> list[dict[str, Any]]:
    frame = validation_results.copy().fillna("")
    eligible = frame[
        frame["validation_status"].eq("PASS_APP_DISPLAY_VALIDATION")
        & frame.get("display_eligible", "true").astype(str).str.lower().isin(["true", ""])
    ].copy()
    rows = [
        {
            "field_id": str(row.field_id),
            "position": str(row.position),
            "threshold": int(row.threshold),
            "horizon": str(row.horizon),
        }
        for row in eligible.itertuples(index=False)
    ]
    return sorted(rows, key=_field_sort_key)


def _blocked_fields(validation_results: pd.DataFrame) -> tuple[str, ...]:
    frame = validation_results.copy().fillna("")
    blocked = frame[~frame["validation_status"].eq("PASS_APP_DISPLAY_VALIDATION")]
    return tuple(str(value) for value in blocked["field_id"].tolist())


def _probability_for_field(
    *,
    field: dict[str, Any],
    feature_row: Any,
    probability_lookup: dict[tuple[str, str], float],
    baseline_lookup: dict[str, float],
) -> float | None:
    field_id = str(field["field_id"])
    bucket = _profile_bucket(
        finish=feature_row.anchor_position_finish,
        points=feature_row.anchor_fantasy_points,
        games=feature_row.anchor_games_played,
        threshold=int(field["threshold"]),
    )
    probability = probability_lookup.get((field_id, bucket))
    if probability is None:
        probability = baseline_lookup.get(field_id)
    return probability


def _profile_bucket(*, finish: Any, points: Any, games: Any, threshold: int) -> str:
    finish_value = pd.to_numeric(finish, errors="coerce")
    points_value = pd.to_numeric(points, errors="coerce")
    games_value = pd.to_numeric(games, errors="coerce")
    if pd.isna(finish_value):
        if pd.isna(points_value) or float(points_value) <= 0:
            return "missing_or_no_prior_production"
        return "missing_finish_has_points"
    if float(finish_value) <= threshold:
        return "prior_threshold_hit"
    if float(finish_value) <= threshold * 2:
        return "near_threshold"
    if float(finish_value) <= threshold * 3:
        return "depth_relevant"
    if (
        not pd.isna(games_value)
        and float(games_value) >= 8
        and not pd.isna(points_value)
        and float(points_value) > 0
    ):
        return "active_low_finish"
    return "limited_or_inactive"


def _probability_lookup(model_bucket_rates: pd.DataFrame) -> dict[tuple[str, str], float]:
    lookup: dict[tuple[str, str], float] = {}
    for row in model_bucket_rates.fillna("").itertuples(index=False):
        probability = pd.to_numeric(row.probability, errors="coerce")
        if not pd.isna(probability):
            lookup[(str(row.field_id), str(row.profile_bucket))] = float(probability)
    return lookup


def _baseline_lookup(validation_results: pd.DataFrame) -> dict[str, float]:
    lookup: dict[str, float] = {}
    if "baseline_probability" not in validation_results.columns:
        return lookup
    for row in validation_results.fillna("").itertuples(index=False):
        probability = pd.to_numeric(row.baseline_probability, errors="coerce")
        if not pd.isna(probability):
            lookup[str(row.field_id)] = float(probability)
    return lookup


def _probability_eligible(player: Any, bridge_row: Any | None, feature_row: Any | None) -> bool:
    if str(player.position) not in SUPPORTED_POSITIONS:
        return False
    if bridge_row is None or feature_row is None:
        return False
    return str(bridge_row.identity_status) in MATCHED_IDENTITY_STATUSES


def _eligibility_status(player: Any, bridge_row: Any | None, feature_row: Any | None) -> str:
    if str(player.position) not in SUPPORTED_POSITIONS:
        return "out_of_scope_unsupported_position"
    if bridge_row is None:
        return "missing_identity_bridge"
    identity_status = str(bridge_row.identity_status)
    if identity_status == "out_of_scope_rookie_or_prospect":
        return "out_of_scope_rookie_or_prospect"
    if identity_status not in MATCHED_IDENTITY_STATUSES:
        return "missing_or_unapproved_identity_bridge"
    if feature_row is None:
        return "missing_current_feature_coverage"
    return "eligible_veteran_feature_covered"


def _feature_coverage_status(eligibility_status: str) -> str:
    return {
        "eligible_veteran_feature_covered": "feature_covered_2025_regular_season",
        "missing_current_feature_coverage": "missing_2025_feature_row",
        "out_of_scope_rookie_or_prospect": "out_of_scope_rookie_or_prospect",
        "out_of_scope_unsupported_position": "out_of_scope_unsupported_position",
        "missing_identity_bridge": "missing_identity_bridge",
        "missing_or_unapproved_identity_bridge": "missing_or_unapproved_identity_bridge",
    }.get(eligibility_status, NOT_ENOUGH_INFORMATION)


def _caveat_summary(eligibility_status: str) -> str:
    if eligibility_status == "eligible_veteran_feature_covered":
        return (
            "Display-only Outcome V2 probability context from approved partial 2025 "
            "feature source; games missing, sack_fumbles_lost missing, availability "
            "not clean health."
        )
    if eligibility_status == "missing_current_feature_coverage":
        return "Not enough information: no approved 2025 feature row."
    if eligibility_status == "out_of_scope_rookie_or_prospect":
        return "Not enough information: Normal Outcome V2 excludes rookies/prospects."
    if eligibility_status == "out_of_scope_unsupported_position":
        return "Not enough information: unsupported Outcome V2 position."
    return "Not enough information: identity or feature coverage is not approved."


def _identity_status_for_missing(player: Any) -> str:
    if str(player.position) not in SUPPORTED_POSITIONS:
        return "not_applicable_unsupported_position"
    return "missing_identity_bridge"


def _display_name(field: dict[str, Any]) -> str:
    horizon_label = {
        "this_year": "This Year",
        "next_year": "Next Year",
        "within_5y": "Within 5Y",
    }[str(field["horizon"])]
    return f"{field['position']} T{field['threshold']} {horizon_label}"


def _field_sort_key(field: dict[str, Any]) -> tuple[int, int, int]:
    position_order = {position: index for index, position in enumerate(SUPPORTED_POSITIONS)}
    horizon_order = {"this_year": 0, "next_year": 1, "within_5y": 2}
    return (
        position_order.get(str(field["position"]), 99),
        horizon_order.get(str(field["horizon"]), 99),
        int(field["threshold"]),
    )


def _format_probability(probability: float) -> str:
    return f"{probability * 100:.1f}%"


def _result_for_artifact(
    path: Path,
    artifact: pd.DataFrame,
    validation_results: pd.DataFrame,
) -> CurrentPlayerDisplayArtifactResult:
    probability_columns = [column for column in artifact.columns if column not in BASE_COLUMNS]
    has_probability = artifact[probability_columns].ne(NOT_ENOUGH_INFORMATION).any(axis=1)
    not_enough_rows = artifact[probability_columns].eq(NOT_ENOUGH_INFORMATION).all(axis=1)
    blocked_fields = _blocked_fields(validation_results)
    sha = _sha256(path) if path and path.is_file() else ""
    return CurrentPlayerDisplayArtifactResult(
        artifact_path=path,
        row_count=len(artifact),
        eligible_probability_rows=int(has_probability.sum()),
        not_enough_information_rows=int(not_enough_rows.sum()),
        rookie_out_of_scope_rows=int(
            artifact["eligibility_status"].eq("out_of_scope_rookie_or_prospect").sum()
        ),
        missing_feature_rows=int(
            artifact["eligibility_status"].eq("missing_current_feature_coverage").sum()
        ),
        unsupported_position_rows=int(
            artifact["eligibility_status"].eq("out_of_scope_unsupported_position").sum()
        ),
        included_fields=tuple(probability_columns),
        blocked_fields=blocked_fields,
        sha256=sha,
    )


def _bridge_value(bridge_row: Any | None, field: str) -> str:
    if bridge_row is None:
        return ""
    value = getattr(bridge_row, field, "")
    return "" if pd.isna(value) else str(value).strip()


def _text_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([""] * len(frame), index=frame.index)
    return frame[column].fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def _require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
