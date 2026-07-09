from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


ARTIFACT_DIR = Path(__file__).resolve().parent
WORKTREE_ROOT = ARTIFACT_DIR.parents[4]

REMOTE_HQ_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_SCOREBOARD_COMMIT = "70be361e7d440d139af99c403f157b894f6e09c8"
VERDICT = "YELLOW_MARKET_ADP_FOUND_BUT_ASOF_GATE_NOT_PASSED"

HIGH_VALUE_DIR = Path(
    r"C:\NWR\Niners-War-Room-high-value-signal-data-locator-audit-v1-20260709"
    r"\docs\hq\data_hygiene\high_value_signal_data_locator_audit_v1_20260709"
)
HIGH_VALUE_LEDGER = HIGH_VALUE_DIR / "HIGH_VALUE_SIGNAL_FOUND_ARTIFACT_LEDGER.csv"

EXTRA_MARKET_PATHS = [
    r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\20260623_dynastyprocess_v1\values.csv",
    r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\20260623_dynastyprocess_v1\values-players.csv",
    r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\20260623_dynastyprocess_v1\db_fpecr_latest.csv",
    r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\20260623_dynastyprocess_v1\db_playerids.csv",
    r"C:\NWR_SHARED_DATA\market_sources\dynastyprocess\20260623_dynastyprocess_v1\snapshot_metadata.json",
    r"C:\NWR\Niners-War-Room-dynasty-rankings-page\docs\hq\parallel_lanes\dynastyprocess_market_baseline_20260622\dp_market_baseline_context.csv",
    r"C:\NWR\Niners-War-Room-dynasty-rankings-page\docs\hq\parallel_lanes\dynastyprocess_market_baseline_20260622\dp_pick_value_context.csv",
    r"C:\NWR\Niners-War-Room-dynasty-rankings-page\docs\hq\parallel_lanes\dynastyprocess_market_baseline_20260622\dp_nwr_join_coverage.csv",
    r"C:\NWR_SHARED_DATA\vendor_spikes\sleeper_adp\sleeper_adp_endpoint_discovery_results_20260621.csv",
    r"C:\NWR_SHARED_DATA\vendor_spikes\sleeper_adp\SLEEPER_ADP_ENDPOINT_DISCOVERY_SCHEMA_REPORT_20260621.md",
    r"C:\NWR_SHARED_DATA\lane_exchange\market_behavior\sleeper_adp_display_context\latest_candidate.json",
    r"C:\NWR_SHARED_DATA\lane_exchange\market_behavior\sleeper_adp_display_context\20260621_064418_sleeper_adp_display_context_v0\manifest.json",
    r"C:\NWR_SHARED_DATA\lane_exchange\market_behavior\sleeper_adp_display_context\20260621_064418_sleeper_adp_display_context_v0\sleeper_adp_display_context.csv",
    r"C:\NWR\Niners-War-Room-dynasty-rankings-page\docs\hq\parallel_lanes\NWR_MARKET_ADP_DISPLAY_ONLY_POLICY_20260620.md",
    r"C:\NWR\Niners-War-Room-dynasty-rankings-page\docs\hq\parallel_lanes\NWR_SLEEPER_ADP_DISPLAY_CONTEXT_V0.md",
    r"C:\NWR\Niners-War-Room-dynasty-rankings-page\docs\hq\parallel_lanes\NWR_SLEEPER_ADP_ENDPOINT_DISCOVERY_20260621.md",
    r"C:\NWR\Niners-War-Room-dynasty-rankings-page\docs\hq\parallel_lanes\NWR_DYNASTYPROCESS_SUSTAINABLE_CONNECTOR_V1_20260622.md",
    r"C:\NWR\_rookie_recovery_temp\20260619_010650_handoff_zip_ingest_1\rookie_evidence_handoff_20260619_005620\01_RECOVERED_EXPORTS\rookie_framework\draft_ranking_model_v1_20260615\rookie_market_overlay_v1_20260615.csv",
    r"C:\NWR\_rookie_recovery_temp\20260619_010650_handoff_zip_ingest_1\rookie_evidence_handoff_20260619_005620\02_PLAYER_EVIDENCE\C_Users_smcol_Documents_Vacation_Niners-War-Room_l\84c318bf0b_current_player_value_receipts.csv",
    r"C:\NWR\_rookie_recovery_temp\20260619_010650_handoff_zip_ingest_1\rookie_evidence_handoff_20260619_005620\02_PLAYER_EVIDENCE\C_Users_smcol_Documents_Vacation_Niners-War-Room_l\d64c98447d_market_contamination_audit.csv",
]

MARKET_FIELD_TOKENS = (
    "adp",
    "market",
    "rank",
    "value",
    "ecr",
    "tier",
    "delta",
)
DATE_FIELD_TOKENS = (
    "date",
    "timestamp",
    "scrape",
    "collected",
    "updated",
    "asof",
    "as_of",
    "modified",
    "season",
    "year",
)
PLAYER_ID_TOKENS = (
    "player_id",
    "sleeper_id",
    "gsis_id",
    "fp_id",
    "fantasypros_id",
    "source_player_id",
    "canonical_player_key",
    "player_key",
)
NAME_TOKENS = ("player_name", "name", "player")
POSITION_TOKENS = ("position", "pos")
TEAM_TOKENS = ("team", "club")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_header_and_count(path: Path) -> Tuple[int, List[str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, [])
            count = sum(1 for _ in reader)
        return count, header
    except UnicodeDecodeError:
        with path.open("r", encoding="latin-1", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, [])
            count = sum(1 for _ in reader)
        return count, header
    except Exception:
        return -1, []


def inspect_json(path: Path) -> Tuple[int, List[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return -1, []
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            return len(data), sorted(data[0].keys())
        return len(data), []
    if isinstance(data, dict):
        return 1, sorted(data.keys())
    return 1, []


def split_columns(value: str) -> List[str]:
    if not value:
        return []
    if "|" in value:
        return [part.strip() for part in value.split("|") if part.strip()]
    if "," in value:
        return [part.strip() for part in value.split(",") if part.strip()]
    return [value.strip()]


def find_columns(columns: Iterable[str], tokens: Iterable[str]) -> str:
    found: List[str] = []
    token_list = [token.lower() for token in tokens]
    for col in columns:
        low = col.lower()
        if any(token in low for token in token_list):
            found.append(col)
    return "|".join(found[:40])


def classify_source(path_text: str, columns: List[str], row_count: Optional[int], prior_status: str) -> Tuple[str, str, str, str, str, str]:
    text = path_text.lower()
    col_text = "|".join(columns).lower()

    if "sleeper_adp" in text or "sleeper_adp_display_context" in text or "sleeper adp" in text:
        return (
            "CURRENT_ONLY_DISPLAY",
            "Sleeper ADP package is 2026/current-context display-only and source-risk YELLOW_UNDOCUMENTED_ENDPOINT.",
            "blocked_current_only_or_display_policy",
            "high",
            "low_for_display_high_for_formula",
            "display_only_market_context",
        )

    if "dynastyprocess" in text or "dp_market_baseline" in text or "market_sources\\dynastyprocess" in text:
        return (
            "CURRENT_ONLY_DISPLAY",
            "DynastyProcess snapshot has 2026 scrape/fetch metadata and explicit display-only policy; no historical player-season panel was found.",
            "blocked_current_snapshot_only",
            "medium",
            "low_for_display_high_for_historical_formula",
            "display_only_market_context",
        )

    if "current_value" in text or "current_player_value" in text or "rb_wr_current_value" in text:
        return (
            "CURRENT_ONLY_BLOCKED_FOR_HISTORICAL",
            "Current-value receipt layer points at current evidence matrices and cannot be backfilled into historical target seasons.",
            "current_only_value_layer",
            "high",
            "high_for_historical_formula",
            "blocked_historical_formula_input",
        )

    if "final_draft_board" in text or "draft_day_exports" in text or "trade_tier_values" in text:
        return (
            "CURRENT_ONLY_BLOCKED_FOR_HISTORICAL",
            "Draft-day board or trading-lab artifact is a current-board/canonical board artifact, not a historical/as-of market panel.",
            "current_board_artifact",
            "medium",
            "high_for_historical_formula",
            "blocked_historical_formula_input",
        )

    if "rookie_market_overlay" in text:
        return (
            "CURRENT_ONLY_BLOCKED_FOR_HISTORICAL",
            "Rookie overlay explicitly reports unavailable market data and isolates display-only fields from ranking score.",
            "no_admitted_player_level_market_values",
            "medium",
            "medium",
            "blocked_historical_formula_input",
        )

    if "missing_adp_market_template" in text:
        return (
            "SOURCE_GATE_REQUIRED",
            "Missing-market template contains placeholder needs_data rows, not admitted market/ADP values.",
            "placeholder_needs_data_rows",
            "unknown",
            "unknown_until_source_filled",
            "requires_source_gate_before_use",
        )

    if "player_market_inputs.csv" in text:
        if row_count == 0:
            return (
                "SOURCE_GATE_REQUIRED",
                "Market input template contains as_of/date fields but has zero source rows; it proves schema intent only.",
                "empty_template_no_source_values",
                "unknown",
                "unknown_until_populated",
                "requires_source_gate_before_use",
            )
        return (
            "LIKELY_HISTORICAL_NEEDS_PROOF",
            "Market input file has as_of/date fields but still needs source provenance, licensing/use gate, and historical date proof.",
            "needs_asof_and_source_proof",
            "unknown",
            "medium",
            "requires_source_gate_before_use",
        )

    if "db_playerids" in text:
        return (
            "IDENTITY_REVIEW_REQUIRED",
            "Player-id crosswalk may help joins but is not itself market/ADP values.",
            "identity_only_no_market_values",
            "medium",
            "low_for_formula_no_values",
            "identity_support_only",
        )

    if "market_contamination_audit" in text or "display_only_policy" in text:
        return (
            "SOURCE_GATE_REQUIRED",
            "Governance/audit artifact informs policy but does not provide gate-passed historical market rows.",
            "policy_or_audit_no_sidecar_values",
            "low",
            "low",
            "policy_evidence_only",
        )

    if any(token in col_text for token in ("asof", "as_of", "scrape_date", "market_scrape_date")):
        return (
            "LIKELY_HISTORICAL_NEEDS_PROOF",
            "Columns include date/as-of markers but source proof and row-level historical coverage still need review.",
            "needs_asof_and_source_proof",
            "unknown",
            "medium",
            "requires_source_gate_before_use",
        )

    if prior_status == "AVAILABLE_BUT_CURRENT_ONLY":
        return (
            "CURRENT_ONLY_BLOCKED_FOR_HISTORICAL",
            "Prior locator classified this candidate as current-only; no contrary as-of evidence was found.",
            "current_only_prior_locator",
            "unknown",
            "high_for_historical_formula",
            "blocked_historical_formula_input",
        )

    return (
        "NOT_ENOUGH_INFORMATION",
        "Candidate path matched market/ADP terms, but no historical/as-of-safe tabular market values were proven.",
        "insufficient_source_evidence",
        "unknown",
        "unknown",
        "park_pending_manual_source_review",
    )


def load_prior_market_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    if not HIGH_VALUE_LEDGER.exists():
        return rows
    with HIGH_VALUE_LEDGER.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("signal_family") == "historical_market_adp":
                rows.append(row)
    return rows


def build_source_rows() -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    seen_paths = set()

    for row in load_prior_market_rows():
        path_text = row.get("found_path", "")
        if not path_text:
            continue
        seen_paths.add(path_text.lower())
        candidates.append(
            {
                "source_path": path_text,
                "file_folder_name": row.get("file_folder_name", Path(path_text).name),
                "source_family": "historical_market_adp",
                "source_type": row.get("source_type", ""),
                "raw_vs_derived": row.get("raw_vs_derived", ""),
                "prior_availability_status": row.get("availability_status", ""),
                "prior_source_use_gate_status": row.get("source_use_gate_status", ""),
                "prior_leakage_asof_status": row.get("leakage_asof_status", ""),
                "prior_identity_risk": row.get("identity_risk", ""),
                "prior_missingness_risk": row.get("missingness_risk", ""),
                "prior_row_count": row.get("row_count", ""),
                "prior_columns": row.get("columns", ""),
            }
        )

    for path_text in EXTRA_MARKET_PATHS:
        if path_text.lower() in seen_paths:
            continue
        seen_paths.add(path_text.lower())
        candidates.append(
            {
                "source_path": path_text,
                "file_folder_name": Path(path_text).name,
                "source_family": "historical_market_adp",
                "source_type": "targeted_market_source",
                "raw_vs_derived": "",
                "prior_availability_status": "",
                "prior_source_use_gate_status": "",
                "prior_leakage_asof_status": "",
                "prior_identity_risk": "",
                "prior_missingness_risk": "",
                "prior_row_count": "",
                "prior_columns": "",
            }
        )

    ledger_rows: List[Dict[str, str]] = []
    for candidate in candidates:
        path = Path(candidate["source_path"])
        exists = path.exists()
        file_size = ""
        sha = ""
        row_count: Optional[int] = None
        columns: List[str] = split_columns(candidate.get("prior_columns", ""))
        modified_time = ""
        if exists and path.is_file():
            stat = path.stat()
            file_size = str(stat.st_size)
            modified_time = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds")
            sha = sha256_file(path)
            suffix = path.suffix.lower()
            if suffix == ".csv":
                csv_count, csv_columns = read_csv_header_and_count(path)
                if csv_count >= 0:
                    row_count = csv_count
                    columns = csv_columns
            elif suffix == ".json":
                json_count, json_columns = inspect_json(path)
                if json_count >= 0:
                    row_count = json_count
                    columns = json_columns
            elif suffix in {".md", ".txt", ".py"}:
                row_count = None
        elif candidate.get("prior_row_count"):
            try:
                row_count = int(float(candidate["prior_row_count"]))
            except ValueError:
                row_count = None

        if row_count is None and candidate.get("prior_row_count"):
            try:
                row_count = int(float(candidate["prior_row_count"]))
            except ValueError:
                row_count = None

        classification, evidence, blocked_reason, identity_risk, asof_risk, use_gate = classify_source(
            candidate["source_path"],
            columns,
            row_count,
            candidate.get("prior_availability_status", ""),
        )
        safe_join = "no"
        safe_display = "yes" if classification in {"CURRENT_ONLY_DISPLAY", "SOURCE_GATE_REQUIRED"} else "no"
        blocked = "yes" if classification != "HISTORICAL_ASOF_SAFE" else "no"

        ledger_rows.append(
            {
                "source_path": candidate["source_path"],
                "file_folder_name": candidate["file_folder_name"],
                "source_family": candidate["source_family"],
                "source_type": candidate["source_type"],
                "raw_vs_derived": candidate["raw_vs_derived"] or infer_raw_vs_derived(candidate["source_path"]),
                "row_grain": infer_row_grain(candidate["source_path"], columns),
                "file_size": file_size,
                "modified_time": modified_time,
                "sha256": sha,
                "row_count": "" if row_count is None else str(row_count),
                "columns": "|".join(columns[:80]),
                "seasons_or_dates_covered": infer_dates(candidate["source_path"], columns),
                "timestamp_date_fields": find_columns(columns, DATE_FIELD_TOKENS),
                "player_id_fields": find_columns(columns, PLAYER_ID_TOKENS),
                "player_name_fields": find_columns(columns, NAME_TOKENS),
                "position_fields": find_columns(columns, POSITION_TOKENS),
                "team_fields": find_columns(columns, TEAM_TOKENS),
                "rank_value_adp_fields": find_columns(columns, MARKET_FIELD_TOKENS),
                "whether_data_is_current_only": "yes" if classification.startswith("CURRENT_ONLY") else "not_proven",
                "whether_data_is_historical_asof": "no" if classification.startswith("CURRENT_ONLY") else "not_proven",
                "whether_source_is_paid_api_current_snapshot": infer_paid_api_status(candidate["source_path"]),
                "source_use_gate_status": use_gate,
                "identity_risk": identity_risk,
                "asof_leakage_risk": asof_risk,
                "safe_for_formula_mart_review_only_join": safe_join,
                "safe_only_for_display": safe_display,
                "blocked": blocked,
                "asof_leakage_classification": classification,
                "classification_evidence": evidence,
                "blocked_reason": blocked_reason,
                "prior_locator_status": candidate.get("prior_availability_status", ""),
                "notes": "No historical Formula Data Mart sidecar was built from this source in this lane.",
            }
        )
    return ledger_rows


def infer_raw_vs_derived(path_text: str) -> str:
    text = path_text.lower()
    if "nwr_shared_data\\market_sources" in text:
        return "raw_public_cache"
    if "local_exports" in text:
        return "derived_local_export"
    if "\\docs\\" in text:
        return "review_or_derived_artifact"
    if "\\templates\\" in text:
        return "input_template"
    if "\\tests\\" in text or "\\src\\" in text or "\\scripts\\" in text:
        return "code_or_test_artifact"
    return "unknown"


def infer_row_grain(path_text: str, columns: List[str]) -> str:
    text = path_text.lower()
    col_text = "|".join(columns).lower()
    if "sleeper_adp_display_context" in text:
        return "player_current_market_snapshot"
    if "dynastyprocess" in text or "dp_market_baseline" in text:
        return "player_current_market_snapshot"
    if "values-picks" in text or "pick_value" in text:
        return "pick_current_market_snapshot"
    if "db_playerids" in text or "crosswalk" in text:
        return "player_identity_crosswalk"
    if "player_market_inputs.csv" in text:
        return "intended_player_season_asof_template"
    if "current_value" in text:
        return "current_player_receipt_layer"
    if "season" in col_text and ("asof" in col_text or "as_of" in col_text):
        return "candidate_player_season_asof"
    return "not_proven"


def infer_dates(path_text: str, columns: List[str]) -> str:
    text = path_text.lower()
    col_text = "|".join(columns).lower()
    if "20260623_dynastyprocess" in text or "dp_market_baseline" in text:
        return "scrape_date=2026-06-19; fetch=2026-06-23"
    if "sleeper_adp" in text or "20260621_064418" in text:
        return "season=2026; collected=2026-06-21"
    if "rookie_market_overlay_v1_20260615" in text:
        return "snapshot=2026-06-15; rookie/current overlay"
    if "final_board_v1_20260622" in text:
        return "snapshot=2026-06-22; draft board"
    if "player_market_inputs.csv" in text and ("asof" in col_text or "as_of" in col_text):
        return "schema_has_asof_fields_no_rows"
    return ""


def infer_paid_api_status(path_text: str) -> str:
    text = path_text.lower()
    if "sleeper_adp" in text:
        return "public_undocumented_no_key_current_snapshot"
    if "dynastyprocess" in text:
        return "public_open_data_current_snapshot"
    if "fantasypros" in text or "ktc" in text or "keeptradecut" in text:
        return "source_gate_required_possible_third_party"
    return "not_detected"


def write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def build_outputs() -> None:
    ledger = build_source_rows()
    classification_counts = Counter(row["asof_leakage_classification"] for row in ledger)
    source_family_counts = Counter(row["source_use_gate_status"] for row in ledger)
    historical_safe = classification_counts.get("HISTORICAL_ASOF_SAFE", 0)
    likely_needs_proof = classification_counts.get("LIKELY_HISTORICAL_NEEDS_PROOF", 0)
    current_only = (
        classification_counts.get("CURRENT_ONLY_DISPLAY", 0)
        + classification_counts.get("CURRENT_ONLY_BLOCKED_FOR_HISTORICAL", 0)
    )

    source_fields = [
        "source_path",
        "file_folder_name",
        "source_family",
        "source_type",
        "raw_vs_derived",
        "row_grain",
        "file_size",
        "modified_time",
        "sha256",
        "row_count",
        "columns",
        "seasons_or_dates_covered",
        "timestamp_date_fields",
        "player_id_fields",
        "player_name_fields",
        "position_fields",
        "team_fields",
        "rank_value_adp_fields",
        "whether_data_is_current_only",
        "whether_data_is_historical_asof",
        "whether_source_is_paid_api_current_snapshot",
        "source_use_gate_status",
        "identity_risk",
        "asof_leakage_risk",
        "safe_for_formula_mart_review_only_join",
        "safe_only_for_display",
        "blocked",
        "asof_leakage_classification",
        "classification_evidence",
        "blocked_reason",
        "prior_locator_status",
        "notes",
    ]
    write_csv(ARTIFACT_DIR / "HISTORICAL_MARKET_ADP_SOURCE_LEDGER.csv", ledger, source_fields)

    classification_rows = [
        {
            "source_path": row["source_path"],
            "file_folder_name": row["file_folder_name"],
            "classification": row["asof_leakage_classification"],
            "evidence": row["classification_evidence"],
            "blocked_reason": row["blocked_reason"],
            "next_action": next_action_for(row["asof_leakage_classification"]),
        }
        for row in ledger
    ]
    write_csv(
        ARTIFACT_DIR / "HISTORICAL_MARKET_ADP_ASOF_LEAKAGE_CLASSIFICATION.csv",
        classification_rows,
        ["source_path", "file_folder_name", "classification", "evidence", "blocked_reason", "next_action"],
    )

    schema_rows = [
        {
            "check_name": "source_rows_ledgered",
            "status": "pass",
            "value": str(len(ledger)),
            "notes": "Market/ADP candidate rows were ledgered from the prior locator plus targeted DynastyProcess/Sleeper checks.",
        },
        {
            "check_name": "historical_asof_safe_sources",
            "status": "fail",
            "value": str(historical_safe),
            "notes": "No source proved historical player-season as-of-safe market or ADP values.",
        },
        {
            "check_name": "likely_historical_needs_proof_sources",
            "status": "review",
            "value": str(likely_needs_proof),
            "notes": "These are schemas or candidates with date fields, not gate-passed formula inputs.",
        },
        {
            "check_name": "current_or_display_only_sources",
            "status": "blocked_for_historical",
            "value": str(current_only),
            "notes": "Current-only market snapshots cannot be backfilled into historical formula tests.",
        },
        {
            "check_name": "sidecar_built",
            "status": "blocked",
            "value": "no",
            "notes": "Source/as-of gate did not pass.",
        },
        {
            "check_name": "component_tests_run",
            "status": "blocked",
            "value": "no",
            "notes": "Testing is blocked until a review-only historical/as-of-safe sidecar exists.",
        },
        {
            "check_name": "formula_x_ingredient_tests_run",
            "status": "blocked",
            "value": "no",
            "notes": "Testing is blocked until a review-only historical/as-of-safe sidecar exists.",
        },
        {
            "check_name": "production_or_ranking_use",
            "status": "blocked",
            "value": "no",
            "notes": "No production/model-use, ranking integration, app/runtime change, source promotion, push, or merge.",
        },
    ]
    write_csv(
        ARTIFACT_DIR / "HISTORICAL_MARKET_ADP_SCHEMA_VALIDATION.csv",
        schema_rows,
        ["check_name", "status", "value", "notes"],
    )

    write_report(ledger, classification_counts, source_family_counts)
    write_next_use_decision(ledger, classification_counts)
    write_blockers(classification_counts)
    write_source_trace()


def next_action_for(classification: str) -> str:
    if classification == "HISTORICAL_ASOF_SAFE":
        return "eligible_for_review_only_sidecar_build"
    if classification == "LIKELY_HISTORICAL_NEEDS_PROOF":
        return "manual_source_asof_proof_required_before_sidecar"
    if classification in {"CURRENT_ONLY_DISPLAY", "CURRENT_ONLY_BLOCKED_FOR_HISTORICAL"}:
        return "do_not_use_as_historical_formula_input"
    if classification == "SOURCE_GATE_REQUIRED":
        return "run_source_policy_and_license_gate_before_use"
    if classification == "IDENTITY_REVIEW_REQUIRED":
        return "identity_support_only_not_market_signal"
    return "park_until_better_source_evidence_exists"


def md_counts(counter: Counter) -> str:
    return "\n".join(f"- `{key}`: `{value}`" for key, value in sorted(counter.items()))


def write_report(ledger: List[Dict[str, str]], class_counts: Counter, gate_counts: Counter) -> None:
    report = f"""
# Historical Market / ADP Source Gate and Data Mart Join V1 Report

Verdict: `{VERDICT}`

Artifact path: `{ARTIFACT_DIR}`

Remote HQ verified: `{REMOTE_HQ_HEAD}`

Prior scoreboard normalization commit verified: `{PRIOR_SCOREBOARD_COMMIT}`

## Executive Decision

Historical market / ADP data was found, but no candidate source passed the historical/as-of gate for review-only Formula Data Mart use. The lane therefore did not build a sidecar and did not run component, formula x ingredient, or bounded combination tests.

The strongest concrete market sources are:

- DynastyProcess public market cache and derived context from the `2026-06-19` scrape / `2026-06-23` NWR fetch.
- Sleeper ADP display-context candidate from the `2026` endpoint package collected on `2026-06-21`.
- Current-value, final-board, trading-lab, and rookie-market overlay artifacts from recovered local exports.
- Empty `player_market_inputs.csv` schema templates that include `season`, `asof_date`, and market fields but contain no source rows.

These are useful for future policy/source review, but they are not historical player-season market panels. Current-only ADP, current dynasty values, and current-board artifacts cannot be used as historical features.

## Candidate Source Counts

- Candidate rows ledgered: `{len(ledger)}`
- Historical/as-of safe sources: `{class_counts.get("HISTORICAL_ASOF_SAFE", 0)}`
- Likely historical but still needs proof: `{class_counts.get("LIKELY_HISTORICAL_NEEDS_PROOF", 0)}`
- Current/display-only or current-blocked sources: `{class_counts.get("CURRENT_ONLY_DISPLAY", 0) + class_counts.get("CURRENT_ONLY_BLOCKED_FOR_HISTORICAL", 0)}`
- Source-gate-required / identity-only / insufficient-information sources: `{len(ledger) - class_counts.get("HISTORICAL_ASOF_SAFE", 0) - class_counts.get("LIKELY_HISTORICAL_NEEDS_PROOF", 0) - class_counts.get("CURRENT_ONLY_DISPLAY", 0) - class_counts.get("CURRENT_ONLY_BLOCKED_FOR_HISTORICAL", 0)}`

## As-Of Classification Counts

{md_counts(class_counts)}

## Source / Use-Gate Counts

{md_counts(gate_counts)}

## Gate Result

Historical/as-of gate passed: `no`

Sidecar built: `no`

Component tests run: `no`

Formula x ingredient tests run: `no`

Ingredient combination tests run: `no`

## Why No Sidecar Was Built

The lane found no source that proves all of the following at once:

- player-season grain or a reliable transform to player-season grain
- market/ADP fields with row-level as-of dates
- historical coverage suitable for lagged 2013-2025 Formula Data Mart use
- source/use-gate approval for formula testing
- identity coverage sufficient for Formula Data Mart joins
- no current-only or same-season/future leakage

DynastyProcess and Sleeper are the clearest market sources, but both are current-context packages with explicit display-only / market-awareness constraints in existing NWR governance. They remain blocked as historical formula inputs.

## Scoreboard Impact

Because no sidecar was built and no tests were run, this lane produced no result that could beat the `.755` full-history plateau or the `.763` snap/depth broad-window reference.

Review-only ranking simulation remains `not justified`.

## Recommended Next Step

Recommended next lane: `Rookie Draft Capital Data Mart Join / Component Test V1`

Rationale: market/ADP needs a true historical/as-of source before it can be tested. Rookie/draft-capital data is more likely to help sparse-history and young-player false-negative problems without relying on current market snapshots.

## Preserved Gates

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior remains unchanged.
- Push/merge was not performed.
- Source promotion was not performed.
- Canonical `local_exports` was not mutated.
- SportsDataIO, paid/API/free-trial/API-key work, PFF Elusive Rating, and `nwr_elusive_proxy_review_only` remain blocked.
"""
    write_text(ARTIFACT_DIR / "HISTORICAL_MARKET_ADP_SOURCE_GATE_DATA_MART_JOIN_V1_REPORT.md", report)


def write_next_use_decision(ledger: List[Dict[str, str]], class_counts: Counter) -> None:
    text = f"""
# Historical Market / ADP Next Use Decision

Decision: `AVAILABLE_NEEDS_ASOF_PROOF`

Secondary status: `AVAILABLE_DISPLAY_ONLY_CURRENT`

Historical market / ADP artifacts exist, but the source/as-of gate did not pass. No review-only Formula Data Mart sidecar may be built from the current evidence, and no formula tests may run from these sources.

## Allowed Now

- Display-only market-awareness review from already-governed DynastyProcess and Sleeper packages.
- Source-policy review of market/ADP licensing, cache handling, identity joins, and stale/current labels.
- Manual search for a true historical market/ADP panel with row-level as-of dates.

## Blocked Now

- Historical formula input.
- Current-only ADP backfill into prior seasons.
- 2026 market value as a 2013-2025 feature.
- Model training, hidden sort, recommendations, ranking integration, production/model-use, or app/runtime wiring.

## Sidecar/Test Decision

- Sidecar built: `no`
- Component tests run: `no`
- Formula x ingredient tests run: `no`
- Bounded combinations run: `no`

## Recommended Next Lane

`Rookie Draft Capital Data Mart Join / Component Test V1`

Market/ADP should reopen only when a true historical/as-of-safe source is available or when Master HQ approves a narrow source-gate lane for a specific historical provider.
"""
    write_text(ARTIFACT_DIR / "HISTORICAL_MARKET_ADP_NEXT_USE_DECISION.md", text)


def write_blockers(class_counts: Counter) -> None:
    text = f"""
# Historical Market / ADP Blockers and Caveats

## Primary Blocker

No historical/as-of-safe market or ADP data source was proven. The lane found current-context market data and display-only ADP packages, not a historical player-season market panel.

## Specific Caveats

- DynastyProcess is a useful public current market baseline, but the available local package is a `2026-06-19` scrape / `2026-06-23` fetch and is explicitly display-only.
- Sleeper ADP is a 2026 display-context candidate from an undocumented endpoint and is explicitly not approved for model training, rankings, hidden sort, or final recommendations.
- Current value receipts and final-board exports are current-board artifacts and cannot be used as historical Formula Data Mart inputs.
- Empty `player_market_inputs.csv` templates prove only schema intent; they do not provide source values.
- Rookie market overlay rows explicitly state that no admitted local player-level ADP/market source was loaded.

## Classification Counts

{md_counts(class_counts)}

## Tests Not Run

Component, formula x ingredient, and ingredient-combination tests were blocked because a clean market/ADP sidecar was not built.
"""
    write_text(ARTIFACT_DIR / "HISTORICAL_MARKET_ADP_BLOCKERS_AND_CAVEATS.md", text)


def write_source_trace() -> None:
    text = f"""
# Historical Market / ADP Source Trace

## Canonical / Prior Review Context

- Remote HQ verified: `{REMOTE_HQ_HEAD}`
- Prior scoreboard normalization commit: `{PRIOR_SCOREBOARD_COMMIT}`
- Prior scoreboard artifact: `docs/hq/master/ingredient_scoreboard_normalization_best_candidate_consolidation_v1_20260709/`
- Prior high-value signal locator artifact: `{HIGH_VALUE_DIR}`
- nflverse advanced ingredient audit artifact: `docs/hq/data_hygiene/nflverse_advanced_ingredient_availability_formula_mart_gap_audit_v1_20260709/`

## Market / ADP Inputs Reviewed

- `HIGH_VALUE_SIGNAL_FOUND_ARTIFACT_LEDGER.csv` market/ADP rows.
- DynastyProcess local public cache under `C:\\NWR_SHARED_DATA\\market_sources\\dynastyprocess\\20260623_dynastyprocess_v1`.
- DynastyProcess derived display-only packet under `C:\\NWR\\Niners-War-Room-dynasty-rankings-page\\docs\\hq\\parallel_lanes\\dynastyprocess_market_baseline_20260622`.
- Sleeper ADP discovery and display-context packets under `C:\\NWR_SHARED_DATA\\vendor_spikes\\sleeper_adp` and `C:\\NWR_SHARED_DATA\\lane_exchange\\market_behavior\\sleeper_adp_display_context`.
- Current-value receipts, final-board exports, trading-lab values, rookie market overlay files, and market input templates discovered by repo/local artifact search.

## Commands / Process Summary

- `git fetch origin`
- `git rev-parse origin/work/hq-parallel-control`
- Prior source ledgers were read from existing local review worktrees.
- Targeted file inspection was performed for DynastyProcess, Sleeper ADP, current-value receipts, rookie overlay, and market/ADP display-only policy docs.
- No network fetch, paid/API/free-trial/API-key work, push, merge, source promotion, canonical `local_exports` mutation, production/model-use, rankings integration, or app/runtime change occurred.
"""
    write_text(ARTIFACT_DIR / "HISTORICAL_MARKET_ADP_SOURCE_TRACE.md", text)


if __name__ == "__main__":
    build_outputs()
    print(f"Wrote Historical Market / ADP source gate artifacts to {ARTIFACT_DIR}")
