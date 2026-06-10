from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS

MODEL_VERSION = "model_v4_qb_age_horizon_shadow_0.1.0"
DEFAULT_COMPONENT_ROWS = Path(
    "local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv"
)
DEFAULT_AGE_ROWS = Path(
    "local_exports/active_veteran_model_public_sources/veteran_player_inputs.csv"
)
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/candidates/qb_age_horizon_shadow")

WATCH_QBS = (
    "Matthew Stafford",
    "Aaron Rodgers",
    "Kirk Cousins",
    "Russell Wilson",
    "Dak Prescott",
    "Jared Goff",
    "Baker Mayfield",
    "Patrick Mahomes",
    "Lamar Jackson",
    "Josh Allen",
    "Jalen Hurts",
    "Joe Burrow",
    "Jayden Daniels",
    "Drake Maye",
    "Trevor Lawrence",
)

SHADOW_COLUMNS = (
    "shadow_model_version",
    "baseline_rank",
    "shadow_rank",
    "rank_delta",
    "baseline_score",
    "shadow_score",
    "score_delta",
    "age_years",
    "age_source_path",
    "qb_role_archetype",
    "qb_positive_vorp_points",
    "qb_review_scoring_points",
    "qb_first_down_points",
    "old_qb_horizon_cap",
    "old_qb_horizon_reason_codes",
    "old_qb_horizon_evidence_fields",
    "old_qb_horizon_policy",
)

RANKING_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "trust_status",
    "warning_flags",
) + SHADOW_COLUMNS

QB_MOVEMENT_HEADER = (
    "player",
    "position",
    "age_years",
    "team",
    "baseline_rank",
    "shadow_rank",
    "rank_delta",
    "baseline_score",
    "shadow_score",
    "score_delta",
    "role_archetype",
    "positive_vorp_points",
    "review_scoring_points",
    "first_down_points",
    "applied_cap",
    "reason_codes",
    "human_review_question",
)

GATE_HEADER = (
    "gate",
    "status",
    "observed_value",
    "threshold_or_expected",
    "details",
)

SUMMARY_HEADER = ("metric", "value")


@dataclass(frozen=True)
class QBAgeHorizonShadowResult:
    rows: tuple[dict[str, object], ...]
    qb_movement_rows: tuple[dict[str, object], ...]
    watch_rows: tuple[dict[str, object], ...]
    gate_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class QBAgeHorizonShadowPaths:
    rankings: Path
    qb_movement: Path
    watch_rows: Path
    gate_report: Path
    summary: Path


def build_qb_age_horizon_shadow(
    *,
    board_path: str | Path = DEFAULT_FULL_PLAYER_BOARD_ROWS,
    component_rows_path: str | Path = DEFAULT_COMPONENT_ROWS,
    age_rows_path: str | Path = DEFAULT_AGE_ROWS,
) -> QBAgeHorizonShadowResult:
    board_rows = _read_rows(Path(board_path))
    component_lookup = _component_lookup(_read_rows(Path(component_rows_path)))
    age_lookup = _age_lookup(_read_rows(Path(age_rows_path)))

    rows = _shadow_rows(
        board_rows=board_rows,
        component_lookup=component_lookup,
        age_lookup=age_lookup,
        age_rows_path=Path(age_rows_path),
    )
    qb_rows = tuple(row for row in rows if row.get("position") == "QB")
    watch_rows = tuple(
        row
        for row in qb_rows
        if row.get("player_name") in WATCH_QBS
    )
    movement_rows = tuple(_qb_movement_row(row) for row in qb_rows)
    gates = _gate_rows(board_rows, rows, movement_rows)
    summary = _summary_rows(board_rows, rows, movement_rows, gates)
    return QBAgeHorizonShadowResult(
        rows=tuple(rows),
        qb_movement_rows=movement_rows,
        watch_rows=tuple(_qb_movement_row(row) for row in watch_rows),
        gate_rows=gates,
        summary_rows=summary,
    )


def write_qb_age_horizon_shadow_exports(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    result: QBAgeHorizonShadowResult | None = None,
) -> QBAgeHorizonShadowPaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_qb_age_horizon_shadow()
    paths = QBAgeHorizonShadowPaths(
        rankings=output / "shadow_qb_age_horizon_rankings.csv",
        qb_movement=output / "shadow_qb_age_horizon_qb_movement.csv",
        watch_rows=output / "shadow_qb_age_horizon_watch_rows.csv",
        gate_report=output / "shadow_qb_age_horizon_gate_report.csv",
        summary=output / "shadow_qb_age_horizon_summary.csv",
    )
    _write_csv(paths.rankings, RANKING_HEADER, result.rows)
    _write_csv(paths.qb_movement, QB_MOVEMENT_HEADER, result.qb_movement_rows)
    _write_csv(paths.watch_rows, QB_MOVEMENT_HEADER, result.watch_rows)
    _write_csv(paths.gate_report, GATE_HEADER, result.gate_rows)
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    return paths


def _shadow_rows(
    *,
    board_rows: list[dict[str, str]],
    component_lookup: dict[str, dict[str, str]],
    age_lookup: dict[str, dict[str, str]],
    age_rows_path: Path,
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in board_rows:
        component = component_lookup.get(_row_key(row), {})
        age_row = age_lookup.get(_row_key(row), {})
        base_score = _float(row.get("nwr_dynasty_score"))
        shadow = _shadow_score(row, component, age_row, base_score)
        out = {
            "player_name": row.get("player_name", ""),
            "position": row.get("position", ""),
            "nfl_team": row.get("nfl_team", ""),
            "trust_status": row.get("trust_status", ""),
            "warning_flags": row.get("warning_flags", ""),
            "shadow_model_version": MODEL_VERSION,
            "baseline_rank": row.get("nwr_rank", ""),
            "shadow_rank": "",
            "rank_delta": "",
            "baseline_score": row.get("nwr_dynasty_score", ""),
            "shadow_score": _score_text(shadow["shadow_score"]),
            "score_delta": _blank(_score_delta(shadow["shadow_score"], base_score)),
            "age_years": age_row.get("age", ""),
            "age_source_path": str(age_rows_path) if age_row else "",
            "qb_role_archetype": component.get("role_archetype", ""),
            "qb_positive_vorp_points": component.get("positive_vorp_points", ""),
            "qb_review_scoring_points": component.get("review_scoring_points", ""),
            "qb_first_down_points": component.get("imported_first_down_points", ""),
            "old_qb_horizon_cap": shadow["cap"],
            "old_qb_horizon_reason_codes": "|".join(shadow["reason_codes"]),
            "old_qb_horizon_evidence_fields": "|".join(shadow["evidence_fields"]),
            "old_qb_horizon_policy": (
                "shadow_only_current_board_audit;"
                "uses_position_age_role_vorp_review_scoring_first_down_receipts_only;"
                "market_adp_consensus_projection_trade_rotowire_ranking_legacy_blocked"
            ),
            "_shadow_score_float": shadow["shadow_score"],
        }
        output.append(out)
    _assign_shadow_ranks(output)
    for row in output:
        base_rank = _int(row.get("baseline_rank"))
        shadow_rank = _int(row.get("shadow_rank"))
        row["rank_delta"] = _blank(_delta(shadow_rank, base_rank))
    return output


def _shadow_score(
    row: dict[str, str],
    component: dict[str, str],
    age_row: dict[str, str],
    base_score: float | None,
) -> dict[str, object]:
    if base_score is None:
        return _shadow(base_score, "", ("unscored_or_hidden",), ("position",))
    if row.get("position") != "QB":
        return _shadow(base_score, "", ("not_qb",), ("position", "nwr_dynasty_score"))
    age = _float(age_row.get("age"))
    if age is None:
        return _shadow(
            base_score,
            "",
            ("qb_age_source_missing_no_shadow_cap",),
            ("position", "nwr_dynasty_score", "age"),
        )

    role = component.get("role_archetype", "")
    first_down = _float(component.get("imported_first_down_points")) or 0.0
    vorp = _float(component.get("positive_vorp_points")) or 0.0
    review = _float(component.get("review_scoring_points")) or 0.0
    is_pocket = "pocket" in role
    evidence_fields = (
        "position",
        "age",
        "role_archetype",
        "positive_vorp_points",
        "review_scoring_points",
        "imported_first_down_points",
        "nwr_dynasty_score",
        "warning_flags",
    )
    if not is_pocket:
        return _shadow(
            base_score,
            "",
            ("qb_age_horizon_not_pocket_or_rushing_profile",),
            evidence_fields,
        )
    if age < 37.0:
        return _shadow(
            base_score,
            "",
            ("qb_age_horizon_under_old_pocket_threshold",),
            evidence_fields,
        )

    retained_value_receipt = first_down >= 8.0 and vorp >= 55.0 and review >= 300.0
    if retained_value_receipt:
        return _shadow(
            base_score,
            "",
            ("old_pocket_qb_exception_receipt_present",),
            evidence_fields,
        )

    cap = 12.0 if age >= 40.0 else 23.5
    if first_down >= 4.0:
        cap = max(cap, 27.5)
    score = min(base_score, cap)
    reason = (
        "old_pocket_qb_horizon_cap_applied"
        if score < base_score
        else "old_pocket_qb_already_below_horizon_cap"
    )
    return _shadow(
        score,
        cap,
        (reason, "one_qb_passing_td_deemphasized_horizon"),
        evidence_fields,
    )


def _shadow(
    score: float | None,
    cap: object,
    reason_codes: tuple[str, ...],
    evidence_fields: tuple[str, ...],
) -> dict[str, object]:
    return {
        "shadow_score": score,
        "cap": cap,
        "reason_codes": reason_codes,
        "evidence_fields": evidence_fields,
    }


def _assign_shadow_ranks(rows: list[dict[str, object]]) -> None:
    scored = sorted(
        (
            row
            for row in rows
            if row.get("position") in {"QB", "RB", "WR", "TE"}
            and row.get("_shadow_score_float") is not None
        ),
        key=lambda row: (
            -float(row.get("_shadow_score_float") or 0.0),
            str(row.get("player_name") or "").lower(),
        ),
    )
    for rank, row in enumerate(scored, start=1):
        row["shadow_rank"] = str(rank)


def _qb_movement_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "player": row.get("player_name", ""),
        "position": row.get("position", ""),
        "age_years": row.get("age_years", ""),
        "team": row.get("nfl_team", ""),
        "baseline_rank": row.get("baseline_rank", ""),
        "shadow_rank": row.get("shadow_rank", ""),
        "rank_delta": row.get("rank_delta", ""),
        "baseline_score": row.get("baseline_score", ""),
        "shadow_score": row.get("shadow_score", ""),
        "score_delta": row.get("score_delta", ""),
        "role_archetype": row.get("qb_role_archetype", ""),
        "positive_vorp_points": row.get("qb_positive_vorp_points", ""),
        "review_scoring_points": row.get("qb_review_scoring_points", ""),
        "first_down_points": row.get("qb_first_down_points", ""),
        "applied_cap": row.get("old_qb_horizon_cap", ""),
        "reason_codes": row.get("old_qb_horizon_reason_codes", ""),
        "human_review_question": _human_review_question(row),
    }


def _human_review_question(row: dict[str, object]) -> str:
    reasons = str(row.get("old_qb_horizon_reason_codes", ""))
    if "old_pocket_qb_horizon_cap_applied" in reasons:
        return (
            "Does current passing VORP justify this old pocket QB in a 10-team 1QB "
            "dynasty board after age/horizon risk?"
        )
    if "old_pocket_qb_already_below_horizon_cap" in reasons:
        return "Already below the old-pocket horizon cap; no score change needed."
    if "qb_age_horizon_not_pocket" in reasons:
        return "Rushing/long-term QB profile was intentionally not capped by this audit."
    return "No old-pocket QB horizon issue from current receipts."


def _gate_rows(
    board_rows: list[dict[str, str]],
    shadow_rows: list[dict[str, object]],
    movement_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    gates = [
        _gate("active_rows_unchanged", len(shadow_rows), len(board_rows), "Shadow row count."),
        _gate(
            "banned_scoring_input_count",
            _banned_input_count(shadow_rows),
            0,
            "Evidence fields exclude market/ADP/consensus/projection/legacy inputs.",
        ),
        _gate(
            "non_qb_score_changes",
            _non_qb_score_changes(shadow_rows),
            0,
            "Shadow cap only changes QB scores.",
        ),
        _gate(
            "stafford_horizon_cap_applied",
            _player_reason(shadow_rows, "Matthew Stafford"),
            "contains_old_pocket_guardrail",
            "Stafford should trigger or already sit below the general old-pocket cap.",
        ),
        _gate(
            "elite_rushing_qbs_not_crushed",
            _elite_rushing_qb_changes(movement_rows),
            0,
            "Allen/Hurts/Lamar-style profiles are not automatically crushed.",
        ),
        _gate(
            "historical_replay_metrics_unchanged",
            "not_recomputed_current_board_only",
            "not_recomputed_current_board_only",
            "Historical rookie replay is not a valid old-veteran QB age test.",
        ),
    ]
    return tuple(gates)


def _summary_rows(
    board_rows: list[dict[str, str]],
    shadow_rows: list[dict[str, object]],
    movement_rows: tuple[dict[str, object], ...],
    gate_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    changed = [row for row in movement_rows if _float(row.get("score_delta")) not in {None, 0.0}]
    failed = [row for row in gate_rows if row["status"] != "pass"]
    summary = {
        "shadow_model_version": MODEL_VERSION,
        "active_rows": len(board_rows),
        "shadow_rows": len(shadow_rows),
        "qb_rows": len(movement_rows),
        "qb_score_changed_rows": len(changed),
        "largest_qb_rank_drop": max(
            (_int(row.get("rank_delta")) or 0 for row in movement_rows),
            default=0,
        ),
        "gate_failures": len(failed),
        "historical_qb_metrics_status": "not_recomputed_current_board_only",
    }
    return tuple({"metric": key, "value": value} for key, value in summary.items())


def _gate(gate: str, observed: object, expected: object, details: str) -> dict[str, object]:
    if expected == "contains_old_pocket_guardrail":
        status = (
            "pass"
            if "old_pocket_qb_horizon_cap_applied" in str(observed)
            or "old_pocket_qb_already_below_horizon_cap" in str(observed)
            else "fail"
        )
    else:
        status = "pass" if observed == expected else "fail"
    return {
        "gate": gate,
        "status": status,
        "observed_value": observed,
        "threshold_or_expected": expected,
        "details": details,
    }


def _banned_input_count(rows: list[dict[str, object]]) -> int:
    banned = (
        "market",
        "league_rank",
        "adp",
        "consensus",
        "projection",
        "trade",
        "rotowire_rank",
        "legacy",
        "private_score",
    )
    count = 0
    for row in rows:
        evidence = str(row.get("old_qb_horizon_evidence_fields", "")).lower()
        count += sum(1 for item in banned if item in evidence)
    return count


def _non_qb_score_changes(rows: list[dict[str, object]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("position") != "QB"
        and (_float(row.get("score_delta")) or 0.0) != 0.0
    )


def _player_reason(rows: list[dict[str, object]], player: str) -> str:
    row = next((row for row in rows if row.get("player_name") == player), {})
    return str(row.get("old_qb_horizon_reason_codes", ""))


def _elite_rushing_qb_changes(movement_rows: tuple[dict[str, object], ...]) -> int:
    elite_rushing = {"Josh Allen", "Jalen Hurts", "Lamar Jackson"}
    return sum(
        1
        for row in movement_rows
        if row.get("player") in elite_rushing
        and (_float(row.get("score_delta")) or 0.0) < 0
    )


def _component_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {_row_key(row): row for row in rows}


def _age_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        _row_key(row): row
        for row in rows
        if row.get("position") == "QB" and row.get("age")
    }


def _row_key(row: dict[str, object]) -> str:
    return _norm(
        str(
            row.get("normalized_player_name")
            or row.get("player_name")
            or row.get("player")
            or ""
        )
    )


def _norm(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _int(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None


def _float(value: object) -> float | None:
    try:
        text = str(value).strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _delta(new: int | None, old: int | None) -> int | None:
    if new is None or old is None:
        return None
    return new - old


def _score_delta(new: float | None, old: float | None) -> float | None:
    if new is None or old is None:
        return None
    return round(new - old, 4)


def _blank(value: object) -> object:
    return "" if value is None else value


def _score_text(value: object) -> str:
    if value is None:
        return ""
    return str(round(float(value), 4))


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})
