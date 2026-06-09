from __future__ import annotations

# ruff: noqa: E402,I001

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODEL_PREVIEW_ROOT = ROOT / "local_exports" / "nflverse_model_previews"
TRUTH_ROOT = ROOT / "local_exports" / "truth_set_lab"
V2_REPORTS = TRUTH_ROOT / "v2" / "reports"
SAMPLE_PLAYERS = ROOT / "templates" / "real_data_inputs" / "paid_data_trial" / (
    "paid_data_trial_sample_players.csv"
)
DOCS_ROOT = ROOT / "docs" / "codex"

AUDIT_GROUP_HEADER = (
    "audit_group",
    "player_name",
    "position",
    "overall_rank",
    "position_rank_label",
    "model_value",
    "keeper_score",
    "trade_value",
    "confidence",
    "warning_status",
    "warning_reasons",
    "asset_lifecycle",
    "movement_delta",
    "movement_reason",
    "source_flags",
    "audit_note",
)

MAJOR_MOVEMENT_HEADER = (
    "player_name",
    "position",
    "v1_overall_rank",
    "v2_overall_rank",
    "overall_rank_delta",
    "v1_model_value",
    "v2_model_value",
    "model_value_delta",
    "movement_cause",
)

SUSPICIOUS_HEADER = (
    "player_name",
    "position",
    "overall_rank",
    "model_value",
    "confidence",
    "suspicion_type",
    "severity",
    "evidence",
    "recommended_action",
)

SUMMARY_HEADER = ("metric", "value")


def main() -> None:
    v2_preview = _latest_preview("truth_set_lab_v2_preview_*")
    if v2_preview is None:
        raise FileNotFoundError("No Truth Set Lab v2 preview folder found.")
    output_rows = _read_rows(v2_preview / "stats_first_veteran_model_preview_outputs.csv")
    movement_rows = _read_rows(v2_preview / "truth_set_v2_movement_vs_v1.csv")
    source_rows = _read_rows(v2_preview / "truth_set_v2_source_log.csv")
    import_rows = _read_rows(v2_preview / "truth_set_v2_import_eligibility.csv")
    sample_rows = _read_rows(SAMPLE_PLAYERS)

    truth_names = {row["player_name"] for row in sample_rows}
    output_by_name = {_name_key(row.get("player_name")): row for row in output_rows}
    movement_by_name = {_name_key(row.get("player_name")): row for row in movement_rows}
    source_flags_by_name = _source_flags_by_name(source_rows)

    audit_rows = _audit_group_rows(
        sample_rows,
        output_by_name,
        movement_by_name,
        source_flags_by_name,
    )
    major_movements = _major_movement_rows(movement_rows)
    suspicious_rows = _suspicious_rows(
        truth_names,
        output_by_name,
        source_flags_by_name,
        import_rows,
    )
    summary = {
        "v2_preview": str(v2_preview),
        "truth_set_players": len(truth_names),
        "audit_group_rows": len(audit_rows),
        "major_movement_rows": len(major_movements),
        "suspicious_rows": len(suspicious_rows),
        "production_import_status": _source_classification(import_rows, "production"),
        "role_usage_import_status": _source_classification(import_rows, "role_usage"),
        "projection_import_status": _source_classification(import_rows, "projections"),
        "formula_changes_applied": False,
        "active_rankings_overwritten": False,
        "review_status": "review_only",
    }

    V2_REPORTS.mkdir(parents=True, exist_ok=True)
    audit_path = V2_REPORTS / "truth_set_v2_audit_groups.csv"
    movement_path = V2_REPORTS / "truth_set_v2_audit_major_movements.csv"
    suspicious_path = V2_REPORTS / "truth_set_v2_audit_suspicious_rankings.csv"
    summary_path = V2_REPORTS / "truth_set_v2_audit_summary.csv"
    _write_csv(audit_path, AUDIT_GROUP_HEADER, audit_rows)
    _write_csv(movement_path, MAJOR_MOVEMENT_HEADER, major_movements)
    _write_csv(suspicious_path, SUSPICIOUS_HEADER, suspicious_rows)
    _write_csv(
        summary_path,
        SUMMARY_HEADER,
        tuple({"metric": key, "value": value} for key, value in summary.items()),
    )
    _write_json(V2_REPORTS / "truth_set_v2_audit_summary.json", summary)
    _write_note(
        v2_preview=v2_preview,
        audit_path=audit_path,
        movement_path=movement_path,
        suspicious_path=suspicious_path,
        summary=summary,
        suspicious_rows=suspicious_rows,
        import_rows=import_rows,
    )
    print(json.dumps(summary, indent=2))


def _audit_group_rows(
    sample_rows: list[dict[str, str]],
    output_by_name: dict[str, dict[str, str]],
    movement_by_name: dict[str, dict[str, str]],
    source_flags_by_name: dict[str, set[str]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for sample in sample_rows:
        player = sample["player_name"]
        groups = _groups_for_sample(sample)
        output = output_by_name.get(_name_key(player), {})
        movement = movement_by_name.get(_name_key(player), {})
        for group in groups:
            rows.append(
                {
                    "audit_group": group,
                    "player_name": player,
                    "position": output.get("position") or sample.get("position", ""),
                    "overall_rank": output.get("overall_rank", ""),
                    "position_rank_label": output.get("position_rank_label", ""),
                    "model_value": output.get("private_lve_value", ""),
                    "keeper_score": output.get("keeper_score", ""),
                    "trade_value": output.get("trade_value", ""),
                    "confidence": output.get("confidence_score", ""),
                    "warning_status": output.get("warning_status", ""),
                    "warning_reasons": output.get("warning_reasons", ""),
                    "asset_lifecycle": output.get("asset_lifecycle_label", ""),
                    "movement_delta": movement.get("model_value_delta", ""),
                    "movement_reason": movement.get("movement_reason", ""),
                    "source_flags": "|".join(sorted(source_flags_by_name[_name_key(player)])),
                    "audit_note": _audit_note(output, source_flags_by_name[_name_key(player)]),
                }
            )
    return tuple(rows)


def _groups_for_sample(sample: dict[str, str]) -> tuple[str, ...]:
    player = sample["player_name"]
    position = sample.get("position", "")
    reason = sample.get("reason", "")
    groups: list[str] = []
    if reason.startswith("niners_roster"):
        groups.append("niners_roster_players")
    if player in {
        "Bijan Robinson",
        "Jahmyr Gibbs",
        "Kyren Williams",
        "Christian McCaffrey",
        "Ashton Jeanty",
        "De'Von Achane",
        "Chase Brown",
    }:
        groups.append("elite_or_control_rbs")
    if player in {
        "Justin Jefferson",
        "Ja'Marr Chase",
        "CeeDee Lamb",
        "Amon-Ra St. Brown",
        "Puka Nacua",
        "Malik Nabers",
        "Jaxon Smith-Njigba",
        "Tee Higgins",
        "Brian Thomas Jr.",
    }:
        groups.append("elite_or_control_wrs")
    if "young" in reason or "rookie" in reason:
        groups.append("young_bridge_players")
    if position in {"QB", "TE"}:
        groups.append("qb_te_controls")
    return tuple(groups or ("truth_set_other",))


def _major_movement_rows(rows: list[dict[str, str]]) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        model_delta = _float(row.get("model_value_delta"))
        rank_delta = abs(int(_float(row.get("overall_rank_delta"))))
        if abs(model_delta) < 2 and rank_delta < 15:
            continue
        output.append(
            {
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "v1_overall_rank": row.get("v1_overall_rank", ""),
                "v2_overall_rank": row.get("v2_overall_rank", ""),
                "overall_rank_delta": row.get("overall_rank_delta", ""),
                "v1_model_value": row.get("v1_model_value", ""),
                "v2_model_value": row.get("v2_model_value", ""),
                "model_value_delta": row.get("model_value_delta", ""),
                "movement_cause": _movement_cause(row),
            }
        )
    return tuple(output)


def _suspicious_rows(
    truth_names: set[str],
    output_by_name: dict[str, dict[str, str]],
    source_flags_by_name: dict[str, set[str]],
    import_rows: list[dict[str, str]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    role_rejected = _source_classification(import_rows, "role_usage") == "rejected"
    production_rejected = _source_classification(import_rows, "production") == "rejected"
    for player in truth_names:
        output = output_by_name.get(_name_key(player), {})
        if not output:
            rows.append(
                _suspicious(
                    player,
                    "",
                    "",
                    "",
                    "",
                    "missing_model_output",
                    "high",
                    "No v2 model output row found for truth-set player.",
                    "Check identity/name normalization before trusting the row.",
                )
            )
            continue
        flags = source_flags_by_name[_name_key(player)]
        warning_reasons = str(output.get("warning_reasons") or "")
        confidence = _float(output.get("confidence_score"))
        if str(output.get("warning_status")) == "blocking" or confidence < 45:
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "low_confidence_or_blocking_warning",
                    "high",
                    warning_reasons,
                    "Do not use as decision-ready; inspect receipts and source gaps.",
                )
            )
        if "missing_truth_set_projection" in flags:
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "missing_projection",
                    "medium",
                    "No usable offensive projection row in Truth Set v2.",
                    "Keep projection value review-only until a projection source is added.",
                )
            )
        if "projection_quality_team_mismatch" in flags:
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "projection_team_mismatch",
                    "medium",
                    "Projection team differs from active model team.",
                    "Confirm player team/source date before using projection evidence.",
                )
            )
        if role_rejected and output.get("position") in {"RB", "WR", "TE"}:
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "role_usage_rejected",
                    "medium",
                    "Corrected role/usage export has not passed validation.",
                    "Do not diagnose route/workload formula balance from this data yet.",
                )
            )
        if production_rejected:
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "production_rejected",
                    "medium",
                    "Corrected production export has not passed validation.",
                    "Request strict production re-export before formula tuning.",
                )
            )
    return tuple(rows)


def _suspicious(
    player_name: str,
    position: object,
    rank: object,
    model_value: object,
    confidence: object,
    suspicion_type: str,
    severity: str,
    evidence: str,
    recommended_action: str,
) -> dict[str, object]:
    return {
        "player_name": player_name,
        "position": position,
        "overall_rank": rank,
        "model_value": model_value,
        "confidence": confidence,
        "suspicion_type": suspicion_type,
        "severity": severity,
        "evidence": evidence,
        "recommended_action": recommended_action,
    }


def _movement_cause(row: dict[str, str]) -> str:
    reason = str(row.get("movement_reason") or "")
    if reason == "no material movement":
        return "no material movement"
    return (
        "projection recompute / young-prior update / source-quality flag rerun; "
        "production and role/usage were not corrected"
    )


def _source_flags_by_name(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    output: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        source = str(row.get("source") or "")
        if (
            row.get("source_status") == "review_flag"
            or row.get("source_status") == "rejected"
        ):
            output[_name_key(row.get("player_name"))].add(source)
    return output


def _audit_note(row: dict[str, str], flags: set[str]) -> str:
    if not row:
        return "Missing output row; identity review required."
    if row.get("warning_status") == "blocking":
        return "Blocking warning remains; not decision-ready."
    if "production_stat_columns_rejected" in flags or "role_usage_strict_export_rejected" in flags:
        return "Ranking is still limited by rejected production/role evidence."
    if "missing_truth_set_projection" in flags:
        return "Projection gap remains."
    return "No v2-specific movement; use receipts for normal review."


def _source_classification(rows: list[dict[str, str]], source: str) -> str:
    matches = [row for row in rows if row.get("source") == source]
    if not matches:
        return "missing"
    classifications = {row.get("classification", "") for row in matches}
    if "safe_after_derivation" in classifications:
        if "rejected" in classifications:
            return "safe_after_derivation_with_rejections"
        return "safe_after_derivation"
    if "rejected" in classifications:
        return "rejected"
    return sorted(classifications)[0] if classifications else "missing"


def _latest_preview(pattern: str) -> Path | None:
    candidates = [path for path in MODEL_PREVIEW_ROOT.glob(pattern) if path.is_dir()]
    return sorted(candidates)[-1] if candidates else None


def _write_note(
    *,
    v2_preview: Path,
    audit_path: Path,
    movement_path: Path,
    suspicious_path: Path,
    summary: dict[str, object],
    suspicious_rows: tuple[dict[str, object], ...],
    import_rows: list[dict[str, str]],
) -> None:
    source_status_rows = "\n".join(
        f"- {row['source']} / {row['field_group']}: "
        f"`{row['classification']}` ({row['recommendation']})"
        for row in import_rows
    )
    top_suspicious = "\n".join(
        f"- {row['player_name']}: {row['suspicion_type']} ({row['severity']})"
        for row in suspicious_rows[:12]
    )
    note = "\n".join(
        [
            "# Truth Set Lab v2 Audit",
            "",
            "Status: review-only. No model formulas, active rankings, or gates changed.",
            "",
            "## Files",
            "",
            f"- v2 preview folder: `{v2_preview}`",
            f"- Audit groups: `{audit_path}`",
            f"- Major movement: `{movement_path}`",
            f"- Suspicious rankings: `{suspicious_path}`",
            "",
            "## Summary",
            "",
            f"- Truth-set players: {summary['truth_set_players']}",
            f"- Audit group rows: {summary['audit_group_rows']}",
            f"- Major movement rows: {summary['major_movement_rows']}",
            f"- Suspicious rows: {summary['suspicious_rows']}",
            f"- Production import status: `{summary['production_import_status']}`",
            f"- Role/usage import status: `{summary['role_usage_import_status']}`",
            f"- Projection import status: `{summary['projection_import_status']}`",
            "",
            "## Verdict",
            "",
            "Truth Set Lab v2 improves auditability, not decision trust. Projection "
            "recompute and young-prior gap fills are stable, but production and "
            "role/usage remain rejected. Because those are the core evidence buckets, "
            "there is not enough clean signal to make formula conclusions yet.",
            "",
            "## Import Status",
            "",
            source_status_rows,
            "",
            "## Movement Classification",
            "",
            "No major v1-to-v2 movement was found under the current thresholds. That "
            "means the v2 rerun did not destabilize rankings, but it also did not solve "
            "the trust problem because corrected production and role/usage did not enter.",
            "",
            "## Remaining Suspicious Rows",
            "",
            top_suspicious or "- None.",
            "",
            "## Recommended Next Action",
            "",
            "Do not tune formulas from this v2 audit. The next useful step is still "
            "clean production plus clean numeric role/usage, or a paid route/usage "
            "trial that passes the Post-Pro Phase 6 criteria.",
            "",
        ]
    )
    (DOCS_ROOT / "TRUTH_SET_LAB_V2_AUDIT.md").write_text(note, encoding="utf-8")


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


if __name__ == "__main__":
    main()
