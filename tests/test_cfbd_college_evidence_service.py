from __future__ import annotations

import pandas as pd
import pytest

from src.services import cfbd_college_evidence_service as college


def _rookies() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gsis_id": "00-0000001",
                "player_name": "Exact Player",
                "position": "WR",
                "draft_year": 2024,
                "draft_round": 2,
                "draft_pick": 40,
                "drafted_status": "DRAFTED",
            },
            {
                "gsis_id": "00-0000002",
                "player_name": "Undrafted Player",
                "position": "RB",
                "draft_year": 2024,
                "draft_round": None,
                "draft_pick": None,
                "drafted_status": "UNDRAFTED",
            },
        ]
    )


def _draft_rows() -> list[dict[str, object]]:
    return [
        {
            "year": 2024,
            "round": 2,
            "overall": 40,
            "collegeAthleteId": 123,
            "nflAthleteId": 456,
            "collegeTeam": "Example",
            "name": "Display Name May Differ",
            "position": "Wide Receiver",
        }
    ]


def test_identity_crosswalk_uses_unique_draft_slot_not_name() -> None:
    result = college.build_identity_crosswalk(_rookies(), _draft_rows())
    assert len(result.exact) == 1
    assert result.exact.iloc[0]["cfbd_college_athlete_id"] == "123"
    assert bool(result.exact.iloc[0]["name_used_as_identity"]) is False
    assert bool(result.exact.iloc[0]["name_agreement_diagnostic"]) is False
    assert len(result.review) == 0
    assert result.unresolved.iloc[0]["unresolved_reason"] == (
        "UNDRAFTED_NO_CFBD_DRAFT_IDENTITY"
    )


def test_duplicate_authoritative_draft_slot_fails_closed() -> None:
    rows = _draft_rows() * 2
    with pytest.raises(college.CfbdIdentityError):
        college.build_identity_crosswalk(_rookies(), rows)


def test_terminal_feature_builder_rejects_post_draft_season() -> None:
    identity = college.build_identity_crosswalk(_rookies(), _draft_rows())
    stats = [
        {
            "season": 2024,
            "playerId": "123",
            "player": "Exact Player",
            "position": "WR",
            "team": "Example",
            "conference": "Test",
            "category": "receiving",
            "statType": "YDS",
            "stat": "900",
        }
    ]
    with pytest.raises(college.CfbdEvidenceError):
        college.build_college_features(
            identity.exact,
            stat_rows=stats,
            usage_rows=[],
            ppa_rows=[],
        )


def test_terminal_feature_builder_preserves_missing_advanced_metrics() -> None:
    identity = college.build_identity_crosswalk(_rookies(), _draft_rows())
    stats = [
        {
            "season": 2023,
            "playerId": "123",
            "player": "Exact Player",
            "position": "WR",
            "team": "Example",
            "conference": "Test",
            "category": "receiving",
            "statType": "REC",
            "stat": "60",
        },
        {
            "season": 2023,
            "playerId": "123",
            "player": "Exact Player",
            "position": "WR",
            "team": "Example",
            "conference": "Test",
            "category": "receiving",
            "statType": "YDS",
            "stat": "900",
        },
    ]
    result = college.build_college_features(
        identity.exact,
        stat_rows=stats,
        usage_rows=[],
        ppa_rows=[],
    )
    assert result.iloc[0]["college_receiving_yards"] == 900
    assert result.iloc[0]["college_receiving_yards_per_reception"] == 15
    assert pd.isna(result.iloc[0]["college_usage_overall"])
    assert bool(result.iloc[0]["college_usage_present"]) is False
