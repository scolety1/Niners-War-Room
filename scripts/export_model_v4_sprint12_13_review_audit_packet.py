from __future__ import annotations

import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_sprint12_13_review_service import (  # noqa: E402
    build_sprint12_13_review_outputs,
    write_sprint12_13_review_outputs,
)

PACKET_ROOT = Path("local_exports/model_v4/audit_packets")
PROMPT_PATH = Path("docs/model_v4/SPRINT_12_13_REVIEW_EXTERNAL_AUDIT_PROMPT.md")
DATE_TAG = datetime.now(UTC).strftime("%Y%m%d")

FULL_PACKET = PACKET_ROOT / f"sprint12_13_review_audit_full_{DATE_TAG}.zip"
CORE_PACKET = PACKET_ROOT / f"sprint12_13_review_audit_core20_{DATE_TAG}.zip"

FULL_FILES = (
    "docs/model_v4/SPRINT_12_13_REVIEW_EXTERNAL_AUDIT_PROMPT.md",
    "docs/model_v4/SPRINT_12_REVIEW_ONLY_DYNASTY_VALUE.md",
    "docs/model_v4/SPRINT_13_REVIEW_ONLY_ROOKIE_BOARD.md",
    "docs/model_v4/PHASE_10O_FORMULA_REQUIREMENTS_LOCK.md",
    "docs/model_v4/PHASE_11A_FORMULA_CONTRACT.md",
    "docs/model_v4/PHASE_11B_REPLACEMENT_VORP_CORE.md",
    "docs/model_v4/PHASE_11G_CURRENT_VALUE_CHECKPOINT.md",
    "docs/model_v4/PHASE_11G_EXTERNAL_AUDIT_RESULT.md",
    "local_exports/model_v4/formula_contract/latest/formula_allowed_field_registry.csv",
    "local_exports/model_v4/formula_contract/latest/formula_blocked_field_registry.csv",
    "local_exports/model_v4/formula_contract/latest/formula_loader_guard_report.csv",
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv",
    "local_exports/model_v4/current_value/latest/current_player_value_component_rows.csv",
    "local_exports/model_v4/current_value/latest/current_player_value_receipts.csv",
    "local_exports/model_v4/current_value/latest/current_player_value_warnings.csv",
    "local_exports/model_v4/current_value/latest/confidence_missingness_review_rows.csv",
    "local_exports/model_v4/evidence_matrices/latest/admitted_prospect_current_feature_matrix.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_component_rows.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_receipts.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_warnings.csv",
    "local_exports/model_v4/pick_values/latest/pick_value_baselines_review.csv",
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv",
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_component_rows.csv",
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_receipts.csv",
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_warnings.csv",
    "src/services/model_v4_sprint12_13_review_service.py",
    "scripts/build_model_v4_sprint12_13_review.py",
    "tests/test_model_v4_sprint12_13_review_service.py",
)

CORE_FILES = (
    "docs/model_v4/SPRINT_12_13_REVIEW_EXTERNAL_AUDIT_PROMPT.md",
    "docs/model_v4/SPRINT_12_REVIEW_ONLY_DYNASTY_VALUE.md",
    "docs/model_v4/SPRINT_13_REVIEW_ONLY_ROOKIE_BOARD.md",
    "docs/model_v4/PHASE_10O_FORMULA_REQUIREMENTS_LOCK.md",
    "docs/model_v4/PHASE_11A_FORMULA_CONTRACT.md",
    "docs/model_v4/PHASE_11G_EXTERNAL_AUDIT_RESULT.md",
    "local_exports/model_v4/formula_contract/latest/formula_allowed_field_registry.csv",
    "local_exports/model_v4/formula_contract/latest/formula_loader_guard_report.csv",
    "local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv",
    "local_exports/model_v4/current_value/latest/confidence_missingness_review_rows.csv",
    "local_exports/model_v4/evidence_matrices/latest/admitted_prospect_current_feature_matrix.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_review_rows.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_component_rows.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_receipts.csv",
    "local_exports/model_v4/prospect_value/latest/prospect_value_warnings.csv",
    "local_exports/model_v4/pick_values/latest/pick_value_baselines_review.csv",
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv",
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_component_rows.csv",
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_warnings.csv",
)


def main() -> None:
    result = build_sprint12_13_review_outputs()
    write_sprint12_13_review_outputs(result=result)
    PACKET_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "packet_type": "model_v4_sprint12_13_review_external_audit",
        "review_status": "review_only",
        "full_packet": str(FULL_PACKET),
        "core_packet": str(CORE_PACKET),
        "prompt": str(PROMPT_PATH),
        "full_files": list(FULL_FILES),
        "core_files": list(CORE_FILES),
        "summary": result.summary,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    manifest_path = PACKET_ROOT / f"sprint12_13_review_audit_manifest_{DATE_TAG}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _zip(FULL_PACKET, (*FULL_FILES, str(manifest_path)))
    _zip(CORE_PACKET, (*CORE_FILES, str(manifest_path)))
    print(f"full_packet={FULL_PACKET}")
    print(f"core_packet={CORE_PACKET}")
    print(f"prompt={PROMPT_PATH}")
    print(f"manifest={manifest_path}")
    print(f"full_file_count={len(FULL_FILES) + 1}")
    print(f"core_file_count={len(CORE_FILES) + 1}")


def _zip(packet_path: Path, files: tuple[str, ...]) -> None:
    if packet_path.exists():
        packet_path.unlink()
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_name in files:
            path = Path(file_name)
            if not path.exists():
                raise FileNotFoundError(path)
            archive.write(path, path.as_posix())


if __name__ == "__main__":
    main()
