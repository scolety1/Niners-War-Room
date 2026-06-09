from __future__ import annotations

import json
import shutil
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DOCS_ROOT = ROOT / "docs" / "model_v4"
MODEL_V4_EXPORT_ROOT = ROOT / "local_exports" / "model_v4"
PACKET_ROOT = MODEL_V4_EXPORT_ROOT / "audit_packets"
FIRST_DOWN_ROOT = MODEL_V4_EXPORT_ROOT / "first_downs" / "latest"
RETURN_ROOT = MODEL_V4_EXPORT_ROOT / "returns" / "latest"
IDENTITY_ROOT = MODEL_V4_EXPORT_ROOT / "player_identity" / "latest"
MATRIX_ROOT = MODEL_V4_EXPORT_ROOT / "evidence_matrices" / "latest"

PROMPT_PATH = DOCS_ROOT / "PHASE_10U_RENEWED_PRE_FORMULA_AUDIT_PROMPT.md"

PACKET_FILES: tuple[tuple[Path, str], ...] = (
    (
        DOCS_ROOT / "PHASE_10A_SOURCE_INVENTORY.md",
        "01_source_inventory/PHASE_10A_SOURCE_INVENTORY.md",
    ),
    (
        DOCS_ROOT / "PHASE_10A_SOURCE_INVENTORY.csv",
        "01_source_inventory/PHASE_10A_SOURCE_INVENTORY.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10A_SOURCE_INVENTORY_ISSUES.csv",
        "01_source_inventory/PHASE_10A_SOURCE_INVENTORY_ISSUES.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10F_SOURCE_TRUST_CONTRACT.md",
        "02_source_trust/PHASE_10F_SOURCE_TRUST_CONTRACT.md",
    ),
    (
        DOCS_ROOT / "PHASE_10F_SOURCE_TRUST_CONTRACT.csv",
        "02_source_trust/PHASE_10F_SOURCE_TRUST_CONTRACT.csv",
    ),
    (DOCS_ROOT / "FEATURE_SOURCE_CONTRACT.md", "02_source_trust/FEATURE_SOURCE_CONTRACT.md"),
    (
        DOCS_ROOT / "FEATURE_SOURCE_CONTRACT.csv",
        "02_source_trust/FEATURE_SOURCE_CONTRACT.csv",
    ),
    (
        DOCS_ROOT / "RECEIPT_REQUIREMENT_CONTRACT.md",
        "02_source_trust/RECEIPT_REQUIREMENT_CONTRACT.md",
    ),
    (
        DOCS_ROOT / "RECEIPT_REQUIREMENT_CONTRACT.csv",
        "02_source_trust/RECEIPT_REQUIREMENT_CONTRACT.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10B_FIRST_DOWN_CANONICALIZATION.md",
        "03_first_downs/PHASE_10B_FIRST_DOWN_CANONICALIZATION.md",
    ),
    (
        FIRST_DOWN_ROOT / "canonical_rushing_first_downs.csv",
        "03_first_downs/canonical_rushing_first_downs.csv",
    ),
    (
        FIRST_DOWN_ROOT / "canonical_receiving_first_downs.csv",
        "03_first_downs/canonical_receiving_first_downs.csv",
    ),
    (
        FIRST_DOWN_ROOT / "admitted_rushing_first_downs.csv",
        "03_first_downs/admitted_rushing_first_downs.csv",
    ),
    (
        FIRST_DOWN_ROOT / "admitted_receiving_first_downs.csv",
        "03_first_downs/admitted_receiving_first_downs.csv",
    ),
    (
        FIRST_DOWN_ROOT / "first_down_canonicalization_summary.csv",
        "03_first_downs/first_down_canonicalization_summary.csv",
    ),
    (
        FIRST_DOWN_ROOT / "first_down_canonicalization_validation.csv",
        "03_first_downs/first_down_canonicalization_validation.csv",
    ),
    (
        FIRST_DOWN_ROOT / "first_down_source_coverage.csv",
        "03_first_downs/first_down_source_coverage.csv",
    ),
    (FIRST_DOWN_ROOT / "first_down_receipts.csv", "03_first_downs/first_down_receipts.csv"),
    (
        DOCS_ROOT / "PHASE_10C_RETURN_DATA_AND_SCORING_CONTRACT.md",
        "04_returns/PHASE_10C_RETURN_DATA_AND_SCORING_CONTRACT.md",
    ),
    (RETURN_ROOT / "canonical_return_stats.csv", "04_returns/canonical_return_stats.csv"),
    (
        RETURN_ROOT / "admitted_return_scoring_evidence.csv",
        "04_returns/admitted_return_scoring_evidence.csv",
    ),
    (
        RETURN_ROOT / "return_canonicalization_summary.csv",
        "04_returns/return_canonicalization_summary.csv",
    ),
    (
        RETURN_ROOT / "return_canonicalization_validation.csv",
        "04_returns/return_canonicalization_validation.csv",
    ),
    (RETURN_ROOT / "return_source_coverage.csv", "04_returns/return_source_coverage.csv"),
    (RETURN_ROOT / "return_scoring_receipts.csv", "04_returns/return_scoring_receipts.csv"),
    (
        DOCS_ROOT / "PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.md",
        "05_prospect_sources/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.md",
    ),
    (
        DOCS_ROOT / "PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv",
        "05_prospect_sources/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10E_PLAYER_IDENTITY_CROSSWALK.md",
        "06_identity/PHASE_10E_PLAYER_IDENTITY_CROSSWALK.md",
    ),
    (
        IDENTITY_ROOT / "player_identity_crosswalk_summary.csv",
        "06_identity/player_identity_crosswalk_summary.csv",
    ),
    (
        IDENTITY_ROOT / "player_identity_crosswalk_summary.json",
        "06_identity/player_identity_crosswalk_summary.json",
    ),
    (
        IDENTITY_ROOT / "canonical_player_identity_crosswalk.csv",
        "06_identity/canonical_player_identity_crosswalk.csv",
    ),
    (
        IDENTITY_ROOT / "unresolved_identity_report.csv",
        "06_identity/unresolved_identity_report.csv",
    ),
    (
        IDENTITY_ROOT / "ambiguous_identity_report.csv",
        "06_identity/ambiguous_identity_report.csv",
    ),
    (
        MATRIX_ROOT / "admitted_current_prospect_identity_spine.csv",
        "07_evidence_matrices/admitted_current_prospect_identity_spine.csv",
    ),
    (
        MATRIX_ROOT / "prospect_current_feature_matrix.csv",
        "07_evidence_matrices/prospect_current_feature_matrix.csv",
    ),
    (
        MATRIX_ROOT / "admitted_prospect_current_feature_matrix.csv",
        "07_evidence_matrices/admitted_prospect_current_feature_matrix.csv",
    ),
    (
        MATRIX_ROOT / "current_prospect_identity_review_report.csv",
        "07_evidence_matrices/current_prospect_identity_review_report.csv",
    ),
    (
        MATRIX_ROOT / "current_prospect_identity_admission_notes.csv",
        "07_evidence_matrices/current_prospect_identity_admission_notes.csv",
    ),
    (
        MATRIX_ROOT / "historical_rookie_backtest_feature_matrix.csv",
        "07_evidence_matrices/historical_rookie_backtest_feature_matrix.csv",
    ),
    (
        MATRIX_ROOT / "nfl_player_current_evidence_matrix.csv",
        "07_evidence_matrices/nfl_player_current_evidence_matrix.csv",
    ),
    (
        MATRIX_ROOT / "source_coverage_matrix.csv",
        "07_evidence_matrices/source_coverage_matrix.csv",
    ),
    (MATRIX_ROOT / "warning_matrix.csv", "07_evidence_matrices/warning_matrix.csv"),
    (
        MATRIX_ROOT / "evidence_matrix_summary.csv",
        "07_evidence_matrices/evidence_matrix_summary.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10O_FORMULA_REQUIREMENTS_LOCK.md",
        "08_checkpoints/PHASE_10O_FORMULA_REQUIREMENTS_LOCK.md",
    ),
    (
        DOCS_ROOT / "PHASE_10Q_WORKOUT_MISSINGNESS_AND_SOURCE_LANE_REPAIR.md",
        "08_checkpoints/PHASE_10Q_WORKOUT_MISSINGNESS_AND_SOURCE_LANE_REPAIR.md",
    ),
    (
        DOCS_ROOT / "PHASE_10R_PROSPECT_FORMULA_ADMISSION_HARDENING.md",
        "08_checkpoints/PHASE_10R_PROSPECT_FORMULA_ADMISSION_HARDENING.md",
    ),
    (
        DOCS_ROOT / "PHASE_10S_TRACEABILITY_CLEANUP.md",
        "08_checkpoints/PHASE_10S_TRACEABILITY_CLEANUP.md",
    ),
    (
        DOCS_ROOT / "PHASE_10T_FINAL_SPINE_REPAIR_RECHECK.md",
        "08_checkpoints/PHASE_10T_FINAL_SPINE_REPAIR_RECHECK.md",
    ),
    (
        DOCS_ROOT / "PHASE_10N_EVIDENCE_ADMISSION_RECHECK.md",
        "08_checkpoints/PHASE_10N_EVIDENCE_ADMISSION_RECHECK.md",
    ),
    (
        DOCS_ROOT / "PHASE_10P_FINAL_PRE_FORMULA_CHECKPOINT.md",
        "08_checkpoints/PHASE_10P_FINAL_PRE_FORMULA_CHECKPOINT.md",
    ),
)


def main() -> None:
    packet_id = "model_v4_phase10u_renewed_pre_formula_audit_" + datetime.now(
        UTC
    ).strftime("%Y%m%dT%H%M%SZ")
    packet_dir = PACKET_ROOT / packet_id
    packet_dir.mkdir(parents=True, exist_ok=False)

    copied: list[dict[str, object]] = []
    missing: list[str] = []
    for source, relative_target in PACKET_FILES:
        _copy_if_present(source, packet_dir / relative_target, packet_dir, copied, missing)

    readme_dir = packet_dir / "00_READ_ME"
    readme_dir.mkdir(parents=True, exist_ok=True)

    prompt_target = readme_dir / "renewed_pre_formula_audit_prompt.md"
    shutil.copy2(PROMPT_PATH, prompt_target)
    copied.append(
        {
            "source": str(PROMPT_PATH),
            "packet_path": str(prompt_target.relative_to(packet_dir)),
            "bytes": prompt_target.stat().st_size,
        }
    )

    excluded_note = readme_dir / "excluded_raw_paid_sources.md"
    excluded_note.write_text(_excluded_note(), encoding="utf-8")
    copied.append(
        {
            "source": "generated exclusion note",
            "packet_path": str(excluded_note.relative_to(packet_dir)),
            "bytes": excluded_note.stat().st_size,
        }
    )

    zip_path = packet_dir.with_suffix(".zip")
    manifest = {
        "packet_id": packet_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "review_status": "renewed_pre_formula_audit_after_phase_10q_10r_10s_10t",
        "model_logic_changed": False,
        "formula_changes": False,
        "app_promotion": False,
        "readiness_unlocked": False,
        "raw_paid_source_files_excluded": True,
        "packet_dir": str(packet_dir),
        "zip_path": str(zip_path),
        "prompt_path": str(PROMPT_PATH),
        "included_file_count": len(copied),
        "missing_file_count": len(missing),
        "included_files": copied,
        "missing_files": missing,
        "audit_prompt": str(prompt_target.relative_to(packet_dir)),
    }
    manifest_path = readme_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_readme(readme_dir / "README.md", manifest)
    _zip_dir(packet_dir, zip_path)
    print(json.dumps(manifest, indent=2))


def _copy_if_present(
    source: Path,
    target: Path,
    packet_dir: Path,
    copied: list[dict[str, object]],
    missing: list[str],
) -> None:
    if not source.exists():
        missing.append(str(source))
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied.append(
        {
            "source": str(source),
            "packet_path": str(target.relative_to(packet_dir)),
            "bytes": target.stat().st_size,
        }
    )


def _write_readme(path: Path, manifest: dict[str, object]) -> None:
    lines = [
        "# Model v4 Phase 10U Renewed Pre-Formula Audit Packet",
        "",
        "This packet is for renewed external/pro audit after Phase 10Q, 10R, 10S, and 10T.",
        "",
        "## Safety",
        "",
        "- No formula design or formula scoring is included.",
        "- No active rankings were promoted.",
        "- My Team and War Board remain unchanged.",
        "- No readiness gates were unlocked.",
        (
            "- Raw paid/source files and source snapshots are intentionally "
            "excluded unless represented by generated manifests/reports."
        ),
        "",
        "## Audit Prompt",
        "",
        f"Use `{manifest['audit_prompt']}` as the neutral renewed audit prompt.",
        "",
        "## Packet Contents",
        "",
        f"- Included files: {manifest['included_file_count']}",
        f"- Missing files: {manifest['missing_file_count']}",
        "- See `manifest.json` for the complete file list.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _excluded_note() -> str:
    return """# Excluded Raw Paid/Source Files

This packet intentionally excludes raw paid/source exports and copied source
snapshots, including raw RotoWire subscription CSVs, raw CFBD/Kaggle archives,
and third-party raw combine/pro-day files.

The packet includes generated reports, source inventories, source trust
contracts, receipts, canonical/admitted evidence outputs, source coverage,
warning matrices, and model-ready evidence matrices so the auditor can inspect
data health without redistributing raw paid/source files.
"""


def _zip_dir(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


if __name__ == "__main__":
    main()
