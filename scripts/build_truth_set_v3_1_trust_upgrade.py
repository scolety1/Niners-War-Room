from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.truth_set_first_down_projection_estimator_service import (  # noqa: E402
    build_first_down_estimator_preview,
    write_first_down_estimator_outputs,
)

TRUTH_SET_ROOT = ROOT / "local_exports" / "truth_set_lab"
V1_SOURCE_ROOT = TRUTH_SET_ROOT / "v1" / "source_clean"
V3_REPORT_ROOT = TRUTH_SET_ROOT / "v3" / "reports"
V31_REPORT_ROOT = TRUTH_SET_ROOT / "v3_1" / "reports"
PREVIEW_ROOT = ROOT / "local_exports" / "nflverse_model_previews"
DOCS_ROOT = ROOT / "docs" / "codex"

ROUTE_CAUTION_HEADER = (
    "player_name",
    "position",
    "overall_rank",
    "model_value",
    "confidence",
    "warning_label",
    "route_data_status",
    "what_this_means",
    "allowed_proxy_fields",
    "model_usage_status",
    "next_action",
)

INJURY_REVIEW_HEADER = (
    "player_name",
    "position",
    "injury_source_status",
    "coverage_status",
    "manual_review_status",
    "known_current_issue",
    "source_url",
    "review_note",
    "model_usage_status",
    "next_action",
)

SUMMARY_HEADER = ("metric", "value")


def main() -> None:
    preview = _latest_preview()
    if preview is None:
        raise FileNotFoundError("No Truth Set Lab v3 preview folder found.")

    V31_REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    first_down = build_first_down_estimator_preview(
        V1_SOURCE_ROOT / "projections.csv",
        V3_REPORT_ROOT / "truth_set_v3_production_player_week.csv",
    )
    first_down_paths = {
        "estimates": V31_REPORT_ROOT / "truth_set_v3_1_first_down_projection_estimates.csv",
        "rates": V31_REPORT_ROOT / "truth_set_v3_1_first_down_projection_rates.csv",
        "summary": V31_REPORT_ROOT / "truth_set_v3_1_first_down_projection_summary.csv",
        "summary_json": V31_REPORT_ROOT / "truth_set_v3_1_first_down_projection_summary.json",
    }
    write_first_down_estimator_outputs(
        estimate_path=first_down_paths["estimates"],
        rate_path=first_down_paths["rates"],
        summary_path=first_down_paths["summary"],
        result=first_down,
    )
    first_down_paths["summary_json"].write_text(
        json.dumps(first_down.summary, indent=2) + "\n",
        encoding="utf-8",
    )

    model_rows = _read_rows(preview / "stats_first_veteran_model_preview_outputs.csv")
    coverage_rows = _read_rows(preview / "truth_set_v3_source_coverage.csv")
    truth_set_players = {row.get("player_name", "") for row in coverage_rows}
    route_rows = _route_caution_rows(model_rows, truth_set_players)
    injury_rows = _injury_review_rows(coverage_rows)

    route_path = V31_REPORT_ROOT / "truth_set_v3_1_route_proxy_caution_worklist.csv"
    injury_path = V31_REPORT_ROOT / "truth_set_v3_1_injury_review_template.csv"
    summary_path = V31_REPORT_ROOT / "truth_set_v3_1_trust_upgrade_summary.csv"
    summary_json_path = V31_REPORT_ROOT / "truth_set_v3_1_trust_upgrade_summary.json"

    _write_csv(route_path, ROUTE_CAUTION_HEADER, route_rows)
    _write_csv(injury_path, INJURY_REVIEW_HEADER, injury_rows)

    summary = {
        "review_status": "review_only",
        "model_logic_changed": False,
        "model_scores_changed": False,
        "active_rankings_overwritten": False,
        "v3_preview": str(preview),
        "first_down_projection_rows": len(first_down.estimate_rows),
        "first_down_estimated_from_history_rows": first_down.summary["estimated_from_history_rows"],
        "first_down_missing_projection_rows": first_down.summary[
            "missing_first_down_projection_rows"
        ],
        "route_proxy_caution_rows": len(route_rows),
        "injury_review_rows": len(injury_rows),
        "route_caution_positions": dict(Counter(row["position"] for row in route_rows)),
    }
    _write_csv(
        summary_path,
        SUMMARY_HEADER,
        tuple({"metric": key, "value": value} for key, value in summary.items()),
    )
    summary_json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _write_note(
        summary=summary,
        first_down_paths=first_down_paths,
        route_path=route_path,
        injury_path=injury_path,
        summary_path=summary_path,
        summary_json_path=summary_json_path,
    )
    print(json.dumps(summary, indent=2))


def _route_caution_rows(
    model_rows: list[dict[str, str]],
    truth_set_players: set[str],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for row in model_rows:
        if row.get("player_name", "") not in truth_set_players:
            continue
        position = str(row.get("position") or "")
        if position not in {"WR", "TE"}:
            continue
        warning_reasons = str(row.get("warning_reasons") or "")
        if "route" not in warning_reasons.lower():
            continue
        rows.append(
            {
                "player_name": row.get("player_name", ""),
                "position": position,
                "overall_rank": row.get("overall_rank", ""),
                "model_value": row.get("private_lve_value", ""),
                "confidence": row.get("confidence_score", ""),
                "warning_label": "Route proxy caution",
                "route_data_status": "true_routes_unavailable_free_public",
                "what_this_means": (
                    "Model has snap/target context, but not true routes run, route share, "
                    "TPRR, or YPRR."
                ),
                "allowed_proxy_fields": "snap_share|target_share|targets_per_game",
                "model_usage_status": "review_only_context_not_full_route_evidence",
                "next_action": (
                    "Do not make WR/TE decisions from route_role alone until a structured "
                    "route source exists or the limitation is accepted."
                ),
            }
        )
    return tuple(rows)


def _injury_review_rows(coverage_rows: list[dict[str, str]]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for row in coverage_rows:
        if row.get("bucket") != "injury":
            continue
        if row.get("coverage_status") != "review":
            continue
        rows.append(
            {
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "injury_source_status": row.get("source_status", ""),
                "coverage_status": row.get("coverage_status", ""),
                "manual_review_status": "unreviewed",
                "known_current_issue": "",
                "source_url": "",
                "review_note": "",
                "model_usage_status": "context_only_not_scored",
                "next_action": (
                    "Only add a sourced current injury note; do not infer durability or "
                    "healthy status from absence of news."
                ),
            }
        )
    return tuple(rows)


def _write_note(
    *,
    summary: dict[str, object],
    first_down_paths: dict[str, Path],
    route_path: Path,
    injury_path: Path,
    summary_path: Path,
    summary_json_path: Path,
) -> None:
    note = "\n".join(
        [
            "# Truth Set Lab v3.1 Trust Upgrade",
            "",
            "Status: review-only. This phase adds caution and preview reports only.",
            "",
            "## What Changed",
            "",
            "- Built a preview-only first-down projection estimator from v3 historical "
            "nflverse first-down rates.",
            "- Added a WR/TE route-proxy caution worklist so route gaps are not hidden.",
            "- Added a current injury review template for sourced notes only.",
            "- Did not change model scores, formulas, active rankings, or readiness gates.",
            "",
            "## Summary",
            "",
            f"- First-down projection rows: {summary['first_down_projection_rows']}",
            (f"- Estimated from history rows: {summary['first_down_estimated_from_history_rows']}"),
            (
                "- Missing first-down projection rows: "
                f"{summary['first_down_missing_projection_rows']}"
            ),
            f"- Route-proxy caution rows: {summary['route_proxy_caution_rows']}",
            f"- Injury review rows: {summary['injury_review_rows']}",
            "",
            "## Files",
            "",
            f"- First-down estimates: `{first_down_paths['estimates']}`",
            f"- First-down rates: `{first_down_paths['rates']}`",
            f"- First-down summary: `{first_down_paths['summary']}`",
            f"- Route-proxy cautions: `{route_path}`",
            f"- Injury review template: `{injury_path}`",
            f"- Summary CSV: `{summary_path}`",
            f"- Summary JSON: `{summary_json_path}`",
            "",
            "## Use",
            "",
            "Use these reports to inspect uncertainty while the agents finish source "
            "discovery. The estimates are not active scoring and should not unlock "
            "decision-ready status by themselves.",
            "",
        ]
    )
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_1_TRUST_UPGRADE.md").write_text(
        note,
        encoding="utf-8",
    )


def _latest_preview() -> Path | None:
    candidates = [path for path in PREVIEW_ROOT.glob("truth_set_lab_v3_preview_*") if path.is_dir()]
    return sorted(candidates, key=lambda path: path.stat().st_mtime)[-1] if candidates else None


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


if __name__ == "__main__":
    main()
