from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path
from typing import Iterable

import pandas as pd


ARTIFACT_DIR = Path(__file__).resolve().parent
ROOT = ARTIFACT_DIR.parents[3]
BASELINE_INPUT = Path(
    r"C:\NWR_REVIEW\current_board_shadow_input_gate_v1_20260702"
    r"\current_board_baseline_shadow_input_review_only.csv"
)
OUTSIDE_DIR = Path(r"C:\NWR_REVIEW\current_board_candidate_feature_input_gate_v1_20260702")
OUTSIDE_EXPORT = OUTSIDE_DIR / "current_board_candidate_feature_input_review_only.csv"
USAGE_DATASET = (
    ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_core_usage_review_dataset_v1_20260701"
    / "nwr_nflverse_usage_review_dataset_v1.parquet"
)
SOURCE_CONTRACT = (
    ROOT
    / "docs"
    / "hq"
    / "experiments"
    / "historical_tuning_source_contract_v1_20260701"
)

BRANCH = "work/current-board-candidate-feature-input-gate-v1-20260702"
BASE_HEAD = "30b5010156bb6991158f11dec632107e769058d0"
BASELINE_SHA256 = "85bca72a67860260eb03e5907087c3fe7e7e521fb69779bd3264e747d5908952"
BASELINE_ROWS = 370
FEATURE_ANCHOR_SEASON = 2025
PREDICTION_ANCHOR = "2026_current_board_shadow_review"
SELECTED = "wr_boundary_breakout_sensitivity_guard"
DECISION = "PARTIAL_CANDIDATE_FEATURE_INPUT_NEEDS_REVIEW"

ELIGIBLE_POSITIONS = {"QB", "RB", "WR", "TE"}
AVAILABLE_SUM_FEATURES = {
    "prior_carries": "carries",
    "prior_interceptions": "passing_interceptions",
    "prior_opportunities": "opportunities",
    "prior_passing_attempts": "passing_attempts",
    "prior_passing_completions": "completions",
    "prior_passing_first_downs": "passing_first_downs",
    "prior_passing_td": "passing_touchdowns",
    "prior_passing_yards": "passing_yards",
    "prior_receiving_first_downs": "receiving_first_downs",
    "prior_receiving_yards": "receiving_yards",
    "prior_receptions": "receptions",
    "prior_rushing_first_downs": "rushing_first_downs",
    "prior_rushing_yards": "rushing_yards",
    "prior_targets": "targets",
    "prior_touches": "touches",
}
BLOCKED_PRIMARY_FEATURES = {
    "prior_games": "BLOCKED_WEEKLY_ROW_COUNT_NOT_ADMITTED_AS_GAMES",
    "prior_nwr_points": "BLOCKED_CORE_USAGE_DATASET_LACKS_FULL_SCORING_COMPONENTS",
    "prior_nwr_ppg": "BLOCKED_CORE_USAGE_DATASET_LACKS_FULL_SCORING_COMPONENTS_AND_GAMES",
}
NULL_FENCED_EXCLUDED = [
    "prior_offensive_snaps",
    "prior_offense_pct",
    "prior_receiving_air_yards",
    "prior_receiving_yards_after_catch",
]
PRIMARY_FEATURES = [
    "prior_carries",
    "prior_games",
    "prior_interceptions",
    "prior_nwr_points",
    "prior_nwr_ppg",
    "prior_opportunities",
    "prior_passing_attempts",
    "prior_passing_completions",
    "prior_passing_first_downs",
    "prior_passing_td",
    "prior_passing_yards",
    "prior_receiving_first_downs",
    "prior_receiving_yards",
    "prior_receptions",
    "prior_rushing_first_downs",
    "prior_rushing_yards",
    "prior_targets",
    "prior_touches",
]
OUTPUT_FIELDS = [
    "stable_player_id",
    "player_name",
    "position",
    "team",
    "feature_anchor_season",
    "prediction_anchor",
    "player_id_sleeper",
    "player_id_gsis",
    "feature_join_status",
    "candidate_feature_ready",
    "missing_required_features",
    *PRIMARY_FEATURES,
    "feature_source_artifact",
    "join_method",
    "review_only",
    "candidate_rank_output_present",
    "production_approved",
    "app_wiring_allowed",
    "model_use_allowed",
    "source_truth_allowed",
]


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    OUTSIDE_DIR.mkdir(parents=True, exist_ok=True)

    baseline_checksum = sha256(BASELINE_INPUT)
    if baseline_checksum != BASELINE_SHA256:
        raise SystemExit(f"Baseline checksum mismatch: {baseline_checksum}")
    baseline_rows = read_csv(BASELINE_INPUT)
    if len(baseline_rows) != BASELINE_ROWS:
        raise SystemExit(f"Baseline row count mismatch: {len(baseline_rows)}")

    usage_raw = load_usage_dataset()
    usage_exact_duplicate_rows = int(usage_raw.duplicated(keep=False).sum())
    usage = usage_raw.drop_duplicates().copy()
    aggregate = aggregate_usage_features(usage)
    export_rows = build_feature_input_rows(baseline_rows, aggregate)
    write_csv_path(OUTSIDE_EXPORT, export_rows, OUTPUT_FIELDS)

    context = {
        "branch": BRANCH,
        "base_head": BASE_HEAD,
        "current_head": git("rev-parse", "HEAD"),
        "decision": DECISION,
        "selected": SELECTED,
        "baseline_checksum": baseline_checksum,
        "baseline_rows": len(baseline_rows),
        "export_rows": len(export_rows),
        "join_count": sum(row["feature_join_status"] == "EXACT_SLEEPER_MATCH_2025_USAGE" for row in export_rows),
        "ready_count": sum(row["candidate_feature_ready"] == "true" for row in export_rows),
        "missing_count": sum(row["feature_join_status"] != "EXACT_SLEEPER_MATCH_2025_USAGE" for row in export_rows),
        "outside_export": str(OUTSIDE_EXPORT),
        "outside_export_sha256": sha256(OUTSIDE_EXPORT),
        "usage_rows_2025_raw": len(usage_raw),
        "usage_rows_2025_exact_duplicate_rows": usage_exact_duplicate_rows,
        "usage_rows_2025_after_exact_dedup": len(usage),
    }

    write_csv("current_board_candidate_feature_input_schema.csv", schema_rows())
    write_csv("current_board_candidate_feature_input_sample.csv", export_rows[:40], OUTPUT_FIELDS)
    write_csv("current_board_candidate_feature_input_row_count_report.csv", row_count_rows(context))
    write_csv("current_board_feature_join_report.csv", join_report_rows(export_rows))
    write_csv("missing_candidate_feature_report.csv", missing_report_rows(export_rows))
    write_csv("required_candidate_feature_schema.csv", required_feature_schema_rows())
    write_csv("allowed_feature_use_report.csv", allowed_feature_use_rows())
    write_text("current_board_candidate_feature_input_gate_summary.md", summary(context))
    write_text("candidate_feature_input_decision.md", decision_doc(context))
    write_text("feature_anchor_decision.md", feature_anchor_decision(context))
    write_text("null_fenced_feature_policy.md", null_fenced_policy())
    write_text("blocked_input_fields_report.md", blocked_input_fields_report())
    write_text("candidate_shadow_rank_calculation_contract.md", rank_contract(context))
    write_text("guardrail_report.md", guardrail_report(context))
    write_text("merge_safety_report.md", merge_safety_report())
    write_text("next_phase_handoff.md", next_phase_handoff(context))
    write_text("artifact_manifest.md", artifact_manifest(context))
    write_outside_readme(context)


def load_usage_dataset() -> pd.DataFrame:
    frame = pd.read_parquet(USAGE_DATASET)
    frame = frame[
        (pd.to_numeric(frame["season"], errors="coerce") == FEATURE_ANCHOR_SEASON)
        & (frame["season_type"].astype(str).eq("REG"))
    ].copy()
    frame["player_id_sleeper"] = frame["player_id_sleeper"].astype(str).str.strip()
    frame = frame[frame["player_id_sleeper"].ne("") & frame["player_id_sleeper"].ne("nan")]
    return frame


def aggregate_usage_features(usage: pd.DataFrame) -> dict[str, dict[str, object]]:
    grouped = usage.groupby("player_id_sleeper", dropna=False)
    rows: dict[str, dict[str, object]] = {}
    for sleeper_id, group in grouped:
        out: dict[str, object] = {
            "player_id_sleeper": str(sleeper_id),
            "player_id_gsis": first_nonblank(group["player_id_gsis"]),
            "source_week_rows": int(len(group)),
        }
        for feature, source in AVAILABLE_SUM_FEATURES.items():
            out[feature] = safe_sum(group[source])
        for feature in BLOCKED_PRIMARY_FEATURES:
            out[feature] = ""
        rows[str(sleeper_id)] = out
    return rows


def build_feature_input_rows(
    baseline_rows: list[dict[str, str]],
    aggregate: dict[str, dict[str, object]],
) -> list[dict[str, str]]:
    output = []
    for baseline in baseline_rows:
        player_id = clean(baseline.get("stable_player_id"))
        position = clean(baseline.get("position")).upper()
        agg = aggregate.get(player_id)
        eligible = position in ELIGIBLE_POSITIONS
        row = {
            "stable_player_id": player_id,
            "player_name": clean(baseline.get("player_name")),
            "position": position,
            "team": clean(baseline.get("team")),
            "feature_anchor_season": str(FEATURE_ANCHOR_SEASON),
            "prediction_anchor": PREDICTION_ANCHOR,
            "player_id_sleeper": player_id if agg else "",
            "player_id_gsis": str(agg.get("player_id_gsis", "")) if agg else "",
            "feature_join_status": feature_join_status(eligible, agg),
            "candidate_feature_ready": "false",
            "missing_required_features": "",
            "feature_source_artifact": str(USAGE_DATASET.relative_to(ROOT)).replace("\\", "/"),
            "join_method": "stable_player_id_to_player_id_sleeper_exact" if agg else "no_join",
            "review_only": "true",
            "candidate_rank_output_present": "false",
            "production_approved": "false",
            "app_wiring_allowed": "false",
            "model_use_allowed": "false",
            "source_truth_allowed": "false",
        }
        for feature in PRIMARY_FEATURES:
            row[feature] = ""
        if agg and eligible:
            for feature in AVAILABLE_SUM_FEATURES:
                row[feature] = format_number(agg[feature])
        missing = missing_required(row, eligible)
        row["missing_required_features"] = ";".join(missing)
        output.append(row)
    return output


def feature_join_status(eligible: bool, aggregate_row: dict[str, object] | None) -> str:
    if not eligible:
        return "NOT_ELIGIBLE_POSITION_FOR_SELECTED_CANDIDATE"
    if not aggregate_row:
        return "MISSING_2025_USAGE_FEATURES"
    return "EXACT_SLEEPER_MATCH_2025_USAGE"


def missing_required(row: dict[str, str], eligible: bool) -> list[str]:
    if not eligible:
        return ["not_eligible_position_for_selected_candidate"]
    missing = [feature for feature in PRIMARY_FEATURES if clean(row.get(feature)) == ""]
    return missing


def safe_sum(series: pd.Series) -> float | int | str:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.isna().all():
        return ""
    total = numeric.sum(skipna=True)
    return int(total) if float(total).is_integer() else round(float(total), 6)


def first_nonblank(series: pd.Series) -> str:
    for value in series:
        text = clean(value)
        if text and text.lower() != "nan":
            return text
    return ""


def schema_rows() -> list[dict[str, str]]:
    rows = []
    for field in OUTPUT_FIELDS:
        rows.append(
            {
                "field_name": field,
                "field_type": field_type(field),
                "source_or_derivation": field_source(field),
                "primary_candidate_input": str(field in PRIMARY_FEATURES),
                "review_only": "true",
                "production_approved": "false",
                "notes": field_notes(field),
            }
        )
    return rows


def field_type(field: str) -> str:
    if field in PRIMARY_FEATURES:
        return "number_or_null"
    if field in {"review_only", "candidate_rank_output_present", "production_approved", "app_wiring_allowed", "model_use_allowed", "source_truth_allowed", "candidate_feature_ready"}:
        return "boolean_string"
    return "string"


def field_source(field: str) -> str:
    if field in AVAILABLE_SUM_FEATURES:
        return f"2025 REG sum of {AVAILABLE_SUM_FEATURES[field]}"
    if field in BLOCKED_PRIMARY_FEATURES:
        return BLOCKED_PRIMARY_FEATURES[field]
    if field == "player_id_sleeper":
        return "stable_player_id exact join to nflverse player_id_sleeper"
    if field == "player_id_gsis":
        return "nflverse player_id_gsis audit field after exact sleeper join"
    return "baseline input or gate metadata"


def field_notes(field: str) -> str:
    if field in BLOCKED_PRIMARY_FEATURES:
        return "Required for candidate rank calculation; remains null pending a safer source gate."
    if field in AVAILABLE_SUM_FEATURES:
        return "Generated only for exact stable-id joins; missing rows remain null."
    return ""


def row_count_rows(context: dict[str, object]) -> list[dict[str, str]]:
    return [
        metric("baseline_rows", context["baseline_rows"], "Rows read from approved current-board baseline input."),
        metric("candidate_feature_input_rows", context["export_rows"], "Rows written to local-only feature input."),
        metric("exact_feature_join_rows", context["join_count"], "Rows joined by stable_player_id to player_id_sleeper."),
        metric("candidate_feature_ready_rows", context["ready_count"], "Rows with every required primary feature available."),
        metric("missing_or_not_eligible_rows", context["missing_count"], "Rows not joined or not eligible by position."),
        metric("outside_export_path", context["outside_export"], "Full export path outside repo."),
        metric("outside_export_sha256", context["outside_export_sha256"], "SHA256 checksum for outside export."),
        metric("feature_anchor_season", FEATURE_ANCHOR_SEASON, "Completed season factual anchor."),
        metric("usage_rows_2025_raw", context["usage_rows_2025_raw"], "Raw 2025 REG rows read from core usage dataset."),
        metric("usage_rows_2025_exact_duplicate_rows", context["usage_rows_2025_exact_duplicate_rows"], "Rows participating in exact duplicate groups."),
        metric("usage_rows_2025_after_exact_dedup", context["usage_rows_2025_after_exact_dedup"], "Rows used for aggregation after dropping exact duplicates."),
    ]


def join_report_rows(export_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counts: dict[tuple[str, str], int] = {}
    for row in export_rows:
        key = (row["position"], row["feature_join_status"])
        counts[key] = counts.get(key, 0) + 1
    return [
        {
            "position": position,
            "feature_join_status": status,
            "rows": str(count),
            "join_key": "stable_player_id_to_player_id_sleeper_exact",
            "fuzzy_name_match_used": "false",
        }
        for (position, status), count in sorted(counts.items())
    ]


def missing_report_rows(export_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in export_rows:
        if row["missing_required_features"]:
            rows.append(
                {
                    "stable_player_id": row["stable_player_id"],
                    "player_name": row["player_name"],
                    "position": row["position"],
                    "team": row["team"],
                    "feature_join_status": row["feature_join_status"],
                    "missing_required_features": row["missing_required_features"],
                    "review_action": "Not enough information; do not fill missing with zero.",
                }
            )
    return rows or [
        {
            "stable_player_id": "",
            "player_name": "",
            "position": "",
            "team": "",
            "feature_join_status": "",
            "missing_required_features": "",
            "review_action": "No missing rows.",
        }
    ]


def required_feature_schema_rows() -> list[dict[str, str]]:
    source_contract_rows = read_csv(SOURCE_CONTRACT / "allowed_review_only_feature_contract_v1.csv")
    by_feature = {row["feature"]: row for row in source_contract_rows}
    rows = []
    for feature in PRIMARY_FEATURES:
        contract = by_feature.get(feature, {})
        rows.append(
            {
                "feature": feature,
                "required_for_primary_candidate": "true",
                "source_contract_decision": contract.get("contract_decision", ""),
                "candidate_gate_status": "AVAILABLE_FROM_2025_USAGE_AGGREGATE" if feature in AVAILABLE_SUM_FEATURES else BLOCKED_PRIMARY_FEATURES[feature],
                "null_fenced_primary_excluded": "false",
                "notes": field_notes(feature),
            }
        )
    return rows


def allowed_feature_use_rows() -> list[dict[str, str]]:
    rows = []
    for feature in PRIMARY_FEATURES:
        rows.append(
            {
                "feature": feature,
                "primary_input_status": "AVAILABLE_PARTIAL_EXPORT" if feature in AVAILABLE_SUM_FEATURES else "BLOCKED_NULL_IN_PARTIAL_EXPORT",
                "production_approved": "false",
                "model_use_allowed": "false",
                "source_truth_allowed": "false",
                "hidden_sort_allowed": "false",
                "recommendation_allowed": "false",
                "notes": field_notes(feature),
            }
        )
    return rows


def summary(context: dict[str, object]) -> str:
    return f"""# Current Board Candidate Feature Input Gate Summary

Decision: `{context['decision']}`

This gate generated a partial current-board candidate feature input for `{context['selected']}` using completed 2025 NFLVerse Core Usage Review Dataset facts where a stable ID join was available.

Key facts:

- Baseline input rows: `{context['baseline_rows']}`
- Baseline checksum: `{context['baseline_checksum']}`
- Feature anchor season: `{FEATURE_ANCHOR_SEASON}`
- Prediction anchor: `{PREDICTION_ANCHOR}`
- Exact feature joins: `{context['join_count']}`
- Candidate-feature-ready rows: `{context['ready_count']}`
- 2025 raw usage rows / after exact dedup: `{context['usage_rows_2025_raw']}` / `{context['usage_rows_2025_after_exact_dedup']}`
- Outside export: `{context['outside_export']}`
- Outside export checksum: `{context['outside_export_sha256']}`

Why partial:

- `prior_nwr_points` and `prior_nwr_ppg` remain blocked because Core Usage Review Dataset V1 does not carry the full scoring components required to derive NWR scoring safely.
- `prior_games` remains blocked because weekly row counts have not been admitted as the source-contract games denominator.
- Therefore no current-board candidate ranks should be calculated from this export yet.
- Exact duplicate source rows were collapsed before aggregation; no fuzzy matching or missing-as-zero transformation was applied.
"""


def decision_doc(context: dict[str, object]) -> str:
    return f"""# Candidate Feature Input Decision

Decision: `{context['decision']}`

Safe to use now:

- Stable ID exact joins from `stable_player_id` to `player_id_sleeper`.
- Completed 2025 REG factual usage sums for the available primary features.
- Missing rows and blocked features are explicitly null/blank and labeled `Not enough information`.

Not safe yet:

- Candidate rank calculation.
- Candidate score calculation.
- Production formula use.
- App/rank/runtime wiring.

Required before rank calculation:

1. Admit a safe source for `prior_nwr_points`.
2. Admit a safe source for `prior_nwr_ppg`.
3. Admit a safe source for `prior_games`.
4. Re-run this gate and require `candidate_feature_ready_rows > 0`.
"""


def feature_anchor_decision(context: dict[str, object]) -> str:
    return f"""# Feature Anchor Decision

Feature anchor used: `{FEATURE_ANCHOR_SEASON}`

Prediction anchor: `{PREDICTION_ANCHOR}`

Rationale:

- Current HQ context is July 2026.
- The latest completed NFL season available in Core Usage Review Dataset V1 is 2025.
- 2025 factual usage can be used as lagged review-only feature context for a 2026 current-board shadow packet only when stable identity joins pass.

Limitations:

- This gate does not use current injuries, depth, schedule, role, availability, rankings, ADP, projections, vendor context, or target outcomes.
- The feature anchor is not a production model anchor.
"""


def null_fenced_policy() -> str:
    items = "\n".join(f"- `{feature}`" for feature in NULL_FENCED_EXCLUDED)
    return f"""# Null-Fenced Feature Policy

The four Source Contract V1 null-fenced optional fields are excluded from the primary current-board candidate feature input:

{items}

They are not present in the outside export and cannot be used for primary candidate rank calculation. Any future sensitivity-only use requires a separate explicit human gate.
"""


def blocked_input_fields_report() -> str:
    return """# Blocked Input Fields Report

Blocked from this feature input:

- Target-season outcomes.
- Current injuries, depth, schedule, role, availability, rankings, ADP, projections, or vendor context.
- Market/ADP/vendor/projection fields as source truth.
- Routes, TPRR, YPRR, route proxies.
- Red-zone sidecars and ambiguous `rz_att`.
- Null-fenced optional features in the primary input.
- Missing-as-zero transformations.
- Candidate rank, candidate score, app wiring, hidden sort, recommendation, production approval, or runtime output.
"""


def rank_contract(context: dict[str, object]) -> str:
    return f"""# Candidate Shadow Rank Calculation Contract

Candidate: `{context['selected']}`

Current status: `DO_NOT_CALCULATE_RANKS_FROM_THIS_PARTIAL_EXPORT`

Required before rank calculation:

- Every row intended for candidate scoring must have non-null `prior_nwr_points`.
- QB rows intended for guard evaluation must have non-null `prior_games`.
- `prior_nwr_ppg` must be safely available if any future candidate variant uses it.
- Missing values must not be converted to zero.

Allowed later, after a successful feature input gate:

- Calculate review-only candidate scores outside app/runtime paths.
- Join candidate shadow scores back to the approved baseline input by `stable_player_id`.
- Produce static CSV/HTML review artifacts only.

Blocked:

- App wiring, live preview, hidden sort, recommendations, production ranking logic, source-truth promotion, and production formula updates.
"""


def guardrail_report(context: dict[str, object]) -> str:
    return f"""# Guardrail Report

Verdict: `GREEN_GUARDRAILS_PARTIAL_INPUT_REVIEW_ONLY`

- Baseline checksum matched before use.
- Current-board row count was `{context['baseline_rows']}`.
- Joins used stable IDs only; no fuzzy name matching.
- No target-season outcomes were used.
- Feature anchor is documented as `{FEATURE_ANCHOR_SEASON}`.
- No blocked fields are included.
- Null-fenced optional fields are excluded from the primary input.
- Missing values were not forced to zero.
- No app/model/rank/source-truth/runtime behavior changed.
- No candidate ranks were wired into NWR.
- No production formula/config files changed.
- No raw/shared/cache/local export/secrets files are tracked.
"""


def merge_safety_report() -> str:
    return """# Merge Safety Report

Merge-safe changed paths:

- `docs/hq/experiments/current_board_candidate_feature_input_gate_v1_20260702/`
- `tests/test_current_board_candidate_feature_input_gate_v1_20260702.py`

The full generated feature input lives outside the repo. Do not track raw/shared/cache/local export/secrets files.
"""


def next_phase_handoff(context: dict[str, object]) -> str:
    return f"""# Next Phase Handoff

Recommended next phase: `Current Board Candidate Scoring Feature Completion Gate V1`.

Goal:

- Admit safe completed-2025 sources for `prior_nwr_points`, `prior_nwr_ppg`, and `prior_games`.
- Then re-run this gate.

Do not run current-board candidate rank calculation until this partial export becomes complete enough for `{context['selected']}`.
"""


def artifact_manifest(context: dict[str, object]) -> str:
    names = [
        "current_board_candidate_feature_input_gate_summary.md",
        "candidate_feature_input_decision.md",
        "feature_anchor_decision.md",
        "required_candidate_feature_schema.csv",
        "current_board_feature_join_report.csv",
        "missing_candidate_feature_report.csv",
        "allowed_feature_use_report.csv",
        "null_fenced_feature_policy.md",
        "blocked_input_fields_report.md",
        "candidate_shadow_rank_calculation_contract.md",
        "guardrail_report.md",
        "merge_safety_report.md",
        "next_phase_handoff.md",
        "current_board_candidate_feature_input_schema.csv",
        "current_board_candidate_feature_input_sample.csv",
        "current_board_candidate_feature_input_row_count_report.csv",
        Path(__file__).name,
    ]
    table = "\n".join(
        f"| `{name}` | `{(ARTIFACT_DIR / name).stat().st_size}` | `{sha256(ARTIFACT_DIR / name)}` |"
        for name in names
        if (ARTIFACT_DIR / name).exists()
    )
    return f"""# Artifact Manifest

Artifact directory: `docs/hq/experiments/current_board_candidate_feature_input_gate_v1_20260702/`

Branch: `{context['branch']}`

Base HEAD: `{context['base_head']}`

Decision: `{context['decision']}`

Outside export: `{context['outside_export']}`

| artifact | bytes | sha256 |
|---|---:|---|
{table}

All artifacts are review-only and not production-approved.
"""


def write_outside_readme(context: dict[str, object]) -> None:
    (OUTSIDE_DIR / "README.md").write_text(
        f"""# Current Board Candidate Feature Input Gate V1

Decision: `{context['decision']}`

Generated partial feature input:

`{context['outside_export']}`

Checksum: `{context['outside_export_sha256']}`

Do not calculate candidate shadow ranks from this export until the blocked scoring/games features are admitted.
""",
        encoding="utf-8",
        newline="\n",
    )


def metric(metric_name: str, value: object, notes: str) -> dict[str, str]:
    return {"metric": metric_name, "value": str(value), "notes": notes}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, str]], fields: list[str] | None = None) -> None:
    write_csv_path(ARTIFACT_DIR / name, rows, fields)


def write_csv_path(path: Path, rows: list[dict[str, str]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8", newline="\n")
        return
    fieldnames = fields or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(name: str, text: str) -> None:
    (ARTIFACT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def clean(value: object) -> str:
    return str(value or "").strip()


def format_number(value: object) -> str:
    if value == "":
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return str(int(number))
    return str(round(number, 6))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


if __name__ == "__main__":
    main()
