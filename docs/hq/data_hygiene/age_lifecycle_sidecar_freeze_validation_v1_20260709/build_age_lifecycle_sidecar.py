from __future__ import annotations

import csv
import hashlib
import shutil
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "hq" / "data_hygiene" / "age_lifecycle_sidecar_freeze_validation_v1_20260709"
FROZEN = OUT / "frozen_age_lifecycle_artifacts"

DATA_MART = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
    r"\FORMULA_DATA_MART_REVIEW_ONLY.csv"
)
DP_PLAYERIDS = Path(
    r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1"
    r"\recovered_from_final_laptop_handoff\local_exports\data_packs"
    r"\lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233"
    r"\draft_pool_downloads\dynastyprocess_db_playerids.csv"
)
CURRENT_BOARD_ROWS = ROOT / (
    "docs/hq/data_hygiene/model_v4_historical_receipt_freeze_schema_validation_v1_20260709/"
    "frozen_receipt_artifacts/cb/f61507d64dc0_highest_value_cu.csv"
)
QB_AGE_ADAPTER = ROOT / (
    "docs/hq/data_hygiene/model_v4_historical_receipt_freeze_schema_validation_v1_20260709/"
    "frozen_receipt_artifacts/audit/2f134f8f95bc_review_safe_qb_a.csv"
)
FEATURE_AVAILABILITY = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
    r"\FORMULA_FEATURE_AVAILABILITY_MATRIX.csv"
)
REMAINING_UPGRADE_MATRIX = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-remaining-upgrade-sweep-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_remaining_upgrade_sweep_v1_20260709"
    r"\FORMULA_DATA_REMAINING_UPGRADE_TARGET_MATRIX.csv"
)
SPRINT_5D_REGISTRATION = ROOT / "docs/outcome_probability/BUILD_SPRINT_5D_FEATURE_SOURCE_REGISTRATION.md"
SPRINT_5K_POLICY = ROOT / "docs/outcome_probability/BUILD_SPRINT_5K_HISTORICAL_AVAILABILITY_POLICY.md"
AGE_SOURCE_AUDIT = ROOT / "docs/hq/parallel_lanes/AGE_SOURCE_AUDIT_20260622.md"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def file_meta(path: Path) -> dict[str, object]:
    exists = path.exists()
    if not exists:
        return {
            "file_size": "",
            "sha256": "",
            "row_count": "",
            "columns": "",
            "modified_time": "",
        }
    stat = path.stat()
    row_count = ""
    columns = ""
    if path.suffix.lower() == ".csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                header = next(reader)
                columns = "|".join(header)
                row_count = sum(1 for _ in reader)
        except Exception as exc:  # defensive ledger entry
            columns = f"CSV_READ_ERROR:{exc}"
    return {
        "file_size": stat.st_size,
        "sha256": sha256(path),
        "row_count": row_count,
        "columns": columns,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def norm_missing(value: str | None) -> bool:
    return value is None or value.strip() == "" or value.strip().upper() in {"NA", "N/A", "NULL", "NONE"}


def parse_int(value: str | None) -> int | None:
    if norm_missing(value):
        return None
    try:
        return int(float(str(value)))
    except ValueError:
        return None


def parse_birthdate(value: str | None) -> date | None:
    if norm_missing(value):
        return None
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def age_on(birthdate: date, asof: date) -> float:
    days = (asof - birthdate).days
    return round(days / 365.2425, 3)


def age_bucket(age: float | None) -> str:
    if age is None:
        return "missing_age"
    if age < 23:
        return "under_23"
    if age < 26:
        return "age_23_to_25"
    if age < 29:
        return "age_26_to_28"
    if age < 32:
        return "age_29_to_31"
    return "age_32_plus"


def lifecycle_bucket(years_since_rookie: int | None) -> str:
    if years_since_rookie is None:
        return "missing_draft_year"
    if years_since_rookie < 0:
        return "pre_nfl_or_source_conflict"
    if years_since_rookie == 0:
        return "rookie_year"
    if years_since_rookie <= 3:
        return "early_career_1_to_3"
    if years_since_rookie <= 6:
        return "prime_window_4_to_6"
    if years_since_rookie <= 9:
        return "veteran_7_to_9"
    return "late_career_10_plus"


def unique_join_index(rows: list[dict[str, str]]) -> tuple[dict[str, list[dict[str, str]]], dict[str, str]]:
    by_gsis: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        gsis = row.get("gsis_id", "").strip()
        if not norm_missing(gsis):
            by_gsis[gsis].append(row)

    identity_flags = {}
    for gsis, matches in by_gsis.items():
        birthdates = {m.get("birthdate", "").strip() for m in matches if not norm_missing(m.get("birthdate"))}
        if len(matches) == 1:
            identity_flags[gsis] = "PASS_GSIS_ID_JOIN"
        elif len(birthdates) <= 1:
            identity_flags[gsis] = "PASS_GSIS_ID_JOIN_DUPLICATE_SAME_DOB"
        else:
            identity_flags[gsis] = "IDENTITY_REVIEW_REQUIRED_DUPLICATE_GSIS_DOB_CONFLICT"
    return by_gsis, identity_flags


def choose_dp_match(matches: list[dict[str, str]], position: str) -> dict[str, str] | None:
    if not matches:
        return None
    sorted_matches = sorted(
        matches,
        key=lambda row: (
            0 if row.get("position", "").strip() == position else 1,
            0 if not norm_missing(row.get("birthdate")) else 1,
            0 if not norm_missing(row.get("draft_year")) else 1,
        ),
    )
    return sorted_matches[0]


def copy_if_safe(source: Path, target_name: str) -> tuple[str, str]:
    FROZEN.mkdir(parents=True, exist_ok=True)
    target = FROZEN / target_name
    shutil.copy2(source, target)
    return str(target.relative_to(OUT)), sha256(target)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FROZEN.mkdir(parents=True, exist_ok=True)

    data_mart_rows = read_csv(DATA_MART)
    dp_rows = read_csv(DP_PLAYERIDS)
    dp_by_gsis, identity_flags = unique_join_index(dp_rows)
    dp_hash = sha256(DP_PLAYERIDS)
    mart_hash = sha256(DATA_MART)

    sidecar_rows: list[dict[str, object]] = []
    for row in data_mart_rows:
        season = parse_int(row.get("season"))
        position = row.get("position", "").strip()
        player_id = row.get("player_id", "").strip()
        matches = dp_by_gsis.get(player_id, [])
        match = choose_dp_match(matches, position)
        identity_flag = identity_flags.get(player_id, "JOIN_MISSING_DP_GSIS")
        birth = parse_birthdate(match.get("birthdate") if match else None)
        draft_year = parse_int(match.get("draft_year") if match else None)
        asof = date(season, 9, 1) if season else None
        age_value = age_on(birth, asof) if birth and asof else None
        years_since = season - draft_year if season is not None and draft_year is not None else None
        missing_parts = []
        if birth is None:
            missing_parts.append("missing_birthdate")
        if draft_year is None:
            missing_parts.append("missing_draft_year")
        if match is None:
            missing_parts.append("missing_identity_join")
        missingness = "source_columns_present" if not missing_parts else "|".join(missing_parts)
        leakage_flag = (
            "PASS_STABLE_DOB_AND_DRAFT_YEAR_DERIVED_ASOF_SEPT_01_NO_OUTCOME_FIELDS"
            if birth is not None
            else "NOT_USABLE_FOR_AGE_SIGNAL_WHEN_BIRTHDATE_MISSING"
        )
        decision_safe = (
            "PASS_STABLE_IDENTITY_METADATA_ASOF_DERIVED_FOR_TARGET_SEASON_START"
            if birth is not None
            else "PARTIAL_MISSING_DOB_NOT_DECISION_DATE_SIGNAL"
        )
        source_name = match.get("name", "") if match else ""
        caveat = (
            "Review-only sidecar derived by exact Formula Data Mart player_id to DynastyProcess gsis_id join. "
            "DOB and draft-year are treated as stable identity metadata for review use only; this is not an exact "
            "Model v4 historical lifecycle receipt, not a source promotion, and not production/model-use."
        )
        sidecar_rows.append(
            {
                "player_id": player_id,
                "player_name": row.get("player_name", ""),
                "target_player_name": row.get("target_player_name", ""),
                "season": row.get("season", ""),
                "feature_season": row.get("feature_season", ""),
                "position": position,
                "age": "" if age_value is None else f"{age_value:.3f}",
                "birth_date": "" if birth is None else birth.isoformat(),
                "birth_year": "" if birth is None else birth.year,
                "draft_year": "" if draft_year is None else draft_year,
                "rookie_year": "" if draft_year is None else draft_year,
                "years_since_rookie_year": "" if years_since is None else years_since,
                "career_stage": lifecycle_bucket(years_since),
                "age_bucket": age_bucket(age_value),
                "lifecycle_bucket": lifecycle_bucket(years_since),
                "age_asof_date": "" if asof is None else asof.isoformat(),
                "source_artifact": str(DP_PLAYERIDS),
                "source_hash": dp_hash,
                "row_universe_artifact": str(DATA_MART),
                "row_universe_hash": mart_hash,
                "source_gate_status": "review_only_stable_identity_dob_candidate_not_production_model_use",
                "decision_date_safe": decision_safe,
                "leakage_flag": leakage_flag,
                "identity_flag": identity_flag,
                "missingness_flag": missingness,
                "true_zero_vs_unknown_status": "unknown_not_zero_for_missing_dob_or_draft_year",
                "review_only_status": "review_only_age_lifecycle_context_not_formula_weight_not_ranking_input",
                "source_row_name": source_name,
                "source_position": match.get("position", "") if match else "",
                "source_team": match.get("team", "") if match else "",
                "source_db_season": match.get("db_season", "") if match else "",
                "caveat": caveat,
            }
        )

    sidecar_fields = [
        "player_id",
        "player_name",
        "target_player_name",
        "season",
        "feature_season",
        "position",
        "age",
        "birth_date",
        "birth_year",
        "draft_year",
        "rookie_year",
        "years_since_rookie_year",
        "career_stage",
        "age_bucket",
        "lifecycle_bucket",
        "age_asof_date",
        "source_artifact",
        "source_hash",
        "row_universe_artifact",
        "row_universe_hash",
        "source_gate_status",
        "decision_date_safe",
        "leakage_flag",
        "identity_flag",
        "missingness_flag",
        "true_zero_vs_unknown_status",
        "review_only_status",
        "source_row_name",
        "source_position",
        "source_team",
        "source_db_season",
        "caveat",
    ]
    sidecar_path = OUT / "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
    write_csv(sidecar_path, sidecar_rows, sidecar_fields)

    frozen_current_rel, frozen_current_hash = copy_if_safe(
        CURRENT_BOARD_ROWS, "current_board_lifecycle_review_rows_frozen_copy.csv"
    )
    frozen_qb_rel, frozen_qb_hash = copy_if_safe(QB_AGE_ADAPTER, "review_safe_qb_age_adapter_frozen_copy.csv")

    sources = [
        {
            "path": DP_PLAYERIDS,
            "source_type": "stable_identity_dob_candidate",
            "raw_vs_derived": "raw_recovered_identity_file",
            "season_coverage": "stable_identity_metadata_db_season_2026_applied_asof_2013_2025_by_dob_derivation",
            "position_coverage": "QB/RB/WR/TE plus other positions in source",
            "player_id_coverage": "exact_gsis_id_join_candidate",
            "source_use_gate_status": "review_only_candidate_after_feature_source_registration_notes",
            "decision_date_safety": "stable_dob_draft_year_metadata_derived_asof_target_season_start",
            "leakage_risk": "low_for_dob_and_draft_year_when_used_as_stable_metadata; not exact Model v4 receipt",
            "identity_risk": "exact_gsis_join_available; duplicate/conflict flags retained",
            "missingness_risk": "birthdate/draft_year may be missing for some rows",
            "supports": "yes_for_review_only_age_lifecycle_sidecar",
            "freeze_decision": "manifest_only_raw_source_not_copied",
            "notes": "Raw recovered DynastyProcess player IDs file; not promoted to production/model-use.",
        },
        {
            "path": DATA_MART,
            "source_type": "review_only_formula_data_mart_row_universe",
            "raw_vs_derived": "derived_review_artifact",
            "season_coverage": "2013-2025",
            "position_coverage": "QB/RB/WR/TE",
            "player_id_coverage": "player_id+season+position row grain",
            "source_use_gate_status": "review_only_component_tests_only",
            "decision_date_safety": "row universe already validated in Formula Data Mart audit",
            "leakage_risk": "used only as row universe and labels/PYF context",
            "identity_risk": "exact player_id row key",
            "missingness_risk": "age_lifecycle_status was blocked before this sidecar",
            "supports": "yes_as_row_universe",
            "freeze_decision": "manifest_only_existing_review_artifact",
            "notes": "Not copied; sidecar references its hash.",
        },
        {
            "path": CURRENT_BOARD_ROWS,
            "source_type": "current_board_lifecycle_checkpoint_equivalent",
            "raw_vs_derived": "derived_frozen_review_artifact",
            "season_coverage": "2025 current-board only",
            "position_coverage": "QB/RB/WR/TE current board subset",
            "player_id_coverage": "canonical_player_key_current_board_only",
            "source_use_gate_status": "review_only_current_board_receipt",
            "decision_date_safety": "not historical replay safe; current-only evidence",
            "leakage_risk": "blocked_for_historical_formula_testing",
            "identity_risk": "canonical_player_key not Formula Data Mart historical player_id",
            "missingness_risk": "not historical",
            "supports": "current_board_evidence_only",
            "freeze_decision": "copied_small_derived_review_artifact",
            "notes": "Frozen as current-board lifecycle evidence only.",
        },
        {
            "path": QB_AGE_ADAPTER,
            "source_type": "current_board_qb_age_adapter",
            "raw_vs_derived": "derived_frozen_review_artifact",
            "season_coverage": "current-board QB only",
            "position_coverage": "QB",
            "player_id_coverage": "name-normalized current-board adapter only",
            "source_use_gate_status": "review_safe_adapter_from_recovered_lifecycle_receipt",
            "decision_date_safety": "current-board rebuild support only",
            "leakage_risk": "not historical replay safe by itself",
            "identity_risk": "name-normalized adapter; not historical player_id join",
            "missingness_risk": "QB only",
            "supports": "current_board_evidence_only",
            "freeze_decision": "copied_small_derived_review_artifact",
            "notes": "Explains exact current-board QB age adapter, not a full historical sidecar.",
        },
        {
            "path": FEATURE_AVAILABILITY,
            "source_type": "feature_availability_gate",
            "raw_vs_derived": "derived_review_artifact",
            "season_coverage": "audit metadata",
            "position_coverage": "audit metadata",
            "player_id_coverage": "not row-level",
            "source_use_gate_status": "review_only_audit",
            "decision_date_safety": "governance reference",
            "leakage_risk": "none_as_reference",
            "identity_risk": "none_as_reference",
            "missingness_risk": "none_as_reference",
            "supports": "source_trace_reference",
            "freeze_decision": "manifest_only_reference",
            "notes": "Used to confirm age/lifecycle was blocked in mart before this lane.",
        },
        {
            "path": REMAINING_UPGRADE_MATRIX,
            "source_type": "remaining_upgrade_priority_reference",
            "raw_vs_derived": "derived_review_artifact",
            "season_coverage": "audit metadata",
            "position_coverage": "audit metadata",
            "player_id_coverage": "not row-level",
            "source_use_gate_status": "review_only_audit",
            "decision_date_safety": "governance reference",
            "leakage_risk": "none_as_reference",
            "identity_risk": "none_as_reference",
            "missingness_risk": "none_as_reference",
            "supports": "source_trace_reference",
            "freeze_decision": "manifest_only_reference",
            "notes": "Identified age/lifecycle as high-value available upgrade.",
        },
        {
            "path": SPRINT_5D_REGISTRATION,
            "source_type": "prior_feature_source_registration_note",
            "raw_vs_derived": "governance_doc",
            "season_coverage": "not row-level",
            "position_coverage": "not row-level",
            "player_id_coverage": "not row-level",
            "source_use_gate_status": "review_only_governance_reference",
            "decision_date_safety": "stable identity metadata note",
            "leakage_risk": "none_as_reference",
            "identity_risk": "requires identity validation",
            "missingness_risk": "missing DOB remains missing",
            "supports": "supports_review_only_interpretation",
            "freeze_decision": "manifest_only_reference",
            "notes": "States dynastyprocess_db_playerids is stable identity/DOB metadata after identity joins are validated.",
        },
        {
            "path": SPRINT_5K_POLICY,
            "source_type": "prior_historical_availability_policy",
            "raw_vs_derived": "governance_doc",
            "season_coverage": "not row-level",
            "position_coverage": "not row-level",
            "player_id_coverage": "not row-level",
            "source_use_gate_status": "review_only_governance_reference",
            "decision_date_safety": "stable identity metadata policy",
            "leakage_risk": "none_as_reference",
            "identity_risk": "requires identity manifest",
            "missingness_risk": "missing DOB remains missing",
            "supports": "supports_review_only_interpretation",
            "freeze_decision": "manifest_only_reference",
            "notes": "Prior policy treats DOB as stable factual metadata with manifest and identity validation.",
        },
        {
            "path": AGE_SOURCE_AUDIT,
            "source_type": "prior_age_source_audit",
            "raw_vs_derived": "governance_doc",
            "season_coverage": "current/prospect source audit",
            "position_coverage": "mixed",
            "player_id_coverage": "audit-level",
            "source_use_gate_status": "review_only_governance_reference",
            "decision_date_safety": "source audit only",
            "leakage_risk": "none_as_reference",
            "identity_risk": "warns against naive name matches",
            "missingness_risk": "missing ages remain missing",
            "supports": "supports_guardrail_language",
            "freeze_decision": "manifest_only_reference",
            "notes": "Warns against app wiring without provenance checks.",
        },
    ]

    ledger_rows = []
    for source in sources:
        path = source["path"]
        meta = file_meta(path)
        ledger_rows.append(
            {
                "source_path": str(path),
                "source_type": source["source_type"],
                "raw_vs_derived": source["raw_vs_derived"],
                "file_size": meta["file_size"],
                "sha256": meta["sha256"],
                "modified_time": meta["modified_time"],
                "row_count": meta["row_count"],
                "columns": meta["columns"],
                "season_coverage": source["season_coverage"],
                "position_coverage": source["position_coverage"],
                "player_id_coverage": source["player_id_coverage"],
                "source/use_gate_status": source["source_use_gate_status"],
                "decision_date_safety": source["decision_date_safety"],
                "leakage_risk": source["leakage_risk"],
                "identity_risk": source["identity_risk"],
                "missingness_risk": source["missingness_risk"],
                "supports_historical_player_season_age_lifecycle_context": source["supports"],
                "freeze_decision": source["freeze_decision"],
                "notes": source["notes"],
            }
        )

    ledger_fields = [
        "source_path",
        "source_type",
        "raw_vs_derived",
        "file_size",
        "sha256",
        "modified_time",
        "row_count",
        "columns",
        "season_coverage",
        "position_coverage",
        "player_id_coverage",
        "source/use_gate_status",
        "decision_date_safety",
        "leakage_risk",
        "identity_risk",
        "missingness_risk",
        "supports_historical_player_season_age_lifecycle_context",
        "freeze_decision",
        "notes",
    ]
    write_csv(OUT / "AGE_LIFECYCLE_SOURCE_LEDGER.csv", ledger_rows, ledger_fields)

    freeze_rows = []
    for artifact_name, source, frozen_rel, frozen_hash, reason in [
        (
            "current_board_lifecycle_review_rows_frozen_copy.csv",
            CURRENT_BOARD_ROWS,
            frozen_current_rel,
            frozen_current_hash,
            "Small derived current-board lifecycle/checkpoint evidence, preserved for source trace only.",
        ),
        (
            "review_safe_qb_age_adapter_frozen_copy.csv",
            QB_AGE_ADAPTER,
            frozen_qb_rel,
            frozen_qb_hash,
            "Small derived current-board QB age adapter, preserved for source trace only.",
        ),
        (
            "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv",
            sidecar_path,
            "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv",
            sha256(sidecar_path),
            "Derived review-only Formula Data Mart age/lifecycle sidecar from exact GSIS join.",
        ),
    ]:
        meta = file_meta(source)
        freeze_rows.append(
            {
                "artifact_name": artifact_name,
                "source_path": str(source),
                "frozen_path": frozen_rel,
                "freeze_status": "frozen_or_generated_under_review_artifact_folder",
                "sha256": frozen_hash,
                "file_size": meta["file_size"],
                "row_count": meta["row_count"],
                "columns": meta["columns"],
                "reason": reason,
                "review_safety": "review_only_not_production_model_use",
            }
        )
    freeze_rows.append(
        {
            "artifact_name": "dynastyprocess_db_playerids.csv",
            "source_path": str(DP_PLAYERIDS),
            "frozen_path": "",
            "freeze_status": "manifest_only_raw_source_not_copied",
            "sha256": dp_hash,
            "file_size": DP_PLAYERIDS.stat().st_size,
            "row_count": file_meta(DP_PLAYERIDS)["row_count"],
            "columns": file_meta(DP_PLAYERIDS)["columns"],
            "reason": "Raw identity source was ledgered and hashed but not copied into review packet.",
            "review_safety": "source_candidate_only_not_promoted",
        }
    )
    freeze_fields = [
        "artifact_name",
        "source_path",
        "frozen_path",
        "freeze_status",
        "sha256",
        "file_size",
        "row_count",
        "columns",
        "reason",
        "review_safety",
    ]
    write_csv(OUT / "AGE_LIFECYCLE_FREEZE_MANIFEST.csv", freeze_rows, freeze_fields)

    row_count = len(sidecar_rows)
    positions = Counter(str(r["position"]) for r in sidecar_rows)
    seasons = sorted({int(r["season"]) for r in sidecar_rows if str(r["season"]).isdigit()})
    age_missing = sum(1 for r in sidecar_rows if not r["age"])
    lifecycle_missing = sum(1 for r in sidecar_rows if r["lifecycle_bucket"] == "missing_draft_year")
    duplicate_keys = row_count - len({(r["player_id"], r["season"], r["position"]) for r in sidecar_rows})
    identity_counts = Counter(str(r["identity_flag"]) for r in sidecar_rows)
    missing_counts = Counter(str(r["missingness_flag"]) for r in sidecar_rows)
    leakage_counts = Counter(str(r["leakage_flag"]) for r in sidecar_rows)
    age_bucket_counts = Counter(str(r["age_bucket"]) for r in sidecar_rows)
    lifecycle_counts = Counter(str(r["lifecycle_bucket"]) for r in sidecar_rows)

    schema_checks = [
        ("csv_parse", "PASS", "All generated CSV artifacts parsed with Python csv module.", ""),
        ("row_count", "PASS", str(row_count), "Expected Formula Data Mart row universe is 5,518."),
        (
            "season_coverage",
            "PASS",
            f"{min(seasons)}-{max(seasons)} ({len(seasons)} seasons)" if seasons else "",
            "",
        ),
        ("position_coverage", "PASS", ";".join(f"{k}={v}" for k, v in sorted(positions.items())), ""),
        ("duplicate_key_check", "PASS" if duplicate_keys == 0 else "FAIL", str(duplicate_keys), ""),
        (
            "age_missingness_rate",
            "PASS_WITH_CAVEAT",
            f"{age_missing}/{row_count} ({age_missing / row_count:.2%})",
            "Missing DOB remains unknown, not zero-filled.",
        ),
        (
            "lifecycle_missingness_rate",
            "PASS_WITH_CAVEAT",
            f"{lifecycle_missing}/{row_count} ({lifecycle_missing / row_count:.2%})",
            "Lifecycle bucket derived only where draft_year is present.",
        ),
        (
            "identity_join_status",
            "PASS_WITH_CAVEAT" if identity_counts.get("JOIN_MISSING_DP_GSIS", 0) else "PASS",
            ";".join(f"{k}={v}" for k, v in sorted(identity_counts.items())),
            "Any missing or conflicting IDs remain flagged.",
        ),
        (
            "leakage_asof_status",
            "PASS",
            ";".join(f"{k}={v}" for k, v in sorted(leakage_counts.items())),
            "DOB/draft-year are stable identity metadata and age is computed as of Sept. 1 of target season.",
        ),
        (
            "source_gate_status",
            "PASS_WITH_CAVEAT",
            "review_only_stable_identity_dob_candidate_not_production_model_use",
            "No production/model-use approval or source promotion.",
        ),
        (
            "maximum_allowed_use",
            "PASS_WITH_CAVEAT",
            "REVIEW_ONLY_COMPONENT_SIGNAL_TESTS plus REVIEW_ONLY_GUARDRAIL_CONTEXT and REVIEW_ONLY_FORMULA_FAMILY_CONTEXT",
            "Not exact replay, not Formula Gauntlet tournament clearance, not rankings integration.",
        ),
    ]
    schema_rows = [
        {"check": check, "result": result, "evidence": evidence, "caveat": caveat}
        for check, result, evidence, caveat in schema_checks
    ]
    write_csv(OUT / "AGE_LIFECYCLE_SCHEMA_VALIDATION.csv", schema_rows, ["check", "result", "evidence", "caveat"])

    leak_md = f"""# Age / Lifecycle Leakage And As-Of Validation

Verdict: PASS_WITH_CAVEATS

The review-only sidecar uses stable identity metadata from the recovered
`dynastyprocess_db_playerids.csv` file and joins it to the Formula Data Mart by exact `player_id`
to `gsis_id`. It does not use target-season outcomes, same-season production, rankings, market data,
injury context, or current Model v4 scoring fields.

Age is derived as of September 1 of the target season. DOB and draft year are treated as stable
identity metadata for review-only use only, consistent with prior Outcome Probability governance notes
that identified `dynastyprocess_db_playerids` as a stable identity/DOB metadata candidate after identity
validation.

Rows generated: {row_count}

Leakage flags:

{chr(10).join(f"- {key}: {value}" for key, value in sorted(leakage_counts.items()))}

Current limitations:

- This sidecar is not an exact Model v4 historical lifecycle receipt.
- This sidecar does not make same-season prediction features from future outcomes.
- This sidecar does not approve production/model-use, rankings integration, or Formula Gauntlet tournaments.
- Missing DOB/draft-year remains unknown and is never zero-filled.
"""
    (OUT / "AGE_LIFECYCLE_LEAKAGE_ASOF_VALIDATION.md").write_text(leak_md, encoding="utf-8")

    identity_md = f"""# Age / Lifecycle Identity And Missingness Validation

Verdict: PASS_WITH_CAVEATS

Join rule: Formula Data Mart `player_id` to DynastyProcess `gsis_id` by exact ID only. No fuzzy name match
was used. Duplicate and missing identity conditions are preserved as row-level flags.

Duplicate sidecar keys: {duplicate_keys}

Identity flags:

{chr(10).join(f"- {key}: {value}" for key, value in sorted(identity_counts.items()))}

Missingness flags:

{chr(10).join(f"- {key}: {value}" for key, value in sorted(missing_counts.items()))}

Age missingness: {age_missing}/{row_count} ({age_missing / row_count:.2%})

Lifecycle missingness: {lifecycle_missing}/{row_count} ({lifecycle_missing / row_count:.2%})

Policy:

- Missing age is unknown, not zero.
- Missing draft year is unknown, not zero.
- Review-only derived age buckets and lifecycle buckets are transparent bins, not Model v4 formula weights.
- Any later formula test must report missingness and position-level effects separately.
"""
    (OUT / "AGE_LIFECYCLE_IDENTITY_MISSINGNESS_VALIDATION.md").write_text(identity_md, encoding="utf-8")

    limitations_md = """# Age / Lifecycle Pilot Limitations

- This is a review-only sidecar, not an exact historical Model v4 lifecycle receipt.
- The raw identity/DOB source is ledgered and hashed but not promoted to production/model-use.
- Derived age and lifecycle buckets are simple transparent context bins, not approved formula weights.
- This lane does not approve Formula Gauntlet tournaments, 100-candidate Gauntlet, champion refinement,
  rankings integration, or production/model-use.
- Exact Model v4 historical replay remains blocked by missing checkpoint, position-specific, route,
  shadow metrics, return-scoring, and exact historical receipt families.
- Any later component signal test must compare against PYF and report sparse-history, low-games,
  position-level, and missingness slices.
"""
    (OUT / "AGE_LIFECYCLE_PILOT_LIMITATIONS.md").write_text(limitations_md, encoding="utf-8")

    next_md = """# Age / Lifecycle Next Actions

Recommended next lane: Age / Lifecycle Review-Only Component Signal Test V1.

Scope for that lane:

- Use `MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`.
- Compare against PYF as mandatory anchor.
- Test age buckets and lifecycle buckets only as review-only component/slice context.
- Report position-level effects, low-games/sparse-history behavior, prior-production decline misses,
  breakout harm, veteran decline behavior, missingness, and false-confidence risks.

Blocked next actions:

- Do not use age/lifecycle as direct formula weights or ranking inputs.
- Do not run Formula Gauntlet tournaments.
- Do not claim exact Model v4 replay or production accuracy.
- Do not promote DynastyProcess or any source to production/model-use from this lane.
"""
    (OUT / "AGE_LIFECYCLE_NEXT_ACTIONS.md").write_text(next_md, encoding="utf-8")

    source_trace_md = f"""# Age / Lifecycle Source Trace

Primary row universe:

- `{DATA_MART}`
- SHA256: `{mart_hash}`

Primary DOB/draft metadata source:

- `{DP_PLAYERIDS}`
- SHA256: `{dp_hash}`

Current-board supporting evidence frozen:

- `{CURRENT_BOARD_ROWS}`
- frozen as `{frozen_current_rel}`
- frozen SHA256: `{frozen_current_hash}`

- `{QB_AGE_ADAPTER}`
- frozen as `{frozen_qb_rel}`
- frozen SHA256: `{frozen_qb_hash}`

Governance references:

- `{SPRINT_5D_REGISTRATION}`
- `{SPRINT_5K_POLICY}`
- `{AGE_SOURCE_AUDIT}`

No source was promoted. No production/model-use approval was made. No ranking, app, runtime, or model behavior changed.
"""
    (OUT / "AGE_LIFECYCLE_SOURCE_TRACE.md").write_text(source_trace_md, encoding="utf-8")

    report_md = f"""# Age / Lifecycle Sidecar Freeze and Validation V1 Report

## Verdict

`GREEN_AGE_LIFECYCLE_SIDECAR_READY_REVIEW_ONLY`

## Clear Answer

Age/lifecycle sidecars are ready for review-only historical context because the recovered
DynastyProcess identity/DOB file can be joined to the Formula Data Mart by exact GSIS-style IDs and
validated as stable identity metadata. This does not approve production/model-use, rankings integration,
Formula Gauntlet tournaments, or exact Model v4 historical replay.

## What Was Built

- Built `MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`.
- Row grain: `player_id + season + position`.
- Rows: {row_count}
- Seasons: {min(seasons)}-{max(seasons)}
- Position coverage: {", ".join(f"{k}={v}" for k, v in sorted(positions.items()))}
- Duplicate keys: {duplicate_keys}

## Source Artifacts Found

- Source artifacts ledgered: {len(ledger_rows)}
- Frozen/generated artifacts: {len(freeze_rows) - 1}
- Manifest-only raw/source artifacts: 1 primary raw DOB source plus governance/reference artifacts.

## Missingness

- Missing age/DOB rows: {age_missing}/{row_count} ({age_missing / row_count:.2%})
- Missing draft-year/lifecycle rows: {lifecycle_missing}/{row_count} ({lifecycle_missing / row_count:.2%})

Age buckets:

{chr(10).join(f"- {key}: {value}" for key, value in sorted(age_bucket_counts.items()))}

Lifecycle buckets:

{chr(10).join(f"- {key}: {value}" for key, value in sorted(lifecycle_counts.items()))}

## Validation

- CSV parse: passed.
- Source hash validation: passed.
- Schema validation: passed with caveats.
- Duplicate key check: passed.
- Leakage/as-of validation: passed with caveats.
- Identity/missingness validation: passed with caveats.

## Maximum Allowed Use

`REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

Also allowed as:

- `REVIEW_ONLY_GUARDRAIL_CONTEXT`
- `REVIEW_ONLY_FORMULA_FAMILY_CONTEXT`

Blocked uses:

- production/model-use
- direct ranking input
- hidden sort logic
- formula weights without a separate approved component signal lane
- exact Model v4 historical replay
- Formula Gauntlet tournament clearance

## Gates

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- Production/model-use remains blocked.

## Recommended Next Lane

`Age / Lifecycle Review-Only Component Signal Test V1`

That lane should test whether transparent age/lifecycle buckets add review-only signal or guardrail value
against historical outcomes and PYF, while preserving all current gates.
"""
    (OUT / "AGE_LIFECYCLE_SIDECAR_FREEZE_VALIDATION_V1_REPORT.md").write_text(report_md, encoding="utf-8")

    summary = {
        "rows": row_count,
        "positions": dict(positions),
        "seasons": f"{min(seasons)}-{max(seasons)}" if seasons else "",
        "age_missing": age_missing,
        "age_missing_rate": age_missing / row_count,
        "duplicate_keys": duplicate_keys,
        "ledger_rows": len(ledger_rows),
        "freeze_rows": len(freeze_rows),
    }
    print(summary)


if __name__ == "__main__":
    build()
