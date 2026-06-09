from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

ROLE_USAGE_AUDIT_HEADER = (
    "player_id",
    "player_name",
    "position",
    "team",
    "feature_name",
    "input_truth_bucket",
    "source_status",
    "source_key",
    "raw_value",
    "normalized_score",
    "feature_contribution",
    "role_contribution_share",
    "rank_driver_flag",
    "warning_reason",
    "imputed_flag",
    "model_usage",
)

ROLE_USAGE_SUMMARY_HEADER = (
    "summary_type",
    "position",
    "feature_name",
    "input_truth_bucket",
    "rows",
    "flagged_rank_driver_rows",
)

ROLE_USAGE_GAP_REPORT_HEADER = (
    "area",
    "status",
    "detail",
    "next_action",
)

ROLE_USAGE_FEATURES = {
    "role_security",
    "workload_earning",
    "target_earning_stability",
    "route_role",
}
WR_TE_RECEIVING_ROLE_FEATURES = {"target_earning_stability", "route_role"}
RB_WORKLOAD_FEATURES = {"workload_earning", "role_security"}
PROXY_WARNING_MARKERS = {
    "missing_participation_proxy",
    "missing_snap_counts",
    "missing_depth_chart",
    "te_route_role_gate",
}
MISSING_WARNING_MARKERS = {
    "missing_role_usage_features",
}


@dataclass(frozen=True)
class RoleUsageTruthCheckReport:
    audit_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    gap_report_rows: tuple[dict[str, object], ...]


def build_role_usage_truth_check_report(
    receipt_path: str | Path,
    contribution_path: str | Path,
) -> RoleUsageTruthCheckReport:
    receipt_rows = [
        row
        for row in _read_csv(receipt_path)
        if row.get("feature_name") in ROLE_USAGE_FEATURES
    ]
    contribution_by_player_feature = _contribution_by_player_feature(
        _read_csv(contribution_path)
    )
    total_contribution_by_player = _total_contribution_by_player(
        _read_csv(contribution_path)
    )
    audit_rows = tuple(
        _audit_row(
            row,
            contribution_by_player_feature.get(
                (row.get("player_id", ""), row.get("feature_name", "")),
                0.0,
            ),
            total_contribution_by_player.get(row.get("player_id", ""), 0.0),
        )
        for row in receipt_rows
    )
    return RoleUsageTruthCheckReport(
        audit_rows=audit_rows,
        summary_rows=tuple(_summary_rows(audit_rows)),
        gap_report_rows=tuple(_gap_report_rows(audit_rows)),
    )


def write_role_usage_truth_check_report(
    output_dir: str | Path,
    report: RoleUsageTruthCheckReport,
) -> dict[str, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "audit": root / "role_usage_truth_audit.csv",
        "summary": root / "role_usage_truth_summary.csv",
        "gap_report": root / "role_usage_gap_report.csv",
    }
    _write_csv(paths["audit"], ROLE_USAGE_AUDIT_HEADER, report.audit_rows)
    _write_csv(paths["summary"], ROLE_USAGE_SUMMARY_HEADER, report.summary_rows)
    _write_csv(paths["gap_report"], ROLE_USAGE_GAP_REPORT_HEADER, report.gap_report_rows)
    return paths


def _audit_row(
    row: dict[str, str],
    feature_contribution: float,
    total_contribution: float,
) -> dict[str, object]:
    bucket = _input_truth_bucket(row)
    share = (
        abs(feature_contribution) / total_contribution
        if total_contribution > 0
        else 0.0
    )
    flag = _rank_driver_flag(row, bucket, feature_contribution, share)
    return {
        "player_id": row.get("player_id", ""),
        "player_name": row.get("player_name", ""),
        "position": row.get("position", ""),
        "team": row.get("team", ""),
        "feature_name": row.get("feature_name", ""),
        "input_truth_bucket": bucket,
        "source_status": row.get("source_status", ""),
        "source_key": row.get("source_key", ""),
        "raw_value": row.get("raw_value", ""),
        "normalized_score": row.get("normalized_score", ""),
        "feature_contribution": round(feature_contribution, 3),
        "role_contribution_share": round(share, 4),
        "rank_driver_flag": flag,
        "warning_reason": row.get("warning_reason", ""),
        "imputed_flag": row.get("imputed_flag", ""),
        "model_usage": row.get("model_usage", ""),
    }


def _input_truth_bucket(row: dict[str, str]) -> str:
    warnings = _warning_set(row.get("warning_reason", ""))
    source_status = row.get("source_status", "")
    feature_name = row.get("feature_name", "")
    raw_value = row.get("raw_value", "")
    if warnings & MISSING_WARNING_MARKERS:
        return "missing"
    if row.get("imputed_flag") == "true" or source_status == "neutral_imputation":
        return "neutral_imputation"
    if feature_name == "workload_earning" and raw_value:
        return "derived_usage"
    if feature_name == "target_earning_stability" and raw_value:
        if any(marker in raw_value for marker in ("target_share=", "wopr=", "air_yards_share=")):
            return "derived_usage"
        if "targets_per_game=" in raw_value and warnings & PROXY_WARNING_MARKERS:
            return "proxy_usage"
    if feature_name == "role_security":
        if "missing_snap_counts" in warnings and "missing_depth_chart" in warnings:
            return "missing"
        if warnings & PROXY_WARNING_MARKERS:
            return "proxy_usage"
    if feature_name == "route_role" and warnings & PROXY_WARNING_MARKERS:
        return "proxy_usage"
    if warnings & PROXY_WARNING_MARKERS:
        return "proxy_usage"
    if source_status == "imported_real_data":
        return "imported_real_usage"
    if source_status == "derived_real_data":
        return "derived_usage"
    if source_status == "manual_review":
        return "proxy_usage"
    return "missing" if not row.get("raw_value") else "derived_usage"


def _rank_driver_flag(
    row: dict[str, str],
    bucket: str,
    feature_contribution: float,
    role_contribution_share: float,
) -> str:
    position = row.get("position", "")
    feature_name = row.get("feature_name", "")
    suspect_bucket = bucket in {"proxy_usage", "neutral_imputation", "missing"}
    high_feature_driver = abs(feature_contribution) >= 10.0 or role_contribution_share >= 0.18
    if suspect_bucket and high_feature_driver:
        return "role_driven_by_proxy_or_imputation"
    if position in {"WR", "TE"} and feature_name in WR_TE_RECEIVING_ROLE_FEATURES:
        if bucket == "proxy_usage":
            return "wr_te_route_target_proxy_review"
        if bucket in {"neutral_imputation", "missing"}:
            return "wr_te_route_target_missing_review"
    if position == "RB" and feature_name in RB_WORKLOAD_FEATURES:
        if bucket == "proxy_usage":
            return "rb_workload_proxy_review"
        if bucket in {"neutral_imputation", "missing"}:
            return "rb_workload_missing_review"
    return ""


def _summary_rows(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    flagged: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        key = (
            str(row.get("position", "")),
            str(row.get("feature_name", "")),
            str(row.get("input_truth_bucket", "")),
        )
        counts[key] += 1
        if row.get("rank_driver_flag"):
            flagged[key] += 1
    output = [
        {
            "summary_type": "by_position_feature_bucket",
            "position": position,
            "feature_name": feature_name,
            "input_truth_bucket": bucket,
            "rows": count,
            "flagged_rank_driver_rows": flagged[(position, feature_name, bucket)],
        }
        for (position, feature_name, bucket), count in sorted(counts.items())
    ]
    total_counts: Counter[str] = Counter(str(row.get("input_truth_bucket", "")) for row in rows)
    total_flagged: Counter[str] = Counter(
        str(row.get("input_truth_bucket", ""))
        for row in rows
        if row.get("rank_driver_flag")
    )
    output.extend(
        {
            "summary_type": "overall_bucket",
            "position": "ALL",
            "feature_name": "ALL",
            "input_truth_bucket": bucket,
            "rows": count,
            "flagged_rank_driver_rows": total_flagged[bucket],
        }
        for bucket, count in sorted(total_counts.items())
    )
    return output


def _gap_report_rows(rows: tuple[dict[str, object], ...]) -> list[dict[str, object]]:
    flagged_rows = [row for row in rows if row.get("rank_driver_flag")]
    bucket_counts = Counter(str(row.get("input_truth_bucket", "")) for row in rows)
    flag_counts = Counter(str(row.get("rank_driver_flag", "")) for row in flagged_rows)
    player_flags: dict[str, set[str]] = defaultdict(set)
    for row in flagged_rows:
        player_flags[str(row.get("player_name") or row.get("player_id"))].add(
            str(row.get("rank_driver_flag", ""))
        )
    return [
        {
            "area": "role_usage_truth",
            "status": "review" if flagged_rows else "ready",
            "detail": (
                f"{len(flagged_rows)} role/usage rows are rank-sensitive and "
                "driven by proxy, neutral, or missing inputs."
            ),
            "next_action": "Inspect flagged players before trusting role-driven ranks.",
        },
        {
            "area": "input_truth_buckets",
            "status": "review",
            "detail": "; ".join(
                f"{bucket}={count}" for bucket, count in sorted(bucket_counts.items())
            ),
            "next_action": (
                "Backfill paid/free route, participation, or workload sources where gaps "
                "matter."
            ),
        },
        {
            "area": "flag_types",
            "status": "review" if flag_counts else "ready",
            "detail": "; ".join(
                f"{flag}={count}" for flag, count in sorted(flag_counts.items())
            )
            or "No rank-sensitive role/usage proxy flags.",
            "next_action": "Prioritize WR/TE route/target flags and RB workload flags.",
        },
        {
            "area": "flagged_players",
            "status": "review" if player_flags else "ready",
            "detail": "; ".join(
                f"{player}:{','.join(sorted(flags))}"
                for player, flags in sorted(player_flags.items())[:25]
            )
            or "No flagged players.",
            "next_action": (
                "Use receipts to decide whether each proxy is acceptable or needs better data."
            ),
        },
    ]


def _contribution_by_player_feature(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], float]:
    output: dict[tuple[str, str], float] = defaultdict(float)
    for row in rows:
        feature = row.get("feature_name", "")
        if feature in ROLE_USAGE_FEATURES:
            output[(row.get("player_id", ""), feature)] += _float(
                row.get("component_contribution")
            )
    return dict(output)


def _total_contribution_by_player(rows: list[dict[str, str]]) -> dict[str, float]:
    output: dict[str, float] = defaultdict(float)
    for row in rows:
        output[row.get("player_id", "")] += abs(_float(row.get("component_contribution")))
    return dict(output)


def _warning_set(value: object) -> set[str]:
    return {part.strip() for part in str(value or "").split("|") if part.strip()}


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8") as handle:
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


def _float(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0
