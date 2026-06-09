from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.config.lve_scoring import LVE_SCORING
from src.services.model_v4_fantasypros_identity_mapping_service import normalize_player_name
from src.services.model_v4_formula_contract_service import (
    ADMITTED_RECEIVING_FIRST_DOWNS,
    ADMITTED_RETURN_SCORING,
    ADMITTED_RUSHING_FIRST_DOWNS,
    NFL_MATRIX,
    assert_formula_field_allowed,
)

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/replacement_vorp/latest")
DEFAULT_DOC_PATH = Path("docs/model_v4/PHASE_11B_REPLACEMENT_VORP_CORE.md")

VORP_CORE_VERSION = "model_v4_phase_11b_replacement_vorp_core_0.1.0"
SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")

REPLACEMENT_DEFAULTS = {
    "QB": {
        "required_starter_rank": 10,
        "configured_replacement_rank": 12,
        "lineup_assumption": "10 teams x 1QB; conservative shallow-league fringe starter.",
    },
    "RB": {
        "required_starter_rank": 20,
        "configured_replacement_rank": 30,
        "lineup_assumption": "10 teams x 2RB plus flex pressure.",
    },
    "WR": {
        "required_starter_rank": 30,
        "configured_replacement_rank": 40,
        "lineup_assumption": "10 teams x 3WR plus flex pressure.",
    },
    "TE": {
        "required_starter_rank": 10,
        "configured_replacement_rank": 12,
        "lineup_assumption": "10 teams x 1TE; no TE premium.",
    },
}

BASELINE_HEADER = (
    "position",
    "league_teams",
    "lineup_assumption",
    "required_starter_rank",
    "configured_replacement_rank",
    "applied_replacement_rank",
    "player_pool_count",
    "replacement_player",
    "replacement_team",
    "replacement_review_scoring_points",
    "replacement_base_scoring_points",
    "replacement_imported_first_down_points",
    "replacement_return_scoring_points",
    "replacement_first_down_source_status",
    "replacement_warning",
    "allowed_use",
    "baseline_version",
)

PLAYER_VORP_HEADER = (
    "canonical_player_key",
    "player_name",
    "normalized_player_name",
    "position",
    "nfl_team",
    "scoring_season",
    "base_scoring_points",
    "imported_rushing_first_downs",
    "imported_receiving_first_downs",
    "imported_first_down_points",
    "first_down_source_status",
    "return_scoring_points",
    "return_source_status",
    "review_scoring_points",
    "configured_replacement_rank",
    "applied_replacement_rank",
    "replacement_player",
    "replacement_review_scoring_points",
    "vorp_points",
    "positive_vorp_points",
    "position_rank",
    "overall_vorp_rank",
    "qb_te_discipline_status",
    "allowed_use",
    "warning_flags",
    "vorp_version",
)

COMPONENT_HEADER = (
    "canonical_player_key",
    "player_name",
    "position",
    "component_name",
    "component_value",
    "component_source_status",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "receipt_pointer",
    "component_warning",
    "vorp_version",
)

RECEIPT_HEADER = (
    "canonical_player_key",
    "player_name",
    "position",
    "feature_group",
    "receipt_pointer",
    "source_status",
    "allowed_input_file",
    "allowed_lane",
    "allowed_field_or_json_path",
    "receipt_requirement",
    "vorp_version",
)

WARNING_HEADER = (
    "entity_key",
    "player_name",
    "position",
    "warning_type",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "vorp_version",
)


@dataclass(frozen=True)
class ReplacementVorpResult:
    baseline_rows: tuple[dict[str, object], ...]
    player_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass(frozen=True)
class ReplacementVorpPaths:
    baselines: Path
    player_rows: Path
    component_rows: Path
    receipts: Path
    warnings: Path
    doc: Path


@dataclass(frozen=True)
class _ScoredPlayer:
    canonical_player_key: str
    player_name: str
    normalized_player_name: str
    position: str
    nfl_team: str
    scoring_season: int | None
    base_scoring_points: float | None
    imported_rushing_first_downs: float | None
    imported_receiving_first_downs: float | None
    imported_first_down_points: float
    first_down_source_status: str
    return_scoring_points: float
    return_source_status: str
    review_scoring_points: float | None
    source_status: dict[str, Any]
    receipts: dict[str, Any]
    warning_flags: tuple[str, ...]


def build_replacement_vorp_core(
    *,
    nfl_matrix_path: str | Path = NFL_MATRIX,
    rushing_first_downs_path: str | Path = ADMITTED_RUSHING_FIRST_DOWNS,
    receiving_first_downs_path: str | Path = ADMITTED_RECEIVING_FIRST_DOWNS,
    return_scoring_path: str | Path = ADMITTED_RETURN_SCORING,
    replacement_defaults: dict[str, dict[str, object]] | None = None,
) -> ReplacementVorpResult:
    _assert_phase_11a_contract()
    defaults = replacement_defaults or REPLACEMENT_DEFAULTS
    nfl_rows = _read_rows(Path(nfl_matrix_path))
    rushing_first_downs = _first_down_index(Path(rushing_first_downs_path), "rushing")
    receiving_first_downs = _first_down_index(Path(receiving_first_downs_path), "receiving")
    return_scoring = _return_index(Path(return_scoring_path))

    scored_players = tuple(
        _score_player(row, rushing_first_downs, receiving_first_downs, return_scoring)
        for row in nfl_rows
        if row.get("position") in SUPPORTED_POSITIONS
    )
    baselines_by_position = _replacement_baselines(scored_players, defaults)
    player_rows = _player_rows(scored_players, baselines_by_position, defaults)
    component_rows = _component_rows(scored_players, baselines_by_position)
    receipt_rows = _receipt_rows(scored_players)
    warning_rows = _warning_rows(scored_players, baselines_by_position, player_rows)
    baseline_rows = tuple(baseline["row"] for baseline in baselines_by_position.values())
    summary = {
        "vorp_version": VORP_CORE_VERSION,
        "review_status": "review_only",
        "league_teams": 10,
        "format": "1QB non-PPR first-down scoring no TE premium",
        "player_rows": len(player_rows),
        "baseline_rows": len(baseline_rows),
        "component_rows": len(component_rows),
        "receipt_rows": len(receipt_rows),
        "warning_rows": len(warning_rows),
        "market_rows_used": 0,
        "projection_rows_used": 0,
        "adp_rows_used": 0,
        "rank_rows_used": 0,
        "generic_json_slurping_used": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return ReplacementVorpResult(
        baseline_rows=baseline_rows,
        player_rows=player_rows,
        component_rows=component_rows,
        receipt_rows=receipt_rows,
        warning_rows=warning_rows,
        summary=summary,
    )


def write_replacement_vorp_core_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    doc_path: str | Path = DEFAULT_DOC_PATH,
    result: ReplacementVorpResult | None = None,
) -> ReplacementVorpPaths:
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = result or build_replacement_vorp_core()
    paths = ReplacementVorpPaths(
        baselines=output / "replacement_baselines_review.csv",
        player_rows=output / "player_vorp_review_rows.csv",
        component_rows=output / "player_vorp_component_rows.csv",
        receipts=output / "player_vorp_receipts.csv",
        warnings=output / "player_vorp_warnings.csv",
        doc=Path(doc_path),
    )
    _write_csv(paths.baselines, BASELINE_HEADER, result.baseline_rows)
    _write_csv(paths.player_rows, PLAYER_VORP_HEADER, result.player_rows)
    _write_csv(paths.component_rows, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_doc(paths.doc, result, paths)
    return paths


def _assert_phase_11a_contract() -> None:
    allowed = (
        (NFL_MATRIX, "row_metadata", "position"),
        (NFL_MATRIX, "factual_evidence_json", "rotowire_player_stats"),
        (NFL_MATRIX, "derived_evidence_json", "stats_first_component_evidence"),
        (ADMITTED_RUSHING_FIRST_DOWNS, "admitted_first_down_view", "rushing_first_downs"),
        (
            ADMITTED_RECEIVING_FIRST_DOWNS,
            "admitted_first_down_view",
            "receiving_first_downs",
        ),
        (
            ADMITTED_RETURN_SCORING,
            "admitted_return_view",
            "return_yards_total|return_td_total",
        ),
        (NFL_MATRIX, "source_status_json", "source_status_json"),
        (NFL_MATRIX, "receipt_pointers_json", "receipt_pointers_json"),
    )
    for input_file, lane, field in allowed:
        assert_formula_field_allowed(
            module_name="replacement_vorp_core",
            allowed_input_file=input_file,
            allowed_lane=lane,
            allowed_field_or_json_path=field,
            private_value=lane
            not in {
                "source_status_json",
                "receipt_pointers_json",
            },
        )


def _score_player(
    row: dict[str, str],
    rushing_first_downs: dict[tuple[str, str, int], dict[str, str]],
    receiving_first_downs: dict[tuple[str, str, int], dict[str, str]],
    return_scoring: dict[tuple[str, str, int], dict[str, str]],
) -> _ScoredPlayer:
    factual = _json_obj(row.get("factual_evidence_json"))
    source_status = _json_obj(row.get("source_status_json"))
    receipts = _json_obj(row.get("receipt_pointers_json"))
    player_name = row.get("player_name", "")
    normalized = row.get("normalized_player_name") or normalize_player_name(player_name)
    position = row.get("position", "")
    stat_entry = _latest_fantasy_entry(factual.get("rotowire_player_stats", {}))
    metrics = stat_entry.get("metrics") if stat_entry else {}
    metrics = metrics if isinstance(metrics, dict) else {}
    scoring_season = _int(stat_entry.get("season")) if stat_entry else None
    base_points = _base_scoring_points(metrics) if stat_entry else None
    rushing_fd = _first_down_value(
        rushing_first_downs,
        normalized,
        position,
        scoring_season,
        "rushing_first_downs",
    )
    receiving_fd = _first_down_value(
        receiving_first_downs,
        normalized,
        position,
        scoring_season,
        "receiving_first_downs",
    )
    first_down_points = (
        _none_as_zero(rushing_fd) + _none_as_zero(receiving_fd)
    ) * LVE_SCORING["rushing_receiving_first_down"]
    return_row = return_scoring.get((normalized, position, scoring_season or -1), {})
    return_points = _return_points(return_row)
    review_points = (
        base_points + first_down_points + return_points if base_points is not None else None
    )
    warnings = _player_warning_flags(metrics, rushing_fd, receiving_fd, return_row, stat_entry)
    return _ScoredPlayer(
        canonical_player_key=row.get("canonical_player_key", ""),
        player_name=player_name,
        normalized_player_name=normalized,
        position=position,
        nfl_team=row.get("nfl_team", ""),
        scoring_season=scoring_season,
        base_scoring_points=base_points,
        imported_rushing_first_downs=rushing_fd,
        imported_receiving_first_downs=receiving_fd,
        imported_first_down_points=first_down_points,
        first_down_source_status=_first_down_status(rushing_fd, receiving_fd, metrics),
        return_scoring_points=return_points,
        return_source_status="imported_real_data_direct_scoring_only"
        if return_row
        else "no_admitted_return_scoring",
        review_scoring_points=review_points,
        source_status=source_status,
        receipts=receipts,
        warning_flags=tuple(warnings),
    )


def _replacement_baselines(
    players: tuple[_ScoredPlayer, ...],
    defaults: dict[str, dict[str, object]],
) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    for position in SUPPORTED_POSITIONS:
        ranked = sorted(
            [
                player
                for player in players
                if player.position == position and player.review_scoring_points is not None
            ],
            key=lambda player: player.review_scoring_points or 0.0,
            reverse=True,
        )
        config = defaults[position]
        configured_rank = int(config["configured_replacement_rank"])
        applied_rank = min(configured_rank, len(ranked)) if ranked else 0
        replacement = ranked[applied_rank - 1] if applied_rank else None
        warning = ""
        if len(ranked) < configured_rank:
            warning = (
                "admitted_pool_smaller_than_configured_replacement_rank;"
                "applied_last_available_player"
            )
        row = {
            "position": position,
            "league_teams": 10,
            "lineup_assumption": config["lineup_assumption"],
            "required_starter_rank": config["required_starter_rank"],
            "configured_replacement_rank": configured_rank,
            "applied_replacement_rank": applied_rank,
            "player_pool_count": len(ranked),
            "replacement_player": replacement.player_name if replacement else "",
            "replacement_team": replacement.nfl_team if replacement else "",
            "replacement_review_scoring_points": _round(
                replacement.review_scoring_points if replacement else None
            ),
            "replacement_base_scoring_points": _round(
                replacement.base_scoring_points if replacement else None
            ),
            "replacement_imported_first_down_points": _round(
                replacement.imported_first_down_points if replacement else None
            ),
            "replacement_return_scoring_points": _round(
                replacement.return_scoring_points if replacement else None
            ),
            "replacement_first_down_source_status": replacement.first_down_source_status
            if replacement
            else "",
            "replacement_warning": warning,
            "allowed_use": "review_only_replacement_vorp_core",
            "baseline_version": VORP_CORE_VERSION,
        }
        output[position] = {
            "row": row,
            "replacement": replacement,
            "ranked_players": ranked,
            "applied_rank": applied_rank,
            "configured_rank": configured_rank,
            "warning": warning,
        }
    return output


def _player_rows(
    players: tuple[_ScoredPlayer, ...],
    baselines: dict[str, dict[str, object]],
    defaults: dict[str, dict[str, object]],
) -> tuple[dict[str, object], ...]:
    position_rankings = {
        position: {
            player.canonical_player_key: index + 1
            for index, player in enumerate(info["ranked_players"])
        }
        for position, info in baselines.items()
    }
    rows: list[dict[str, object]] = []
    for player in players:
        baseline = baselines.get(player.position, {})
        replacement = baseline.get("replacement")
        replacement_points = (
            replacement.review_scoring_points
            if isinstance(replacement, _ScoredPlayer)
            else None
        )
        vorp = (
            player.review_scoring_points - replacement_points
            if player.review_scoring_points is not None and replacement_points is not None
            else None
        )
        position_rank = position_rankings.get(player.position, {}).get(
            player.canonical_player_key,
            "",
        )
        rows.append(
            {
                "canonical_player_key": player.canonical_player_key,
                "player_name": player.player_name,
                "normalized_player_name": player.normalized_player_name,
                "position": player.position,
                "nfl_team": player.nfl_team,
                "scoring_season": player.scoring_season or "",
                "base_scoring_points": _round(player.base_scoring_points),
                "imported_rushing_first_downs": _round(player.imported_rushing_first_downs),
                "imported_receiving_first_downs": _round(
                    player.imported_receiving_first_downs
                ),
                "imported_first_down_points": _round(player.imported_first_down_points),
                "first_down_source_status": player.first_down_source_status,
                "return_scoring_points": _round(player.return_scoring_points),
                "return_source_status": player.return_source_status,
                "review_scoring_points": _round(player.review_scoring_points),
                "configured_replacement_rank": defaults[player.position][
                    "configured_replacement_rank"
                ],
                "applied_replacement_rank": baseline.get("applied_rank", ""),
                "replacement_player": replacement.player_name
                if isinstance(replacement, _ScoredPlayer)
                else "",
                "replacement_review_scoring_points": _round(replacement_points),
                "vorp_points": _round(vorp),
                "positive_vorp_points": _round(max(vorp, 0.0)) if vorp is not None else "",
                "position_rank": position_rank,
                "overall_vorp_rank": "",
                "qb_te_discipline_status": _discipline_status(player, vorp, position_rank),
                "allowed_use": "review_only_replacement_vorp_core",
                "warning_flags": "|".join(player.warning_flags),
                "vorp_version": VORP_CORE_VERSION,
            }
        )
    ranked_rows = sorted(
        [row for row in rows if row["vorp_points"] != ""],
        key=lambda row: float(row["vorp_points"]),
        reverse=True,
    )
    rank_by_key = {
        str(row["canonical_player_key"]): index + 1 for index, row in enumerate(ranked_rows)
    }
    for row in rows:
        row["overall_vorp_rank"] = rank_by_key.get(str(row["canonical_player_key"]), "")
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row["overall_vorp_rank"] == "",
                int(row["overall_vorp_rank"] or 9999),
                str(row["player_name"]),
            ),
        )
    )


def _component_rows(
    players: tuple[_ScoredPlayer, ...],
    baselines: dict[str, dict[str, object]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for player in players:
        baseline = baselines.get(player.position, {})
        replacement = baseline.get("replacement")
        replacement_points = (
            replacement.review_scoring_points
            if isinstance(replacement, _ScoredPlayer)
            else None
        )
        components = (
            (
                "base_scoring_points",
                player.base_scoring_points,
                "formula_admitted_after_validation",
                NFL_MATRIX,
                "factual_evidence_json",
                "rotowire_player_stats",
                player.receipts.get("rotowire_player_stats", ""),
                "",
            ),
            (
                "imported_first_down_points",
                player.imported_first_down_points,
                player.first_down_source_status,
                ADMITTED_RUSHING_FIRST_DOWNS + "|" + ADMITTED_RECEIVING_FIRST_DOWNS,
                "admitted_first_down_view",
                "rushing_first_downs|receiving_first_downs",
                player.receipts.get("first_downs", ""),
                _first_down_component_warning(player),
            ),
            (
                "return_scoring_points",
                player.return_scoring_points,
                player.return_source_status,
                ADMITTED_RETURN_SCORING,
                "admitted_return_view",
                "return_yards_total|return_td_total",
                player.receipts.get("returns", ""),
                "direct_scoring_only_not_talent_signal",
            ),
            (
                "replacement_subtraction",
                -replacement_points if replacement_points is not None else None,
                "review_only_replacement_baseline",
                "local_exports/model_v4/replacement_vorp/latest/replacement_baselines_review.csv",
                "replacement_baseline",
                "replacement_review_scoring_points",
                "local_exports/model_v4/replacement_vorp/latest/replacement_baselines_review.csv",
                baseline.get("warning", ""),
            ),
        )
        for name, value, status, input_file, lane, field, receipt, warning in components:
            rows.append(
                {
                    "canonical_player_key": player.canonical_player_key,
                    "player_name": player.player_name,
                    "position": player.position,
                    "component_name": name,
                    "component_value": _round(value),
                    "component_source_status": status,
                    "allowed_input_file": input_file,
                    "allowed_lane": lane,
                    "allowed_field_or_json_path": field,
                    "receipt_pointer": receipt,
                    "component_warning": warning,
                    "vorp_version": VORP_CORE_VERSION,
                }
            )
    return tuple(rows)


def _receipt_rows(players: tuple[_ScoredPlayer, ...]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for player in players:
        receipt_specs = (
            (
                "rotowire_player_stats",
                player.receipts.get("rotowire_player_stats", ""),
                "formula_admitted_after_validation",
                NFL_MATRIX,
                "factual_evidence_json",
                "rotowire_player_stats",
            ),
            (
                "first_downs",
                player.receipts.get("first_downs", ""),
                player.first_down_source_status,
                ADMITTED_RUSHING_FIRST_DOWNS + "|" + ADMITTED_RECEIVING_FIRST_DOWNS,
                "admitted_first_down_view",
                "rushing_first_downs|receiving_first_downs",
            ),
            (
                "returns",
                player.receipts.get("returns", ""),
                player.return_source_status,
                ADMITTED_RETURN_SCORING,
                "admitted_return_view",
                "return_yards_total|return_td_total",
            ),
        )
        for group, receipt, status, input_file, lane, field in receipt_specs:
            rows.append(
                {
                    "canonical_player_key": player.canonical_player_key,
                    "player_name": player.player_name,
                    "position": player.position,
                    "feature_group": group,
                    "receipt_pointer": receipt,
                    "source_status": status,
                    "allowed_input_file": input_file,
                    "allowed_lane": lane,
                    "allowed_field_or_json_path": field,
                    "receipt_requirement": (
                        "Receipt pointer required for every consumed feature group."
                    ),
                    "vorp_version": VORP_CORE_VERSION,
                }
            )
    return tuple(rows)


def _warning_rows(
    players: tuple[_ScoredPlayer, ...],
    baselines: dict[str, dict[str, object]],
    player_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for player in players:
        for warning in player.warning_flags:
            rows.append(
                _warning(
                    player.canonical_player_key,
                    player.player_name,
                    player.position,
                    "player",
                    "review",
                    warning,
                    warning,
                    "Inspect before using VORP as a decision input.",
                )
            )
    for position, info in baselines.items():
        if info.get("warning"):
            rows.append(
                _warning(
                    f"baseline:{position}",
                    "",
                    position,
                    "baseline",
                    "review",
                    "admitted_pool_smaller_than_configured_replacement_rank",
                    str(info["warning"]),
                    "Expand admitted player universe or keep applied-rank warning visible.",
                )
            )
    rows.extend(_sanity_fixture_warnings(player_rows))
    return tuple(rows)


def _sanity_fixture_warnings(
    player_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows = list(player_rows)
    by_position = {
        position: [row for row in rows if row["position"] == position and row["vorp_points"] != ""]
        for position in SUPPORTED_POSITIONS
    }
    top_rb = _top_vorp(by_position["RB"])
    top_wr = _top_vorp(by_position["WR"])
    top_qb = _top_vorp(by_position["QB"])
    top_te = _top_vorp(by_position["TE"])
    top_non_qb = max(top_rb, top_wr, top_te)
    warnings = [
        _fixture(
            "elite_rb_vorp_sanity",
            "pass" if top_rb > 0 else "fail",
            f"Top RB VORP is {top_rb:.2f}; elite RB must clear replacement.",
        ),
        _fixture(
            "elite_wr_vorp_sanity",
            "pass" if top_wr > 0 else "fail",
            f"Top WR VORP is {top_wr:.2f}; elite WR must clear replacement.",
        ),
        _fixture(
            "one_qb_qb_sanity",
            "pass" if top_qb <= top_non_qb or top_qb > 75 else "review",
            (
                f"Top QB VORP is {top_qb:.2f}; top non-QB VORP is {top_non_qb:.2f}. "
                "QB value remains replacement-disciplined in 1QB."
            ),
        ),
        _fixture(
            "no_premium_te_sanity",
            "pass" if top_te > 0 else "fail",
            f"Top TE VORP is {top_te:.2f}; TE premium requires real no-premium gap.",
        ),
        _fixture(
            "aging_veteran_warning_sanity",
            "review",
            (
                "Phase 11B does not consume age/context fields; aging-veteran warnings "
                "must be handled by lifecycle_archetype before promotion."
            ),
        ),
        _fixture(
            "niners_roster_sanity",
            "pass" if any(row["nfl_team"] == "SF" for row in rows) else "review",
            "Niners roster players are present in review-only VORP rows.",
        ),
    ]
    mid_qb_issues = [
        row
        for row in by_position["QB"]
        if _int(row.get("position_rank")) and _int(row.get("position_rank")) > 5
        and _float(row.get("vorp_points")) > top_non_qb
    ]
    if mid_qb_issues:
        warnings.append(
            _fixture(
                "mid_qb_cannot_clear_elite_non_qb_without_edge",
                "fail",
                "A mid-rank QB exceeded elite non-QB VORP without a clear replacement edge.",
            )
        )
    else:
        warnings.append(
            _fixture(
                "mid_qb_cannot_clear_elite_non_qb_without_edge",
                "pass",
                "No QB ranked outside the top five by position exceeded elite non-QB VORP.",
            )
        )
    return tuple(warnings)


def _fixture(code: str, status: str, detail: str) -> dict[str, object]:
    severity = "info" if status == "pass" else "review"
    return _warning(
        f"fixture:{code}",
        "",
        "",
        "sanity_fixture",
        severity,
        code,
        f"{status}: {detail}",
        "Review before formula promotion.",
    )


def _warning(
    entity_key: str,
    player_name: str,
    position: str,
    warning_type: str,
    severity: str,
    warning_code: str,
    warning_detail: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "entity_key": entity_key,
        "player_name": player_name,
        "position": position,
        "warning_type": warning_type,
        "severity": severity,
        "warning_code": warning_code,
        "warning_detail": warning_detail,
        "next_action": next_action,
        "vorp_version": VORP_CORE_VERSION,
    }


def _latest_fantasy_entry(stats: object) -> dict[str, Any]:
    if not isinstance(stats, dict):
        return {}
    candidates = [
        value
        for key, value in stats.items()
        if str(key).endswith(":fantasy") and isinstance(value, dict)
    ]
    candidates = [
        candidate
        for candidate in candidates
        if isinstance(candidate.get("metrics"), dict)
    ]
    if not candidates:
        return {}
    latest_season = max(_int(candidate.get("season")) or 0 for candidate in candidates)
    latest = [
        candidate
        for candidate in candidates
        if (_int(candidate.get("season")) or 0) == latest_season
    ]
    return max(latest, key=lambda candidate: _base_scoring_points(candidate["metrics"]))


def _base_scoring_points(metrics: dict[str, Any]) -> float:
    return (
        _float(metrics.get("passing_yds")) * LVE_SCORING["passing_yard"]
        + _float(metrics.get("passing_td")) * LVE_SCORING["passing_td"]
        + _float(metrics.get("passing_int")) * LVE_SCORING["interception"]
        + _float(metrics.get("rushing_yds")) * LVE_SCORING["rushing_yard"]
        + _float(metrics.get("rushing_td")) * LVE_SCORING["rushing_td"]
        + _float(metrics.get("receiving_yds")) * LVE_SCORING["receiving_yard"]
        + _float(metrics.get("receiving_td")) * LVE_SCORING["receiving_td"]
        + _float(metrics.get("fumbles_lost")) * LVE_SCORING["fumble_lost"]
    )


def _first_down_index(
    path: Path,
    category: str,
) -> dict[tuple[str, str, int], dict[str, str]]:
    output: dict[tuple[str, str, int], dict[str, str]] = {}
    for row in _read_rows(path):
        if row.get("join_status") != "matched":
            continue
        if row.get("source_status") != "imported_real_data":
            continue
        key = (
            row.get("normalized_player_name", ""),
            row.get("position", ""),
            _int(row.get("season")) or -1,
        )
        existing = output.get(key)
        if existing:
            field = f"{category}_first_downs"
            existing[field] = str(_float(existing.get(field)) + _float(row.get(field)))
        else:
            output[key] = dict(row)
    return output


def _return_index(path: Path) -> dict[tuple[str, str, int], dict[str, str]]:
    return {
        (
            row.get("normalized_player_name", ""),
            row.get("position", ""),
            _int(row.get("season")) or -1,
        ): row
        for row in _read_rows(path)
        if row.get("join_status") == "matched"
        and row.get("scoring_role") == "small_direct_return_scoring_evidence_not_talent_signal"
    }


def _first_down_value(
    first_downs: dict[tuple[str, str, int], dict[str, str]],
    normalized_name: str,
    position: str,
    season: int | None,
    field: str,
) -> float | None:
    if season is None:
        return None
    row = first_downs.get((normalized_name, position, season))
    if not row:
        return None
    return _float(row.get(field))


def _return_points(row: dict[str, str]) -> float:
    if not row:
        return 0.0
    return (
        _float(row.get("return_yards_total")) * LVE_SCORING["return_yard"]
        + _float(row.get("return_td_total")) * LVE_SCORING["return_td"]
    )


def _first_down_status(
    rushing_fd: float | None,
    receiving_fd: float | None,
    metrics: dict[str, Any],
) -> str:
    expected_rushing = (
        _float(metrics.get("rushing_att")) > 0
        or _float(metrics.get("rushing_yds")) != 0
    )
    expected_receiving = (
        _float(metrics.get("receiving_tar")) > 0
        or _float(metrics.get("receiving_rec")) > 0
        or _float(metrics.get("receiving_yds")) != 0
    )
    imported = [rushing_fd is not None, receiving_fd is not None]
    expected = [expected_rushing, expected_receiving]
    if any(imported) and all(imported[index] or not expected[index] for index in range(2)):
        return "imported_real_data"
    if any(imported):
        return "partial_imported_real_data_missing_not_estimated"
    if any(expected):
        return "missing_imported_first_downs_not_estimated"
    return "not_applicable_no_rushing_or_receiving_role"


def _player_warning_flags(
    metrics: dict[str, Any],
    rushing_fd: float | None,
    receiving_fd: float | None,
    return_row: dict[str, str],
    stat_entry: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not stat_entry:
        warnings.append("missing_rotowire_fantasy_stats")
    status = _first_down_status(rushing_fd, receiving_fd, metrics)
    if "missing" in status:
        warnings.append("first_down_missing_not_estimated")
    if "partial" in status:
        warnings.append("partial_first_down_imported_real_data")
    if return_row:
        warnings.append("return_scoring_direct_only_not_talent_signal")
    if (_int(stat_entry.get("season")) or 0) < 2025:
        warnings.append("latest_scoring_season_before_2025")
    return warnings


def _discipline_status(
    player: _ScoredPlayer,
    vorp: float | None,
    position_rank: int | str,
) -> str:
    if vorp is None:
        return "review_missing_vorp"
    rank = _int(position_rank)
    if player.position == "QB":
        if rank and rank > 5:
            return "one_qb_mid_qb_replacement_discipline"
        if vorp < 25:
            return "one_qb_small_replacement_gap"
        return "one_qb_vorp_gap_review_only"
    if player.position == "TE":
        if vorp < 25:
            return "no_premium_te_small_replacement_gap"
        return "no_premium_te_vorp_gap_review_only"
    return "replacement_vorp_review_only"


def _first_down_component_warning(player: _ScoredPlayer) -> str:
    if "missing" in player.first_down_source_status:
        return "missing_first_downs_not_estimated_or_zero_filled"
    if "partial" in player.first_down_source_status:
        return "partial_imported_first_down_data_not_estimated"
    return ""


def _write_doc(
    path: Path,
    result: ReplacementVorpResult,
    paths: ReplacementVorpPaths,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failed_fixtures = [
        row
        for row in result.warning_rows
        if row["warning_type"] == "sanity_fixture"
        and str(row["warning_detail"]).startswith("fail:")
    ]
    review_fixtures = [
        row
        for row in result.warning_rows
        if row["warning_type"] == "sanity_fixture"
        and str(row["warning_detail"]).startswith("review:")
    ]
    lines = [
        "# Phase 11B Replacement And VORP Core",
        "",
        "## Purpose",
        "",
        (
            "Phase 11B builds the review-only 10-team, 1QB, non-PPR, "
            "first-down scoring replacement/VORP core. It does not promote app "
            "surfaces, change active rankings, alter My Team or War Board, or "
            "unlock readiness gates."
        ),
        "",
        "## Outputs",
        "",
        f"- `{paths.baselines}`",
        f"- `{paths.player_rows}`",
        f"- `{paths.component_rows}`",
        f"- `{paths.receipts}`",
        f"- `{paths.warnings}`",
        "",
        "## League Settings",
        "",
        "- 10-team dynasty.",
        "- 1QB.",
        "- Non-PPR.",
        "- Rushing and receiving first downs score 0.4 points.",
        "- No TE premium.",
        "- Return yards score 1 per 30 yards.",
        "- Return TDs score 4 points.",
        "",
        "## Replacement Defaults",
        "",
        "| Position | Required Starter Rank | Configured Replacement Rank | Note |",
        "| --- | ---: | ---: | --- |",
    ]
    for position, config in REPLACEMENT_DEFAULTS.items():
        lines.append(
            f"| {position} | {config['required_starter_rank']} | "
            f"{config['configured_replacement_rank']} | {config['lineup_assumption']} |"
        )
    lines.extend(
        [
            "",
            "The admitted NFL current evidence matrix is thinner than a full league "
            "pool for QB, RB, and TE, so those positions visibly use the last "
            "available admitted player when the configured replacement rank exceeds "
            "the admitted pool count.",
            "",
            "## Source Rules",
            "",
            "- Phase 11A allowed-field registry is enforced before building outputs.",
            "- No market, projection, ADP, ranking, mock, or big-board fields are consumed.",
            "- First downs come only from admitted matched-only first-down views.",
            "- Missing first downs are not estimated and are not labeled as direct data.",
            "- Return production is direct scoring only, not talent or role signal.",
            "- Review-only prior VORP context is not consumed.",
            "",
            "## Summary",
            "",
            f"- Player rows: {result.summary['player_rows']}",
            f"- Baseline rows: {result.summary['baseline_rows']}",
            f"- Component rows: {result.summary['component_rows']}",
            f"- Receipt rows: {result.summary['receipt_rows']}",
            f"- Warning rows: {result.summary['warning_rows']}",
            f"- Market rows used: {result.summary['market_rows_used']}",
            f"- Projection rows used: {result.summary['projection_rows_used']}",
            f"- Failed sanity fixtures: {len(failed_fixtures)}",
            f"- Review sanity fixtures: {len(review_fixtures)}",
            "",
            "## Safety Confirmations",
            "",
            "- Review-only outputs.",
            "- No active rankings changed.",
            "- No app promotion.",
            "- No readiness unlock.",
            "- No My Team or War Board changes.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(
    path: Path,
    header: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _json_obj(value: object) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _top_vorp(rows: list[dict[str, object]]) -> float:
    return max((_float(row.get("vorp_points")) for row in rows), default=0.0)


def _none_as_zero(value: float | None) -> float:
    return value if value is not None else 0.0


def _round(value: object) -> float | str:
    if value is None or value == "":
        return ""
    return round(_float(value), 4)


def _float(value: object) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(str(value))
    except ValueError:
        return 0.0


def _int(value: object) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(str(value)))
    except ValueError:
        return None
