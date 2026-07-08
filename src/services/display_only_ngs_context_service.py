from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKET_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "display_only_ngs_devlab_datahealth_v1_20260707"
)
PLAYER_CONTEXT_ARTIFACT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
    / "nflverse_player_context_display_artifact.csv"
)
V2_FEATURE_PANEL_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "advanced_metrics_hardening_v2_backtest_20260707"
    / "advanced_metrics_v2_joined_feature_panel_review_only.csv"
)

NGS_GATE = "REVIEW_ONLY_NGS_CONTEXT"
NOT_ENOUGH_INFORMATION = "Not enough information"
UNAVAILABLE_THRESHOLDED = "Unavailable/thresholded"
NOT_APPLICABLE_FOR_POSITION = "Not applicable for position"
REVIEW_ONLY_WARNING = (
    "Display-only context. Not used in rankings. Not a model score. "
    "NGS public thresholds may exclude low-volume players."
)


def development_lab_ngs_rows() -> list[dict[str, str]]:
    rows = _read_csv(PACKET_DIR / "display_only_ngs_development_lab_fields.csv")
    return [
        {
            "Position": row["position_scope"],
            "Metric": row["display_label"],
            "Display mode": row["display_mode"],
            "Direction": row["directionality"],
            "Gate": row["gate"],
            "Tooltip": row["tooltip"],
            "Missingness caveat": row["missingness_caveat"],
        }
        for row in rows
        if row.get("gate") == NGS_GATE
    ]


def data_health_ngs_rows() -> list[dict[str, str]]:
    rows = _read_csv(PACKET_DIR / "display_only_ngs_data_health_fields.csv")
    return [
        {
            "Source family": row["source_family"],
            "Seasons": row["seasons_available"],
            "Source rows": row["source_rows"],
            "Unique players": row["unique_players"],
            "Safe display count": row["safe_display_count"],
            "Identity-review count": row["identity_review_count"],
            "Blocked count": row["blocked_count"],
            "Gate": row["gate"],
            "Caveat": row["public_threshold_caveat"],
        }
        for row in rows
        if row.get("gate") == NGS_GATE
    ]


def blocked_ngs_metric_rows() -> list[dict[str, str]]:
    rows = _read_csv(PACKET_DIR / "display_only_ngs_blocked_metrics_scan.csv")
    return [
        {
            "Metric or source": row["metric_or_source"],
            "Status": row["blocked_status"],
            "Runtime included": row["runtime_included"],
            "Reason": row["reason"],
        }
        for row in rows
    ]


def ngs_gate_validation_rows() -> list[dict[str, str]]:
    return _read_csv(PACKET_DIR / "display_only_ngs_gate_validation.csv")


def player_compare_ngs_rows(
    records: list[dict[str, object]],
    *,
    player_context_path: Path = PLAYER_CONTEXT_ARTIFACT_PATH,
    feature_panel_path: Path = V2_FEATURE_PANEL_PATH,
) -> list[dict[str, str]]:
    """Build side-by-side NGS context using only safe NWR player ID -> GSIS joins."""

    selected = [_selected_player_context(row) for row in records]
    if not selected:
        return []

    safe_gsis_by_nwr_id = _safe_gsis_by_nwr_id(player_context_path)
    features_by_gsis = _features_by_gsis(feature_panel_path)
    fields = [
        row
        for row in _read_csv(PACKET_DIR / "display_only_ngs_development_lab_fields.csv")
        if row.get("gate") == NGS_GATE
        and any(
            _position_applies(context["position"], row["position_scope"])
            for context in selected
        )
    ]
    player_labels = _unique_player_labels(selected)
    rows: list[dict[str, str]] = []
    for field in fields:
        output = {
            "Metric": field["display_label"],
            "Position scope": field["position_scope"],
            "Gate": NGS_GATE,
            "Tooltip": field["tooltip"],
            "Missingness caveat": field["missingness_caveat"],
        }
        for context, label in zip(selected, player_labels, strict=True):
            value, season = _player_metric_value(
                context,
                field,
                safe_gsis_by_nwr_id=safe_gsis_by_nwr_id,
                features_by_gsis=features_by_gsis,
            )
            output[label] = value
            output[f"{label} season"] = season
        rows.append(output)
    return rows


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {str(key): str(value or "") for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def _selected_player_context(row: dict[str, object]) -> dict[str, str]:
    return {
        "player": _clean(row.get("player")) or NOT_ENOUGH_INFORMATION,
        "position": _clean(row.get("position")).upper(),
        "player_id": _clean(row.get("player_id")),
    }


def _safe_gsis_by_nwr_id(path: Path) -> dict[str, str]:
    rows = _read_csv(path)
    safe: dict[str, str] = {}
    for row in rows:
        nwr_player_id = _clean(row.get("nwr_player_id"))
        gsis_id = _clean(row.get("nflverse_gsis_id"))
        identity_status = _clean(row.get("identity_join_status"))
        review_required = _clean(row.get("review_required")).lower()
        if (
            nwr_player_id
            and gsis_id
            and identity_status == "SAFE_NOW_DISPLAY_ONLY"
            and review_required == "false"
        ):
            safe[nwr_player_id] = gsis_id
    return safe


def _features_by_gsis(path: Path) -> dict[str, list[dict[str, str]]]:
    by_gsis: dict[str, list[dict[str, str]]] = {}
    for row in _read_csv(path):
        gsis_id = _clean(row.get("player_id_gsis"))
        if gsis_id:
            by_gsis.setdefault(gsis_id, []).append(row)
    for rows in by_gsis.values():
        rows.sort(key=lambda item: _safe_int(item.get("feature_season")), reverse=True)
    return by_gsis


def _player_metric_value(
    context: dict[str, str],
    field: dict[str, str],
    *,
    safe_gsis_by_nwr_id: dict[str, str],
    features_by_gsis: dict[str, list[dict[str, str]]],
) -> tuple[str, str]:
    position = context["position"]
    if not _position_applies(position, field["position_scope"]):
        return NOT_APPLICABLE_FOR_POSITION, NOT_ENOUGH_INFORMATION
    gsis_id = safe_gsis_by_nwr_id.get(context["player_id"])
    if not gsis_id:
        return UNAVAILABLE_THRESHOLDED, NOT_ENOUGH_INFORMATION
    feature_row = _latest_feature_row(
        features_by_gsis.get(gsis_id, []),
        position=position,
        metric_column=_feature_column(position, field["raw_source_column"]),
    )
    if not feature_row:
        return UNAVAILABLE_THRESHOLDED, NOT_ENOUGH_INFORMATION
    metric_value = _clean(feature_row.get(_feature_column(position, field["raw_source_column"])))
    if not metric_value:
        return (
            UNAVAILABLE_THRESHOLDED,
            _clean(feature_row.get("feature_season")) or NOT_ENOUGH_INFORMATION,
        )
    return metric_value, _clean(feature_row.get("feature_season")) or NOT_ENOUGH_INFORMATION


def _latest_feature_row(
    rows: list[dict[str, str]],
    *,
    position: str,
    metric_column: str,
) -> dict[str, str]:
    for row in rows:
        if _clean(row.get("position")).upper() == position and _clean(row.get(metric_column)):
            return row
    for row in rows:
        if _clean(row.get("position")).upper() == position:
            return row
    return {}


def _feature_column(position: str, raw_source_column: str) -> str:
    if position == "QB":
        return f"ngs_passing__{raw_source_column}"
    if position == "RB":
        return f"ngs_rushing__{raw_source_column}"
    if position in {"WR", "TE"}:
        return f"ngs_receiving__{raw_source_column}"
    return raw_source_column


def _position_applies(position: str, position_scope: str) -> bool:
    if position_scope == "WR/TE":
        return position in {"WR", "TE"}
    return position == position_scope


def _unique_player_labels(selected: list[dict[str, str]]) -> list[str]:
    labels: list[str] = []
    seen: dict[str, int] = {}
    for context in selected:
        base = context["player"] or NOT_ENOUGH_INFORMATION
        seen[base] = seen.get(base, 0) + 1
        labels.append(base if seen[base] == 1 else f"{base} #{seen[base]}")
    return labels


def _clean(value: object) -> str:
    text = str(value if value is not None else "").strip()
    if text.lower() in {"nan", "none", "null", "n/a", "<na>"}:
        return ""
    return text


def _safe_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0
