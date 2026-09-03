"""UDK qualitative flags -- review queue, NOT extraction (section 6).

The directive asked for deterministic PDF/icon extraction of qualitative
badges (My Guy / Value / Bust / Sleeper / Rookie / Injury Concerns /
Breakout) from the owner-authorized UDK PDFs, explicitly forbidding
scraping or inferring a badge from prose, and explicitly instructing:
"If exact deterministic extraction cannot be proven: do NOT fabricate.
Produce a small review queue and move on. Do not spend hours on icon
extraction."

Investigation performed (bounded, not "hours"):
- The real, already-parsed UDK snapshot CSVs
  (sample_data/kha_real_draft_2026/udk_skill_position_snapshot_with_identity_status.csv,
  udk_kdst_snapshot_20260902.csv) carry no my_guy/value/bust/sleeper/
  rookie/injury_concern/breakout columns -- these badges were never
  captured during the original PDF-to-CSV parsing pass.
- The raw source PDFs exist on this machine
  (C:\\NWR_DRAFT_DAY_TOOLS\\2026-09-02\\udk\\default.pdf and expanded.pdf,
  hashed below) but this environment has no PDF-rendering/icon-position
  tooling installed (poppler-utils; no pdfplumber/PyMuPDF/PyPDF2 either),
  and no prior PDF-parsing code exists in this repo to build on.
- Per the directive's own instruction, this script does NOT attempt a
  blind, unverified extraction. It produces the requested review-queue
  CSV instead, with every flag column honestly marked NOT_EXTRACTED
  (never a fabricated True/False) and extraction_confidence explaining
  exactly why, so a future pass with the right tooling has a concrete
  starting point rather than needing to rediscover this from scratch.

Run: python -m scripts.build_udk_qualitative_flags_review_queue_v1
Writes: sample_data/kha_real_draft_2026/UDK_QUALITATIVE_FLAGS_2026.csv
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "sample_data" / "kha_real_draft_2026"
SKILL_SNAPSHOT = FIXTURE_DIR / "udk_skill_position_snapshot_with_identity_status.csv"
KDST_SNAPSHOT = FIXTURE_DIR / "udk_kdst_snapshot_20260902.csv"
OUT_PATH = FIXTURE_DIR / "UDK_QUALITATIVE_FLAGS_2026.csv"

SOURCE_PDF_DIR = Path(r"C:\NWR_DRAFT_DAY_TOOLS\2026-09-02\udk")
SOURCE_PDFS = ("default.pdf", "expanded.pdf")

EXTRACTION_CONFIDENCE = "BLOCKED_NO_DETERMINISTIC_EXTRACTION_TOOLING"
FLAG_COLUMNS = ("my_guy", "value", "bust", "sleeper", "rookie", "injury_concern", "breakout")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pdf_sha_note() -> str:
    hashes = []
    for name in SOURCE_PDFS:
        path = SOURCE_PDF_DIR / name
        if path.is_file():
            hashes.append(f"{name}={_sha256(path)}")
        else:
            hashes.append(f"{name}=NOT_FOUND_ON_THIS_MACHINE")
    return "; ".join(hashes)


def build_rows() -> list[dict[str, str]]:
    pdf_note = _pdf_sha_note()
    rows: list[dict[str, str]] = []
    for source_path in (SKILL_SNAPSHOT, KDST_SNAPSHOT):
        if not source_path.is_file():
            continue
        with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for raw in reader:
                nwr_player_id = raw.get("nwr_player_id") or raw.get("player_name_raw") or ""
                row = {
                    "nwr_player_id": nwr_player_id,
                    **{flag: "NOT_EXTRACTED" for flag in FLAG_COLUMNS},
                    "source_page": "",
                    "extraction_confidence": EXTRACTION_CONFIDENCE,
                    "source_file_sha": pdf_note,
                }
                rows.append(row)
    return rows


def main() -> None:
    rows = build_rows()
    if not rows:
        print("No UDK snapshot rows found -- nothing to write.")
        return
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "nwr_player_id", *FLAG_COLUMNS, "source_page", "extraction_confidence", "source_file_sha"
    ]
    with OUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT_PATH} ({len(rows)} rows, all flags NOT_EXTRACTED -- see module docstring)")


if __name__ == "__main__":
    main()
