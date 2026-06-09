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

PROMPT_PATH = DOCS_ROOT / "PHASE_10I_DATA_SPINE_AUDIT_PROMPT.md"

PROMPT = """You are a senior dynasty fantasy-football data-spine auditor.

Project context:
Model v4 is a local-first dynasty fantasy football model for a 10-team, 1QB,
non-PPR league with rushing/receiving first-down scoring. The current phase is
pre-formula. The packet should be audited before any formula design or scoring
work begins.

Audit goal:
Decide whether the Phase 10 data spine is clean enough for formula work, or
whether source/data/identity repairs are still required.

Important constraints:
- Do not recommend formula tuning in this audit.
- Do not treat ADP, rankings, cheat sheets, mock drafts, big boards, market,
  league rank, or imported projections as private football value.
- Do not assume missing data is zero or average evidence.
- Do not treat source-limited files as fully admitted evidence.
- Do not assume raw paid/source files are included. This packet intentionally
  includes generated reports, manifests, derived matrices, receipts, and source
  coverage outputs, while excluding raw paid/source exports.

Please inspect:
1. Whether the source inventory and raw freeze are sufficient for pre-formula
   audit.
2. Whether first-down canonicalization is safe enough to use as direct sourced
   first-down evidence, including cleanup warnings and unresolved joins.
3. Whether return data and the return scoring contract are safely separated from
   major talent/value signals.
4. Whether the prospect source snapshot is safe, with market context separated
   from prospect evidence.
5. Whether identity joins are safe, especially unresolved and ambiguous reports.
6. Whether the source trust contract correctly classifies scoring evidence,
   derived evidence, prospect-prior evidence, context-only data, market context,
   source-limited data, and rejected fields.
7. Whether evidence matrices are clean enough for formula design:
   - one row per expected entity
   - no duplicate identity rows
   - no market leakage
   - no fake-zero missing evidence
   - ambiguous joins excluded or flagged
8. Whether warning/source-coverage matrices expose the right risks before
   formula work.
9. Whether historical rookie backtest rows avoid market/projection/post-hoc
   leakage.

Output:
Produce a triage report with:
- severity
- affected packet files
- evidence
- likely cause
- recommended next action

End with one verdict:
- ready for formula design,
- ready after minor documentation cleanup,
- needs focused identity/source repair,
- needs source replacement,
- or not ready for formula work.
"""

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
        DOCS_ROOT / "PHASE_10B_FIRST_DOWN_CANONICALIZATION.md",
        "02_first_downs/PHASE_10B_FIRST_DOWN_CANONICALIZATION.md",
    ),
    (
        FIRST_DOWN_ROOT / "first_down_canonicalization_summary.csv",
        "02_first_downs/first_down_canonicalization_summary.csv",
    ),
    (
        FIRST_DOWN_ROOT / "first_down_canonicalization_validation.csv",
        "02_first_downs/first_down_canonicalization_validation.csv",
    ),
    (
        FIRST_DOWN_ROOT / "first_down_source_coverage.csv",
        "02_first_downs/first_down_source_coverage.csv",
    ),
    (FIRST_DOWN_ROOT / "first_down_receipts.csv", "02_first_downs/first_down_receipts.csv"),
    (
        FIRST_DOWN_ROOT / "canonical_rushing_first_downs.csv",
        "02_first_downs/canonical_rushing_first_downs.csv",
    ),
    (
        FIRST_DOWN_ROOT / "canonical_receiving_first_downs.csv",
        "02_first_downs/canonical_receiving_first_downs.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10C_RETURN_DATA_AND_SCORING_CONTRACT.md",
        "03_returns/PHASE_10C_RETURN_DATA_AND_SCORING_CONTRACT.md",
    ),
    (
        RETURN_ROOT / "return_canonicalization_summary.csv",
        "03_returns/return_canonicalization_summary.csv",
    ),
    (
        RETURN_ROOT / "return_canonicalization_validation.csv",
        "03_returns/return_canonicalization_validation.csv",
    ),
    (RETURN_ROOT / "return_source_coverage.csv", "03_returns/return_source_coverage.csv"),
    (RETURN_ROOT / "return_scoring_receipts.csv", "03_returns/return_scoring_receipts.csv"),
    (RETURN_ROOT / "canonical_return_stats.csv", "03_returns/canonical_return_stats.csv"),
    (
        DOCS_ROOT / "PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.md",
        "04_prospect_sources/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.md",
    ),
    (
        DOCS_ROOT / "PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv",
        "04_prospect_sources/PHASE_10D_PROSPECT_SOURCE_SNAPSHOT.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10E_PLAYER_IDENTITY_CROSSWALK.md",
        "05_identity/PHASE_10E_PLAYER_IDENTITY_CROSSWALK.md",
    ),
    (
        IDENTITY_ROOT / "player_identity_crosswalk_summary.csv",
        "05_identity/player_identity_crosswalk_summary.csv",
    ),
    (
        IDENTITY_ROOT / "player_identity_crosswalk_summary.json",
        "05_identity/player_identity_crosswalk_summary.json",
    ),
    (
        IDENTITY_ROOT / "canonical_player_identity_crosswalk.csv",
        "05_identity/canonical_player_identity_crosswalk.csv",
    ),
    (
        IDENTITY_ROOT / "unresolved_identity_report.csv",
        "05_identity/unresolved_identity_report.csv",
    ),
    (
        IDENTITY_ROOT / "ambiguous_identity_report.csv",
        "05_identity/ambiguous_identity_report.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10F_SOURCE_TRUST_CONTRACT.md",
        "06_source_trust/PHASE_10F_SOURCE_TRUST_CONTRACT.md",
    ),
    (
        DOCS_ROOT / "PHASE_10F_SOURCE_TRUST_CONTRACT.csv",
        "06_source_trust/PHASE_10F_SOURCE_TRUST_CONTRACT.csv",
    ),
    (
        DOCS_ROOT / "FEATURE_SOURCE_CONTRACT.md",
        "06_source_trust/FEATURE_SOURCE_CONTRACT.md",
    ),
    (
        DOCS_ROOT / "FEATURE_SOURCE_CONTRACT.csv",
        "06_source_trust/FEATURE_SOURCE_CONTRACT.csv",
    ),
    (
        DOCS_ROOT / "RECEIPT_REQUIREMENT_CONTRACT.md",
        "06_source_trust/RECEIPT_REQUIREMENT_CONTRACT.md",
    ),
    (
        DOCS_ROOT / "RECEIPT_REQUIREMENT_CONTRACT.csv",
        "06_source_trust/RECEIPT_REQUIREMENT_CONTRACT.csv",
    ),
    (
        DOCS_ROOT / "PHASE_10G_EVIDENCE_MATRICES.md",
        "07_evidence_matrices/PHASE_10G_EVIDENCE_MATRICES.md",
    ),
    (
        MATRIX_ROOT / "evidence_matrix_summary.csv",
        "07_evidence_matrices/evidence_matrix_summary.csv",
    ),
    (
        MATRIX_ROOT / "nfl_player_current_evidence_matrix.csv",
        "07_evidence_matrices/nfl_player_current_evidence_matrix.csv",
    ),
    (
        MATRIX_ROOT / "prospect_current_feature_matrix.csv",
        "07_evidence_matrices/prospect_current_feature_matrix.csv",
    ),
    (
        MATRIX_ROOT / "historical_rookie_backtest_feature_matrix.csv",
        "07_evidence_matrices/historical_rookie_backtest_feature_matrix.csv",
    ),
    (
        MATRIX_ROOT / "source_coverage_matrix.csv",
        "07_evidence_matrices/source_coverage_matrix.csv",
    ),
    (MATRIX_ROOT / "warning_matrix.csv", "07_evidence_matrices/warning_matrix.csv"),
    (
        DOCS_ROOT / "PHASE_10H_DATA_SPINE_CHECKPOINT.md",
        "08_checkpoint/PHASE_10H_DATA_SPINE_CHECKPOINT.md",
    ),
)


def main() -> None:
    PROMPT_PATH.write_text(PROMPT, encoding="utf-8")
    packet_id = "model_v4_phase10i_data_spine_audit_" + datetime.now(UTC).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    packet_dir = PACKET_ROOT / packet_id
    packet_dir.mkdir(parents=True, exist_ok=False)

    copied: list[dict[str, object]] = []
    missing: list[str] = []
    for source, relative_target in PACKET_FILES:
        _copy_if_present(source, packet_dir / relative_target, packet_dir, copied, missing)

    readme_dir = packet_dir / "00_READ_ME"
    readme_dir.mkdir(parents=True, exist_ok=True)
    prompt_target = readme_dir / "neutral_data_spine_audit_prompt.md"
    prompt_target.write_text(PROMPT, encoding="utf-8")
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

    manifest = {
        "packet_id": packet_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "review_status": "pre_formula_data_spine_audit",
        "model_logic_changed": False,
        "formula_changes": False,
        "app_promotion": False,
        "decision_ready_unlocked": False,
        "raw_paid_source_files_excluded": True,
        "packet_dir": str(packet_dir),
        "zip_path": str(packet_dir.with_suffix(".zip")),
        "included_file_count": len(copied),
        "missing_file_count": len(missing),
        "included_files": copied,
        "missing_files": missing,
        "audit_prompt": str(prompt_target.relative_to(packet_dir)),
    }
    manifest_path = readme_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _write_readme(readme_dir / "README.md", manifest)

    zip_path = packet_dir.with_suffix(".zip")
    _zip_dir(packet_dir, zip_path)
    print(json.dumps({**manifest, "zip_path": str(zip_path)}, indent=2))


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
        "# Model v4 Phase 10I Data Spine Audit Packet",
        "",
        "This packet is for pre-formula external/pro audit.",
        "",
        "## Safety",
        "",
        "- No formula logic changed in this phase.",
        "- No active app rankings were promoted.",
        "- My Team and War Board remain unchanged.",
        "- No readiness gates were unlocked.",
        "- Raw paid/source files are intentionally excluded.",
        "",
        "## Audit Prompt",
        "",
        f"Use `{manifest['audit_prompt']}` as the neutral audit prompt.",
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

The packet includes generated reports, source inventories, manifests, source
coverage, receipts, canonicalized evidence outputs, and model-ready evidence
matrices so the auditor can inspect data health without redistributing raw
paid/source files.
"""


def _zip_dir(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


if __name__ == "__main__":
    main()
