from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

NOT_ENOUGH_INFORMATION = "Not enough information"
SAFE_NOW_DISPLAY_ONLY = "SAFE_NOW_DISPLAY_ONLY"
NEED_IDENTITY_REVIEW = "NEED_IDENTITY_REVIEW"
DISPLAY_GUARDRAIL = (
    "Display-only context | Manual review only | No valuation calculated | "
    "No automatic recommendation"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTEXT_DIR = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
)
DEFAULT_CONTEXT_ARTIFACT = DEFAULT_CONTEXT_DIR / "nflverse_player_context_display_artifact.csv"
DEFAULT_SCHEMA_MANIFEST = DEFAULT_CONTEXT_DIR / "nflverse_player_context_schema_manifest.csv"

IDENTITY_FIELDS = (
    ("nwr_player_name", "Player name"),
    ("nwr_player_id", "NWR player ID"),
    ("nflverse_gsis_id", "NFLVerse / GSIS ID"),
    ("nflverse_sleeper_id", "Sleeper ID"),
    ("nflverse_player_name", "NFLVerse player name"),
    ("nflverse_position", "NFLVerse position"),
    ("nflverse_team", "NFLVerse team"),
    ("identity_join_status", "Identity join status"),
    ("identity_caveat", "Identity caveat"),
)
AVAILABILITY_FIELDS = (
    ("roster_status", "Roster status"),
    ("weekly_roster_status", "Weekly roster status"),
    ("injury_report_status", "Injury report status"),
    ("practice_status", "Practice status"),
    ("injury_report_date_week", "Report week/date"),
)
ROLE_FIELDS = (
    ("depth_chart_position", "Depth chart position"),
    ("depth_chart_rank", "Depth chart rank"),
    ("depth_chart_role", "Depth chart role"),
    ("snap_count_recency", "Snap count recency"),
    ("latest_snap_season", "Latest snap season"),
    ("latest_snap_week", "Latest snap week"),
    ("snap_sample_size", "Snap sample size"),
)
PRODUCTION_FIELDS = (
    ("last_active_season", "Last active season"),
    ("last_active_week", "Last active week"),
)
DRAFT_FIELDS = (
    ("draft_year", "NFL draft year"),
    ("draft_round", "NFL draft round"),
    ("draft_pick", "NFL draft pick"),
    ("drafted_team", "Drafted team"),
)
CONTRACT_FIELDS = (("contract_context", "Contract context"),)
SCHEDULE_FIELDS = (
    ("next_game_context", "Next game"),
    ("opponent_context", "Opponent"),
    ("bye_context", "Bye"),
)
CONTEXT_GROUPS = (
    ("Identity Context", IDENTITY_FIELDS),
    ("Availability Context", AVAILABILITY_FIELDS),
    ("Role Context", ROLE_FIELDS),
    ("Production / Activity Context", PRODUCTION_FIELDS),
    ("Draft Context", DRAFT_FIELDS),
    ("Contract Context", CONTRACT_FIELDS),
)
ALL_DISPLAY_FIELDS = {
    field
    for _group, fields in (*CONTEXT_GROUPS, ("Schedule Context", SCHEDULE_FIELDS))
    for field, _label in fields
}


@dataclass(frozen=True)
class TradingLabNflverseContextIndex:
    artifact_rows: tuple[dict[str, str], ...]
    schema_safe_fields: frozenset[str]
    safe_by_nwr_player_id: dict[str, dict[str, str]]
    row_by_nwr_player_id: dict[str, dict[str, str]]
    visible_identity_index: dict[tuple[str, str, str, str], dict[str, str]]
    source_path: Path
    schema_path: Path

    @property
    def artifact_row_count(self) -> int:
        return len(self.artifact_rows)

    @property
    def safe_row_count(self) -> int:
        return len(self.safe_by_nwr_player_id)

    @property
    def identity_review_row_count(self) -> int:
        return sum(
            1
            for row in self.artifact_rows
            if _clean(row.get("identity_join_status")) == NEED_IDENTITY_REVIEW
        )


@dataclass(frozen=True)
class TradingLabNflverseContextResult:
    status: str
    item_label: str
    row: dict[str, str] | None
    reason: str
    join_basis: str
    show_details: bool


def load_trading_lab_nflverse_context_index(
    *,
    artifact_path: Path = DEFAULT_CONTEXT_ARTIFACT,
    schema_path: Path = DEFAULT_SCHEMA_MANIFEST,
) -> TradingLabNflverseContextIndex:
    rows = tuple(_read_csv(artifact_path))
    schema_rows = tuple(_read_csv(schema_path))
    safe_fields = frozenset(
        _clean(row.get("column_name"))
        for row in schema_rows
        if _schema_row_is_safe(row)
    )
    safe_by_id: dict[str, dict[str, str]] = {}
    row_by_id: dict[str, dict[str, str]] = {}
    visible_rows: dict[tuple[str, str, str, str], dict[str, str]] = {}
    visible_counts: dict[tuple[str, str, str, str], int] = {}
    for row in rows:
        nwr_player_id = _clean(row.get("nwr_player_id"))
        if _usable(nwr_player_id):
            row_by_id[nwr_player_id] = row
            if _row_is_safe(row):
                safe_by_id[nwr_player_id] = row
        visible_key = _artifact_visible_key(row)
        if visible_key:
            visible_counts[visible_key] = visible_counts.get(visible_key, 0) + 1
            visible_rows[visible_key] = row
    unique_visible_rows = {
        key: row for key, row in visible_rows.items() if visible_counts.get(key) == 1
    }
    return TradingLabNflverseContextIndex(
        artifact_rows=rows,
        schema_safe_fields=safe_fields,
        safe_by_nwr_player_id=safe_by_id,
        row_by_nwr_player_id=row_by_id,
        visible_identity_index=unique_visible_rows,
        source_path=artifact_path,
        schema_path=schema_path,
    )


def resolve_nflverse_context_for_item(
    item: dict[str, object],
    index: TradingLabNflverseContextIndex,
) -> TradingLabNflverseContextResult:
    label = _clean(item.get("label")) or NOT_ENOUGH_INFORMATION
    if _clean(item.get("asset_type")) != "Player":
        return TradingLabNflverseContextResult(
            status="Pick asset raw label only",
            item_label=label,
            row=None,
            reason="Pick/context assets do not receive NFLVerse player context.",
            join_basis="not_player_asset",
            show_details=False,
        )
    nwr_player_id = _clean(item.get("nwr_player_id"))
    if _usable(nwr_player_id):
        row = index.safe_by_nwr_player_id.get(nwr_player_id)
        if row:
            return _safe_result(label, row, "nwr_player_id")
        row = index.row_by_nwr_player_id.get(nwr_player_id)
        if row:
            return _review_result(label, row, "nwr_player_id")
    visible_key = _item_visible_key(item)
    if visible_key:
        row = index.visible_identity_index.get(visible_key)
        if row and _row_is_safe(row):
            return _safe_result(label, row, "artifact_visible_row_resolved_to_nwr_player_id")
        if row:
            return _review_result(label, row, "artifact_visible_identity_status")
    return TradingLabNflverseContextResult(
        status=NOT_ENOUGH_INFORMATION,
        item_label=label,
        row=None,
        reason="No approved NWR player ID is available for this selected player asset.",
        join_basis="nwr_player_id_missing",
        show_details=False,
    )


def nflverse_context_summary_rows(
    selected_items: pd.DataFrame,
    index: TradingLabNflverseContextIndex,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in _item_records(selected_items):
        result = resolve_nflverse_context_for_item(item, index)
        rows.append(
            {
                "Side": _clean(item.get("side")) or NOT_ENOUGH_INFORMATION,
                "Asset": result.item_label,
                "NFLVerse context status": result.status,
                "Join basis": result.join_basis,
                "Reason": result.reason,
                "Guardrail": DISPLAY_GUARDRAIL,
            }
        )
    return rows


def nflverse_context_detail_rows(
    selected_items: pd.DataFrame,
    index: TradingLabNflverseContextIndex,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in _item_records(selected_items):
        result = resolve_nflverse_context_for_item(item, index)
        if not result.row:
            continue
        if not result.show_details:
            rows.append(_identity_review_detail_row(item, result))
            continue
        for group, fields in CONTEXT_GROUPS:
            for field, label in fields:
                if field not in index.schema_safe_fields:
                    continue
                rows.append(
                    _detail_row(
                        item=item,
                        result=result,
                        group=group,
                        label=label,
                        value=_safe_value(result.row.get(field)),
                    )
                )
    return rows


def nflverse_missing_evidence_rows(
    selected_items: pd.DataFrame,
    index: TradingLabNflverseContextIndex,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in _item_records(selected_items):
        result = resolve_nflverse_context_for_item(item, index)
        if not result.row:
            rows.append(
                _missing_row(
                    item=item,
                    block="NFLVerse player context",
                    reason=result.reason,
                    status=result.status,
                )
            )
            continue
        if not result.show_details:
            rows.append(
                _missing_row(
                    item=item,
                    block="NFLVerse player context",
                    reason="Identity review required; details hidden.",
                    status=result.status,
                )
            )
            continue
        for block, fields in (
            ("Availability Context", AVAILABILITY_FIELDS),
            ("Role Context", ROLE_FIELDS),
            ("Production / Activity Context", PRODUCTION_FIELDS),
            ("Draft Context", DRAFT_FIELDS),
            ("Contract Context", CONTRACT_FIELDS),
        ):
            missing = [
                label
                for field, label in fields
                if _safe_value(result.row.get(field)) == NOT_ENOUGH_INFORMATION
            ]
            if missing:
                rows.append(
                    _missing_row(
                        item=item,
                        block=block,
                        reason=", ".join(missing),
                        status="Missing fields display as Not enough information",
                    )
                )
        rows.append(
            _missing_row(
                item=item,
                block="Schedule / next game / opponent / bye",
                reason="No current/future safe schedule rows are approved for Trading Lab.",
                status=NOT_ENOUGH_INFORMATION,
            )
        )
    return rows


def nflverse_manual_row_context_rows(
    planner_rows: list[dict[str, str]],
    index: TradingLabNflverseContextIndex,
) -> list[dict[str, str]]:
    selected_items = pd.DataFrame(
        [
            {
                "side": row.get("scenario_name", "Manual planner row"),
                "asset_type": "Player",
                "label": row.get("anchor_pick_or_asset") or row.get("scenario_name", ""),
                "nwr_player_id": row.get("nwr_player_id", ""),
                "player": row.get("anchor_pick_or_asset", ""),
                "position": "",
                "nfl_team": "",
                "final_board_rank": "",
            }
            for row in planner_rows
            if _usable(row.get("nwr_player_id"))
        ]
    )
    return nflverse_context_detail_rows(selected_items, index) if not selected_items.empty else []


def display_nflverse_context_rows(rows: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows).fillna(NOT_ENOUGH_INFORMATION).astype(str)


def _safe_result(
    label: str,
    row: dict[str, str],
    join_basis: str,
) -> TradingLabNflverseContextResult:
    return TradingLabNflverseContextResult(
        status=SAFE_NOW_DISPLAY_ONLY,
        item_label=label,
        row=row,
        reason="Approved safe display row; details are display-only.",
        join_basis=join_basis,
        show_details=True,
    )


def _review_result(
    label: str,
    row: dict[str, str],
    join_basis: str,
) -> TradingLabNflverseContextResult:
    identity_status = _clean(row.get("identity_join_status")) or NOT_ENOUGH_INFORMATION
    return TradingLabNflverseContextResult(
        status=identity_status,
        item_label=label,
        row=row,
        reason=_safe_value(row.get("identity_caveat")),
        join_basis=join_basis,
        show_details=False,
    )


def _identity_review_detail_row(
    item: dict[str, object],
    result: TradingLabNflverseContextResult,
) -> dict[str, str]:
    row = result.row or {}
    return {
        "Side": _clean(item.get("side")) or NOT_ENOUGH_INFORMATION,
        "Asset": result.item_label,
        "Context Group": "Identity Context",
        "Field": "Identity review status",
        "Value": _safe_value(row.get("identity_join_status")),
        "Source / As Of": _safe_value(row.get("per_field_dataset_source")),
        "Freshness": _safe_value(row.get("per_field_freshness_source_status")),
        "Guardrail": "Identity review required; player context details hidden.",
    }


def _detail_row(
    *,
    item: dict[str, object],
    result: TradingLabNflverseContextResult,
    group: str,
    label: str,
    value: str,
) -> dict[str, str]:
    row = result.row or {}
    return {
        "Side": _clean(item.get("side")) or NOT_ENOUGH_INFORMATION,
        "Asset": result.item_label,
        "Context Group": group,
        "Field": label,
        "Value": value,
        "Source / As Of": _safe_value(row.get("per_field_dataset_source")),
        "Freshness": _safe_value(row.get("per_field_freshness_source_status")),
        "Guardrail": DISPLAY_GUARDRAIL,
    }


def _missing_row(
    *,
    item: dict[str, object],
    block: str,
    reason: str,
    status: str,
) -> dict[str, str]:
    return {
        "Side": _clean(item.get("side")) or NOT_ENOUGH_INFORMATION,
        "Asset": _clean(item.get("label")) or NOT_ENOUGH_INFORMATION,
        "Context Block": block,
        "Missing / Deferred": reason or NOT_ENOUGH_INFORMATION,
        "Status": status or NOT_ENOUGH_INFORMATION,
        "Guardrail": (
            "Missing is not zero, neutral, safe, clean, healthy, no-role, no-usage, "
            "or favorable."
        ),
    }


def _schema_row_is_safe(row: dict[str, str]) -> bool:
    return (
        _clean(row.get("field_status")) == SAFE_NOW_DISPLAY_ONLY
        and _clean(row.get("display_only")).lower() == "true"
        and _clean(row.get("model_use_allowed")).lower() == "false"
        and _clean(row.get("training_allowed")).lower() == "false"
        and _clean(row.get("source_truth_allowed")).lower() == "false"
        and _clean(row.get("rank_logic_allowed")).lower() == "false"
        and _clean(row.get("hidden_sort_allowed")).lower() == "false"
        and _clean(row.get("trade_value_allowed")).lower() == "false"
        and _clean(row.get("pick_value_allowed")).lower() == "false"
    )


def _row_is_safe(row: dict[str, str]) -> bool:
    return (
        _clean(row.get("identity_join_status")) == SAFE_NOW_DISPLAY_ONLY
        and _clean(row.get("review_required")).lower() == "false"
        and _clean(row.get("display_only")).lower() == "true"
        and _clean(row.get("model_use_allowed")).lower() == "false"
        and _clean(row.get("source_truth_allowed")).lower() == "false"
        and _clean(row.get("rank_logic_allowed")).lower() == "false"
        and _clean(row.get("hidden_sort_allowed")).lower() == "false"
        and _clean(row.get("trade_value_allowed")).lower() == "false"
        and _clean(row.get("pick_value_allowed")).lower() == "false"
        and _usable(row.get("nwr_player_id"))
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {key: _clean(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def _item_records(frame: pd.DataFrame) -> list[dict[str, object]]:
    if frame.empty:
        return []
    return frame.fillna("").to_dict("records")


def _artifact_visible_key(row: dict[str, str]) -> tuple[str, str, str, str] | None:
    rank = _clean(row.get("final_board_rank"))
    name = _normalize(row.get("nwr_player_name"))
    position = _normalize(row.get("nwr_position"))
    team = _normalize(row.get("nwr_team"))
    if not all((_usable(rank), name, position, team)):
        return None
    return rank, name, position, team


def _item_visible_key(item: dict[str, object]) -> tuple[str, str, str, str] | None:
    rank = _clean(item.get("final_board_rank"))
    name = _normalize(item.get("player"))
    position = _normalize(item.get("position"))
    team = _normalize(item.get("nfl_team"))
    if not all((_usable(rank), name, position, team)):
        return None
    return rank, name, position, team


def _safe_value(value: object) -> str:
    text = _clean(value)
    if not _usable(text):
        return NOT_ENOUGH_INFORMATION
    if text.startswith(("NEED_", "BLOCKED_")) or text == "Review needed":
        return NOT_ENOUGH_INFORMATION
    return text


def _usable(value: object) -> bool:
    text = _clean(value)
    return text not in {"", "nan", "none", "null", "n/a", NOT_ENOUGH_INFORMATION}


def _clean(value: object) -> str:
    return str(value or "").strip()


def _normalize(value: object) -> str:
    return " ".join(_clean(value).lower().replace(".", "").split())
