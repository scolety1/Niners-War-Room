from __future__ import annotations

# Governed status strings are asserted verbatim for auditability.
# ruff: noqa: E501
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_nwr_rookie_intelligence_v2.py"
PACKET = REPO / "docs/hq/model/nwr_rookie_intelligence_v2_20260814"
FACTUAL_OVERLAY = REPO / (
    "docs/hq/product/nwr_rookie_intelligence_v2_factual_overlay_v1_20260814/"
    "MANUAL_REVIEW_FACTUAL_COMPONENT_OVERLAY.csv"
)


def _load_builder():
    spec = importlib.util.spec_from_file_location("nwr_rookie_intelligence_v2", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rows(name: str) -> list[dict[str, str]]:
    with (PACKET / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def builder():
    return _load_builder()


@pytest.fixture(scope="module")
def state(builder):
    return builder.load_state(REPO)


def test_exact_19_artifacts_and_manifest_hashes(builder):
    assert {path.name for path in PACKET.iterdir() if path.is_file()} == set(
        builder.REQUIRED_FILES
    )
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["class_counts"] == {
        "QB": 10,
        "RB": 12,
        "TE": 22,
        "WR": 36,
        "frozen_blocked": 7,
        "frozen_scored": 73,
        "total": 80,
        "unresolved_draft_assets": 0,
    }
    assert manifest["candidate_scores_ranks_runtime_integrated"] is False
    for name, receipt in manifest["files"].items():
        data = (PACKET / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == receipt["sha256"]
        assert len(data) == receipt["bytes"]


def test_deterministic_render_matches_docs(builder, state):
    rendered = builder.render_packet(state)
    assert set(rendered) == set(builder.REQUIRED_FILES)
    for name, expected in rendered.items():
        assert (PACKET / name).read_bytes() == expected
    assert FACTUAL_OVERLAY.read_bytes() == builder.render_factual_overlay(state)


def test_desktop_factual_overlay_excludes_every_score_and_rank_field():
    with FACTUAL_OVERLAY.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    assert len(rows) == 7
    assert all("score" not in field.casefold() for field in fields)
    assert all("rank" not in field.casefold() for field in fields)
    assert all(row["allowed_use"] == "manual_review_owner_context_only" for row in rows)
    assert all(row["blocked_use"] == "no_score_no_rank_no_model_no_trade_value" for row in rows)


def test_80_73_7_identity_and_score_separation():
    rows = _rows("CURRENT_2026_BOARD.csv")
    assert len(rows) == 80
    assert len({row["official_draft_asset_id"] for row in rows}) == 80
    assert len({row["stable_asset_id"] for row in rows}) == 80
    assert Counter(row["position"] for row in rows) == Counter(
        {"QB": 10, "RB": 12, "WR": 36, "TE": 22}
    )
    assert sum(bool(row["frozen_score"]) for row in rows) == 73
    assert sum(row["manual_review_status"] == "SEVEN_MANUAL_REVIEW" for row in rows) == 7
    assert all(row["refresh_candidate_score"] for row in rows)
    assert all(row["candidate_authority"] == "ROOKIE_REVIEW_REFRESH_CANDIDATE_REVIEW_ONLY" for row in rows)
    assert all("no_runtime" in row["blocked_use"] for row in rows)
    manual = [row for row in rows if row["manual_review_status"] == "SEVEN_MANUAL_REVIEW"]
    assert all(not row["frozen_score"] and not row["frozen_rank"] for row in manual)
    assert all(row["strict_frozen_replay_status"] == "STILL_BLOCKED_REQUIRED_EVIDENCE" for row in manual)
    assert all(row["identity_contract_status"] == "OWNER_APPROVAL_REQUIRED_FOR_NEW_IDENTITY_BRIDGE" for row in manual)


def test_seven_exact_facts_and_missingness():
    rows = {row["player"]: row for row in _rows("SEVEN_MANUAL_REVIEW_AUDIT.csv")}
    assert set(rows) == {
        "De'Zhaun Stribling", "Carson Beck", "Oscar Delp", "Colbie Young",
        "Nicholas Singleton", "Joe Royer", "Deion Burks",
    }
    assert rows["De'Zhaun Stribling"]["live_player_id"] == "00-0041035"
    assert rows["Carson Beck"]["live_player_id"] == "00-0041561"
    assert rows["Oscar Delp"]["live_player_id"] == "00-0041041"
    assert rows["Colbie Young"]["live_player_id"] == "00-0041069"
    assert rows["Nicholas Singleton"]["live_player_id"] == "00-0040886"
    assert rows["Joe Royer"]["live_player_id"] == "00-0041087"
    assert rows["Deion Burks"]["live_player_id"] == "00-0041132"
    assert {int(row["overall_pick"]) for row in rows.values()} == {33, 65, 73, 140, 165, 170, 254}
    assert all(row["production_component"] and row["market_share_component"] for row in rows.values())
    assert all(row["draft_capital_component"] and row["age_at_draft"] for row in rows.values())
    assert all(not row["recruiting_component"] for row in rows.values())
    assert rows["Oscar Delp"]["athletic_component"]
    assert rows["Joe Royer"]["athletic_component"]


def test_frozen_rank_contract_and_candidate_shift_are_explicit():
    rows = _rows("RANK_VS_SCORE_AUDIT.csv")
    assert len(rows) == 73
    assert all(row["recomputed_sprint14e_rank"] == row["frozen_rank"] for row in rows)
    assert all(row["finding"].startswith("NO_RANKING_DEFECT") for row in rows)
    assert sum(int(row["candidate_rank_shift"]) != 0 for row in rows) == 63
    board_header = next(csv.reader((PACKET / "CURRENT_2026_BOARD.csv").open(encoding="utf-8")))
    assert "refresh_candidate_score" in board_header
    assert "refresh_candidate_rank" in board_header
    assert "rookie_tier" not in board_header
    tier_doc = (PACKET / "ROOKIE_TIER_ANALYSIS.md").read_text(encoding="utf-8")
    assert "No validated rookie tiers are promoted" in tier_doc


def test_historical_authority_blocks_promotion():
    gauntlet = _rows("MODEL_GAUNTLET.csv")
    assert all(row["promotion"] in {"NO", "RETAINED_BY_DEFAULT"} for row in gauntlet)
    temporal = _rows("TEMPORAL_VALIDATION.csv")
    assert all(row["execution_status"] == "NOT_EXECUTED_IN_V2" for row in temporal)
    assert all(row["censored_rows_policy"] == "EXCLUDE_NOT_MISS" for row in temporal)
    verdict = (PACKET / "EXECUTIVE_VERDICT.md").read_text(encoding="utf-8")
    assert "GREEN_NWR_ROOKIE_REVIEW_REFRESH_CANDIDATE_READY_FOR_OWNER_APPROVAL" in verdict
    assert "not exact frozen replays" in verdict
