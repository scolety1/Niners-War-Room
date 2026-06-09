from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.asset_board_service import build_unified_asset_board

STRATEGY_ACTIONS = {
    "keep",
    "shop",
    "release",
    "reacquire",
    "target opponent release",
    "trade non-forced player",
}


@dataclass(frozen=True)
class ForcedReleaseStrategyBoard:
    snapshot_date: str | None
    has_real_model_outputs: bool
    team_rows: list[dict[str, object]]
    candidate_rows: list[dict[str, object]]
    niners_action_rows: list[dict[str, object]]
    opponent_target_rows: list[dict[str, object]]
    draft_target_rows: list[dict[str, object]]


@dataclass(frozen=True)
class ForcedReleasePressureProfile:
    top_five_rows: list[dict[str, object]]
    default_release_rows: list[dict[str, object]]
    easy_drop_row: dict[str, object] | None
    bubble_rows: list[dict[str, object]]
    required_release_count: int
    forced_release_pain: float
    easy_drop_available: bool
    top_five_value_gap: float
    release_decision_difficulty: float
    replacement_depth_count: int
    pressure_count: int
    pressure_level: str
    explanation: str


def build_forced_release_strategy(
    data_pack_path: str | Path,
    *,
    team_id: str = "niners",
    official_top_five_keep_limit: int = 4,
) -> ForcedReleaseStrategyBoard:
    validated = validate_data_pack(data_pack_path)
    rows = _joined_player_rows(validated.rows_by_table)
    has_real_outputs = _has_real_model_outputs(rows)
    if not has_real_outputs:
        return ForcedReleaseStrategyBoard(
            snapshot_date=validated.snapshot_date,
            has_real_model_outputs=False,
            team_rows=[],
            candidate_rows=[],
            niners_action_rows=[],
            opponent_target_rows=[],
            draft_target_rows=[],
        )

    target_team_id = _resolve_team_id(rows, team_id)
    asset_values = _asset_values(data_pack_path)
    candidate_rows: list[dict[str, object]] = []
    team_rows: list[dict[str, object]] = []

    for current_team_id, team_player_rows in _rows_by_team(rows).items():
        pressure_profile = team_release_pressure_profile(
            team_player_rows,
            official_top_five_keep_limit=official_top_five_keep_limit,
        )
        top_five_rows = pressure_profile.top_five_rows
        required_count = pressure_profile.required_release_count
        default_release_rows = pressure_profile.default_release_rows
        default_ids = {str(row.get("player_id") or "") for row in default_release_rows}
        team_name = _team_name(team_player_rows, current_team_id)
        candidate_rows.extend(
            _candidate_row(
                row,
                team_id=current_team_id,
                team_name=team_name,
                target_team_id=target_team_id,
                is_default_release=str(row.get("player_id") or "") in default_ids,
                required_release_count=required_count,
                asset_value=asset_values.get(str(row.get("player_id") or ""), 50.0),
                pressure_profile=pressure_profile,
            )
            for row in top_five_rows
        )
        team_rows.append(
            _team_strategy_row(
                team_id=current_team_id,
                team_name=team_name,
                pressure_profile=pressure_profile,
            )
        )

    candidate_rows = sorted(
        candidate_rows,
        key=lambda row: (
            str(row["team"]),
            -int(row["is_default_release"]),
            -float(row["forced_release_candidate_score"]),
            int(row["league_rank"] or 999),
        ),
    )
    niners_rows = [
        row
        for row in candidate_rows
        if str(row["team_id"]) == target_team_id
    ]
    opponent_rows = sorted(
        [
            row
            for row in candidate_rows
            if str(row["team_id"]) != target_team_id and bool(row["is_default_release"])
        ],
        key=lambda row: (
            -float(row["opponent_release_target_score"]),
            -float(row["likely_target_value"]),
            str(row["player"]),
        ),
    )
    draft_rows = sorted(
        [
            row
            for row in candidate_rows
            if bool(row["is_default_release"])
            and str(row["draft_action"]) in {"reacquire", "target opponent release"}
        ],
        key=lambda row: (
            -float(row["reacquisition_priority"] or row["opponent_release_target_score"]),
            str(row["player"]),
        ),
    )
    return ForcedReleaseStrategyBoard(
        snapshot_date=validated.snapshot_date,
        has_real_model_outputs=True,
        team_rows=sorted(
            team_rows,
            key=lambda row: (
                -float(row["forced_release_pain"]),
                -float(row["release_decision_difficulty"]),
                str(row["team"]),
            ),
        ),
        candidate_rows=candidate_rows,
        niners_action_rows=niners_rows,
        opponent_target_rows=opponent_rows,
        draft_target_rows=draft_rows,
    )


def _joined_player_rows(
    rows_by_table: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    rankings = _by_player_id(rows_by_table.get("official_rankings", []))
    outputs = _by_player_id(rows_by_table.get("model_outputs", []))
    rows: list[dict[str, object]] = []
    for roster_row in rows_by_table.get("rosters", []):
        if str(roster_row.get("position") or "").upper() == "K":
            continue
        player_id = str(roster_row.get("player_id") or "")
        ranking_row = rankings.get(player_id, {})
        output_row = outputs.get(player_id, {})
        row = dict(roster_row)
        row["league_rank"] = _first_present(
            roster_row.get("league_rank"),
            ranking_row.get("league_rank"),
            roster_row.get("official_rank"),
            ranking_row.get("official_rank"),
        )
        for column in (
            "private_score",
            "market_score",
            "war_score",
            "keeper_score",
            "drop_candidate_score",
            "confidence_score",
            "risk_level",
            "recommendation",
            "notes",
            "model_version",
            "computed_at",
        ):
            row[column] = output_row.get(column)
        rows.append(row)
    return rows


def _candidate_row(
    row: dict[str, object],
    *,
    team_id: str,
    team_name: str,
    target_team_id: str,
    is_default_release: bool,
    required_release_count: int,
    asset_value: float,
    pressure_profile: ForcedReleasePressureProfile,
) -> dict[str, object]:
    player_id = str(row.get("player_id") or "")
    keeper = _score(row.get("keeper_score"))
    drop = _score(row.get("drop_candidate_score"))
    market = _score(row.get("market_score"), keeper)
    confidence = _confidence(row.get("confidence_score"))
    pressure = pressure_profile.forced_release_pain if is_default_release else 0.0
    candidate_score = forced_release_candidate_score(
        keeper_score=keeper,
        drop_score=drop,
        confidence_score=confidence,
    )
    urgency = pre_declaration_trade_urgency(
        keeper_score=keeper,
        market_score=market,
        drop_score=drop,
        confidence_score=confidence,
        is_default_release=is_default_release,
    )
    reacquire = reacquisition_priority(
        likely_target_value=asset_value,
        keeper_score=keeper,
        drop_score=drop,
        is_own_team=team_id == target_team_id,
        is_default_release=is_default_release,
    )
    opponent_target = opponent_release_target_score(
        likely_target_value=asset_value,
        keeper_score=keeper,
        market_score=market,
        drop_score=drop,
        is_opponent=team_id != target_team_id,
        is_default_release=is_default_release,
    )
    action, draft_action = _actions(
        keeper_score=keeper,
        is_own_team=team_id == target_team_id,
        is_default_release=is_default_release,
        trade_urgency=urgency,
        drop_score=drop,
        reacquisition_score=reacquire,
        opponent_target_score=opponent_target,
    )
    own_team = team_id == target_team_id
    strategy_reason = strategy_reason_code(
        action=action,
        draft_action=draft_action,
        is_own_team=own_team,
        is_default_release=is_default_release,
        keeper_score=keeper,
        drop_score=drop,
        trade_urgency=urgency,
        reacquisition_score=reacquire,
        opponent_target_score=opponent_target,
    )
    rule_explanation = _rule_explanation(
        is_default_release=is_default_release,
        required_release_count=required_release_count,
    )
    score_explanation = _score_explanation(
        keeper_score=keeper,
        drop_score=drop,
        trade_urgency=urgency,
        reacquisition_score=reacquire,
        opponent_target_score=opponent_target,
        own_team=own_team,
    )
    next_step = _next_step(
        action=action,
        draft_action=draft_action,
        own_team=own_team,
        is_default_release=is_default_release,
    )
    return {
        "team_id": team_id,
        "team": team_name,
        "player_id": player_id,
        "player": row.get("player_name") or player_id,
        "pos": row.get("position"),
        "league_rank": _optional_int(row.get("league_rank")),
        "rule_requirement": "must_release_top_five"
        if is_default_release
        else "top_five_rule_candidate",
        "required_release_count": required_release_count,
        "is_default_release": is_default_release,
        "keeper_score": round(keeper, 1),
        "drop_score": round(drop, 1),
        "confidence": round(confidence, 1),
        "forced_release_pressure_score": round(pressure, 1),
        "forced_release_pain": round(pressure_profile.forced_release_pain, 1),
        "easy_drop_available": pressure_profile.easy_drop_available,
        "easy_non_top_five_drop": _row_player_name(pressure_profile.easy_drop_row),
        "top_five_value_gap": round(pressure_profile.top_five_value_gap, 1),
        "release_decision_difficulty": round(
            pressure_profile.release_decision_difficulty,
            1,
        ),
        "replacement_depth_count": pressure_profile.replacement_depth_count,
        "forced_release_candidate_score": round(candidate_score, 1),
        "trade_urgency": round(urgency, 1),
        "likely_target_value": round(asset_value, 1),
        "reacquisition_priority": round(reacquire, 1),
        "opponent_release_target_score": round(opponent_target, 1),
        "action": action,
        "draft_action": draft_action,
        "action_label": _action_label(action, draft_action),
        "strategy_reason": strategy_reason,
        "rule_explanation": rule_explanation,
        "score_explanation": score_explanation,
        "next_step": next_step,
        "explanation": _explanation(
            row,
            is_default_release=is_default_release,
            action=action,
            draft_action=draft_action,
            strategy_reason=strategy_reason,
        ),
    }


def _team_strategy_row(
    *,
    team_id: str,
    team_name: str,
    pressure_profile: ForcedReleasePressureProfile,
) -> dict[str, object]:
    default_release_rows = pressure_profile.default_release_rows
    required_release_count = pressure_profile.required_release_count
    trade_urgency = max(
        [
            pre_declaration_trade_urgency(
                keeper_score=_score(row.get("keeper_score")),
                market_score=_score(row.get("market_score"), _score(row.get("keeper_score"))),
                drop_score=_score(row.get("drop_candidate_score")),
                confidence_score=_confidence(row.get("confidence_score")),
                is_default_release=True,
            )
            for row in default_release_rows
        ],
        default=0.0,
    )
    return {
        "team_id": team_id,
        "team": team_name,
        "league_rank_top_five": len(pressure_profile.top_five_rows),
        "required_release_count": required_release_count,
        "default_release": ", ".join(
            str(row.get("player_name") or row.get("player_id") or "")
            for row in default_release_rows
        ),
        "forced_release_pressure_score": round(pressure_profile.forced_release_pain, 1),
        "forced_release_pain": round(pressure_profile.forced_release_pain, 1),
        "easy_drop_available": pressure_profile.easy_drop_available,
        "easy_non_top_five_drop": _row_player_name(pressure_profile.easy_drop_row),
        "top_five_value_gap": round(pressure_profile.top_five_value_gap, 1),
        "release_decision_difficulty": round(
            pressure_profile.release_decision_difficulty,
            1,
        ),
        "replacement_depth_count": pressure_profile.replacement_depth_count,
        "pressure_count": pressure_profile.pressure_count,
        "trade_urgency": round(trade_urgency, 1),
        "pressure_level": pressure_profile.pressure_level,
        "decision_status": _team_decision_status(required_release_count, trade_urgency),
        "team_explanation": pressure_profile.explanation,
    }


def forced_release_pressure_score(
    *,
    required_release_count: int,
    keeper_score: float,
    market_score: float,
    drop_score: float,
    confidence_score: float,
    is_default_release: bool,
    easy_drop_value: float | None = None,
    top_five_value_gap: float | None = None,
    release_decision_difficulty: float | None = None,
    replacement_depth_count: int = 0,
) -> float:
    if required_release_count <= 0:
        return 0.0
    if not is_default_release:
        return 0.0
    _ = market_score, confidence_score
    inferred_gap = (
        top_five_value_gap
        if top_five_value_gap is not None
        else max(
            0.0,
            keeper_score
            - (easy_drop_value if easy_drop_value is not None else keeper_score),
        )
    )
    difficulty = (
        release_decision_difficulty
        if release_decision_difficulty is not None
        else keeper_score
    )
    easy_top_five_credit = max(0.0, drop_score - 35.0) * 0.18
    depth_credit = min(10.0, replacement_depth_count * 2.0)
    return _clamp(
        (0.62 * keeper_score)
        + (0.30 * inferred_gap)
        + (0.08 * difficulty)
        - easy_top_five_credit
        - depth_credit
    )


def forced_release_candidate_score(
    *,
    keeper_score: float,
    drop_score: float,
    confidence_score: float,
) -> float:
    return _clamp(
        (0.60 * drop_score)
        + (0.25 * (100.0 - keeper_score))
        + (0.15 * (100.0 - confidence_score))
    )


def pre_declaration_trade_urgency(
    *,
    keeper_score: float,
    market_score: float,
    drop_score: float,
    confidence_score: float,
    is_default_release: bool,
) -> float:
    if not is_default_release:
        return 0.0
    return _clamp(
        (0.42 * keeper_score)
        + (0.32 * market_score)
        + (0.16 * confidence_score)
        - (0.30 * drop_score)
    )


def reacquisition_priority(
    *,
    likely_target_value: float,
    keeper_score: float,
    drop_score: float,
    is_own_team: bool,
    is_default_release: bool,
) -> float:
    if not (is_own_team and is_default_release):
        return 0.0
    return _clamp((0.55 * likely_target_value) + (0.30 * keeper_score) - (0.22 * drop_score))


def opponent_release_target_score(
    *,
    likely_target_value: float,
    keeper_score: float,
    market_score: float,
    drop_score: float,
    is_opponent: bool,
    is_default_release: bool,
) -> float:
    if not (is_opponent and is_default_release):
        return 0.0
    return _clamp(
        (0.45 * likely_target_value)
        + (0.25 * keeper_score)
        + (0.20 * market_score)
        - (0.18 * drop_score)
    )


def _actions(
    *,
    keeper_score: float,
    is_own_team: bool,
    is_default_release: bool,
    trade_urgency: float,
    drop_score: float,
    reacquisition_score: float,
    opponent_target_score: float,
) -> tuple[str, str]:
    if not is_default_release:
        return ("keep", "")
    if is_own_team:
        if trade_urgency >= 58:
            action = "shop"
        elif keeper_score >= 82 and drop_score < 35:
            action = "trade non-forced player"
        else:
            action = "release" if drop_score >= 35 else "shop"
        draft_action = "reacquire" if reacquisition_score >= 62 else ""
        return action, draft_action
    draft_action = "target opponent release" if opponent_target_score >= 58 else ""
    return "target opponent release", draft_action


def strategy_reason_code(
    *,
    action: str,
    draft_action: str,
    is_own_team: bool,
    is_default_release: bool,
    keeper_score: float,
    drop_score: float,
    trade_urgency: float,
    reacquisition_score: float,
    opponent_target_score: float,
) -> str:
    if not is_default_release:
        return "top_five_not_required_cut"
    if not is_own_team:
        if opponent_target_score >= 75:
            return "opponent_release_priority_target"
        if opponent_target_score >= 58:
            return "opponent_release_watch_target"
        return "opponent_release_low_priority"
    if action == "trade non-forced player":
        return "protect_top_five_by_trading_elsewhere"
    if action == "shop":
        return "shop_before_declaration" if trade_urgency >= 58 else "shop_if_market_exists"
    if draft_action == "reacquire" or reacquisition_score >= 62:
        return "release_then_reacquire_candidate"
    if drop_score >= 35:
        return "release_as_cleanest_rule_solution"
    if keeper_score >= 80:
        return "painful_top_five_release"
    return "release_lowest_private_cost"


def _action_label(action: str, draft_action: str) -> str:
    if draft_action:
        return f"{action} / {draft_action}"
    return action


def _rule_explanation(*, is_default_release: bool, required_release_count: int) -> str:
    if required_release_count <= 0:
        return "No Required Top-Five Release Slot is active for this team."
    if is_default_release:
        return (
            "This row currently satisfies the Required Top-Five Release Slot "
            "for this roster."
        )
    return (
        "This player is inside this roster's five highest league-ranked players "
        "but is not the current required release slot."
    )


def _score_explanation(
    *,
    keeper_score: float,
    drop_score: float,
    trade_urgency: float,
    reacquisition_score: float,
    opponent_target_score: float,
    own_team: bool,
) -> str:
    if own_team:
        return (
            f"Keeper {keeper_score:.1f}, drop {drop_score:.1f}, trade urgency "
            f"{trade_urgency:.1f}, reacquire {reacquisition_score:.1f}."
        )
    return (
        f"Keeper {keeper_score:.1f}, drop {drop_score:.1f}, opponent target "
        f"{opponent_target_score:.1f}."
    )


def _next_step(
    *,
    action: str,
    draft_action: str,
    own_team: bool,
    is_default_release: bool,
) -> str:
    if not is_default_release:
        return "Keep on the roster top-five watch list; no immediate declaration action."
    if own_team and action == "shop":
        return "Shop before declaration; do not treat release as final until market is checked."
    if own_team and action == "trade non-forced player":
        return "Review non-forced trade paths before locking this player as the release."
    if own_team and action == "release" and draft_action == "reacquire":
        return "Declare release, then keep him on the offline draft target list."
    if own_team and action == "release":
        return "Cleanest current declaration release if no trade market appears."
    if draft_action == "target opponent release":
        return "Track as an opponent release target for the offline draft board."
    return "Monitor only; current target score does not justify a draft-room priority."


def _team_decision_status(required_release_count: int, trade_urgency: float) -> str:
    if required_release_count <= 0:
        return "no_forced_release"
    if trade_urgency >= 65:
        return "trade_before_declaration"
    if trade_urgency >= 45:
        return "review_market"
    return "release_path_clear"


def _team_explanation(
    *,
    team_name: str,
    required_release_count: int,
    default_release_rows: list[dict[str, object]],
    trade_urgency: float,
) -> str:
    if required_release_count <= 0:
        return f"{team_name} has no Required Top-Five Release Slot."
    release_names = ", ".join(
        str(row.get("player_name") or row.get("player_id") or "")
        for row in default_release_rows
    )
    if trade_urgency >= 65:
        return (
            f"{team_name} must release {required_release_count}; {release_names} "
            "should be shopped before declaration."
        )
    if trade_urgency >= 45:
        return (
            f"{team_name} must release {required_release_count}; {release_names} "
            "needs market review before accepting the cut."
        )
    return (
        f"{team_name} must release {required_release_count}; {release_names} "
        "is the current cleanest rule solution."
    )


def _explanation(
    row: dict[str, object],
    *,
    is_default_release: bool,
    action: str,
    draft_action: str,
    strategy_reason: str,
) -> str:
    if not is_default_release:
        return (
            "Inside this roster's five highest league-ranked players, but not "
            "the default rule cut."
        )
    player = str(row.get("player_name") or row.get("player_id") or "Player")
    drop = _score(row.get("drop_candidate_score"))
    keeper = _score(row.get("keeper_score"))
    if strategy_reason == "protect_top_five_by_trading_elsewhere":
        return (
            f"{player} is the default rule cut, but keeper value is strong enough "
            "to review trading a non-forced player before accepting the cut."
        )
    if action == "shop":
        return (
            f"{player} is the default rule cut by lowest model value inside "
            "this roster's league-rank top-five group, but keeper value is high "
            "enough to shop before declaration."
        )
    if draft_action == "reacquire":
        return (
            f"{player} is the default rule cut, but the model still values him "
            "enough to consider reacquiring at draft cost."
        )
    if action == "target opponent release":
        return (
            f"{player} is another team's default rule cut with enough remaining "
            "asset value to monitor as an offline draft target."
        )
    return (
        f"{player} is the default rule cut because his keeper value ({keeper:.1f}) "
        "is the cheapest release inside this roster's five highest league-ranked "
        f"players; drop score is {drop:.1f}."
    )


def team_release_pressure_profile(
    team_player_rows: list[dict[str, object]],
    *,
    official_top_five_keep_limit: int = 4,
) -> ForcedReleasePressureProfile:
    rostered_rows = _rostered_rows(team_player_rows)
    top_five_rows = _league_rank_top_five(rostered_rows)
    required_count = max(0, len(top_five_rows) - official_top_five_keep_limit)
    default_release_rows = _default_release_rows(top_five_rows, required_count)
    top_five_ids = {str(row.get("player_id") or "") for row in top_five_rows}
    non_top_five_rows = [
        row
        for row in rostered_rows
        if str(row.get("player_id") or "") not in top_five_ids
    ]
    easy_drop_row = _easy_non_top_five_drop(non_top_five_rows)
    bubble_rows = _bubble_rows(non_top_five_rows)

    if not default_release_rows:
        team_name = _team_name(team_player_rows, "Team")
        return ForcedReleasePressureProfile(
            top_five_rows=top_five_rows,
            default_release_rows=[],
            easy_drop_row=easy_drop_row,
            bubble_rows=bubble_rows,
            required_release_count=required_count,
            forced_release_pain=0.0,
            easy_drop_available=easy_drop_row is not None,
            top_five_value_gap=0.0,
            release_decision_difficulty=0.0,
            replacement_depth_count=0,
            pressure_count=0,
            pressure_level="none",
            explanation=f"{team_name} has no Required Top-Five Release Slot.",
        )

    release_row = default_release_rows[0]
    release_value = _player_value(release_row)
    easy_drop_value = _player_value(easy_drop_row) if easy_drop_row else release_value
    value_gap = max(0.0, release_value - easy_drop_value)
    next_top_value = _next_top_five_value(top_five_rows, release_row, release_value)
    cluster_gap = max(0.0, next_top_value - release_value)
    replacement_depth_count = sum(
        1
        for row in non_top_five_rows
        if _player_value(row) >= release_value - 8.0
    )
    easy_drop_available = bool(
        easy_drop_row
        and (
            easy_drop_value <= 62.0
            or _drop_risk(easy_drop_row) >= 35.0
        )
    )
    decision_difficulty = _release_decision_difficulty(
        release_value=release_value,
        value_gap=value_gap,
        cluster_gap=cluster_gap,
        replacement_depth_count=replacement_depth_count,
    )
    pain = forced_release_pressure_score(
        required_release_count=required_count,
        keeper_score=release_value,
        market_score=_score(release_row.get("market_score"), release_value),
        drop_score=_drop_risk(release_row),
        confidence_score=_confidence(release_row.get("confidence_score")),
        is_default_release=True,
        easy_drop_value=easy_drop_value,
        top_five_value_gap=value_gap,
        release_decision_difficulty=decision_difficulty,
        replacement_depth_count=replacement_depth_count,
    )
    pressure_count = _pain_pressure_count(pain, decision_difficulty)
    return ForcedReleasePressureProfile(
        top_five_rows=top_five_rows,
        default_release_rows=default_release_rows,
        easy_drop_row=easy_drop_row,
        bubble_rows=bubble_rows,
        required_release_count=required_count,
        forced_release_pain=pain,
        easy_drop_available=easy_drop_available,
        top_five_value_gap=value_gap,
        release_decision_difficulty=decision_difficulty,
        replacement_depth_count=replacement_depth_count,
        pressure_count=pressure_count,
        pressure_level=_pressure_level_from_pain(pain),
        explanation=_pressure_explanation(
            team_name=_team_name(team_player_rows, "Team"),
            release_row=release_row,
            easy_drop_row=easy_drop_row,
            pain=pain,
            value_gap=value_gap,
            easy_drop_available=easy_drop_available,
            replacement_depth_count=replacement_depth_count,
        ),
    )


def _asset_values(data_pack_path: str | Path) -> dict[str, float]:
    board = build_unified_asset_board(data_pack_path)
    values: dict[str, float] = {}
    for row in board.rows:
        asset_id = str(row.get("asset_id") or "")
        if ":" not in asset_id:
            continue
        _, player_id = asset_id.split(":", 1)
        values[player_id] = _score(row.get("acquisition_value"), 50.0)
    return values


def _rostered_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if str(row.get("roster_status") or "rostered").lower() == "rostered"
        and str(row.get("position") or "").upper() != "K"
    ]


def _league_rank_top_five(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    ranked_rows = [row for row in rows if _optional_int(row.get("league_rank")) is not None]
    return sorted(
        ranked_rows,
        key=lambda row: (
            _optional_int(row.get("league_rank")) or 999,
            str(row.get("player_name") or row.get("player_id") or ""),
        ),
    )[:5]


def _default_release_rows(
    top_five_rows: list[dict[str, object]],
    required_release_count: int,
) -> list[dict[str, object]]:
    if required_release_count <= 0:
        return []
    return sorted(
        top_five_rows,
        key=lambda row: (
            _player_value(row),
            -_drop_risk(row),
            _optional_int(row.get("league_rank")) or 999,
            str(row.get("player_name") or row.get("player_id") or ""),
        ),
    )[:required_release_count]


def _easy_non_top_five_drop(
    non_top_five_rows: list[dict[str, object]],
) -> dict[str, object] | None:
    if not non_top_five_rows:
        return None
    return sorted(
        non_top_five_rows,
        key=lambda row: (
            _player_value(row),
            -_drop_risk(row),
            str(row.get("player_name") or row.get("player_id") or ""),
        ),
    )[0]


def _bubble_rows(non_top_five_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return sorted(
        [
            row
            for row in non_top_five_rows
            if _player_value(row) <= 70.0 or _drop_risk(row) >= 30.0
        ],
        key=lambda row: (
            _player_value(row),
            -_drop_risk(row),
            str(row.get("player_name") or row.get("player_id") or ""),
        ),
    )[:5]


def _next_top_five_value(
    top_five_rows: list[dict[str, object]],
    release_row: dict[str, object],
    release_value: float,
) -> float:
    release_id = str(release_row.get("player_id") or "")
    higher_values = sorted(
        _player_value(row)
        for row in top_five_rows
        if str(row.get("player_id") or "") != release_id
    )
    return higher_values[0] if higher_values else release_value


def _release_decision_difficulty(
    *,
    release_value: float,
    value_gap: float,
    cluster_gap: float,
    replacement_depth_count: int,
) -> float:
    cluster_difficulty = max(20.0, 100.0 - min(70.0, cluster_gap * 2.0))
    replacement_credit = min(10.0, replacement_depth_count * 2.0)
    return _clamp(
        (0.55 * release_value)
        + (0.25 * value_gap)
        + (0.20 * cluster_difficulty)
        - replacement_credit
    )


def _pain_pressure_count(pain: float, decision_difficulty: float) -> int:
    return int(pain >= 55.0) + int(decision_difficulty >= 60.0)


def _pressure_level_from_pain(pain: float) -> str:
    if pain >= 70.0:
        return "high"
    if pain >= 45.0:
        return "medium"
    if pain > 0.0:
        return "low"
    return "none"


def _pressure_explanation(
    *,
    team_name: str,
    release_row: dict[str, object],
    easy_drop_row: dict[str, object] | None,
    pain: float,
    value_gap: float,
    easy_drop_available: bool,
    replacement_depth_count: int,
) -> str:
    release_name = _row_player_name(release_row)
    easy_name = _row_player_name(easy_drop_row)
    release_value = _player_value(release_row)
    secondary_context = (
        f" Secondary context: the easiest regular cut outside the roster top five is {easy_name}."
        if easy_name
        else " Secondary context: no clear regular cut outside the roster top five is available."
    )
    if pain >= 70.0:
        return (
            f"{team_name} has real forced-release pain: {release_name} is the "
            "least painful required release inside this roster's five highest "
            "league-ranked players, "
            f"but still carries {release_value:.1f} model value."
            f"{secondary_context} The secondary value gap is {value_gap:.1f}."
        )
    if pain >= 45.0:
        return (
            f"{team_name} has a review-worthy release decision. {release_name} "
            "is the least painful required release inside this roster's five "
            f"highest league-ranked players and carries {release_value:.1f} "
            "model value."
            f"{secondary_context}"
        )
    if easy_drop_available:
        return (
            f"{team_name}'s Required Top-Five Release Slot is relatively painless: "
            f"{release_name} is the least painful roster top-five option and is close "
            f"enough to secondary roster-cut value that pressure stays low."
            f"{secondary_context}"
        )
    if replacement_depth_count:
        return (
            f"{team_name}'s Required Top-Five Release Slot pressure is low because "
            f"internal replacement depth softens the loss of {release_name}."
        )
    return (
        f"{team_name}'s Required Top-Five Release Slot pressure is low because "
        f"{release_name} is not a high-value forced cut."
    )


def _row_player_name(row: dict[str, object] | None) -> str:
    if not row:
        return ""
    return str(row.get("player_name") or row.get("player") or row.get("player_id") or "")


def _player_value(row: dict[str, object] | None) -> float:
    if not row:
        return 50.0
    for column in ("keeper_score", "private_score", "war_score"):
        value = row.get(column)
        if value is not None and value != "":
            return _score(value)
    drop_value = row.get("drop_candidate_score")
    if drop_value is not None and drop_value != "":
        return _clamp(100.0 - float(drop_value))
    return 50.0


def _drop_risk(row: dict[str, object] | None) -> float:
    if not row:
        return 50.0
    value = row.get("drop_candidate_score")
    if value is not None and value != "":
        return _score(value)
    return _clamp(100.0 - _player_value(row))


def _has_real_model_output(row: dict[str, object]) -> bool:
    return bool(row.get("model_version")) and "Neutral placeholder" not in str(
        row.get("notes") or ""
    )


def _has_real_model_outputs(rows: list[dict[str, object]]) -> bool:
    return bool(rows) and all(_has_real_model_output(row) for row in rows)


def _by_player_id(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {str(row.get("player_id")): row for row in rows if row.get("player_id")}


def _rows_by_team(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    rows_by_team: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        rows_by_team[str(row.get("team_id") or "")].append(row)
    return dict(rows_by_team)


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


def _team_name(rows: list[dict[str, object]], fallback: str) -> str:
    if not rows:
        return fallback
    return str(rows[0].get("team_name") or fallback)


def _pressure_level(trade_urgency: float, required_release_count: int) -> str:
    if required_release_count <= 0:
        return "none"
    if trade_urgency >= 65:
        return "high"
    if trade_urgency >= 45:
        return "medium"
    return "low"


def _first_present(*values: object) -> object:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _score(value: object, default: float = 50.0) -> float:
    if value is None or value == "":
        return default
    return _clamp(float(value))


def _confidence(value: object) -> float:
    score = _score(value, 50.0)
    if score <= 1.0:
        return round(score * 100.0, 2)
    return score


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))
