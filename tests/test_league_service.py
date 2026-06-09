from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import src.services.league_service as league_service
from src.data.validators import ValidatedDataPack
from src.services.league_service import build_league_intel

SAMPLE_PACK = "sample_data/2026_pre_declaration"


def test_league_intel_uses_sample_pack_keeper_pressure() -> None:
    board = build_league_intel(SAMPLE_PACK)

    assert board.snapshot_date == "2026-08-01"
    assert board.pressure_rows[0]["team"] == "Niners"
    assert board.pressure_rows[0]["pressure_level"] == "Medium"
    assert board.pressure_rows[0]["pressure_count"] == 2
    assert board.pressure_rows[0]["forced_release_count"] == 1
    assert board.pressure_rows[0]["official_top_five_count"] == 5
    assert board.pressure_rows[0]["roster_count"] == 24
    assert board.pressure_rows[0]["protect_limit"] == 23
    assert "release decision" in str(board.pressure_rows[0]["opportunity_summary"])
    assert "forced_release_pain" in board.pressure_rows[0]
    assert board.pressure_rows[0]["likely_forced_release"] == "Luther Burden"
    assert "likely_forced_release_value" in board.pressure_rows[0]
    assert "top_five_value_gap" in board.pressure_rows[0]
    assert [row["player"] for row in board.default_release_rows] == ["Luther Burden"]
    assert board.target_rows == []
    assert board.target_categories == []
    assert board.default_release_rows[0]["availability_signal"] == "Likely Forced Release"


def test_league_targets_classify_opponent_opportunities(
    monkeypatch: MonkeyPatch,
) -> None:
    rows_by_table = {
        "rosters": [
            *_target_rows("niners", "Niners", 1, 5),
            *_target_rows("alpha", "Alpha", 6, 5),
            *_target_rows("bravo", "Bravo", 11, 5),
            *_target_rows("charlie", "Charlie", 16, 5),
        ],
        "official_rankings": [],
        "model_outputs": [
            _scored_output("niners_1", 90, 90, 82, "keep"),
            _scored_output("niners_2", 88, 88, 80, "keep"),
            _scored_output("niners_3", 86, 86, 78, "keep"),
            _scored_output("niners_4", 84, 84, 76, "keep"),
            _scored_output("niners_5", 82, 82, 74, "keep"),
            _scored_output("alpha_6", 65, 55, 80, "shop", drop_candidate_score=88),
            _scored_output("alpha_7", 92, 92, 85, "keep"),
            _scored_output("alpha_8", 72, 83, 76, "keep"),
            _scored_output("alpha_9", 45, 70, 40, "drop"),
            _scored_output("alpha_10", 82, 95, 82, "keep"),
            _scored_output("bravo_11", 86, 84, 88, "keep"),
            _scored_output("bravo_12", 66, 58, 78, "keep"),
            _scored_output("bravo_13", 52, 70, 52, "drop"),
            _scored_output("bravo_14", 80, 86, 82, "keep"),
            _scored_output("bravo_15", 70, 70, 70, "keep"),
            _scored_output("charlie_16", 95, 95, 86, "keep"),
            _scored_output("charlie_17", 90, 90, 84, "keep"),
            _scored_output("charlie_18", 85, 85, 82, "keep"),
            _scored_output("charlie_19", 80, 80, 80, "keep"),
            _scored_output("charlie_20", 72, 65, 80, "shop"),
        ],
    }
    monkeypatch.setattr(
        league_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="in-memory",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_league_intel("in-memory", protect_limit=4)
    categories = {row["player"]: row["target_category"] for row in board.target_rows}

    assert categories["Alpha 9"] == "Avoid"
    assert categories["Charlie 20"] == "Likely Forced Releases"
    assert categories["Alpha 6"] == "Model vs Market Targets"
    assert categories["Alpha 7"] == "Expensive Targets"
    assert categories["Alpha 8"] == "Expensive Targets"
    assert categories["Alpha 10"] == "Avoid"
    assert categories["Bravo 12"] == "Model vs Market Targets"
    assert categories["Bravo 15"] == "Cheap Targets"
    assert len(set(categories.values())) >= 4
    forced_signals = {
        row["player"]: row["availability_signal"] for row in board.target_rows
    }
    assert forced_signals["Alpha 9"] == "Likely Forced Release"
    assert board.rows_by_category["Avoid"]


def test_league_targets_use_acquisition_focused_category_language() -> None:
    page_text = Path("app/pages/06_league_intel.py").read_text()

    assert "Likely Forced Releases" in league_service.LEAGUE_TARGET_CATEGORIES
    assert "Cheap Targets" in league_service.LEAGUE_TARGET_CATEGORIES
    assert "Expensive Targets" in league_service.LEAGUE_TARGET_CATEGORIES
    assert "Model vs Market Targets" in league_service.LEAGUE_TARGET_CATEGORIES
    assert "Avoid" in league_service.LEAGUE_TARGET_CATEGORIES
    assert "Market Edge Targets" not in league_service.LEAGUE_TARGET_CATEGORIES
    assert "shield" not in page_text.lower()
    assert '"Likely Required Release Slot"' in page_text
    assert "Easy Non-Top-5 Drop?" not in page_text
    assert "Secondary Comparison Drop" in page_text
    assert "Pressure Diagnostics" in page_text
    assert '"Model Value"' in page_text
    assert '"Trade Market"' in page_text
    assert '"Model vs Market"' in page_text


def test_league_intel_sorts_pressure_and_uses_official_rankings(
    monkeypatch: MonkeyPatch,
) -> None:
    rows_by_table = {
        "rosters": [
            *_team_rows("alpha", "Alpha", 1, 7),
            *_team_rows("bravo", "Bravo", 6, 2),
        ],
        "official_rankings": [
            {"player_id": f"alpha_{index}", "official_rank": index}
            for index in range(1, 6)
        ],
        "model_outputs": [
            _output("alpha_1", 96),
            _output("alpha_2", 94),
            _output("alpha_3", 93),
            _output("alpha_4", 92),
            _output("alpha_5", 91),
            _output("alpha_6", 45),
            _output("alpha_7", 52),
        ]
        + [_output(f"bravo_{index}", 80 + index) for index in range(6, 8)],
    }
    monkeypatch.setattr(
        league_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="in-memory",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )

    board = build_league_intel("in-memory", protect_limit=4)

    assert [row["team"] for row in board.pressure_rows] == ["Alpha", "Bravo"]
    assert board.pressure_rows[0]["pressure_count"] == 2
    assert board.pressure_rows[1]["pressure_count"] == 0
    assert board.pressure_levels == ["High", "None"]


def test_league_intel_uses_active_stats_first_preview_for_pressure(
    monkeypatch: MonkeyPatch,
) -> None:
    rows_by_table = {
        "rosters": _team_rows("alpha", "Alpha", 1, 5),
        "official_rankings": [
            {"player_id": f"alpha_{index}", "official_rank": index}
            for index in range(1, 6)
        ],
        "model_outputs": [
            _scored_output(f"alpha_{index}", 90 + index, 90 + index, 80, "keep")
            for index in range(1, 6)
        ],
    }
    monkeypatch.setattr(
        league_service,
        "validate_data_pack",
        lambda path: ValidatedDataPack(
            data_pack_path=Path(str(path)),
            data_pack_name="in-memory",
            snapshot_date="2026-08-01",
            rows_by_table=rows_by_table,
            issues=(),
        ),
    )
    monkeypatch.setattr(
        league_service,
        "_active_stats_first_sync",
        lambda: league_service.ActiveStatsFirstSync(
            rows_by_sleeper_id={
                "alpha_5": {
                    "private_score": 45,
                    "keeper_score": 45,
                    "drop_candidate_score": 55,
                    "confidence_score": 80,
                    "recommendation": "shop",
                    "model_version": "active_preview",
                    "computed_at": "2026-05-12T10:00:00-06:00",
                    "score_source": "active_stats_first_preview",
                    "identity_match_method": "sleeper_id",
                }
            },
            preview_timestamp="2026-05-12T10:00:00-06:00",
            preview_row_count=1,
            matched_row_count=1,
            unmapped_row_count=0,
            identity_match_method="sleeper_id",
            warning="",
        ),
    )

    board = build_league_intel("in-memory", protect_limit=4)

    assert board.pressure_rows[0]["likely_forced_release"] == "Alpha 5"
    assert board.pressure_rows[0]["likely_forced_release_value"] == 45


def _team_rows(
    team_id: str,
    team_name: str,
    first_player_number: int,
    count: int,
) -> list[dict[str, object]]:
    return [
        {
            "team_id": team_id,
            "team_name": team_name,
            "player_id": f"{team_id}_{index}",
            "player_name": f"{team_name} {index}",
            "position": "RB",
            "roster_status": "rostered",
            "official_rank": None,
        }
        for index in range(first_player_number, first_player_number + count)
    ]


def _target_rows(
    team_id: str,
    team_name: str,
    first_player_number: int,
    count: int,
) -> list[dict[str, object]]:
    return [
        {
            "team_id": team_id,
            "team_name": team_name,
            "player_id": f"{team_id}_{index}",
            "player_name": f"{team_name} {index}",
            "position": "WR",
            "roster_status": "rostered",
            "official_rank": index,
        }
        for index in range(first_player_number, first_player_number + count)
    ]


def _output(player_id: str, private_score: float) -> dict[str, object]:
    return {
        "player_id": player_id,
        "private_score": private_score,
        "market_score": private_score,
        "confidence_score": 0.7,
    }


def _scored_output(
    player_id: str,
    private_score: float,
    market_score: float,
    confidence_score: float,
    recommendation: str,
    drop_candidate_score: float | None = None,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "private_score": private_score,
        "market_score": market_score,
        "market_trade_value": market_score,
        "market_edge_score": private_score - market_score,
        "keeper_score": private_score,
        "drop_candidate_score": drop_candidate_score
        if drop_candidate_score is not None
        else max(0, 100 - private_score),
        "confidence_score": confidence_score,
        "recommendation": recommendation,
        "model_version": "test_v1",
        "notes": "",
    }
