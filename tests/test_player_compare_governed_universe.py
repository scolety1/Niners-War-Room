from __future__ import annotations

import csv
import re
from pathlib import Path

from src.services.draft_day_app_v1_service import resolve_dynasty_rankings_path
from src.services.governed_asset_registry_service import (
    file_sha256,
    load_governed_asset_registry,
)
from src.services.player_compare_decision_service import (
    NO_COMMON_SCALE_READ,
    NOT_ENOUGH_INFORMATION,
    build_player_compare_decision_summary,
)
from src.services.player_compare_universe_service import (
    NO_COMMON_SCALE_NOTE,
    build_player_compare_universe,
    governed_source_identity,
)

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "pages" / "22_player_compare_v1.py"

REPRESENTATIVE_PLAYERS = (
    ("9493", "Puka Nacua", "WR"),
    ("9509", "Bijan Robinson", "RB"),
    ("4046", "Patrick Mahomes", "QB"),
    ("8183", "Brock Purdy", "QB"),
    ("6786", "CeeDee Lamb", "WR"),
    ("6794", "Justin Jefferson", "WR"),
    ("6770", "Joe Burrow", "QB"),
    ("4881", "Lamar Jackson", "QB"),
    ("4217", "George Kittle", "TE"),
)


def _write_current_board(path: Path) -> str:
    fields = [
        "player_id",
        "player_name",
        "position",
        "nfl_team",
        "nwr_rank",
        "nwr_dynasty_score",
        "confidence_status",
        "warning_flags",
    ]
    rows = list(REPRESENTATIVE_PLAYERS)
    positions = ("QB", "RB", "WR", "TE")
    rows.extend(
        (f"fixture-{index:03d}", f"Fixture Player {index:03d}", positions[index % 4])
        for index in range(1, 240 - len(rows) + 1)
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for rank, (player_id, player_name, position) in enumerate(rows, start=1):
            writer.writerow(
                {
                    "player_id": player_id,
                    "player_name": player_name,
                    "position": position,
                    "nfl_team": "SFO",
                    "nwr_rank": str(rank),
                    "nwr_dynasty_score": f"{100 - rank / 4:.4f}",
                    "confidence_status": "fixture",
                    "warning_flags": "",
                }
            )
    return file_sha256(path)


def _universe(tmp_path: Path):
    current = tmp_path / "full_player_board_value_review_rows.csv"
    expected_hash = _write_current_board(current)
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=current,
        expected_current_hash=expected_hash,
    )
    return build_player_compare_universe(registry)


def test_governed_compare_universe_contains_veterans_across_positions(tmp_path: Path) -> None:
    universe = _universe(tmp_path)

    assert universe.loaded
    assert universe.counts == {
        "Current Player": 240,
        "Rookie Review": 73,
        "Blocked Rookie": 7,
    }
    current = universe.frame.loc[universe.frame["compare_asset_type"].eq("Current Player")]
    by_name = current.set_index("player").to_dict("index")
    for player_id, name, position in REPRESENTATIVE_PLAYERS:
        assert by_name[name]["asset_id"] == f"current:{player_id}"
        assert by_name[name]["player_id"] == player_id
        assert by_name[name]["position"] == position


def test_rookie_and_blocked_rows_remain_truthful_and_source_separated(tmp_path: Path) -> None:
    universe = _universe(tmp_path)
    rookies = universe.frame.loc[universe.frame["compare_asset_type"].eq("Rookie Review")]
    blocked = universe.frame.loc[universe.frame["compare_asset_type"].eq("Blocked Rookie")]

    assert len(rookies) == 73
    assert rookies["age"].ne("").all()
    assert rookies["source_score_value"].ne("").all()
    assert rookies["compare_source_label"].eq("Model V4 2026 Rookie Review").all()
    assert len(blocked) == 7
    assert blocked["source_rank_value"].eq("").all()
    assert blocked["source_score_value"].eq("").all()
    assert blocked["blocking_reason"].ne("").all()


def test_veteran_rookie_compare_has_no_common_scale() -> None:
    veteran = {
        "player": "Puka Nacua",
        "position": "WR",
        "compare_source_key": "Finished V1",
        "source_rank_label": "NWR Dynasty Rank",
        "source_rank_value": "1",
    }
    rookie = {
        "player": "Makai Lemon",
        "position": "WR",
        "compare_source_key": "Model V4 2026 Rookie Review",
        "source_rank_label": "Rookie Review Rank",
        "source_rank_value": "2",
    }

    mixed = build_player_compare_decision_summary(veteran, rookie)
    veteran_only = build_player_compare_decision_summary(
        veteran,
        {**veteran, "player": "CeeDee Lamb", "source_rank_value": "20"},
    )
    rookie_only = build_player_compare_decision_summary(
        rookie,
        {**rookie, "player": "Carnell Tate", "source_rank_value": "8"},
    )

    assert mixed.visible_context_read == NO_COMMON_SCALE_READ
    assert "not converted or compared" in mixed.context_note
    assert any("No common scale" in item for item in mixed.context_bullets)
    assert veteran_only.visible_context_read == "Visible board context differs"
    assert rookie_only.visible_context_read == "Visible board context differs"


def test_missing_current_board_fails_compare_universe_closed(tmp_path: Path) -> None:
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=tmp_path / "missing.csv",
    )
    universe = build_player_compare_universe(registry)

    assert not universe.loaded
    assert universe.counts["Current Player"] == 0
    assert not universe.frame["asset_id"].astype(str).str.startswith("current:").any()
    assert any("Finished V1 board missing" in error for error in universe.errors)


def test_configured_current_board_root_is_used_without_exposing_it(
    tmp_path: Path, monkeypatch
) -> None:
    configured_root = tmp_path / "configured-current-board"
    configured_root.mkdir()
    current = configured_root / "full_player_board_value_review_rows.csv"
    expected_hash = _write_current_board(current)
    monkeypatch.setenv("NWR_DYNASTY_RANKINGS_ROOT", str(configured_root))

    resolved, _label, _warnings = resolve_dynasty_rankings_path()
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=resolved,
        expected_current_hash=expected_hash,
    )
    universe = build_player_compare_universe(registry)

    assert universe.loaded
    assert universe.counts["Current Player"] == 240
    assert resolved == current
    assert registry.source_hashes["Finished V1"] == expected_hash
    assert not any(str(configured_root) in error for error in universe.errors)


def test_blocked_evidence_does_not_invent_a_rank() -> None:
    blocked = {
        "player": "Blocked Rookie",
        "position": "WR",
        "compare_source_key": "Model V4 2026 Rookie Review",
        "source_rank_label": "Not ranked",
        "source_rank_value": "",
        "blocking_reason": "Identity unresolved",
    }
    scored = {
        "player": "Scored Rookie",
        "position": "WR",
        "compare_source_key": "Model V4 2026 Rookie Review",
        "source_rank_label": "Rookie Review Rank",
        "source_rank_value": "1",
    }

    summary = build_player_compare_decision_summary(blocked, scored)

    assert summary.visible_context_read == NOT_ENOUGH_INFORMATION
    assert any(
        "read-only board context is Not enough information" in item
        for item in summary.open_review_flags
    )


def test_user_facing_source_identity_never_returns_an_absolute_path() -> None:
    windows_path = (
        r"C:\NWR_SHARED_DATA\draft_day_exports\nwr_final_draft_board_v1_frozen_20260622"
        r"\FINAL_DRAFT_BOARD_V1_FROZEN.csv"
    )
    label = governed_source_identity("Governed frozen draft-board source", windows_path)

    assert label == "Governed frozen draft-board source (FINAL_DRAFT_BOARD_V1_FROZEN.csv)"
    assert not re.search(r"[A-Za-z]:\\", label)


def test_page_wires_governed_registry_and_removes_visible_path_interpolation() -> None:
    page = PAGE.read_text(encoding="utf-8")

    assert "build_player_compare_universe(" in page
    assert "evidence_rows=_owner_evidence.rows" in page
    assert 'compare_pool["asset_id"]' in page
    assert "NO_COMMON_SCALE_NOTE" in page
    assert "render_source_of_truth_badge" not in page
    assert 'f"Source/as-of: {context.artifact_path}"' not in page
    assert 'f"{lane} props: {prop_path}"' not in page
    assert "combined score" not in page.lower()
    assert "create a winner" in page.lower()
    assert "No common scale" in NO_COMMON_SCALE_NOTE
