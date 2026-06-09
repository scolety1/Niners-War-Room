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
V3_REPORTS = TRUTH_ROOT / "v3" / "reports"
SAMPLE_PLAYERS = (
    ROOT
    / "templates"
    / "real_data_inputs"
    / "paid_data_trial"
    / ("paid_data_trial_sample_players.csv")
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
    "v2_rank_delta",
    "v2_model_value_delta",
    "movement_cause",
    "top_positive_drivers",
    "top_negative_drivers",
    "coverage_flags",
    "audit_note",
)

MAJOR_MOVEMENT_HEADER = (
    "player_name",
    "position",
    "v2_overall_rank",
    "v3_overall_rank",
    "rank_delta",
    "v2_model_value",
    "v3_model_value",
    "model_value_delta",
    "movement_cause",
    "review_flags",
    "audit_classification",
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
    v3_preview = _latest_preview("truth_set_lab_v3_preview_*")
    v2_preview = _latest_preview("truth_set_lab_v2_preview_*")
    if v3_preview is None:
        raise FileNotFoundError("No Truth Set Lab v3 preview folder found.")
    if v2_preview is None:
        raise FileNotFoundError("No Truth Set Lab v2 preview folder found.")

    output_rows = _read_rows(v3_preview / "stats_first_veteran_model_preview_outputs.csv")
    movement_rows = _read_rows(v3_preview / "truth_set_v3_movement_vs_v2.csv")
    coverage_rows = _read_rows(v3_preview / "truth_set_v3_source_coverage.csv")
    rejected_rows = _read_rows(v3_preview / "truth_set_v3_rejected_field_log.csv")
    contribution_rows = _read_rows(v3_preview / "stats_first_feature_contributions.csv")
    sample_rows = _read_rows(SAMPLE_PLAYERS)

    truth_names = {row["player_name"] for row in sample_rows}
    output_by_name = {_name_key(row.get("player_name")): row for row in output_rows}
    movement_by_name = {_name_key(row.get("player_name")): row for row in movement_rows}
    coverage_by_name = _coverage_by_name(coverage_rows)
    contributions_by_name = _contributions_by_name(contribution_rows)

    audit_rows = _audit_group_rows(
        sample_rows,
        output_by_name,
        movement_by_name,
        coverage_by_name,
        contributions_by_name,
    )
    major_movements = _major_movement_rows(movement_rows)
    suspicious_rows = _suspicious_rows(
        truth_names,
        output_by_name,
        movement_by_name,
        coverage_by_name,
    )
    summary = {
        "v3_preview": str(v3_preview),
        "v2_preview": str(v2_preview),
        "truth_set_players": len(truth_names),
        "audit_group_rows": len(audit_rows),
        "major_movement_rows": len(major_movements),
        "suspicious_rows": len(suspicious_rows),
        "production_coverage_rows": _coverage_count(coverage_rows, "production", "covered"),
        "usage_coverage_rows": _coverage_count(coverage_rows, "role_usage", "covered"),
        "snap_coverage_rows": _coverage_count(coverage_rows, "snap_share", "covered"),
        "route_quarantined_rows": _coverage_count(coverage_rows, "route_participation", "review"),
        "rejected_field_rows": len(rejected_rows),
        "formula_changes_applied": False,
        "active_rankings_overwritten": False,
        "review_status": "review_only",
        "verdict": _verdict(major_movements, suspicious_rows),
    }

    V3_REPORTS.mkdir(parents=True, exist_ok=True)
    audit_path = V3_REPORTS / "truth_set_v3_audit_groups.csv"
    movement_path = V3_REPORTS / "truth_set_v3_audit_major_movements.csv"
    suspicious_path = V3_REPORTS / "truth_set_v3_audit_suspicious_rankings.csv"
    summary_path = V3_REPORTS / "truth_set_v3_audit_summary.csv"
    _write_csv(audit_path, AUDIT_GROUP_HEADER, audit_rows)
    _write_csv(movement_path, MAJOR_MOVEMENT_HEADER, major_movements)
    _write_csv(suspicious_path, SUSPICIOUS_HEADER, suspicious_rows)
    _write_csv(
        summary_path,
        SUMMARY_HEADER,
        tuple({"metric": key, "value": value} for key, value in summary.items()),
    )
    _write_json(V3_REPORTS / "truth_set_v3_audit_summary.json", summary)
    _write_note(
        v3_preview=v3_preview,
        audit_path=audit_path,
        movement_path=movement_path,
        suspicious_path=suspicious_path,
        summary=summary,
        major_movements=major_movements,
        suspicious_rows=suspicious_rows,
    )
    print(json.dumps(summary, indent=2))


def _audit_group_rows(
    sample_rows: list[dict[str, str]],
    output_by_name: dict[str, dict[str, str]],
    movement_by_name: dict[str, dict[str, str]],
    coverage_by_name: dict[str, list[dict[str, str]]],
    contributions_by_name: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for sample in sample_rows:
        player = sample["player_name"]
        output = output_by_name.get(_name_key(player), {})
        movement = movement_by_name.get(_name_key(player), {})
        coverage = coverage_by_name.get(_name_key(player), [])
        contributions = contributions_by_name.get(_name_key(player), [])
        for group in _groups_for_sample(sample):
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
                    "v2_rank_delta": movement.get("rank_delta", ""),
                    "v2_model_value_delta": movement.get("model_value_delta", ""),
                    "movement_cause": _movement_cause(movement),
                    "top_positive_drivers": _top_drivers(contributions, positive=True),
                    "top_negative_drivers": _top_drivers(contributions, positive=False),
                    "coverage_flags": _coverage_flags(coverage),
                    "audit_note": _audit_note(output, movement, coverage),
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
    if position == "QB":
        groups.append("qb_controls")
    if position == "TE":
        groups.append("te_controls")
    return tuple(groups or ("truth_set_other",))


def _major_movement_rows(rows: list[dict[str, str]]) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        model_delta = _float(row.get("model_value_delta"))
        rank_delta = abs(_int(row.get("rank_delta")))
        if abs(model_delta) < 5.0 and rank_delta < 75:
            continue
        output.append(
            {
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "v2_overall_rank": row.get("v2_overall_rank", ""),
                "v3_overall_rank": row.get("v3_overall_rank", ""),
                "rank_delta": row.get("rank_delta", ""),
                "v2_model_value": row.get("v2_model_value", ""),
                "v3_model_value": row.get("v3_model_value", ""),
                "model_value_delta": row.get("model_value_delta", ""),
                "movement_cause": _movement_cause(row),
                "review_flags": row.get("review_flags", ""),
                "audit_classification": _movement_classification(row),
            }
        )
    return tuple(output)


def _suspicious_rows(
    truth_names: set[str],
    output_by_name: dict[str, dict[str, str]],
    movement_by_name: dict[str, dict[str, str]],
    coverage_by_name: dict[str, list[dict[str, str]]],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for player in truth_names:
        output = output_by_name.get(_name_key(player), {})
        movement = movement_by_name.get(_name_key(player), {})
        coverage = coverage_by_name.get(_name_key(player), [])
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
                    "No v3 model output row found for truth-set player.",
                    "Check identity/name normalization before trusting the row.",
                )
            )
            continue
        confidence = _float(output.get("confidence_score"))
        warning_reasons = str(output.get("warning_reasons") or "")
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
        if _missing_bucket(coverage, "production"):
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "missing_native_production",
                    "medium",
                    "No native nflverse player-season production row matched.",
                    "Treat production-driven ranking as incomplete until player has NFL data.",
                )
            )
        if _missing_bucket(coverage, "role_usage"):
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "missing_derived_usage",
                    "medium",
                    "No play-by-play usage row matched.",
                    "Use young/rookie context only; do not infer usage.",
                )
            )
        if _missing_bucket(coverage, "projection"):
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "missing_valid_projection",
                    "medium",
                    "No valid recomputed projection stat line.",
                    "Do not let local baseline projection act as forecast evidence.",
                )
            )
        if _has_route_gap(coverage) and output.get("position") in {"WR", "TE"}:
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "route_data_unavailable",
                    "medium",
                    "Routes/route participation/TPRR/YPRR are unavailable in free data.",
                    "Do not diagnose WR/TE route formula balance without charted route data.",
                )
            )
        if abs(_float(movement.get("model_value_delta"))) >= 8.0:
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "large_v2_to_v3_value_movement",
                    "medium",
                    _movement_cause(movement),
                    "Inspect receipt drivers before promoting any v3 output.",
                )
            )
        if _possible_formula_imbalance(output, movement, coverage):
            rows.append(
                _suspicious(
                    player,
                    output.get("position", ""),
                    output.get("overall_rank", ""),
                    output.get("private_lve_value", ""),
                    output.get("confidence_score", ""),
                    "possible_formula_imbalance",
                    "medium",
                    (
                        "Large movement or ranking depends on route-unavailable/"
                        "position formula behavior."
                    ),
                    "Write a formula fixture before changing weights.",
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
    flags = str(row.get("review_flags") or "")
    position = str(row.get("position") or "")
    causes = []
    if "native nflverse production" in reason:
        causes.append("native production")
        causes.append("real first downs")
    if "derived play-by-play usage" in reason:
        causes.append("derived usage")
    if "snap share" in reason:
        causes.append("snap share")
    if position in {"WR", "TE"} and ("route values quarantined" in reason or "route" in flags):
        causes.append("route unavailable confidence/formula pressure")
    if "projection recompute" in reason:
        causes.append("projection recompute")
    if "young bridge prior" in reason:
        causes.append("young bridge")
    return "; ".join(dict.fromkeys(causes)) or "no material movement"


def _movement_classification(row: dict[str, str]) -> str:
    cause = _movement_cause(row)
    delta = abs(_float(row.get("model_value_delta")))
    if "route unavailable" in cause and row.get("position") in {"WR", "TE"}:
        return "needs_route_data_review"
    if delta >= 8:
        return "large_change_review"
    return "expected_from_v3_data_overlay"


def _coverage_by_name(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        output[_name_key(row.get("player_name"))].append(row)
    return output


def _contributions_by_name(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        output[_name_key(row.get("player_name"))].append(row)
    return output


def _coverage_flags(rows: list[dict[str, str]]) -> str:
    flags = []
    for row in rows:
        status = row.get("coverage_status", "")
        bucket = row.get("bucket", "")
        source_status = row.get("source_status", "")
        if status in {"missing", "review"}:
            flags.append(f"{bucket}:{source_status}")
    return "|".join(flags)


def _top_drivers(rows: list[dict[str, str]], *, positive: bool) -> str:
    parsed = []
    for row in rows:
        value = _float(row.get("component_contribution"))
        if positive and value <= 0:
            continue
        if not positive and value >= 0:
            continue
        parsed.append((abs(value), row.get("component", ""), row.get("feature_name", ""), value))
    parsed.sort(reverse=True)
    return "|".join(
        f"{component}:{feature}={round(value, 2)}" for _, component, feature, value in parsed[:5]
    )


def _audit_note(
    output: dict[str, str],
    movement: dict[str, str],
    coverage: list[dict[str, str]],
) -> str:
    if not output:
        return "Missing output row; identity review required."
    if output.get("warning_status") == "blocking":
        return "Blocking warning remains; not decision-ready."
    if abs(_float(movement.get("model_value_delta"))) >= 8:
        return "Large v2-to-v3 movement; inspect receipts before trusting."
    if _has_route_gap(coverage) and output.get("position") in {"WR", "TE"}:
        return "WR/TE row remains limited by unavailable route data."
    if _missing_bucket(coverage, "production") or _missing_bucket(coverage, "role_usage"):
        return "Core v3 evidence is missing for this player."
    return "V3 evidence is cleaner, but row remains review-only until gate passes."


def _missing_bucket(rows: list[dict[str, str]], bucket: str) -> bool:
    matches = [row for row in rows if row.get("bucket") == bucket]
    return not matches or any(row.get("coverage_status") == "missing" for row in matches)


def _has_route_gap(rows: list[dict[str, str]]) -> bool:
    return any(
        row.get("bucket") == "route_participation"
        and row.get("source_status")
        in {
            "unavailable_free_public",
            "missing_paid_or_charged_data",
            "missing_paid_or_charted_data",
        }
        for row in rows
    )


def _possible_formula_imbalance(
    output: dict[str, str],
    movement: dict[str, str],
    coverage: list[dict[str, str]],
) -> bool:
    position = output.get("position")
    if position in {"WR", "TE"} and _has_route_gap(coverage):
        return abs(_float(movement.get("model_value_delta"))) >= 5.0
    if position == "RB" and _int(output.get("overall_rank")) <= 10:
        return abs(_float(movement.get("model_value_delta"))) >= 8.0
    return False


def _coverage_count(rows: list[dict[str, str]], bucket: str, status: str) -> int:
    return sum(
        1 for row in rows if row.get("bucket") == bucket and row.get("coverage_status") == status
    )


def _verdict(
    major_movements: tuple[dict[str, object], ...],
    suspicious_rows: tuple[dict[str, object], ...],
) -> str:
    high = sum(1 for row in suspicious_rows if row.get("severity") == "high")
    if high:
        return "v3 improves evidence coverage but still has high-severity review rows."
    if major_movements:
        return "v3 improves model trust, but large movements need receipt review."
    return "v3 improves auditability with no large movement flags."


def _write_note(
    *,
    v3_preview: Path,
    audit_path: Path,
    movement_path: Path,
    suspicious_path: Path,
    summary: dict[str, object],
    major_movements: tuple[dict[str, object], ...],
    suspicious_rows: tuple[dict[str, object], ...],
) -> None:
    top_movements = "\n".join(
        f"- {row['player_name']}: {row['model_value_delta']} value, "
        f"{row['rank_delta']} ranks ({row['movement_cause']})"
        for row in major_movements[:12]
    )
    top_suspicious = "\n".join(
        f"- {row['player_name']}: {row['suspicion_type']} ({row['severity']})"
        for row in suspicious_rows[:16]
    )
    note = "\n".join(
        [
            "# Truth Set Lab v3 Ranking Audit",
            "",
            "Status: review-only. No formula tuning, active rankings, or gates changed.",
            "",
            "## Files",
            "",
            f"- v3 preview folder: `{v3_preview}`",
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
            f"- Production coverage rows: {summary['production_coverage_rows']}",
            f"- Usage coverage rows: {summary['usage_coverage_rows']}",
            f"- Snap coverage rows: {summary['snap_coverage_rows']}",
            f"- Route quarantined rows: {summary['route_quarantined_rows']}",
            "",
            "## Verdict",
            "",
            str(summary["verdict"]),
            "",
            "V3 is a real improvement over v2 because native nflverse production, real "
            "rushing/receiving first downs, play-by-play usage, and snap share now enter "
            "the preview. It is still not decision-ready because route participation is "
            "quarantined, all projections lack direct first-down projections, and several "
            "players still have large v2-to-v3 movement requiring receipt review.",
            "",
            "## Major Movement Classification",
            "",
            top_movements or "- None.",
            "",
            "## Suspicious Ranking Worklist",
            "",
            top_suspicious or "- None.",
            "",
            "## Recommended Next Action",
            "",
            "Do not tune formulas from vibes. Review the large movement rows and route-gap "
            "WR/TE rows using receipts. Patch only identity, source, or normalization bugs. "
            "Formula changes should wait for a fixture-backed imbalance note.",
            "",
        ]
    )
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_RANKING_AUDIT.md").write_text(note, encoding="utf-8")


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


def _latest_preview(pattern: str) -> Path | None:
    candidates = [path for path in MODEL_PREVIEW_ROOT.glob(pattern) if path.is_dir()]
    return sorted(candidates, key=lambda path: path.stat().st_mtime)[-1] if candidates else None


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


def _int(value: object) -> int:
    return int(_float(value))


if __name__ == "__main__":
    main()
