from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from src.services.governed_asset_registry_service import (
    EXPECTED_BLOCKED,
    file_sha256,
    finished_v1_coverage_counts,
    load_governed_asset_registry,
)

ROOT = Path(__file__).resolve().parents[1]


def _current_board(path: Path) -> str:
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for rank in range(1, 241):
            writer.writerow(
                {
                    "player_id": f"p{rank:03d}",
                    "player_name": f"Player {rank:03d}",
                    "position": ("QB", "RB", "WR", "TE")[(rank - 1) % 4],
                    "nfl_team": "SFO",
                    "nwr_rank": rank,
                    "nwr_dynasty_score": f"{100 - rank / 3:.4f}",
                    "confidence_status": "fixture",
                    "warning_flags": "",
                }
            )
    return file_sha256(path)


def test_registry_contains_all_governed_asset_types(tmp_path: Path) -> None:
    current = tmp_path / "finished-v1.csv"
    expected_hash = _current_board(current)
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=current,
        expected_current_hash=expected_hash,
    )

    assert registry.errors == ()
    assert registry.counts == {
        "Current Player": 240,
        "Rookie Review": 73,
        "Blocked Rookie": 7,
        "Draft Pick": 50,
        "Future Pick": 9,
    }
    assert len(registry.rows) == 379
    assert len({row["asset_id"] for row in registry.rows}) == 379


def test_registry_keeps_sources_and_scales_separate(tmp_path: Path) -> None:
    current = tmp_path / "finished-v1.csv"
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=current,
        expected_current_hash=_current_board(current),
    )
    current_row = next(row for row in registry.rows if row["asset_type"] == "Current Player")
    rookie = next(row for row in registry.rows if row["asset_type"] == "Rookie Review")
    pick = next(row for row in registry.rows if row["asset_type"] == "Draft Pick")
    future = next(row for row in registry.rows if row["asset_type"] == "Future Pick")

    assert current_row["source_label"] == "Finished V1"
    assert current_row["authority_status"] == "Production"
    assert rookie["authority_status"] == "Review-Only"
    assert "only within the 2026 Rookie Review" in rookie["comparison_scope"]
    assert pick["score_label"] == "No common value"
    assert "no player-value equivalence" in pick["comparison_scope"]
    assert future["asset_id"] == "pick:2027:1st"
    assert future["rank_value"] == ""
    assert future["authority_status"] == "Context-Only"
    assert all("recommendation" not in row for row in registry.rows)


def test_all_seven_blocked_rookies_are_visible(tmp_path: Path) -> None:
    current = tmp_path / "finished-v1.csv"
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=current,
        expected_current_hash=_current_board(current),
    )
    blocked = [row for row in registry.rows if row["asset_type"] == "Blocked Rookie"]

    assert {row["asset_name"] for row in blocked} == EXPECTED_BLOCKED
    assert all(row["authority_status"] == "Blocked - Visible" for row in blocked)
    assert all(row["rank_value"] == "" and row["score_value"] == "" for row in blocked)


def test_current_board_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    current = tmp_path / "finished-v1.csv"
    _current_board(current)
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=current,
        expected_current_hash="0" * 64,
    )

    assert "Finished V1 hash mismatch" in registry.errors


def test_missing_current_board_does_not_fabricate_players(tmp_path: Path) -> None:
    registry = load_governed_asset_registry(
        repo_root=ROOT,
        current_board_path=tmp_path / "missing.csv",
    )

    assert registry.counts["Current Player"] == 0
    assert registry.counts["Rookie Review"] == 73
    assert registry.errors[0].startswith("Finished V1 board missing:")


def test_finished_v1_coverage_separates_ranked_skill_players_and_kickers() -> None:
    frame = pd.DataFrame(
        [
            *(
                {"position": ("QB", "RB", "WR", "TE")[index % 4], "nwr_rank": str(index + 1)}
                for index in range(232)
            ),
            *({"position": "K", "nwr_rank": ""} for _ in range(8)),
        ]
    )
    assert finished_v1_coverage_counts(frame) == {
        "structural_assets": 240,
        "ranked_skill_players": 232,
        "unranked_kickers": 8,
    }


def test_asset_explorer_and_rookie_board_are_read_only_labeled_pages() -> None:
    explorer = (ROOT / "app/pages/47_asset_explorer_v1.py").read_text(encoding="utf-8")
    rookie = (ROOT / "app/pages/48_rookie_board_review_v1.py").read_text(encoding="utf-8")

    assert '"Asset Explorer"' in explorer
    assert "range(0, len(count_items), 4)" in explorer
    assert "st.columns(len(batch))" in explorer
    assert "zip(metrics, registry.counts, strict=True)" not in explorer
    assert '"Browse every governed dynasty asset"' in explorer
    assert "No common scale" in explorer
    assert "No recommendation" in explorer
    assert "st.button(" not in explorer
    assert '"2026 Rookie Review"' in rookie
    assert "all 80 drafted prospects" in rookie
    assert "Why this rank" in rookie
    assert "st.button(" not in rookie
