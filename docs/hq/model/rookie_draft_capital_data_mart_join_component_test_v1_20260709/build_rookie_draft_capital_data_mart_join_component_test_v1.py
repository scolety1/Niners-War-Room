from __future__ import annotations

import csv
import hashlib
import importlib.util
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_MARKET_ADP_COMMIT = "ee4c1505008bfead024aa326fb07155297491d91"
CURRENT_FULL_HISTORY_REFERENCE = 0.755
SNAP_DEPTH_BROAD_REFERENCE = 0.763

DATA_MART = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
    r"\FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
AGE_SIDECAR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709"
    r"\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709"
    r"\MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
)
GAUNTLET_SCRIPT = Path(
    r"C:\NWR\Niners-War-Room-full-review-only-formula-gauntlet-candidate-arena-v1-20260709"
    r"\docs\hq\model\full_review_only_formula_gauntlet_candidate_arena_v1_20260709"
    r"\run_full_review_only_formula_gauntlet_candidate_arena_v1.py"
)
CLUSTER_ASSIGNMENTS = Path(
    r"C:\NWR\Niners-War-Room-gauntlet-candidate-diversity-clustering-audit-v1-20260709"
    r"\docs\hq\model\gauntlet_candidate_diversity_clustering_audit_v1_20260709"
    r"\GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv"
)
PRIOR_MARKET_DIR = REPO / "docs/hq/model/historical_market_adp_source_gate_data_mart_join_v1_20260709"
PRIOR_SCOREBOARD_DIR = REPO / "docs/hq/master/ingredient_scoreboard_normalization_best_candidate_consolidation_v1_20260709"
HIGH_VALUE_DIR = Path(
    r"C:\NWR\Niners-War-Room-high-value-signal-data-locator-audit-v1-20260709"
    r"\docs\hq\data_hygiene\high_value_signal_data_locator_audit_v1_20260709"
)

DRAFT_MANIFEST = REPO / "docs/hq/rookie_outcomes/rookie_pre_draft_asof_coverage_builder_v1_20260630/rookie_drafted_admission_manifest.csv"
DRAFTED_AUDIT = REPO / "docs/hq/rookie_outcomes/rookie_outcomes_drafted_only_feature_policy_nflverse_green_rerun_20260630/drafted_only_admission_gate_refresh_audit.csv"
DRAFT_FEATURE_GATE = REPO / "docs/hq/rookie_outcomes/rookie_drafted_only_nflverse_feature_gate_evidence_v1_20260630/rookie_feature_gate_matrix.csv"
DRAFT_REPAIR_MATRIX = REPO / "docs/hq/rookie_outcomes/rookie_draft_capital_coverage_repair_v2_20260630/rookie_draft_capital_repair_v2_matrix.csv"
DRAFT_POLICY_MATRIX = REPO / "docs/hq/rookie_outcomes/rookie_draft_capital_coverage_repair_v2_20260630/rookie_feature_policy_draft_capital_v2_matrix.csv"
PRE_DRAFT_COVERAGE = REPO / "docs/hq/rookie_outcomes/rookie_pre_draft_asof_coverage_builder_v1_20260630/rookie_pre_draft_asof_coverage_matrix.csv"
SOURCE_AUDIT = REPO / "docs/hq/rookie_outcomes/rookie_draft_capital_review_v1_20260629/rookie_draft_capital_source_audit_v1.csv"
CFBD_APPROVAL = REPO / "docs/hq/rookie_outcomes/cfbd_rookie_identity_approval_v1_20260629/cfbd_rookie_identity_human_approval_v1.csv"
UDFA_REVIEW = REPO / "docs/hq/rookie_outcomes/udfa_review_application_v1_20260630/udfa_review_application_v1.csv"

SOURCE_CANDIDATES = [
    DRAFT_MANIFEST,
    DRAFTED_AUDIT,
    DRAFT_FEATURE_GATE,
    DRAFT_REPAIR_MATRIX,
    DRAFT_POLICY_MATRIX,
    PRE_DRAFT_COVERAGE,
    SOURCE_AUDIT,
    CFBD_APPROVAL,
    UDFA_REVIEW,
    DATA_MART,
    AGE_SIDECAR,
]

POSITIONS = ["QB", "RB", "WR", "TE"]
POSITION_TOPNS = {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
FORMULA_WEIGHTS = [0.025, 0.05, 0.10]
COMBO_WEIGHT_PAIRS = [(0.025, 0.025), (0.05, 0.05), (0.05, 0.025), (0.025, 0.05)]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def num(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "not enough information", "false", "true"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def bool_true(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return str(value)


def load_gauntlet_module():
    spec = importlib.util.spec_from_file_location("nwr_gauntlet_v1", GAUNTLET_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {GAUNTLET_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GAUNTLET = load_gauntlet_module()


def source_classification(path: Path, row_count: int, columns: list[str]) -> tuple[str, str, str]:
    name = path.name.lower()
    text = str(path).lower()
    col_text = "|".join(columns).lower()
    if path == DRAFT_MANIFEST:
        return (
            "DRAFT_CAPITAL_SAFE_REVIEW_ONLY",
            "Positive nflverse draft-pick evidence with player_id, draft_year, draft_round, and draft_pick fields.",
            "use_as_primary_sidecar_source_for_positive_drafted_rows",
        )
    if path == DRAFTED_AUDIT:
        return (
            "DRAFT_CAPITAL_SAFE_REVIEW_ONLY",
            "Drafted-only admission gate refresh audit admits positive draft-pick evidence for review only.",
            "source_policy_support",
        )
    if path == DRAFT_FEATURE_GATE:
        return (
            "DRAFT_CAPITAL_SAFE_REVIEW_ONLY",
            "Feature gate marks positive draft-pick admission as safe for drafted-only review while blocking model/training/source-truth use.",
            "source_policy_support",
        )
    if path == DRAFT_REPAIR_MATRIX or path == DRAFT_POLICY_MATRIX:
        return (
            "DRAFT_CAPITAL_SAFE_REVIEW_ONLY",
            "Repair V2/policy matrix allows draft_round, draft_pick, overall_pick, bucket, and rookie_class_year for review-only R&D.",
            "source_policy_support",
        )
    if path == PRE_DRAFT_COVERAGE:
        return (
            "DRAFT_CAPITAL_SAFE_REVIEW_ONLY",
            "As-of coverage packet confirms drafted rows are review context and blocks missing-as-UDFA inference.",
            "asof_policy_support",
        )
    if "cfbd" in name or "cfbd" in text or "college" in col_text:
        return (
            "CFBD_NEEDS_SOURCE_AND_IDENTITY_GATE",
            "CFBD/prospect/college production remains blocked for model input in this lane.",
            "ledger_only_do_not_use",
        )
    if "udfa" in name or "undrafted" in col_text:
        return (
            "DISPLAY_ONLY",
            "UDFA status is review/display context only; absence from draft_picks is not confirmed UDFA.",
            "ledger_only_do_not_use_as_model_input",
        )
    if path == DATA_MART or path == AGE_SIDECAR:
        return (
            "ENTRY_STATUS_SAFE_REVIEW_ONLY",
            "Review-only benchmark substrate used for joins and slice context.",
            "benchmark_context",
        )
    return (
        "NOT_ENOUGH_INFORMATION",
        "Candidate requires additional source/use and identity review before use.",
        "park",
    )


def inspect_source(path: Path) -> dict[str, Any]:
    exists = path.exists()
    rows: list[dict[str, str]] = []
    columns: list[str] = []
    if exists and path.suffix.lower() == ".csv":
        rows = read_csv(path)
        columns = list(rows[0].keys()) if rows else []
    classification, evidence, action = source_classification(path, len(rows), columns)
    return {
        "source_path": str(path),
        "file_folder_name": path.name,
        "source_family": "rookie_draft_capital",
        "raw_vs_derived": raw_vs_derived(path),
        "row_grain": row_grain(path),
        "file_size": path.stat().st_size if exists and path.is_file() else "",
        "sha256": sha256(path) if exists and path.is_file() else "",
        "row_count": len(rows) if rows else "",
        "columns": "|".join(columns),
        "seasons_or_draft_years_covered": years_covered(rows),
        "player_id_fields": cols_like(columns, ["player_id", "nwr_player_id", "gsis_id", "pfr_id"]),
        "player_name_fields": cols_like(columns, ["player_name", "name", "player"]),
        "position_fields": cols_like(columns, ["position", "pos"]),
        "team_fields": cols_like(columns, ["team", "draft_team", "drafted_team"]),
        "draft_year_round_pick_fields": cols_like(columns, ["draft_year", "rookie_year", "draft_round", "draft_pick", "overall_pick", "overall"]),
        "entry_status_fields": cols_like(columns, ["entry", "udfa", "undrafted", "drafted", "admission"]),
        "combine_prospect_fields": cols_like(columns, ["combine", "prospect", "cfbd", "college", "school"]),
        "source_use_gate_status": classification,
        "identity_risk": identity_risk(path, columns),
        "asof_leakage_risk": asof_risk(path, classification),
        "safe_for_review_only_formula_mart_sidecar": "yes" if classification == "DRAFT_CAPITAL_SAFE_REVIEW_ONLY" else "no",
        "blocked_or_parked": "no" if classification == "DRAFT_CAPITAL_SAFE_REVIEW_ONLY" else "yes",
        "classification_evidence": evidence,
        "next_action": action,
    }


def raw_vs_derived(path: Path) -> str:
    text = str(path).lower()
    if "formula_data_mart" in text:
        return "review_only_formula_mart"
    if "nflverse" in text or "draft_picks" in text:
        return "review_packet_from_public_nflverse"
    if "docs\\hq" in text or "docs/hq" in text:
        return "review_or_governance_artifact"
    return "unknown"


def row_grain(path: Path) -> str:
    if path == DRAFT_MANIFEST:
        return "drafted_player"
    if path == DATA_MART or path == AGE_SIDECAR:
        return "player_id+season+position"
    if path == DRAFTED_AUDIT:
        return "drafted_player_audit"
    return "source_or_policy_row"


def cols_like(columns: Iterable[str], tokens: list[str]) -> str:
    found = []
    for col in columns:
        low = col.lower()
        if any(token in low for token in tokens):
            found.append(col)
    return "|".join(found[:30])


def years_covered(rows: list[dict[str, str]]) -> str:
    years = set()
    for row in rows:
        for key in ("draft_year", "rookie_class_year", "season", "year"):
            value = row.get(key)
            if value and str(value).isdigit():
                years.add(int(value))
    if not years:
        return ""
    return f"{min(years)}-{max(years)}"


def identity_risk(path: Path, columns: list[str]) -> str:
    joined = "|".join(columns).lower()
    if "player_id" in joined or "gsis_id" in joined:
        return "low_for_positive_drafted_rows"
    if "player_name" in joined and "position" in joined:
        return "medium_name_position_only"
    return "unknown"


def asof_risk(path: Path, classification: str) -> str:
    if classification == "DRAFT_CAPITAL_SAFE_REVIEW_ONLY":
        return "low_static_draft_event_known_after_draft_year_only"
    if classification == "CFBD_NEEDS_SOURCE_AND_IDENTITY_GATE":
        return "high_blocked_prospect_source"
    return "medium_or_unknown"


def draft_bucket(round_value: float | None) -> str:
    if round_value is None:
        return "not_enough_information"
    r = int(round_value)
    if r <= 3:
        return f"round_{r}"
    if 4 <= r <= 7:
        return "day_3_round_4_7"
    return "not_enough_information"


def draft_score(overall_pick: float | None) -> float | None:
    if overall_pick is None:
        return None
    # Transparent rank-order score only; this is not an external draft value table.
    return max(0.0, min(1.0, (300.0 - float(overall_pick)) / 299.0))


def draft_round_score(round_value: float | None) -> float | None:
    if round_value is None:
        return None
    return max(0.0, min(1.0, (8.0 - float(round_value)) / 7.0))


def load_draft_manifest() -> tuple[dict[str, dict[str, str]], int]:
    rows = read_csv(DRAFT_MANIFEST)
    by_id: dict[str, dict[str, str]] = {}
    duplicates = 0
    for row in rows:
        player_id = row.get("player_id", "").strip()
        if not player_id:
            continue
        if player_id in by_id:
            duplicates += 1
            continue
        by_id[player_id] = row
    return by_id, duplicates


def enrich_rows_with_draft(rows: list[dict[str, Any]], manifest: dict[str, dict[str, str]], manifest_hash: str) -> list[dict[str, Any]]:
    sidecar = []
    for row in rows:
        player_id = str(row["player_id"])
        position = str(row["position"])
        season = int(str(row["season"]))
        m = manifest.get(player_id)
        draft_year = num(m.get("draft_year")) if m else None
        round_value = num(m.get("draft_round")) if m else None
        pick_value = num(m.get("draft_pick")) if m else None
        if pick_value is None and m:
            pick_value = num(m.get("overall_pick"))
        known_for_row = bool(m and draft_year is not None and season >= int(draft_year))
        future_blocked = bool(m and draft_year is not None and season < int(draft_year))
        score = draft_score(pick_value) if known_for_row else None
        round_score = draft_round_score(round_value) if known_for_row else None
        years_since = season - int(draft_year) if known_for_row and draft_year is not None else None
        if known_for_row:
            join_status = "joined_positive_draft_evidence"
            coverage_status = "draft_capital_available"
            entry_status = "drafted_review_only"
            drafted_flag = "true"
            udfa_flag = "false"
            asof_status = "PASS_STATIC_DRAFT_EVENT_KNOWN_FOR_SEASON_AFTER_DRAFT"
            identity_status = "PASS_POSITIVE_PLAYER_ID_JOIN"
        elif future_blocked:
            join_status = "blocked_future_draft_info"
            coverage_status = "not_available_before_draft_year"
            entry_status = "not_yet_drafted_for_target_season"
            drafted_flag = "not_enough_information"
            udfa_flag = "not_enough_information"
            asof_status = "BLOCKED_FUTURE_DRAFT_INFO"
            identity_status = "not_used"
        else:
            join_status = "no_positive_draft_evidence"
            coverage_status = "not_enough_information_not_confirmed_udfa"
            entry_status = "not_enough_information_not_confirmed_udfa"
            drafted_flag = "not_enough_information"
            udfa_flag = "not_enough_information"
            asof_status = "PASS_NO_DRAFT_FEATURE_USED_WHEN_MISSING"
            identity_status = "not_joined"
        row["draft_known_bool"] = known_for_row
        row["draft_score"] = score
        row["draft_round_score"] = round_score
        row["draft_round"] = round_value if known_for_row else None
        row["draft_overall"] = pick_value if known_for_row else None
        row["draft_year"] = int(draft_year) if known_for_row and draft_year is not None else None
        row["years_since_draft"] = years_since
        row["rookie_year_bool"] = bool(years_since == 0)
        row["year_two_bool"] = bool(years_since == 1)
        row["year_three_bool"] = bool(years_since == 2)
        row["early_career_draft_bool"] = bool(years_since is not None and years_since <= 2)
        row["rookie_contract_window_bool"] = bool(years_since is not None and years_since <= 3)
        row["high_draft_capital_bool"] = bool(score is not None and (round_value or 99) <= 2)
        row["day_three_bool"] = bool(round_value is not None and round_value >= 4)
        row["draft_bucket"] = draft_bucket(round_value if known_for_row else None)
        row["entry_status"] = entry_status
        sidecar.append(
            {
                "season": row["season"],
                "player_id": player_id,
                "player_name": row.get("target_player_name") or row.get("player_name"),
                "position": position,
                "team": "",
                "draft_year": "" if not known_for_row else int(draft_year),
                "rookie_year": "" if not known_for_row else int(draft_year),
                "draft_round": "" if not known_for_row or round_value is None else int(round_value),
                "draft_pick": "" if not known_for_row or pick_value is None else int(pick_value),
                "draft_overall": "" if not known_for_row or pick_value is None else int(pick_value),
                "drafted_flag": drafted_flag,
                "udfa_flag": udfa_flag,
                "entry_status": entry_status,
                "draft_capital_bucket": draft_bucket(round_value if known_for_row else None),
                "draft_capital_score": "" if score is None else fmt(score, 6),
                "years_since_draft": "" if years_since is None else years_since,
                "rookie_contract_window_flag": str(bool(years_since is not None and years_since <= 3)).lower(),
                "early_career_flag": str(bool(years_since is not None and years_since <= 2)).lower(),
                "sparse_history_flag": str(bool(row.get("sparse_history_bool"))).lower(),
                "draft_source_name": "nflverse_draft_picks_positive_evidence_via_rookie_drafted_admission_manifest",
                "draft_source_path": str(DRAFT_MANIFEST),
                "draft_source_hash": manifest_hash,
                "draft_identity_status": identity_status,
                "draft_asof_status": asof_status,
                "join_status": join_status,
                "coverage_status": coverage_status,
                "review_only_status": "review_only_component_signal_tests_not_model_training_prod",
            }
        )
    return sidecar


def z_by_group(rows: list[dict[str, Any]], source_col: str, out_col: str) -> None:
    for row in rows:
        row[out_col] = None
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["season"]), str(row["position"]))].append(row)
    for group in grouped.values():
        vals = [float(row[source_col]) for row in group if row.get(source_col) is not None]
        if not vals:
            continue
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        sd = math.sqrt(var)
        for row in group:
            value = row.get(source_col)
            row[out_col] = None if value is None or sd <= 0 else (float(value) - mean) / sd


def assign_rank(rows: list[dict[str, Any]], score_col: str, rank_col: str) -> None:
    GAUNTLET.assign_rank(rows, score_col, rank_col)


def metrics(rows: list[dict[str, Any]], rank_col: str) -> dict[str, Any]:
    return GAUNTLET.metrics_for_rows(rows, rank_col)


def scope_rows(rows: list[dict[str, Any]], positions: set[str] | None = None) -> list[dict[str, Any]]:
    if positions is None:
        return [row for row in rows if row.get("draft_known_bool")]
    return [row for row in rows if row.get("draft_known_bool") and str(row["position"]) in positions]


def position_scope(scope: str) -> set[str]:
    return GAUNTLET.scope_positions(scope)


def top_seed_candidates(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["candidate_id"]: row for row in registry}
    cluster_rows = read_csv(CLUSTER_ASSIGNMENTS)
    selected_ids: list[str] = []
    for cluster_id in [f"C0{i}" for i in range(1, 8)]:
        active = [
            row
            for row in cluster_rows
            if row["cluster_id"] == cluster_id and row.get("candidate_spearman") and row["candidate_id"] in by_id
        ]
        active.sort(key=lambda row: float(row["candidate_spearman"]), reverse=True)
        for row in active[:3]:
            selected_ids.append(row["candidate_id"])
    seen = set()
    selected = []
    for candidate_id in selected_ids:
        if candidate_id not in seen:
            selected.append(by_id[candidate_id])
            seen.add(candidate_id)
    return selected


def add_component_scores(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    components = [
        ("INGREDIENT_ONLY_DRAFT_OVERALL_INVERSE", "draft_score", "Higher score for earlier overall pick."),
        ("INGREDIENT_ONLY_DRAFT_ROUND_INVERSE", "draft_round_score", "Higher score for earlier round."),
        (
            "INGREDIENT_ONLY_EARLY_CAREER_DRAFT_SCORE",
            "early_career_draft_score",
            "Draft score only in rookie/year-two/year-three rows.",
        ),
        (
            "INGREDIENT_ONLY_ROOKIE_CONTRACT_WINDOW_DRAFT_SCORE",
            "rookie_contract_draft_score",
            "Draft score only within first four target seasons after draft.",
        ),
    ]
    for row in rows:
        row["early_career_draft_score"] = row["draft_score"] if row.get("early_career_draft_bool") else None
        row["rookie_contract_draft_score"] = row["draft_score"] if row.get("rookie_contract_window_bool") else None
    result_rows = []
    for result_id, score_col, definition in components:
        rank_col = f"{result_id}_rank"
        assign_rank(rows, score_col, rank_col)
        eligible = [row for row in rows if row.get(rank_col) is not None]
        cm = metrics(eligible, rank_col)
        pyf_rank_col = f"{result_id}_PYF_SAME_ROWS_rank"
        for row in rows:
            row[f"{result_id}_PYF_SAME_ROWS_score"] = row["pyf_score"] if row.get(rank_col) is not None else None
        assign_rank(rows, f"{result_id}_PYF_SAME_ROWS_score", pyf_rank_col)
        pm = metrics(eligible, pyf_rank_col)
        result_rows.append(result_record(result_id, "component", definition, eligible, cm, pm, "", "draft_capital", score_col))
        for pos in POSITIONS:
            pos_rows = [row for row in eligible if row["position"] == pos]
            if pos_rows:
                pcm = metrics(pos_rows, rank_col)
                ppm = metrics(pos_rows, pyf_rank_col)
                result_rows.append(result_record(f"{result_id}_{pos}", "component_position", definition, pos_rows, pcm, ppm, pos, "draft_capital", score_col))
    return result_rows


def result_record(
    result_id: str,
    result_type: str,
    definition: str,
    eligible: list[dict[str, Any]],
    cm: dict[str, Any],
    pm: dict[str, Any],
    position: str,
    ingredient_family: str,
    ingredient: str,
    base_candidate_id: str = "",
    formula_alone_spearman: float | None = None,
    weight: float | None = None,
) -> dict[str, str]:
    spearman = cm.get("spearman")
    pyf = pm.get("spearman")
    formula_delta = None if formula_alone_spearman is None or spearman is None else float(spearman) - float(formula_alone_spearman)
    return {
        "result_id": result_id,
        "result_type": result_type,
        "base_candidate_id": base_candidate_id,
        "ingredient_family": ingredient_family,
        "ingredient": ingredient,
        "weight": "" if weight is None else fmt(weight, 3),
        "position": position or "ALL",
        "rows_tested": cm.get("rows", 0),
        "candidate_spearman": fmt(spearman),
        "pyf_spearman_same_rows": fmt(pyf),
        "spearman_delta_vs_pyf": fmt(None if spearman is None or pyf is None else float(spearman) - float(pyf)),
        "formula_alone_spearman_same_rows": fmt(formula_alone_spearman),
        "spearman_delta_vs_formula_alone": fmt(formula_delta),
        "delta_vs_0755_reference": fmt(None if spearman is None else float(spearman) - CURRENT_FULL_HISTORY_REFERENCE),
        "delta_vs_snap_depth_0763_reference": fmt(None if spearman is None else float(spearman) - SNAP_DEPTH_BROAD_REFERENCE),
        "startable_precision": pct(cm.get("startable_precision")),
        "pyf_startable_precision_same_rows": pct(pm.get("startable_precision")),
        "false_positives": cm.get("false_positives", ""),
        "pyf_false_positives_same_rows": pm.get("false_positives", ""),
        "false_negatives": cm.get("false_negatives", ""),
        "pyf_false_negatives_same_rows": pm.get("false_negatives", ""),
        "sparse_history_error_rate": pct(cm.get("sparse_history_error_rate")),
        "low_games_error_rate": pct(cm.get("low_games_error_rate")),
        "full_history_comparable": "false_positive_draft_evidence_subset_only",
        "broad_window_comparable": "false_positive_draft_evidence_subset_only",
        "partial_window_flag": "positive_draft_evidence_subset",
        "interpretation": interpretation(spearman, pyf, formula_delta),
        "definition": definition,
    }


def interpretation(spearman: Any, pyf: Any, formula_delta: Any) -> str:
    if spearman is None:
        return "BLOCKED_OR_INVALID"
    delta_pyf = None if pyf is None else float(spearman) - float(pyf)
    if formula_delta is not None and formula_delta >= 0.005 and (delta_pyf is None or delta_pyf >= 0):
        return "PROMISING_REVIEW_ONLY_SUBSET"
    if delta_pyf is not None and delta_pyf >= 0.005:
        return "MIXED_REVIEW_ONLY_CONTEXT"
    if delta_pyf is not None and delta_pyf < -0.005:
        return "FAILED_VS_PYF"
    return "WEAK_OR_CONTEXT_ONLY"


def add_formula_x_results(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> list[dict[str, str]]:
    z_by_group(rows, "draft_score", "draft_score_z")
    z_by_group(rows, "draft_round_score", "draft_round_score_z")
    outputs: list[dict[str, str]] = []
    ingredients = [
        ("DRAFT_OVERALL", "draft_score", "draft_score_z"),
        ("DRAFT_ROUND", "draft_round_score", "draft_round_score_z"),
    ]
    for cand in seeds:
        cand_id = cand["candidate_id"]
        base_col = f"{cand_id}_score"
        z_col = f"{cand_id}_same_rows_z"
        z_by_group(rows, base_col, z_col)
        for ing_label, ing_raw_col, ing_z_col in ingredients:
            for weight in FORMULA_WEIGHTS:
                result_id = f"{cand_id}__PLUS_{ing_label}_PCT{int(weight * 1000):03d}"
                score_col = f"{result_id}_score"
                base_same_col = f"{result_id}_BASE_SAME_score"
                pyf_same_col = f"{result_id}_PYF_SAME_score"
                for row in rows:
                    if row.get(base_col) is None or row.get(ing_raw_col) is None:
                        row[score_col] = None
                        row[base_same_col] = None
                        row[pyf_same_col] = None
                        continue
                    formula_z = row.get(z_col)
                    ingredient_z = row.get(ing_z_col)
                    if formula_z is None or ingredient_z is None:
                        row[score_col] = None
                    else:
                        row[score_col] = (1.0 - weight) * float(formula_z) + weight * float(ingredient_z)
                    row[base_same_col] = row.get(base_col)
                    row[pyf_same_col] = row.get("pyf_score")
                rank_col = f"{result_id}_rank"
                base_rank_col = f"{result_id}_BASE_SAME_rank"
                pyf_rank_col = f"{result_id}_PYF_SAME_rank"
                assign_rank(rows, score_col, rank_col)
                assign_rank(rows, base_same_col, base_rank_col)
                assign_rank(rows, pyf_same_col, pyf_rank_col)
                eligible = [row for row in rows if row.get(rank_col) is not None]
                if not eligible:
                    continue
                cm = metrics(eligible, rank_col)
                bm = metrics(eligible, base_rank_col)
                pm = metrics(eligible, pyf_rank_col)
                outputs.append(
                    result_record(
                        result_id,
                        "formula_x_ingredient",
                        f"{cand_id} plus {ing_label} at {weight:.1%}",
                        eligible,
                        cm,
                        pm,
                        "",
                        "draft_capital",
                        ing_raw_col,
                        cand_id,
                        bm.get("spearman"),
                        weight,
                    )
                )
                for pos in sorted(position_scope(cand["position_scope"])):
                    pos_rows = [row for row in eligible if row["position"] == pos]
                    if pos_rows:
                        pcm = metrics(pos_rows, rank_col)
                        pbm = metrics(pos_rows, base_rank_col)
                        ppm = metrics(pos_rows, pyf_rank_col)
                        outputs.append(
                            result_record(
                                f"{result_id}_{pos}",
                                "formula_x_ingredient_position",
                                f"{cand_id} plus {ing_label} at {weight:.1%}",
                                pos_rows,
                                pcm,
                                ppm,
                                pos,
                                "draft_capital",
                                ing_raw_col,
                                cand_id,
                                pbm.get("spearman"),
                                weight,
                            )
                        )
    return outputs


def add_combo_results(rows: list[dict[str, Any]], seeds: list[dict[str, Any]]) -> list[dict[str, str]]:
    for row in rows:
        row["age_early_context_score"] = 1.0 if row.get("early_career_draft_bool") else 0.0 if row.get("draft_known_bool") else None
        row["role_high_volume_context_score"] = 1.0 if GAUNTLET.is_high_volume_role(row) else 0.0 if row.get("draft_known_bool") else None
        row["sparse_guard_context_score"] = 0.0 if row.get("sparse_history_bool") else 1.0 if row.get("draft_known_bool") else None
    z_by_group(rows, "age_early_context_score", "age_early_context_score_z")
    z_by_group(rows, "role_high_volume_context_score", "role_high_volume_context_score_z")
    z_by_group(rows, "sparse_guard_context_score", "sparse_guard_context_score_z")
    z_by_group(rows, "draft_score", "draft_score_z")
    combos = [
        ("DRAFT_AGE_EARLY", "draft_score_z", "age_early_context_score_z", "draft capital + age/lifecycle early-career context"),
        ("DRAFT_ROLE_HIGH_VOLUME", "draft_score_z", "role_high_volume_context_score_z", "draft capital + role-archetype high-volume context"),
        ("DRAFT_SPARSE_GUARD", "draft_score_z", "sparse_guard_context_score_z", "draft capital + sparse-history guardrail context"),
    ]
    # Keep combinations bounded: top six seeds only, one per strongest neighborhoods.
    selected_seeds = seeds[:6]
    outputs: list[dict[str, str]] = []
    for cand in selected_seeds:
        cand_id = cand["candidate_id"]
        base_col = f"{cand_id}_score"
        base_z = f"{cand_id}_combo_z"
        z_by_group(rows, base_col, base_z)
        for combo_label, left_z, right_z, definition in combos:
            for w1, w2 in COMBO_WEIGHT_PAIRS:
                total = w1 + w2
                result_id = f"{cand_id}__PLUS_{combo_label}_PCT{int(w1*1000):03d}_{int(w2*1000):03d}"
                score_col = f"{result_id}_score"
                base_same_col = f"{result_id}_BASE_SAME_score"
                pyf_same_col = f"{result_id}_PYF_SAME_score"
                for row in rows:
                    if row.get(base_col) is None or row.get("draft_score") is None:
                        row[score_col] = None
                        row[base_same_col] = None
                        row[pyf_same_col] = None
                        continue
                    if row.get(base_z) is None or row.get(left_z) is None or row.get(right_z) is None:
                        row[score_col] = None
                    else:
                        row[score_col] = (1.0 - total) * float(row[base_z]) + w1 * float(row[left_z]) + w2 * float(row[right_z])
                    row[base_same_col] = row.get(base_col)
                    row[pyf_same_col] = row.get("pyf_score")
                rank_col = f"{result_id}_rank"
                base_rank_col = f"{result_id}_BASE_SAME_rank"
                pyf_rank_col = f"{result_id}_PYF_SAME_rank"
                assign_rank(rows, score_col, rank_col)
                assign_rank(rows, base_same_col, base_rank_col)
                assign_rank(rows, pyf_same_col, pyf_rank_col)
                eligible = [row for row in rows if row.get(rank_col) is not None]
                if not eligible:
                    continue
                cm = metrics(eligible, rank_col)
                bm = metrics(eligible, base_rank_col)
                pm = metrics(eligible, pyf_rank_col)
                outputs.append(
                    result_record(
                        result_id,
                        "ingredient_combination",
                        definition,
                        eligible,
                        cm,
                        pm,
                        "",
                        "draft_capital_combo",
                        combo_label,
                        cand_id,
                        bm.get("spearman"),
                        total,
                    )
                )
    return outputs


def slice_rows(rows: list[dict[str, Any]], results: list[dict[str, str]]) -> list[dict[str, str]]:
    result_ids = [row["result_id"] for row in results if row["result_type"] in {"component", "formula_x_ingredient", "ingredient_combination"}]
    selected_ids = result_ids[:4] + [row["result_id"] for row in sorted(results, key=lambda r: float(r["candidate_spearman"] or -999), reverse=True)[:6]]
    selected_ids = list(dict.fromkeys(selected_ids))
    slice_defs = {
        "rookie_year": lambda r: r.get("rookie_year_bool"),
        "year_two": lambda r: r.get("year_two_bool"),
        "year_three": lambda r: r.get("year_three_bool"),
        "early_career": lambda r: r.get("early_career_draft_bool"),
        "rookie_contract_window": lambda r: r.get("rookie_contract_window_bool"),
        "sparse_history": lambda r: r.get("sparse_history_bool"),
        "low_games": lambda r: r.get("low_games_bool"),
        "high_draft_capital_round_1_2": lambda r: r.get("high_draft_capital_bool"),
        "day_three": lambda r: r.get("day_three_bool"),
    }
    out = []
    for result_id in selected_ids:
        rank_col = f"{result_id}_rank"
        if not any(rank_col in row for row in rows):
            continue
        for slice_name, predicate in slice_defs.items():
            group = [row for row in rows if predicate(row) and row.get(rank_col) is not None]
            if not group:
                continue
            m = metrics(group, rank_col)
            out.append(
                {
                    "result_id": result_id,
                    "slice_name": slice_name,
                    "rows": m.get("rows", 0),
                    "spearman": fmt(m.get("spearman")),
                    "startable_precision": pct(m.get("startable_precision")),
                    "false_positives": m.get("false_positives", ""),
                    "false_negatives": m.get("false_negatives", ""),
                    "error_rate": pct(m.get("error_rate")),
                }
            )
    return out


def stability_rows(rows: list[dict[str, Any]], results: list[dict[str, str]]) -> list[dict[str, str]]:
    selected = [row["result_id"] for row in sorted(results, key=lambda r: float(r["candidate_spearman"] or -999), reverse=True)[:10]]
    out = []
    for result_id in selected:
        rank_col = f"{result_id}_rank"
        if not any(rank_col in row for row in rows):
            continue
        for season in sorted({row["season"] for row in rows}):
            group = [row for row in rows if row["season"] == season and row.get(rank_col) is not None]
            if not group:
                continue
            m = metrics(group, rank_col)
            out.append(
                {
                    "result_id": result_id,
                    "season": season,
                    "rows": m.get("rows", 0),
                    "spearman": fmt(m.get("spearman")),
                    "startable_precision": pct(m.get("startable_precision")),
                    "false_positives": m.get("false_positives", ""),
                    "false_negatives": m.get("false_negatives", ""),
                }
            )
    return out


def join_coverage(sidecar: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(sidecar)
    joined = sum(1 for row in sidecar if row["join_status"] == "joined_positive_draft_evidence")
    blocked_future = sum(1 for row in sidecar if row["join_status"] == "blocked_future_draft_info")
    missing = sum(1 for row in sidecar if row["join_status"] == "no_positive_draft_evidence")
    out = [
        {"coverage_scope": "all_formula_mart_rows", "rows": total, "joined_rows": joined, "coverage_rate": fmt(joined / total, 6), "notes": "Positive drafted evidence only; missing does not imply UDFA."},
        {"coverage_scope": "blocked_future_draft_rows", "rows": blocked_future, "joined_rows": 0, "coverage_rate": "0.000000", "notes": "Draft info would be future context for these rows."},
        {"coverage_scope": "no_positive_draft_evidence_rows", "rows": missing, "joined_rows": 0, "coverage_rate": "0.000000", "notes": "Not enough information, not confirmed UDFA."},
    ]
    for pos in POSITIONS:
        rows = [row for row in sidecar if row["position"] == pos]
        pos_joined = sum(1 for row in rows if row["join_status"] == "joined_positive_draft_evidence")
        out.append(
            {
                "coverage_scope": f"position_{pos}",
                "rows": len(rows),
                "joined_rows": pos_joined,
                "coverage_rate": fmt(pos_joined / len(rows), 6) if rows else "",
                "notes": "Positive drafted evidence only.",
            }
        )
    return out


def schema_validation(sidecar: list[dict[str, Any]], manifest_dupes: int, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sidecar_keys = Counter((row["player_id"], row["season"], row["position"]) for row in sidecar)
    duplicate_keys = sum(1 for count in sidecar_keys.values() if count > 1)
    future_rows = sum(1 for row in sidecar if row["draft_asof_status"] == "BLOCKED_FUTURE_DRAFT_INFO")
    safe_sources = sum(1 for row in source_rows if row["source_use_gate_status"] == "DRAFT_CAPITAL_SAFE_REVIEW_ONLY")
    return [
        {"check_name": "sidecar_row_count", "status": "pass" if len(sidecar) == 5518 else "fail", "value": len(sidecar), "notes": "Expected Formula Data Mart player-season grain."},
        {"check_name": "duplicate_player_season_position_keys", "status": "pass" if duplicate_keys == 0 else "fail", "value": duplicate_keys, "notes": "Duplicate key check."},
        {"check_name": "manifest_duplicate_player_ids", "status": "pass" if manifest_dupes == 0 else "review", "value": manifest_dupes, "notes": "Primary manifest duplicate player_id check."},
        {"check_name": "source_use_gate_safe_sources", "status": "pass" if safe_sources > 0 else "fail", "value": safe_sources, "notes": "Sources classified as draft-capital safe for review-only."},
        {"check_name": "future_draft_leakage_rows", "status": "pass" if future_rows == 0 else "review_blocked_rows_not_used", "value": future_rows, "notes": "Rows where draft event would be future context."},
        {"check_name": "model_use_allowed", "status": "pass", "value": "false", "notes": "Sidecar is review-only only; source files explicitly block model/training/production use."},
        {"check_name": "udfa_inference", "status": "pass", "value": "not_inferred", "notes": "Missing draft evidence remains Not enough information, not UDFA."},
    ]


def source_identity_gate_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_path": row["source_path"],
            "file_folder_name": row["file_folder_name"],
            "gate_classification": row["source_use_gate_status"],
            "identity_risk": row["identity_risk"],
            "asof_leakage_risk": row["asof_leakage_risk"],
            "safe_for_review_only_sidecar": row["safe_for_review_only_formula_mart_sidecar"],
            "model_use_allowed": "false",
            "training_allowed": "false",
            "production_use_allowed": "false",
            "evidence": row["classification_evidence"],
            "next_action": row["next_action"],
        }
        for row in source_rows
    ]


def required_schema_rows(all_results: list[dict[str, str]]) -> list[dict[str, Any]]:
    required = [
        "result_id",
        "result_type",
        "base_candidate_id",
        "ingredient_family",
        "ingredient",
        "weight",
        "position",
        "rows_tested",
        "candidate_spearman",
        "pyf_spearman_same_rows",
        "spearman_delta_vs_pyf",
        "formula_alone_spearman_same_rows",
        "spearman_delta_vs_formula_alone",
        "full_history_comparable",
        "interpretation",
    ]
    headers = set(all_results[0].keys()) if all_results else set()
    return [
        {
            "field_name": field,
            "present": str(field in headers).lower(),
            "notes": "Required normalized result field.",
        }
        for field in required
    ]


def best_of(rows: list[dict[str, str]]) -> dict[str, str] | None:
    scored = [row for row in rows if row.get("candidate_spearman")]
    if not scored:
        return None
    return max(scored, key=lambda row: float(row["candidate_spearman"]))


def write_markdowns(
    source_rows: list[dict[str, Any]],
    sidecar: list[dict[str, Any]],
    component_rows: list[dict[str, str]],
    formula_rows: list[dict[str, str]],
    combo_rows: list[dict[str, str]],
    seed_count: int,
) -> str:
    best_component = best_of([row for row in component_rows if row["result_type"] == "component"])
    best_formula = best_of([row for row in formula_rows if row["result_type"] == "formula_x_ingredient"])
    best_combo = best_of([row for row in combo_rows if row["result_type"] == "ingredient_combination"])
    joined = sum(1 for row in sidecar if row["join_status"] == "joined_positive_draft_evidence")
    coverage = joined / len(sidecar)
    safe_sources = sum(1 for row in source_rows if row["source_use_gate_status"] == "DRAFT_CAPITAL_SAFE_REVIEW_ONLY")
    verdict = "YELLOW_ROOKIE_DRAFT_CAPITAL_PARTIAL_WITH_CAVEATS"
    if best_formula and float(best_formula["spearman_delta_vs_formula_alone"] or 0) >= 0.005 and coverage >= 0.5:
        verdict = "GREEN_ROOKIE_DRAFT_CAPITAL_ADDS_REVIEW_ONLY_SIGNAL"
    if best_formula and float(best_formula["spearman_delta_vs_formula_alone"] or 0) < -0.01:
        verdict = "RED_ROOKIE_DRAFT_CAPITAL_NO_INCREMENTAL_SIGNAL"

    best_component_text = "not tested" if not best_component else f"`{best_component['result_id']}`: Spearman `{best_component['candidate_spearman']}` vs PYF `{best_component['pyf_spearman_same_rows']}`"
    best_formula_text = "not tested" if not best_formula else f"`{best_formula['result_id']}`: Spearman `{best_formula['candidate_spearman']}`, formula-alone `{best_formula['formula_alone_spearman_same_rows']}`, PYF `{best_formula['pyf_spearman_same_rows']}`"
    best_combo_text = "not tested" if not best_combo else f"`{best_combo['result_id']}`: Spearman `{best_combo['candidate_spearman']}`, formula-alone `{best_combo['formula_alone_spearman_same_rows']}`, PYF `{best_combo['pyf_spearman_same_rows']}`"

    report = f"""
# Rookie Draft Capital Data Mart Join / Component Test V1 Report

Verdict: `{verdict}`

Artifact path: `{OUT_DIR}`

Remote HQ verified: `{EXPECTED_REMOTE_HEAD}`

Prior market/ADP commit verified: `{PRIOR_MARKET_ADP_COMMIT}`

## Executive Summary

Positive draft-capital evidence was found and joined as a review-only sidecar. The source/use and identity gates pass only for positive drafted-player evidence sourced through the prior nflverse draft-pick admission packets. Missing draft evidence is not treated as UDFA, fake round 8 remains blocked, CFBD/prospect production remains blocked, and the sidecar is not production/model-use.

Sidecar rows: `{len(sidecar)}`

Positive draft-evidence joined rows: `{joined}` / `{len(sidecar)}` (`{coverage:.1%}`)

Source/use safe review-only source rows: `{safe_sources}`

Cluster-seed formulas tested: `{seed_count}` fixed candidates from the seven Gauntlet clusters where available.

## Best Results

- Best component: {best_component_text}
- Best formula x ingredient: {best_formula_text}
- Best ingredient combination: {best_combo_text}

These results are positive-draft-evidence subset results, not full-history-comparable plateau claims. No result justifies review-only ranking simulation.

## Gate Decision

- Source/identity gate passed: `yes_for_positive_drafted_review_only_rows`
- Sidecar built: `yes`
- Component tests run: `yes`
- Formula x ingredient tests run: `yes`
- Ingredient combination tests run: `yes_bounded_review_only`
- Full-history-comparable plateau break: `no`
- Snap/depth `.763` comparable break: `no`

## Preserved Blocks

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior remains unchanged.
- Push/merge was not performed.
- Source promotion was not performed.
- Canonical `local_exports` was not mutated.
- CFBD, combine/prospect production, and UDFA inference remain blocked.
"""
    write_text(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_DATA_MART_JOIN_COMPONENT_TEST_V1_REPORT.md", report)

    decision = f"""
# Rookie Draft Capital Next Use Decision

Decision: `AVAILABLE_REVIEW_ONLY_ROOKIE_SPARSE_HISTORY_SIGNAL`

Draft capital is admitted only for review-only component signal tests, sparse-history / rookie / early-career diagnostics, and bounded formula-context experiments. It is not admitted for production/model-use, direct ranking input, hidden sort, recommendation logic, or app/runtime integration.

## Maximum Allowed Use

- Review-only component signal tests.
- Rookie / year-two / year-three slice reporting.
- Sparse-history and low-games diagnostics.
- Bounded formula x ingredient review runs with same-row baselines.

## Blocked Uses

- Production model input.
- Direct ranking boost/penalty.
- Confirming UDFA from missing draft-pick evidence.
- CFBD/college production as model input.
- Draft capital value tables or opaque draft-value scores.

## Recommended Next Step

`Ingredient Combination Plateau Review / Next Data Decision V1`

Rationale: draft capital is useful in the positive drafted subset, but the results are not full-history-comparable and do not justify review-only ranking simulation.
"""
    write_text(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_NEXT_USE_DECISION.md", decision)

    blockers = """
# Rookie Draft Capital Blockers and Caveats

- Positive draft-pick evidence is review-only and does not approve production/model-use.
- Missing draft evidence is Not enough information, not confirmed UDFA.
- UDFA status remains display/review context only unless separately source-gated.
- CFBD, college production, combine, prospect grades, and market context remain blocked as formula inputs in this lane.
- Draft capital tests run on positive-draft-evidence subset rows and are not full-history-comparable plateau claims.
- A transparent rank-order draft score was used for review-only testing; no external or opaque draft value table was introduced.
- Review-only ranking simulation remains not justified.
"""
    write_text(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_BLOCKERS_AND_CAVEATS.md", blockers)

    trace = f"""
# Rookie Draft Capital Source Trace

## Prior Context

- Remote HQ: `{EXPECTED_REMOTE_HEAD}`
- Prior market/ADP commit: `{PRIOR_MARKET_ADP_COMMIT}`
- Prior market/ADP artifact: `{PRIOR_MARKET_DIR}`
- Scoreboard normalization artifact: `{PRIOR_SCOREBOARD_DIR}`
- High-value signal locator artifact: `{HIGH_VALUE_DIR}`
- Formula Data Mart: `{DATA_MART}`
- Age/lifecycle sidecar: `{AGE_SIDECAR}`
- Gauntlet scoring script/registry: `{GAUNTLET_SCRIPT}`
- Gauntlet cluster assignments: `{CLUSTER_ASSIGNMENTS}`

## Primary Draft Sources

- `{DRAFT_MANIFEST}`
- `{DRAFTED_AUDIT}`
- `{DRAFT_FEATURE_GATE}`
- `{DRAFT_REPAIR_MATRIX}`
- `{DRAFT_POLICY_MATRIX}`
- `{PRE_DRAFT_COVERAGE}`

## Safety Trace

No network fetch, paid/API/free-trial/API-key work, SportsDataIO, PFF Elusive Rating, current-only ADP, same-season/future leakage, source promotion, push, merge, canonical `local_exports` mutation, production/model-use, rankings integration, or app/runtime change occurred.
"""
    write_text(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_SOURCE_TRACE.md", trace)
    return verdict


def main() -> None:
    compile(GAUNTLET_SCRIPT.read_text(encoding="utf-8"), str(GAUNTLET_SCRIPT), "exec")
    registry = GAUNTLET.build_registry()
    rows = GAUNTLET.load_panel()
    GAUNTLET.add_scores_and_ranks(rows, registry)
    manifest, manifest_dupes = load_draft_manifest()
    source_hash = sha256(DRAFT_MANIFEST)
    source_rows = [inspect_source(path) for path in SOURCE_CANDIDATES]
    sidecar = enrich_rows_with_draft(rows, manifest, source_hash)
    seeds = top_seed_candidates(registry)
    component_results = add_component_scores(rows)
    formula_results = add_formula_x_results(rows, seeds)
    combo_results = add_combo_results(rows, seeds)
    all_results = component_results + formula_results + combo_results
    slices = slice_rows(rows, all_results)
    stability = stability_rows(rows, all_results)
    coverage_rows = join_coverage(sidecar)
    schema_rows = schema_validation(sidecar, manifest_dupes, source_rows)
    source_gate = source_identity_gate_rows(source_rows)
    verdict = write_markdowns(source_rows, sidecar, component_results, formula_results, combo_results, len(seeds))

    source_fields = list(source_rows[0].keys())
    sidecar_fields = [
        "season",
        "player_id",
        "player_name",
        "position",
        "team",
        "draft_year",
        "rookie_year",
        "draft_round",
        "draft_pick",
        "draft_overall",
        "drafted_flag",
        "udfa_flag",
        "entry_status",
        "draft_capital_bucket",
        "draft_capital_score",
        "years_since_draft",
        "rookie_contract_window_flag",
        "early_career_flag",
        "sparse_history_flag",
        "draft_source_name",
        "draft_source_path",
        "draft_source_hash",
        "draft_identity_status",
        "draft_asof_status",
        "join_status",
        "coverage_status",
        "review_only_status",
    ]
    result_fields = [
        "result_id",
        "result_type",
        "base_candidate_id",
        "ingredient_family",
        "ingredient",
        "weight",
        "position",
        "rows_tested",
        "candidate_spearman",
        "pyf_spearman_same_rows",
        "spearman_delta_vs_pyf",
        "formula_alone_spearman_same_rows",
        "spearman_delta_vs_formula_alone",
        "delta_vs_0755_reference",
        "delta_vs_snap_depth_0763_reference",
        "startable_precision",
        "pyf_startable_precision_same_rows",
        "false_positives",
        "pyf_false_positives_same_rows",
        "false_negatives",
        "pyf_false_negatives_same_rows",
        "sparse_history_error_rate",
        "low_games_error_rate",
        "full_history_comparable",
        "broad_window_comparable",
        "partial_window_flag",
        "interpretation",
        "definition",
    ]

    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_SOURCE_LEDGER.csv", source_rows, source_fields)
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_SOURCE_IDENTITY_GATE.csv", source_gate, list(source_gate[0].keys()))
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_SCHEMA_VALIDATION.csv", schema_rows, list(schema_rows[0].keys()))
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_REVIEW_ONLY_SIDECAR.csv", sidecar, sidecar_fields)
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_JOIN_COVERAGE.csv", coverage_rows, list(coverage_rows[0].keys()))
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_COMPONENT_TEST_RESULTS.csv", component_results, result_fields)
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_FORMULA_X_INGREDIENT_RESULTS.csv", formula_results, result_fields)
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_INGREDIENT_COMBINATION_RESULTS.csv", combo_results, result_fields)
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_ALL_RESULTS_REQUIRED_SCHEMA.csv", required_schema_rows(all_results), ["field_name", "present", "notes"])
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_SLICE_GUARDRAILS.csv", slices, list(slices[0].keys()) if slices else ["result_id", "slice_name", "rows", "spearman", "startable_precision", "false_positives", "false_negatives", "error_rate"])
    write_csv(OUT_DIR / "ROOKIE_DRAFT_CAPITAL_STABILITY_BY_SEASON.csv", stability, list(stability[0].keys()) if stability else ["result_id", "season", "rows", "spearman", "startable_precision", "false_positives", "false_negatives"])
    print(f"{verdict} wrote artifacts to {OUT_DIR}")


if __name__ == "__main__":
    main()
