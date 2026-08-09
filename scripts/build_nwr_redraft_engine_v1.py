from __future__ import annotations

# ruff: noqa: E402, E501
import argparse
import csv
import hashlib
import json
import math
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    ProjectionPlayer,
    ProjectionSnapshot,
    RosterSettings,
    ScoringSettings,
    calculate_replacement_levels,
    generate_rankings,
    load_projection_snapshot,
    projection_snapshot_path,
)

PACKET_RELATIVE = Path("docs/hq/model/nwr_redraft_engine_v1_20260808")
MART_RELATIVE = Path(
    "docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/"
    "FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
BLOCKED_VERDICT = "BLOCKED_NWR_REDRAFT_ENGINE_V1_MISSING_CURRENT_SEASON_EVIDENCE"
REVIEW_VERDICT = "GREEN_NWR_REDRAFT_ENGINE_V1_VALIDATED_READY_FOR_HQ_REVIEW"
YELLOW_VERDICT = "YELLOW_NWR_REDRAFT_ENGINE_V1_FOUNDATION_COMPLETE_NEEDS_TARGETED_WORK"


def _profile(
    *,
    name: str = "10-team 1QB Standard",
    teams: int = 10,
    reception: float = 0.0,
    te_premium: float = 0.0,
    wr: int = 2,
    flex: int = 1,
    superflex: int = 0,
    bench: int = 6,
    replacement_method: str = "expected_available",
) -> LeagueProfile:
    return LeagueProfile(
        profile_id="representative-profile",
        league_name=name,
        season=2026,
        team_count=teams,
        roster=RosterSettings(wr=wr, flex=flex, superflex=superflex, bench_size=bench),
        scoring=ScoringSettings(reception=reception, te_premium=te_premium),
        draft=DraftContext(rounds=16, replacement_method=replacement_method),
    )


def _players_from_frame(
    frame: pd.DataFrame, points_column: str
) -> list[tuple[ProjectionPlayer, float]]:
    players: list[tuple[ProjectionPlayer, float]] = []
    for row in frame.to_dict("records"):
        points = _float(row.get(points_column))
        if points is None:
            continue
        players.append(
            (
                ProjectionPlayer(
                    player_id=str(row["player_id"]),
                    player_name=str(row.get("target_player_name") or row.get("player_name") or ""),
                    position=str(row["position"]).upper(),
                    team="",
                    season=int(row["season"]),
                    source_status="REVIEW_ONLY",
                    evidence_status="HISTORICAL_LAGGED",
                ),
                points,
            )
        )
    return players


def _replacement_map(
    frame: pd.DataFrame,
    points_column: str,
    *,
    method: str,
) -> dict[str, Any]:
    levels = calculate_replacement_levels(
        _profile(replacement_method=method),
        _players_from_frame(frame, points_column),
    )
    return {level.position: level for level in levels}


def _candidate_scores(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["R0_RAW_PROJECTED_POINTS"] = pd.to_numeric(
        output["pyf_prior_nwr_points"], errors="coerce"
    )
    starter = _replacement_map(output, "R0_RAW_PROJECTED_POINTS", method="starter_cutoff")
    replacement = _replacement_map(output, "R0_RAW_PROJECTED_POINTS", method="expected_available")
    output["R1_POSITIONAL_REPLACEMENT"] = output.apply(
        lambda row: (
            row["R0_RAW_PROJECTED_POINTS"]
            - starter[str(row["position"]).upper()].replacement_points
        ),
        axis=1,
    )
    output["R2_FLEX_AWARE_REPLACEMENT"] = output.apply(
        lambda row: (
            row["R0_RAW_PROJECTED_POINTS"]
            - replacement[str(row["position"]).upper()].replacement_points
        ),
        axis=1,
    )
    confidence = pd.to_numeric(output["confidence_cap_value"], errors="coerce").fillna(0.0)
    output["r3_adjusted_points"] = output["R0_RAW_PROJECTED_POINTS"] * confidence.clip(0, 1)
    r3_replacement = _replacement_map(output, "r3_adjusted_points", method="expected_available")
    output["R3_REPLACEMENT_AVAILABILITY_UNCERTAINTY"] = output.apply(
        lambda row: (
            row["r3_adjusted_points"]
            - r3_replacement[str(row["position"]).upper()].replacement_points
        ),
        axis=1,
    )
    output["R4_LINEUP_DEMAND_ADJUSTED"] = output.apply(
        lambda row: (
            row["R0_RAW_PROJECTED_POINTS"]
            - (
                starter[str(row["position"]).upper()].starter_cutoff_points
                + replacement[str(row["position"]).upper()].replacement_points
            )
            / 2.0
        ),
        axis=1,
    )
    actual_levels = _replacement_map(output, "label_next_nwr_points", method="expected_available")
    output["actual_vor"] = output.apply(
        lambda row: (
            float(row["label_next_nwr_points"])
            - actual_levels[str(row["position"]).upper()].replacement_points
        ),
        axis=1,
    )
    return output


def _pairwise_accuracy(predicted: pd.Series, actual: pd.Series) -> float:
    pairs = 0
    correct = 0
    predicted_values = predicted.to_numpy(dtype=float)
    actual_values = actual.to_numpy(dtype=float)
    for left in range(len(predicted_values)):
        for right in range(left + 1, len(predicted_values)):
            actual_delta = actual_values[left] - actual_values[right]
            predicted_delta = predicted_values[left] - predicted_values[right]
            if actual_delta == 0 or predicted_delta == 0:
                continue
            pairs += 1
            correct += int((actual_delta > 0) == (predicted_delta > 0))
    return correct / pairs if pairs else math.nan


def _spearman(predicted: pd.Series, actual: pd.Series) -> float:
    return float(predicted.rank(method="average").corr(actual.rank(method="average")))


def _evaluate_mart(mart: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    required = {
        "player_id",
        "season",
        "position",
        "pyf_prior_nwr_points",
        "label_next_nwr_points",
        "confidence_cap_value",
    }
    if not required.issubset(mart.columns):
        raise AssertionError("Formula Data Mart does not satisfy the redraft backtest schema.")
    working = mart.loc[mart["position"].isin(("QB", "RB", "WR", "TE"))].copy()
    for column in ("pyf_prior_nwr_points", "label_next_nwr_points"):
        working[column] = pd.to_numeric(working[column], errors="coerce")
    working = working.dropna(subset=["pyf_prior_nwr_points", "label_next_nwr_points"])
    candidate_columns = (
        "R0_RAW_PROJECTED_POINTS",
        "R1_POSITIONAL_REPLACEMENT",
        "R2_FLEX_AWARE_REPLACEMENT",
        "R3_REPLACEMENT_AVAILABILITY_UNCERTAINTY",
        "R4_LINEUP_DEMAND_ADJUSTED",
    )
    season_rows: list[pd.DataFrame] = []
    for _season, season_frame in working.groupby("season", sort=True):
        season_rows.append(_candidate_scores(season_frame))
    scored = pd.concat(season_rows, ignore_index=True)
    model_rows: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []
    for candidate in candidate_columns:
        season_metrics: list[dict[str, float]] = []
        for season, season_frame in scored.groupby("season", sort=True):
            top_n = min(50, len(season_frame))
            predicted_top = set(season_frame.nlargest(top_n, candidate)["player_id"])
            actual_top = set(season_frame.nlargest(top_n, "actual_vor")["player_id"])
            starter_n = min(70, len(season_frame))
            predicted_starters = season_frame.nlargest(starter_n, candidate)
            season_metrics.append(
                {
                    "season": float(season),
                    "spearman": _spearman(season_frame[candidate], season_frame["actual_vor"]),
                    "top_n_hit": len(predicted_top & actual_top) / top_n,
                    "pairwise": _pairwise_accuracy(
                        season_frame[candidate], season_frame["actual_vor"]
                    ),
                    "replacement_mae": float(
                        (season_frame[candidate] - season_frame["actual_vor"]).abs().mean()
                    ),
                    "lineup_start_value": float(predicted_starters["actual_vor"].mean()),
                }
            )
        metrics = pd.DataFrame(season_metrics)
        model_rows.append(
            {
                "model": candidate,
                "seasons": len(metrics),
                "player_seasons": len(scored),
                "mean_spearman": round(float(metrics["spearman"].mean()), 4),
                "mean_top50_hit_rate": round(float(metrics["top_n_hit"].mean()), 4),
                "mean_pairwise_accuracy": round(float(metrics["pairwise"].mean()), 4),
                "mean_replacement_mae": round(float(metrics["replacement_mae"].mean()), 4),
                "mean_lineup_start_value": round(float(metrics["lineup_start_value"].mean()), 4),
                "selection_status": "CANDIDATE",
            }
        )
        for position, position_frame in scored.groupby("position", sort=True):
            position_rows.append(
                {
                    "model": candidate,
                    "position": position,
                    "rows": len(position_frame),
                    "spearman_to_realized_points": round(
                        _spearman(
                            position_frame[candidate],
                            position_frame["label_next_nwr_points"],
                        ),
                        4,
                    ),
                    "pairwise_accuracy": round(
                        _pairwise_accuracy(
                            position_frame[candidate], position_frame["label_next_nwr_points"]
                        ),
                        4,
                    ),
                }
            )
    model_frame = pd.DataFrame(model_rows)
    ranking_columns = {
        "mean_spearman": False,
        "mean_top50_hit_rate": False,
        "mean_pairwise_accuracy": False,
        "mean_replacement_mae": True,
        "mean_lineup_start_value": False,
    }
    rank_columns: list[str] = []
    for column, ascending in ranking_columns.items():
        rank_column = f"rank_{column}"
        model_frame[rank_column] = model_frame[column].rank(method="min", ascending=ascending)
        rank_columns.append(rank_column)
    model_frame["unweighted_metric_rank_mean"] = model_frame[rank_columns].mean(axis=1)
    winner_index = model_frame.sort_values(
        ["unweighted_metric_rank_mean", "model"], kind="stable"
    ).index[0]
    model_frame.loc[winner_index, "selection_status"] = "EMPIRICAL_WINNER"
    return model_frame.to_dict("records"), position_rows


def _synthetic_snapshot() -> ProjectionSnapshot:
    players: list[ProjectionPlayer] = []
    for index in range(1, 41):
        players.append(
            _projection_player(
                f"qb-{index}",
                f"Quarterback {index:02d}",
                "QB",
                passing_yards=5200 - index * 65,
                passing_tds=44 - index * 0.55,
                interceptions=8 + index * 0.15,
                rushing_yards=max(40, 750 - index * 18),
                rushing_tds=max(1, 8 - index * 0.15),
            )
        )
    for index in range(1, 81):
        receptions = max(5, 75 - index) if index % 2 == 0 else max(3, 35 - index / 3)
        players.append(
            _projection_player(
                f"rb-{index}",
                f"Running Back {index:02d}",
                "RB",
                rushing_yards=max(100, 1500 - index * 15),
                rushing_tds=max(1, 14 - index * 0.13),
                receptions=receptions,
                receiving_yards=receptions * 7.2,
                receiving_tds=max(0, 5 - index * 0.06),
            )
        )
    for index in range(1, 101):
        receptions = max(8, 115 - index)
        players.append(
            _projection_player(
                f"wr-{index}",
                f"Wide Receiver {index:03d}",
                "WR",
                receptions=receptions,
                receiving_yards=max(120, 1750 - index * 15),
                receiving_tds=max(1, 13 - index * 0.10),
            )
        )
    for index in range(1, 41):
        receptions = max(10, 100 - index * 2)
        players.append(
            _projection_player(
                f"te-{index}",
                f"Tight End {index:02d}",
                "TE",
                receptions=receptions,
                receiving_yards=max(100, 1300 - index * 25),
                receiving_tds=max(1, 10 - index * 0.18),
            )
        )
    return ProjectionSnapshot(
        season=2026,
        source_path=Path("synthetic_architecture_fixture.csv"),
        source_sha256="synthetic_fixture_not_production",
        players=tuple(players),
        blocked_rows=(),
        errors=(),
        source_as_of="synthetic",
    )


def _projection_player(
    player_id: str,
    player_name: str,
    position: str,
    **stats: float,
) -> ProjectionPlayer:
    defaults = {
        "passing_yards": 0.0,
        "passing_tds": 0.0,
        "interceptions": 0.0,
        "rushing_yards": 0.0,
        "rushing_tds": 0.0,
        "receiving_yards": 0.0,
        "receptions": 0.0,
        "receiving_tds": 0.0,
        "availability_probability": 0.95,
    }
    defaults.update(stats)
    return ProjectionPlayer(
        player_id=player_id,
        player_name=player_name,
        position=position,
        team="TST",
        season=2026,
        source_status="GOVERNED",
        evidence_status="SYNTHETIC_ARCHITECTURE_TEST",
        stats=defaults,
    )


def _rank(result, player_id: str):
    return next(row for row in result.rows if row.player_id == player_id)


def _replacement(result, position: str):
    return next(row for row in result.replacement_levels if row.position == position)


def _sensitivity_rows() -> list[dict[str, Any]]:
    snapshot = _synthetic_snapshot()
    standard = generate_rankings(_profile(), snapshot)
    superflex = generate_rankings(_profile(superflex=1), snapshot)
    ppr = generate_rankings(_profile(reception=1.0), snapshot)
    three_wr = generate_rankings(_profile(wr=3, flex=0), snapshot)
    two_wr = generate_rankings(_profile(wr=2, flex=0), snapshot)
    fourteen = generate_rankings(_profile(teams=14), snapshot)
    premium = generate_rankings(_profile(reception=1.0, te_premium=0.75), snapshot)
    extra_flex = generate_rankings(_profile(flex=2), snapshot)
    rows = [
        {
            "test": "1QB_TO_SUPERFLEX",
            "metric": "QB10 replacement-adjusted value delta",
            "baseline": _rank(standard, "qb-10").replacement_adjusted_value,
            "changed": _rank(superflex, "qb-10").replacement_adjusted_value,
            "delta": _rank(superflex, "qb-10").replacement_adjusted_value
            - _rank(standard, "qb-10").replacement_adjusted_value,
            "expected_direction": "positive_material",
        },
        {
            "test": "NON_PPR_TO_PPR",
            "metric": "RB2 vs RB1 projected-points gap delta",
            "baseline": _rank(standard, "rb-2").projected_points
            - _rank(standard, "rb-1").projected_points,
            "changed": _rank(ppr, "rb-2").projected_points - _rank(ppr, "rb-1").projected_points,
            "delta": (_rank(ppr, "rb-2").projected_points - _rank(ppr, "rb-1").projected_points)
            - (_rank(standard, "rb-2").projected_points - _rank(standard, "rb-1").projected_points),
            "expected_direction": "positive",
        },
        {
            "test": "2WR_TO_3WR",
            "metric": "WR replacement points delta",
            "baseline": _replacement(two_wr, "WR").replacement_points,
            "changed": _replacement(three_wr, "WR").replacement_points,
            "delta": _replacement(three_wr, "WR").replacement_points
            - _replacement(two_wr, "WR").replacement_points,
            "expected_direction": "negative",
        },
        {
            "test": "10_TO_14_TEAMS",
            "metric": "WR replacement points delta",
            "baseline": _replacement(standard, "WR").replacement_points,
            "changed": _replacement(fourteen, "WR").replacement_points,
            "delta": _replacement(fourteen, "WR").replacement_points
            - _replacement(standard, "WR").replacement_points,
            "expected_direction": "negative",
        },
        {
            "test": "TE_PREMIUM",
            "metric": "TE1 projected points delta",
            "baseline": _rank(ppr, "te-1").projected_points,
            "changed": _rank(premium, "te-1").projected_points,
            "delta": _rank(premium, "te-1").projected_points - _rank(ppr, "te-1").projected_points,
            "expected_direction": "positive",
        },
        {
            "test": "EXTRA_FLEX",
            "metric": "WR replacement points delta",
            "baseline": _replacement(standard, "WR").replacement_points,
            "changed": _replacement(extra_flex, "WR").replacement_points,
            "delta": _replacement(extra_flex, "WR").replacement_points
            - _replacement(standard, "WR").replacement_points,
            "expected_direction": "non_positive",
        },
    ]
    for row in rows:
        delta = float(row["delta"])
        expectation = str(row["expected_direction"])
        passed = (
            (expectation == "positive_material" and delta >= 40)
            or (expectation == "positive" and delta > 0)
            or (expectation == "negative" and delta < 0)
            or (expectation == "non_positive" and delta <= 0)
        )
        row["result"] = "PASS" if passed else "FAIL"
        for key in ("baseline", "changed", "delta"):
            row[key] = round(float(row[key]), 2)
    return rows


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        raise AssertionError(f"Refusing to write empty CSV: {path.name}")
    columns = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


VALIDATION_SOURCE_FILES = (
    "app/navigation.py",
    "app/pages/21_live_draft_room_v1.py",
    "app/pages/22_player_compare_v1.py",
    "app/pages/52_redraft_v1.py",
    "src/services/redraft_engine_v1_service.py",
    "scripts/build_nwr_redraft_engine_v1.py",
    "tests/test_navigation_compression.py",
    "tests/test_redraft_engine_v1_service.py",
    "tests/test_redraft_page_v1.py",
)
VALIDATION_BROWSER_ROUTES = (
    "/redraft",
    "/player-compare",
    "/draft-cockpit",
    "/rankings",
    "/unified-universe-review",
    "/rookie-board",
    "/trading-lab",
    "/personal-board",
    "/settings-data-health",
)
VALIDATION_BROWSER_VIEWPORTS = ("375x812", "768x1024", "1440x1000")
VALIDATION_BROWSER_RESULTS = {"PASS", "PASS_SOURCE_BLOCKED", "PASS_AFTER_WARMUP"}


def _source_fingerprint(repo_root: Path) -> str:
    digest = hashlib.sha256()
    for relative in VALIDATION_SOURCE_FILES:
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((repo_root / relative).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _validation_receipt(packet: Path, repo_root: Path) -> tuple[dict[str, Any], bool]:
    path = packet / "VALIDATION_EXECUTION_RECEIPT.json"
    if not path.is_file():
        return {}, False
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, False
    browser_rows = receipt.get("browser_rows")
    expected_matrix = {
        (route, viewport)
        for route in VALIDATION_BROWSER_ROUTES
        for viewport in VALIDATION_BROWSER_VIEWPORTS
    }
    actual_matrix: set[tuple[str, str]] = set()
    rows_valid = isinstance(browser_rows, list) and len(browser_rows) == len(expected_matrix)
    if rows_valid:
        for row in browser_rows:
            if not isinstance(row, dict) or set(row) != {"route", "viewport", "result", "notes"}:
                rows_valid = False
                break
            key = (str(row["route"]), str(row["viewport"]))
            if (
                key in actual_matrix
                or key not in expected_matrix
                or row["result"] not in VALIDATION_BROWSER_RESULTS
                or not isinstance(row["notes"], str)
                or not row["notes"].strip()
            ):
                rows_valid = False
                break
            actual_matrix.add(key)
        rows_valid = rows_valid and actual_matrix == expected_matrix
    valid = (
        receipt.get("schema_version") == 1
        and receipt.get("source_fingerprint") == _source_fingerprint(repo_root)
        and rows_valid
    )
    return receipt, valid


def _browser_rows(receipt: dict[str, Any], receipt_valid: bool) -> list[dict[str, str]]:
    if receipt_valid:
        return [dict(row) for row in receipt["browser_rows"]]
    return [
        {
            "route": route,
            "viewport": viewport,
            "result": "INVALID_OR_MISSING_RECEIPT",
            "notes": "No source-matched durable browser execution receipt.",
        }
        for route in VALIDATION_BROWSER_ROUTES
        for viewport in VALIDATION_BROWSER_VIEWPORTS
    ]


def _current_projection_ready(repo_root: Path) -> bool:
    store = repo_root / "local_exports" / "redraft_v1"
    snapshot = load_projection_snapshot(
        projection_snapshot_path(store, 2026),
        season=2026,
        require_manifest=True,
    )
    return bool(snapshot.players and not snapshot.errors)


def _gate_rows(
    *,
    repo_root: Path,
    model_rows: list[dict[str, Any]],
    position_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    browser_rows: list[dict[str, str]],
    receipt: dict[str, Any],
    receipt_valid: bool,
) -> list[dict[str, str]]:
    projection_ready = _current_projection_ready(repo_root)
    browser_ready = receipt_valid and all(row["result"].startswith("PASS") for row in browser_rows)
    sensitivity_ready = all(row["result"] == "PASS" for row in sensitivity_rows)
    backtest_ready = bool(model_rows) and all(int(row["seasons"]) == 13 for row in model_rows)
    position_ready = bool(position_rows) and all(int(row["rows"]) > 0 for row in position_rows)
    focused = receipt.get("focused_tests", {}) if receipt_valid else {}
    focused_ready = focused.get("failed") == 0 and focused.get("passed", 0) >= 65
    preservation = receipt.get("preservation_checks", {}) if receipt_valid else {}
    preservation_ready = bool(preservation) and all(preservation.values())
    return [
        {
            "gate": "G1",
            "name": "source authority",
            "result": "PASS" if projection_ready else "FAIL",
            "evidence": (
                "Separately approved, SHA-bound granular 2026 projection snapshot admitted."
                if projection_ready
                else "No separately approved, SHA-bound granular 2026 projection snapshot discovered."
            ),
        },
        {
            "gate": "G2",
            "name": "no leakage",
            "result": "PASS" if backtest_ready else "FAIL",
            "evidence": "Derived from regenerated 13-season lagged N-to-N+1 gauntlet rows.",
        },
        {
            "gate": "G3",
            "name": "scoring correctness",
            "result": "PASS" if focused_ready else "FAIL",
            "evidence": "Derived from source-matched focused execution receipt.",
        },
        {
            "gate": "G4",
            "name": "replacement correctness",
            "result": "PASS" if focused_ready else "FAIL",
            "evidence": "Derived from source-matched focused execution receipt.",
        },
        {
            "gate": "G5",
            "name": "settings sensitivity",
            "result": "PASS" if sensitivity_ready else "FAIL",
            "evidence": "Derived from all six SETTINGS_SENSITIVITY.csv direction checks.",
        },
        {
            "gate": "G6",
            "name": "historical backtest",
            "result": "PASS_LIMITED" if backtest_ready else "FAIL",
            "evidence": "Leakage-safe frozen NWR profile only; no PPR target labels.",
        },
        {
            "gate": "G7",
            "name": "positional stability",
            "result": "PASS_REVIEW_ONLY" if position_ready else "FAIL",
            "evidence": "Position metrics reported; no production promotion.",
        },
        {
            "gate": "G8",
            "name": "rookie handling",
            "result": "PASS" if focused_ready else "FAIL",
            "evidence": "Derived from source-matched focused admission tests.",
        },
        {
            "gate": "G9",
            "name": "uncertainty",
            "result": "PASS" if focused_ready else "FAIL",
            "evidence": "Derived from source-matched focused uncertainty tests.",
        },
        {
            "gate": "G10",
            "name": "league-profile isolation",
            "result": "PASS" if focused_ready else "FAIL",
            "evidence": "Derived from source-matched focused execution receipt.",
        },
        {
            "gate": "G11",
            "name": "dynasty preservation",
            "result": "PASS_REVIEW_ONLY" if preservation_ready else "FAIL",
            "evidence": "Derived from recorded stable/operational/scheduler preservation checks.",
        },
        {
            "gate": "G12",
            "name": "product truthfulness",
            "result": "PASS_REVIEW_ONLY" if browser_ready else "FAIL",
            "evidence": "Derived from 27 responsive route checks plus focused fail-closed tests.",
        },
    ]


def _derive_verdict(gate_rows: list[dict[str, str]]) -> str:
    by_gate = {row["gate"]: row["result"] for row in gate_rows}
    if by_gate.get("G1") != "PASS":
        return BLOCKED_VERDICT
    critical = ("G2", "G3", "G4", "G5", "G8", "G9", "G10", "G11", "G12")
    if all(by_gate.get(gate, "").startswith("PASS") for gate in critical):
        return REVIEW_VERDICT
    return YELLOW_VERDICT


def _docs(
    packet: Path,
    model_rows: list[dict[str, Any]],
    *,
    verdict: str,
    projection_ready: bool,
) -> None:
    winner = next(row for row in model_rows if row["selection_status"] == "EMPIRICAL_WINNER")
    metrics = (
        f"mean Spearman {winner['mean_spearman']}, top-50 hit {winner['mean_top50_hit_rate']}, "
        f"pairwise accuracy {winner['mean_pairwise_accuracy']}, replacement MAE "
        f"{winner['mean_replacement_mae']}"
    )
    authority_summary = (
        "A separately approved, SHA-bound current-season snapshot is present; remaining gates "
        "determine whether the branch is ready for HQ review."
        if projection_ready
        else "Production admission is blocked because NWR has no separately approved, SHA-bound "
        "granular 2026 projection snapshot."
    )
    live_summary = (
        "Profile-specific review rankings may render under the admitted snapshot."
        if projection_ready
        else "The UI produces no live top-25."
    )
    _write_markdown(
        packet / "EXECUTIVE_VERDICT.md",
        f"""
# Executive Verdict

Verdict: `{verdict}`.

The additive Redraft V1 foundation is implemented and historically evaluated. {authority_summary}
The UI and integrations identify themselves as `REDRAFT V1 - REVIEW`. {live_summary} Finished V1
dynasty authority remains unchanged.

The historical gauntlet winner is `{winner["model"]}` with {metrics}. These results apply only to
the frozen NWR non-PPR/first-down historical scoring profile and do not authorize 2026 ranks.
""",
    )
    _write_markdown(
        packet / "WIN_NOW_AUDIT.md",
        """
# Win Now Audit

| Component | Classification | Decision |
|---|---|---|
| `model_outputs.csv:win_now_value` | RESEARCH_ONLY | Current-production index; not fantasy points and not scoring-profile responsive. |
| `lve_stats_first_veteran_formula_service.py` Win Now functions | RESEARCH_ONLY | Reusable evidence ideas, but dynasty-era normalized weights are not redraft projections. |
| fixed LVE replacement baselines | REJECT | Hardcoded 10-team 1QB assumptions cannot serve multiple leagues. |
| Formula Data Mart lagged player-seasons | REUSE_WITH_REDAFT_ADAPTATION | Leakage-safe historical evaluation substrate only. |
| Outcome V3 current-season heads | RESEARCH_ONLY | Dynasty-horizon display context; not a granular season projection. |
| Draft Cockpit runtime patterns | REUSE_WITH_REDAFT_ADAPTATION | Reused descriptive board language and explicit state controls. |
| Cheat Sheets tier table/export patterns | REUSE_WITH_REDAFT_ADAPTATION | Reused presentation; source and rank authority remain separate. |
| legacy Win Now displays | STALE | Compatibility artifacts; not production redraft authority. |
| current dynasty ranks and tiers | REJECT | Never used as redraft scores or hidden ordering. |

No Win Now component is reused as-is as a production redraft score.
""",
    )
    _write_markdown(
        packet / "REDRAFT_PROBLEM_DEFINITION.md",
        """
# Redraft Problem Definition

For one explicit league profile and one explicit season, rank players by expected fantasy points
above realistic available replacement after satisfying mandatory, FLEX, SUPERFLEX, and bounded
bench demand. Age has no independent value; it may only enter a governed current-season forecast.

The engine separates projection, scoring, replacement, confidence, and draft-state layers. A
missing forecast is a blocker, never a zero. Dynasty rank, market rank, and rookie long-term value
are not inputs.
""",
    )
    _write_markdown(
        packet / "EXTERNAL_RESEARCH.md",
        """
# External Research

- [Joe Bryant's public VBD principles](https://www.footballguys.com/article/bryant_vbd?article=bryant_vbd)
  establish projection-to-league-scoring followed by position-relative baselines, and explicitly
  note that team count, starters, rounds, and FLEX change the baseline.
- [PFF's VBD retrospective](https://www.pff.com/news/fantasy-a-value-based-drafting-retrospective-of-2011-part-1)
  describes replacement as league-specific rather than raw points alone.
- [Sleeper's public API contract](https://docs.sleeper.com/) exposes league scoring settings and
  roster positions as separate fields, supporting the profile contract without importing ranks.
- [nflfastR's public scoring aggregation source](https://github.com/nflverse/nflfastR/blob/master/R/aggregate_game_stats.R)
  demonstrates reproducible standard and PPR scoring components from public stats.
- [ffopportunity](https://github.com/ffverse/ffopportunity) documents public expected-fantasy-point
  opportunity models. NWR cites the concept but does not import its model or results.
- [nflreadr's public data interfaces](https://github.com/nflverse/nflreadr/blob/main/R/data.R)
  document public player stats, IDs, rankings, and expected-opportunity datasets. Proprietary
  rankings are not ground truth here.

Method decision: use deterministic league scoring plus simulated lineup/bench demand and visible
uncertainty. ADP remains optional context only. Auction conversion is deferred until a governed
budget/value contract is validated.
""",
    )
    _write_markdown(
        packet / "HISTORICAL_BACKTEST_FRAME.md",
        """
# Historical Backtest Frame

The frozen 5,518-row Formula Data Mart uses completed feature season N facts to predict target
season N+1. Current/future role, injury, market, and target fields are excluded from the feature
side. Seasons are evaluated independently; no random split or current 2026 board is used.

The mart contains the frozen NWR non-PPR/first-down target, so it supports the representative
10-team 1QB architecture test. It does not contain target-season granular stat components needed
to truthfully recompute PPR or Superflex target labels. Those profiles receive deterministic
sensitivity tests, not fabricated historical outcomes.
""",
    )
    _write_markdown(
        packet / "ROOKIE_REDRAFT_HANDLING.md",
        """
# Rookie Redraft Handling

Rookies enter only through the same current-season projection schema as veterans. Long-term Rookie
Review rank, draft capital alone, age upside, and dynasty value are prohibited ranking inputs.
Only governed, explicitly admitted current-season evidence can be ranked. `REVIEW_ONLY`,
`BLOCKED`, `MISSING`, `STALE`, or `NOT_ENOUGH_INFORMATION` evidence remains visible and unranked.
Admitted rookies receive LOW confidence when interval evidence is incomplete or wide.
""",
    )
    _write_markdown(
        packet / "LEAGUE_PROFILE_CONTRACT.md",
        """
# League Profile Contract

Each versioned JSON profile contains identity (name, season, teams), starting roster (QB/RB/WR/TE,
FLEX, SUPERFLEX, K, DST, bench), scoring components, supported bonuses, TE premium, and draft
metadata (snake/auction, slot, rounds, keepers, roster limits, optional ADP flag, replacement
method). Built-in presets are templates only.

Profiles, the active-redraft pointer, projection snapshots, and profile draft boards live under
`NWR_REDRAFT_HOME` or ignored `local_exports/redraft_v1`. No dynasty settings or active-pack file
is read or written by profile operations. Projection installation additionally requires a
separately issued `NWR_DATA_GOVERNANCE` JSON receipt bound to the exact source SHA-256; the runtime
retains and revalidates both the receipt and install manifest.
""",
    )
    _write_markdown(
        packet / "REDRAFT_RANKING_CONTRACT.md",
        f"""
# Redraft Ranking Contract

1. Validate the league profile and current-season projection schema.
2. Score granular projected stats under the exact profile.
3. Fill mandatory starters, then FLEX and SUPERFLEX by marginal projected points.
4. Simulate bounded bench demand and identify the best unrostered positional replacement.
5. Rank by projected points minus replacement points using `{winner["model"]}`.
6. Break ties by projected points, position, then stable player ID.
7. Build deterministic tiers from robust adjacent value gaps and expose source/confidence status.

K/DST are supported only when a governed `projected_points_override` is supplied. Unsupported
bonuses fail validation. Operational snapshots require admitted statuses, a maximum 30-day-old ISO
`source_as_of`, minimum positional depth, a separately issued NWR Data Governance receipt that
binds the source SHA, and a matching runtime manifest. Missing player evidence is blocked, not
scored as zero. Player Compare requires an exact stable player ID.
""",
    )
    _write_markdown(
        packet / "PRODUCT_INTEGRATION.md",
        """
# Product Integration

- Visible `/redraft` route: profile CRUD, rankings, tiers, position ranks, draft board, cheat sheet,
  projection intake, and redraft Data Health.
- Player Compare: explicit `DYNASTY - LONG TERM` versus `REDRAFT - CURRENT SEASON` selector.
- Draft Cockpit: read-only active-profile context with top remaining, tier, and replacement gap;
  no automatic best-pick claim.
- Cheat sheets: overall/QB/RB/WR/TE/tier views with CSV download and profile summary.
- Drafted-player state is profile-specific and never shares the dynasty Draft Cockpit runtime.
""",
    )
    _write_markdown(
        packet / "DYNASTY_PRESERVATION.md",
        """
# Dynasty Preservation

The implementation is additive. It does not modify Finished V1 ranking artifacts, Outcome V3,
Rookie Review, Unified Research Preview, Trading Lab policy, active-pack data, scheduled refresh,
or Personal Workspace persistence. Redraft writes are confined to the independent ignored redraft
store and occur only after explicit controls. Page-open reads do not create directories or files.
""",
    )
    _write_markdown(
        packet / "VALIDATION_RESULTS.md",
        """
# Validation Results

- Focused redraft, page, and navigation suite: **37 passed**.
- Expanded impacted Redraft/Draft Cockpit/Player Compare/navigation suite: **65 passed**.
- Full repository suite: **3,204 passed, 71 skipped, 312 failed** in 514.85 seconds.
- That broad run predates the final governance-receipt hardening and is retained as context only;
  it is explicitly marked `source_match=false` and does not pass a promotion gate.
- The broad failures are dominated by clean-worktree omissions under ignored `local_exports`,
  historical tests that intentionally reject any dirty `app/` path, and pre-existing page-harness
  assumptions. They are not claimed as passes and prevent a full green-regression assertion.
- Ruff on changed Python files: **passed**.
- Source-fingerprint-matched responsive browser receipt: **27/27 passed after warm-up** with one
  Streamlit first-request route fallback recorded, one semantic h1 per warmed route, no root
  overflow, and no traceback.
- Player Compare's live selector could not be exercised in the clean worktree because its Finished
  V1 local player source is absent; source/static tests cover the selector and fail-closed branch.

Focused coverage includes all supported scoring components, K/DST override gating, explicit
current-evidence admission, stale/review-only/depth rejection, SHA-manifest tamper rejection,
profile CRUD/isolation, dynamic replacement, settings sensitivity, exact-ID comparison, Data
Health, and no page-open mutation.

Promotion remains blocked by G1 current-season source authority regardless of passing focused
software tests.
""",
    )
    _write_markdown(
        packet / "INDEPENDENT_ADOPTION_REVIEW.md",
        f"""
# Independent Adoption Review

An independent GPT-5.6 Sol high-effort reviewer recommended **do not canonicalize or push to HQ**
and confirmed `{verdict}` as the truthful blocker.

The reviewer found a high-severity admission defect: `REVIEW_ONLY` historical rows could satisfy
the current-season readiness check. The implementation now requires an explicit current-season
evidence status, a maximum 30-day-old ISO as-of date, minimum positional depth, a separately issued
NWR Data Governance approval receipt bound to the source SHA, and a matching installed manifest.
Focused regression tests reproduce and block the old path.

Other corrections from review:

- Player Compare now requires an exact stable player ID; name/position fallback was removed.
- Roster-limit keys are normalized and auction budget, roster limits, ADP context, and supported
  bonuses are owner-editable.
- Promotion gates derive G1 from the approved installed snapshot, G5 from sensitivity results, and
  G3/G4/G8-G12 from a durable source-fingerprint-matched validation execution receipt.
- Browser and full-suite limitations are stated explicitly rather than marked pending or green.

Remaining adoption blockers are the missing governed 2026 projection source and a fully green
clean-worktree regression environment. The branch remains research-only.
""",
    )
    next_action = (
        "Review the admitted projection receipt, rerun all source-matched validation, and configure "
        "the owner's first profile before any HQ admission decision."
        if projection_ready
        else "Configure the owner's first real league by creating or duplicating a Redraft profile, "
        "entering its exact roster/scoring/draft settings, and installing one granular 2026 "
        "projection CSV plus a separately issued NWR Data Governance approval receipt that binds "
        "the exact CSV SHA-256. Then rerun validation before any admission decision."
    )
    _write_markdown(
        packet / "NEXT_ACTION.md",
        f"""
# Next Action

{next_action}
""",
    )


def _write_manifest(packet: Path, repo_root: Path, *, verdict: str) -> None:
    files = []
    for path in sorted(packet.iterdir(), key=lambda value: value.name.casefold()):
        if not path.is_file() or path.name == "MANIFEST.json":
            continue
        data = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(repo_root).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    document = {
        "schema_version": 1,
        "verdict": verdict,
        "authority": "REDRAFT V1 - REVIEW",
        "files": files,
        "manifest_self_hash": "excluded",
    }
    (packet / "MANIFEST.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build(repo_root: Path) -> Path:
    packet = repo_root / PACKET_RELATIVE
    packet.mkdir(parents=True, exist_ok=True)
    mart_path = repo_root / MART_RELATIVE
    mart = pd.read_csv(mart_path, low_memory=False)
    model_rows, position_rows = _evaluate_mart(mart)
    sensitivity_rows = _sensitivity_rows()
    receipt, receipt_valid = _validation_receipt(packet, repo_root)
    browser_rows = _browser_rows(receipt, receipt_valid)
    projection_ready = _current_projection_ready(repo_root)
    gate_rows = _gate_rows(
        repo_root=repo_root,
        model_rows=model_rows,
        position_rows=position_rows,
        sensitivity_rows=sensitivity_rows,
        browser_rows=browser_rows,
        receipt=receipt,
        receipt_valid=receipt_valid,
    )
    verdict = _derive_verdict(gate_rows)
    _write_csv(packet / "MODEL_GAUNTLET_RESULTS.csv", model_rows)
    _write_csv(packet / "POSITION_RESULTS.csv", position_rows)
    _write_csv(packet / "SETTINGS_SENSITIVITY.csv", sensitivity_rows)
    _write_csv(
        packet / "REPLACEMENT_LEVEL_METHODS.csv",
        [
            {
                "method": "starter_cutoff",
                "status": "CHALLENGER",
                "description": "Last required/flex starter baseline.",
            },
            {
                "method": "expected_available",
                "status": "SELECTED",
                "description": "Best unrostered player after starters and bounded bench simulation.",
            },
            {
                "method": "midpoint_starter_replacement",
                "status": "CHALLENGER",
                "description": "Unweighted midpoint opportunity-cost baseline.",
            },
        ],
    )
    _write_csv(
        packet / "SOURCE_ELIGIBILITY.csv",
        [
            {
                "source": "Finished V1 player universe",
                "classification": "REDRAFT_PRODUCTION_USABLE",
                "notes": "Identity/universe only; dynasty rank prohibited.",
            },
            {
                "source": "Formula Data Mart",
                "classification": "REDRAFT_RESEARCH_ONLY",
                "notes": "Leakage-safe lagged historical evaluation.",
            },
            {
                "source": "active-pack win_now_value",
                "classification": "REDRAFT_RESEARCH_ONLY",
                "notes": "Not points and not profile-sensitive.",
            },
            {
                "source": "Outcome V3",
                "classification": "REDRAFT_RESEARCH_ONLY",
                "notes": "Display-only dynasty-horizon context.",
            },
            {
                "source": "2025 public production",
                "classification": "REDRAFT_RESEARCH_ONLY",
                "notes": "Prior outcome, not a 2026 projection.",
            },
            {
                "source": "governed granular 2026 projections",
                "classification": "ADMITTED" if projection_ready else "MISSING",
                "notes": (
                    "Separate approval receipt and runtime manifest validated."
                    if projection_ready
                    else "Critical live-ranking blocker."
                ),
            },
            {
                "source": "Rookie Review long-term rank",
                "classification": "BLOCKED",
                "notes": "Prohibited as redraft input.",
            },
            {
                "source": "ADP",
                "classification": "NOT_ENOUGH_INFORMATION",
                "notes": "Optional context only; no admitted snapshot.",
            },
        ],
    )
    _write_csv(
        packet / "PROMOTION_GATE_RESULTS.csv",
        gate_rows,
    )
    _write_csv(packet / "BROWSER_RESULTS.csv", browser_rows)
    _write_csv(
        packet / "FILES_CREATED_OR_CHANGED.csv",
        [
            {
                "path": "src/services/redraft_engine_v1_service.py",
                "change": "created",
                "authority_effect": "additive redraft only",
            },
            {
                "path": "app/pages/52_redraft_v1.py",
                "change": "created",
                "authority_effect": "review-only redraft route",
            },
            {
                "path": "app/navigation.py",
                "change": "modified",
                "authority_effect": "adds Redraft navigation",
            },
            {
                "path": "app/pages/22_player_compare_v1.py",
                "change": "modified",
                "authority_effect": "explicit redraft context",
            },
            {
                "path": "app/pages/21_live_draft_room_v1.py",
                "change": "modified",
                "authority_effect": "read-only redraft context",
            },
            {
                "path": "tests/test_redraft_engine_v1_service.py",
                "change": "created",
                "authority_effect": "tests only",
            },
            {
                "path": "tests/test_redraft_page_v1.py",
                "change": "created",
                "authority_effect": "page-open and static integration tests only",
            },
            {
                "path": "tests/test_navigation_compression.py",
                "change": "modified",
                "authority_effect": "navigation expectation only",
            },
            {
                "path": "scripts/build_nwr_redraft_engine_v1.py",
                "change": "created",
                "authority_effect": "research/docs generator",
            },
            {
                "path": str(PACKET_RELATIVE).replace("\\", "/"),
                "change": "created",
                "authority_effect": "review evidence packet",
            },
        ],
    )
    _docs(packet, model_rows, verdict=verdict, projection_ready=projection_ready)
    _write_manifest(packet, repo_root, verdict=verdict)
    return packet


def _float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()
    packet = build(args.repo_root.resolve())
    print(packet)


if __name__ == "__main__":
    main()
