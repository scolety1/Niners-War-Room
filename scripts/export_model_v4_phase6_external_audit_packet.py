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
REVIEW_ROOT = MODEL_V4_EXPORT_ROOT / "review_only_latest"
PHASE5_BASELINE_ROOT = MODEL_V4_EXPORT_ROOT / "phase5_checkpoint_reconstructed"
PACKET_ROOT = MODEL_V4_EXPORT_ROOT / "audit_packets"

PROMPT_PATH = DOCS_ROOT / "MODEL_V4_PHASE_6_EXTERNAL_AUDIT_PROMPT.md"
PACKET_NOTE_PATH = DOCS_ROOT / "MODEL_V4_PHASE_6_EXTERNAL_AUDIT_PACKET.md"
REMAINING_BLOCKERS_PATH = DOCS_ROOT / "PHASE_6_REMAINING_BLOCKERS.md"

PROMPT = """You are a senior dynasty fantasy-football model auditor and data-quality investigator.

Project context:
This is a local-first deterministic dynasty fantasy football model for a 10-team
1QB league with no PPR, 0.4 rushing/receiving first-down bonus, 3 WR, 2 RB,
1 TE, 2 flex, no TE premium, deep benches, 23 keepers, and a forced
Roster's League-Rank Top Five release rule.

Goal:
Audit the attached Model v4 Phase 6 formula-patched packet scientifically before
any app promotion or readiness unlock. Do not tune rankings to match opinions.
Determine whether the formula changes are justified by receipts, sanity
fixtures, source coverage, and football logic.

Required audit areas:
1. Verify whether the Phase 6 formula changes are justified by the Phase 5
   checkpoint, Phase 6A formula patch summary, receipts, and movement audit.
2. Check whether the v4 preview rankings now make football sense for this league
   format, while still respecting source limitations and review-only status.
3. Evaluate RB/WR cross-position balance. Decide whether elite RBs and elite WRs
   are in plausible ranges, or whether a formula/data issue remains.
4. Evaluate QB suppression for a 10-team 1QB league. Confirm elite rushing QBs
   are not erased, but replaceable QBs are not over-prioritized.
5. Evaluate TE suppression for no TE premium. Confirm true elite TEs can survive
   the suppression layer, but replaceable TEs are not treated like cornerstone
   WR/RB assets.
6. Evaluate young-player bridge behavior. Check whether young players are helped
   by draft/prospect context only when appropriate, and whether weak evidence is
   still shown honestly instead of becoming fake certainty.
7. Evaluate missing-data handling. Missing production, projection, route metrics,
   injury context, or first-down projection data should be visible in receipts
   and should not masquerade as real evidence.
8. Find any player ranking that is unsupported by receipts. For each suspicious
   ranking, identify whether the likely cause is data gap, identity issue,
   lifecycle issue, normalization issue, formula issue, confidence issue, or
   acceptable model disagreement.

Important constraints:
- Do not treat market/liquidity as private football value.
- Do not treat league rank as player quality; it is a rule-context signal only.
- Do not assume unavailable route metrics are real evidence. Snap share is only a
  proxy and should be labeled that way.
- Do not recommend forbidden scraping.
- Do not hide unresolved issues.
- If a ranking is surprising but supported by receipts, say why.
- If a ranking is unsupported, identify the exact file/field/component causing it.

Output:
Produce a triage report with severity, evidence, affected packet files, likely
cause, and recommended next action. End with a verdict:
- ready for app promotion planning,
- needs another formula patch pass,
- needs source/data repair,
- needs external data,
- or requires architecture redesign.
"""

PACKET_FILES: tuple[tuple[Path, str], ...] = (
    (DOCS_ROOT / "PHASE_5_CHECKPOINT.md", "01_phase5_checkpoint/PHASE_5_CHECKPOINT.md"),
    (
        DOCS_ROOT / "PHASE_5_MOVEMENT_AUDIT.md",
        "01_phase5_checkpoint/PHASE_5_MOVEMENT_AUDIT.md",
    ),
    (
        DOCS_ROOT / "PHASE_5_MOVEMENT_AUDIT.csv",
        "01_phase5_checkpoint/PHASE_5_MOVEMENT_AUDIT.csv",
    ),
    (
        PHASE5_BASELINE_ROOT / "MODEL_V4_FORMULA_CONFIG_PHASE5_RECONSTRUCTED.json",
        "01_phase5_checkpoint/MODEL_V4_FORMULA_CONFIG_PHASE5_RECONSTRUCTED.json",
    ),
    (
        PHASE5_BASELINE_ROOT / "v4_preview_outputs.csv",
        "01_phase5_checkpoint/phase5_reconstructed_v4_preview_outputs.csv",
    ),
    (
        DOCS_ROOT / "PHASE_6A_FORMULA_PATCH_PASS.md",
        "02_formula_patch/PHASE_6A_FORMULA_PATCH_PASS.md",
    ),
    (
        DOCS_ROOT / "PHASE_6A_FORMULA_PATCH_PASS.csv",
        "02_formula_patch/PHASE_6A_FORMULA_PATCH_PASS.csv",
    ),
    (
        DOCS_ROOT / "PHASE_6A_PRE_PATCH_SANITY_FIXTURES.md",
        "02_formula_patch/PHASE_6A_PRE_PATCH_SANITY_FIXTURES.md",
    ),
    (
        DOCS_ROOT / "PHASE_6A_PRE_PATCH_SANITY_FIXTURES.csv",
        "02_formula_patch/PHASE_6A_PRE_PATCH_SANITY_FIXTURES.csv",
    ),
    (
        DOCS_ROOT / "PHASE_6A_SANITY_FIXTURE_RESULTS.md",
        "02_formula_patch/PHASE_6A_SANITY_FIXTURE_RESULTS.md",
    ),
    (
        DOCS_ROOT / "PHASE_6A_SANITY_FIXTURE_RESULTS.csv",
        "02_formula_patch/PHASE_6A_SANITY_FIXTURE_RESULTS.csv",
    ),
    (
        DOCS_ROOT / "MODEL_V4_FORMULA_CONFIG.json",
        "02_formula_patch/MODEL_V4_FORMULA_CONFIG.json",
    ),
    (
        DOCS_ROOT / "POSITION_FORMULA_PROPOSAL.md",
        "02_formula_patch/POSITION_FORMULA_PROPOSAL.md",
    ),
    (
        REVIEW_ROOT / "v4_preview_outputs.csv",
        "03_v4_preview/v4_preview_outputs.csv",
    ),
    (
        REVIEW_ROOT / "v4_normalized_component_rows.csv",
        "03_v4_preview/v4_normalized_component_rows.csv",
    ),
    (REVIEW_ROOT / "v4_receipt_rows.csv", "03_v4_preview/v4_receipt_rows.csv"),
    (
        REVIEW_ROOT / "v4_source_coverage_rows.csv",
        "03_v4_preview/v4_source_coverage_rows.csv",
    ),
    (REVIEW_ROOT / "v4_warning_rows.csv", "03_v4_preview/v4_warning_rows.csv"),
    (REVIEW_ROOT / "v4_preview_summary.csv", "03_v4_preview/v4_preview_summary.csv"),
    (
        REVIEW_ROOT / "v4_preview_summary.json",
        "03_v4_preview/v4_preview_summary.json",
    ),
    (
        REVIEW_ROOT / "v4_first_down_projection_estimates.csv",
        "03_v4_preview/v4_first_down_projection_estimates.csv",
    ),
    (
        REVIEW_ROOT / "v4_first_down_projection_rates.csv",
        "03_v4_preview/v4_first_down_projection_rates.csv",
    ),
    (
        REVIEW_ROOT / "v4_first_down_projection_summary.csv",
        "03_v4_preview/v4_first_down_projection_summary.csv",
    ),
    (
        DOCS_ROOT / "PHASE_6_MOVEMENT_AUDIT.md",
        "04_phase6_audits/PHASE_6_MOVEMENT_AUDIT.md",
    ),
    (
        DOCS_ROOT / "PHASE_6_MOVEMENT_AUDIT.csv",
        "04_phase6_audits/PHASE_6_MOVEMENT_AUDIT.csv",
    ),
    (
        DOCS_ROOT / "PHASE_6_SANITY_FIXTURE_RESULTS.md",
        "04_phase6_audits/PHASE_6_SANITY_FIXTURE_RESULTS.md",
    ),
    (
        DOCS_ROOT / "PHASE_6_SANITY_FIXTURE_RESULTS.csv",
        "04_phase6_audits/PHASE_6_SANITY_FIXTURE_RESULTS.csv",
    ),
    (
        DOCS_ROOT / "PHASE_6_NAMED_PLAYER_REVIEW.md",
        "04_phase6_audits/PHASE_6_NAMED_PLAYER_REVIEW.md",
    ),
    (
        DOCS_ROOT / "PHASE_6_NAMED_PLAYER_REVIEW.csv",
        "04_phase6_audits/PHASE_6_NAMED_PLAYER_REVIEW.csv",
    ),
    (
        REMAINING_BLOCKERS_PATH,
        "05_remaining_blockers/PHASE_6_REMAINING_BLOCKERS.md",
    ),
    (
        DOCS_ROOT / "FEATURE_SOURCE_CONTRACT.md",
        "06_supporting_contracts/FEATURE_SOURCE_CONTRACT.md",
    ),
    (
        DOCS_ROOT / "FORMULA_LANE_ARCHITECTURE.md",
        "06_supporting_contracts/FORMULA_LANE_ARCHITECTURE.md",
    ),
    (
        DOCS_ROOT / "RECEIPT_REQUIREMENT_CONTRACT.md",
        "06_supporting_contracts/RECEIPT_REQUIREMENT_CONTRACT.md",
    ),
    (
        DOCS_ROOT / "SANITY_FIXTURE_CONTRACT.csv",
        "06_supporting_contracts/SANITY_FIXTURE_CONTRACT.csv",
    ),
    (
        DOCS_ROOT / "TRUTH_SET_PLAYER_UNIVERSE.csv",
        "06_supporting_contracts/TRUTH_SET_PLAYER_UNIVERSE.csv",
    ),
)


def main() -> None:
    _write_prompt_and_blockers()
    packet_id = "model_v4_phase6_formula_patch_external_audit_" + datetime.now(
        UTC,
    ).strftime("%Y%m%dT%H%M%SZ")
    packet_dir = PACKET_ROOT / packet_id
    packet_dir.mkdir(parents=True, exist_ok=False)

    copied: list[dict[str, object]] = []
    missing: list[str] = []
    for source, relative_target in PACKET_FILES:
        _copy_if_present(source, packet_dir / relative_target, packet_dir, copied, missing)

    prompt_path = packet_dir / "00_READ_ME" / "neutral_external_audit_prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(PROMPT, encoding="utf-8")
    copied.append(
        {
            "source": str(PROMPT_PATH),
            "packet_path": str(prompt_path.relative_to(packet_dir)),
            "bytes": prompt_path.stat().st_size,
        }
    )

    manifest = {
        "packet_id": packet_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "review_status": "review_only",
        "model_logic_changed": False,
        "app_promotion": False,
        "decision_ready_unlocked": False,
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
    _write_packet_note(packet_dir, manifest)
    zip_path = packet_dir.with_suffix(".zip")
    _zip_dir(packet_dir, zip_path)
    print(json.dumps({**manifest, "zip_path": str(zip_path)}, indent=2))


def _write_prompt_and_blockers() -> None:
    PROMPT_PATH.write_text(PROMPT, encoding="utf-8")
    REMAINING_BLOCKERS_PATH.write_text(_remaining_blockers_text(), encoding="utf-8")


def _remaining_blockers_text() -> str:
    return "\n".join(
        [
            "# Phase 6 Remaining Blockers",
            "",
            "Status: review-only. These are blockers or review findings before any app "
            "promotion, not proof that the formula patch failed.",
            "",
            "## Blockers Before Promotion",
            "",
            "- External audit after Phase 6 formula patch has not been reviewed yet.",
            "- Model v4 preview is not wired into active War Board, My Team, Rankings, "
            "Draft Board, League Targets, or Trade Lab decision surfaces.",
            "- Readiness gates remain locked; no roster, draft, or final-money readiness "
            "was unlocked in Phase 6.",
            "- Draft readiness still requires official released veterans and final "
            "draft-pool gates.",
            "",
            "## Review Findings To Inspect",
            "",
            "- Young-player bridge behavior still has weak-evidence rows. This is expected "
            "when young players lack NFL production, first-down, usage, or snap evidence.",
            "- True route metrics remain unavailable from safe free/public structured data: "
            "routes run, route participation, TPRR, and YPRR are not scored as real evidence.",
            "- Snap share remains a proxy-only role input and must not be interpreted as "
            "route participation.",
            "- Projection first downs are estimated from history when direct projection "
            "fields are unavailable; receipts label this as estimated, not direct.",
            "- Injury context remains weak/context-only unless sourced.",
            "",
            "## Phase 6 Audit Status",
            "",
            "- Phase 6 movement audit found zero unexpected movement rows.",
            "- Phase 6 sanity fixtures were 29 ready, 0 review, 0 blocked.",
            "- Phase 6 named-player review matched all 19 requested players and left one "
            "inspection review: young-player bridge weak-evidence rows.",
            "",
        ]
    )


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


def _write_packet_note(packet_dir: Path, manifest: dict[str, object]) -> None:
    note = "\n".join(
        [
            "# Model v4 Phase 6 External Audit Packet",
            "",
            "Status: review-only. This packet packages the formula-patched v4 preview "
            "for independent audit and does not change model logic.",
            "",
            "## Packet",
            "",
            f"- Packet folder: `{packet_dir}`",
            f"- Zip file: `{packet_dir.with_suffix('.zip')}`",
            f"- Neutral external audit prompt: `{PROMPT_PATH}`",
            f"- Included copied/generated source files: {manifest['included_file_count']}",
            "- The zip also contains `00_READ_ME/manifest.json`.",
            f"- Missing files: {manifest['missing_file_count']}",
            "",
            "## Use",
            "",
            "Upload the zip and use the neutral prompt. Ask the auditor to focus on "
            "formula justification, receipt support, RB/WR balance, QB/TE suppression, "
            "young-player bridge behavior, missing-data honesty, and unsupported rankings.",
            "",
        ]
    )
    PACKET_NOTE_PATH.write_text(note, encoding="utf-8")


if __name__ == "__main__":
    main()
