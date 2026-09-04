"""One-command historical calibration readiness entrypoint (section 34).

When the owner says "the historical dataset is at C:\\...", this is the
one command to run:

    python scripts/run_historical_calibration_readiness_v1.py --dataset-dir C:\\path\\to\\dataset

Without --dataset-dir (or when the expected file is missing there), this
runs the SAME pipeline against a deterministic, clearly-labeled SYNTHETIC
dataset instead (section 33) -- proving every stage of the mechanics
works end-to-end before real data ever arrives. Every synthetic output is
marked SYNTHETIC_PIPELINE_TEST_ONLY and must never be read as evidence
about anything real.

Expected real-dataset shape (a contract this script defines, since
docs/codex/HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md states the
required FIELDS but not a file format): a CSV at
`<dataset-dir>/historical_replay_rows.csv` with one row per
(player, season), columns = every
historical_replay_data_adapter_service.REQUIRED_PRE_DRAFT_FIELDS plus
OUTCOME_ONLY_FIELDS; optionally
`<dataset-dir>/historical_picks.csv` (columns: player_id,
identity_status) for the identity-completeness check.

Report sections produced (JSON, plus a short console summary):
DATASET_READINESS_REPORT, LEAKAGE_REPORT, BASELINE_RESULTS,
TEAM_SCORE_CALIBRATION, CHALLENGER_COMPARISON, and three sections
(CHAMPIONSHIP_EQUITY_CALIBRATION, PICK_SCORE_EVALUATION,
COST_OF_WAITING_CALIBRATION) that this pass can name the EXACT blocker
for but not yet compute (they need a historical-row -> RankingResult/
AdpSnapshot adapter this pass did not build -- named explicitly in each
section's own `blocked_reason`, not silently omitted).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from src.services.ai_research_agent_input_service import build_ai_research_agent_input
from src.services.calibration_acceptance_gates_service import (
    ALL_GATE_SPECS,
    evaluate_gate,
)
from src.services.calibration_toolkit_service import (
    PIPELINE_TEST_ONLY,
    REAL_EVIDENCE,
    bucket_team_score_outcomes,
    fit_pick_score_calibrator,
)
from src.services.draft_strategy_framework_service import (
    STRATEGY_GREEDY_NWR,
    STRATEGY_PLATFORM_ADP,
    greedy_nwr_strategy,
    platform_adp_strategy,
)
from src.services.failure_analysis_service import (
    EvaluationRecord,
    slice_by_every_dimension,
)
from src.services.historical_decision_state_service import (
    build_historical_decision_state,
    evaluate_historical_candidates,
)
from src.services.historical_draft_replay_engine_service import run_historical_draft_replay
from src.services.historical_ranking_bridge_service import (
    HistoricalRankingBridgeError,
    build_ranking_result_from_historical_rows,
)
from src.services.historical_replay_data_adapter_service import (
    chronological_split,
    load_historical_replay_dataset,
    validate_historical_dataset,
)
from src.services.model_health_dashboard_service import (
    HEALTH_AREA_PICK_SCORE,
    HEALTH_AREA_TEAM_SCORE,
    ModelHealthMetric,
    build_model_health_report,
)
from src.services.point_in_time_feature_store_service import (
    FAMILY_MARKET_ADP,
    FAMILY_NWR_COMPONENT_SCORES,
    PointInTimeFeatureStore,
    known_feature_value,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RosterSettings,
    ScoringSettings,
)
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import simulate_comparable_leagues
from src.services.strategy_tournament_service import run_strategy_tournament

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_LABEL = "SYNTHETIC_PIPELINE_TEST_ONLY"
STATUS_PASS_READY_FOR_REPLAY = "PASS_READY_FOR_REPLAY"
STATUS_BLOCKED_NO_DATASET_FOUND = "BLOCKED_NO_DATASET_FOUND"

CALIBRATION_HOOK_BLOCKED_REASON = (
    "Needs a historical-row -> RankingResult/AdpSnapshot adapter this pass did not "
    "build -- shadow_numeric_authorities_service's team_score/championship_equity/"
    "pick_score/cost_of_waiting are real and tested, but they consume a RankingResult "
    "pool, not raw historical_replay_rows.csv rows. Building that adapter is the exact "
    "next task, not attempted here to avoid a rushed, undertested bridge."
)


# --- Synthetic fixture (section 33) -----------------------------------------


def synthetic_dataset_rows(
    seed: int = 20260903,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """A deterministic, clearly-synthetic 2-season, 24-player-per-season
    dataset conforming exactly to the real contract's required fields,
    plus one extra `nwr_overall_rank` column (not a blocked-token name)
    so GREEDY_NWR has something to rank by. Every player_id and every
    value here is fabricated -- never presented as real evidence."""
    rows: list[dict[str, Any]] = []
    for season, draft_date, prior_date in (
        (2023, "2023-08-25", "2023-08-24"),
        (2024, "2024-08-23", "2024-08-22"),
    ):
        for i in range(24):
            player_id = f"SYN-{season}-{i:02d}"
            rows.append(
                {
                    "player_id": player_id,
                    "player_name": f"Synthetic Player {season}-{i:02d}",
                    "position": ("QB", "RB", "WR", "TE")[i % 4],
                    "team": f"T{i % 8}",
                    "season": season,
                    "draft_date": draft_date,
                    "projection_as_of": prior_date,
                    "adp_as_of": prior_date,
                    "platform_adp": float(i + 1),
                    "status_as_of": draft_date,
                    "scoring_format": "ppr",
                    "nwr_overall_rank": float(24 - i),  # deliberately reversed vs ADP
                    # Real projection stat-category columns (historical_ranking_bridge_
                    # service.PROJECTION_STAT_FIELDS) so the bridge can build a real
                    # RankingResult -- every value here is fabricated, never real evidence.
                    "passing_yards": 4000.0 - 100 * i if i % 4 == 0 else 0.0,
                    "passing_tds": 25.0 if i % 4 == 0 else 0.0,
                    "rushing_yards": 1200.0 - 50 * i if i % 4 == 1 else 0.0,
                    "rushing_tds": 8.0 if i % 4 == 1 else 0.0,
                    "receiving_yards": 1000.0 - 30 * i if i % 4 in (2, 3) else 0.0,
                    "receptions": 80.0 if i % 4 in (2, 3) else 0.0,
                    "receiving_tds": 7.0 if i % 4 in (2, 3) else 0.0,
                    "realized_weekly_points": round(300.0 - 8.0 * i + (seed % 7), 2),
                    # Comfortably past MATURITY_MIN_DAYS_AFTER_DRAFT (140d).
                    "outcome_as_of": (
                        date.fromisoformat(draft_date) + timedelta(days=150)
                    ).isoformat(),
                }
            )
    # A small synthetic historical_picks set so IDENTITY_REPORT (section 15)
    # exercises a real resolved/unresolved check, not just an untested
    # "checked=False" path. Every id is fabricated, same as the rows above.
    picks = [
        {"player_id": "SYN-2023-00", "identity_status": "RESOLVED"},
        {"player_id": "SYN-2023-01", "identity_status": "RESOLVED"},
        {"player_id": "SYN-2023-99", "identity_status": "AMBIGUOUS_NAME_MATCH"},
    ]
    return rows, picks


# --- Real-dataset loading ----------------------------------------------------


def load_real_dataset_rows(
    dataset_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    rows_path = dataset_dir / "historical_replay_rows.csv"
    if not rows_path.is_file():
        return None
    with rows_path.open(newline="", encoding="utf-8") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    for row in rows:
        if row.get("season"):
            try:
                row["season"] = int(row["season"])
            except ValueError:
                pass
        if row.get("platform_adp"):
            try:
                row["platform_adp"] = float(row["platform_adp"])
            except ValueError:
                pass
    picks_path = dataset_dir / "historical_picks.csv"
    picks: list[dict[str, Any]] = []
    if picks_path.is_file():
        with picks_path.open(newline="", encoding="utf-8") as handle:
            picks = [dict(row) for row in csv.DictReader(handle)]
    return rows, picks


# --- Pipeline stages ----------------------------------------------------------


def build_feature_store(
    rows: Sequence[dict[str, Any]], *, has_nwr_rank: bool
) -> PointInTimeFeatureStore:
    values = []
    for row in rows:
        player_id = str(row["player_id"])
        season = int(row["season"])
        draft_date = str(row["draft_date"])
        adp = row.get("platform_adp")
        if adp is not None and str(adp).strip() != "":
            values.append(
                known_feature_value(
                    player_id=player_id, season=season, as_of=draft_date,
                    feature_name="market.overall_adp", feature_family=FAMILY_MARKET_ADP,
                    value=float(adp), source="historical_dataset",
                    source_as_of=str(row.get("adp_as_of") or draft_date),
                    retrieved_at=draft_date,
                )
            )
        if has_nwr_rank and row.get("nwr_overall_rank") is not None:
            values.append(
                known_feature_value(
                    player_id=player_id, season=season, as_of=draft_date,
                    feature_name="nwr_component_scores.overall_rank",
                    feature_family=FAMILY_NWR_COMPONENT_SCORES,
                    value=float(row["nwr_overall_rank"]), source="historical_dataset",
                    source_as_of=draft_date, retrieved_at=draft_date,
                )
            )
    return PointInTimeFeatureStore().with_values(values)


def run_pipeline(
    rows: list[dict[str, Any]], picks: list[dict[str, Any]], *, synthetic: bool
) -> dict[str, Any]:
    label = SYNTHETIC_LABEL if synthetic else "REAL_DATASET"
    validation = validate_historical_dataset(rows, picks or None)
    dataset_readiness_report = {
        "label": label,
        "status": STATUS_PASS_READY_FOR_REPLAY if validation.status == "OK" else validation.status,
        "row_count": validation.schema.row_count,
        "seasons": sorted({int(r["season"]) for r in rows if r.get("season") is not None}),
        "missing_field_rows": len(validation.schema.missing_field_rows),
        "duplicate_player_seasons": len(validation.duplicate_player_seasons),
        "immature_outcome_rows": len(validation.immature_outcome_rows),
    }
    leakage_report = {
        "label": label,
        "valid": validation.leakage.valid,
        "blocked_column_rows": len(validation.leakage.blocked_column_rows),
        "future_dated_rows": len(validation.leakage.future_dated_rows),
        "outcome_before_draft_rows": len(validation.leakage.outcome_before_draft_rows),
    }
    report: dict[str, Any] = {
        "label": label,
        "DATASET_READINESS_REPORT": dataset_readiness_report,
        "LEAKAGE_REPORT": leakage_report,
    }
    if validation.status != "OK":
        report["BASELINE_RESULTS"] = {"blocked_reason": f"Dataset blocked: {validation.status}"}
        return report

    dataset = load_historical_replay_dataset(rows)
    seasons = sorted(dataset.seasons)
    if len(seasons) >= 2:
        split = chronological_split(
            dataset, train_seasons=seasons[:-1], validate_seasons=[], test_seasons=seasons[-1:],
        )
        report["CHRONOLOGICAL_SPLIT"] = {
            "train_seasons": split.train_seasons,
            "validate_seasons": split.validate_seasons,
            "test_seasons": split.test_seasons,
        }

    has_nwr_rank = any("nwr_overall_rank" in row for row in rows)
    feature_store = build_feature_store(rows, has_nwr_rank=has_nwr_rank)
    rows_by_season: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        rows_by_season.setdefault(int(row["season"]), []).append(row)

    strategies = {STRATEGY_PLATFORM_ADP: platform_adp_strategy}
    if has_nwr_rank:
        strategies[STRATEGY_GREEDY_NWR] = greedy_nwr_strategy

    baseline_results: dict[str, Any] = {}
    challenger_totals: dict[str, list[float]] = {}
    for season, season_rows in rows_by_season.items():
        player_ids = [str(r["player_id"]) for r in season_rows]
        draft_date = str(season_rows[0]["draft_date"])
        realized_by_player = {
            str(r["player_id"]): float(r.get("realized_weekly_points") or 0.0) for r in season_rows
        }
        team_count = min(4, max(2, len(player_ids) // 6))
        rounds = max(1, len(player_ids) // team_count)
        for name, strategy in strategies.items():
            receipt = run_historical_draft_replay(
                season=season, team_count=team_count, rounds=rounds,
                available_player_ids=player_ids, feature_store=feature_store,
                as_of=draft_date, owner_slot=1, owner_strategy_name=name,
                owner_strategy=strategy, opponent_strategy_name=STRATEGY_PLATFORM_ADP,
                opponent_strategy=platform_adp_strategy, seed=20260903,
            )
            owner_roster = receipt.rosters_by_slot.get(1, ())
            total_realized = round(
                sum(realized_by_player.get(pid, 0.0) for pid in owner_roster), 2
            )
            baseline_results[f"{season}:{name}"] = {
                "picks": len(receipt.picks), "owner_roster_size": len(owner_roster),
                "owner_roster_realized_production_total": total_realized,
            }
            challenger_totals.setdefault(name, []).append(total_realized)

    report["BASELINE_RESULTS"] = baseline_results
    report["TEAM_SCORE_CALIBRATION"] = {
        "label": label,
        "method": "owner-roster realized production total per strategy per season "
        "(a real proxy; full Team Score percentile calibration needs the RankingResult "
        "adapter named in CHAMPIONSHIP_EQUITY_CALIBRATION below)",
        "per_strategy_mean_realized_production": {
            name: round(sum(values) / len(values), 2)
            for name, values in challenger_totals.items()
            if values
        },
    }
    if len(challenger_totals) >= 2:
        report["CHALLENGER_COMPARISON"] = {
            name: round(sum(values) / len(values), 2) for name, values in challenger_totals.items()
        }
    else:
        report["CHALLENGER_COMPARISON"] = {
            "blocked_reason": "Only one baseline strategy had resolvable features this run "
            "(need at least two comparable strategies -- e.g. a real NWR-rank feature "
            "was not present in this dataset)."
        }
    for section in (
        "CHAMPIONSHIP_EQUITY_CALIBRATION", "PICK_SCORE_EVALUATION", "COST_OF_WAITING_CALIBRATION",
        "STRATEGY_TOURNAMENT", "PICK_SCORE_CALIBRATION", "FAILURE_SLICES", "CALIBRATION_GATES",
    ):
        report[section] = {"blocked_reason": CALIBRATION_HOOK_BLOCKED_REASON}

    identity_report: dict[str, Any] = {"checked": validation.identity is not None}
    if validation.identity is not None:
        identity_report["resolved_pick_count"] = validation.identity.resolved_pick_count
        identity_report["unresolved_pick_count"] = len(validation.identity.unresolved_picks)
    report["IDENTITY_REPORT"] = identity_report

    _wire_bridge_dependent_sections(
        report, rows_by_season=rows_by_season, label=label, data_source=(
            PIPELINE_TEST_ONLY if synthetic else REAL_EVIDENCE
        ),
    )
    report["MODEL_HEALTH_REPORT"] = _build_model_health_report(report)
    report["AI_RESEARCH_AGENT_INPUT"] = _build_ai_research_agent_input_summary(report)
    return report


def _profile_for_season(season: int, *, team_count: int, rounds: int) -> LeagueProfile:
    return LeagueProfile(
        profile_id=f"historical-{season}", league_name=f"Historical {season}", season=season,
        team_count=team_count,
        roster=RosterSettings(
            qb=1, rb=1, wr=1, te=1, flex=1, superflex=0, k=0, dst=0, bench_size=1
        ),
        scoring=ScoringSettings(reception=1.0),
        draft=DraftContext(rounds=rounds, draft_slot=1),
    )


def _wire_bridge_dependent_sections(
    report: dict[str, Any], *, rows_by_season: dict[int, list[dict[str, Any]]],
    label: str, data_source: str,
) -> None:
    """Replaces the CHAMPIONSHIP_EQUITY_CALIBRATION/PICK_SCORE_EVALUATION/
    COST_OF_WAITING_CALIBRATION/STRATEGY_TOURNAMENT/PICK_SCORE_CALIBRATION/
    FAILURE_SLICES/CALIBRATION_GATES blocked_reason placeholders with real
    content WHEN the historical-row -> RankingResult bridge succeeds for a
    season (i.e. real projection stat components were present). Leaves the
    honest blocked_reason in place otherwise -- never fabricates."""
    tournament_all: dict[str, Any] = {}
    equity_all: dict[str, Any] = {}
    pick_score_all: dict[str, Any] = {}
    cow_all: dict[str, Any] = {}
    failure_records: list[EvaluationRecord] = []
    utility_quality_pairs: list[tuple[float, float]] = []
    team_score_value_pairs: list[tuple[float, float]] = []

    for season, season_rows in rows_by_season.items():
        player_ids = [str(r["player_id"]) for r in season_rows]
        team_count = min(4, max(2, len(player_ids) // 6))
        rounds = max(1, len(player_ids) // team_count)
        profile = _profile_for_season(season, team_count=team_count, rounds=rounds)
        try:
            bridge = build_ranking_result_from_historical_rows(
                season_rows, profile, generated_at_utc="2026-09-03T00:00:00Z",
                source_sha256="0" * 64,
            )
        except HistoricalRankingBridgeError:
            continue
        if not bridge.ranking.ready:
            continue

        realized_by_player = {
            str(r["player_id"]): float(r.get("realized_weekly_points") or 0.0) for r in season_rows
        }
        strategies = {
            STRATEGY_PLATFORM_ADP: platform_adp_strategy,
            STRATEGY_GREEDY_NWR: greedy_nwr_strategy,
        }
        draft_date_str = str(season_rows[0]["draft_date"])
        tournament = run_strategy_tournament(
            season=season, league_format_label=f"{team_count}T_1QB", team_count=team_count,
            rounds=rounds, owner_slot=1, available_player_ids=bridge.included_player_ids,
            feature_store=bridge.feature_store, as_of=draft_date_str, seed=20260903,
            strategies=strategies,
        )
        tournament_all[str(season)] = [
            {
                "strategy_name": entry.strategy_name, "final_roster_size": len(entry.final_roster),
                "construction_failure_count": entry.construction_failure_count,
                "runtime_seconds": entry.runtime_seconds,
                "realized_production_total": round(
                    sum(realized_by_player.get(pid, 0.0) for pid in entry.final_roster), 2
                ),
            }
            for entry in tournament
        ]
        for entry in tournament:
            for player_id in entry.final_roster:
                position = next(
                    (row.position for row in bridge.ranking.rows if row.player_id == player_id),
                    None,
                )
                if position is None:
                    continue
                failure_records.append(
                    EvaluationRecord(
                        record_id=f"{season}:{entry.strategy_name}:{player_id}",
                        dimensions={
                            "position": position, "strategy": entry.strategy_name,
                            "season": season,
                        },
                        outcome_value=realized_by_player.get(player_id, 0.0),
                    )
                )

        provenance = build_score_provenance(
            league_profile_hash="historical", roster_state_hash="empty",
            available_player_hash=bridge.ranking.projection_sha256,
            universe_hash=bridge.ranking.projection_sha256, projection_model_version="bridge-v1",
            market_snapshot_hash=bridge.adp.source_sha256, feature_set_version="bridge-v1",
            team_score_version="ts-v1", championship_equity_version="ce-v1",
            pick_score_version="ps-v1", optimizer_version="opt-v1", seed=20260903,
            simulation_count=50, timestamp_utc="2026-09-03T00:00:00Z",
        )
        comparable_leagues = simulate_comparable_leagues(
            profile, bridge.ranking, (), bridge.adp, trials=2, base_seed=20260903,
        )
        state = build_historical_decision_state(
            bridge, season=season, as_of=str(season_rows[0]["draft_date"]), pick_number=1,
            round_number=1, owner_slot=1, rosters_by_slot={1: ()},
            strategy_version=STRATEGY_GREEDY_NWR,
        )
        top_candidates = [row.player_id for row in bridge.ranking.rows[:4]]
        bundle = evaluate_historical_candidates(
            state, candidate_player_ids=top_candidates, comparable_leagues=comparable_leagues,
            provenance=provenance,
        )
        equity_all[str(season)] = {
            "current_win_probability": bundle.current_championship_equity.win_probability,
            "candidates": [
                {"player_id": c.player_id, "championship_equity_after": c.championship_equity_after,
                 "equity_gain": c.equity_gain}
                for c in bundle.candidates
            ],
            "label": label,
        }
        pick_score_all[str(season)] = {
            "candidates": [
                {"player_id": c.player_id, "pick_score": c.pick_score,
                 "raw_decision_utility": c.raw_decision_utility}
                for c in bundle.candidates
            ],
            "label": label,
        }
        cow_all[str(season)] = {
            "candidates": [
                {"player_id": c.player_id, "cost_of_waiting": c.cost_of_waiting,
                 "make_it_back_probability": c.make_it_back_probability}
                for c in bundle.candidates
            ],
            "label": label,
        }
        for candidate in bundle.candidates:
            realized = realized_by_player.get(candidate.player_id)
            if realized is not None:
                utility_quality_pairs.append((candidate.raw_decision_utility, realized))
                team_score_value_pairs.append((candidate.team_score_after, realized))

    if tournament_all:
        report["STRATEGY_TOURNAMENT"] = tournament_all
        report["CHAMPIONSHIP_EQUITY_CALIBRATION"] = equity_all
        report["PICK_SCORE_EVALUATION"] = pick_score_all
        report["COST_OF_WAITING_CALIBRATION"] = cow_all

        if len(utility_quality_pairs) >= 2:
            calibrator = fit_pick_score_calibrator(utility_quality_pairs, data_source=data_source)
            report["PICK_SCORE_CALIBRATION"] = {
                "model_version": calibrator.model_version, "data_source": calibrator.data_source,
                "sample_size": calibrator.isotonic.sample_size,
            }
        if len(team_score_value_pairs) >= 2:
            bucket_report = bucket_team_score_outcomes(
                team_score_value_pairs, data_source=data_source, bucket_count=3,
            )
            report["TEAM_SCORE_CALIBRATION"]["bucket_report"] = {
                "monotonic": bucket_report.monotonic, "spearman": bucket_report.spearman,
                "sample_size": bucket_report.sample_size,
            }

        if failure_records:
            slices = slice_by_every_dimension(
                failure_records, dimension_names=["position", "strategy", "season"],
            )
            report["FAILURE_SLICES"] = {
                name: [
                    {"dimension_value": s.dimension_value, "sample_size": s.sample_size,
                     "mean_outcome": s.mean_outcome, "low_confidence": s.low_confidence}
                    for s in slice_report.slices
                ]
                for name, slice_report in slices.items()
            }

        observed_for_gates: dict[str, Any] = {}
        team_score_bucket_report = report["TEAM_SCORE_CALIBRATION"].get("bucket_report")
        if team_score_bucket_report is not None:
            observed_for_gates["monotonic"] = team_score_bucket_report["monotonic"]
            observed_for_gates["spearman"] = team_score_bucket_report["spearman"]
        gate_results = [
            evaluate_gate(spec, observed=observed_for_gates)
            for spec in ALL_GATE_SPECS if spec.subject == "TEAM_SCORE"
        ]
        report["CALIBRATION_GATES"] = {
            "TEAM_SCORE": [
                {"gate_id": g.gate_id, "status": g.status, "detail": g.detail} for g in gate_results
            ]
        }


def _build_model_health_report(report: dict[str, Any]) -> dict[str, Any]:
    metrics: list[ModelHealthMetric] = []
    team_calibration = report.get("TEAM_SCORE_CALIBRATION", {})
    bucket_report = (
        team_calibration.get("bucket_report") if isinstance(team_calibration, dict) else None
    )
    if bucket_report and bucket_report.get("spearman") is not None:
        metrics.append(
            ModelHealthMetric(
                health_area=HEALTH_AREA_TEAM_SCORE, metric_name="spearman",
                value=float(bucket_report["spearman"]),
                sample_size=int(bucket_report["sample_size"]),
            )
        )
    pick_score_calibration = report.get("PICK_SCORE_CALIBRATION")
    if isinstance(pick_score_calibration, dict) and "sample_size" in pick_score_calibration:
        metrics.append(
            ModelHealthMetric(
                health_area=HEALTH_AREA_PICK_SCORE, metric_name="calibration_sample_size",
                value=float(pick_score_calibration["sample_size"]),
                sample_size=int(pick_score_calibration["sample_size"]),
            )
        )
    if not metrics:
        return {"metrics": [], "note": "No model-health metrics were computable this run."}
    health_report = build_model_health_report(metrics)
    return {
        "low_confidence_count": health_report.low_confidence_count,
        "total_sample_size": health_report.total_sample_size,
        "metric_count": len(health_report.metrics),
    }


def _build_ai_research_agent_input_summary(report: dict[str, Any]) -> dict[str, Any]:
    failure_slices = report.get("FAILURE_SLICES")
    if not failure_slices or "blocked_reason" in failure_slices:
        return {"note": "No failure slices were computable this run -- nothing to hand off."}
    payload = build_ai_research_agent_input(
        metric_summaries={}, failure_slices={}, feature_availability={},
        challenger_metadata={}, sample_sizes={
            name: sum(row["sample_size"] for row in rows) for name, rows in failure_slices.items()
        },
        confidence={}, known_leakage_constraints=("source_as_of < draft_date",),
        generated_at_utc="2026-09-03T00:00:00Z",
    )
    return {
        "sample_sizes": payload.sample_sizes,
        "known_leakage_constraints": payload.known_leakage_constraints,
        "note": "Structured evidence only -- see FAILURE_SLICES/STRATEGY_TOURNAMENT for detail.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-dir", type=Path, default=None,
        help="Directory containing historical_replay_rows.csv (+ optional historical_picks.csv). "
        "Omit to run the synthetic pipeline test instead.",
    )
    default_out = REPO_ROOT / "docs" / "codex" / "HISTORICAL_CALIBRATION_READINESS_REPORT.json"
    parser.add_argument("--out", type=Path, default=default_out)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    synthetic = True
    rows: list[dict[str, Any]]
    picks: list[dict[str, Any]]
    if args.dataset_dir is not None:
        loaded = load_real_dataset_rows(args.dataset_dir)
        if loaded is None:
            report = {
                "label": "REAL_DATASET",
                "DATASET_READINESS_REPORT": {
                    "status": STATUS_BLOCKED_NO_DATASET_FOUND,
                    "blocked_reason": (
                        f"No historical_replay_rows.csv found under {args.dataset_dir}"
                    ),
                },
            }
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
            print(json.dumps(report["DATASET_READINESS_REPORT"], indent=2))
            return 1
        rows, picks = loaded
        synthetic = False
    else:
        rows, picks = synthetic_dataset_rows()

    report = run_pipeline(rows, picks, synthetic=synthetic)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"Label: {report['label']}")
    print(f"DATASET_READINESS_REPORT status: {report['DATASET_READINESS_REPORT']['status']}")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
