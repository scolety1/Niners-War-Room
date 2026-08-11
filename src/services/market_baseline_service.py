from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.dynastyprocess_generation_service import (
    GenerationResolutionError,
    GenerationSnapshot,
    resolve_current_generation,
    resolve_legacy_latest_snapshot,
)
from src.services.market_baseline_registry import validate_market_baseline_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_DIR = (
    REPO_ROOT
    / "local_exports"
    / "refresh_data"
    / "dynastyprocess_market_baseline"
)


def runtime_artifact_dir() -> Path:
    """Return the launcher-owned physical market root without following a repo junction."""

    configured = os.environ.get("NWR_REFRESH_DATA_ROOT", "").strip()
    refresh_root = (
        Path(configured)
        if configured
        else Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        / "NinersWarRoom"
        / "data"
        / "refresh_data"
    )
    return refresh_root / "dynastyprocess_market_baseline"

PLAYER_CONTEXT_FILENAMES = (
    "dp_player_market_context.csv",
    "dp_market_baseline_context.csv",
)
PICK_CONTEXT_FILENAMES = (
    "dp_pick_market_context.csv",
    "dp_pick_value_context.csv",
)
FRESHNESS_FILENAME = "dp_freshness_report.csv"

DISPLAY_LABEL = "Market Baseline / Display-Only"
DISPLAY_ONLY_WARNING = (
    "Display-only DynastyProcess market baseline; not NWR source truth; "
    "not used for model inputs, candidate rank, or hidden sort."
)
FRESH_STATUSES = {
    "GREEN_CURRENT",
    "GREEN_SAME_WEEK_NO_CHANGE",
    "YELLOW_STALE",
    "RED_STALE",
    "YELLOW_FETCH_FAILED_USING_LAST_CACHE",
    "RED_NO_VALID_CACHE",
}
STALE_STATUSES = {
    "YELLOW_STALE",
    "RED_STALE",
    "YELLOW_FETCH_FAILED_USING_LAST_CACHE",
    "RED_NO_VALID_CACHE",
}
FORBIDDEN_INPUT_COLUMNS = {
    "candidate_rank_override",
    "final_rank_override",
    "final_board_rank_override",
    "dynasty_rank_override",
    "model_input",
    "private_model_input",
    "hidden_sort",
    "source_truth_replacement",
}
MARKET_PLAYER_REQUIRED_COLUMNS = {
    "player",
    "pos",
    "dp_market_rank_1qb",
    "dp_value_1qb",
    "join_method",
    "join_confidence",
    "dp_display_only_warning",
    "freshness_status",
}
MARKET_PICK_REQUIRED_COLUMNS = {
    "pick_label",
    "value_1qb",
    "ecr_1qb",
    "freshness_status",
}
FRESHNESS_REQUIRED_COLUMNS = {
    "nwr_fetch_timestamp",
    "upstream_scrape_date",
    "upstream_latest_commit_sha",
    "upstream_latest_commit_timestamp",
    "freshness_status",
}


def load_market_player_context(
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> pd.DataFrame:
    frame = _load_first_existing_csv(artifact_dir, PLAYER_CONTEXT_FILENAMES)
    _require_columns(frame, MARKET_PLAYER_REQUIRED_COLUMNS, "player market context")
    _assert_no_forbidden_columns(frame)
    return _with_display_label(frame)


def load_market_pick_context(
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> pd.DataFrame:
    frame = _load_first_existing_csv(artifact_dir, PICK_CONTEXT_FILENAMES)
    _require_columns(frame, MARKET_PICK_REQUIRED_COLUMNS, "pick market context")
    _assert_no_forbidden_columns(frame)
    return _with_display_label(frame)


def load_market_freshness(
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, str]:
    snapshot = _resolve_generation(artifact_dir)
    frame = _read_csv_bytes(snapshot.payloads[FRESHNESS_FILENAME])
    _require_columns(frame, FRESHNESS_REQUIRED_COLUMNS, "freshness report")
    if frame.empty:
        return {
            "freshness_status": "RED_NO_VALID_CACHE",
            "market_baseline_stale_warning": (
                "Market baseline unavailable: freshness report is empty."
            ),
        }
    row = {column: _text(value) for column, value in frame.iloc[0].to_dict().items()}
    status = row.get("freshness_status", "")
    if status and status not in FRESH_STATUSES:
        row["freshness_status"] = "RED_NO_VALID_CACHE"
        row["market_baseline_stale_warning"] = f"Unknown freshness status: {status}"
    scrape_date = row.get("upstream_scrape_date", "")
    if scrape_date and row.get("freshness_status", "") in {
        "GREEN_CURRENT",
        "GREEN_SAME_WEEK_NO_CHANGE",
    }:
        try:
            age_days = (datetime.now(UTC).date() - datetime.fromisoformat(scrape_date).date()).days
        except ValueError:
            age_days = 0
        if age_days > 7:
            row["freshness_status"] = "YELLOW_STALE"
            row["market_baseline_stale_warning"] = (
                f"Market evidence is {age_days} days old (upstream date {scrape_date}); "
                "display-only context remains available but is not current."
            )
    return row


def join_market_to_players(
    players_df: pd.DataFrame,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> pd.DataFrame:
    """Return a copy of player rows with display-only market context appended."""

    players = players_df.copy()
    players["_market_original_order"] = range(len(players))
    market = load_market_player_context(artifact_dir)

    market_by_id = _market_lookup_by_id(market)
    market_exact = _market_lookup(market, exact=True)
    market_normalized = _market_lookup(market, exact=False)

    rows: list[dict[str, Any]] = []
    for player_row in players.to_dict("records"):
        match = _find_market_match(player_row, market_by_id, market_exact, market_normalized)
        enriched = dict(player_row)
        enriched.update(_market_display_fields(match))
        rows.append(enriched)

    output = pd.DataFrame(rows)
    return output.sort_values("_market_original_order").drop(columns=["_market_original_order"])


def compute_market_sanity_flags(
    players_df: pd.DataFrame,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> pd.DataFrame:
    """Compute display-only NWR-vs-market labels without changing rank/model columns."""

    frame = players_df.copy()
    if "dp_market_rank_1qb" not in frame.columns:
        frame = join_market_to_players(frame, artifact_dir)

    labels: list[str] = []
    gaps: list[float | str] = []
    for row in frame.to_dict("records"):
        label, gap = _market_gap_label(row)
        labels.append(label)
        gaps.append("" if gap is None else gap)

    output = frame.copy()
    output["market_sanity_label"] = labels
    output["market_gap"] = gaps
    output["market_baseline_label"] = DISPLAY_LABEL
    return output


def get_pick_market_value(
    pick_label: str,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, str] | None:
    picks = load_market_pick_context(artifact_dir)
    normalized = _normalize_pick_label(pick_label)
    for row in picks.to_dict("records"):
        if _normalize_pick_label(row.get("pick_label")) == normalized:
            return {key: _text(value) for key, value in row.items()}
    return None


def summarize_market_gap(player_or_row: pd.Series | dict[str, Any]) -> str:
    row = player_or_row.to_dict() if isinstance(player_or_row, pd.Series) else player_or_row
    label, gap = _market_gap_label(row)
    if label == "No market match":
        return "No market match"
    if label == "Market data stale":
        return "Market data stale"
    if gap is None:
        return label
    return f"{label}: NWR rank gap {gap:+.1f} vs DynastyProcess"


def assert_market_data_is_display_only(
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> None:
    issues = validate_market_baseline_registry()
    snapshot = _resolve_generation(artifact_dir)
    for loader_name, names in (
        ("player market context", PLAYER_CONTEXT_FILENAMES),
        ("pick market context", PICK_CONTEXT_FILENAMES),
    ):
        frame = _load_first_existing_csv_from_snapshot(snapshot, names)
        try:
            _assert_no_forbidden_columns(frame)
        except ValueError as exc:
            issues.append(f"{loader_name}: {exc}")
    if issues:
        raise AssertionError("; ".join(issues))


def _load_first_existing_csv(artifact_dir: str | Path, names: tuple[str, ...]) -> pd.DataFrame:
    snapshot = _resolve_generation(artifact_dir)
    return _load_first_existing_csv_from_snapshot(snapshot, names)


def _load_first_existing_csv_from_snapshot(
    snapshot: GenerationSnapshot,
    names: tuple[str, ...],
) -> pd.DataFrame:
    for name in names:
        body = snapshot.payloads.get(name)
        if body is not None:
            return _read_csv_bytes(body)
    expected = ", ".join(names)
    raise FileNotFoundError(
        f"No market baseline artifact found in generation "
        f"{snapshot.generation_id}: {expected}"
    )


def _resolve_generation(artifact_dir: str | Path) -> GenerationSnapshot:
    root = Path(artifact_dir)
    if root == DEFAULT_ARTIFACT_DIR:
        runtime_root = runtime_artifact_dir()
        if runtime_root.is_dir():
            try:
                return resolve_current_generation(
                    runtime_root,
                    repo_root=REPO_ROOT,
                    trusted_runtime_root=runtime_root,
                )
            except GenerationResolutionError:
                return resolve_legacy_latest_snapshot(
                    runtime_root,
                    repo_root=REPO_ROOT,
                    trusted_runtime_root=runtime_root,
                )
    if (
        root.name != "dynastyprocess_market_baseline"
        or root.parent.name != "refresh_data"
        or root.parent.parent.name != "local_exports"
    ):
        raise ValueError(
            "Market baseline readers require the canonical versioned-generation root."
        )
    repo_root = root.parents[2]
    return resolve_current_generation(root, repo_root=repo_root)


def _read_csv_bytes(body: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(body), dtype=str, keep_default_na=False)


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _assert_no_forbidden_columns(frame: pd.DataFrame) -> None:
    columns = {column.lower() for column in frame.columns}
    forbidden = sorted(FORBIDDEN_INPUT_COLUMNS & columns)
    if forbidden:
        raise ValueError(f"Market baseline contains forbidden input columns: {forbidden}")


def _with_display_label(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["market_baseline_label"] = DISPLAY_LABEL
    return output


def _normalize_name(value: Any) -> str:
    text = _text(value).casefold().strip()
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?$", "", text).strip()
    return re.sub(r"[^a-z0-9]+", "", text)


def _normalize_pos(value: Any) -> str:
    return _text(value).upper().strip()


def _normalize_pick_label(value: Any) -> str:
    text = _text(value).casefold().strip()
    text = text.replace("pick", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        return text[:-2]
    return text


def _float(value: Any) -> float | None:
    text = _text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _first_present(row: dict[str, Any], columns: tuple[str, ...]) -> str:
    for column in columns:
        value = _text(row.get(column))
        if value:
            return value
    return ""


def _rank_basis(row: dict[str, Any]) -> float | None:
    for column in (
        "nwr_candidate_rank",
        "final_board_rank",
        "nwr_final_board_rank",
        "nwr_dynasty_rank",
        "dynasty_rank",
        "nwr_rank",
    ):
        value = _float(row.get(column))
        if value is not None:
            return value
    return None


def _player_name(row: dict[str, Any]) -> str:
    return _first_present(row, ("player", "player_name", "name", "nwr_name"))


def _player_pos(row: dict[str, Any]) -> str:
    return _first_present(row, ("pos", "position", "nwr_pos"))


def _player_ids(row: dict[str, Any]) -> tuple[str, ...]:
    values = (
        row.get("player_id"),
        row.get("nwr_player_id"),
        row.get("sleeper_id"),
        row.get("fp_id"),
    )
    return tuple(_text(value) for value in values if _text(value))


def _market_lookup_by_id(market: pd.DataFrame) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in market.to_dict("records"):
        for column in ("nwr_player_id", "sleeper_id", "fp_id"):
            value = _text(row.get(column))
            if value:
                lookup[value] = row
    return lookup


def _market_lookup(market: pd.DataFrame, *, exact: bool) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for row in market.to_dict("records"):
        name = _text(row.get("nwr_name")) or _text(row.get("player"))
        pos = _text(row.get("nwr_pos")) or _text(row.get("pos"))
        key_name = name.casefold().strip() if exact else _normalize_name(name)
        lookup[(key_name, _normalize_pos(pos))] = row
    return lookup


def _find_market_match(
    player_row: dict[str, Any],
    market_by_id: dict[str, dict[str, Any]],
    market_exact: dict[tuple[str, str], dict[str, Any]],
    market_normalized: dict[tuple[str, str], dict[str, Any]],
) -> dict[str, Any] | None:
    for player_id in _player_ids(player_row):
        if player_id in market_by_id:
            return market_by_id[player_id]

    name = _player_name(player_row)
    pos = _normalize_pos(_player_pos(player_row))
    if not name or not pos:
        return None

    exact_key = (name.casefold().strip(), pos)
    if exact_key in market_exact:
        return market_exact[exact_key]

    normalized_key = (_normalize_name(name), pos)
    return market_normalized.get(normalized_key)


def _market_display_fields(match: dict[str, Any] | None) -> dict[str, Any]:
    if not match:
        return {
            "market_baseline_label": DISPLAY_LABEL,
            "market_sanity_label": "No market match",
            "dp_market_rank_1qb": "",
            "dp_value_1qb": "",
            "dp_ecr_pos": "",
            "dp_age": "",
            "market_join_confidence": "unmatched / manual review",
            "freshness_status": "",
            "market_source_label": "",
            "market_baseline_stale_warning": "",
        }
    return {
        "market_baseline_label": DISPLAY_LABEL,
        "dp_market_player": _text(match.get("player")),
        "dp_market_rank_1qb": _text(match.get("dp_market_rank_1qb")),
        "dp_value_1qb": _text(match.get("dp_value_1qb")),
        "dp_ecr_pos": _text(match.get("ecr_pos")),
        "dp_age": _text(match.get("age")),
        "market_join_method": _text(match.get("join_method")),
        "market_join_confidence": _text(match.get("join_confidence")),
        "freshness_status": _text(match.get("freshness_status")),
        "market_source_label": _text(match.get("source_note")) or "DynastyProcess public data",
        "market_baseline_stale_warning": _text(match.get("market_baseline_stale_warning")),
        "dp_display_only_warning": _text(match.get("dp_display_only_warning"))
        or DISPLAY_ONLY_WARNING,
    }


def _market_gap_label(row: dict[str, Any]) -> tuple[str, float | None]:
    status = _text(row.get("freshness_status"))
    if status in STALE_STATUSES:
        return "Market data stale", None

    market_rank = _float(row.get("dp_market_rank_1qb") or row.get("ecr_1qb"))
    if market_rank is None:
        return "No market match", None

    nwr_rank = _rank_basis(row)
    if nwr_rank is None:
        return "Aligned", None

    gap = round(nwr_rank - market_rank, 1)
    if gap <= -20:
        return "NWR much higher", gap
    if gap >= 20:
        return "NWR much lower", gap
    return "Aligned", gap
