from __future__ import annotations

# ruff: noqa: E402,I001

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.truth_set_first_down_projection_estimator_service import (
    build_first_down_estimator_preview,
    write_first_down_estimator_outputs,
)
from src.services.truth_set_production_validation_service import (
    validate_truth_set_production_export,
    write_production_validation_flags,
    write_production_validation_summary,
    write_production_validation_summary_json,
)
from src.services.truth_set_projection_recompute_service import (
    recompute_truth_set_projection_rows,
    write_truth_set_projection_flags,
    write_truth_set_projection_recompute,
)
from src.services.truth_set_role_usage_validation_service import (
    validate_truth_set_role_usage_export,
    write_role_usage_validation_flags,
    write_role_usage_validation_summary,
    write_role_usage_validation_summary_json,
)
from src.services.truth_set_safe_preview_service import (
    create_truth_set_safe_model_preview,
    write_safe_preview_comparison,
    write_safe_preview_source_log,
    write_safe_preview_summary,
)
from src.services.truth_set_young_bridge_prior_service import (
    build_truth_set_young_bridge_prior,
    write_truth_set_young_bridge_flags,
    write_truth_set_young_bridge_prior,
    write_truth_set_young_bridge_receipts,
)

V1_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v1"
V2_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v2"
V2_REPORTS = V2_ROOT / "reports"
V1_SOURCE = V1_ROOT / "source_clean"
V1_RAW = V1_ROOT / "source_raw"
ACTIVE_ROOT = ROOT / "local_exports" / "active_veteran_model_public_sources"
MODEL_PREVIEW_ROOT = ROOT / "local_exports" / "nflverse_model_previews"
DOCS_ROOT = ROOT / "docs" / "codex"
HISTORICAL_STATS = (
    ROOT
    / "local_exports"
    / "nflverse"
    / "preview"
    / "sprint2_phase7_public_20260514"
    / "raw"
    / "nflverse_player_stats_weekly.csv"
)

IMPORT_ELIGIBILITY_HEADER = (
    "source",
    "field_group",
    "classification",
    "recommendation",
    "used_in_v2_preview",
    "reason",
    "report_file",
)

MOVEMENT_HEADER = (
    "player_name",
    "position",
    "v1_overall_rank",
    "v2_overall_rank",
    "overall_rank_delta",
    "v1_model_value",
    "v2_model_value",
    "model_value_delta",
    "movement_reason",
)

SUMMARY_HEADER = (
    "metric",
    "value",
)


def main() -> None:
    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    preview_id = "truth_set_lab_v2_preview_" + _stamp(computed_at)
    V2_REPORTS.mkdir(parents=True, exist_ok=True)

    expected_players = _expected_players(V1_SOURCE / "projections.csv")

    projection_result = recompute_truth_set_projection_rows(
        V1_SOURCE / "projections.csv",
        reference_player_path=ACTIVE_ROOT / "stats_first_veteran_model_preview_outputs.csv",
    )
    projection_path = V2_REPORTS / "projection_recompute_preview.csv"
    projection_flags_path = V2_REPORTS / "projection_recompute_flags.csv"
    write_truth_set_projection_recompute(projection_path, projection_result.rows)
    write_truth_set_projection_flags(projection_flags_path, projection_result.flags)
    _write_json(V2_REPORTS / "projection_recompute_summary.json", projection_result.summary)

    first_down_result = build_first_down_estimator_preview(
        V1_SOURCE / "projections.csv",
        HISTORICAL_STATS,
    )
    write_first_down_estimator_outputs(
        estimate_path=V2_REPORTS / "first_down_projection_estimator_preview.csv",
        rate_path=V2_REPORTS / "first_down_projection_estimator_rates.csv",
        summary_path=V2_REPORTS / "first_down_projection_estimator_summary.csv",
        result=first_down_result,
    )
    _write_json(
        V2_REPORTS / "first_down_projection_estimator_summary.json",
        first_down_result.summary,
    )

    young_result = build_truth_set_young_bridge_prior(V1_SOURCE / "young_player_prior.csv")
    young_path = V2_REPORTS / "young_bridge_prior_preview.csv"
    write_truth_set_young_bridge_prior(young_path, young_result.rows)
    write_truth_set_young_bridge_receipts(
        V2_REPORTS / "young_bridge_prior_receipts.csv",
        young_result.receipt_rows,
    )
    write_truth_set_young_bridge_flags(
        V2_REPORTS / "young_bridge_prior_preview_flags.csv",
        young_result.flags,
    )
    _write_json(V2_REPORTS / "young_bridge_prior_preview_summary.json", young_result.summary)

    production_results = (
        validate_truth_set_production_export(
            V1_RAW / "production_data.csv",
            expected_players=expected_players,
        ),
        validate_truth_set_production_export(
            V1_SOURCE / "production_data.csv",
            expected_players=expected_players,
        ),
    )
    write_production_validation_summary(
        V2_REPORTS / "production_strict_validation_summary.csv",
        tuple(result.summary for result in production_results),
    )
    write_production_validation_flags(
        V2_REPORTS / "production_strict_validation_flags.csv",
        tuple(flag for result in production_results for flag in result.flags),
    )
    write_production_validation_summary_json(
        V2_REPORTS / "production_strict_validation_summary.json",
        tuple(result.summary for result in production_results),
    )

    role_result = validate_truth_set_role_usage_export(
        V1_SOURCE / "role_usage.csv",
        expected_players=expected_players,
    )
    write_role_usage_validation_summary(
        V2_REPORTS / "role_usage_strict_validation_summary.csv",
        (role_result.summary,),
    )
    write_role_usage_validation_flags(
        V2_REPORTS / "role_usage_strict_validation_flags.csv",
        role_result.flags,
    )
    write_role_usage_validation_summary_json(
        V2_REPORTS / "role_usage_strict_validation_summary.json",
        (role_result.summary,),
    )

    safe_preview = create_truth_set_safe_model_preview(
        active_output_path=ACTIVE_ROOT / "stats_first_veteran_model_preview_outputs.csv",
        active_normalized_path=ACTIVE_ROOT / "stats_first_normalized_features.csv",
        projection_preview_path=projection_path,
        young_bridge_preview_path=young_path,
        injury_path=V1_SOURCE / "injury.csv",
        market_path=V1_SOURCE / "trade_liquidity.csv",
        production_path=V1_SOURCE / "production_data.csv",
        output_root=MODEL_PREVIEW_ROOT,
        preview_id=preview_id,
        computed_at=computed_at,
    )
    comparison_path = safe_preview.preview_path / "truth_set_v2_preview_comparison.csv"
    source_coverage_path = safe_preview.preview_path / "truth_set_v2_source_coverage.csv"
    source_log_path = safe_preview.preview_path / "truth_set_v2_source_log.csv"
    rejected_log_path = safe_preview.preview_path / "truth_set_v2_rejected_field_log.csv"
    summary_path = safe_preview.preview_path / "truth_set_v2_summary.csv"
    import_eligibility_path = safe_preview.preview_path / "truth_set_v2_import_eligibility.csv"
    movement_path = safe_preview.preview_path / "truth_set_v2_movement_vs_v1.csv"

    source_rows = _with_role_usage_rejection_rows(
        safe_preview.source_log_rows,
        expected_players,
        role_result.status,
    )
    write_safe_preview_comparison(comparison_path, safe_preview.comparison_rows)
    write_safe_preview_source_log(source_log_path, tuple(source_rows))
    write_safe_preview_source_log(source_coverage_path, tuple(source_rows))
    write_safe_preview_source_log(
        rejected_log_path,
        tuple(row for row in source_rows if row["source_status"] == "rejected"),
    )
    write_safe_preview_summary(summary_path, safe_preview.summary)

    eligibility_rows = _import_eligibility_rows(
        projection_result.summary,
        first_down_result.summary,
        young_result.summary,
        tuple(result.summary for result in production_results),
        role_result.summary,
        safe_preview.preview_path,
    )
    _write_csv(import_eligibility_path, IMPORT_ELIGIBILITY_HEADER, eligibility_rows)

    v1_preview = _latest_v1_preview_path()
    movement_rows = _movement_rows(v1_preview, safe_preview.output_path, expected_players)
    _write_csv(movement_path, MOVEMENT_HEADER, movement_rows)

    summary = {
        **safe_preview.summary,
        "computed_at": computed_at,
        "preview_path": str(safe_preview.preview_path),
        "projection_rows_recomputed": projection_result.summary["projection_rows"],
        "first_down_estimated_from_history_rows": first_down_result.summary[
            "estimated_from_history_rows"
        ],
        "young_bridge_rows": young_result.summary["rows"],
        "production_validation_status": _combined_status(
            result.status for result in production_results
        ),
        "role_usage_validation_status": role_result.status,
        "movement_rows": len(movement_rows),
        "active_rankings_overwritten": False,
        "review_status": "review_only",
    }
    _write_csv(
        V2_REPORTS / "truth_set_lab_v2_summary.csv",
        SUMMARY_HEADER,
        tuple({"metric": key, "value": value} for key, value in summary.items()),
    )
    _write_json(V2_REPORTS / "truth_set_lab_v2_summary.json", summary)
    _write_json(safe_preview.preview_path / "truth_set_v2_manifest.json", summary)
    _write_note(safe_preview, movement_path, import_eligibility_path, summary)
    print(json.dumps(summary, indent=2))


def _with_role_usage_rejection_rows(
    rows: tuple[dict[str, object], ...],
    expected_players: tuple[str, ...],
    role_status: str,
) -> tuple[dict[str, object], ...]:
    output = list(rows)
    if role_status == "accepted":
        return tuple(output)
    for player in expected_players:
        output.append(
            {
                "player_name": player,
                "source": "role_usage_strict_export_rejected",
                "field_group": "role_usage",
                "source_status": "rejected",
                "model_usage": "not_used",
                "detail": (
                    "Role/usage source did not pass strict numeric validation; "
                    "no role fields were imported into the v2 preview."
                ),
            }
        )
    return tuple(output)


def _import_eligibility_rows(
    projection_summary: dict[str, object],
    first_down_summary: dict[str, object],
    young_summary: dict[str, object],
    production_summaries: tuple[dict[str, object], ...],
    role_summary: dict[str, object],
    preview_path: Path,
) -> tuple[dict[str, object], ...]:
    production_status = _combined_status(summary["status"] for summary in production_summaries)
    role_status = str(role_summary["status"])
    return (
        _eligibility(
            "projections",
            "raw stat columns",
            "safe_after_derivation",
            "can_import_after_recompute",
            "yes",
            f"{projection_summary['projection_rows']} projection rows recomputed into LVE scoring.",
            preview_path / "truth_set_v2_preview_comparison.csv",
        ),
        _eligibility(
            "projections",
            "supplied fantasy points",
            "rejected",
            "do_not_use",
            "no",
            "Supplied points are not LVE-safe; recomputed points are used instead.",
            preview_path / "truth_set_v2_source_log.csv",
        ),
        _eligibility(
            "projections",
            "first-down estimates",
            "preview_only",
            "needs_manual_review",
            "no",
            (
                f"{first_down_summary['estimated_from_history_rows']} rows estimated "
                "from broad position rates; active scoring remains unchanged."
            ),
            V2_REPORTS / "first_down_projection_estimator_preview.csv",
        ),
        _eligibility(
            "young_player_prior",
            "draft capital prior",
            "safe_after_derivation",
            "can_import_after_recompute",
            "yes",
            f"{young_summary['scored_bridge_prior_rows']} bridge-prior rows available.",
            V2_REPORTS / "young_bridge_prior_preview.csv",
        ),
        _eligibility(
            "production",
            "production stat columns",
            production_status,
            "can_import" if production_status == "accepted" else "needs_reexport",
            "yes" if production_status == "accepted" else "no",
            "Production must pass strict schema validation before model use.",
            V2_REPORTS / "production_strict_validation_summary.csv",
        ),
        _eligibility(
            "role_usage",
            "route/workload usage fields",
            role_status,
            "can_import" if role_status == "accepted" else "needs_reexport",
            "yes" if role_status == "accepted" else "no",
            "Role/usage must pass strict numeric validation before model use.",
            V2_REPORTS / "role_usage_strict_validation_summary.csv",
        ),
        _eligibility(
            "injury",
            "sourced injury context",
            "review_only",
            "can_import_as_context",
            "yes",
            "Only sourced injury rows are retained as confidence/context.",
            preview_path / "truth_set_v2_source_log.csv",
        ),
        _eligibility(
            "market",
            "trade liquidity",
            "trade_context_only",
            "can_import_as_context",
            "yes",
            "Market data stays separate from private/model value.",
            preview_path / "truth_set_v2_source_log.csv",
        ),
    )


def _eligibility(
    source: str,
    field_group: str,
    classification: str,
    recommendation: str,
    used: str,
    reason: str,
    report_file: Path,
) -> dict[str, object]:
    return {
        "source": source,
        "field_group": field_group,
        "classification": classification,
        "recommendation": recommendation,
        "used_in_v2_preview": used,
        "reason": reason,
        "report_file": str(report_file),
    }


def _movement_rows(
    v1_preview: Path | None,
    v2_output: Path,
    expected_players: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    if not v1_preview:
        return ()
    expected_keys = {_name_key(player) for player in expected_players}
    v1_output = v1_preview / "stats_first_veteran_model_preview_outputs.csv"
    if not v1_output.exists():
        return ()
    v1_rows = {_name_key(row.get("player_name")): row for row in _read_rows(v1_output)}
    rows = []
    for v2 in _read_rows(v2_output):
        key = _name_key(v2.get("player_name"))
        if key not in expected_keys:
            continue
        v1 = v1_rows.get(key, {})
        if not v1:
            continue
        model_delta = round(
            _float(v2.get("private_lve_value")) - _float(v1.get("private_lve_value")),
            2,
        )
        rank_delta = int(_float(v1.get("overall_rank")) - _float(v2.get("overall_rank")))
        rows.append(
            {
                "player_name": v2.get("player_name", ""),
                "position": v2.get("position", ""),
                "v1_overall_rank": v1.get("overall_rank", ""),
                "v2_overall_rank": v2.get("overall_rank", ""),
                "overall_rank_delta": rank_delta,
                "v1_model_value": v1.get("private_lve_value", ""),
                "v2_model_value": v2.get("private_lve_value", ""),
                "model_value_delta": model_delta,
                "movement_reason": _movement_reason(model_delta, rank_delta),
            }
        )
    return tuple(sorted(rows, key=lambda row: abs(float(row["model_value_delta"])), reverse=True))


def _movement_reason(model_delta: float, rank_delta: int) -> str:
    if abs(model_delta) < 0.01 and rank_delta == 0:
        return "no material movement"
    if abs(model_delta) < 0.5:
        return "ranking/order movement from same safe inputs"
    return "safe input rerun movement"


def _latest_v1_preview_path() -> Path | None:
    candidates = [
        path
        for path in MODEL_PREVIEW_ROOT.glob("truth_set_safe_inputs_*")
        if path.is_dir()
    ]
    return sorted(candidates)[-1] if candidates else None


def _expected_players(path: Path) -> tuple[str, ...]:
    return tuple(row["player_name"] for row in _read_rows(path))


def _combined_status(statuses: object) -> str:
    status_list = [str(status) for status in statuses]
    if status_list and all(status == "accepted" for status in status_list):
        return "accepted"
    return "rejected"


def _write_note(
    safe_preview: object,
    movement_path: Path,
    eligibility_path: Path,
    summary: dict[str, object],
) -> None:
    note_path = DOCS_ROOT / "TRUTH_SET_LAB_V2_PREVIEW_RERUN.md"
    source_coverage_path = safe_preview.preview_path / "truth_set_v2_source_coverage.csv"
    rejected_field_path = safe_preview.preview_path / "truth_set_v2_rejected_field_log.csv"
    note_path.write_text(
        "\n".join(
            [
                "# Truth Set Lab v2 Preview Rerun",
                "",
                "Status: review-only. Active rankings were not overwritten.",
                "",
                "## Outputs",
                "",
                f"- Preview folder: `{safe_preview.preview_path}`",
                f"- Model outputs: `{safe_preview.output_path}`",
                f"- Receipts: `{safe_preview.contribution_path}`",
                f"- Source coverage/log: `{source_coverage_path}`",
                f"- Import eligibility: `{eligibility_path}`",
                f"- Movement vs v1: `{movement_path}`",
                f"- Rejected field log: `{rejected_field_path}`",
                "",
                "## Summary",
                "",
                f"- Truth-set players: {summary['truth_set_players']}",
                f"- Projection rows applied: {summary['projection_rows_applied']}",
                f"- Young bridge rows applied: {summary['young_bridge_rows_applied']}",
                f"- Market context rows applied: {summary['market_context_rows_applied']}",
                f"- Rejected production rows: {summary['rejected_production_rows']}",
                f"- Production validation status: `{summary['production_validation_status']}`",
                f"- Role/usage validation status: `{summary['role_usage_validation_status']}`",
                "- First-down estimated-from-history rows: "
                f"{summary['first_down_estimated_from_history_rows']}",
                "",
                "## Guardrails",
                "",
                "- Only validated safe fields were used.",
                "- Production stayed out because the current export still fails validation.",
                "- Role/usage stayed out because the current export still fails validation.",
                "- First-down estimates stayed preview-only and did not affect active scoring.",
                "- Market data stayed trade/context only.",
                "- Injury context came only from sourced rows.",
                "- Active rankings remain review-only until formal gates pass.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _name_key(value: object) -> str:
    text = " ".join(str(value or "").replace("\u00a0", " ").strip().split())
    for suffix in (" III", " II", " IV", " Jr.", " Jr"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
    return "".join(char for char in text.lower() if char.isalnum())


def _float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _stamp(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("Z", "")


if __name__ == "__main__":
    main()
