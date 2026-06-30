# ruff: noqa: E501

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "rookie_outcomes_drafted_only_feature_policy_nflverse_green_rerun_20260630"
)

BASE_HEAD = "2070a2f4ffa6b6ae83bd6ca1529880f67dd6cab0"
BRANCH = "work/rookie-outcomes-drafted-only-feature-policy-nflverse-green-rerun-20260630"
WORKTREE = r"C:\NWR\Niners-War-Room-rookie-outcomes-drafted-only-feature-policy-nflverse-green-rerun-20260630"
VERDICT = "YELLOW_REVIEW_PACKET_PARTIAL_AFTER_NFLVERSE"
NOT_ENOUGH = "Not enough information"

REFRESH_ROOT = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "nflverse_dataset_level_refresh_health_20260630"
)
PLAYER_CONTEXT_ROOT = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "nflverse_player_context_display_20260630"
)
IDENTITY_REVIEW_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_identity_review_20260630"
)
SCHEDULE_AUDIT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_schedule_audit_20260630"
)
ENTRY_STATUS_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_entry_status_hygiene_v1_20260630"
    / "historical_rookie_entry_status_v1.csv"
)
DRAFTED_AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_model"
    / "rookie_outcome_drafted_only_review_v1_20260630"
    / "drafted_only_outcome_player_audit.csv"
)
DISPLAY_V5_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "rookie_outcomes"
    / "udfa_review_application_v1_20260630"
    / "rookie_display_artifact_v5_coverage_matrix.csv"
)

DATASET_RECEIPT_COLUMNS = (
    "dataset_name",
    "source_path_or_artifact",
    "available_now",
    "row_count",
    "coverage_years",
    "positions_covered",
    "key_ids_present",
    "source_policy_status",
    "approved_for_review",
    "approved_for_model_use",
    "approved_for_training",
    "allowed_as_label_source",
    "allowed_as_feature_source",
    "allowed_for_pre_draft_context",
    "allowed_for_post_draft_context",
    "leakage_risk",
    "blocker_reason",
    "next_action",
)

ADMISSION_COLUMNS = (
    "player_name",
    "position",
    "draft_year",
    "draft_round",
    "overall_pick",
    "drafted_team",
    "college",
    "pfr_id",
    "gsis_id",
    "cfb_id",
    "has_combine_row",
    "has_ff_playerids_crosswalk",
    "admission_status",
    "blocker_reason",
    "review_only",
    "model_use_allowed",
    "training_allowed",
)

SIDECAR_COLUMNS = (
    "season_or_year",
    "position",
    "player_stats_rows",
    "matched_drafted_players",
    "outcome_v2_label_overlap",
    "missing_match_count",
    "feasible_for_review_sidecar",
    "blocker_reason",
    "notes",
)

WATCHLIST_COLUMNS = (
    "position",
    "likely_udfa_or_nondrafted_count",
    "matched_to_depth_chart_count",
    "high_depth_chart_watchlist_candidate_count",
    "identity_blocker_count",
    "missing_depth_chart_data_count",
    "feasible_for_review_watchlist",
    "blocker_reason",
    "notes",
)

FEATURE_COLUMNS = (
    "feature_name",
    "source_family",
    "source_path_or_artifact",
    "pre_draft_allowed",
    "post_draft_allowed",
    "review_only",
    "model_use_allowed",
    "training_allowed",
    "blocked_leakage",
    "required_gate",
    "reason",
)

TARGET_DATASETS = (
    "draft_picks",
    "combine",
    "player_stats",
    "rosters",
    "weekly_rosters",
    "ff_playerids",
    "depth_charts",
    "injuries",
    "snap_counts",
    "players",
    "contracts",
    "teams",
)

SIX_GATE_E_FEATURES = (
    "draft_round",
    "draft_pick",
    "draft_capital_bucket",
    "draft_year",
    "rookie_class_year",
    "position",
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)

    source = load_source_data()
    dataset_rows = build_dataset_receipt_rows(source)
    admission_rows = build_admission_rows(source)
    sidecar_rows = build_sidecar_rows(source)
    watchlist_rows = build_watchlist_rows(source)
    feature_rows = build_feature_rows()

    write_csv(args.output_root / "nflverse_dataset_receipt_matrix.csv", DATASET_RECEIPT_COLUMNS, dataset_rows)
    write_csv(args.output_root / "drafted_only_admission_gate_refresh_audit.csv", ADMISSION_COLUMNS, admission_rows)
    write_csv(args.output_root / "nflverse_player_stats_sidecar_feasibility.csv", SIDECAR_COLUMNS, sidecar_rows)
    write_csv(args.output_root / "depth_chart_nondrafted_watchlist_refresh_feasibility.csv", WATCHLIST_COLUMNS, watchlist_rows)
    write_csv(args.output_root / "gate_e_feature_policy_refresh_manifest.csv", FEATURE_COLUMNS, feature_rows)
    write_docs(args.output_root, source, dataset_rows, admission_rows, sidecar_rows, watchlist_rows, feature_rows)

    print(
        {
            "verdict": VERDICT,
            "base_head": BASE_HEAD,
            "output_root": str(args.output_root),
            "datasets": len(dataset_rows),
            "admission_rows": len(admission_rows),
            "player_context_rows": source["counts"]["player_context_rows"],
            "safe_display_rows": source["counts"]["safe_display_rows"],
        }
    )


def load_source_data() -> dict[str, object]:
    build_report = (PLAYER_CONTEXT_ROOT / "nflverse_player_context_build_report.md").read_text(encoding="utf-8")
    dataset_report = parse_dataset_table(build_report)
    display_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_display_artifact.csv")
    schema_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_schema_manifest.csv")
    join_rows = read_csv(PLAYER_CONTEXT_ROOT / "nflverse_player_context_join_health.csv")
    registry_rows = read_csv(REFRESH_ROOT / "nflverse_dataset_registry_v1.csv")
    coverage_rows = read_csv(REFRESH_ROOT / "nflverse_dataset_coverage_matrix_v1.csv")
    policy_rows = read_csv(REFRESH_ROOT / "nflverse_source_policy_matrix_v1.csv")
    entry_rows = read_csv(ENTRY_STATUS_PATH)
    drafted_rows = read_csv(DRAFTED_AUDIT_PATH)
    v5_rows = read_csv(DISPLAY_V5_PATH)
    identity_summary = (IDENTITY_REVIEW_ROOT / "nflverse_player_context_identity_review_summary.md").read_text(encoding="utf-8")
    schedule_report = (SCHEDULE_AUDIT_ROOT / "nflverse_schedule_context_build_report.md").read_text(encoding="utf-8")
    schedule_rows = read_csv(SCHEDULE_AUDIT_ROOT / "nflverse_schedule_context_audit.csv")

    counts = build_counts(display_rows, entry_rows, drafted_rows, v5_rows, schedule_rows, identity_summary)
    depth_rows = [row for row in display_rows if row["depth_chart_position"] != NOT_ENOUGH]
    depth_rank_rows = [row for row in display_rows if row["depth_chart_rank"] != NOT_ENOUGH]
    depth_team_1_rows = [row for row in depth_rows if "depth_team=1" in row["depth_chart_role"]]

    return {
        "dataset_report": dataset_report,
        "display_rows": display_rows,
        "schema_rows": schema_rows,
        "join_rows": join_rows,
        "registry_rows": registry_rows,
        "coverage_rows": coverage_rows,
        "policy_rows": policy_rows,
        "entry_rows": entry_rows,
        "drafted_rows": drafted_rows,
        "v5_rows": v5_rows,
        "identity_summary": identity_summary,
        "schedule_report": schedule_report,
        "schedule_rows": schedule_rows,
        "counts": counts,
        "depth_rows": depth_rows,
        "depth_rank_rows": depth_rank_rows,
        "depth_team_1_rows": depth_team_1_rows,
    }


def build_counts(
    display_rows: list[dict[str, str]],
    entry_rows: list[dict[str, str]],
    drafted_rows: list[dict[str, str]],
    v5_rows: list[dict[str, str]],
    schedule_rows: list[dict[str, str]],
    identity_summary: str,
) -> dict[str, int | str]:
    display_identity = Counter(row["identity_join_status"] for row in display_rows)
    display_review = Counter(row["review_required"] for row in display_rows)
    display_depth = Counter(row["depth_chart_position"] for row in display_rows)
    entry = Counter(row["entry_status"] for row in entry_rows)
    v5_udfa = Counter(row["udfa_status"] for row in v5_rows)
    v5_display = Counter(row["display_status"] for row in v5_rows)
    positions = ",".join(sorted({row["nwr_position"] for row in display_rows if row["nwr_position"]}))
    depth_positions = ",".join(
        sorted({row["depth_chart_position"] for row in display_rows if row["depth_chart_position"] != NOT_ENOUGH})
    )
    depth_teams = ",".join(
        sorted({row["nflverse_team"] for row in display_rows if row["depth_chart_position"] != NOT_ENOUGH and row["nflverse_team"] != NOT_ENOUGH})
    )
    return {
        "player_context_rows": len(display_rows),
        "safe_display_rows": display_identity["SAFE_NOW_DISPLAY_ONLY"],
        "identity_review_rows": display_identity["NEED_IDENTITY_REVIEW"],
        "review_required_true": display_review["true"],
        "entry_drafted": entry["drafted"],
        "entry_likely_udfa": entry["likely_udfa_needs_review"],
        "entry_confirmed_udfa": entry["confirmed_udfa"],
        "entry_wrong_universe": entry["wrong_universe"],
        "entry_name_collision": entry["name_collision"],
        "drafted_rows": len(drafted_rows),
        "drafted_any_label": sum(row["outcome_window_status"] != "missing_outcome_label" for row in drafted_rows),
        "v5_rows": len(v5_rows),
        "v5_udfa_review_only": v5_udfa["confirmed_udfa_review_only"],
        "v5_not_enough": v5_display[NOT_ENOUGH],
        "v5_wrong_universe": v5_display["wrong_universe_blocked"],
        "schedule_rows": len(schedule_rows),
        "positions": positions,
        "depth_positions": depth_positions,
        "depth_teams": depth_teams,
        "depth_joined": sum(count for name, count in display_depth.items() if name != NOT_ENOUGH),
        "depth_rank_present": sum(row["depth_chart_rank"] != NOT_ENOUGH for row in display_rows),
        "depth_team_1": sum(row["depth_chart_position"] != NOT_ENOUGH and "depth_team=1" in row["depth_chart_role"] for row in display_rows),
        "identity_proposals": extract_int(identity_summary, r"Safe resolution proposals: `(\d+)`"),
        "identity_human_review": extract_int(identity_summary, r"Needs human review: `(\d+)`"),
        "identity_keep_review": extract_int(identity_summary, r"Keep NEED_IDENTITY_REVIEW: `(\d+)`"),
    }


def build_dataset_receipt_rows(source: dict[str, object]) -> list[dict[str, str]]:
    report = source["dataset_report"]
    counts = source["counts"]
    rows: list[dict[str, str]] = []
    for dataset in TARGET_DATASETS:
        info = aggregate_dataset_info(dataset, report)
        row_count = info["rows"]
        coverage = info["coverage"]
        policy = info["policy"]
        available_now = "yes" if row_count != NOT_ENOUGH and info["status"] in {"GREEN", "YELLOW"} else "no"
        rows.append(
            {
                "dataset_name": dataset,
                "source_path_or_artifact": dataset_source_path(dataset),
                "available_now": available_now,
                "row_count": row_count,
                "coverage_years": coverage,
                "positions_covered": positions_for_dataset(dataset, counts),
                "key_ids_present": key_ids_for_dataset(dataset),
                "source_policy_status": policy,
                "approved_for_review": "yes" if available_now == "yes" else "no",
                "approved_for_model_use": "no",
                "approved_for_training": "no",
                "allowed_as_label_source": allowed_label_source(dataset),
                "allowed_as_feature_source": "no",
                "allowed_for_pre_draft_context": pre_draft_context(dataset),
                "allowed_for_post_draft_context": post_draft_context(dataset),
                "leakage_risk": leakage_risk(dataset),
                "blocker_reason": dataset_blocker(dataset),
                "next_action": dataset_next_action(dataset),
            }
        )
    return rows


def aggregate_dataset_info(dataset: str, report: dict[str, dict[str, str]]) -> dict[str, str]:
    if dataset == "player_stats":
        weekly = report.get("player_stats_weekly", {})
        seasonal = report.get("player_stats_seasonal", {})
        return {
            "status": "YELLOW" if weekly or seasonal else "MISSING",
            "rows": f"weekly={weekly.get('rows', NOT_ENOUGH)}; seasonal={seasonal.get('rows', NOT_ENOUGH)}",
            "coverage": f"weekly={weekly.get('coverage', NOT_ENOUGH)}; seasonal={seasonal.get('coverage', NOT_ENOUGH)}",
            "policy": f"weekly={weekly.get('policy', 'safe_review')}; seasonal={seasonal.get('policy', 'safe_review')}",
        }
    info = report.get(dataset, {})
    return {
        "status": info.get("status", "MISSING"),
        "rows": info.get("rows", NOT_ENOUGH),
        "coverage": info.get("coverage", NOT_ENOUGH),
        "policy": info.get("policy", "Not enough information"),
    }


def dataset_source_path(dataset: str) -> str:
    if dataset == "player_stats":
        return "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_build_report.md#player_stats_weekly_and_seasonal"
    return "docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_build_report.md"


def positions_for_dataset(dataset: str, counts: dict[str, int | str]) -> str:
    if dataset in {"teams", "contracts"}:
        return "not position scoped"
    return f"current player context positions={counts['positions']}"


def key_ids_for_dataset(dataset: str) -> str:
    mapping = {
        "draft_picks": "draft_year,draft_round,draft_pick,drafted_team; player IDs available only through joined artifacts",
        "combine": "review receipt only; raw combine schema not tracked in this rerun",
        "player_stats": "player/week and player/season keys in source; sidecar matching not computed here",
        "rosters": "gsis_id,sleeper_id,player_name,team,position",
        "weekly_rosters": "gsis_id,sleeper_id,team,week,status",
        "ff_playerids": "crosswalk support; player-level details not promoted here",
        "depth_charts": "player identity plus depth position/rank/role in display artifact",
        "injuries": "player identity, report week/status/practice status in display artifact",
        "snap_counts": "player identity, latest season/week/sample size in display artifact",
        "players": "player identity support",
        "contracts": "non-financial display metadata only",
        "teams": "team metadata",
    }
    return mapping[dataset]


def allowed_label_source(dataset: str) -> str:
    if dataset == "player_stats":
        return "future_review_sidecar_only_requires_label_gate"
    return "no"


def pre_draft_context(dataset: str) -> str:
    if dataset in {"draft_picks", "combine"}:
        return "review_only_after_as_of_gate"
    if dataset in {"players", "ff_playerids"}:
        return "identity_review_only"
    return "no"


def post_draft_context(dataset: str) -> str:
    if dataset in {"rosters", "weekly_rosters", "depth_charts", "injuries", "snap_counts", "contracts", "teams", "players", "ff_playerids", "draft_picks", "combine", "player_stats"}:
        return "display_or_review_only"
    return "no"


def leakage_risk(dataset: str) -> str:
    high = {"player_stats", "depth_charts", "injuries", "snap_counts", "rosters", "weekly_rosters", "contracts"}
    medium = {"combine", "players", "ff_playerids"}
    if dataset in high:
        return "high_without_as_of_gate"
    if dataset in medium:
        return "medium_identity_or_context_gate"
    return "low_review_only"


def dataset_blocker(dataset: str) -> str:
    if dataset == "player_stats":
        return "Sidecar comparison only; not label truth/training/model input without label-spec gate."
    if dataset == "depth_charts":
        return "Current opportunity context only; not pre-draft feature, UDFA proof, or historical model input."
    if dataset in {"injuries", "snap_counts", "rosters", "weekly_rosters"}:
        return "Post-draft/current context cannot confirm UDFA or become model input here."
    if dataset == "draft_picks":
        return "Positive drafted admission source only; absence does not confirm UDFA."
    if dataset == "combine":
        return "Factual context only; feature use needs explicit Gate E approval."
    return "Review/display only; no model/training/source-truth promotion."


def dataset_next_action(dataset: str) -> str:
    if dataset == "player_stats":
        return "Build separate review-only sidecar parity lane."
    if dataset == "depth_charts":
        return "Build review-only opportunity watchlist only after identity review is accepted."
    if dataset == "draft_picks":
        return "Use as drafted-only admission receipt; keep model/training closed."
    if dataset == "combine":
        return "Feature-policy approval before any model R&D use."
    return "Keep display/review-only and maintain schema/health receipts."


def build_admission_rows(source: dict[str, object]) -> list[dict[str, str]]:
    entry_by_key = {
        (row["player_name"], row["position"], row["draft_year"], row["overall_pick"]): row
        for row in source["entry_rows"]
        if row["entry_status"] == "drafted" and row["position"] in {"QB", "RB", "WR", "TE"}
    }
    rows: list[dict[str, str]] = []
    for drafted in source["drafted_rows"]:
        key = (
            drafted["player_name"],
            drafted["position"],
            drafted["draft_year"],
            drafted["overall_pick"],
        )
        entry = entry_by_key.get(key, {})
        complete = all(drafted[field] != NOT_ENOUGH and drafted[field] != "" for field in ("draft_year", "draft_round", "overall_pick", "drafted_team"))
        real_round = drafted["draft_round"].isdigit() and 1 <= int(drafted["draft_round"]) <= 7
        admitted = complete and real_round and drafted["entry_status"] == "drafted"
        rows.append(
            {
                "player_name": drafted["player_name"],
                "position": drafted["position"],
                "draft_year": drafted["draft_year"],
                "draft_round": drafted["draft_round"],
                "overall_pick": drafted["overall_pick"],
                "drafted_team": drafted["drafted_team"],
                "college": NOT_ENOUGH,
                "pfr_id": NOT_ENOUGH,
                "gsis_id": entry.get("gsis_id", NOT_ENOUGH),
                "cfb_id": entry.get("cfbd_player_id", NOT_ENOUGH),
                "has_combine_row": "Not enough information; raw combine rows are not tracked in this packet",
                "has_ff_playerids_crosswalk": "Not enough information; historical ff_playerids row-level join not computed here",
                "admission_status": "drafted_admitted_review_only" if admitted else "drafted_admission_review_required",
                "blocker_reason": "NO_BLOCKER_DRAFTED_ADMISSION_REVIEW_ONLY" if admitted else "MISSING_OR_SYNTHETIC_DRAFT_FIELD_REVIEW_REQUIRED",
                "review_only": "true",
                "model_use_allowed": "false",
                "training_allowed": "false",
            }
        )
    return rows


def build_sidecar_rows(source: dict[str, object]) -> list[dict[str, str]]:
    drafted_rows = source["drafted_rows"]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in drafted_rows:
        if row["draft_year"].isdigit() and int(row["draft_year"]) >= 2012:
            grouped[(row["draft_year"], row["position"])].append(row)
    rows: list[dict[str, str]] = []
    for (year, position), group in sorted(grouped.items(), key=lambda item: (int(item[0][0]), item[0][1])):
        player_stats_rows = (
            "weekly=76804; seasonal=42419 aggregate 2024-2025"
            if year in {"2024", "2025"}
            else "Not enough information; current tracked receipt covers 2024-2025 player context only"
        )
        overlap = sum(row["outcome_window_status"] != "missing_outcome_label" for row in group)
        rows.append(
            {
                "season_or_year": year,
                "position": position,
                "player_stats_rows": player_stats_rows,
                "matched_drafted_players": str(len(group)),
                "outcome_v2_label_overlap": str(overlap),
                "missing_match_count": "Not enough information; player_stats sidecar match not computed in this review packet",
                "feasible_for_review_sidecar": "partial_future_lane" if year in {"2024", "2025"} else "needs_historical_player_stats_refresh",
                "blocker_reason": "Requires sidecar parity lane; no label truth or training promotion.",
                "notes": "player_stats can support future review-only comparison after explicit label-spec/parity checks.",
            }
        )
    return rows


def build_watchlist_rows(source: dict[str, object]) -> list[dict[str, str]]:
    display_by_id = {row["nwr_player_id"]: row for row in source["display_rows"]}
    candidate_rows = [
        row
        for row in source["v5_rows"]
        if row.get("udfa_status") == "confirmed_udfa_review_only"
        or row.get("udffa_or_undrafted_status") in {"likely_udfa_needs_review", "confirmed_udfa_review_only"}
    ]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        grouped[row["position"]].append(row)
    rows: list[dict[str, str]] = []
    for position, group in sorted(grouped.items()):
        matched = 0
        high = 0
        identity_blocked = 0
        missing_depth = 0
        for row in group:
            context = display_by_id.get(row["player_id"])
            if not context:
                identity_blocked += 1
                missing_depth += 1
                continue
            if context["identity_join_status"] != "SAFE_NOW_DISPLAY_ONLY":
                identity_blocked += 1
            has_depth = context["depth_chart_position"] != NOT_ENOUGH
            if has_depth:
                matched += 1
                if context["depth_chart_rank"] in {"1", "2"} or "depth_team=1" in context["depth_chart_role"]:
                    high += 1
            else:
                missing_depth += 1
        rows.append(
            {
                "position": position,
                "likely_udfa_or_nondrafted_count": str(len(group)),
                "matched_to_depth_chart_count": str(matched),
                "high_depth_chart_watchlist_candidate_count": str(high),
                "identity_blocker_count": str(identity_blocked),
                "missing_depth_chart_data_count": str(missing_depth),
                "feasible_for_review_watchlist": "partial_review_only" if matched else "blocked_no_depth_match",
                "blocker_reason": "Depth-chart context cannot confirm UDFA, cannot model, and needs identity review before watchlist use.",
                "notes": "Counts are a feasibility receipt only; no active app output was created.",
            }
        )
    return rows


def build_feature_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for feature in SIX_GATE_E_FEATURES:
        source_family = "draft_picks" if feature != "position" else "draft_picks / entry-status review"
        rows.append(
            feature_row(
                feature,
                source_family,
                "docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/",
                "review_only_after_draft_as_of_gate",
                "review_only",
                "false",
                "Gate E model-use approval",
                "Named in six-feature Gate E policy cap; still not model/training approved here.",
            )
        )
    for feature, family, path, pre, post, leakage, gate, reason in (
        ("overall_pick", "draft_picks", "nflverse player-context draft receipts", "review_only_after_draft_as_of_gate", "review_only", "false", "Gate E feature approval", "Factual draft context but not part of the six-feature cap."),
        ("drafted_team", "draft_picks", "nflverse player-context draft receipts", "review_only_after_draft_as_of_gate", "review_only", "false", "Gate E feature approval", "Display context only."),
        ("combine measurements", "combine", "nflverse player-context combine receipt", "pending_as_of_gate", "review_only", "false", "Feature/source gate", "Factual measurements need explicit feature approval."),
        ("age", "rosters", "nflverse_player_context_display_artifact.csv", "pending_as_of_gate", "display_only", "false", "Feature/source gate", "Derived current age is display-only; no model approval."),
        ("roster status", "rosters/weekly_rosters", "nflverse_player_context_display_artifact.csv", "no", "display_only", "yes", "Leakage/as-of gate", "Post-draft status cannot be pre-draft input or UDFA proof."),
        ("injury_report_status", "injuries", "nflverse_player_context_display_artifact.csv", "no", "display_only", "yes", "Leakage/as-of gate", "Availability transparency only; not injury-risk score."),
        ("depth_chart_rank", "depth_charts", "nflverse_player_context_display_artifact.csv", "no", "display_only", "yes", "Leakage/as-of gate", "Opportunity context only; not pre-draft model feature."),
        ("snap_count_recency", "snap_counts", "nflverse_player_context_display_artifact.csv", "no", "display_only", "yes", "Leakage/as-of gate", "Future participation is leakage for pre-draft prediction."),
        ("player_stats", "player_stats", "nflverse player_stats receipts", "no", "review_sidecar_only", "yes", "Label-source sidecar gate", "Future production cannot be an input feature."),
        ("Outcome V2 labels", "Outcome V2", "historical label artifacts", "no", "label_target_only", "yes", "Label-source gate", "Labels are targets/evaluation only."),
        ("RotoWire/model_v4 labels", "local/vendor display labels", "model_v4 service docs", "no", "display_only", "yes", "Blocked source-policy gate", "Local/vendor-derived labels are not truth/training."),
        ("CFBD production", "CFBD", "CFBD review artifacts", "pending_identity_approval", "no", "yes", "CFBD approval gate", "CFBD remains review-only candidate context."),
        ("UDFA status", "entry-status/UDFA packets", "rookie_entry_status_hygiene_v1", "no", "status_only", "yes", "UDFA source-policy gate", "Draft absence does not confirm UDFA."),
        ("ff_rankings", "ff_rankings", "blocked NFLVerse source policy", "no", "no", "yes", "Blocked", "Vendor/private-like rankings remain blocked."),
    ):
        rows.append(feature_row(feature, family, path, pre, post, leakage, gate, reason))
    return rows


def feature_row(
    feature_name: str,
    source_family: str,
    source_path: str,
    pre_draft: str,
    post_draft: str,
    leakage: str,
    gate: str,
    reason: str,
) -> dict[str, str]:
    return {
        "feature_name": feature_name,
        "source_family": source_family,
        "source_path_or_artifact": source_path,
        "pre_draft_allowed": pre_draft,
        "post_draft_allowed": post_draft,
        "review_only": "true",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "blocked_leakage": leakage,
        "required_gate": gate,
        "reason": reason,
    }


def write_docs(
    output_root: Path,
    source: dict[str, object],
    dataset_rows: list[dict[str, str]],
    admission_rows: list[dict[str, str]],
    sidecar_rows: list[dict[str, str]],
    watchlist_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
) -> None:
    counts = source["counts"]
    docs = {
        "artifact_manifest.md": artifact_manifest(dataset_rows, admission_rows, sidecar_rows, watchlist_rows, feature_rows),
        "nflverse_green_rerun_summary.md": nflverse_green_rerun_summary(counts),
        "drafted_only_admission_gate_refresh_audit.md": drafted_only_admission_gate_refresh_audit(counts),
        "historical_label_source_refresh_policy.md": historical_label_source_refresh_policy(),
        "depth_chart_green_reaudit.md": depth_chart_green_reaudit(counts),
        "cfbd_udfa_blocker_refresh_status.md": cfbd_udfa_blocker_refresh_status(counts),
        "synthetic_draft_capital_refresh_quarantine.md": synthetic_draft_capital_refresh_quarantine(),
        "gate_f_gate_g_refresh_decision.md": gate_f_gate_g_refresh_decision(),
        "next_safe_upgrade_plan_after_nflverse_green.md": next_safe_upgrade_plan_after_nflverse_green(),
        "merge_safety_report.md": merge_safety_report(),
        "README.md": readme(),
    }
    for name, text in docs.items():
        (output_root / name).write_text(text.strip() + "\n", encoding="utf-8")


def artifact_manifest(
    dataset_rows: list[dict[str, str]],
    admission_rows: list[dict[str, str]],
    sidecar_rows: list[dict[str, str]],
    watchlist_rows: list[dict[str, str]],
    feature_rows: list[dict[str, str]],
) -> str:
    return f"""
# Artifact Manifest

Title: `NWR Rookie Outcomes Drafted-Only / Feature Policy Safe Upgrade Lane — NFLVerse + Player Context Review Rerun`

Verdict: `{VERDICT}`

Branch: `{BRANCH}`

Worktree: `{WORKTREE}`

Base HEAD: `{BASE_HEAD}`

All artifacts are review-only/spec/audit outputs. No model training, model tuning, active probabilities, app wiring, Rankings wiring, Gate G approval, source-truth promotion, CFBD model input, or UDFA modeling approval is included.

| Artifact | Rows | Purpose |
|---|---:|---|
| `nflverse_dataset_receipt_matrix.csv` | {len(dataset_rows)} | Dataset receipt and policy matrix for the NFLVerse green rerun |
| `drafted_only_admission_gate_refresh_audit.csv` | {len(admission_rows)} | Player-level drafted-only admission audit using tracked historical drafted rows |
| `nflverse_player_stats_sidecar_feasibility.csv` | {len(sidecar_rows)} | Future player_stats sidecar feasibility matrix |
| `depth_chart_nondrafted_watchlist_refresh_feasibility.csv` | {len(watchlist_rows)} | Review-only non-drafted/depth-chart watchlist feasibility |
| `gate_e_feature_policy_refresh_manifest.csv` | {len(feature_rows)} | Gate E feature/source policy refresh manifest |
| `nflverse_green_rerun_summary.md` | n/a | Summary of what changed after NFLVerse green artifacts landed |
| `drafted_only_admission_gate_refresh_audit.md` | n/a | Drafted-only admission source audit |
| `historical_label_source_refresh_policy.md` | n/a | Label-source partition after NFLVerse refresh |
| `depth_chart_green_reaudit.md` | n/a | Depth-chart updated status |
| `cfbd_udfa_blocker_refresh_status.md` | n/a | CFBD and UDFA blocker update |
| `synthetic_draft_capital_refresh_quarantine.md` | n/a | Quarantine policy for pseudo draft capital |
| `gate_f_gate_g_refresh_decision.md` | n/a | Gate F/G post-refresh decision |
| `next_safe_upgrade_plan_after_nflverse_green.md` | n/a | Safe next work map |
| `merge_safety_report.md` | n/a | Merge and guardrail proof |
"""


def nflverse_green_rerun_summary(counts: dict[str, int | str]) -> str:
    return f"""
# NFLVerse Green Rerun Summary

Base HEAD: `{BASE_HEAD}`

The required NFLVerse refresh-health artifacts are present on current `origin/work/hq-parallel-control`. The refresh-health implementation report is GREEN for dataset-level health/status reporting, and the player-context artifact is `YELLOW_PARTIAL_PLAYER_CONTEXT_ARTIFACT`.

## NFLVerse Evidence Found

- Dataset-level refresh-health folder: present.
- `src/services/nflverse_refresh_health_service.py`: present.
- `tests/test_nflverse_refresh_health_service.py`: present.
- Player-context display artifact: `{counts["player_context_rows"]}` rows.
- Safe player-context display rows: `{counts["safe_display_rows"]}`.
- Identity review rows: `{counts["identity_review_rows"]}`.
- Safe identity proposals: `{counts["identity_proposals"]}` proposals only.
- Needs human identity review: `{counts["identity_human_review"]}`.
- Keep identity review: `{counts["identity_keep_review"]}`.

## Datasets Now Available As Review/Display Receipts

`draft_picks`, `combine`, `player_stats`, `rosters`, `weekly_rosters`, `ff_playerids`, `depth_charts`, `injuries`, `snap_counts`, `players`, `contracts`, and `teams` now have tracked receipt/status evidence through the NFLVerse player-context packet.

## Changed Versus Previous WAIT State

The first safe-upgrade lane classified NFLVerse-dependent items as `WAIT_FOR_NFLVERSE_REFRESH_HEALTH_GREEN`. That wait is now resolved for audit visibility: dataset receipts exist and can be referenced in review-only policy. It is not resolved for model use, training use, source truth, Gate G, or app behavior.

Depth-chart status changed materially: a populated tracked receipt exists in the player-context report, and `{counts["depth_joined"]}` current player-context rows have a depth-chart position. This supersedes the old zero-row conclusion for review-only current opportunity context only.

## Still Blocked

- Model training/tuning/scoring.
- Active rookie probabilities.
- Gate G and Rankings/app wiring.
- UDFA modeling and UDFA confirmation from draft absence.
- CFBD model/training input.
- player_stats as label truth or input feature.
- depth chart, injury, snap, roster, and player_stats data as pre-draft/model features without explicit as-of/leakage gates.
"""


def drafted_only_admission_gate_refresh_audit(counts: dict[str, int | str]) -> str:
    return f"""
# Drafted-Only Admission Gate Refresh Audit

`draft_picks` is now present as a GREEN review/display receipt in the NFLVerse player-context packet.

Receipt facts from tracked docs:

- `draft_picks` row count: `514`.
- Coverage: `seasons=2024-2025`.
- Player-context draft-capital join rows: `75` clean joins out of `{counts["player_context_rows"]}` current Rankings rows.
- Historical drafted-only audit rows: `{counts["drafted_rows"]}`.
- Historical drafted rows with any Outcome V2 label linkage: `{counts["drafted_any_label"]}`.

The refreshed receipt supports the existing admission policy: positive `draft_picks` evidence is the only drafted-only admission source. Other datasets can enrich identity/status but cannot admit a player into the drafted-only path.

Round/pick/team completeness is preserved in the historical drafted audit for review purposes. Age, combine, and ff_playerids row-level coverage are not recalculated for all historical rows in this packet because raw refreshed rows are not tracked here and the task is audit-only.

Drafted-only review can proceed. Drafted-only model training is not approved.

`draft_picks` remains the only drafted admission source because roster, player_stats, depth chart, snap, injury, and schedule appearance are post-entry context and cannot prove draft status. Draft absence remains insufficient to confirm UDFA.
"""


def historical_label_source_refresh_policy() -> str:
    return """
# Historical Label Source Refresh Policy

Outcome V2 exact verified first-down labels remain the review-only historical evaluation target for drafted-only label coverage. They are label/evaluation targets only and are not input features.

Existing RotoWire/model_v4 labels remain local-source-derived display-only comparison material. They are not training truth, source truth, model input, or a replacement for Outcome V2.

NFLVerse `player_stats` is now visible through green/yellow refresh receipts and can support a future public sidecar comparison lane. It is not automatically label truth, training truth, model input, or source truth. A separate sidecar parity and label-spec gate is required before stronger use.

Missing labels are `Not enough information`, not failures. Incomplete windows remain right-censored, not misses. No active rookie probabilities or fake T12/T24/T36 current rookie outputs are approved.
"""


def depth_chart_green_reaudit(counts: dict[str, int | str]) -> str:
    return f"""
# Depth Chart Green Re-Audit

Approved populated tracked depth-chart receipt now exists in the NFLVerse player-context packet.

## Receipt Facts

- Source artifact: `docs/hq/data_sources/nflverse_player_context_display_20260630/nflverse_player_context_build_report.md`.
- Dataset row count in build report: `591527`.
- Coverage in build report: `seasons=2024; weeks=22`.
- Current player-context rows with depth-chart position: `{counts["depth_joined"]}`.
- Current player-context rows with explicit depth rank: `{counts["depth_rank_present"]}`.
- Current player-context rows with `depth_team=1` role text: `{counts["depth_team_1"]}`.
- Teams represented in current display joins: `{counts["depth_teams"]}`.
- Depth-chart positions represented in current display joins: `{counts["depth_positions"]}`.
- Player IDs present for display joins: yes, through `nflverse_gsis_id` and `nflverse_sleeper_id` after identity filter.
- Current-only vs historical: current player-context artifact uses 2024 depth-chart receipts; historical point-in-time pre-draft snapshots are not established.

## Policy Result

Depth charts may support a review-only current opportunity watchlist after identity review. They are not historical model features, not pre-draft features without an as-of/leakage gate, and not UDFA confirmation evidence. Missing depth chart data is not no-role.

The prior zero-row conclusion is superseded for current review-only opportunity context. It is not superseded for model/training/historical pre-draft use.

RotoWire, local_exports, and vendor depth-chart sources remain blocked.
"""


def cfbd_udfa_blocker_refresh_status(counts: dict[str, int | str]) -> str:
    return f"""
# CFBD and UDFA Blocker Refresh Status

Historical entry-status counts:

- Confirmed UDFA rows: `{counts["entry_confirmed_udfa"]}`.
- Likely UDFA / needs-review rows: `{counts["entry_likely_udfa"]}`.
- Wrong-universe rows: `{counts["entry_wrong_universe"]}`.
- Name-collision rows: `{counts["entry_name_collision"]}`.

No new NFLVerse data confirms UDFA status. Draft absence remains insufficient. Roster, weekly roster, depth chart, player_stats, snap, injury, and schedule appearance remain insufficient. Current review-only UDFA status rows are not historical source truth and do not authorize UDFA modeling.

CFBD approved historical model/training join count: `0`. CFBD can remain review-only identity/college context where human-approved, but it is not model input or training truth.

High-production non-drafted watchlist work may become a review-only packet only after identity and source-policy gates. It cannot populate model/training features from CFBD or NFLVerse appearance alone.

Remaining blocker: approved UDFA source-policy evidence and human-reviewed identity/source promotion.
"""


def synthetic_draft_capital_refresh_quarantine() -> str:
    return """
# Synthetic Draft-Capital Refresh Quarantine

No fake round 8 is admitted to drafted-only model buckets.

Synthetic or pseudo draft capital remains display-only/review-only. Missing draft capital is not zero. A player not found in `draft_picks` is not confirmed UDFA.

Only positive draft-pick evidence with a real draft year, real round, and real pick admits the drafted-only review path. This packet does not create or approve model buckets.
"""


def gate_f_gate_g_refresh_decision() -> str:
    return """
# Gate F / Gate G Refresh Decision

Gate F can be refreshed only as a partial review-only display artifact. The NFLVerse player-context artifact provides safe display/status fields for filtered rows, but it is not model-ready and not app-release approval.

Gate F cannot become model-ready from this lane. Gate G remains blocked. Rankings/app wiring is not approved. Active rookie probabilities are not approved. Fake T12/T24/T36 current rookie outputs remain blocked.

Verdict for release posture: `YELLOW_REVIEW_PACKET_PARTIAL_AFTER_NFLVERSE`.
"""


def next_safe_upgrade_plan_after_nflverse_green() -> str:
    return """
# Next Safe Upgrade Plan After NFLVerse Green

## Safe Now

- Drafted-only review/audit using positive draft-pick evidence.
- NFLVerse dataset receipt review.
- Player-context display-only review for rows passing identity filters.
- Depth-chart opportunity watchlist feasibility as review-only, not app output.
- player_stats sidecar planning as review-only.

## Safe Later After Explicit Gates

- player_stats sidecar parity build after label-spec approval.
- combine/age/draft feature expansion after Gate E feature approval.
- depth-chart watchlist after identity review acceptance.
- Gate F display refresh after UI/display policy approval.

## Blocked

- UDFA modeling.
- CFBD model/training input.
- Gate G / Rankings / app wiring.
- active rookie probabilities.
- model training/tuning/scoring.
- fake T12/T24/T36 outputs.
"""


def merge_safety_report() -> str:
    return """
# Merge Safety Report

This lane changes review-only docs, CSV audit matrices, a non-runtime report builder, and focused tests only.

Confirmed:

- no app files changed;
- no Rankings, Draft Room, Player Compare, Gate F, or Gate G behavior changed;
- no model outputs changed;
- no pinned snapshots changed;
- no `latest_candidate` or `latest_approved` changed;
- no source-truth behavior changed;
- no protected/raw/private paths tracked;
- no secrets tracked;
- no local_exports, raw, or vendor files tracked.

All new rows keep `model_use_allowed=false` and `training_allowed=false`.
"""


def readme() -> str:
    return f"""
# Rookie Outcomes Drafted-Only / Feature Policy NFLVerse Green Rerun

Verdict: `{VERDICT}`

This packet re-runs the drafted-only/feature-policy safe-upgrade review after NFLVerse refresh-health and player-context artifacts landed. It is review-only and audit/spec only.

No model training, active probabilities, Gate G, app wiring, source-truth promotion, UDFA modeling, or CFBD model/training input is approved.
"""


def parse_dataset_table(report: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for line in report.splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0] in {"dataset", "---"}:
            continue
        dataset, status, row_count, coverage, freshness, policy, usability = cells[:7]
        rows[dataset] = {
            "status": status,
            "rows": row_count,
            "coverage": coverage,
            "freshness": freshness,
            "policy": policy,
            "usability": usability,
        }
    return rows


def extract_int(text: str, pattern: str) -> int:
    match = re.search(pattern, text)
    return int(match.group(1)) if match else 0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
