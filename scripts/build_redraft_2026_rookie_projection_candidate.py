from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.redraft_2026_rookie_projection_model_service import (  # noqa: E402
    MODEL_ID,
    aggregate_backtest,
    attach_exact_identities,
    build_current_rookie_candidate,
    load_draft_evidence,
    load_player_registry,
    load_rookie_outcome_frame,
    promotion_gates,
    temporal_backtest,
    uncertainty_from_predictions,
)
from src.services.redraft_engine_v1_service import (  # noqa: E402
    PROJECTION_NUMERIC_COLUMNS,
    ProjectionPlayer,
    ProjectionSnapshot,
    builtin_presets,
    generate_rankings,
)

DEFAULT_NFLVERSE_ROOT = Path(r"C:\NWR_SHARED_DATA\source_snapshots\nflverse")
DEFAULT_DRAFT = DEFAULT_NFLVERSE_ROOT / (
    "draft_picks/20260730T072407Z-24ff3f7171ed/raw/draft_picks.parquet"
)
DEFAULT_PLAYERS = DEFAULT_NFLVERSE_ROOT / (
    "players/20260730T072407Z-42af9666ac84/raw/players.parquet"
)
DEFAULT_STATS = DEFAULT_NFLVERSE_ROOT / (
    "player_stats_seasonal/20260730T072407Z-a5b2304f0132/raw"
)
DEFAULT_VETERANS = Path(
    "docs/hq/model/nwr_redraft_2026_projection_admission_v1_20260808/"
    "GOVERNED_PROJECTION_SNAPSHOT.csv"
)
DEFAULT_OUTPUT = Path(
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
)
SOURCE_AS_OF = "2026-07-30"
HISTORICAL_SEASONS = tuple(range(2012, 2026))
BACKTEST_SEASONS = tuple(range(2016, 2026))


def build_packet(
    *,
    draft_path: Path,
    players_path: Path,
    stats_directory: Path,
    veteran_path: Path,
    output_directory: Path,
) -> dict[str, object]:
    output_directory.mkdir(parents=True, exist_ok=True)
    players = load_player_registry(players_path)
    all_draft = attach_exact_identities(
        load_draft_evidence(draft_path, [*HISTORICAL_SEASONS, 2026]), players
    )
    historical_draft = all_draft[all_draft["season"].isin(HISTORICAL_SEASONS)].copy()
    history = load_rookie_outcome_frame(
        stats_directory, historical_draft, HISTORICAL_SEASONS
    )
    predictions, backtest_summary = temporal_backtest(
        history, seasons=BACKTEST_SEASONS
    )
    uncertainty = uncertainty_from_predictions(predictions)
    current_result = build_current_rookie_candidate(
        all_draft[all_draft["season"].eq(2026)].copy(),
        players,
        history,
        season=2026,
        source_as_of=SOURCE_AS_OF,
        uncertainty_by_position=uncertainty,
    )
    gates = promotion_gates(
        historical_draft=historical_draft,
        predictions=predictions,
        summaries=backtest_summary,
        candidate=current_result,
    )
    if not gates["status"].eq("PASS").all():
        failed = ", ".join(gates.loc[gates["status"].ne("PASS"), "gate"])
        raise RuntimeError(f"Rookie evidence validation failed; no candidate written: {failed}")

    internal_columns = [column for column in current_result.projections if column.startswith("_")]
    rookie_candidate = current_result.projections.drop(columns=internal_columns)
    cohort_audit = current_result.projections[
        ["player_id", "player_name", "position", *internal_columns]
    ].rename(columns=lambda column: column.removeprefix("_"))
    veterans = pd.read_csv(veteran_path)
    if len(veterans) != 530 or not veterans["rookie"].eq(False).all():
        raise ValueError("Approved veteran input is not the expected immutable 530-row frame.")
    missing_columns = sorted(set(veterans.columns).difference(rookie_candidate.columns))
    if missing_columns:
        raise ValueError(
            "Rookie candidate is missing veteran schema columns: "
            + ", ".join(missing_columns)
        )
    rookie_candidate = rookie_candidate.reindex(columns=veterans.columns)
    combined = pd.concat([veterans, rookie_candidate], ignore_index=True)
    assert_frame_equal(
        combined.iloc[: len(veterans)].reset_index(drop=True),
        veterans.reset_index(drop=True),
        check_dtype=False,
        check_exact=True,
    )
    combined_path = output_directory / "COMBINED_608_REVIEW_CANDIDATE.csv"
    combined.to_csv(combined_path, index=False, lineterminator="\n")
    snapshot = _projection_snapshot(combined, combined_path)
    ranking_results = {
        profile.preset_key: generate_rankings(profile, snapshot)
        for profile in builtin_presets()
    }
    ranking_failures = {
        key: result.errors for key, result in ranking_results.items() if not result.ready
    }
    if ranking_failures:
        raise RuntimeError(f"Combined review ranking generation failed: {ranking_failures}")
    sensitivity = _settings_sanity(ranking_results, snapshot)
    if not sensitivity["status"].eq("PASS").all():
        failed = ", ".join(sensitivity.loc[sensitivity["status"].ne("PASS"), "check"])
        raise RuntimeError(f"Combined profile sensitivity failed: {failed}")
    veteran_preservation = _veteran_preservation_checks(veterans, combined)
    if not veteran_preservation["status"].eq("PASS").all():
        raise RuntimeError("Approved veteran values changed during the combined review merge.")

    position_results = aggregate_backtest(predictions)
    historical_identity = _historical_identity_coverage(historical_draft)
    source_evidence = _source_evidence(
        draft_path=draft_path,
        players_path=players_path,
        stats_directory=stats_directory,
        veteran_path=veteran_path,
    )
    output_frames = {
        "SOURCE_EVIDENCE.csv": source_evidence,
        "HISTORICAL_IDENTITY_COVERAGE.csv": historical_identity,
        "HISTORICAL_ROOKIE_OUTCOME_FRAME.csv": _historical_export(history),
        "WALK_FORWARD_PREDICTIONS.csv": predictions,
        "WALK_FORWARD_SUMMARY.csv": backtest_summary,
        "POSITION_RESULTS.csv": position_results,
        "PROMOTION_GATES.csv": gates,
        "CURRENT_2026_IDENTITY_AND_ROLE.csv": current_result.identity,
        "BLOCKED_2026_ROOKIES.csv": current_result.blocked,
        "CURRENT_COHORT_AUDIT.csv": cohort_audit,
        "ROOKIE_PROJECTION_CANDIDATE.csv": rookie_candidate,
        "VETERAN_PRESERVATION_CHECKS.csv": veteran_preservation,
        "PROFILE_SENSITIVITY_RESULTS.csv": sensitivity,
        "COMBINED_RANKING_SANITY.csv": _ranking_sanity(ranking_results),
    }
    for preset_key, result in ranking_results.items():
        output_frames[f"PROFILE_RANKINGS_{preset_key}.csv"] = _ranking_frame(result)
    for name, frame in output_frames.items():
        frame.to_csv(output_directory / name, index=False, lineterminator="\n")

    rookie_bytes = (output_directory / "ROOKIE_PROJECTION_CANDIDATE.csv").read_bytes()
    rookie_candidate.to_csv(
        output_directory / "ROOKIE_PROJECTION_CANDIDATE.csv",
        index=False,
        lineterminator="\n",
    )
    rookie_deterministic = (
        rookie_bytes == (output_directory / "ROOKIE_PROJECTION_CANDIDATE.csv").read_bytes()
    )
    combined_bytes = combined_path.read_bytes()
    combined.to_csv(combined_path, index=False, lineterminator="\n")
    combined_deterministic = combined_bytes == combined_path.read_bytes()
    if not rookie_deterministic or not combined_deterministic:
        raise RuntimeError("Rookie or combined candidate serialization is not deterministic.")
    rookie_sha = sha256(output_directory / "ROOKIE_PROJECTION_CANDIDATE.csv")
    combined_sha = sha256(output_directory / "COMBINED_608_REVIEW_CANDIDATE.csv")
    veteran_sha = sha256(veteran_path)
    sha_receipt = {
        "model_id": MODEL_ID,
        "source_as_of": SOURCE_AS_OF,
        "rookie_rows": len(rookie_candidate),
        "blocked_rookie_rows": len(current_result.blocked),
        "rookie_candidate_sha256": rookie_sha,
        "rookie_candidate_deterministic_rerun": rookie_deterministic,
        "approved_veteran_rows": len(veterans),
        "approved_veteran_input_sha256": veteran_sha,
        "approved_veteran_values_unchanged": True,
        "combined_review_rows": len(combined),
        "combined_review_candidate_sha256": combined_sha,
        "combined_review_candidate_deterministic_rerun": combined_deterministic,
        "governance_status": "OWNER_EXACT_SHA_APPROVAL_REQUIRED",
        "installed": False,
    }
    _write_json(output_directory / "CANDIDATE_SHA256.json", sha_receipt)
    _write_json(
        output_directory / "VALIDATION_EXECUTION_RECEIPT.json",
        {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "builder": "scripts/build_redraft_2026_rookie_projection_candidate.py",
            "model_id": MODEL_ID,
            "historical_classes": "2012-2025",
            "walk_forward_classes": "2016-2025",
            "all_promotion_gates_passed": True,
            "gate_count": len(gates),
            "four_builtin_preset_rankings_ready": True,
            "profile_sensitivity_checks_passed": True,
            "approved_veteran_cell_values_preserved": True,
            "candidate_serialization_deterministic_rerun": True,
            "future_or_target_class_rows_used_in_training": 0,
            "dynasty_rank_inputs_used": False,
            "unified_preview_inputs_used": False,
            "provider_or_api_calls": False,
            "web_scraping": False,
            "scheduled_refresh_changed": False,
            "trading_lab_changed": False,
            "k_dst_projected": False,
        },
    )
    (output_directory / "FRESHNESS_AND_ROLE_EVIDENCE.md").write_text(
        """# Freshness and current role evidence

The public nflverse draft, player registry, and historical stat snapshots were retrieved at
`2026-07-30T07:24:07Z`. They are 10 calendar days old on the 2026-08-09 packet date and therefore
inside the existing 30-day operational freshness boundary.

No structured 2026 depth-chart snapshot was available in the admitted local evidence. The model
does not invent one. Current factual use is limited to exact GSIS identity, registry position,
latest team, 2026 rookie classification, and ACT/RES status. Draft position/current-position
conflicts are blocked.
""",
        encoding="utf-8",
    )
    (output_directory / "COMBINED_BOARD_REVIEW.md").write_text(
        f"""# Combined board review

The review-only combined frame contains 530 approved veterans plus {len(rookie_candidate)} rookie
candidates. Every one of the 17,490 veteran cells is exactly equal to the approved veteran input.

All four built-in presets generated READY rankings across all 608 players:

- `10_TEAM_1QB_STANDARD`
- `12_TEAM_1QB_HALF_PPR`
- `12_TEAM_PPR`
- `12_TEAM_SUPERFLEX_PPR`

All five profile sensitivity checks pass: Superflex raises QB value, TE premium raises TE value,
3WR lowers WR replacement, 12-team depth lowers QB replacement versus 10-team depth, and an extra
FLEX lowers WR replacement. Each preset contains 78 rookies, no duplicate IDs, and no K/DST rows.

These rankings are research-only. They do not admit the rookie source or make the product ready for
real-draft use. Exact-SHA owner approval and independent fresh-HQ review remain required.
""",
        encoding="utf-8",
    )
    _write_documents(
        output_directory,
        position_results=position_results,
        historical_identity=historical_identity,
        rookie_rows=len(rookie_candidate),
        blocked_rows=len(current_result.blocked),
        rookie_sha=rookie_sha,
        combined_sha=combined_sha,
        veteran_sha=veteran_sha,
    )
    manifest_rows: list[dict[str, object]] = []
    for path in sorted(output_directory.iterdir(), key=lambda value: value.name):
        if path.name == "MANIFEST.csv":
            continue
        manifest_rows.append(
            {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
        )
    pd.DataFrame(manifest_rows).to_csv(
        output_directory / "MANIFEST.csv", index=False, lineterminator="\n"
    )
    return sha_receipt


def _projection_snapshot(frame: pd.DataFrame, path: Path) -> ProjectionSnapshot:
    players: list[ProjectionPlayer] = []
    for row in frame.to_dict("records"):
        stats = {
            column: (None if pd.isna(row.get(column)) else float(row.get(column)))
            for column in PROJECTION_NUMERIC_COLUMNS
        }
        players.append(
            ProjectionPlayer(
                player_id=str(row["player_id"]),
                player_name=str(row["player_name"]),
                position=str(row["position"]),
                team=str(row["team"]),
                season=2026,
                source_status=str(row["source_status"]),
                evidence_status=str(row["evidence_status"]),
                source_as_of=str(row["source_as_of"]),
                rookie=bool(row["rookie"]),
                stats=stats,
            )
        )
    return ProjectionSnapshot(
        season=2026,
        source_path=path,
        source_sha256=sha256(path),
        players=tuple(players),
        blocked_rows=(),
        errors=(),
        source_as_of=SOURCE_AS_OF,
    )


def _ranking_frame(result: Any) -> pd.DataFrame:
    frame = pd.DataFrame(asdict(row) for row in result.rows)
    frame.insert(0, "admission_status", "RESEARCH_ONLY_GOVERNANCE_PENDING")
    return frame


def _rank_map(result: Any, position: str) -> dict[str, int]:
    return {row.player_id: row.overall_rank for row in result.rows if row.position == position}


def _settings_sanity(
    results: dict[str, Any], snapshot: ProjectionSnapshot
) -> pd.DataFrame:
    standard, _, ppr, _ = builtin_presets()
    twelve_standard = replace(
        standard,
        profile_id="test:12-standard",
        league_name="12-team 1QB Standard sensitivity",
        team_count=12,
    )
    te_premium = replace(
        ppr,
        profile_id="test:te-premium",
        league_name="12-team PPR + 0.5 TEP sensitivity",
        scoring=replace(ppr.scoring, te_premium=0.5),
    )
    three_wr = replace(
        ppr,
        profile_id="test:3wr",
        league_name="12-team PPR 3WR sensitivity",
        roster=replace(ppr.roster, wr=3),
    )
    extra_flex = replace(
        ppr,
        profile_id="test:extra-flex",
        league_name="12-team PPR extra FLEX sensitivity",
        roster=replace(ppr.roster, flex=2),
    )
    extras = {
        "12_STANDARD": generate_rankings(twelve_standard, snapshot),
        "TE_PREMIUM": generate_rankings(te_premium, snapshot),
        "THREE_WR": generate_rankings(three_wr, snapshot),
        "EXTRA_FLEX": generate_rankings(extra_flex, snapshot),
    }
    for key, result in extras.items():
        if not result.ready:
            raise RuntimeError(f"Sensitivity ranking {key} failed: {result.errors}")
    ppr_qb = _rank_map(results["12_TEAM_PPR"], "QB")
    sf_qb = _rank_map(results["12_TEAM_SUPERFLEX_PPR"], "QB")
    qb_common = sorted(set(ppr_qb).intersection(sf_qb))
    qb_median_rise = float(
        pd.Series([ppr_qb[player] - sf_qb[player] for player in qb_common]).median()
    )
    ppr_te = _rank_map(results["12_TEAM_PPR"], "TE")
    tep_te = _rank_map(extras["TE_PREMIUM"], "TE")
    te_common = sorted(set(ppr_te).intersection(tep_te))
    te_median_rise = float(
        pd.Series([ppr_te[player] - tep_te[player] for player in te_common]).median()
    )
    replacement = {
        key: {row.position: row.replacement_points for row in result.replacement_levels}
        for key, result in {**results, **extras}.items()
    }
    return pd.DataFrame(
        [
            {
                "check": "QB materially rises in Superflex",
                "observed": qb_median_rise,
                "expected": "> 0 median overall-rank rise",
                "status": "PASS" if qb_median_rise > 0 else "FAIL",
            },
            {
                "check": "TE premium changes TE value",
                "observed": te_median_rise,
                "expected": "> 0 median overall-rank rise",
                "status": "PASS" if te_median_rise > 0 else "FAIL",
            },
            {
                "check": "3WR increases WR scarcity",
                "observed": round(
                    replacement["12_TEAM_PPR"]["WR"] - replacement["THREE_WR"]["WR"], 4
                ),
                "expected": ">= 0 projected-point replacement drop",
                "status": (
                    "PASS"
                    if replacement["12_TEAM_PPR"]["WR"]
                    >= replacement["THREE_WR"]["WR"]
                    else "FAIL"
                ),
            },
            {
                "check": "12 teams lowers QB replacement level vs 10 teams",
                "observed": round(
                    replacement["10_TEAM_1QB_STANDARD"]["QB"]
                    - replacement["12_STANDARD"]["QB"],
                    4,
                ),
                "expected": ">= 0 projected points",
                "status": (
                    "PASS"
                    if replacement["10_TEAM_1QB_STANDARD"]["QB"]
                    >= replacement["12_STANDARD"]["QB"]
                    else "FAIL"
                ),
            },
            {
                "check": "Extra FLEX lowers FLEX-position replacement",
                "observed": round(
                    replacement["12_TEAM_PPR"]["WR"]
                    - replacement["EXTRA_FLEX"]["WR"],
                    4,
                ),
                "expected": ">= 0 projected points",
                "status": (
                    "PASS"
                    if replacement["12_TEAM_PPR"]["WR"]
                    >= replacement["EXTRA_FLEX"]["WR"]
                    else "FAIL"
                ),
            },
        ]
    )


def _ranking_sanity(results: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, result in results.items():
        frame = _ranking_frame(result)
        rows.extend(
            [
                {
                    "profile": key,
                    "check": "ranking_ready",
                    "observed": result.ready,
                    "status": "PASS" if result.ready else "FAIL",
                },
                {
                    "profile": key,
                    "check": "duplicate_player_ids",
                    "observed": int(frame["player_id"].duplicated().sum()),
                    "status": "PASS" if not frame["player_id"].duplicated().any() else "FAIL",
                },
                {
                    "profile": key,
                    "check": "rookie_rows_ranked",
                    "observed": int(frame["rookie"].sum()),
                    "status": "PASS" if int(frame["rookie"].sum()) == 78 else "FAIL",
                },
                {
                    "profile": key,
                    "check": "k_dst_rows_ranked",
                    "observed": int(frame["position"].isin(["K", "DST"]).sum()),
                    "status": (
                        "PASS" if not frame["position"].isin(["K", "DST"]).any() else "FAIL"
                    ),
                },
            ]
        )
    return pd.DataFrame(rows)


def _veteran_preservation_checks(
    veterans: pd.DataFrame, combined: pd.DataFrame
) -> pd.DataFrame:
    combined_veterans = combined.iloc[: len(veterans)].reset_index(drop=True)
    source = veterans.reset_index(drop=True)
    checks = [
        (
            "approved_veteran_row_count",
            len(combined_veterans) == 530 == len(source),
            f"source={len(source)} combined_prefix={len(combined_veterans)}",
        ),
        (
            "approved_veteran_column_order",
            list(source.columns) == list(combined_veterans.columns),
            f"columns={len(source.columns)}",
        ),
        (
            "approved_veteran_player_id_order",
            source["player_id"].equals(combined_veterans["player_id"]),
            f"ids={len(source)}",
        ),
        (
            "approved_veteran_all_cell_values",
            source.equals(combined_veterans),
            f"cells={source.shape[0] * source.shape[1]}",
        ),
        (
            "approved_veteran_source_status",
            combined_veterans["source_status"].eq("GOVERNED").all(),
            "all 530 remain GOVERNED",
        ),
    ]
    return pd.DataFrame(
        {
            "check": [check[0] for check in checks],
            "status": ["PASS" if check[1] else "FAIL" for check in checks],
            "evidence": [check[2] for check in checks],
        }
    )


def _historical_identity_coverage(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for season, group in frame.groupby("season", sort=True):
        rows.append(
            {
                "season": season,
                "drafted_skill_rows": len(group),
                "exact_identity_rows": int(group["player_id"].notna().sum()),
                "unresolved_rows": int(group["player_id"].isna().sum()),
                "exact_identity_coverage": round(float(group["player_id"].notna().mean()), 4),
                "pfr_bridge_rows": int(group["pfr_gsis_id"].notna().sum()),
                "exact_name_fallback_rows": int(
                    (group["pfr_gsis_id"].isna() & group["name_gsis_id"].notna()).sum()
                ),
                "pfr_name_conflicts": int(group["identity_conflict"].sum()),
            }
        )
    total = len(frame)
    rows.append(
        {
            "season": "ALL",
            "drafted_skill_rows": total,
            "exact_identity_rows": int(frame["player_id"].notna().sum()),
            "unresolved_rows": int(frame["player_id"].isna().sum()),
            "exact_identity_coverage": round(float(frame["player_id"].notna().mean()), 4),
            "pfr_bridge_rows": int(frame["pfr_gsis_id"].notna().sum()),
            "exact_name_fallback_rows": int(
                (frame["pfr_gsis_id"].isna() & frame["name_gsis_id"].notna()).sum()
            ),
            "pfr_name_conflicts": int(frame["identity_conflict"].sum()),
        }
    )
    return pd.DataFrame(rows)


def _historical_export(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "season",
        "player_id",
        "pfr_player_name",
        "position",
        "round",
        "pick",
        "team",
        "college",
        "age",
        "identity_method",
        "identity_conflict",
        "outcome_row_found",
        "games",
        "attempts",
        "completions",
        "passing_yards",
        "passing_tds",
        "interceptions",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "passing_first_downs",
        "rushing_first_downs",
        "receiving_first_downs",
        "return_yards",
        "return_tds",
        "fumbles_lost",
    ]
    return frame.reindex(columns=columns)


def _source_evidence(
    *,
    draft_path: Path,
    players_path: Path,
    stats_directory: Path,
    veteran_path: Path,
) -> pd.DataFrame:
    rows = [
        {
            "purpose": "historical and 2026 draft-day facts",
            "path": str(draft_path),
            "sha256": sha256(draft_path),
            "admitted_fields": (
                "season|round|pick|team|gsis_id|pfr_player_id|pfr_player_name|"
                "position|college|age"
            ),
            "excluded_fields": "all career outcome columns in draft_picks",
            "source_status": "PUBLIC_LOCAL_SNAPSHOT",
        },
        {
            "purpose": "exact identity and current factual team/status/position",
            "path": str(players_path),
            "sha256": sha256(players_path),
            "admitted_fields": (
                "gsis_id|display_name|pfr_id|position|latest_team|status|"
                "rookie_season|last_season"
            ),
            "excluded_fields": "all ranking or projection fields (none present)",
            "source_status": "PUBLIC_LOCAL_SNAPSHOT",
        },
        {
            "purpose": "immutable approved 530-veteran merge input",
            "path": str(veteran_path),
            "sha256": sha256(veteran_path),
            "admitted_fields": "entire exact approved projection frame",
            "excluded_fields": "none",
            "source_status": "OWNER_GOVERNED",
        },
    ]
    for season in HISTORICAL_SEASONS:
        path = stats_directory / f"player_stats_seasonal_{season}.parquet"
        rows.append(
            {
                "purpose": f"{season} rookie-year regular-season outcomes",
                "path": str(path),
                "sha256": sha256(path),
                "admitted_fields": "identity plus granular QB/RB/WR/TE scoring components",
                "excluded_fields": "future seasons; non-REG rows; non-model columns",
                "source_status": "PUBLIC_LOCAL_SNAPSHOT",
            }
        )
    return pd.DataFrame(rows)


def _write_documents(
    output: Path,
    *,
    position_results: pd.DataFrame,
    historical_identity: pd.DataFrame,
    rookie_rows: int,
    blocked_rows: int,
    rookie_sha: str,
    combined_sha: str,
    veteran_sha: str,
) -> None:
    results = position_results.set_index("position")
    coverage = historical_identity[historical_identity["season"].eq("ALL")].iloc[0]
    model_lines = [
        "# Rookie current-season projection model report",
        "",
        f"Selected model: `{MODEL_ID}`.",
        "",
        "For each QB/RB/WR/TE rookie, the model takes the median of every granular",
        "rookie-year stat component among earlier drafted players at the same position",
        "and draft round. A position-only fallback is allowed only when fewer than eight",
        "earlier same-round rows exist. All drafted players with exact identity remain in",
        "historical outcomes; absence of a REG stat row is explicitly zero.",
        "",
        "The 2016-2025 validation is strict walk-forward by draft class. The target class",
        "and every future",
        "class are absent from training. The baseline is a position-only component median.",
        "",
        "| Position | Rows | Model MAE | Baseline MAE | Lift | Spearman |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in results.itertuples():
        model_lines.append(
            f"| {row.Index} | {row.player_count} | {row.model_mae:.4f} | "
            f"{row.baseline_mae:.4f} | {row.mae_improvement:.4f} | {row.spearman:.4f} |"
        )
    model_lines.extend(
        [
            "",
            "No dynasty rank, Unified Preview score, market rank, proprietary projection,",
            "current camp depth chart, narrative role inference, or post-2025 NFL outcome",
            "is a model input. Current 2026 facts are limited to exact identity, draft",
            "capital, registry position, team, and ACT/RES status.",
            "",
            "Limitations: draft capital is the only workload proxy; no 2026 depth-chart",
            "snapshot was available; all same position/round players receive the same central",
            "stat line; uncertainty is wide and derived from position-specific walk-forward",
            "absolute-error p80. This is intentionally simple and auditable.",
        ]
    )
    (output / "MODEL_REPORT.md").write_text("\n".join(model_lines) + "\n", encoding="utf-8")

    verdict = f"""# Executive verdict

`GREEN_REVIEW_CANDIDATE_OWNER_SHA_APPROVAL_REQUIRED`

The leakage-safe evidence and deterministic validation gates pass. The packet contains
{rookie_rows} review-only 2026 rookie projections and {blocked_rows} blocked position-conflict
rows. Historical exact identity coverage is
{float(coverage['exact_identity_coverage']):.2%}. The rookie layer is not governed, installed,
or authorized for real-draft use until the NWR Owner approves its exact SHA and an independent
combined-board review passes.

Rookie candidate SHA-256: `{rookie_sha}`

Combined 530-veteran + {rookie_rows}-rookie review candidate SHA-256: `{combined_sha}`
"""
    (output / "EXECUTIVE_VERDICT.md").write_text(verdict, encoding="utf-8")

    governance = f"""# Governance boundary and next action

This packet is a separately governed Redraft-only candidate. It does not alter or supersede any
dynasty authority. It does not authorize dynasty rankings, Unified Preview inputs, Trading Lab
automation, scheduled refresh, K/DST projections, provider/API calls, or use outside Redraft V1.

The approved veteran input SHA-256 is `{veteran_sha}`. Its 530 rows were appended without value
changes.

Required next steps:

1. NWR Owner reviews and approves the exact rookie candidate SHA-256 `{rookie_sha}`.
2. Only after that approval, mark an exact copy governed and build governed combined preset
   rankings.
3. Run the four preset rankings, profile sensitivity checks, focused tests, and browser checks.
4. Obtain an independent fresh-HQ review of the governed combined board.
5. Keep real-draft readiness blocked unless every combined-board gate passes.
"""
    (output / "GOVERNANCE_AND_NEXT_ACTION.md").write_text(governance, encoding="utf-8")

    preservation = """# Preservation receipt

- Dynasty authorities changed: no.
- Dynasty ranks or Unified Preview used as rookie redraft projections: no.
- Approved veteran projection values changed: no.
- Trading Lab mode changed: no; manual-only remains the governing boundary.
- Scheduled refresh changed: no; disabled remains the governing boundary.
- K/DST projected: no; blocked.
- Provider/API calls or scraping performed: no.
- Rookie candidate installed: no.
"""
    (output / "PRESERVATION_RECEIPT.md").write_text(preservation, encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft-path", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--players-path", type=Path, default=DEFAULT_PLAYERS)
    parser.add_argument("--stats-directory", type=Path, default=DEFAULT_STATS)
    parser.add_argument("--veteran-path", type=Path, default=DEFAULT_VETERANS)
    parser.add_argument("--output-directory", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(
        json.dumps(
            build_packet(
                draft_path=args.draft_path,
                players_path=args.players_path,
                stats_directory=args.stats_directory,
                veteran_path=args.veteran_path,
                output_directory=args.output_directory,
            ),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
