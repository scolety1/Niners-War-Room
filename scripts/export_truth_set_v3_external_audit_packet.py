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

TRUTH_SET_ROOT = ROOT / "local_exports" / "truth_set_lab" / "v3"
REPORT_ROOT = TRUTH_SET_ROOT / "reports"
PACKET_ROOT = TRUTH_SET_ROOT / "audit_packets"
PREVIEW_ROOT = ROOT / "local_exports" / "nflverse_model_previews"
DOCS_ROOT = ROOT / "docs" / "codex"

PROMPT = """You are a senior fantasy-football model auditor and data-quality investigator.

Project context:
This is a local-first deterministic dynasty fantasy football model for a 10-team
1QB league with no PPR, 0.4 rushing/receiving first-down bonus, 3 WR, 2 RB,
1 TE, 2 flex, no TE premium, deep benches, 23 keepers, and a forced roster
league-rank top-five release rule.

Goal:
Audit the attached Truth Set Lab v3 packet scientifically. Do not tune rankings
to match opinions. Determine whether the v3 public-data pipeline improved the
model evidence enough to trust preview rankings, and identify what still blocks
roster, draft, or final money decisions.

Required audit areas:
1. Verify that v3 uses structured free/public data where claimed: native
nflverse production, play-by-play derived usage, snap share, projection
recompute, young bridge prior, sourced injury context, and market context only.
2. Check whether rejected sources stayed rejected: malformed production CSV,
unsafe role/usage CSV, supplied non-LVE projection points, fake route values,
and manual stat compilations.
3. Check whether route data honesty is clear: routes run, route participation,
TPRR, and YPRR should not appear as real free/public evidence unless a
validated structured source exists.
4. Check whether source coverage and receipts explain player values without
hidden defaults or fake confidence.
5. Check movement vs v2 and classify whether major movements are supported by
production, first downs, derived usage, snap share, projection recompute, young
bridge, source-quality flags, or formula imbalance.
6. Check whether remaining agent gaps are scoped correctly and avoid manual
player-stat compilation.
7. Identify confirmed bugs, likely bugs, source gaps, terminology/UI issues,
model-policy decisions, and false positives separately.

Important constraints:
- Do not assume public market value is private football value.
- Do not assume league rank is player quality; it is a rule/availability signal.
- Do not hide unresolved issues.
- Do not recommend forbidden scraping.
- If data is missing, say exactly what is missing and whether it should block
  roster decisions, draft decisions, or final money decisions.

Output:
Produce a triage report with severity, evidence, affected exports, likely cause,
and recommended next action. End with a verdict: continue with v3, gather
specific agent/source data, trial paid data, rebuild formulas later, or rebuild
architecture.
"""

PACKET_FILES: tuple[tuple[Path, str], ...] = (
    (
        REPORT_ROOT / "free_data_source_contract.csv",
        "01_source_contract/free_data_source_contract.csv",
    ),
    (
        REPORT_ROOT / "truth_set_v3_production_player_week.csv",
        "02_production_preview/player_week.csv",
    ),
    (
        REPORT_ROOT / "truth_set_v3_production_player_season.csv",
        "02_production_preview/player_season.csv",
    ),
    (REPORT_ROOT / "truth_set_v3_production_summary.csv", "02_production_preview/summary.csv"),
    (REPORT_ROOT / "truth_set_v3_production_summary.json", "02_production_preview/summary.json"),
    (REPORT_ROOT / "truth_set_v3_usage_player_week.csv", "03_usage_preview/player_week.csv"),
    (REPORT_ROOT / "truth_set_v3_usage_player_season.csv", "03_usage_preview/player_season.csv"),
    (REPORT_ROOT / "truth_set_v3_usage_summary.csv", "03_usage_preview/summary.csv"),
    (REPORT_ROOT / "truth_set_v3_usage_summary.json", "03_usage_preview/summary.json"),
    (REPORT_ROOT / "truth_set_v3_snap_share_player_week.csv", "04_snap_preview/player_week.csv"),
    (
        REPORT_ROOT / "truth_set_v3_snap_share_player_season.csv",
        "04_snap_preview/player_season.csv",
    ),
    (REPORT_ROOT / "truth_set_v3_snap_share_summary.csv", "04_snap_preview/summary.csv"),
    (REPORT_ROOT / "truth_set_v3_snap_share_summary.json", "04_snap_preview/summary.json"),
    (
        REPORT_ROOT / "truth_set_v3_route_data_honesty.csv",
        "05_route_honesty/route_data_honesty.csv",
    ),
    (REPORT_ROOT / "truth_set_v3_route_data_honesty_summary.csv", "05_route_honesty/summary.csv"),
    (REPORT_ROOT / "truth_set_v3_route_data_honesty_summary.json", "05_route_honesty/summary.json"),
    (REPORT_ROOT / "truth_set_v3_audit_groups.csv", "09_ranking_audit/audit_groups.csv"),
    (
        REPORT_ROOT / "truth_set_v3_audit_major_movements.csv",
        "09_ranking_audit/major_movements.csv",
    ),
    (REPORT_ROOT / "truth_set_v3_audit_summary.csv", "09_ranking_audit/summary.csv"),
    (REPORT_ROOT / "truth_set_v3_audit_summary.json", "09_ranking_audit/summary.json"),
    (
        REPORT_ROOT / "truth_set_v3_audit_suspicious_rankings.csv",
        "09_ranking_audit/suspicious_rankings.csv",
    ),
    (
        REPORT_ROOT / "truth_set_v3_remaining_agent_gap_list.csv",
        "10_remaining_gaps/remaining_agent_gap_list.csv",
    ),
    (
        REPORT_ROOT / "truth_set_v3_remaining_agent_gap_summary.json",
        "10_remaining_gaps/summary.json",
    ),
    (
        REPORT_ROOT / "truth_set_v3_agent_prompt_index.csv",
        "10_remaining_gaps/agent_prompt_index.csv",
    ),
    (REPORT_ROOT / "truth_set_v3_agent_prompts.md", "10_remaining_gaps/agent_prompts.md"),
)

PREVIEW_FILES: tuple[tuple[str, str], ...] = (
    ("stats_first_veteran_model_preview_outputs.csv", "06_model_preview/model_preview_outputs.csv"),
    ("truth_set_v3_preview_summary.csv", "06_model_preview/summary.csv"),
    ("truth_set_v3_preview_summary.json", "06_model_preview/summary.json"),
    ("truth_set_v3_preview_manifest.json", "06_model_preview/preview_manifest.json"),
    ("stats_first_feature_contributions.csv", "07_receipts/feature_contributions.csv"),
    ("stats_first_normalized_features.csv", "07_receipts/normalized_features.csv"),
    ("truth_set_v3_movement_vs_v2.csv", "08_movement_vs_v2/movement_vs_v2.csv"),
    ("truth_set_v3_source_coverage.csv", "11_supporting/source_coverage.csv"),
    ("truth_set_v3_rejected_field_log.csv", "11_supporting/rejected_field_log.csv"),
)

DOC_FILES: tuple[tuple[Path, str], ...] = (
    (
        DOCS_ROOT / "TRUTH_SET_LAB_V3_FREE_DATA_SOURCE_CONTRACT.md",
        "12_docs/free_data_source_contract.md",
    ),
    (
        DOCS_ROOT / "TRUTH_SET_LAB_V3_NATIVE_PRODUCTION_IMPORT.md",
        "12_docs/native_production_import.md",
    ),
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_DERIVED_USAGE_FROM_PBP.md", "12_docs/derived_usage_from_pbp.md"),
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_SNAP_SHARE_IMPORT.md", "12_docs/snap_share_import.md"),
    (
        DOCS_ROOT / "TRUTH_SET_LAB_V3_ROUTE_DATA_HONESTY_LAYER.md",
        "12_docs/route_data_honesty_layer.md",
    ),
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_PREVIEW_BUILD.md", "12_docs/preview_build.md"),
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_RANKING_AUDIT.md", "12_docs/ranking_audit.md"),
    (
        DOCS_ROOT / "TRUTH_SET_LAB_V3_REMAINING_AGENT_GAP_LIST.md",
        "12_docs/remaining_agent_gap_list.md",
    ),
)


def main() -> None:
    preview_dir = _latest_preview()
    if preview_dir is None:
        raise FileNotFoundError("No truth_set_lab_v3_preview_* folder found.")

    packet_id = "truth_set_lab_v3_external_audit_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    packet_dir = PACKET_ROOT / packet_id
    packet_dir.mkdir(parents=True, exist_ok=False)

    copied: list[dict[str, object]] = []
    missing: list[str] = []

    for source, relative_target in PACKET_FILES + DOC_FILES:
        _copy_if_present(source, packet_dir / relative_target, packet_dir, copied, missing)

    for file_name, relative_target in PREVIEW_FILES:
        _copy_if_present(
            preview_dir / file_name,
            packet_dir / relative_target,
            packet_dir,
            copied,
            missing,
        )

    prompt_path = packet_dir / "00_READ_ME" / "neutral_pro_audit_prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(PROMPT, encoding="utf-8")
    copied.append(
        {
            "source": "generated",
            "packet_path": str(prompt_path.relative_to(packet_dir)),
            "bytes": prompt_path.stat().st_size,
        }
    )

    docs_prompt_path = DOCS_ROOT / "TRUTH_SET_LAB_V3_EXTERNAL_AUDIT_PROMPT.md"
    docs_prompt_path.write_text(PROMPT, encoding="utf-8")

    manifest = {
        "packet_id": packet_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "review_status": "review_only",
        "model_logic_changed": False,
        "v3_preview_source": str(preview_dir),
        "packet_dir": str(packet_dir),
        "zip_path": str(packet_dir.with_suffix(".zip")),
        "included_file_count": len(copied),
        "missing_file_count": len(missing),
        "included_files": copied,
        "missing_files": missing,
        "audit_prompt": str(prompt_path.relative_to(packet_dir)),
    }
    manifest_path = packet_dir / "00_READ_ME" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    _write_checkpoint_note(packet_dir, manifest, docs_prompt_path)

    zip_path = packet_dir.with_suffix(".zip")
    _zip_dir(packet_dir, zip_path)

    print(json.dumps({**manifest, "zip_path": str(zip_path)}, indent=2))


def _latest_preview() -> Path | None:
    candidates = [path for path in PREVIEW_ROOT.glob("truth_set_lab_v3_preview_*") if path.is_dir()]
    return sorted(candidates, key=lambda path: path.stat().st_mtime)[-1] if candidates else None


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


def _zip_dir(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir))


def _write_checkpoint_note(
    packet_dir: Path,
    manifest: dict[str, object],
    docs_prompt_path: Path,
) -> None:
    note = "\n".join(
        [
            "# Truth Set Lab v3 External Audit Packet",
            "",
            "Status: review-only. This phase packages evidence only and does not "
            "change model logic.",
            "",
            "## Packet",
            "",
            f"- Packet folder: `{packet_dir}`",
            f"- Zip file: `{packet_dir.with_suffix('.zip')}`",
            f"- Neutral Pro audit prompt: `{docs_prompt_path}`",
            f"- Included files: {manifest['included_file_count']}",
            f"- Missing files: {manifest['missing_file_count']}",
            "",
            "## Use",
            "",
            "Upload the zip and use the neutral prompt. Ask the auditor to focus on evidence, "
            "source quality, rejected fields, movement reasons, route-data honesty, and remaining "
            "agent gaps. Do not ask it to tune rankings to opinions.",
            "",
        ]
    )
    (DOCS_ROOT / "TRUTH_SET_LAB_V3_EXTERNAL_AUDIT_PACKET.md").write_text(
        note,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
