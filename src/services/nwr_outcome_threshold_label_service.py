from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from src.services.nwr_outcome_internal_model_package_service import BASE_ALLOWED_FEATURES
from src.services.nwr_outcome_scoring_service import FINISH_BANDS, MODELED_POSITIONS
from src.services.nwr_outcome_training_row_service import FORBIDDEN_FEATURE_FRAGMENTS

DIRECT_THRESHOLD_LABEL_VERSION = "nwr_direct_threshold_labels_v1"
CURRENT_FEATURE_COVERAGE_VERSION = "nwr_2026_prediction_feature_coverage_v1"

REQUIRED_2026_FEATURES = tuple(
    feature for feature in BASE_ALLOWED_FEATURES if feature != "position"
)


def direct_threshold_targets() -> tuple[str, ...]:
    return tuple(
        _target_name(position, threshold)
        for position in MODELED_POSITIONS
        for threshold in FINISH_BANDS[position]
    )


def direct_threshold_label_schema_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for position in MODELED_POSITIONS:
        for threshold in FINISH_BANDS[position]:
            rows.append(
                {
                    "target": _target_name(position, threshold),
                    "position": position,
                    "threshold": f"T{threshold}",
                    "applicability": "position_specific",
                    "rank_basis": "best_of_position_season_total_rank_or_qualified_ppg_rank",
                    "source_fields": "season_total_rank_pos|qualified_ppg_rank_pos",
                    "scoring_basis": "reconstructed_nwr_scoring_components",
                    "tie_policy": "competition_rank_with_deterministic_name_tiebreak_for_order",
                    "non_applicable_value": "null",
                    "label_version": DIRECT_THRESHOLD_LABEL_VERSION,
                    "notes": "Legal historical label only; not a prediction feature.",
                }
            )
    return rows


def direct_threshold_labels_for_row(row: Mapping[str, Any]) -> dict[str, bool | None]:
    position = str(row.get("position") or row.get("fantasy_position") or "").upper()
    best_rank = _best_rank(
        _optional_int(row.get("season_total_rank_pos")),
        _optional_int(row.get("qualified_ppg_rank_pos")),
    )
    labels: dict[str, bool | None] = {}
    for target_position in MODELED_POSITIONS:
        for threshold in FINISH_BANDS[target_position]:
            target = _target_name(target_position, threshold)
            if position != target_position or best_rank is None:
                labels[target] = None if position != target_position else False
            else:
                labels[target] = best_rank <= threshold
    return labels


def threshold_label_legality_audit_rows() -> list[dict[str, str]]:
    return [
        {
            "audit": "rank_source",
            "status": "pass",
            "details": "Labels use position-specific ranks from reconstructed NWR scoring.",
        },
        {
            "audit": "source_fields",
            "status": "pass",
            "details": "Only season_total_rank_pos and qualified_ppg_rank_pos are label inputs.",
        },
        {
            "audit": "public_fantasy_totals",
            "status": "pass",
            "details": "Imported public fantasy total fields are not label inputs.",
        },
        {
            "audit": "non_applicable_thresholds",
            "status": "pass",
            "details": "Non-position thresholds are null/not_applicable, not false labels.",
        },
        {
            "audit": "prediction_feature_leakage",
            "status": "pass",
            "details": "Threshold labels are outcomes only and are not emitted as features.",
        },
    ]


def direct_threshold_support_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[bool]] = defaultdict(list)
    for row in rows:
        season = str(row.get("season") or "")
        position = str(row.get("position") or row.get("fantasy_position") or "").upper()
        labels = direct_threshold_labels_for_row(row)
        for threshold in FINISH_BANDS.get(position, ()):
            target = _target_name(position, threshold)
            value = labels[target]
            if value is not None:
                grouped[(season, position, threshold)].append(value)

    output: list[dict[str, Any]] = []
    for (season, position, threshold), values in sorted(grouped.items()):
        events = sum(1 for value in values if value)
        non_events = len(values) - events
        one_class = events == 0 or non_events == 0
        sparse = events < 20 or non_events < 20
        output.append(
            {
                "target": _target_name(position, threshold),
                "season": season,
                "position": position,
                "threshold": f"T{threshold}",
                "eligible_rows": len(values),
                "events": events,
                "non_events": non_events,
                "event_rate": round(events / len(values), 6) if values else "",
                "one_class_flag": "yes" if one_class else "no",
                "sparse_flag": "yes" if sparse else "no",
                "release_model_feasibility": "blocked_sparse_or_one_class"
                if one_class or sparse
                else "candidate_internal_training",
            }
        )
    return output


def current_2026_feature_source_inventory_rows() -> list[dict[str, str]]:
    return [
        {
            "source_family": "current_app_player_pool",
            "status": "available_sample_only",
            "allowed_for_features": "no",
            "notes": "Identifies rows for coverage audit; does not provide prediction features.",
        },
        {
            "source_family": "completed_prior_season_stats",
            "status": "missing_in_current_clone",
            "allowed_for_features": "yes_when_available_and_cutoff_legal",
            "notes": "Required for veteran 2026 prediction feature snapshots.",
        },
        {
            "source_family": "rookie_prior_features",
            "status": "separate_model_required",
            "allowed_for_features": "not_for_veteran_prior_season_head",
            "notes": "Do not force veteran prior-season schema onto rookies.",
        },
        {
            "source_family": "public_market_projection_rank_sources",
            "status": "blocked",
            "allowed_for_features": "no",
            "notes": (
                "ADP, rankings, projections, market/trade, and outlook/value sources "
                "are forbidden."
            ),
        },
    ]


def current_2026_prediction_feature_coverage_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    return [_coverage_row(row) for row in rows]


def rookie_feature_blocker_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for row in rows:
        if _is_rookie(row):
            blockers.append(
                {
                    "player": str(row.get("player") or row.get("player_name") or ""),
                    "position": str(row.get("position") or "").upper(),
                    "blocker": "rookie_requires_separate_head",
                    "notes": (
                        "Veteran prior-completed-season features are not forced onto "
                        "rookie rows."
                    ),
                }
            )
    return blockers


def monotonicity_readiness_plan_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for position in MODELED_POSITIONS:
        chain = " <= ".join(f"T{threshold}" for threshold in FINISH_BANDS[position])
        rows.append(
            {
                "position": position,
                "threshold_chain": chain,
                "non_applicable_policy": "exclude_non_position_thresholds",
                "check_timing": "after_player_level_threshold_probabilities_exist",
                "repair_method_if_needed": (
                    "pool_adjacent_thresholds_or_apply_cumulative_minmax_internal_only"
                ),
                "repair_applied_now": "no",
                "release_block_if_fails": "yes",
            }
        )
    return rows


def blocked_threshold_probability_unblocker_rows() -> list[dict[str, str]]:
    return [
        {
            "blocker": "historical_threshold_support_export",
            "status": "blocked_until_rebuilt_or_restored",
            "next_action": "Run direct threshold labels on full 2020-2024 historical ranked rows.",
        },
        {
            "blocker": "legal_2026_feature_snapshots",
            "status": "blocked_in_current_clone",
            "next_action": "Create veteran prior-season feature snapshots with renamed schema.",
        },
        {
            "blocker": "rookie_threshold_head",
            "status": "separate_model_required",
            "next_action": (
                "Define rookie-specific legal feature schema before rookie probabilities."
            ),
        },
        {
            "blocker": "player_level_monotonicity",
            "status": "not_ready_no_probabilities",
            "next_action": "Run only after internal threshold model predictions exist.",
        },
    ]


def _coverage_row(row: Mapping[str, Any]) -> dict[str, str]:
    player = str(row.get("player") or row.get("player_name") or "")
    position = str(row.get("position") or row.get("fantasy_position") or "").upper()
    if position in {"K", "PK"}:
        status = "not_applicable_kicker"
    elif _is_rookie(row):
        status = "blocked_rookie_requires_separate_head"
    else:
        forbidden = _forbidden_feature_hits(row)
        old_names = _old_ambiguous_feature_hits(row)
        missing = [feature for feature in REQUIRED_2026_FEATURES if _missing(row.get(feature))]
        if _missing_identity(row):
            status = "blocked_missing_identity"
        elif forbidden:
            status = "blocked_forbidden_feature"
        elif old_names:
            status = "blocked_old_ambiguous_feature_schema"
        elif missing:
            status = "blocked_missing_prior_season_features"
        else:
            status = "ready_internal_feature_row"

    return {
        "player": player,
        "position": position,
        "is_rookie": "yes" if _is_rookie(row) else "no",
        "is_kicker": "yes" if position in {"K", "PK"} else "no",
        "legal_2026_prediction_features": "yes"
        if status == "ready_internal_feature_row"
        else "no",
        "coverage_status": status,
        "missing_required_features": "|".join(
            feature for feature in REQUIRED_2026_FEATURES if _missing(row.get(feature))
        ),
        "forbidden_feature_hits": "|".join(_forbidden_feature_hits(row)),
        "old_ambiguous_feature_hits": "|".join(_old_ambiguous_feature_hits(row)),
        "notes": _coverage_notes(status),
    }


def _coverage_notes(status: str) -> str:
    notes = {
        "not_applicable_kicker": "K rows do not receive threshold probability features.",
        "blocked_rookie_requires_separate_head": (
            "Rookie row requires a separate rookie model/head."
        ),
        "blocked_forbidden_feature": "Forbidden feature/source field found.",
        "blocked_old_ambiguous_feature_schema": "Old ambiguous Sprint 5R pre-rename feature found.",
        "blocked_missing_identity": (
            "Current row identity is not clean enough for prediction features."
        ),
        "blocked_missing_prior_season_features": (
            "Required legal prior-season features are missing."
        ),
        "ready_internal_feature_row": (
            "Row has renamed legal prior-season features for internal modeling."
        ),
    }
    return notes[status]


def _target_name(position: str, threshold: int) -> str:
    return f"same_year_{position.lower()}_t{threshold}"


def _best_rank(*ranks: int | None) -> int | None:
    available = [rank for rank in ranks if rank is not None]
    return min(available) if available else None


def _optional_int(value: object) -> int | None:
    try:
        text = str(value or "").strip()
        return int(float(text)) if text else None
    except (TypeError, ValueError):
        return None


def _missing(value: object) -> bool:
    text = str(value or "").strip()
    return not text or text.lower() in {"nan", "none", "null", "n/a"}


def _is_rookie(row: Mapping[str, Any]) -> bool:
    value = str(row.get("is_rookie") or row.get("rookie_flag") or "").strip().lower()
    return value in {"1", "true", "yes", "rookie"}


def _missing_identity(row: Mapping[str, Any]) -> bool:
    warnings = str(row.get("warning_reasons") or row.get("warning_flags") or "").lower()
    if (
        "unmatched_identity_join_key" in warnings
        or "missing_model_v4_current_player_row" in warnings
    ):
        return True
    return _missing(row.get("player_id")) and _missing(row.get("canonical_player_key"))


def _forbidden_feature_hits(row: Mapping[str, Any]) -> tuple[str, ...]:
    hits: list[str] = []
    for field in row:
        normalized = str(field).lower()
        for fragment in FORBIDDEN_FEATURE_FRAGMENTS:
            if fragment in normalized and fragment not in hits:
                hits.append(fragment)
    return tuple(hits)


def _old_ambiguous_feature_hits(row: Mapping[str, Any]) -> tuple[str, ...]:
    old_names = (
        "prior_nwr_ppg",
        "prior_nwr_finish_rank",
        "prior_games",
        "prior_games_played",
        "prior_games_active",
        "prior_rushing_first_downs",
        "prior_receiving_first_downs",
        "prior_receptions",
        "prior_rushing_yards",
        "prior_receiving_yards",
        "prior_passing_yards",
    )
    return tuple(name for name in old_names if name in row)
