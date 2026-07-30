"""Governed 2026 input reconstruction and review-only Model V4 execution.

This module is an adapter around the existing Sprint 12/13 and Sprint 14E
public builders.  It does not implement or tune a rookie scoring formula.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.model_v4_confidence_missingness_service import (
    CONFIDENCE_RECEIPT_HEADER,
    CONFIDENCE_REVIEW_HEADER,
    CONFIDENCE_WARNING_HEADER,
    build_confidence_missingness_layer,
)
from src.services.model_v4_draft_capital_snapshot_service import DRAFT_CAPITAL_HEADER
from src.services.model_v4_evidence_matrix_service import (
    BACKTEST_MATRIX_HEADER,
    COVERAGE_HEADER,
    NFL_MATRIX_HEADER,
    PROSPECT_MATRIX_HEADER,
)
from src.services.model_v4_evidence_matrix_service import (
    WARNING_HEADER as MATRIX_WARNING_HEADER,
)
from src.services.model_v4_rookie_age_intake_service import ROOKIE_AGE_HEADER
from src.services.model_v4_sprint12_13_review_service import (
    COMPONENT_HEADER as SPRINT_COMPONENT_HEADER,
)
from src.services.model_v4_sprint12_13_review_service import (
    PROSPECT_REVIEW_HEADER,
    SPRINT_12_13_VERSION,
    build_sprint12_13_review_outputs,
)
from src.services.model_v4_sprint12_13_review_service import (
    RECEIPT_HEADER as SPRINT_RECEIPT_HEADER,
)
from src.services.model_v4_sprint12_13_review_service import (
    WARNING_HEADER as SPRINT_WARNING_HEADER,
)
from src.services.model_v4_sprint14e_rookie_draft_review_service import (
    POSITION_FORMAT_FACTORS,
    SPRINT_14E_VERSION,
    build_rookie_draft_review_outputs,
)
from src.services.model_v4_sprint14e_rookie_draft_review_service import (
    ROOKIE_BOARD_HEADER as SPRINT14E_BOARD_HEADER,
)

INPUT_PACK_VERSION = "MODEL_V4_2026_COMPATIBLE_INPUT_PACK_V1"
BOARD_VERSION = "NWR_MODEL_V4_2026_ROOKIE_BOARD_REVIEW_V1"
SCORE_LABEL = "Rookie Analyzer Review Score"
RANK_LABEL = "2026 Rookie Review Rank"
BOARD_LABEL = "Review-Only"

CORE_POSITIONS = {"QB", "RB", "WR", "TE"}
CFBD_POSITION_MAP = {
    "Quarterback": "QB",
    "Running Back": "RB",
    "Wide Receiver": "WR",
    "Tight End": "TE",
}
CFBD_STATS = {
    ("passing", "YDS"): "passing_yards",
    ("passing", "TD"): "passing_tds",
    ("rushing", "YDS"): "rushing_yards",
    ("rushing", "TD"): "rushing_tds",
    ("receiving", "REC"): "receptions",
    ("receiving", "YDS"): "receiving_yards",
    ("receiving", "TD"): "receiving_tds",
}
FORMULA_WEIGHTS = {
    "production": 0.30,
    "market_share": 0.20,
    "draft_capital": 0.25,
    "athletic_prior": 0.12,
    "recruiting_prior": 0.05,
    "age_lifecycle": 0.08,
}
EXPECTED_BLOCKERS = {
    "De'Zhaun Stribling",
    "Carson Beck",
    "Oscar Delp",
    "Colbie Young",
    "Nicholas Singleton",
    "Joe Royer",
    "Deion Burks",
}
SELECTION_DATES = {
    1: date(2026, 4, 23),
    2: date(2026, 4, 24),
    3: date(2026, 4, 24),
    4: date(2026, 4, 25),
    5: date(2026, 4, 25),
    6: date(2026, 4, 25),
    7: date(2026, 4, 25),
}

BOARD_HEADER = (
    "player_id",
    "player_name",
    "position",
    "nfl_team",
    "college",
    "draft_round",
    "overall_pick",
    "age_at_draft",
    "identity_status",
    "identity_method",
    "production_component",
    "market_share_component",
    "draft_capital_component",
    "athletic_component",
    "recruiting_component",
    "age_component",
    "weighted_component_sum",
    "raw_model_v4_score",
    "confidence_cap",
    "final_review_score",
    "sprint14e_format_score",
    "position_rank",
    "overall_review_rank",
    "tier",
    "floor_anchor_cap_states",
    "missing_components",
    "warning_codes",
    "evidence_confidence",
    "source_limit_state",
    "blocking_reason",
    "score_label",
    "rank_label",
    "board_label",
    "formula_version",
    "board_formula_version",
    "input_pack_version",
    "board_version",
)


class RookieBoardReconstructionError(RuntimeError):
    """A source, identity, formula-freeze, or review-board gate failed."""


@dataclass(frozen=True)
class ReconstructionResult:
    run_root: Path
    input_root: Path
    analyzer_root: Path
    board_path: Path
    board_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    confidence_rows: tuple[dict[str, object], ...]
    prospect_matrix_rows: tuple[dict[str, object], ...]
    coverage_rows: tuple[dict[str, object], ...]
    blocker_rows: tuple[dict[str, object], ...]
    sprint14e_rows: tuple[dict[str, object], ...]
    governed_digest: str


def execute_review_build(
    *,
    repo_root: str | Path,
    config_path: str | Path,
    run_root: str | Path,
) -> ReconstructionResult:
    """Reconstruct inputs and invoke the existing analyzer layers."""
    repo = Path(repo_root).resolve()
    config = _read_json(Path(config_path))
    root = Path(run_root).resolve()
    assert_output_root_safe(root)
    _validate_config(config)
    sources = _load_sources(repo, config)
    inputs = root / "compatible_input_pack"
    analyzer = root / "analyzer_outputs"
    inputs.mkdir(parents=True, exist_ok=True)
    analyzer.mkdir(parents=True, exist_ok=True)

    college = _build_college_profiles(sources["exact"], sources["cfbd_root"])
    matrix_rows, coverage_rows, warning_rows = _build_prospect_inputs(
        sources, college, config
    )
    _validate_input_rows(matrix_rows, sources["exact"])
    paths = _write_input_pack(
        inputs,
        matrix_rows,
        coverage_rows,
        warning_rows,
        sources,
        config,
    )

    confidence = build_confidence_missingness_layer(
        nfl_matrix_path=paths["nfl_matrix"],
        admitted_prospect_matrix_path=paths["prospect_matrix"],
        historical_backtest_matrix_path=paths["historical_matrix"],
        source_coverage_matrix_path=paths["coverage"],
        warning_matrix_path=paths["warnings"],
    )
    confidence_path = analyzer / "confidence_missingness_review_rows.csv"
    _write_csv(confidence_path, CONFIDENCE_REVIEW_HEADER, confidence.review_rows)
    _write_csv(
        analyzer / "confidence_missingness_receipts.csv",
        CONFIDENCE_RECEIPT_HEADER,
        confidence.receipt_rows,
    )
    _write_csv(
        analyzer / "confidence_missingness_warnings.csv",
        CONFIDENCE_WARNING_HEADER,
        confidence.warning_rows,
    )

    sprint = build_sprint12_13_review_outputs(
        admitted_prospect_matrix_path=paths["prospect_matrix"],
        confidence_rows_path=confidence_path,
        rookie_age_rows_path=paths["age"],
        draft_capital_rows_path=paths["draft_capital"],
        current_value_rows_path=paths["empty_current"],
        current_component_rows_path=paths["empty_components"],
        current_receipt_rows_path=paths["empty_receipts"],
        current_warning_rows_path=paths["empty_warnings"],
    )
    prospect_path = analyzer / "prospect_value_review_rows.csv"
    _write_csv(prospect_path, PROSPECT_REVIEW_HEADER, sprint.prospect_rows)
    _write_csv(
        analyzer / "prospect_value_component_rows.csv",
        SPRINT_COMPONENT_HEADER,
        sprint.prospect_component_rows,
    )
    _write_csv(
        analyzer / "prospect_value_receipts.csv",
        SPRINT_RECEIPT_HEADER,
        sprint.prospect_receipt_rows,
    )
    _write_csv(
        analyzer / "prospect_value_warnings.csv",
        SPRINT_WARNING_HEADER,
        sprint.prospect_warning_rows,
    )

    sprint14 = build_rookie_draft_review_outputs(
        prospect_rows_path=prospect_path,
        pick_inventory_path=paths["empty_picks"],
        roster_state_path=paths["empty_roster"],
    )
    _write_csv(
        analyzer / "sprint14e_rookie_draft_board_review_rows.csv",
        SPRINT14E_BOARD_HEADER,
        sprint14.rookie_board_rows,
    )

    board_rows = _build_complete_board(
        sources=sources,
        prospect_rows=sprint.prospect_rows,
        component_rows=sprint.prospect_component_rows,
        sprint14e_rows=sprint14.rookie_board_rows,
    )
    _validate_complete_board(
        board_rows,
        exact=sources["exact"],
        blockers=sources["blocked"],
        component_rows=sprint.prospect_component_rows,
        sprint14e_rows=sprint14.rookie_board_rows,
    )
    board_path = root / "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv"
    _write_csv(board_path, BOARD_HEADER, board_rows)
    digest = _governed_digest(
        [
            paths["prospect_matrix"],
            paths["age"],
            paths["draft_capital"],
            confidence_path,
            prospect_path,
            analyzer / "prospect_value_component_rows.csv",
            analyzer / "sprint14e_rookie_draft_board_review_rows.csv",
            board_path,
        ]
    )
    receipt = {
        "board_version": BOARD_VERSION,
        "input_pack_version": INPUT_PACK_VERSION,
        "sprint_12_13_version": SPRINT_12_13_VERSION,
        "sprint_14e_version": SPRINT_14E_VERSION,
        "drafted_rows": 80,
        "exact_rows": 73,
        "blocked_rows": 7,
        "governed_digest": digest,
        "provider_calls": 0,
        "formula_changes": "NONE",
    }
    (root / "DETERMINISTIC_RUN_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return ReconstructionResult(
        run_root=root,
        input_root=inputs,
        analyzer_root=analyzer,
        board_path=board_path,
        board_rows=tuple(board_rows),
        component_rows=tuple(sprint.prospect_component_rows),
        confidence_rows=tuple(confidence.review_rows),
        prospect_matrix_rows=tuple(matrix_rows),
        coverage_rows=tuple(coverage_rows),
        blocker_rows=tuple(sources["blocked"]),
        sprint14e_rows=tuple(sprint14.rookie_board_rows),
        governed_digest=digest,
    )


def _validate_config(config: dict[str, Any]) -> None:
    if config.get("input_pack_version") != INPUT_PACK_VERSION:
        raise RookieBoardReconstructionError("input-pack version drift")
    if config.get("board_version") != BOARD_VERSION:
        raise RookieBoardReconstructionError("board version drift")
    if config.get("draft_class_year") != 2026:
        raise RookieBoardReconstructionError("draft class is not 2026")
    if config.get("formula_freeze") != FORMULA_WEIGHTS:
        raise RookieBoardReconstructionError("Model V4 component weight drift")
    if config.get("format_factors") != POSITION_FORMAT_FACTORS:
        raise RookieBoardReconstructionError("Sprint 14E format factor drift")
    analyzers = config.get("analyzers", {})
    if analyzers.get("sprint_12_13_version") != SPRINT_12_13_VERSION:
        raise RookieBoardReconstructionError("Sprint 12/13 version drift")
    if analyzers.get("sprint_14e_version") != SPRINT_14E_VERSION:
        raise RookieBoardReconstructionError("Sprint 14E version drift")
    cfbd = config.get("cfbd", {})
    if set(cfbd.get("forbidden_scoring_families", [])) != {
        "player_ppa",
        "player_usage",
    }:
        raise RookieBoardReconstructionError("CFBD scoring-family prohibition drift")


def _load_sources(repo: Path, config: dict[str, Any]) -> dict[str, Any]:
    nflverse = config["nflverse"]
    roots = {
        "draft": Path(nflverse["draft_picks_root"]),
        "combine": Path(nflverse["combine_root"]),
        "players": Path(nflverse["players_root"]),
    }
    for key, expected in (
        ("draft", nflverse["draft_picks_aggregate_sha256"]),
        ("combine", nflverse["combine_aggregate_sha256"]),
        ("players", nflverse["players_aggregate_sha256"]),
    ):
        _validate_manifest(roots[key] / "COMPLETION_MANIFEST.json", expected)
    cfbd_root = Path(config["cfbd"]["snapshot_root"])
    _validate_manifest(
        cfbd_root / "COMPLETION_MANIFEST.json", config["cfbd"]["aggregate_sha256"]
    )

    draft = pd.read_parquet(roots["draft"] / "raw" / "draft_picks.parquet")
    combine = pd.read_parquet(roots["combine"] / "raw" / "combine.parquet")
    players = pd.read_parquet(roots["players"] / "raw" / "players.parquet")
    drafted = draft.loc[
        draft["season"].eq(2026) & draft["position"].isin(CORE_POSITIONS)
    ].copy()
    drafted = drafted.sort_values("pick", kind="stable").reset_index(drop=False)
    if len(drafted) != 80:
        raise RookieBoardReconstructionError(
            f"expected 80 drafted skill players, found {len(drafted)}"
        )

    identity = config["identity"]
    exact_source = _read_csv(repo / identity["exact_crosswalk"])
    blocked_source = _read_csv(repo / identity["unresolved_inventory"])
    exact_rows = [
        row
        for row in exact_source
        if row.get("source_dataset") == "draft_picks"
        and _int(row.get("draft_year")) == 2026
        and row.get("position") in CORE_POSITIONS
    ]
    blocked_rows = [
        row
        for row in blocked_source
        if row.get("source_dataset") == "draft_picks"
        and _int(row.get("draft_year")) == 2026
        and row.get("position") in CORE_POSITIONS
    ]
    if len(exact_rows) != 73 or len(blocked_rows) != 7:
        raise RookieBoardReconstructionError(
            f"identity partition drift: {len(exact_rows)} exact/{len(blocked_rows)} blocked"
        )
    if {row["player_name"] for row in blocked_rows} != EXPECTED_BLOCKERS:
        raise RookieBoardReconstructionError("known blocked identity set drift")
    if any(row.get("name_used_as_identity", "").lower() != "false" for row in exact_rows):
        raise RookieBoardReconstructionError("name-only identity entered exact crosswalk")

    drafted_by_source = {str(row["index"]): row for _, row in drafted.iterrows()}
    exact: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for authority_row, target in (
        *((row, exact) for row in exact_rows),
        *((row, blocked) for row in blocked_rows),
    ):
        source_row = drafted_by_source.get(str(_int(authority_row["source_row"])))
        if source_row is None:
            raise RookieBoardReconstructionError("crosswalk source row not in 2026 class")
        source_id = _text(source_row.get("gsis_id"))
        if target is exact and source_id != authority_row.get("gsis_id"):
            raise RookieBoardReconstructionError("exact GSIS identity disagrees with source row")
        if target is blocked and source_id:
            raise RookieBoardReconstructionError("blocked row unexpectedly has source GSIS ID")
        record = {
            "player_id": source_id,
            "player_name": _text(source_row.get("pfr_player_name")),
            "position": _text(source_row.get("position")),
            "nfl_team": _text(source_row.get("team")),
            "college": _text(source_row.get("college")),
            "draft_year": int(source_row["season"]),
            "draft_round": int(source_row["round"]),
            "overall_pick": int(source_row["pick"]),
            "pfr_player_id": _text(source_row.get("pfr_player_id")),
            "cfb_player_id": _text(source_row.get("cfb_player_id")),
            "source_row": int(source_row["index"]),
            "identity_method": (
                "EXACT_SHARED_GSIS_ID" if target is exact else "UNRESOLVED_SOURCE_GSIS_ID"
            ),
            "name_used_as_identity": False,
        }
        target.append(record)
    exact.sort(key=lambda row: row["overall_pick"])
    blocked.sort(key=lambda row: row["overall_pick"])
    if len({row["player_id"] for row in exact}) != 73:
        raise RookieBoardReconstructionError("exact player IDs are blank or duplicated")

    players_by_pfr = {
        _text(row.get("pfr_id")): row
        for _, row in players.iterrows()
        if _text(row.get("pfr_id"))
    }
    combine_2026 = combine.loc[combine["season"].eq(2026)].copy()
    combine_by_pfr = {
        _text(row.get("pfr_id")): row
        for _, row in combine_2026.iterrows()
        if _text(row.get("pfr_id"))
    }
    for row in exact:
        player = players_by_pfr.get(row["pfr_player_id"])
        if player is None or not _text(player.get("birth_date")):
            raise RookieBoardReconstructionError(
                f"exact birth authority missing for {row['player_id']}"
            )
        row["birth_date"] = _text(player.get("birth_date"))
        row["combine"] = combine_by_pfr.get(row["pfr_player_id"])
    return {
        "exact": exact,
        "blocked": blocked,
        "drafted": drafted,
        "cfbd_root": cfbd_root,
        "roots": roots,
        "config": config,
    }


def _build_college_profiles(
    exact: list[dict[str, Any]], cfbd_root: Path
) -> dict[str, dict[str, Any]]:
    draft_rows = _read_json(cfbd_root / "raw" / "draft_picks" / "2026.json")
    slot_map: dict[tuple[int, int, int], dict[str, Any]] = {}
    for row in draft_rows:
        slot = (_int(row.get("year")), _int(row.get("round")), _int(row.get("overall")))
        if slot in slot_map:
            raise RookieBoardReconstructionError("CFBD draft slot is not unique")
        slot_map[slot] = row
    athlete_to_player: dict[str, str] = {}
    for row in exact:
        slot = (2026, row["draft_round"], row["overall_pick"])
        cfbd = slot_map.get(slot)
        athlete_id = _id(cfbd.get("collegeAthleteId")) if cfbd else ""
        if not athlete_id:
            continue
        if CFBD_POSITION_MAP.get(_text(cfbd.get("position"))) != row["position"]:
            raise RookieBoardReconstructionError(
                f"CFBD position disagreement at draft slot {slot}"
            )
        if athlete_id in athlete_to_player:
            raise RookieBoardReconstructionError("CFBD athlete ID maps to multiple players")
        athlete_to_player[athlete_id] = row["player_id"]
        row["cfbd_college_athlete_id"] = athlete_id
        row["cfbd_identity_method"] = (
            "CFBD_AND_NFLVERSE_UNIQUE_DRAFT_YEAR_ROUND_OVERALL"
        )

    denominators: dict[tuple[int, str, str], float] = defaultdict(float)
    player_stats: dict[tuple[str, int, str, str], float] = defaultdict(float)
    stat_root = cfbd_root / "raw" / "player_season_stats"
    for path in sorted(stat_root.glob("*.json"), key=lambda item: item.name):
        for stat in _read_json(path):
            feature = CFBD_STATS.get((stat.get("category"), stat.get("statType")))
            if not feature:
                continue
            season = _int(stat.get("season"))
            if season >= 2026:
                raise RookieBoardReconstructionError("future college season entered input")
            value = _number(stat.get("stat"))
            team = _text(stat.get("team"))
            if value is None or not team:
                continue
            denominators[(season, team, feature)] += value
            player_id = athlete_to_player.get(_id(stat.get("playerId")))
            if player_id:
                player_stats[(player_id, season, team, feature)] += value

    by_player: dict[str, dict[int, dict[str, Any]]] = defaultdict(
        lambda: defaultdict(lambda: {"values": defaultdict(float), "teams": defaultdict(set)})
    )
    for (player_id, season, team, feature), value in player_stats.items():
        by_player[player_id][season]["values"][feature] += value
        by_player[player_id][season]["teams"][feature].add(team)
    profiles: dict[str, dict[str, Any]] = {}
    for row in exact:
        seasons = by_player.get(row["player_id"], {})
        if not seasons:
            profiles[row["player_id"]] = {}
            continue
        season_rows: dict[int, dict[str, Any]] = {}
        for season, payload in seasons.items():
            values = dict(payload["values"])
            shares: dict[str, float | None] = {}
            for feature, numerator in values.items():
                denominator = sum(
                    denominators.get((season, team, feature), 0.0)
                    for team in payload["teams"][feature]
                )
                shares[feature] = (
                    round(numerator / denominator, 8) if denominator > 0 else None
                )
            season_rows[season] = {"values": values, "shares": shares}
        latest_season = max(season_rows)
        latest = season_rows[latest_season]

        def career(
            feature: str, season_payloads: dict[int, dict[str, Any]] = season_rows
        ) -> float | None:
            values = [
                payload["values"].get(feature)
                for payload in season_payloads.values()
                if payload["values"].get(feature) is not None
            ]
            return round(sum(values), 4) if values else None

        def max_share(
            feature: str, season_payloads: dict[int, dict[str, Any]] = season_rows
        ) -> float | None:
            values = [
                payload["shares"].get(feature)
                for payload in season_payloads.values()
                if payload["shares"].get(feature) is not None
            ]
            return round(max(values), 8) if values else None

        profiles[row["player_id"]] = {
            "latest_season": latest_season,
            "latest": latest,
            "career": {
                feature: career(feature)
                for feature in (
                    "passing_yards",
                    "rushing_yards",
                    "receiving_yards",
                )
            },
            "max_share": {
                feature: max_share(feature)
                for feature in (
                    "passing_yards",
                    "passing_tds",
                    "rushing_yards",
                    "rushing_tds",
                    "receiving_yards",
                    "receiving_tds",
                    "receptions",
                )
            },
        }
    return profiles


def _build_prospect_inputs(
    sources: dict[str, Any],
    college: dict[str, dict[str, Any]],
    config: dict[str, Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    coverage: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    nfl_receipts = {
        "draft_capital": (
            f"nflverse:draft_picks:{config['nflverse']['draft_picks_aggregate_sha256']}"
        ),
        "rookie_age": f"nflverse:players:{config['nflverse']['players_aggregate_sha256']}",
        "workouts": f"nflverse:combine:{config['nflverse']['combine_aggregate_sha256']}",
        "recruiting_profile": "governed_source_absent:missing_not_zero",
        "college_production": f"cfbd:rest_v2:{config['cfbd']['aggregate_sha256']}",
        "college_targets": "governed_target_source_absent:missing_not_zero",
        "college_market_share": f"cfbd:rest_v2:{config['cfbd']['aggregate_sha256']}",
    }
    for exact in sources["exact"]:
        player_id = exact["player_id"]
        profile = college.get(player_id, {})
        factual, derived = _college_formula_payload(profile)
        workout = _workout_payload(exact.get("combine"))
        prior = {
            "workout_profile": workout,
            "recruiting_profile": {},
        }
        warning_codes = ["missing_recruiting_prior"]
        if not workout:
            warning_codes.append("missing_combine_evidence")
        else:
            warning_codes.append("combine_percentile_normalization_not_governed")
        if not factual:
            warning_codes.append("missing_college_production")
        if not derived:
            warning_codes.append("missing_college_market_share")
        row = {
            "canonical_prospect_key": player_id,
            "prospect_name": exact["player_name"],
            "normalized_player_name": _normalize_name(exact["player_name"]),
            "position": exact["position"],
            "college": exact["college"],
            "nfl_team": exact["nfl_team"],
            "draft_year": "2026",
            "identity_status": "exact_provider_gsis_id",
            "formula_identity_admitted": "true",
            "factual_evidence_json": _json_text(factual),
            "derived_evidence_json": _json_text(derived),
            "prospect_prior_evidence_json": _json_text(prior),
            "context_fields_json": _json_text(
                {
                    "nfl_depth_chart": {
                        "team": exact["nfl_team"],
                        "depth_rank": None,
                        "source_status": "admitted_draft_team_landing_context_only",
                    }
                }
            ),
            "market_context_fields_json": "{}",
            "source_status_json": _json_text(
                {
                    "identity": "exact_shared_gsis_id",
                    "draft": "admitted_nflverse_snapshot",
                    "age": "admitted_nflverse_players_birth_date",
                    "combine": (
                        "admitted_nflverse_raw_measurements_no_percentile_substitution"
                        if workout
                        else "missing_not_zero"
                    ),
                    "college": (
                        "reviewed_cfbd_exact_draft_slot_temporally_valid"
                        if profile
                        else "missing_not_zero"
                    ),
                    "recruiting": "missing_not_zero",
                }
            ),
            "receipt_pointers_json": _json_text(nfl_receipts),
            "warning_flags": "|".join(warning_codes),
            "excluded_reason": "",
            "matrix_version": INPUT_PACK_VERSION,
        }
        rows.append(row)
        present_by_group = {
            "college_production": bool(factual),
            "college_market_share": bool(derived),
            "prospect_prior": bool(workout),
            "source_limited_combine": bool(workout),
        }
        for feature_group, present in present_by_group.items():
            coverage.append(
                {
                    "matrix_name": "admitted_prospect_current_feature_matrix",
                    "entity_key": player_id,
                    "entity_name": exact["player_name"],
                    "entity_type": "current_prospect",
                    "position": exact["position"],
                    "feature_group": feature_group,
                    "lane": "compatible_2026_reconstruction",
                    "source_status": (
                        "formula_admitted_after_validation" if present else "missing_not_zero"
                    ),
                    "present": str(present).lower(),
                    "row_count": 1 if present else 0,
                    "latest_season": profile.get("latest_season", ""),
                    "source_files": (
                        "immutable_nflverse_and_reviewed_cfbd_snapshots"
                    ),
                    "receipt_pointer": (
                        nfl_receipts["workouts"]
                        if "combine" in feature_group
                        else nfl_receipts["college_production"]
                    ),
                    "warnings": "" if present else f"missing_{feature_group}",
                    "matrix_version": INPUT_PACK_VERSION,
                }
            )
        for code in warning_codes:
            warnings.append(
                {
                    "matrix_name": "admitted_prospect_current_feature_matrix",
                    "entity_key": player_id,
                    "entity_name": exact["player_name"],
                    "entity_type": "current_prospect",
                    "position": exact["position"],
                    "feature_group": (
                        "recruiting"
                        if "recruiting" in code
                        else "combine"
                        if "combine" in code
                        else "college"
                    ),
                    "severity": "review",
                    "warning_code": code,
                    "warning_detail": code.replace("_", " "),
                    "source_status": "missing_not_zero_or_source_limited",
                    "next_action": "Retain missingness and existing confidence behavior.",
                    "matrix_version": INPUT_PACK_VERSION,
                }
            )
    return rows, coverage, warnings


def _college_formula_payload(
    profile: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not profile:
        return {}, {}
    latest = profile["latest"]["values"]
    shares = profile["latest"]["shares"]
    career = profile["career"]
    max_share = profile["max_share"]
    factual = {
        "college_production_summary": {
            "passing": {
                "max_passing_yard_share": max_share.get("passing_yards"),
                "max_passing_td_share": max_share.get("passing_tds"),
                "career_yards": career.get("passing_yards"),
            },
            "rushing": {
                "max_rushing_yard_share": max_share.get("rushing_yards"),
                "max_rushing_td_share": max_share.get("rushing_tds"),
                "career_yards": career.get("rushing_yards"),
            },
            "receiving": {
                "max_receiving_yard_share": max_share.get("receiving_yards"),
                "max_receiving_td_share": max_share.get("receiving_tds"),
                "max_reception_share": max_share.get("receptions"),
                "career_yards": career.get("receiving_yards"),
            },
        },
        "college_season_latest": {
            "season": profile["latest_season"],
            "passing_yards": latest.get("passing_yards"),
            "rushing_yards": latest.get("rushing_yards"),
            "receiving_yards": latest.get("receiving_yards"),
        },
        "college_targets_latest": {},
    }
    derived = {
        "college_market_share": {
            "passing": {
                "passing_yard_share": shares.get("passing_yards"),
                "passing_td_share": shares.get("passing_tds"),
            },
            "rushing": {
                "rushing_yard_share": shares.get("rushing_yards"),
                "rushing_td_share": shares.get("rushing_tds"),
            },
            "receiving": {
                "receiving_yard_share": shares.get("receiving_yards"),
                "receiving_td_share": shares.get("receiving_tds"),
                "reception_share": shares.get("receptions"),
            },
        },
        "college_team_context": {
            "denominator_contract": "sum_selected_player_stats_by_exact_season_team_stat",
        },
    }
    return factual, derived


def _workout_payload(row: Any) -> dict[str, Any]:
    if row is None or not hasattr(row, "get"):
        return {}
    measurements = {
        "height": _nullable(row.get("ht")),
        "height_inches": _nullable(row.get("ht")),
        "weight": _nullable(row.get("wt")),
        "forty": _nullable(row.get("forty")),
        "bench": _nullable(row.get("bench")),
        "vertical": _nullable(row.get("vertical")),
        "broad": _nullable(row.get("broad_jump")),
        "cone": _nullable(row.get("cone")),
        "shuttle": _nullable(row.get("shuttle")),
        "forty_pct": None,
        "broad_pct": None,
        "vertical_pct": None,
        "cone_pct": None,
    }
    if not any(
        measurements.get(field) is not None
        for field in ("weight", "forty", "bench", "vertical", "broad", "cone", "shuttle")
    ):
        return {}
    return measurements


def _write_input_pack(
    root: Path,
    matrix_rows: list[dict[str, object]],
    coverage_rows: list[dict[str, object]],
    warning_rows: list[dict[str, object]],
    sources: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Path]:
    paths = {
        "prospect_matrix": root / "admitted_prospect_current_feature_matrix.csv",
        "coverage": root / "source_coverage_matrix.csv",
        "warnings": root / "warning_matrix.csv",
        "nfl_matrix": root / "nfl_player_current_evidence_matrix.csv",
        "historical_matrix": root / "historical_rookie_backtest_feature_matrix.csv",
        "age": root / "player_age_2026.csv",
        "draft_capital": root / "rookie_draft_capital_2026.csv",
        "empty_current": root / "empty_current_player_value_review_rows.csv",
        "empty_components": root / "empty_current_player_value_component_rows.csv",
        "empty_receipts": root / "empty_current_player_value_receipts.csv",
        "empty_warnings": root / "empty_current_player_value_warnings.csv",
        "empty_picks": root / "empty_pick_inventory.csv",
        "empty_roster": root / "empty_roster_state.csv",
    }
    _write_csv(paths["prospect_matrix"], PROSPECT_MATRIX_HEADER, matrix_rows)
    _write_csv(paths["coverage"], COVERAGE_HEADER, coverage_rows)
    _write_csv(paths["warnings"], MATRIX_WARNING_HEADER, warning_rows)
    _write_csv(paths["nfl_matrix"], NFL_MATRIX_HEADER, [])
    _write_csv(paths["historical_matrix"], BACKTEST_MATRIX_HEADER, [])

    age_rows: list[dict[str, object]] = []
    draft_rows: list[dict[str, object]] = []
    for index, row in enumerate(sources["exact"], start=1):
        birthday = date.fromisoformat(row["birth_date"][:10])
        selected = SELECTION_DATES[row["draft_round"]]
        age_decimal = round((selected - birthday).days / 365.2425, 6)
        total_months = round(age_decimal * 12)
        age_rows.append(
            {
                "source_row": index,
                "player": row["player_name"],
                "normalized_player_name": _normalize_name(row["player_name"]),
                "nfl_team": row["nfl_team"],
                "position": row["position"],
                "position_rank_text": "",
                "age_years": int(total_months // 12),
                "age_month_remainder": int(total_months % 12),
                "age_total_months": total_months,
                "age_years_decimal": age_decimal,
                "source_status": "admitted_nflverse_birth_date_exact_pfr_crosswalk",
                "allowed_use": "prospect_lifecycle_age_evidence_not_ranking_input",
                "warning_flags": "",
            }
        )
        draft_rows.append(
            {
                "source": "admitted nflverse immutable draft_picks snapshot",
                "source_file": (
                    f"aggregate:{config['nflverse']['draft_picks_aggregate_sha256']}"
                ),
                "collected_at_utc": "2026-07-30T07:24:07Z",
                "draft_year": "2026",
                "round": row["draft_round"],
                "overall_pick": row["overall_pick"],
                "draft_day": 1 if row["draft_round"] == 1 else 2 if row["draft_round"] <= 3 else 3,
                "player": row["player_name"],
                "normalized_player_name": _normalize_name(row["player_name"]),
                "source_status": "admitted_primary_source_exact_gsis_identity",
                "allowed_use": "prospect_prior_draft_capital_after_identity_validation",
            }
        )
    _write_csv(paths["age"], ROOKIE_AGE_HEADER, age_rows)
    _write_csv(paths["draft_capital"], DRAFT_CAPITAL_HEADER, draft_rows)
    _write_csv(paths["empty_current"], ("canonical_player_key",), [])
    _write_csv(paths["empty_components"], ("canonical_player_key",), [])
    _write_csv(paths["empty_receipts"], ("canonical_player_key",), [])
    _write_csv(paths["empty_warnings"], ("entity_key",), [])
    _write_csv(paths["empty_picks"], ("pick_review_key",), [])
    _write_csv(paths["empty_roster"], ("position",), [])

    receipt = {
        "input_pack_version": INPUT_PACK_VERSION,
        "reconstruction_status": "COMPATIBLE_2026_RECONSTRUCTION_REQUIRED",
        "exact_rows": 73,
        "blocked_rows": 7,
        "identity_method": "exact GSIS plus authoritative unique draft-slot CFBD crosswalk",
        "temporal_boundary": "college seasons strictly before 2026 draft",
        "missingness": "missing remains null/blank and enters existing confidence contract",
        "nflverse": config["nflverse"],
        "cfbd": config["cfbd"],
    }
    (root / "INPUT_PACK_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return paths


def _build_complete_board(
    *,
    sources: dict[str, Any],
    prospect_rows: Iterable[dict[str, object]],
    component_rows: Iterable[dict[str, object]],
    sprint14e_rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    prospects = {str(row["canonical_prospect_key"]): row for row in prospect_rows}
    format_rows = {str(row["rookie_board_key"]): row for row in sprint14e_rows}
    component_index: dict[str, dict[str, dict[str, object]]] = defaultdict(dict)
    for row in component_rows:
        if row.get("component_layer") != "prospect_prior":
            continue
        component_index[str(row["entity_key"])][str(row["component_name"])] = row
    rows: list[dict[str, object]] = []
    for source in sources["exact"]:
        key = source["player_id"]
        prospect = prospects[key]
        formatted = format_rows[key]
        components = component_index[key]
        values = {
            name: _blank_or_float(prospect.get(column))
            for name, column in (
                ("production", "production_score"),
                ("market_share", "market_share_score"),
                ("draft_capital", "draft_capital_score"),
                ("athletic_prior", "athletic_prior_score"),
                ("recruiting_prior", "recruiting_prior_score"),
                ("age_lifecycle", "age_lifecycle_score"),
            )
        }
        missing = [name for name, value in values.items() if value == ""]
        contribution_sum = round(
            sum(
                float(row["weighted_contribution"])
                for row in components.values()
                if row.get("weighted_contribution") not in ("", None)
            ),
            4,
        )
        available_weight = float(prospect["component_weight_available"])
        weighted_mean = (
            round(contribution_sum / available_weight, 4) if available_weight else ""
        )
        confidence_cap = float(prospect["confidence_cap"])
        final_score = float(prospect["prospect_private_value_review_score"])
        raw_score = round(final_score / confidence_cap, 4)
        birthday = date.fromisoformat(source["birth_date"][:10])
        selected = SELECTION_DATES[source["draft_round"]]
        age_decimal = round((selected - birthday).days / 365.2425, 6)
        warning_codes = _split_flags(prospect.get("warning_flags"))
        rows.append(
            {
                "player_id": key,
                "player_name": source["player_name"],
                "position": source["position"],
                "nfl_team": source["nfl_team"],
                "college": source["college"],
                "draft_round": source["draft_round"],
                "overall_pick": source["overall_pick"],
                "age_at_draft": age_decimal,
                "identity_status": "EXACT_IDENTITY_PARTIAL_EVIDENCE",
                "identity_method": "EXACT_SHARED_GSIS_ID",
                "production_component": values["production"],
                "market_share_component": values["market_share"],
                "draft_capital_component": values["draft_capital"],
                "athletic_component": values["athletic_prior"],
                "recruiting_component": values["recruiting_prior"],
                "age_component": values["age_lifecycle"],
                "weighted_component_sum": weighted_mean,
                "raw_model_v4_score": raw_score,
                "confidence_cap": confidence_cap,
                "final_review_score": final_score,
                "sprint14e_format_score": formatted["league_format_adjusted_score"],
                "position_rank": 0,
                "overall_review_rank": formatted["board_rank"],
                "tier": formatted["draft_board_band"],
                "floor_anchor_cap_states": (
                    prospect.get("rookie_formula_balance_label") or "none"
                ),
                "missing_components": "|".join(missing),
                "warning_codes": "|".join(warning_codes),
                "evidence_confidence": prospect.get("confidence_status", ""),
                "source_limit_state": (
                    "REVIEW_ONLY_SOURCE_LIMITED"
                    if missing
                    else "EXACT_IDENTITY_COMPLETE"
                ),
                "blocking_reason": "",
                "score_label": SCORE_LABEL,
                "rank_label": RANK_LABEL,
                "board_label": BOARD_LABEL,
                "formula_version": SPRINT_12_13_VERSION,
                "board_formula_version": SPRINT_14E_VERSION,
                "input_pack_version": INPUT_PACK_VERSION,
                "board_version": BOARD_VERSION,
            }
        )
    for position in sorted(CORE_POSITIONS):
        position_rows = sorted(
            (row for row in rows if row["position"] == position),
            key=lambda row: int(row["overall_review_rank"]),
        )
        for rank, row in enumerate(position_rows, start=1):
            row["position_rank"] = rank
    for source in sources["blocked"]:
        rows.append(
            {
                "player_id": "",
                "player_name": source["player_name"],
                "position": source["position"],
                "nfl_team": source["nfl_team"],
                "college": source["college"],
                "draft_round": source["draft_round"],
                "overall_pick": source["overall_pick"],
                "age_at_draft": "",
                "identity_status": "BLOCKED_UNRESOLVED_IDENTITY",
                "identity_method": "UNRESOLVED_SOURCE_GSIS_ID",
                "production_component": "",
                "market_share_component": "",
                "draft_capital_component": "",
                "athletic_component": "",
                "recruiting_component": "",
                "age_component": "",
                "weighted_component_sum": "",
                "raw_model_v4_score": "",
                "confidence_cap": "",
                "final_review_score": "",
                "sprint14e_format_score": "",
                "position_rank": "",
                "overall_review_rank": "",
                "tier": "blocked_unranked",
                "floor_anchor_cap_states": "",
                "missing_components": (
                    "production|market_share|draft_capital|athletic_prior|"
                    "recruiting_prior|age_lifecycle"
                ),
                "warning_codes": "blocked_unresolved_identity",
                "evidence_confidence": "fail_closed",
                "source_limit_state": "BLOCKED_IDENTITY",
                "blocking_reason": "Canonical nflverse draft row has no exact GSIS player_id.",
                "score_label": SCORE_LABEL,
                "rank_label": RANK_LABEL,
                "board_label": BOARD_LABEL,
                "formula_version": SPRINT_12_13_VERSION,
                "board_formula_version": SPRINT_14E_VERSION,
                "input_pack_version": INPUT_PACK_VERSION,
                "board_version": BOARD_VERSION,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            row["overall_review_rank"] == "",
            _int(row["overall_review_rank"]) or 10_000,
            _int(row["overall_pick"]),
        ),
    )


def _validate_input_rows(
    rows: Iterable[dict[str, object]],
    exact: list[dict[str, Any]],
) -> None:
    materialized = list(rows)
    if len(materialized) != 73:
        raise RookieBoardReconstructionError("admitted prospect matrix must have 73 rows")
    expected = {row["player_id"]: row for row in exact}
    ids = [str(row.get("canonical_prospect_key") or "") for row in materialized]
    if not all(ids) or len(set(ids)) != len(ids):
        raise RookieBoardReconstructionError("blank or duplicate GSIS ID in prospect matrix")
    if set(ids) != set(expected):
        raise RookieBoardReconstructionError("prospect matrix identity set drift")
    for row in materialized:
        authority = expected[str(row["canonical_prospect_key"])]
        if row.get("prospect_name") != authority["player_name"]:
            raise RookieBoardReconstructionError("identity metadata swap or name-only join")
        if row.get("identity_status") != "exact_provider_gsis_id":
            raise RookieBoardReconstructionError("non-exact identity entered analyzer matrix")
        if str(row.get("formula_identity_admitted")).lower() != "true":
            raise RookieBoardReconstructionError("exact formula admission missing")
        combined = "|".join(
            str(row.get(field) or "")
            for field in (
                "factual_evidence_json",
                "derived_evidence_json",
                "prospect_prior_evidence_json",
            )
        ).lower()
        if "ppa" in combined or "future_nfl" in combined:
            raise RookieBoardReconstructionError("forbidden feature entered prospect matrix")
        prior = _json_object(row.get("prospect_prior_evidence_json"))
        recruiting = prior.get("recruiting_profile") or {}
        if recruiting and any(value == 0 for value in recruiting.values()):
            raise RookieBoardReconstructionError(
                "missing recruiting was converted to zero"
            )
        workout = prior.get("workout_profile") or {}
        if "missing_combine_evidence" in str(row.get("warning_flags") or "") and any(
            value == 0 for value in workout.values()
        ):
            raise RookieBoardReconstructionError("missing combine was converted to zero")


def _validate_complete_board(
    rows: Iterable[dict[str, object]],
    *,
    exact: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    component_rows: Iterable[dict[str, object]],
    sprint14e_rows: Iterable[dict[str, object]],
) -> None:
    board = list(rows)
    if len(board) != 80:
        raise RookieBoardReconstructionError("complete rookie board must contain 80 rows")
    exact_rows = [row for row in board if row["identity_status"] != "BLOCKED_UNRESOLVED_IDENTITY"]
    blocked_rows = [row for row in board if row["identity_status"] == "BLOCKED_UNRESOLVED_IDENTITY"]
    if len(exact_rows) != 73 or len(blocked_rows) != 7:
        raise RookieBoardReconstructionError("board identity partition drift")
    expected_ids = {row["player_id"] for row in exact}
    if {row["player_id"] for row in exact_rows} != expected_ids:
        raise RookieBoardReconstructionError("board exact identity set drift")
    if {row["player_name"] for row in blocked_rows} != {
        row["player_name"] for row in blockers
    }:
        raise RookieBoardReconstructionError("board blocker set drift")
    if any(
        row["player_name"] == "Ashton Jeanty"
        or "synthetic" in str(row["player_name"]).lower()
        for row in board
    ):
        raise RookieBoardReconstructionError("non-2026 or synthetic player entered board")
    if any(
        row["overall_review_rank"] != ""
        or row["position_rank"] != ""
        or row["final_review_score"] != ""
        for row in blocked_rows
    ):
        raise RookieBoardReconstructionError("blocked identity received score or rank")
    if any(
        row["score_label"] != SCORE_LABEL
        or row["rank_label"] != RANK_LABEL
        or row["board_label"] != BOARD_LABEL
        for row in board
    ):
        raise RookieBoardReconstructionError("review-only score/rank/board label drift")
    if any(row["formula_version"] != SPRINT_12_13_VERSION for row in board):
        raise RookieBoardReconstructionError("analyzer version drift in board")
    if any(row["board_formula_version"] != SPRINT_14E_VERSION for row in board):
        raise RookieBoardReconstructionError("board-layer version drift")
    weights = {
        str(row["component_name"]): float(row["component_weight"])
        for row in component_rows
        if row.get("component_layer") == "prospect_prior"
        and row.get("component_weight") not in ("", None)
    }
    if weights != FORMULA_WEIGHTS:
        raise RookieBoardReconstructionError("executed component weights drift")
    sprint_index = {str(row["rookie_board_key"]): row for row in sprint14e_rows}
    for row in exact_rows:
        cap = float(row["confidence_cap"])
        raw = float(row["raw_model_v4_score"])
        final = float(row["final_review_score"])
        if not (0 <= cap <= 1) or abs(round(raw * cap, 4) - final) > 0.0001:
            raise RookieBoardReconstructionError("confidence reconciliation failed")
        sprint = sprint_index[str(row["player_id"])]
        if float(row["sprint14e_format_score"]) != float(
            sprint["league_format_adjusted_score"]
        ):
            raise RookieBoardReconstructionError("Sprint 14E format reconciliation failed")
        missing = set(_split_flags(row["missing_components"]))
        for component, field in (
            ("athletic_prior", "athletic_component"),
            ("recruiting_prior", "recruiting_component"),
        ):
            if component in missing and row[field] not in ("", None):
                raise RookieBoardReconstructionError(
                    f"missing {component} masqueraded as numeric evidence"
                )


def run_required_mutations(
    result: ReconstructionResult,
) -> tuple[dict[str, object], ...]:
    """Run the 20 required negative controls through the real validators."""
    baseline_matrix = [dict(row) for row in result.prospect_matrix_rows]
    baseline_board = [dict(row) for row in result.board_rows]
    baseline_components = [dict(row) for row in result.component_rows]
    baseline_sprint14 = [dict(row) for row in result.sprint14e_rows]
    exact = [
        {
            "player_id": row["player_id"],
            "player_name": row["player_name"],
        }
        for row in baseline_board
        if row["identity_status"] != "BLOCKED_UNRESOLVED_IDENTITY"
    ]
    blockers = [
        {"player_name": row["player_name"]}
        for row in baseline_board
        if row["identity_status"] == "BLOCKED_UNRESOLVED_IDENTITY"
    ]
    cases: list[tuple[str, str, Any]] = []

    def matrix_case(name: str, mutate: Any) -> None:
        def run() -> None:
            rows = copy.deepcopy(baseline_matrix)
            mutate(rows)
            _validate_input_rows(rows, exact)
            _assert_equal_rows(rows, baseline_matrix, "prospect matrix")

        cases.append((name, "admitted_prospect_current_feature_matrix.csv", run))

    def board_case(name: str, mutate: Any) -> None:
        def run() -> None:
            rows = copy.deepcopy(baseline_board)
            mutate(rows)
            _validate_complete_board(
                rows,
                exact=exact,
                blockers=blockers,
                component_rows=baseline_components,
                sprint14e_rows=baseline_sprint14,
            )
            _assert_equal_rows(rows, baseline_board, "complete board")

        cases.append((name, "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv", run))

    matrix_case(
        "join_player_by_name_only",
        lambda rows: rows[0].update({"identity_status": "name_only"}),
    )

    def swap(rows: list[dict[str, object]]) -> None:
        first = rows[0]
        second = next(row for row in rows[1:] if row["position"] == first["position"])
        first["canonical_prospect_key"], second["canonical_prospect_key"] = (
            second["canonical_prospect_key"],
            first["canonical_prospect_key"],
        )

    matrix_case("swap_same_position_rookies", swap)
    matrix_case(
        "duplicate_gsis_id",
        lambda rows: rows[1].update(
            {"canonical_prospect_key": rows[0]["canonical_prospect_key"]}
        ),
    )
    matrix_case(
        "blank_gsis_id", lambda rows: rows[0].update({"canonical_prospect_key": ""})
    )

    def invent_blocked(rows: list[dict[str, object]]) -> None:
        invented = dict(rows[0])
        invented.update(
            {
                "canonical_prospect_key": "INVENTED-GSIS",
                "prospect_name": "Carson Beck",
            }
        )
        rows.append(invented)

    matrix_case("resolve_blocked_without_authority", invent_blocked)

    def add_player(rows: list[dict[str, object]], name: str, key: str) -> None:
        added = dict(rows[0])
        added.update({"canonical_prospect_key": key, "prospect_name": name})
        rows.append(added)

    matrix_case(
        "include_ashton_jeanty",
        lambda rows: add_player(rows, "Ashton Jeanty", "00-0039915"),
    )
    matrix_case(
        "include_synthetic_v1_fixture",
        lambda rows: add_player(rows, "Synthetic V1 Fixture", "SYNTHETIC-V1"),
    )

    def zero_combine(rows: list[dict[str, object]]) -> None:
        target = next(
            row for row in rows if "missing_combine_evidence" in str(row["warning_flags"])
        )
        prior = _json_object(target["prospect_prior_evidence_json"])
        prior["workout_profile"] = {"forty_pct": 0}
        target["prospect_prior_evidence_json"] = _json_text(prior)

    matrix_case("convert_missing_combine_to_zero", zero_combine)

    def zero_recruiting(rows: list[dict[str, object]]) -> None:
        prior = _json_object(rows[0]["prospect_prior_evidence_json"])
        prior["recruiting_profile"] = {"rating": 0, "stars": 0}
        rows[0]["prospect_prior_evidence_json"] = _json_text(prior)

    matrix_case("convert_missing_recruiting_to_zero", zero_recruiting)

    def add_ppa(rows: list[dict[str, object]]) -> None:
        derived = _json_object(rows[0]["derived_evidence_json"])
        derived["college_ppa"] = {"average_ppa": 1.0}
        rows[0]["derived_evidence_json"] = _json_text(derived)

    matrix_case("substitute_ppa_for_production_share", add_ppa)

    def component_case(name: str, component: str, weight: float) -> None:
        def run() -> None:
            components = copy.deepcopy(baseline_components)
            for row in components:
                if row.get("component_name") == component:
                    row["component_weight"] = weight
            _validate_complete_board(
                baseline_board,
                exact=exact,
                blockers=blockers,
                component_rows=components,
                sprint14e_rows=baseline_sprint14,
            )

        cases.append((name, "prospect_value_component_rows.csv", run))

    component_case("alter_production_weight", "production", 0.31)
    component_case("alter_draft_capital_weight", "draft_capital", 0.24)
    board_case(
        "remove_confidence_cap",
        lambda rows: rows[0].update({"confidence_cap": 1.0}),
    )

    def remove_guard(rows: list[dict[str, object]], token: str) -> None:
        target = next(
            (
                row
                for row in rows
                if token in str(row.get("floor_anchor_cap_states") or "")
            ),
            next(row for row in rows if row["identity_status"] != "BLOCKED_UNRESOLVED_IDENTITY"),
        )
        target["floor_anchor_cap_states"] = "none"

    board_case(
        "remove_day_three_guardrail",
        lambda rows: remove_guard(rows, "day_three"),
    )
    board_case(
        "remove_one_qb_qb_cap",
        lambda rows: remove_guard(rows, "one_qb_qb_scarcity_cap"),
    )

    def future_nfl(rows: list[dict[str, object]]) -> None:
        factual = _json_object(rows[0]["factual_evidence_json"])
        factual["future_nfl_production"] = {"yards": 1000}
        rows[0]["factual_evidence_json"] = _json_text(factual)

    matrix_case("use_future_nfl_production", future_nfl)

    def rank_blocked(rows: list[dict[str, object]]) -> None:
        target = next(
            row for row in rows if row["identity_status"] == "BLOCKED_UNRESOLVED_IDENTITY"
        )
        target["overall_review_rank"] = 74

    board_case("rank_blocked_row", rank_blocked)
    board_case(
        "label_review_rank_as_dynasty_rank",
        lambda rows: rows[0].update({"rank_label": "Dynasty Rank"}),
    )
    cases.append(
        (
            "write_output_into_finished_v1",
            "output path gate",
            lambda: assert_output_root_safe(
                Path(
                    r"C:\NWR\Niners-War-Room\local_exports\model_v4"
                    r"\current_value\latest\full_player_board_value_review_rows.csv"
                )
            ),
        )
    )
    cases.append(
        (
            "alter_outcome_v3",
            "output path gate",
            lambda: assert_output_root_safe(
                Path(
                    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/"
                    "OUTCOME_V3_INTEGRATION_PACK.csv"
                )
            ),
        )
    )

    results: list[dict[str, object]] = []
    for index, (name, owner, action) in enumerate(cases, start=1):
        try:
            action()
        except (RookieBoardReconstructionError, ValueError, AssertionError) as exc:
            results.append(
                {
                    "mutation_number": index,
                    "mutation": name,
                    "owning_path": owner,
                    "result": "PASS_REJECTED",
                    "failure": str(exc),
                }
            )
        else:
            results.append(
                {
                    "mutation_number": index,
                    "mutation": name,
                    "owning_path": owner,
                    "result": "FAIL_ACCEPTED",
                    "failure": "",
                }
            )
    if len(results) != 20 or any(row["result"] != "PASS_REJECTED" for row in results):
        raise RookieBoardReconstructionError("required mutation suite failed")
    return tuple(results)


def assert_output_root_safe(path: Path) -> None:
    normalized = str(path.resolve()).replace("\\", "/").lower()
    forbidden = (
        "full_player_board_value_review_rows.csv",
        "outcome_v3_integration_pack.csv",
        "prospective_2026_baseline_freeze.csv",
        "/active_pack/",
        "/trading_lab/",
    )
    if any(token in normalized for token in forbidden):
        raise RookieBoardReconstructionError("protected production/output path rejected")


def _validate_manifest(path: Path, expected_aggregate: str) -> None:
    if not path.is_file():
        raise RookieBoardReconstructionError(f"snapshot manifest missing: {path}")
    manifest = _read_json(path)
    if manifest.get("aggregate_sha256") != expected_aggregate:
        raise RookieBoardReconstructionError(f"snapshot aggregate drift: {path}")
    asset_hashes: list[str] = []
    for asset in manifest.get("assets", []):
        relative = Path(str(asset.get("relative_path") or ""))
        if relative.is_absolute() or ".." in relative.parts:
            raise RookieBoardReconstructionError("unsafe snapshot asset path")
        asset_path = path.parent / relative
        if not asset_path.is_file():
            raise RookieBoardReconstructionError(f"snapshot asset missing: {relative}")
        if asset_path.stat().st_size != int(asset.get("bytes", -1)):
            raise RookieBoardReconstructionError(f"snapshot asset size drift: {relative}")
        actual = _sha256(asset_path)
        if actual != asset.get("sha256"):
            raise RookieBoardReconstructionError(f"snapshot asset hash drift: {relative}")
        asset_hashes.append(actual)
    recomputed = hashlib.sha256("".join(asset_hashes).encode("ascii")).hexdigest()
    if recomputed != expected_aggregate:
        raise RookieBoardReconstructionError("snapshot aggregate recomputation failed")


def _assert_equal_rows(
    actual: list[dict[str, object]],
    expected: list[dict[str, object]],
    label: str,
) -> None:
    if _json_text(actual) != _json_text(expected):
        raise RookieBoardReconstructionError(f"{label} differs from governed regeneration")


def _governed_digest(paths: Iterable[Path]) -> str:
    records = [
        {"path": path.name, "sha256": _sha256(path)}
        for path in sorted(paths, key=lambda item: item.name)
    ]
    return hashlib.sha256(_json_text(records).encode("utf-8")).hexdigest()


def _write_csv(
    path: Path,
    header: Iterable[str],
    rows: Iterable[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=tuple(header), extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _json_object(value: object) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(str(value))
    return parsed if isinstance(parsed, dict) else {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _nullable(value: object) -> object | None:
    text = _text(value)
    if not text:
        return None
    number = _number(value)
    return number if number is not None else text


def _number(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _int(value: object) -> int:
    number = _number(value)
    return int(number) if number is not None else 0


def _id(value: object) -> str:
    number = _number(value)
    if number is not None and number.is_integer():
        return str(int(number))
    return _text(value)


def _normalize_name(value: object) -> str:
    lowered = _text(value).lower()
    for token in (" jr.", " sr.", " ii", " iii", " iv"):
        lowered = lowered.replace(token, "")
    return re.sub(r"[^a-z0-9]+", "", lowered)


def _split_flags(value: object) -> tuple[str, ...]:
    return tuple(flag.strip() for flag in str(value or "").split("|") if flag.strip())


def _blank_or_float(value: object) -> object:
    number = _number(value)
    return "" if number is None else number
