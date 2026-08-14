from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/build_nwr_rookie_review_candidate_v1.py"
PACKET = REPO / "docs/hq/model/nwr_rookie_review_candidate_v1_20260814"


def _builder():
    spec = importlib.util.spec_from_file_location("rookie_candidate_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rows(name: str) -> list[dict[str, str]]:
    with (PACKET / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_candidate_packet_is_deterministic_and_manifested():
    builder = _builder()
    assert {path.name for path in PACKET.iterdir() if path.is_file()} == set(builder.REQUIRED_FILES)
    for name, data in builder.render(REPO).items():
        assert (PACKET / name).read_bytes() == data
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["canonical_promotion"] == "NOT_APPROVED"
    assert manifest["candidate_scores_ranks_runtime_integrated"] is False
    for name, receipt in manifest["files"].items():
        assert hashlib.sha256((PACKET / name).read_bytes()).hexdigest() == receipt["sha256"]


def test_full_class_score_rank_and_missingness_contract():
    rows = _rows("MODEL_V4_2026_ROOKIE_REVIEW_CANDIDATE.csv")
    assert len(rows) == 80
    assert len({row["official_draft_asset_id"] for row in rows}) == 80
    assert sum(row["identity_contract"] == "APPROVED_OFFICIAL_PICK_PLUS_PINNED_GOVERNED_LIVE_ID_V1" for row in rows) == 7
    assert all(row["candidate_board_score"] and row["candidate_rank"] for row in rows)
    assert all(not row["recruiting_component"] for row in rows)
    manual = [row for row in rows if row["identity_contract"].startswith("APPROVED_")]
    assert all(not row["frozen_board_score"] and not row["frozen_rank"] for row in manual)


def test_rank_diff_is_insertion_only_and_seven_receipts_are_exact():
    diff = _rows("FROZEN_VS_CANDIDATE_RANK_DIFF.csv")
    seven = _rows("SEVEN_NEWLY_SCORED_ROOKIES.csv")
    assert len(diff) == 80
    existing = [row for row in diff if row["frozen_rank"]]
    assert sum(row["classification"] == "PURE_INSERTION_DISPLACEMENT" for row in existing) == 63
    assert all(row["existing_player_score_change"] == "NO" for row in existing)
    stribling = next(row for row in seven if row["player"] == "De'Zhaun Stribling")
    assert stribling["live_player_id"] == "00-0041035"
    assert stribling["candidate_review_score"] == "62.0096"
    assert stribling["candidate_board_score"] == "51.468"
    assert stribling["candidate_rank"] == "11"
    assert not stribling["athletic_component"] and not stribling["recruiting_component"]
