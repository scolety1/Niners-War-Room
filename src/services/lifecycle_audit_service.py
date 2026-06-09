from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.services.draft_service import build_draft_room
from src.services.player_feature_receipts_service import (
    DEFAULT_RECEIPT_VETERAN_MODEL_DIR,
    build_player_feature_receipts,
)
from src.services.player_lifecycle_service import (
    ESTABLISHED_VETERAN,
    FREE_AGENT,
    INCOMING_ROOKIE,
    RELEASED_VETERAN,
    YEAR_ONE_NFL_BRIDGE,
    YEAR_THREE_NFL_BRIDGE,
    YEAR_TWO_NFL_BRIDGE,
    YOUNG_NFL_BRIDGE,
    asset_lifecycle_label,
    is_young_nfl_bridge_lifecycle,
)

BRIDGE_RECEIPT_FEATURES = {
    "draft_capital_prior_score",
    "young_nfl_bridge_decay_weight",
    "young_nfl_bridge_nfl_evidence_weight",
    "young_nfl_bridge_prior",
}


@dataclass(frozen=True)
class LifecycleAuditReport:
    count_rows: list[dict[str, object]]
    player_rows: list[dict[str, object]]
    suspicious_rows: list[dict[str, object]]
    issues: list[str]

    @property
    def has_blockers(self) -> bool:
        return any(row["severity"] == "blocking" for row in self.suspicious_rows)


def build_lifecycle_audit(
    data_pack_path: str | Path,
    *,
    veteran_model_dir: str | Path | None = None,
) -> LifecycleAuditReport:
    source_root = (
        Path(veteran_model_dir) if veteran_model_dir else DEFAULT_RECEIPT_VETERAN_MODEL_DIR
    )
    issues: list[str] = []
    try:
        draft_board = build_draft_room(data_pack_path)
    except (OSError, ValueError) as exc:
        draft_board = None
        issues.append(f"Draft pool lifecycle audit could not run: {exc}")
    receipt_report = build_player_feature_receipts(data_pack_path, veteran_model_dir=source_root)
    issues.extend(receipt_report.issues)

    player_rows: list[dict[str, object]] = []
    player_rows.extend(_receipt_player_rows(receipt_report.rows))
    if draft_board is not None:
        player_rows.extend(_draft_pool_player_rows(draft_board.combined_rows))

    suspicious_rows = _suspicious_rows(player_rows)
    return LifecycleAuditReport(
        count_rows=_count_rows(player_rows),
        player_rows=sorted(
            player_rows,
            key=lambda row: (
                str(row["source_area"]),
                str(row["asset_lifecycle_label"]),
                str(row["position"]),
                str(row["player"]),
            ),
        ),
        suspicious_rows=sorted(
            suspicious_rows,
            key=lambda row: (
                _severity_sort(str(row["severity"])),
                str(row["warning_type"]),
                str(row["player"]),
            ),
        ),
        issues=issues,
    )


def _receipt_player_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for row in rows:
        player = str(row.get("player") or "")
        position = str(row.get("position") or "")
        if not player:
            continue
        grouped.setdefault((player, position, str(row.get("team") or "")), []).append(row)

    player_rows: list[dict[str, object]] = []
    for (player, position, team), grouped_rows in grouped.items():
        first = grouped_rows[0]
        lifecycle = _lifecycle_from_row(first)
        feature_names = {str(row.get("formula_feature_name") or "") for row in grouped_rows}
        sections = {str(row.get("receipt_section_label") or "") for row in grouped_rows}
        warning_reasons = sorted(
            {
                str(row.get("warning_reason") or row.get("warning_status") or "")
                for row in grouped_rows
                if str(row.get("warning_reason") or row.get("warning_status") or "")
            }
        )
        draft_prior_rows = [
            row
            for row in grouped_rows
            if str(row.get("formula_feature_name") or "") in BRIDGE_RECEIPT_FEATURES
            and (
                _float(row.get("feature_weight")) > 0
                or abs(_float(row.get("contribution"))) > 0.0001
            )
        ]
        player_rows.append(
            {
                "source_area": "model_receipts",
                "player": player,
                "position": position,
                "team": team,
                "asset_lifecycle": lifecycle,
                "asset_lifecycle_label": asset_lifecycle_label(lifecycle),
                "asset_type": "",
                "warning": "; ".join(warning_reasons),
                "has_bridge_prior_receipts": _has_bridge_receipts(
                    feature_names,
                    sections,
                    grouped_rows,
                ),
                "has_draft_capital_prior_scored": bool(draft_prior_rows),
                "receipt_hint": f"Open Model Lab > Receipts and select {player}.",
            }
        )
    return player_rows


def _draft_pool_player_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    player_rows: list[dict[str, object]] = []
    for row in rows:
        player = str(row.get("player") or "")
        if not player:
            continue
        lifecycle = str(row.get("asset_lifecycle") or "")
        lifecycle_label = str(row.get("asset_lifecycle_label") or "")
        player_rows.append(
            {
                "source_area": "draft_pool",
                "player": player,
                "position": row.get("position", ""),
                "team": row.get("team", ""),
                "asset_lifecycle": lifecycle,
                "asset_lifecycle_label": lifecycle_label
                or (asset_lifecycle_label(lifecycle) if lifecycle else ""),
                "asset_type": row.get("asset_type", ""),
                "warning": row.get("warning") or row.get("warning_status") or "",
                "has_bridge_prior_receipts": "",
                "has_draft_capital_prior_scored": "",
                "receipt_hint": f"Open Rankings or Draft Board and inspect {player}.",
            }
        )
    return player_rows


def _suspicious_rows(player_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in player_rows:
        lifecycle = str(row.get("asset_lifecycle") or "")
        source_area = str(row.get("source_area") or "")
        if source_area == "model_receipts" and lifecycle == INCOMING_ROOKIE:
            rows.append(
                _suspicious_row(
                    row,
                    warning_type="incoming_rookie_on_veteran_board",
                    severity="blocking",
                    warning=(
                        "Incoming rookie has veteran/model receipts. Current rookies "
                        "should route through the rookie model."
                    ),
                    next_action="Move this player to rookie model/draftable inputs.",
                )
            )
        if (
            source_area == "model_receipts"
            and is_young_nfl_bridge_lifecycle(lifecycle)
            and not bool(row.get("has_bridge_prior_receipts"))
        ):
            rows.append(
                _suspicious_row(
                    row,
                    warning_type="young_nfl_player_missing_bridge_prior",
                    severity="blocking",
                    warning=(
                        "Young NFL bridge player does not show draft/prospect prior, "
                        "decay weight, NFL evidence weight, and bridge contribution receipts."
                    ),
                    next_action="Regenerate stats-first receipts with young bridge prior rows.",
                )
            )
        if (
            source_area == "model_receipts"
            and lifecycle == ESTABLISHED_VETERAN
            and bool(row.get("has_draft_capital_prior_scored"))
        ):
            rows.append(
                _suspicious_row(
                    row,
                    warning_type="established_veteran_with_draft_capital_prior",
                    severity="blocking",
                    warning=(
                        "Established veteran still has scored draft-capital/young-bridge "
                        "prior rows."
                    ),
                    next_action="Remove draft-capital prior from established veteran scoring.",
                )
            )
        if source_area == "draft_pool" and not lifecycle:
            rows.append(
                _suspicious_row(
                    row,
                    warning_type="draftable_player_missing_asset_lifecycle",
                    severity="blocking",
                    warning="Draftable player is missing an asset lifecycle label.",
                    next_action="Regenerate draftable pool with lifecycle fields.",
                )
            )
    return rows


def _suspicious_row(
    row: dict[str, object],
    *,
    warning_type: str,
    severity: str,
    warning: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "warning_type": warning_type,
        "severity": severity,
        "player": row.get("player", ""),
        "position": row.get("position", ""),
        "team": row.get("team", ""),
        "source_area": row.get("source_area", ""),
        "asset_type": row.get("asset_type", ""),
        "asset_lifecycle": row.get("asset_lifecycle", ""),
        "asset_lifecycle_label": row.get("asset_lifecycle_label", ""),
        "warning": warning,
        "next_action": next_action,
        "receipt_hint": row.get("receipt_hint", ""),
    }


def _count_rows(player_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = {}
    for row in player_rows:
        lifecycle = str(row.get("asset_lifecycle") or "missing")
        label = (
            str(row.get("asset_lifecycle_label") or "")
            or (asset_lifecycle_label(lifecycle) if lifecycle != "missing" else "Missing")
        )
        counts[(lifecycle, label)] = counts.get((lifecycle, label), 0) + 1
    ordered_lifecycles = [
        INCOMING_ROOKIE,
        YEAR_ONE_NFL_BRIDGE,
        YEAR_TWO_NFL_BRIDGE,
        YEAR_THREE_NFL_BRIDGE,
        YOUNG_NFL_BRIDGE,
        ESTABLISHED_VETERAN,
        RELEASED_VETERAN,
        FREE_AGENT,
        "missing",
    ]
    return [
        {
            "asset_lifecycle": lifecycle,
            "asset_lifecycle_label": label,
            "players": counts[(lifecycle, label)],
        }
        for lifecycle, label in sorted(
            counts,
            key=lambda item: (
                ordered_lifecycles.index(item[0])
                if item[0] in ordered_lifecycles
                else len(ordered_lifecycles),
                item[1],
            ),
        )
    ]


def _has_bridge_receipts(
    feature_names: set[str],
    sections: set[str],
    rows: list[dict[str, object]],
) -> bool:
    explanations = " ".join(str(row.get("lifecycle_explanation") or "") for row in rows)
    return (
        BRIDGE_RECEIPT_FEATURES.issubset(feature_names)
        and "Young-Player Bridge Prior" in sections
        and "young NFL bridge asset" in explanations
    )


def _lifecycle_from_row(row: dict[str, object]) -> str:
    lifecycle = str(row.get("asset_lifecycle") or "")
    if lifecycle:
        return lifecycle
    label = str(row.get("asset_lifecycle_label") or "")
    for candidate in (
        INCOMING_ROOKIE,
        YEAR_ONE_NFL_BRIDGE,
        YEAR_TWO_NFL_BRIDGE,
        YEAR_THREE_NFL_BRIDGE,
        YOUNG_NFL_BRIDGE,
        ESTABLISHED_VETERAN,
        RELEASED_VETERAN,
        FREE_AGENT,
    ):
        if label == asset_lifecycle_label(candidate):
            return candidate
    return ""


def _severity_sort(value: str) -> int:
    return {"blocking": 0, "review": 1, "info": 2}.get(value, 9)


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default
