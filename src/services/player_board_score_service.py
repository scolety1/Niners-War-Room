from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.data.validators import validate_data_pack
from src.services.full_player_board_value_service import (
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
    FULL_BOARD_SCORE_COLUMN,
    data_needed_messages,
)
from src.services.market_gap_service import build_market_gap_report
from src.services.model_v4_evidence_gate_service import model_v4_evidence_gate
from src.services.model_v4_identity_join_gate_service import (
    IdentityJoinLookup,
    build_identity_join_lookup,
    identity_join_gate,
    normalize_identity_name,
)
from src.services.review_score_envelope_service import (
    MODEL_V4_CURRENT_PLAYER_CHECKPOINT,
    ReviewScoreEnvelope,
    envelope_from_row,
    export_score_disclosure,
    validate_score_envelope,
)

MODEL_V4_CURRENT_PLAYER_ROWS = Path(MODEL_V4_CURRENT_PLAYER_CHECKPOINT.source_path)


def build_player_board_score_rows(
    data_pack_path: str | Path,
    *,
    current_value_path: str | Path | None = None,
    age_lookup: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    resolved_current_value_path = Path(current_value_path or _default_current_value_path())
    validated = validate_data_pack(data_pack_path)
    rows_by_table = validated.rows_by_table
    rosters = _by_player_id(rows_by_table.get("rosters", []))
    rankings = _by_player_id(rows_by_table.get("official_rankings", []))
    market_gap = {
        str(row.get("player_id") or ""): row
        for row in build_market_gap_report(data_pack_path).rows
        if row.get("player_id")
    }
    current_rows = _current_value_lookup(resolved_current_value_path)
    rows: list[dict[str, object]] = []
    for output in rows_by_table.get("model_outputs", []):
        player_id = str(output.get("player_id") or "")
        roster = rosters.get(player_id, {})
        ranking = rankings.get(player_id, {})
        gap = market_gap.get(player_id, {})
        player = str(output.get("player_name") or ranking.get("player_name") or player_id)
        position = str(output.get("position") or ranking.get("position") or "")
        current_key = (normalize_identity_name(player), position.upper())
        current_gate = identity_join_gate(current_key, current_rows)
        current_row = current_rows.rows_by_key.get(current_key)
        current_metadata = current_row or {}
        evidence_gate = model_v4_evidence_gate(current_metadata)
        legacy_env = validate_score_envelope(
            envelope_from_row(
                {
                    **output,
                    "asset_id": player_id,
                    "asset_type": "player",
                    "display_name": player,
                    "source_path": str(Path(data_pack_path) / "model_outputs.csv"),
                    "source_column": "private_score",
                    "score_as_of_date": validated.snapshot_date,
                    "confidence_cap": output.get("confidence_score") or 0.0,
                    "warnings": output.get("warning_reasons", ""),
                    "allowed_use": "legacy_score_comparison_context",
                    "blocked_use": "primary_review_score|default_sort|review_label",
                },
                asset_type="player",
                score_column="private_score",
                source_column="private_score",
            )
        )
        review_env = _current_player_envelope(
            current_row,
            player_id=player_id,
            fallback_name=player,
            snapshot_date=validated.snapshot_date,
            current_value_path=resolved_current_value_path,
            extra_warnings=(*current_gate.warning_flags, *evidence_gate.warning_flags),
        )
        primary_score = review_env.primary_review_score
        manual_required = (
            review_env.manual_decision_required
            or evidence_gate.manual_decision_required
            or primary_score is None
        )
        disclosure = export_score_disclosure(review_env)
        rows.append(
            {
                "overall_rank": "",
                "player": player,
                "age": _display_age((age_lookup or {}).get(_normalize_name(player))),
                "position": position,
                "nfl_team": current_row.get("nfl_team", ranking.get("nfl_team", ""))
                if current_row
                else ranking.get("nfl_team", ""),
                "owner": roster.get("team_name", ""),
                "league_rank": ranking.get("league_rank", roster.get("league_rank", "")),
                "league_rank_normalized_score": gap.get("league_rank_normalized_score", ""),
                "dynasty_startup_adp": gap.get("dynasty_startup_adp", ""),
                "adp_normalized_score": gap.get("adp_normalized_score", ""),
                "private_score": "" if primary_score is None else round(primary_score, 4),
                "primary_review_score": "" if primary_score is None else round(primary_score, 4),
                "legacy_active_pack_score": legacy_env.legacy_active_pack_score or "",
                "score_type": review_env.score_type or "",
                "source_path": review_env.source_path or "",
                "source_column": review_env.source_column or "",
                "model_version": review_env.model_version or "",
                "lineage_class": review_env.lineage_class,
                "score_as_of_date": review_env.score_as_of_date or "",
                "allowed_use": review_env.allowed_use or "",
                "blocked_use": review_env.blocked_use or "",
                "legacy_formula_warning": legacy_env.legacy_formula_warning,
                "stale_or_legacy_formula_warning": legacy_env.stale_or_legacy_formula_warning,
                "market_display_only": False,
                "manual_decision_required": manual_required,
                "identity_uncertain": current_gate.identity_uncertain,
                "stale_team_or_status": evidence_gate.stale_team_or_status,
                "missing_role_evidence": evidence_gate.missing_role_evidence,
                "partial_or_quarantined_contribution": (
                    evidence_gate.partial_or_quarantined_contribution
                ),
                    "model_source_status": (
                        str(current_metadata.get("score_status") or "model_v4_current_player")
                        if primary_score is not None
                        else str(
                            current_metadata.get("score_status")
                            or "manual_required_no_model_v4_current_player"
                        )
                    ),
                    "nwr_trust_status": current_metadata.get("trust_status", ""),
                    "pool_status": current_metadata.get("pool_status", ""),
                    "is_my_team": current_metadata.get("is_my_team", ""),
                    "is_available": current_metadata.get("is_available", ""),
                    "is_rookie": current_metadata.get("is_rookie", ""),
                    "data_needed": (
                        current_metadata.get("data_needed")
                        or " | ".join(data_needed_messages(review_env.warnings))
                    ),
                    "risk_level_source": current_metadata.get("risk_level_source", ""),
                "keeper_score": "",
                "drop_candidate_score": "",
                "veteran_base_value": output.get("veteran_base_value", ""),
                "win_now_value": output.get("win_now_value", ""),
                "dynasty_hold_value": output.get("dynasty_hold_value", ""),
                "horizon_retention_score": output.get("horizon_retention_score", ""),
                "trade_value": output.get("trade_value", ""),
                "market_trade_value": output.get("market_trade_value", ""),
                "market_edge_score": "",
                "war_score": output.get("war_score", ""),
                "pick_adjusted_value": output.get("pick_adjusted_value", ""),
                "confidence_score": review_env.confidence_cap or "",
                "confidence_cap": review_env.confidence_cap or "",
                "risk_level": output.get("risk_level", ""),
                "recommendation": output.get("recommendation", ""),
                "review_label": (
                    "Manual decision required"
                    if manual_required
                    else "Model v4 current-player review"
                ),
                "confidence_status": _confidence_status(review_env),
                "top_warning_group": _top_warning_group(review_env.warnings),
                "market_gap_signal": "",
                "manual_review_notes": _plain_warning_summary(review_env.warnings),
                "warning_reasons": "|".join(review_env.warnings),
                "score_disclosure": disclosure,
            }
        )
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            0 if _sort_score(row.get("primary_review_score")) >= 0 else 1,
            -_sort_score(row.get("primary_review_score")),
            _rank_sort(row.get("league_rank")),
            _rank_sort(row.get("dynasty_startup_adp")),
            str(row.get("player") or "").lower(),
        ),
    )
    private_rank = 1
    for row in sorted_rows:
        if _sort_score(row.get("primary_review_score")) >= 0:
            row["overall_rank"] = private_rank
            private_rank += 1
        else:
            row["overall_rank"] = ""
    return sorted_rows


def _current_player_envelope(
    row: dict[str, str] | None,
    *,
    player_id: str,
    fallback_name: str,
    snapshot_date: str | None,
    current_value_path: Path,
    extra_warnings: tuple[str, ...] = (),
) -> ReviewScoreEnvelope:
    score_column = _current_score_column(row, current_value_path=current_value_path)
    source_path = str(current_value_path)
    if not row:
        return validate_score_envelope(
            ReviewScoreEnvelope(
                asset_id=player_id,
                asset_type="player",
                display_name=fallback_name,
                primary_review_score=None,
                source_path=source_path,
                source_column=score_column,
                model_version=None,
                lineage_class="unknown",
                score_type=MODEL_V4_CURRENT_PLAYER_CHECKPOINT.score_type,
                score_as_of_date=snapshot_date,
                confidence_cap=None,
                warnings=("missing_model_v4_current_player_row", *extra_warnings),
                legacy_formula_warning=False,
                stale_or_legacy_formula_warning=False,
                market_display_only=False,
                manual_decision_required=True,
                allowed_use="manual_review_only_missing_current_player_score",
                blocked_use="primary_review_score",
            )
        )
    return validate_score_envelope(
        envelope_from_row(
            {
                **row,
                "asset_id": player_id,
                "asset_type": "player",
                "display_name": row.get("player_name", fallback_name),
                "source_path": source_path,
                "source_column": score_column,
                "model_version": row.get("checkpoint_version") or row.get("model_version"),
                "score_as_of_date": snapshot_date,
                "warnings": _join_warnings(row.get("warning_flags", ""), extra_warnings),
            },
            asset_type="player",
            score_column=score_column,
            source_column=score_column,
            source_path=source_path,
            score_type=score_column,
        )
    )


def _default_current_value_path() -> Path:
    if DEFAULT_FULL_PLAYER_BOARD_ROWS.exists():
        return DEFAULT_FULL_PLAYER_BOARD_ROWS
    return MODEL_V4_CURRENT_PLAYER_ROWS


def _current_score_column(row: dict[str, str] | None, *, current_value_path: Path) -> str:
    if row and FULL_BOARD_SCORE_COLUMN in row:
        return FULL_BOARD_SCORE_COLUMN
    if current_value_path.name == DEFAULT_FULL_PLAYER_BOARD_ROWS.name:
        return FULL_BOARD_SCORE_COLUMN
    return MODEL_V4_CURRENT_PLAYER_CHECKPOINT.source_column


def _current_value_lookup(path: Path) -> IdentityJoinLookup:
    rows: list[dict[str, str]] = []
    if not path.exists():
        return build_identity_join_lookup(rows, source_name=str(path))
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
    return build_identity_join_lookup(rows, source_name=str(path))


def _by_player_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _confidence_status(env: ReviewScoreEnvelope) -> str:
    if env.manual_decision_required:
        return "Manual decision required"
    if env.confidence_cap is None:
        return "Trust unknown"
    return f"Confidence cap {env.confidence_cap}"


def _plain_warning_summary(warnings: tuple[str, ...]) -> str:
    if not warnings:
        return "No warnings"
    friendly = [warning.replace("_", " ").replace("/", " / ") for warning in warnings[:3]]
    if len(warnings) > 3:
        friendly.append(f"{len(warnings) - 3} more")
    return "; ".join(friendly)


def _top_warning_group(warnings: tuple[str, ...]) -> str:
    text = "|".join(warnings)
    if not text:
        return "No major warning"
    if "missing_" in text or "partial_or_quarantined" in text:
        return "Data incomplete"
    if "identity_review" in text or "quarantined" in text:
        return "Identity/source review"
    if "team_mismatch" in text:
        return "Team/source review"
    return "Review warning"


def _display_age(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "Age missing"
    try:
        return f"{float(text):.1f}"
    except ValueError:
        return text


def _sort_score(value: object) -> float:
    try:
        if value in ("", None):
            return -1.0
        return float(value)
    except (TypeError, ValueError):
        return -1.0


def _rank_sort(value: object) -> float:
    try:
        text = str(value or "").strip()
        if not text:
            return 999999.0
        return float(text)
    except (TypeError, ValueError):
        return 999999.0


def _normalize_name(value: object) -> str:
    return normalize_identity_name(value)


def _join_warnings(value: object, extra_warnings: tuple[str, ...]) -> str:
    warnings = [part.strip() for part in str(value or "").split("|") if part.strip()]
    for warning in extra_warnings:
        if warning not in warnings:
            warnings.append(warning)
    return "|".join(warnings)
