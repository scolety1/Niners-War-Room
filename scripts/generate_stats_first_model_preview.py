from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.age_curve_service import (  # noqa: E402
    age_curve_profile,
    age_for_row,
    build_age_lookup,
)
from src.services.lve_normalization_service import (  # noqa: E402
    derive_lve_normalized_feature_receipt_rows,
    derive_lve_normalized_veteran_feature_rows,
    write_lve_normalized_feature_receipt_rows,
    write_lve_normalized_veteran_feature_rows,
)
from src.services.lve_projection_import_service import (  # noqa: E402
    PROJECTION_SOURCE_LOCAL_BASELINE,
)
from src.services.lve_scoring_derivation_service import derive_lve_weekly_scoring_rows  # noqa: E402
from src.services.lve_stats_first_preview_service import (  # noqa: E402
    STATS_FIRST_PREVIEW_CONTRIBUTIONS_FILE,
    create_stats_first_model_preview,
    stats_first_preview_review_rows,
    stats_first_preview_review_summary_rows,
)
from src.services.real_input_template_service import (  # noqa: E402
    NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS,
)
from src.services.young_nfl_bridge_service import (  # noqa: E402
    apply_bridge_metadata_to_rows,
    load_young_nfl_bridge_priors,
)

DEFAULT_PUBLIC_PREVIEW_ROOT = REPO_ROOT / "local_exports" / "nflverse" / "preview"
DEFAULT_MODEL_PREVIEW_ROOT = REPO_ROOT / "local_exports" / "nflverse_model_previews"
DEFAULT_ACTIVE_RECEIPT_ROOT = (
    REPO_ROOT / "local_exports" / "active_veteran_model_public_sources"
)
PROJECTION_FILE = "projection_raw_import.csv"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate stats-first model preview outputs from imported public data. "
            "This does not promote live data-pack model outputs or mark decision-ready."
        )
    )
    parser.add_argument(
        "--public-preview-dir",
        type=Path,
        help=(
            "Public import preview folder. Defaults to the newest "
            "local_exports/nflverse/preview run."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_MODEL_PREVIEW_ROOT,
    )
    parser.add_argument("--preview-id", help="Optional deterministic preview id.")
    parser.add_argument(
        "--mirror-active-receipts",
        action="store_true",
        help=(
            "Copy preview normalized features/contributions into the active receipt "
            "source folder so Model Lab receipts use this preview source."
        ),
    )
    args = parser.parse_args()

    public_preview = args.public_preview_dir or _latest_public_preview_dir(
        DEFAULT_PUBLIC_PREVIEW_ROOT
    )
    raw_dir = public_preview / "raw"
    if not raw_dir.exists():
        raise SystemExit(f"Raw public data folder not found: {raw_dir}")

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    preview_id = args.preview_id or "stats_first_public_" + computed_at.replace(
        "-",
        "",
    ).replace(":", "").replace("Z", "")

    projection_path = raw_dir / PROJECTION_FILE
    baseline_projection_rows = _write_baseline_projection_file(
        raw_dir,
        projection_path,
        computed_at,
    )

    normalized = derive_lve_normalized_veteran_feature_rows(raw_dir, computed_at=computed_at)
    if normalized.status == "blocked":
        raise SystemExit("Normalization blocked: " + "; ".join(normalized.issues))
    age_lookup = build_age_lookup(public_preview)
    normalized_rows = _rows_with_age_curve(normalized.rows, age_lookup)
    bridge_priors = load_young_nfl_bridge_priors(public_preview, season=2026)
    normalized_rows = apply_bridge_metadata_to_rows(normalized_rows, bridge_priors)
    normalized = replace(normalized, rows=tuple(normalized_rows))
    normalized_path = raw_dir / "stats_first_normalized_features.csv"
    write_lve_normalized_veteran_feature_rows(normalized_path, normalized.rows)

    normalized_receipts = derive_lve_normalized_feature_receipt_rows(
        raw_dir,
        computed_at=computed_at,
    )
    normalized_receipts = replace(
        normalized_receipts,
        rows=tuple(_receipt_rows_with_age_curve(normalized.rows, normalized_receipts.rows)),
    )
    normalized_receipts_path = raw_dir / "lve_normalized_feature_receipts.csv"
    write_lve_normalized_feature_receipt_rows(
        normalized_receipts_path,
        normalized_receipts.rows,
    )

    preview = create_stats_first_model_preview(
        normalized_path,
        args.output_root,
        preview_id=preview_id,
        computed_at=computed_at,
    )
    if not preview.created:
        raise SystemExit(preview.message)

    shutil.copy2(normalized_path, preview.preview_path / "stats_first_normalized_features.csv")
    shutil.copy2(
        normalized_receipts_path,
        preview.preview_path / "lve_normalized_feature_receipts.csv",
    )
    source_coverage_path = preview.preview_path / "stats_first_source_coverage.csv"
    source_coverage_rows = _source_coverage_rows(normalized.rows)
    _write_csv(source_coverage_path, source_coverage_rows)

    outlier_path = preview.preview_path / "stats_first_preview_outliers.csv"
    outlier_rows = _outlier_rows(
        _read_csv(preview.output_path),
        _read_csv(preview.contribution_path),
        normalized.rows,
    )
    _write_csv(outlier_path, outlier_rows)

    review_rows = stats_first_preview_review_rows(args.output_root)
    review_summary = [
        row for row in stats_first_preview_review_summary_rows(review_rows)
        if row.get("preview_id", preview_id) == preview_id or True
    ]
    review_summary_path = preview.preview_path / "stats_first_preview_review_summary.csv"
    _write_csv(review_summary_path, review_summary)

    manifest_path = preview.preview_path / "stats_first_generation_manifest.json"
    manifest = {
        "preview_id": preview.preview_id,
        "created_at": computed_at,
        "public_preview_dir": str(public_preview),
        "raw_dir": str(raw_dir),
        "baseline_projection_file": str(projection_path),
        "baseline_projection_rows": len(baseline_projection_rows),
        "baseline_projection_policy": (
            "local_baseline_from_recent_lve_points; not a paid/market projection feed"
        ),
        "normalized_rows": len(normalized.rows),
        "normalized_status": normalized.status,
        "normalized_issues": list(normalized.issues),
        "normalized_receipt_rows": len(normalized_receipts.rows),
        "preview_output_rows": preview.row_count,
        "source_coverage_file": str(source_coverage_path),
        "outlier_file": str(outlier_path),
        "decision_ready": False,
        "review_status": "review",
        "model_promotion": "not_allowed",
        "market_policy": (
            "market_liquidity is neutral/default unless supplied; private/stat value "
            "does not use market data"
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    if args.mirror_active_receipts:
        DEFAULT_ACTIVE_RECEIPT_ROOT.mkdir(parents=True, exist_ok=True)
        for source, destination_name in (
            (normalized_path, "stats_first_normalized_features.csv"),
            (preview.contribution_path, STATS_FIRST_PREVIEW_CONTRIBUTIONS_FILE),
            (preview.output_path, "stats_first_veteran_model_preview_outputs.csv"),
            (source_coverage_path, "stats_first_source_coverage.csv"),
            (outlier_path, "stats_first_preview_outliers.csv"),
        ):
            shutil.copy2(source, DEFAULT_ACTIVE_RECEIPT_ROOT / destination_name)

    print(f"preview_id={preview.preview_id}")
    print("status=review")
    print(f"public_preview={public_preview}")
    print(f"preview_path={preview.preview_path}")
    print(f"outputs={preview.output_path}")
    print(f"contributions={preview.contribution_path}")
    print(f"normalized={normalized_path}")
    print(f"normalized_receipts={normalized_receipts_path}")
    print(f"source_coverage={source_coverage_path}")
    print(f"outliers={outlier_path}")
    print(f"baseline_projection_rows={len(baseline_projection_rows)}")
    print(f"normalized_rows={len(normalized.rows)}")
    print(f"preview_rows={preview.row_count}")
    print(f"outlier_rows={len(outlier_rows)}")
    if args.mirror_active_receipts:
        print(f"active_receipts_mirror={DEFAULT_ACTIVE_RECEIPT_ROOT}")
    return 0


def _latest_public_preview_dir(root: Path) -> Path:
    candidates = [path for path in root.iterdir() if path.is_dir()] if root.exists() else []
    if not candidates:
        raise SystemExit(f"No public preview imports found under {root}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _write_baseline_projection_file(
    raw_dir: Path,
    projection_path: Path,
    computed_at: str,
) -> list[dict[str, object]]:
    scoring = derive_lve_weekly_scoring_rows(raw_dir)
    if scoring.status == "blocked":
        raise SystemExit("Cannot derive baseline projections: " + "; ".join(scoring.issues))
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in scoring.rows:
        key = (
            str(row.get("player_id") or ""),
            str(row.get("gsis_id") or ""),
        )
        grouped[key].append(row)

    rows: list[dict[str, object]] = []
    for (player_id, gsis_id), player_rows in grouped.items():
        games = max(len(player_rows), 1)
        totals = _projection_totals(player_rows)
        season = _latest_group_value(player_rows, "season")
        player_name = _latest_group_value(player_rows, "player_name")
        position = _latest_group_value(player_rows, "position")
        team = _latest_group_value(player_rows, "team")
        rows.append(
            {
                "season": season,
                "week": "0",
                "projection_scope": "local_baseline_recent_lve",
                "projection_source_status": PROJECTION_SOURCE_LOCAL_BASELINE,
                "source_id": "local_baseline_from_imported_nflverse_stats",
                "source_player_id": player_id or gsis_id,
                "sleeper_id": player_id,
                "gsis_id": gsis_id,
                "player_name": player_name,
                "position": position,
                "team": team,
                "projected_games": games,
                "projected_starts": "",
                "projected_passing_yards": totals["passing_yards"],
                "projected_passing_tds": totals["passing_tds"],
                "projected_interceptions": totals["interceptions"],
                "projected_rushing_attempts": totals["rushing_attempts"],
                "projected_rushing_yards": totals["rushing_yards"],
                "projected_rushing_tds": totals["rushing_tds"],
                "projected_targets": totals["targets"],
                "projected_receptions": totals["receptions"],
                "projected_receiving_yards": totals["receiving_yards"],
                "projected_receiving_tds": totals["receiving_tds"],
                "projected_rushing_first_downs": totals["rushing_first_downs"],
                "projected_receiving_first_downs": totals["receiving_first_downs"],
                "projected_fumbles_lost": totals["fumbles_lost"],
                "source_projected_points": round(
                    sum(float(row["lve_points"]) for row in player_rows),
                    2,
                ),
                "source_scoring_format": "LVE_baseline_from_actual_recent_stats",
                "source_updated_at": computed_at,
                "imported_at": computed_at,
                "confidence": 62,
            }
        )
    header = NFLVERSE_STATS_UPGRADE_TEMPLATE_HEADERS[PROJECTION_FILE]
    _write_csv(projection_path, rows, header=header)
    return rows


def _latest_group_value(rows: list[dict[str, object]], column: str) -> str:
    latest_key = (-1, -1)
    latest_value = ""
    for row in rows:
        value = str(row.get(column) or "")
        if not value:
            continue
        sort_key = (
            int(_float(row.get("season"), 0)),
            int(_float(row.get("week"), 0)),
        )
        if sort_key >= latest_key:
            latest_key = sort_key
            latest_value = value
    return latest_value


def _projection_totals(rows: list[dict[str, object]]) -> dict[str, float]:
    totals = {
        "passing_yards": 0.0,
        "passing_tds": 0.0,
        "interceptions": 0.0,
        "rushing_attempts": 0.0,
        "rushing_yards": 0.0,
        "rushing_tds": 0.0,
        "targets": 0.0,
        "receptions": 0.0,
        "receiving_yards": 0.0,
        "receiving_tds": 0.0,
        "rushing_first_downs": 0.0,
        "receiving_first_downs": 0.0,
        "fumbles_lost": 0.0,
    }
    source_rows = _raw_player_stats_by_key(rows)
    if not source_rows:
        return totals
    for row in source_rows:
        for key in totals:
            totals[key] += _float(row.get(key))
    return {key: round(value, 2) for key, value in totals.items()}


def _raw_player_stats_by_key(scoring_rows: list[dict[str, object]]) -> list[dict[str, str]]:
    # The baseline projection needs source stat categories that derived LVE rows do
    # not preserve. Re-read the raw rows and match on player/week.
    # This function is patched below by binding RAW_STATS_LOOKUP before use.
    output: list[dict[str, str]] = []
    for row in scoring_rows:
        lookup_key = (
            str(row.get("season") or ""),
            str(row.get("week") or ""),
            str(row.get("player_id") or ""),
            str(row.get("gsis_id") or ""),
        )
        raw = RAW_STATS_LOOKUP.get(lookup_key)
        if raw:
            output.append(raw)
    return output


def _source_coverage_rows(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        warnings = set(str(row.get("warnings") or "").split("|")) - {""}
        bridge_weight = _float(row.get("young_nfl_bridge_weight"), 0.0)
        bridge_active = bridge_weight > 0
        missing = {
            "production": "missing_lve_scoring_history" in warnings and not bridge_active,
            "production_freshness": "stale_lve_scoring_source" in warnings,
            "role/usage": "missing_role_usage_features" in warnings,
            "projections": "missing_projection_features" in warnings,
            "projection_independence": (
                "local_baseline_projection_not_independent" in warnings
            ),
            "injury": "missing_injury_features" in warnings,
            "age/bio": row.get("age_source_status") == "neutral_imputation",
            "market/liquidity": True,
        }
        critical_missing = [
            bucket for bucket in ("production", "role/usage", "age/bio") if missing[bucket]
        ]
        review_missing = [
            bucket for bucket in ("projections", "injury", "market/liquidity")
            if missing[bucket]
        ]
        if missing["production_freshness"]:
            review_missing.insert(0, "production freshness")
        if missing["projection_independence"]:
            review_missing.insert(0, "independent projection")
        output.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "team": row.get("team", ""),
                "production": (
                    "review"
                    if (
                        ("missing_lve_scoring_history" in warnings and bridge_active)
                        or missing["production_freshness"]
                    )
                    else _status(not missing["production"])
                ),
                "role_usage": _status(not missing["role/usage"]),
                "projection": (
                    "review"
                    if missing["projection_independence"]
                    else _status(not missing["projections"])
                ),
                "projection_source_status": row.get("projection_source_status", ""),
                "injury": _status(not missing["injury"]),
                "age_bio": _status(not missing["age/bio"]),
                "market_liquidity": "review_missing",
                "critical_missing_buckets": "|".join(critical_missing),
                "review_missing_buckets": "|".join(review_missing),
                "confidence": row.get("confidence", ""),
                "experience_bucket": row.get("experience_bucket", ""),
                "age_raw": row.get("age_raw", ""),
                "age_bucket": row.get("age_bucket", ""),
                "age_warning": row.get("age_warning", ""),
                "age_interaction_flags": row.get("age_interaction_flags", ""),
                "young_nfl_bridge_prior_score": row.get(
                    "young_nfl_bridge_prior_score",
                    "",
                ),
                "young_nfl_bridge_weight": row.get("young_nfl_bridge_weight", ""),
                "decision_effect": (
                    "blocks_decision_ready" if critical_missing else "review_only"
                ),
            }
        )
    return output


def _rows_with_age_curve(
    rows: tuple[dict[str, object], ...],
    age_lookup: dict[tuple[str, str], float],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        age = age_for_row(row, age_lookup)
        profile = age_curve_profile(
            str(row.get("position") or ""),
            age,
            role_score=_float(row.get("role_security"), 50.0),
            target_score=_float(row.get("target_earning_stability"), 50.0),
            workload_score=_float(row.get("workload_earning"), 50.0),
            injury_score=_float(row.get("injury_durability"), 75.0),
            rushing_profile_score=_float(row.get("first_down_td_fit"), 50.0),
            route_score=_float(row.get("route_role"), 50.0),
        )
        updated = dict(row)
        updated["age_raw"] = "" if profile.age is None else profile.age
        updated["age_bucket"] = profile.age_bucket
        updated["age_warning"] = profile.age_warning
        updated["age_source_status"] = profile.source_status
        updated["age_interaction_flags"] = "|".join(profile.age_interaction_flags)
        if profile.age is not None:
            updated["age_curve"] = profile.age_curve_score
            warnings = {
                warning
                for warning in str(updated.get("warnings") or "").split("|")
                if warning and warning != "age_curve_source_not_imported_yet"
            }
            if profile.age_warning:
                warnings.add(profile.age_warning)
            warnings.update(profile.age_interaction_flags)
            updated["warnings"] = "|".join(sorted(warnings))
            updated["private_stat_value"] = _private_stat_value_with_age(updated)
        output.append(updated)
    return output


def _receipt_rows_with_age_curve(
    normalized_rows: tuple[dict[str, object], ...],
    receipt_rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    normalized_by_player = {
        str(row.get("player_id") or ""): row for row in normalized_rows
    }
    output: list[dict[str, object]] = []
    for row in receipt_rows:
        updated = dict(row)
        if row.get("feature_name") == "age_curve":
            normalized = normalized_by_player.get(str(row.get("player_id") or ""), {})
            updated["raw_value"] = (
                f"age={normalized.get('age_raw', '')};"
                f"bucket={normalized.get('age_bucket', '')};"
                f"interaction_flags={normalized.get('age_interaction_flags', '')}"
            )
            updated["normalized_value"] = normalized.get(
                "age_curve",
                row.get("normalized_value", ""),
            )
            updated["normalized_score"] = normalized.get(
                "age_curve",
                row.get("normalized_score", ""),
            )
            updated["source_status"] = normalized.get(
                "age_source_status",
                row.get("source_status", ""),
            )
            updated["source_key"] = "identity_player_bio"
            updated["source_field"] = "age_or_birth_date"
            updated["warning_status"] = (
                "review" if normalized.get("age_warning") else "ready"
            )
            updated["warning_reason"] = normalized.get("age_warning", "")
            updated["imputed_flag"] = (
                "true" if normalized.get("age_source_status") == "neutral_imputation" else "false"
            )
            updated["is_missing"] = updated["imputed_flag"]
            updated["imputation_value"] = (
                50.0 if updated["imputed_flag"] == "true" else ""
            )
        output.append(updated)
    return output


def _private_stat_value_with_age(row: dict[str, object]) -> float:
    position = str(row.get("position") or "")
    projection = _float(row.get("lve_projection_value"))
    role = _float(row.get("role_security"))
    workload = _float(row.get("workload_earning"))
    target = _float(row.get("target_earning_stability"))
    route = _float(row.get("route_role"))
    efficiency = _float(row.get("efficiency_score"))
    first_down = _float(row.get("first_down_td_fit"))
    age = _float(row.get("age_curve"), 50.0)
    injury = _float(row.get("injury_durability"), 75.0)
    if position == "QB":
        return round(_clamp(
            (0.31 * projection)
            + (0.30 * role)
            + (0.06 * efficiency)
            + (0.12 * first_down)
            + (0.11 * age)
            + (0.10 * injury)
            - 8.0
        ), 2)
    if position == "RB":
        return round(_clamp(
            (0.27 * projection)
            + (0.25 * role)
            + (0.17 * workload)
            + (0.08 * efficiency)
            + (0.12 * first_down)
            + (0.05 * age)
            + (0.07 * injury)
        ), 2)
    if position == "WR":
        bonus = 3.0 if role >= 75 and target >= 70 else 1.0 if role >= 65 else 0.0
        return round(_clamp(
            (0.25 * projection)
            + (0.24 * role)
            + (0.20 * target)
            + (0.08 * efficiency)
            + (0.10 * first_down)
            + (0.07 * age)
            + (0.07 * injury)
            + bonus
        ), 2)
    penalty = 0.0 if route >= 75 and target >= 70 else 8.0 if route >= 55 else 14.0
    return round(_clamp(
        (0.21 * projection)
        + (0.26 * route)
        + (0.20 * target)
        + (0.07 * efficiency)
        + (0.08 * first_down)
        + (0.08 * age)
        + (0.10 * injury)
        - penalty
    ), 2)


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _outlier_rows(
    outputs: list[dict[str, str]],
    contributions: list[dict[str, str]],
    normalized_rows: tuple[dict[str, object], ...],
) -> list[dict[str, object]]:
    contribution_by_player: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in contributions:
        contribution_by_player[str(row.get("player_id") or "")].append(row)
    normalized_by_player = {
        str(row.get("player_id") or ""): row for row in normalized_rows
    }
    rows: list[dict[str, object]] = []
    for output in outputs:
        player_id = str(output.get("player_id") or "")
        normalized = normalized_by_player.get(player_id, {})
        confidence = _float(output.get("confidence_score"))
        rank = int(_float(output.get("overall_rank"), 9999))
        if confidence < 65:
            rows.append(
                _outlier_row(
                    output,
                    "low_confidence",
                    "Missing or weak source coverage keeps this preview review-only.",
                    "Review source coverage and receipts before trusting rank.",
                    "high" if rank <= 50 else "medium",
                )
            )
        if rank <= 12 and confidence < 75:
            rows.append(
                _outlier_row(
                    output,
                    "top_rank_low_confidence",
                    "A highly ranked player has below-target confidence.",
                    "Do not use as money-decision-ready until coverage improves.",
                    "high",
                )
            )
        dominant = _dominant_feature(contribution_by_player[player_id])
        if dominant and dominant[1] >= 0.42 and rank <= 50:
            rows.append(
                _outlier_row(
                    output,
                    "one_feature_driven_rank",
                    f"{dominant[0]} drives {dominant[1]:.1%} of a core component.",
                    "Open receipts and verify the raw source behind that feature.",
                    "medium",
                )
            )
        warnings = str(normalized.get("warnings") or "")
        if warnings:
            rows.append(
                _outlier_row(
                    output,
                    "source_warning",
                    warnings,
                    "Inspect source coverage and normalized receipts.",
                    "medium",
                )
            )
        if abs(_float(output.get("market_trade_value"), 50.0) - 50.0) < 0.01:
            rows.append(
                _outlier_row(
                    output,
                    "missing_market_reference",
                    "Market/liquidity is neutral default; market edge is not real yet.",
                    "Use this only as stats value until a legal market export is loaded.",
                    "low",
                )
            )
    return _dedupe_outliers(rows)


def _dominant_feature(rows: list[dict[str, str]]) -> tuple[str, float] | None:
    component_totals: dict[str, float] = defaultdict(float)
    feature_totals: dict[tuple[str, str], float] = defaultdict(float)
    for row in rows:
        component = str(row.get("component") or "")
        if component == "trade_value":
            continue
        contribution = abs(_float(row.get("component_contribution")))
        component_totals[component] += contribution
        feature_totals[(component, str(row.get("feature_name") or ""))] += contribution
    best: tuple[str, float] | None = None
    for (component, feature), contribution in feature_totals.items():
        total = component_totals[component]
        if total <= 0:
            continue
        share = contribution / total
        if best is None or share > best[1]:
            best = (feature, share)
    return best


def _outlier_row(
    output: dict[str, str],
    outlier_type: str,
    reason: str,
    next_action: str,
    severity: str,
) -> dict[str, object]:
    return {
        "outlier_type": outlier_type,
        "severity": severity,
        "player_id": output.get("player_id", ""),
        "player_name": output.get("player_name", ""),
        "position": output.get("position", ""),
        "team": output.get("team", ""),
        "overall_rank": output.get("overall_rank", ""),
        "position_rank": output.get("position_rank_label", ""),
        "private_lve_value": output.get("private_lve_value", ""),
        "keeper_score": output.get("keeper_score", ""),
        "confidence_score": output.get("confidence_score", ""),
        "warning_status": output.get("warning_status", ""),
        "reason": reason,
        "next_action": next_action,
        "review_status": "review_required",
    }


def _dedupe_outliers(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, object]] = []
    for row in rows:
        key = (
            str(row.get("player_id")),
            str(row.get("outlier_type")),
            str(row.get("reason")),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return sorted(
        output,
        key=lambda row: (
            {"high": 0, "medium": 1, "low": 2}.get(str(row["severity"]), 9),
            int(_float(row.get("overall_rank"), 9999)),
            str(row.get("player_name") or ""),
        ),
    )


def _status(is_ready: bool) -> str:
    return "ready" if is_ready else "review_missing"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(
    path: Path,
    rows: list[dict[str, object]],
    *,
    header: tuple[str, ...] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(header or (tuple(rows[0].keys()) if rows else ()))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value)
        if text == "":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


RAW_STATS_LOOKUP: dict[tuple[str, str, str, str], dict[str, str]] = {}


if __name__ == "__main__":
    public_preview_dir = None
    if "--public-preview-dir" in sys.argv:
        index = sys.argv.index("--public-preview-dir")
        if index + 1 < len(sys.argv):
            public_preview_dir = Path(sys.argv[index + 1])
    preview_dir = public_preview_dir or _latest_public_preview_dir(DEFAULT_PUBLIC_PREVIEW_ROOT)
    raw_stats_path = preview_dir / "raw" / "nflverse_player_stats_weekly.csv"
    for raw_row in _read_csv(raw_stats_path):
        RAW_STATS_LOOKUP[
            (
                str(raw_row.get("season") or ""),
                str(raw_row.get("week") or ""),
                str(raw_row.get("player_id") or ""),
                str(raw_row.get("gsis_id") or ""),
            )
        ] = raw_row
    raise SystemExit(main())
