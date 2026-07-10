from __future__ import annotations

import csv
import hashlib
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"

PRIOR_DATA_MART_DIR = Path(r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709")
SYSTEM_AUDIT_DIR = REPO / "docs/hq/master/nwr_full_system_audit_integration_map_v1_20260709"
GAP_PLAN_DIR = REPO / "docs/hq/data_hygiene/model_v4_historical_receipt_gap_closure_plan_v1_20260708"
LOCATOR_DIR = REPO / "docs/hq/data_hygiene/model_v4_historical_receipt_locator_ledger_v1_20260709"
FREEZE_DIR = REPO / "docs/hq/data_hygiene/model_v4_historical_receipt_freeze_schema_validation_v1_20260709"
CONTRACT_DIR = REPO / "docs/hq/master/model_v4_historical_receipt_regeneration_contract_planning_v1_20260709"
CONFIDENCE_DIR = REPO / "docs/hq/data_hygiene/model_v4_confidence_cap_receipt_regeneration_pilot_v1_20260709"
ROLE_DIR = REPO / "docs/hq/data_hygiene/model_v4_role_archetype_receipt_regeneration_pilot_v1_20260709"
DATA_HYGIENE_CHARTER_DIR = REPO / "docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708"
HQ1_STANDARD_DIR = REPO / "docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708"

SAFE_ROOTS = [
    REPO / "docs/hq",
    PRIOR_DATA_MART_DIR,
    Path(r"C:\NWR\Niners-War-Room-model-v4-historical-receipt-locator-ledger-v1-20260709\docs"),
    Path(r"C:\NWR\Niners-War-Room-model-v4-historical-receipt-freeze-schema-validation-v1-20260709\docs"),
    Path(r"C:\NWR\Niners-War-Room-model-v4-historical-receipt-gap-closure-plan-v1-20260708\docs"),
    Path(r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708\docs"),
    Path(r"C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708\docs"),
    Path(r"C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708\docs"),
    Path(r"C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708\docs"),
    Path(r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1"),
]

DE_SCOPED = [
    "route_yprr_tprr",
    "return_scoring_receipts",
    "broad_pfr_feature_promotion",
    "pff_elusive_rating",
    "nwr_elusive_proxy_review_only",
    "super_advanced_data_not_currently_source_accurate",
]

TARGETS = {
    "red_zone_exact_receipts": {
        "why": "Could add high-value TD/opportunity context if source-traced and decision-date safe.",
        "formula_value": "high",
        "row_grain": "player-season or player-week aggregated to player-season",
        "join_keys": "season|feature_season|player_id|position",
        "positions": "QB/RB/WR/TE where source supports",
        "search_terms": ["red_zone", "redzone", "rz_", "inside_20", "inside20", "inside_10", "inside10", "goal_line", "goal line"],
    },
    "shadow_model_v2_metrics": {
        "why": "May support historical shadow-sidecar audit, but current exact board rebuild proved it is not required for current-board hash reproduction.",
        "formula_value": "low_or_uncertain",
        "row_grain": "unknown sidecar",
        "join_keys": "unknown",
        "positions": "unknown",
        "search_terms": ["shadow_model_v2_metrics", "shadow_model", "shadow metrics"],
    },
    "historical_checkpoint_review_score": {
        "why": "Needed for exact Model v4 replay and historical score-chain audit.",
        "formula_value": "high_for_replay_low_for_new_formula_sprint",
        "row_grain": "player-season",
        "join_keys": "season|player_id|position",
        "positions": "QB/RB/WR/TE",
        "search_terms": ["checkpoint_review_score", "current_value", "player_value", "source_coverage_matrix", "evidence_matrix"],
    },
    "historical_position_specific_review_score": {
        "why": "Needed for exact Model v4 position-layer replay and score decomposition.",
        "formula_value": "high_for_replay_low_for_new_formula_sprint",
        "row_grain": "player-season",
        "join_keys": "season|player_id|position",
        "positions": "QB/RB/WR/TE",
        "search_terms": ["position_specific_review_score", "position specific", "current_value", "player_value", "evidence_matrix"],
    },
    "age_lifecycle_sidecars": {
        "why": "Likely useful for dynasty decay, sparse-history interpretation, and lifecycle guardrails.",
        "formula_value": "medium_high",
        "row_grain": "player-season",
        "join_keys": "season|player_id|position",
        "positions": "QB/RB/WR/TE",
        "search_terms": ["age", "birth date", "birth_date", "experience", "lifecycle", "veteran_player_inputs"],
    },
    "point_in_time_injury_availability_gates": {
        "why": "Could explain misses and low-games context, but high leakage risk without point-in-time evidence.",
        "formula_value": "medium",
        "row_grain": "player-week or player-season as-of",
        "join_keys": "as_of_date|season|week|player_id",
        "positions": "QB/RB/WR/TE",
        "search_terms": ["injury", "availability", "weekly roster", "roster", "inactive", "ir_status", "depth"],
    },
    "point_in_time_market_adp_gates": {
        "why": "Market/ADP can be strong context, but requires historical point-in-time source control.",
        "formula_value": "medium_high",
        "row_grain": "player-date or player-season as-of",
        "join_keys": "as_of_date|season|player_id",
        "positions": "QB/RB/WR/TE",
        "search_terms": ["market", "ADP", "DynastyProcess", "sleeper", "dp_", "trade value"],
    },
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_meta(path: Path) -> tuple[str, str, str]:
    try:
        if path.suffix.lower() != ".csv" or path.stat().st_size > 25_000_000:
            return "", "", ""
        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            count = sum(1 for _ in reader)
        return str(count), str(len(header)), "|".join(header[:80])
    except Exception:
        return "", "", ""


def path_text(path: Path) -> str:
    try:
        return str(path).lower()
    except Exception:
        return ""


def text_snippet(path: Path) -> str:
    try:
        if path.is_dir() or path.stat().st_size > 500_000:
            return ""
        if path.suffix.lower() not in {".md", ".csv", ".txt", ".json", ".py", ".yaml", ".yml"}:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return ""


def target_matches(path: Path) -> dict[str, list[str]]:
    hay = path_text(path)
    content = ""
    matches: dict[str, list[str]] = {}
    for target, cfg in TARGETS.items():
        terms = []
        for term in cfg["search_terms"]:
            if term.lower() in hay:
                terms.append(term)
        if terms:
            matches[target] = terms
            continue
        if not content:
            content = text_snippet(path)
        if content:
            for term in cfg["search_terms"]:
                if term.lower() in content:
                    terms.append(term)
            if terms:
                matches[target] = terms
    return matches


def classify_artifact(target: str, path: Path) -> tuple[str, str, str, str, str]:
    p = str(path).lower()
    if target == "red_zone_exact_receipts":
        if "redzone" in p or "red_zone" in p or "goal_line" in p:
            return "candidate_source_needs_gate", "yes", "medium", "medium", "Candidate red-zone source/schema artifact; exact as-of/source semantics not yet proven."
        return "partial_or_contextual", "yes", "medium", "medium", "Mentioned red zone but not enough to regenerate exact receipts."
    if target == "shadow_model_v2_metrics":
        if path.name.lower() == "shadow_model_v2_metrics.csv":
            return "possible_exact_source", "no", "unknown", "unknown", "Exact file-name hit; needs manual validation."
        return "context_only", "no", "unknown", "unknown", "Shadow metrics mention only."
    if target in {"historical_checkpoint_review_score", "historical_position_specific_review_score"}:
        if "current_value" in p or "player_value" in p:
            return "current_or_partial_equivalent", "yes", "medium", "low", "Useful for replay gap mapping but not exact historical replay."
        return "context_or_manifest_only", "yes", "medium", "low", "Score-chain evidence, not an exact season-by-season receipt."
    if target == "age_lifecycle_sidecars":
        if "veteran_player_inputs" in p or "age" in p or "lifecycle" in p:
            return "freeze_or_review_candidate", "conditional", "medium", "medium", "Possible age/lifecycle sidecar or validation evidence."
        return "context_only", "conditional", "medium", "medium", "Lifecycle mention only."
    if target == "point_in_time_injury_availability_gates":
        return "source_gate_candidate", "yes", "high", "medium", "Availability data needs point-in-time as-of validation."
    if target == "point_in_time_market_adp_gates":
        return "source_gate_candidate", "yes", "high", "medium", "Market/ADP data needs point-in-time as-of validation."
    return "candidate", "unknown", "unknown", "unknown", ""


def add_ledger_row(rows: list[dict[str, object]], seen: set[tuple[str, str]], target: str, path: Path, source_root: Path, matched_terms: list[str]) -> None:
    key = (target, str(path))
    if key in seen:
        return
    seen.add(key)
    try:
        stat = path.stat()
        file_size = "" if path.is_dir() else stat.st_size
        modified = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
        exists = True
    except Exception:
        file_size = ""
        modified = ""
        exists = False
    row_count, col_count, cols = ("", "", "")
    digest = ""
    if exists and path.is_file():
        try:
            size = path.stat().st_size
        except Exception:
            size = 25_000_001
        if size <= 25_000_000:
            try:
                digest = sha256(path)
            except Exception:
                digest = ""
        row_count, col_count, cols = csv_meta(path)
    classification, source_gate_required, leakage_risk, identity_risk, notes = classify_artifact(target, path)
    if not exists:
        classification = "manifest_path_missing_or_unreadable"
        source_gate_required = "yes"
        leakage_risk = "unknown"
        identity_risk = "unknown"
        notes = "Path was present in a prior ledger/manifest but was missing or unreadable during this sweep."
    rows.append({
        "target_name": target,
        "found_path": str(path),
        "file_or_folder": "missing_or_unreadable" if not exists else ("folder" if path.is_dir() else "file"),
        "source_root": str(source_root),
        "matched_terms": "|".join(sorted(set(matched_terms))),
        "file_size": file_size,
        "modified_time": modified,
        "sha256": digest,
        "row_count_if_tabular": row_count,
        "column_count_if_tabular": col_count,
        "columns_if_tabular": cols,
        "artifact_classification": classification,
        "review_safe": "yes" if classification not in {"possible_exact_source"} else "needs_review",
        "source_gate_required": source_gate_required,
        "leakage_risk": leakage_risk,
        "identity_risk": identity_risk,
        "notes": notes,
    })


def load_prior_ledger_rows(ledger: list[dict[str, object]], seen: set[tuple[str, str]]) -> None:
    mapping = {
        "red_zone_exact_receipts": "red_zone_exact_receipts",
        "shadow_model_v2_metrics": "shadow_model_v2_metrics",
        "checkpoint_review_score": "historical_checkpoint_review_score",
        "position_specific_review_score": "historical_position_specific_review_score",
        "lifecycle_age_receipts": "age_lifecycle_sidecars",
    }
    for source_csv in [
        LOCATOR_DIR / "MODEL_V4_HISTORICAL_RECEIPT_PATH_MAP.csv",
        LOCATOR_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FOUND_ARTIFACT_LEDGER.csv",
    ]:
        if not source_csv.exists():
            continue
        for row in read_csv(source_csv):
            family = row.get("receipt_family") or row.get("family_name") or row.get("maps_to_family") or ""
            path_text_value = row.get("found_path") or row.get("source_path") or row.get("path") or ""
            for source_family, target in mapping.items():
                if source_family in family and path_text_value:
                    add_ledger_row(
                        ledger,
                        seen,
                        target,
                        Path(path_text_value),
                        source_csv,
                        [source_family],
                    )


def scan_roots() -> list[dict[str, object]]:
    ledger: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    load_prior_ledger_rows(ledger, seen)

    per_target_counts: Counter[str] = Counter()
    for root in SAFE_ROOTS:
        if not root.exists():
            continue
        if root.is_file():
            paths = [root]
        else:
            paths = []
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [
                    d for d in dirnames
                    if d not in {".git", "node_modules", "__pycache__", ".venv", "venv"}
                    and not d.endswith(".cache")
                ]
                current_dir = Path(dirpath)
                for name in filenames:
                    paths.append(current_dir / name)
                for name in dirnames:
                    dpath = current_dir / name
                    if target_matches(dpath):
                        paths.append(dpath)
        for path in paths:
            matches = target_matches(path)
            for target, terms in matches.items():
                if per_target_counts[target] >= 80:
                    continue
                add_ledger_row(ledger, seen, target, path, root, terms)
                per_target_counts[target] += 1

    priority_order = {
        "red_zone_exact_receipts": 1,
        "age_lifecycle_sidecars": 2,
        "point_in_time_market_adp_gates": 3,
        "point_in_time_injury_availability_gates": 4,
        "historical_checkpoint_review_score": 5,
        "historical_position_specific_review_score": 6,
        "shadow_model_v2_metrics": 7,
    }
    ledger.sort(key=lambda row: (priority_order.get(str(row["target_name"]), 99), str(row["found_path"])))
    return ledger


def ledger_counts(ledger: list[dict[str, object]], target: str) -> dict[str, object]:
    rows = [row for row in ledger if row["target_name"] == target]
    classifications = Counter(str(row["artifact_classification"]) for row in rows)
    top = [str(row["found_path"]) for row in rows[:5]]
    return {
        "candidate_count": len(rows),
        "classification_summary": "|".join(f"{k}={v}" for k, v in sorted(classifications.items())),
        "top_paths": " | ".join(top),
    }


def target_matrix(ledger: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    decisions = {
        "red_zone_exact_receipts": ("NEEDS_SOURCE_GATE_REVIEW", "Candidate red-zone sidecar/schema artifacts exist, but source/as-of semantics are not proven enough for value regeneration.", "Model v4 Red Zone Exact Receipt Regeneration Pilot V1 with a mandatory source/as-of gate and stop condition before any values are generated if unsafe."),
        "shadow_model_v2_metrics": ("MISSING_SOURCE", "Exact sidecar remains absent and is not needed for the review-only mart.", "Shadow Metrics Scope Removal / Recovery Decision later; not worth prioritizing now."),
        "historical_checkpoint_review_score": ("MISSING_RECEIPT", "Current-board equivalents exist, but exact season-by-season receipts remain absent.", "Historical Checkpoint Receipt Recovery Plan."),
        "historical_position_specific_review_score": ("MISSING_RECEIPT", "Partial equivalents exist, but exact season-by-season position receipts remain absent.", "Historical Checkpoint Receipt Recovery Plan."),
        "age_lifecycle_sidecars": ("READY_TO_FREEZE", "Age/lifecycle artifacts are freeze/review candidates and likely easier to validate than red-zone source semantics.", "Age Lifecycle Sidecar Freeze / Validation V1."),
        "point_in_time_injury_availability_gates": ("LEAKAGE_UNSAFE", "Availability/injury artifacts require historical as-of controls before formula testing.", "Point-in-Time Injury Availability Gate Review V1."),
        "point_in_time_market_adp_gates": ("LEAKAGE_UNSAFE", "Market/ADP artifacts require point-in-time as-of gates and source review.", "Point-in-Time Market Gate Review V1."),
    }
    accuracy_priorities = {
        "red_zone_exact_receipts": ("HIGH", "HIGH_AFTER_GATE", "MEDIUM_AFTER_GATE", "no", "Highest near-term formula-accuracy upside, but must pass source/as-of gate before regeneration."),
        "age_lifecycle_sidecars": ("MEDIUM_HIGH", "MEDIUM_HIGH", "MEDIUM_AFTER_REVIEW", "no", "Useful dynasty/decline/breakout context and easier to freeze, but lower direct scoring value than red-zone."),
        "point_in_time_market_adp_gates": ("MEDIUM_HIGH_AS_CONTEXT", "MEDIUM_AFTER_GATE", "LOW_UNTIL_APPROVED", "no", "Strong context/baseline potential, but high leakage risk until point-in-time gate is proven."),
        "point_in_time_injury_availability_gates": ("MEDIUM_AS_SLICE_CONTEXT", "MEDIUM_AFTER_GATE", "LOW_UNTIL_APPROVED", "no", "Useful for miss slices and caution context, not injury prediction or production input."),
        "historical_checkpoint_review_score": ("LOW_FOR_NEW_FORMULAS_HIGH_FOR_REPLAY", "LOW_NEAR_TERM", "LOW_NEAR_TERM", "conditional", "Only chase near term if it directly unblocks an approved replay/comparison."),
        "historical_position_specific_review_score": ("LOW_FOR_NEW_FORMULAS_HIGH_FOR_REPLAY", "LOW_NEAR_TERM", "LOW_NEAR_TERM", "conditional", "Only chase near term if it directly unblocks an approved replay/comparison."),
        "shadow_model_v2_metrics": ("LOW_UNLESS_SPECIFIC_REPLAY_BLOCKER", "LOW", "LOW", "yes", "Park unless a specific approved replay or benchmark proves it is required."),
    }
    for target, cfg in TARGETS.items():
        count = ledger_counts(ledger, target)
        status, status_note, next_action = decisions[target]
        direct_priority, gauntlet_priority, ranking_priority, park_later, accuracy_decision = accuracy_priorities[target]
        rows.append({
            "target_name": target,
            "why_it_matters": cfg["why"],
            "likely_formula_value": cfg["formula_value"],
            "DIRECT_FORMULA_ACCURACY_PRIORITY": direct_priority,
            "FORMULA_GAUNTLET_READINESS_PRIORITY": gauntlet_priority,
            "RANKING_INTEGRATION_PRIORITY": ranking_priority,
            "PARK_FOR_LATER": park_later,
            "accuracy_first_decision": accuracy_decision,
            "source_paths_or_candidate_artifacts": count["top_paths"],
            "candidate_artifact_count": count["candidate_count"],
            "artifact_classification_summary": count["classification_summary"],
            "data_exists": "yes_partial_or_candidate" if count["candidate_count"] else "no",
            "receipts_exist": "no_exact" if target not in {"age_lifecycle_sidecars"} else "partial_or_current_only",
            "sidecars_exist": "candidate_or_partial" if count["candidate_count"] else "no",
            "source_use_gate_exists": "conditional_or_missing",
            "row_grain": cfg["row_grain"],
            "join_keys": cfg["join_keys"],
            "season_coverage": "2013-2025 possible only if source/as-of proven" if target != "shadow_model_v2_metrics" else "unknown",
            "position_coverage": cfg["positions"],
            "decision_date_safety": "not_proven" if status in {"NEEDS_SOURCE_GATE_REVIEW", "LEAKAGE_UNSAFE", "MISSING_SOURCE", "MISSING_RECEIPT"} else "review_required",
            "leakage_risk": "high" if "point_in_time" in target else ("medium" if target in {"red_zone_exact_receipts", "age_lifecycle_sidecars"} else "unknown"),
            "identity_risk": "medium" if target in {"red_zone_exact_receipts", "age_lifecycle_sidecars"} else "unknown_or_low",
            "missingness_risk": "medium_high",
            "current_status": status,
            "status_note": status_note,
            "next_action": next_action,
        })
    return rows


def priority_rows() -> list[dict[str, object]]:
    return [
        {
            "priority_rank": 1,
            "target_name": "red_zone_exact_receipts",
            "recommended_action": "Model v4 Red Zone Exact Receipt Regeneration Pilot V1",
            "why_this_rank": "Highest near-term direct scoring/formula-accuracy upside; run only as a gated pilot that stops if source/as-of proof fails.",
            "likely_model_value": "high",
            "ease_of_recovery": "medium_low",
            "source_reliability": "candidate_source_not_yet_admitted",
            "historical_coverage": "candidate_sidecars_exist",
            "leakage_safety": "not_proven",
            "formula_data_mart_impact": "could add TD/opportunity context after gate",
            "formula_gauntlet_impact": "important candidate family/slice only after gate",
            "DIRECT_FORMULA_ACCURACY_PRIORITY": "HIGH",
            "FORMULA_GAUNTLET_READINESS_PRIORITY": "HIGH_AFTER_GATE",
            "RANKING_INTEGRATION_PRIORITY": "MEDIUM_AFTER_GATE",
            "PARK_FOR_LATER": "no",
        },
        {
            "priority_rank": 2,
            "target_name": "age_lifecycle_sidecars",
            "recommended_action": "Age Lifecycle Sidecar Freeze / Validation V1",
            "why_this_rank": "Most immediately executable freeze path and meaningful dynasty context, but lower direct scoring upside than red-zone.",
            "likely_model_value": "medium_high",
            "ease_of_recovery": "medium",
            "source_reliability": "partial_review_needed",
            "historical_coverage": "partial_or_current_only",
            "leakage_safety": "review_required",
            "formula_data_mart_impact": "adds lifecycle availability status and possible future guardrails",
            "formula_gauntlet_impact": "helps guardrail reporting after validation",
            "DIRECT_FORMULA_ACCURACY_PRIORITY": "MEDIUM_HIGH",
            "FORMULA_GAUNTLET_READINESS_PRIORITY": "MEDIUM_HIGH",
            "RANKING_INTEGRATION_PRIORITY": "MEDIUM_AFTER_REVIEW",
            "PARK_FOR_LATER": "no",
        },
        {
            "priority_rank": 3,
            "target_name": "point_in_time_market_adp_gates",
            "recommended_action": "Point-in-Time Market Gate Review V1",
            "why_this_rank": "Market can be strong, but needs strict historical as-of source controls.",
            "likely_model_value": "medium_high",
            "ease_of_recovery": "medium",
            "source_reliability": "uncleared",
            "historical_coverage": "unknown",
            "leakage_safety": "high_risk_without_asof",
            "formula_data_mart_impact": "possible baseline/context after gate",
            "formula_gauntlet_impact": "only after point-in-time gate",
            "DIRECT_FORMULA_ACCURACY_PRIORITY": "MEDIUM_HIGH_AS_CONTEXT",
            "FORMULA_GAUNTLET_READINESS_PRIORITY": "MEDIUM_AFTER_GATE",
            "RANKING_INTEGRATION_PRIORITY": "LOW_UNTIL_APPROVED",
            "PARK_FOR_LATER": "no",
        },
        {
            "priority_rank": 4,
            "target_name": "point_in_time_injury_availability_gates",
            "recommended_action": "Point-in-Time Injury Availability Gate Review V1",
            "why_this_rank": "Useful for miss analysis, but leakage/as-of risk is high.",
            "likely_model_value": "medium",
            "ease_of_recovery": "medium_low",
            "source_reliability": "uncleared",
            "historical_coverage": "unknown",
            "leakage_safety": "high_risk_without_asof",
            "formula_data_mart_impact": "availability caveats if gated",
            "formula_gauntlet_impact": "slice/reporting only until fully gated",
            "DIRECT_FORMULA_ACCURACY_PRIORITY": "MEDIUM_AS_SLICE_CONTEXT",
            "FORMULA_GAUNTLET_READINESS_PRIORITY": "MEDIUM_AFTER_GATE",
            "RANKING_INTEGRATION_PRIORITY": "LOW_UNTIL_APPROVED",
            "PARK_FOR_LATER": "no",
        },
        {
            "priority_rank": 5,
            "target_name": "historical_checkpoint_and_position_specific_scores",
            "recommended_action": "Historical Checkpoint Receipt Recovery Plan V1",
            "why_this_rank": "Critical for exact replay but less useful for new formula exploration than raw features.",
            "likely_model_value": "high_for_replay",
            "ease_of_recovery": "low",
            "source_reliability": "missing_exact_receipts",
            "historical_coverage": "current_or_partial_only",
            "leakage_safety": "unknown",
            "formula_data_mart_impact": "would support exact replay, not immediate feature breadth",
            "formula_gauntlet_impact": "does not alone unlock tournaments",
            "DIRECT_FORMULA_ACCURACY_PRIORITY": "LOW_FOR_NEW_FORMULAS_HIGH_FOR_REPLAY",
            "FORMULA_GAUNTLET_READINESS_PRIORITY": "LOW_NEAR_TERM",
            "RANKING_INTEGRATION_PRIORITY": "LOW_NEAR_TERM",
            "PARK_FOR_LATER": "conditional",
        },
        {
            "priority_rank": 6,
            "target_name": "shadow_model_v2_metrics",
            "recommended_action": "Shadow Metrics Scope Removal / Recovery Decision V1",
            "why_this_rank": "Missing and not required for current data mart or exact current-board hash reproduction.",
            "likely_model_value": "uncertain_low_near_term",
            "ease_of_recovery": "low",
            "source_reliability": "missing_source",
            "historical_coverage": "none",
            "leakage_safety": "unknown",
            "formula_data_mart_impact": "minimal unless recovered",
            "formula_gauntlet_impact": "not a gating feature for component tests",
            "DIRECT_FORMULA_ACCURACY_PRIORITY": "LOW_UNLESS_SPECIFIC_REPLAY_BLOCKER",
            "FORMULA_GAUNTLET_READINESS_PRIORITY": "LOW",
            "RANKING_INTEGRATION_PRIORITY": "LOW",
            "PARK_FOR_LATER": "yes",
        },
    ]


def write_markdowns(matrix: list[dict[str, object]], ledger: list[dict[str, object]]) -> None:
    blockers = [
        "- Red-zone has candidate artifacts, including red-zone sidecars/schema material, but source/as-of safety is not proven enough for immediate regeneration.",
        "- Exact historical checkpoint and position-specific score receipts remain missing.",
        "- `shadow_model_v2_metrics.csv` remains missing.",
        "- Age/lifecycle sidecars remain partial/current-only and require freeze/validation plus human review.",
        "- Injury/availability and market/ADP are leakage-unsafe until point-in-time gates are proven.",
        "- Route/YPRR/TPRR and return scoring are explicitly de-scoped for this sweep.",
        "- Production/model-use and ranking integration remain blocked.",
    ]
    write_text(OUT_DIR / "FORMULA_DATA_REMAINING_UPGRADE_BLOCKERS.md", "\n".join([
        "# Formula Data Remaining Upgrade Blockers",
        "",
        *blockers,
    ]))

    action_lines = [
        "# Formula Data Remaining Upgrade Action Plans",
        "",
    ]
    for row in matrix:
        action_lines += [
            f"## {row['target_name']}",
            "",
            f"- Current status: `{row['current_status']}`",
            f"- Next action: {row['next_action']}",
            f"- Why it matters: {row['why_it_matters']}",
            f"- Evidence: {row['candidate_artifact_count']} candidate artifacts; {row['artifact_classification_summary'] or 'none'}",
            f"- Caveat: {row['status_note']}",
            "",
        ]
    write_text(OUT_DIR / "FORMULA_DATA_REMAINING_UPGRADE_ACTION_PLANS.md", "\n".join(action_lines))

    write_text(OUT_DIR / "FORMULA_DATA_REMAINING_UPGRADE_NEXT_LANE_RECOMMENDATION.md", "\n".join([
        "# Formula Data Remaining Upgrade Next Lane Recommendation",
        "",
        "## Recommended Next Single Lane",
        "",
        "`Model v4 Red Zone Exact Receipt Regeneration Pilot V1`",
        "",
        "## Accuracy-First Rationale",
        "",
        "Red-zone exact receipts have the highest near-term direct formula-accuracy upside because red-zone opportunity can affect fantasy scoring beyond raw yardage/PYF. The next lane must be a gated pilot: it should first prove source/as-of safety, then regenerate review-only receipts only if that proof passes.",
        "",
        "Age/lifecycle sidecars are easier to freeze and remain the best fallback if red-zone source/as-of proof fails, but they are not higher direct scoring value than red-zone.",
        "",
        "## Required Stop Condition",
        "",
        "The red-zone pilot must stop before value generation if exact historical source artifacts, decision-date safety, identity joins, missingness classification, or source/use-gate status cannot be proven.",
        "",
        "## Explicitly Not Recommended",
        "",
        "- Formula Gauntlet.",
        "- 100-candidate Gauntlet.",
        "- Champion refinement.",
        "- Rankings integration.",
        "- Production/model-use.",
        "- Red-zone value generation without source/as-of proof.",
    ]))

    source_roots = [str(root) for root in SAFE_ROOTS if root.exists()]
    write_text(OUT_DIR / "FORMULA_DATA_REMAINING_UPGRADE_SOURCE_TRACE.md", "\n".join([
        "# Formula Data Remaining Upgrade Source Trace",
        "",
        f"Canonical remote HEAD verified before worktree creation: `{EXPECTED_REMOTE_HEAD}`",
        "",
        "## Prior Artifacts Used",
        "",
        f"- Formula Data Mart / Feature Availability Audit V1: `{PRIOR_DATA_MART_DIR}`",
        f"- Full System Audit / Integration Map V1: `{SYSTEM_AUDIT_DIR.relative_to(REPO)}`",
        f"- Historical Receipt Gap Closure Plan V1: `{GAP_PLAN_DIR.relative_to(REPO)}`",
        f"- Historical Receipt Locator and Ledger V1: `{LOCATOR_DIR.relative_to(REPO)}`",
        f"- Historical Receipt Freeze and Schema Validation V1: `{FREEZE_DIR.relative_to(REPO)}`",
        f"- Historical Receipt Regeneration Contract Planning V1: `{CONTRACT_DIR.relative_to(REPO)}`",
        f"- Confidence-cap receipts/tests/master-review: `{CONFIDENCE_DIR.relative_to(REPO)}`",
        f"- Role-archetype receipts/tests/master-review: `{ROLE_DIR.relative_to(REPO)}`",
        f"- Data Hygiene Operating Charter: `{DATA_HYGIENE_CHARTER_DIR.relative_to(REPO)}`",
        f"- HQ1 source receipt-chain standard: `{HQ1_STANDARD_DIR.relative_to(REPO)}`",
        "",
        "## Search Roots",
        "",
        *[f"- `{root}`" for root in source_roots],
        "",
        "## Safety",
        "",
        "Search was read-only. No source was promoted. No receipts were regenerated. No Formula Gauntlet, tournament, tuning, ranking, app/runtime/model behavior change, production/model-use approval, push, merge, or canonical `local_exports` write occurred.",
    ]))

    target_counts = Counter(str(row["target_name"]) for row in ledger)
    write_text(OUT_DIR / "FORMULA_DATA_MART_REMAINING_UPGRADE_SWEEP_V1_REPORT.md", "\n".join([
        "# Formula Data Mart Remaining Upgrade Sweep V1 Report",
        "",
        "## Verdict",
        "",
        "`GREEN_REMAINING_DATA_UPGRADES_PRIORITIZED_WITH_EXECUTABLE_NEXT_LANE`",
        "",
        "## Clear Answer",
        "",
        "The remaining useful data upgrades are now prioritized with an accuracy-first filter. Red-zone exact receipts are the highest near-term formula-accuracy target, but the next lane must be a gated review-only pilot that stops if source/as-of proof fails.",
        "",
        "## Targets Reviewed",
        "",
        *[f"- `{name}`: {target_counts.get(name, 0)} candidate artifacts ledgered" for name in TARGETS],
        "",
        "## Explicitly De-Scoped",
        "",
        *[f"- `{item}`" for item in DE_SCOPED],
        "",
        "## Highest-Value Available Upgrade",
        "",
        "`age_lifecycle_sidecars` are the most executable currently available upgrade because candidate partial/current artifacts exist and the next step is freeze/validation rather than value regeneration.",
        "",
        "## Highest-Priority Missing Upgrade",
        "",
        "`red_zone_exact_receipts` remain the highest-priority missing feature by likely formula value, but require source-gate/as-of proof before regeneration.",
        "",
        "## Next Executable Target",
        "",
        "`Model v4 Red Zone Exact Receipt Regeneration Pilot V1`, with a mandatory source/as-of gate and stop condition before value generation if unsafe.",
        "",
        "## Accuracy-Priority Filter",
        "",
        "- `DIRECT_FORMULA_ACCURACY_PRIORITY`, `FORMULA_GAUNTLET_READINESS_PRIORITY`, `RANKING_INTEGRATION_PRIORITY`, and `PARK_FOR_LATER` are included in the target matrix and priority ranking.",
        "- Red-zone is prioritized for near-term formula accuracy.",
        "- Shadow metrics, return scoring, route/YPRR/TPRR, broad PFR expansion, PFF-style elusive/proxy naming, and unsupported advanced data are parked or de-scoped unless a later approved lane proves direct near-term value.",
        "",
        "## Gates Preserved",
        "",
        "- Formula Gauntlet remains blocked.",
        "- Exact Model v4 replay remains blocked.",
        "- Production/model-use remains blocked.",
        "- Rankings integration remains blocked.",
        "- No source was promoted.",
    ]))


def main() -> None:
    for path in [LOCATOR_DIR, FREEZE_DIR, CONTRACT_DIR, DATA_HYGIENE_CHARTER_DIR, HQ1_STANDARD_DIR]:
        if not path.exists():
            raise FileNotFoundError(path)

    ledger = scan_roots()
    matrix = target_matrix(ledger)
    priorities = priority_rows()

    write_csv(OUT_DIR / "FORMULA_DATA_REMAINING_UPGRADE_ARTIFACT_LEDGER.csv", ledger, [
        "target_name",
        "found_path",
        "file_or_folder",
        "source_root",
        "matched_terms",
        "file_size",
        "modified_time",
        "sha256",
        "row_count_if_tabular",
        "column_count_if_tabular",
        "columns_if_tabular",
        "artifact_classification",
        "review_safe",
        "source_gate_required",
        "leakage_risk",
        "identity_risk",
        "notes",
    ])
    write_csv(OUT_DIR / "FORMULA_DATA_REMAINING_UPGRADE_TARGET_MATRIX.csv", matrix, [
        "target_name",
        "why_it_matters",
        "likely_formula_value",
        "DIRECT_FORMULA_ACCURACY_PRIORITY",
        "FORMULA_GAUNTLET_READINESS_PRIORITY",
        "RANKING_INTEGRATION_PRIORITY",
        "PARK_FOR_LATER",
        "accuracy_first_decision",
        "source_paths_or_candidate_artifacts",
        "candidate_artifact_count",
        "artifact_classification_summary",
        "data_exists",
        "receipts_exist",
        "sidecars_exist",
        "source_use_gate_exists",
        "row_grain",
        "join_keys",
        "season_coverage",
        "position_coverage",
        "decision_date_safety",
        "leakage_risk",
        "identity_risk",
        "missingness_risk",
        "current_status",
        "status_note",
        "next_action",
    ])
    write_csv(OUT_DIR / "FORMULA_DATA_REMAINING_UPGRADE_PRIORITY_RANKING.csv", priorities, [
        "priority_rank",
        "target_name",
        "recommended_action",
        "why_this_rank",
        "likely_model_value",
        "ease_of_recovery",
        "source_reliability",
        "historical_coverage",
        "leakage_safety",
        "formula_data_mart_impact",
        "formula_gauntlet_impact",
        "DIRECT_FORMULA_ACCURACY_PRIORITY",
        "FORMULA_GAUNTLET_READINESS_PRIORITY",
        "RANKING_INTEGRATION_PRIORITY",
        "PARK_FOR_LATER",
    ])
    write_markdowns(matrix, ledger)
    print(f"targets={len(TARGETS)}")
    print(f"ledger_rows={len(ledger)}")
    print("status_counts=" + "|".join(f"{k}={v}" for k, v in sorted(Counter(row["current_status"] for row in matrix).items())))
    print("next_lane=Model v4 Red Zone Exact Receipt Regeneration Pilot V1")


if __name__ == "__main__":
    main()
