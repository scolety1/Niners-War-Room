from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
STATUS_MATRIX_PATH = (
    REPO_ROOT / "docs" / "hq" / "future_tools" / "future_tools_status_matrix_20260626.csv"
)

ALLOWED_DECISIONS = {
    "SAFE_NOW_DISPLAY_ONLY",
    "SAFE_NOW_FRAMEWORK_ONLY",
    "BLOCKED_NEEDS_DATA",
    "BLOCKED_NEEDS_API",
    "BLOCKED_NEEDS_MODEL_GATE",
    "BLOCKED_NEEDS_HUMAN_APPROVAL",
    "BLOCKED_NEEDS_SOURCE_POLICY",
    "DEFER",
}

REQUIRED_COLUMNS = (
    "tool_id",
    "tool_name",
    "tool_group",
    "decision",
    "status_label",
    "output_type",
    "required_data_summary",
    "nwr_coverage_summary",
    "blocker_next_gate",
    "scaffold_status",
    "active_output_allowed",
    "model_input_allowed",
    "uses_market_or_adp",
    "uses_cfbd_or_nfl_usage",
    "docs_spec",
    "next_step",
    "notes",
)

SAFE_V0_TOOL_IDS = {
    "roster_weakness_tracker",
    "future_pick_planning",
    "upcoming_draft_prep",
    "keeper_deadline_prep",
    "drop_deadline_prep",
    "trade_deadline_prep",
}

NOT_ENOUGH_INFORMATION = "Not enough information"
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DST")
STARTER_FORMAT = {"QB": 1, "RB": 2, "WR": 3, "TE": 1}


@dataclass(frozen=True)
class FutureToolStatus:
    tool_id: str
    tool_name: str
    tool_group: str
    decision: str
    status_label: str
    output_type: str
    required_data_summary: str
    nwr_coverage_summary: str
    blocker_next_gate: str
    scaffold_status: str
    active_output_allowed: str
    model_input_allowed: str
    uses_market_or_adp: str
    uses_cfbd_or_nfl_usage: str
    docs_spec: str
    next_step: str
    notes: str

    @property
    def is_blocked(self) -> bool:
        return self.decision.startswith("BLOCKED") or self.decision == "DEFER"

    @property
    def is_framework_only(self) -> bool:
        return self.decision == "SAFE_NOW_FRAMEWORK_ONLY"

    @property
    def is_safe_v0_candidate(self) -> bool:
        return self.tool_id in SAFE_V0_TOOL_IDS and self.is_framework_only


def load_future_tools_status_matrix(path: Path | None = None) -> list[FutureToolStatus]:
    source = path or STATUS_MATRIX_PATH
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Future Tools status matrix missing columns: {', '.join(missing)}")
        rows = [
            FutureToolStatus(**{column: row.get(column, "") for column in REQUIRED_COLUMNS})
            for row in reader
        ]
    validate_future_tools_statuses(rows)
    return rows


def validate_future_tools_statuses(rows: list[FutureToolStatus]) -> None:
    if not rows:
        raise ValueError("Future Tools status matrix is empty.")
    for row in rows:
        if row.decision not in ALLOWED_DECISIONS:
            raise ValueError(f"{row.tool_id} has unsupported decision {row.decision!r}.")
        if row.active_output_allowed.lower() != "no":
            raise ValueError(f"{row.tool_id} incorrectly allows active output.")
        if row.model_input_allowed.lower() != "no":
            raise ValueError(f"{row.tool_id} incorrectly allows model input.")


def group_future_tools(rows: list[FutureToolStatus]) -> dict[str, list[FutureToolStatus]]:
    grouped: dict[str, list[FutureToolStatus]] = {}
    for row in rows:
        grouped.setdefault(row.tool_group, []).append(row)
    return grouped


def future_tools_summary(rows: list[FutureToolStatus]) -> dict[str, int]:
    return {
        "total_tools": len(rows),
        "blocked": sum(1 for row in rows if row.is_blocked),
        "framework_only": sum(1 for row in rows if row.is_framework_only),
        "safe_v0_candidates": sum(1 for row in rows if row.is_safe_v0_candidate),
        "active_outputs": sum(1 for row in rows if row.active_output_allowed.lower() == "yes"),
        "model_inputs": sum(1 for row in rows if row.model_input_allowed.lower() == "yes"),
    }


def safe_v0_tools(rows: list[FutureToolStatus]) -> list[FutureToolStatus]:
    return [row for row in rows if row.is_safe_v0_candidate]


def blocked_tools(rows: list[FutureToolStatus]) -> list[FutureToolStatus]:
    return [row for row in rows if not row.is_safe_v0_candidate]


def parse_manual_roster_text(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue
        parts = [part.strip() for part in raw.split(",")]
        player = parts[0] if parts else ""
        position = _position(parts[1] if len(parts) > 1 else "")
        rows.append(
            {
                "player": player or NOT_ENOUGH_INFORMATION,
                "position": position or NOT_ENOUGH_INFORMATION,
                "age": parts[2] if len(parts) > 2 and parts[2] else NOT_ENOUGH_INFORMATION,
                "dynasty_rank": (
                    parts[3] if len(parts) > 3 and parts[3] else NOT_ENOUGH_INFORMATION
                ),
                "notes": parts[4] if len(parts) > 4 and parts[4] else "",
                "source": "Manual input / display-only",
            }
        )
    return rows


def roster_position_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts = {position: 0 for position in POSITIONS}
    unknown = 0
    for row in rows:
        position = _position(row.get("position", ""))
        if position in counts:
            counts[position] += 1
        else:
            unknown += 1
    summary = []
    for position in POSITIONS:
        starter_need = STARTER_FORMAT.get(position)
        count = counts[position]
        if starter_need is None:
            coverage = "Display-only count; no starter threshold."
        elif count >= starter_need:
            coverage = "Meets entered starter-count threshold."
        else:
            coverage = "Below entered starter-count threshold; review manually."
        summary.append(
            {
                "position": position,
                "player_count": str(count),
                "starter_threshold": str(starter_need) if starter_need is not None else "",
                "coverage_note": coverage,
                "guardrail": "Display-only roster structure; not a recommendation.",
            }
        )
    if unknown:
        summary.append(
            {
                "position": NOT_ENOUGH_INFORMATION,
                "player_count": str(unknown),
                "starter_threshold": "",
                "coverage_note": "One or more manual rows have missing/unknown position.",
                "guardrail": "Missing position is not treated as depth.",
            }
        )
    return summary


def roster_age_bucket_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    buckets = {
        "Under 25": 0,
        "25 to 29": 0,
        "30+": 0,
        NOT_ENOUGH_INFORMATION: 0,
    }
    for row in rows:
        age = _float(row.get("age"))
        if age is None:
            buckets[NOT_ENOUGH_INFORMATION] += 1
        elif age < 25:
            buckets["Under 25"] += 1
        elif age < 30:
            buckets["25 to 29"] += 1
        else:
            buckets["30+"] += 1
    return [
        {
            "age_bucket": bucket,
            "player_count": str(count),
            "guardrail": "Display-only age structure; missing age stays Not enough information.",
        }
        for bucket, count in buckets.items()
    ]


def roster_dynasty_rank_bucket_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    buckets = {
        "Top 24": 0,
        "25 to 72": 0,
        "73+": 0,
        NOT_ENOUGH_INFORMATION: 0,
    }
    for row in rows:
        rank = _float(row.get("dynasty_rank"))
        if rank is None:
            buckets[NOT_ENOUGH_INFORMATION] += 1
        elif rank <= 24:
            buckets["Top 24"] += 1
        elif rank <= 72:
            buckets["25 to 72"] += 1
        else:
            buckets["73+"] += 1
    return [
        {
            "dynasty_rank_bucket": bucket,
            "player_count": str(count),
            "guardrail": "Display-only rank bucket; does not change Dynasty Rank.",
        }
        for bucket, count in buckets.items()
    ]


def future_pick_ledger_from_runtime_state(state: dict[str, Any]) -> list[dict[str, str]]:
    ledger: list[dict[str, str]] = []
    for trade in state.get("trade_events", []):
        if not isinstance(trade, dict):
            continue
        for asset in trade.get("team_a_assets", []):
            if isinstance(asset, dict) and asset.get("asset_type") == "future_pick":
                ledger.append(_future_pick_row(asset, trade, direction="Sent by Team A"))
        for asset in trade.get("team_b_assets", []):
            if isinstance(asset, dict) and asset.get("asset_type") == "future_pick":
                ledger.append(_future_pick_row(asset, trade, direction="Received by Team A"))
    return ledger


def parse_manual_future_pick_text(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue
        parts = [part.strip() for part in raw.split(",")]
        rows.append(
            {
                "pick_year": parts[0] if parts else NOT_ENOUGH_INFORMATION,
                "pick_round": parts[1] if len(parts) > 1 else NOT_ENOUGH_INFORMATION,
                "direction": parts[2] if len(parts) > 2 else "Manual note",
                "counterparty": parts[3] if len(parts) > 3 else NOT_ENOUGH_INFORMATION,
                "source": "Manual input / display-only",
                "notes": parts[4] if len(parts) > 4 else "",
                "guardrail": "Planning ledger only; no pick valuation.",
            }
        )
    return rows


def parse_manual_table_text(
    text: str,
    columns: tuple[str, ...],
    *,
    source: str,
    guardrail: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue
        parts = [part.strip() for part in raw.split(",")]
        row = {
            column: (
                parts[index]
                if index < len(parts) and parts[index]
                else NOT_ENOUGH_INFORMATION
            )
            for index, column in enumerate(columns)
        }
        row["source"] = source
        row["guardrail"] = guardrail
        rows.append(row)
    return rows


def upcoming_draft_setup_checklist(*, notes: str = "") -> list[dict[str, str]]:
    tasks = (
        "Confirm league settings",
        "Confirm scoring",
        "Confirm draft date/time",
        "Confirm draft order",
        "Confirm owned picks",
        "Confirm traded picks",
        "Confirm keeper/drop deadlines",
        "Confirm available roster spots",
        "Export current prep notes",
    )
    return _manual_checklist_rows(
        tasks,
        notes=notes,
        guardrail="Manual draft setup checklist only; not a recommendation or model output.",
    )


def upcoming_draft_questions_checklist(*, notes: str = "") -> list[dict[str, str]]:
    questions = (
        "Who are my must-know players?",
        "What positions can I ignore?",
        "Which picks are trade candidates?",
        "What players need more evidence?",
        "What roster decisions need human review?",
    )
    return _manual_checklist_rows(
        questions,
        notes=notes,
        guardrail="Manual question list only; not a target plan or player recommendation.",
        task_column="question",
    )


def upcoming_draft_data_readiness_checklist(*, notes: str = "") -> list[dict[str, str]]:
    checks = (
        "Sleeper league state checked",
        "Dynasty Rankings reviewed",
        "Market baseline freshness checked, display-only",
        "CFBD review status checked, review-only",
        "NFL usage status checked, review-only",
        "Protected artifacts verified",
        "Runtime draft state backup/export tested",
    )
    return _manual_checklist_rows(
        checks,
        notes=notes,
        guardrail="Manual readiness checklist only; not a refresh, promotion, or model gate.",
        task_column="check",
    )


def deadline_checklist(
    tool_id: str,
    *,
    date_text: str = "",
    notes: str = "",
) -> list[dict[str, str]]:
    rows_by_tool = {
        "keeper_deadline_prep": (
            "Confirm league keeper deadline",
            "Review protected artifacts remain unchanged",
            "Collect manual keep/cut notes",
            "Export review packet if needed",
        ),
        "drop_deadline_prep": (
            "Confirm league drop deadline",
            "Review roster/status missing data",
            "List players requiring human review",
            "Do not produce automatic drop decisions",
        ),
        "trade_deadline_prep": (
            "Confirm league trade deadline",
            "Review manual trade goals",
            "Audit existing trade/event log",
            "Keep market context display-only",
        ),
    }
    tasks = rows_by_tool.get(tool_id, ())
    return [
        {
            "task": task,
            "status": "Not Started",
            "manual_deadline": date_text or NOT_ENOUGH_INFORMATION,
            "manual_notes": notes,
            "guardrail": "Manual checklist only; not a recommendation or model output.",
        }
        for task in tasks
    ]


def _manual_checklist_rows(
    tasks: tuple[str, ...],
    *,
    notes: str,
    guardrail: str,
    task_column: str = "task",
) -> list[dict[str, str]]:
    return [
        {
            task_column: task,
            "status": "Not Started",
            "manual_notes": notes,
            "guardrail": guardrail,
        }
        for task in tasks
    ]


def _future_pick_row(
    asset: dict[str, Any],
    trade: dict[str, Any],
    *,
    direction: str,
) -> dict[str, str]:
    return {
        "pick_year": str(asset.get("pick_year") or NOT_ENOUGH_INFORMATION),
        "pick_round": str(asset.get("round") or asset.get("pick_label") or NOT_ENOUGH_INFORMATION),
        "direction": direction,
        "counterparty": str(trade.get("team_b") or NOT_ENOUGH_INFORMATION),
        "source": "Live Draft runtime event log / manual",
        "notes": str(trade.get("notes") or ""),
        "guardrail": "Planning ledger only; no pick valuation.",
    }


def _position(value: object) -> str:
    position = str(value or "").strip().upper()
    if position in {"DEF", "D/ST"}:
        return "DST"
    return position


def _float(value: object) -> float | None:
    try:
        text = str(value or "").strip()
        if not text or text == NOT_ENOUGH_INFORMATION:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None
