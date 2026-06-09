from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.models.keeper_scores import KeeperDecision, KeeperScoreInputs
from src.services.command_board_service import (
    ActiveStatsFirstSync,
    _active_stats_first_sync,
    _is_newer_timestamp,
    _latest_model_output_timestamp,
)
from src.services.forced_release_strategy_service import team_release_pressure_profile
from src.services.market_influence_policy_service import (
    first_market_value,
    market_status_warning,
    market_value_status,
    safe_market_edge_score,
)
from src.services.player_lifecycle_service import (
    lifecycle_from_lookup,
    load_active_lifecycle_lookup,
)
from src.services.table_sort_service import SortSpec
from src.services.team_service import build_team_keeper_board
from src.services.warning_language_service import (
    confidence_explanation,
    confidence_label,
    warning_summary,
)

LEAGUE_PRESSURE_SORT = SortSpec(
    table_key="league_pressure",
    label="Forced-release pain descending, then team",
    sort_columns=("forced_release_pain", "release_decision_difficulty", "team"),
    directions=("desc", "desc", "asc"),
    meaning="Teams with the most forced-release pressure appear first.",
)
LEAGUE_DEFAULT_RELEASE_SORT = SortSpec(
    table_key="league_default_release",
    label="Acquisition value descending, then team",
    sort_columns=("acquisition_value", "team"),
    directions=("desc", "asc"),
    meaning="Most interesting likely required top-five release slots appear first.",
)
LEAGUE_TARGET_SORT = SortSpec(
    table_key="league_targets",
    label="Target category, then acquisition value",
    sort_columns=("target_category", "acquisition_value", "market_edge", "player"),
    directions=("custom", "desc", "desc", "asc"),
    meaning=(
        "Targets are grouped by acquisition opportunity; within each category, "
        "higher acquisition value appears first."
    ),
)

LEAGUE_TARGET_CATEGORIES: tuple[str, ...] = (
    "Likely Forced Releases",
    "Cheap Targets",
    "Expensive Targets",
    "Model vs Market Targets",
    "Avoid",
)


@dataclass(frozen=True)
class LeagueIntelBoard:
    snapshot_date: str | None
    pressure_rows: list[dict[str, object]]
    default_release_rows: list[dict[str, object]]
    target_rows: list[dict[str, object]]
    rows_by_category: dict[str, list[dict[str, object]]]
    pressure_levels: list[str]
    target_categories: list[str]
    sort_metadata: dict[str, SortSpec]


def build_league_intel(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
    protect_limit: int = 23,
    official_top_five_keep_limit: int = 4,
) -> LeagueIntelBoard:
    validated = validate_data_pack(data_pack_path)
    active_sync = _active_stats_first_sync()
    all_rows = _joined_player_rows(
        validated.rows_by_table,
        active_sync=active_sync,
        active_preview_is_newer=_is_newer_timestamp(
            active_sync.preview_timestamp,
            _latest_model_output_timestamp(validated),
        ),
    )
    target_team_id = _resolve_team_id(all_rows, team_id)
    rows_by_team = _rows_by_team(all_rows)
    pressure_rows: list[dict[str, object]] = []
    default_release_rows: list[dict[str, object]] = []
    target_rows: list[dict[str, object]] = []

    for team_id, rows in rows_by_team.items():
        team_name = _team_name(rows, team_id)
        pain_profile = team_release_pressure_profile(
            rows,
            official_top_five_keep_limit=official_top_five_keep_limit,
        )
        board = build_team_keeper_board(
            [_keeper_input(row) for row in rows],
            team_id=team_id,
            team_name=team_name,
            protect_limit=protect_limit,
            official_top_five_keep_limit=official_top_five_keep_limit,
        )
        default_release_names = ", ".join(
            _row_player_name(row) for row in pain_profile.default_release_rows
        )
        default_release_value = max(
            (
                _score(row.get("private_score") or row.get("keeper_score"), 0.0)
                for row in pain_profile.default_release_rows
            ),
            default=0.0,
        )
        pressure_rows.append(
            {
                "team_id": team_id,
                "team": team_name,
                "pressure_level": pain_profile.pressure_level.title(),
                "pressure_count": pain_profile.pressure_count,
                "forced_release_count": pain_profile.required_release_count,
                "official_top_five_count": len(pain_profile.top_five_rows),
                "roster_count": board.pressure.roster_count,
                "protect_limit": board.pressure.protect_limit,
                "forced_release_pain": round(pain_profile.forced_release_pain, 2),
                "likely_forced_release": default_release_names,
                "likely_forced_release_value": round(default_release_value, 2),
                "easy_drop_available": pain_profile.easy_drop_available,
                "easy_non_top_five_drop": _row_player_name(pain_profile.easy_drop_row),
                "top_five_value_gap": round(pain_profile.top_five_value_gap, 2),
                "release_decision_difficulty": round(
                    pain_profile.release_decision_difficulty,
                    2,
                ),
                "replacement_depth_count": pain_profile.replacement_depth_count,
                "opportunity_summary": pain_profile.explanation,
            }
        )
        decisions = {decision.player_id: decision for decision in board.decisions}
        if _has_scored_model_outputs(rows):
            forced_release_rows = pain_profile.default_release_rows
            default_release_rows.extend(
                _model_candidate_row(
                    team_name,
                    row,
                    "Likely Forced Release",
                    is_default_release=True,
                    pressure_count=pain_profile.pressure_count,
                    forced_release_count=pain_profile.required_release_count,
                )
                for row in forced_release_rows
            )
        else:
            forced_release_rows = []
            default_release_rows.extend(
                _candidate_row(team_name, player.player_id, decisions, "Likely Forced Release")
                for player in board.forced_release_candidates
            )

        if team_id != target_team_id and _has_scored_model_outputs(rows):
            forced_ids = {str(row.get("player_id") or "") for row in forced_release_rows}
            target_rows.extend(
                _target_row(
                    row,
                    team_name=team_name,
                    is_default_release=str(row.get("player_id") or "") in forced_ids,
                    pressure_count=pain_profile.pressure_count,
                    forced_release_count=pain_profile.required_release_count,
                )
                for row in rows
                if str(row.get("roster_status") or "rostered") == "rostered"
            )
        elif team_id != target_team_id:
            target_rows.extend(
                _legacy_target_row(
                    team_name,
                    decision,
                    pressure_count=pain_profile.pressure_count,
                    forced_release_count=pain_profile.required_release_count,
                )
                for decision in board.decisions
                if decision.player_id in decisions
            )

    pressure_rows = sorted(
        pressure_rows,
        key=lambda row: (
            -float(row.get("forced_release_pain") or 0.0),
            -float(row.get("release_decision_difficulty") or 0.0),
            str(row["team"]),
        ),
    )
    default_release_rows = sorted(
        default_release_rows,
        key=lambda row: (-float(row.get("acquisition_value") or 0.0), str(row["team"])),
    )
    target_rows = sorted(target_rows, key=_target_sort_key)
    rows_by_category = {
        category: [row for row in target_rows if row.get("target_category") == category]
        for category in LEAGUE_TARGET_CATEGORIES
    }
    return LeagueIntelBoard(
        snapshot_date=validated.snapshot_date,
        pressure_rows=pressure_rows,
        default_release_rows=default_release_rows,
        target_rows=target_rows,
        rows_by_category=rows_by_category,
        pressure_levels=_ordered_pressure_levels(
            {str(row["pressure_level"]) for row in pressure_rows}
        ),
        target_categories=[
            category
            for category in LEAGUE_TARGET_CATEGORIES
            if rows_by_category.get(category)
        ],
        sort_metadata={
            "pressure_rows": LEAGUE_PRESSURE_SORT,
            "default_release_rows": LEAGUE_DEFAULT_RELEASE_SORT,
            "target_rows": LEAGUE_TARGET_SORT,
        },
    )


def _joined_player_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
    *,
    active_sync: ActiveStatsFirstSync | None = None,
    active_preview_is_newer: bool = False,
) -> list[dict[str, object]]:
    rankings = _by_player_id(rows_by_table.get("official_rankings", []))
    outputs = _by_player_id(rows_by_table.get("model_outputs", []))
    active_outputs = active_sync.rows_by_sleeper_id if active_sync else {}
    lifecycle_lookup = load_active_lifecycle_lookup()
    rows: list[dict[str, object]] = []
    for roster_row in rows_by_table.get("rosters", []):
        player_id = str(roster_row.get("player_id") or "")
        ranking_row = rankings.get(player_id, {})
        active_output_row = active_outputs.get(player_id)
        output_row = active_output_row or outputs.get(player_id, {})
        row = dict(roster_row)
        row["league_rank"] = _first_present(
            roster_row.get("league_rank"),
            ranking_row.get("league_rank"),
            roster_row.get("official_rank"),
            ranking_row.get("official_rank"),
        )
        row["official_rank"] = row["league_rank"]
        for column in (
            "private_score",
            "market_score",
            "market_trade_value",
            "market_edge_score",
            "market_edge_label",
            "war_score",
            "keeper_score",
            "confidence_score",
            "drop_candidate_score",
            "risk_level",
            "warning_status",
            "warning_reasons",
            "recommendation",
            "experience_bucket",
            "young_nfl_bridge_prior_score",
            "young_nfl_bridge_weight",
            "young_nfl_bridge_source",
            "asset_lifecycle",
            "model_version",
            "computed_at",
            "score_source",
            "identity_match_method",
            "score_source_warning",
            "notes",
        ):
            row[column] = output_row.get(column)
        if not active_output_row:
            row["score_source"] = row.get("score_source") or "data_pack_model_outputs"
            row["identity_match_method"] = row.get("identity_match_method") or "player_id"
            if active_preview_is_newer and output_row:
                row["score_source_warning"] = (
                    "Active stats-first preview is newer, but this player did not "
                    "map through the Sleeper/nflverse identity bridge; showing data-pack "
                    "model output for review."
                )
        rows.append(lifecycle_from_lookup(row, lifecycle_lookup))
    return rows


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _rows_by_team(
    rows: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    rows_by_team: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        team_id = str(row.get("team_id") or "")
        rows_by_team[team_id].append(row)
    return dict(rows_by_team)


def _keeper_input(row: dict[str, object]) -> KeeperScoreInputs:
    formula_value = _optional_float(row.get("keeper_score"))
    if formula_value is None:
        formula_value = _optional_float(row.get("private_score"), 50.0)
    confidence_value = _optional_float(row.get("confidence_score"), 0.0)
    return KeeperScoreInputs(
        player_id=str(row.get("player_id") or ""),
        player_name=str(row.get("player_name") or row.get("player_id") or ""),
        position=str(row.get("position") or ""),
        official_rank=_optional_int(row.get("official_rank")),
        private_score=_optional_float(row.get("private_score"), 50.0),
        market_score=_optional_float(row.get("market_score")),
        confidence_score=_optional_float(row.get("confidence_score"), 0.6),
        roster_status=str(row.get("roster_status") or "rostered"),
        long_term_private_value=_optional_float(
            row.get("long_term_private_value"), formula_value
        ),
        next_2_year_starter_value=_optional_float(
            row.get("next_2_year_starter_value"), formula_value
        ),
        scarcity_bonus=_optional_float(row.get("scarcity_bonus"), formula_value),
        trade_liquidity=_optional_float(row.get("trade_liquidity"), formula_value),
        age_curve=_optional_float(row.get("age_curve"), formula_value),
        risk_adj=_optional_float(row.get("risk_adj"), formula_value),
        build_fit=_optional_float(row.get("build_fit"), formula_value),
        roster_redundancy=_optional_float(row.get("roster_redundancy"), 0.0) or 0.0,
        decline_risk=_optional_float(row.get("decline_risk"), 0.0) or 0.0,
        data_completeness=_optional_float(
            row.get("data_completeness"), confidence_value
        ),
        historical_cohort_size=_optional_float(
            row.get("historical_cohort_size"), confidence_value
        ),
        market_agreement=_optional_float(row.get("market_agreement"), confidence_value),
        model_separation=_optional_float(row.get("model_separation"), confidence_value),
    )


def _team_name(rows: list[dict[str, object]], fallback: str) -> str:
    if not rows:
        return fallback
    return str(rows[0].get("team_name") or fallback)


def _resolve_team_id(rows: list[dict[str, object]], requested_team_id: str) -> str:
    if any(str(row.get("team_id") or "") == requested_team_id for row in rows):
        return requested_team_id
    normalized_request = _normalize_name(requested_team_id)
    for row in rows:
        if _normalize_name(str(row.get("team_name") or "")) == normalized_request:
            return str(row.get("team_id") or "")
    if normalized_request == "niners":
        for row in rows:
            if _normalize_name(str(row.get("team_name") or "")) == "niners":
                return str(row.get("team_id") or "")
    return requested_team_id


def _normalize_name(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _candidate_row(
    team_name: str,
    player_id: str,
    decisions: dict[str, KeeperDecision],
    signal: str,
) -> dict[str, object]:
    decision = decisions[player_id]
    stats_value = round(decision.keeper_score, 2)
    market_value = round(decision.keeper_score, 2)
    market_edge = 0.0
    acquisition_value = _acquisition_value(
        stats_value=stats_value,
        market_value=market_value,
        market_edge=market_edge,
        confidence=_confidence(decision.confidence_score),
        is_default_release=True,
        pressure_count=1,
        forced_release_count=1,
    )
    return {
        "team": team_name,
        "player": decision.player_name,
        "pos": decision.position,
        "signal": signal,
        "availability_signal": signal,
        "target_category": "Likely Forced Releases",
        "league_rank": decision.official_rank,
        "official_rank": decision.official_rank,
        "acquisition_value": round(acquisition_value, 2),
        "stats_value": stats_value,
        "market_value": market_value,
        "market_edge": market_edge,
        "keeper_score": round(decision.keeper_score, 2),
        "drop_score": round(decision.drop_candidate_score, 2),
        "confidence": _confidence(decision.confidence_score),
        "confidence_label": confidence_label(_confidence(decision.confidence_score)),
        "confidence_explanation": confidence_explanation(
            _confidence(decision.confidence_score)
        ),
        "opportunity_reason": (
            "Likely required release from the roster's five highest league-ranked "
            "players."
        ),
    }


def _model_candidate_row(
    team_name: str,
    row: dict[str, object],
    signal: str,
    *,
    is_default_release: bool,
    pressure_count: int,
    forced_release_count: int,
) -> dict[str, object]:
    stats_value = _score(row.get("private_score"))
    market_context = _market_context(row, stats_value)
    market_value = market_context["market_value"]
    market_value_for_math = _score(market_value, stats_value)
    market_edge = _edge_score(market_context["market_edge"])
    confidence = _confidence(row.get("confidence_score"))
    acquisition_value = _acquisition_value(
        stats_value=stats_value,
        market_value=market_value_for_math,
        market_edge=market_edge,
        confidence=confidence,
        is_default_release=is_default_release,
        pressure_count=pressure_count,
        forced_release_count=forced_release_count,
    )
    category = _target_category(
        is_default_release=is_default_release,
        acquisition_value=acquisition_value,
        stats_value=stats_value,
        market_value=market_value_for_math,
        market_edge=market_edge,
        confidence=confidence,
        pressure_count=pressure_count,
        forced_release_count=forced_release_count,
    )
    return {
        "team": team_name,
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "asset_lifecycle": row.get("asset_lifecycle"),
        "asset_lifecycle_label": row.get("asset_lifecycle_label"),
        "signal": signal,
        "availability_signal": signal,
        "target_category": category,
        "league_rank": row.get("league_rank"),
        "official_rank": row.get("league_rank"),
        "acquisition_value": round(acquisition_value, 2),
        "stats_value": round(stats_value, 2),
        "market_value": round(market_value, 2) if market_value is not None else "",
        "market_value_status": market_context["market_value_status"],
        "market_edge": round(market_edge, 2) if market_context["market_edge"] is not None else "",
        "market_edge_warning": market_context["market_edge_warning"],
        "keeper_score": _optional_float(row.get("keeper_score")),
        "drop_score": _optional_float(row.get("drop_candidate_score")),
        "confidence": round(confidence, 2),
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(
            confidence,
            row.get("warning_reasons"),
            market_context["market_edge_warning"],
        ),
        "opportunity_reason": _target_reason(
            is_default_release=is_default_release,
            category=category,
            acquisition_value=acquisition_value,
            market_value=market_value_for_math,
            market_edge=market_edge,
            pressure_count=pressure_count,
            forced_release_count=forced_release_count,
        ),
    }


def _target_row(
    row: dict[str, object],
    *,
    team_name: str,
    is_default_release: bool,
    pressure_count: int,
    forced_release_count: int,
) -> dict[str, object]:
    stats_value = _score(row.get("private_score"))
    market_context = _market_context(row, stats_value)
    market_value = market_context["market_value"]
    market_value_for_math = _score(market_value, stats_value)
    market_edge = _edge_score(market_context["market_edge"])
    confidence = _confidence(row.get("confidence_score"))
    acquisition_value = _acquisition_value(
        stats_value=stats_value,
        market_value=market_value_for_math,
        market_edge=market_edge,
        confidence=confidence,
        is_default_release=is_default_release,
        pressure_count=pressure_count,
        forced_release_count=forced_release_count,
    )
    category = _target_category(
        is_default_release=is_default_release,
        acquisition_value=acquisition_value,
        stats_value=stats_value,
        market_value=market_value_for_math,
        market_edge=market_edge,
        confidence=confidence,
        pressure_count=pressure_count,
        forced_release_count=forced_release_count,
    )
    return {
        "team": team_name,
        "player": row.get("player_name"),
        "pos": row.get("position"),
        "asset_lifecycle": row.get("asset_lifecycle"),
        "asset_lifecycle_label": row.get("asset_lifecycle_label"),
        "target_category": category,
        "availability_signal": "Likely Forced Release"
        if is_default_release
        else _availability_signal(pressure_count),
        "league_rank": row.get("league_rank"),
        "acquisition_value": round(acquisition_value, 2),
        "stats_value": round(stats_value, 2),
        "market_value": round(market_value, 2) if market_value is not None else "",
        "market_value_status": market_context["market_value_status"],
        "market_edge": round(market_edge, 2) if market_context["market_edge"] is not None else "",
        "market_edge_warning": market_context["market_edge_warning"],
        "confidence": round(confidence, 2),
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(
            confidence,
            row.get("warning_reasons"),
            market_context["market_edge_warning"],
        ),
        "pressure_opportunity": _pressure_opportunity_summary(
            team_name=team_name,
            forced_release_count=forced_release_count,
            pressure_count=pressure_count,
        ),
        "opportunity_reason": _target_reason(
            is_default_release=is_default_release,
            category=category,
            acquisition_value=acquisition_value,
            market_value=market_value_for_math,
            market_edge=market_edge,
            pressure_count=pressure_count,
            forced_release_count=forced_release_count,
        ),
        "warning_status": row.get("warning_status") or "",
        "warning_reason": _clean_warning(row.get("warning_reasons")),
    }


def _legacy_target_row(
    team_name: str,
    decision: KeeperDecision,
    *,
    pressure_count: int,
    forced_release_count: int,
) -> dict[str, object]:
    confidence = _confidence(decision.confidence_score)
    stats_value = _score(decision.keeper_score)
    market_value = stats_value
    market_edge = 0.0
    acquisition_value = _acquisition_value(
        stats_value=stats_value,
        market_value=market_value,
        market_edge=market_edge,
        confidence=confidence,
        is_default_release=False,
        pressure_count=pressure_count,
        forced_release_count=forced_release_count,
    )
    category = _target_category(
        is_default_release=False,
        acquisition_value=acquisition_value,
        stats_value=stats_value,
        market_value=market_value,
        market_edge=market_edge,
        confidence=confidence,
        pressure_count=pressure_count,
        forced_release_count=forced_release_count,
    )
    return {
        "team": team_name,
        "player": decision.player_name,
        "pos": decision.position,
        "target_category": category,
        "availability_signal": _availability_signal(pressure_count),
        "league_rank": decision.official_rank,
        "acquisition_value": round(acquisition_value, 2),
        "stats_value": round(stats_value, 2),
        "market_value": round(market_value, 2),
        "market_edge": round(market_edge, 2),
        "confidence": round(confidence, 2),
        "confidence_label": confidence_label(confidence),
        "confidence_explanation": confidence_explanation(
            confidence,
            "review_needed",
        ),
        "pressure_opportunity": _pressure_opportunity_summary(
            team_name=team_name,
            forced_release_count=forced_release_count,
            pressure_count=pressure_count,
        ),
        "opportunity_reason": "Legacy keeper inputs only; review before treating as a target.",
        "warning_status": "review_needed",
        "warning_reason": "Legacy keeper data, no scored model output.",
    }


def _target_category(
    *,
    is_default_release: bool,
    acquisition_value: float,
    stats_value: float,
    market_value: float,
    market_edge: float,
    confidence: float,
    pressure_count: int,
    forced_release_count: int,
) -> str:
    has_rule_pressure = pressure_count > 0 or forced_release_count > 0
    if confidence < 50 or acquisition_value < 48 or market_edge <= -12:
        return "Avoid"
    if is_default_release and has_rule_pressure and acquisition_value >= 58:
        return "Likely Forced Releases"
    if market_edge >= 7 and acquisition_value >= 60:
        return "Model vs Market Targets"
    if has_rule_pressure and market_value <= 72 and acquisition_value >= 58:
        return "Cheap Targets"
    if market_value >= 82 and stats_value >= 72 and confidence >= 60:
        return "Expensive Targets"
    return "Avoid"


def _acquisition_value(
    *,
    stats_value: float,
    market_value: float,
    market_edge: float,
    confidence: float,
    is_default_release: bool,
    pressure_count: int,
    forced_release_count: int,
) -> float:
    availability_bonus = 16.0 if is_default_release else min(8.0, pressure_count * 2.0)
    rule_bonus = min(6.0, forced_release_count * 3.0)
    discount_bonus = max(0.0, market_edge) * 0.35
    cost_drag = max(0.0, market_value - stats_value) * 0.25
    confidence_drag = max(0.0, 65.0 - confidence) * 0.18
    return _clamp(
        (0.68 * stats_value)
        + (0.16 * confidence)
        + discount_bonus
        + availability_bonus
        + rule_bonus
        - cost_drag
        - confidence_drag
    )


def _availability_signal(pressure_count: int) -> str:
    if pressure_count >= 2:
        return "Pressure-created opportunity"
    if pressure_count == 1:
        return "Light pressure watch"
    return "No pressure discount"


def _target_reason(
    *,
    is_default_release: bool,
    category: str,
    acquisition_value: float,
    market_value: float,
    market_edge: float,
    pressure_count: int,
    forced_release_count: int,
) -> str:
    if category == "Avoid":
        if is_default_release:
            return (
                "Likely release, but not a target yet: value, confidence, or market "
                "cost does not justify chasing him."
            )
        return "No realistic acquisition path from pressure, price, confidence, or value."
    if is_default_release:
        return (
            "Actual pressure plus release-candidate logic makes this a real possible "
            "availability spot."
        )
    if category == "Model vs Market Targets":
        return f"Model Value beats Trade Market by {market_edge:.1f}; check source confidence."
    if category == "Cheap Targets":
        return (
            f"Market cost is manageable ({market_value:.1f}) and team pressure can "
            f"create a plausible buy path; acquisition value {acquisition_value:.1f}."
        )
    if category == "Expensive Targets":
        return "Good player, but likely requires a premium. Track, do not assume discount."
    if forced_release_count or pressure_count:
        return "Team pressure creates some negotiating leverage."
    return "Watch only."


def _market_context(row: dict[str, object], stats_value: float) -> dict[str, object]:
    status = market_value_status(row)
    market_value = first_market_value(row)
    edge = safe_market_edge_score(
        stats_value,
        market_value,
        status,
        explicit_edge=row.get("market_edge_score"),
    )
    warning = str(row.get("market_edge_warning") or "")
    status_warning = market_status_warning(status)
    if status_warning != "none":
        warning = status_warning
    return {
        "market_value_status": status,
        "market_value": market_value,
        "market_edge": edge,
        "market_edge_warning": warning,
    }


def _target_sort_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        _target_category_order(str(row.get("target_category") or "")),
        -_score(row.get("acquisition_value"), 0.0),
        -_score(row.get("market_edge"), 0.0),
        str(row.get("player") or ""),
    )


def _target_category_order(category: str) -> int:
    try:
        return LEAGUE_TARGET_CATEGORIES.index(category)
    except ValueError:
        return 99


def _pressure_opportunity_summary(
    *,
    team_name: str,
    forced_release_count: int,
    pressure_count: int,
) -> str:
    if forced_release_count <= 0 and pressure_count <= 0:
        return f"{team_name} has no obvious rule-created opportunity."
    if forced_release_count > 0:
        return (
            f"{team_name} must expose {forced_release_count} player from its "
            "Roster's League-Rank Top Five; that can create target opportunity."
        )
    return f"{team_name} has roster pressure, but no required top-five release slot."


def _visible_top_five_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked_rows = [row for row in rows if _optional_int(row.get("league_rank")) is not None]
    return sorted(
        ranked_rows,
        key=lambda row: (
            _optional_int(row.get("league_rank")) or 999,
            str(row.get("player_name")),
        ),
    )[:5]


def _visible_forced_release_rows(
    top_five_rows: list[dict[str, object]],
    official_top_five_keep_limit: int,
) -> list[dict[str, object]]:
    release_count = max(0, len(top_five_rows) - official_top_five_keep_limit)
    if release_count == 0:
        return []
    return sorted(
        top_five_rows,
        key=lambda row: (
            -(_optional_float(row.get("drop_candidate_score"), 0.0) or 0.0),
            _optional_float(row.get("keeper_score"), 0.0) or 0.0,
            _optional_int(row.get("league_rank")) or 999,
            str(row.get("player_name")),
        ),
    )[:release_count]


def _has_scored_model_outputs(rows: list[dict[str, object]]) -> bool:
    return bool(rows) and all(
        row.get("model_version") and "Neutral placeholder" not in str(row.get("notes") or "")
        for row in rows
    )


def _ordered_pressure_levels(levels: set[str]) -> list[str]:
    order = {"High": 0, "Medium": 1, "Low": 2}
    return sorted(levels, key=lambda level: (order.get(level, 99), level))


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_float(value: object, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    return float(value)


def _score(value: object, default: float = 50.0) -> float:
    if value is None or value == "":
        return default
    return _clamp(float(value))


def _edge_score(value: object, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return _clamp(float(value), -100.0, 100.0)


def _confidence(value: object) -> float:
    score = _score(value, 50.0)
    if 0.0 < score <= 1.0:
        return round(score * 100.0, 2)
    return score


def _market_edge(row: dict[str, object], stats_value: float, market_value: float) -> float:
    explicit = row.get("market_edge_score")
    if explicit is not None and explicit != "":
        return _clamp(float(explicit), -100.0, 100.0)
    return _clamp(stats_value - market_value, -100.0, 100.0)


def _clean_warning(value: object) -> str:
    return warning_summary(value, default="")


def _row_player_name(row: dict[str, object] | None) -> str:
    if not row:
        return ""
    return str(row.get("player_name") or row.get("player") or row.get("player_id") or "")


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))
