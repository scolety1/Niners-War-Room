from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from src.services.redraft_2026_rookie_projection_model_service import (
    INSUFFICIENT_HISTORY_FALLBACK_MODEL_ID,
    MODEL_STAT_COLUMNS,
    aggregate_backtest,
    attach_exact_identities,
    build_current_rookie_candidate,
    build_insufficient_history_fallback_candidate,
    normalize_name,
    score_half_ppr,
    temporal_backtest,
    uncertainty_from_predictions,
)


def _stat_row(**overrides: float) -> dict[str, float]:
    row = {column: 0.0 for column in MODEL_STAT_COLUMNS}
    row.update(overrides)
    return row


def _history() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for season in range(2012, 2016):
        for index in range(2):
            rows.append(
                {
                    "season": season,
                    "player_id": f"{season}-{index}",
                    "pfr_player_name": f"Rookie {season}-{index}",
                    "position": "RB",
                    "round": 1,
                    "pick": index + 1,
                    **_stat_row(
                        games=10 + index,
                        carries=100 + (10 * index),
                        rushing_yards=500 + (100 * index),
                        rushing_tds=4 + index,
                    ),
                }
            )
    rows.append(
        {
            "season": 2016,
            "player_id": "2016-1",
            "pfr_player_name": "Target Rookie",
            "position": "RB",
            "round": 1,
            "pick": 1,
            **_stat_row(games=12, carries=120, rushing_yards=650, rushing_tds=5),
        }
    )
    return pd.DataFrame(rows)


def test_name_normalization_is_exact_and_suffix_safe() -> None:
    assert normalize_name("Ted Hurst III") == normalize_name("Ted Hurst")
    assert normalize_name("De'Zhaun Stribling") == "dezhaunstribling"


def test_exact_identity_prefers_pfr_bridge_and_records_method() -> None:
    players = pd.DataFrame(
        [
            {
                "gsis_id": "00-1",
                "display_name": "Ted Hurst III",
                "pfr_id": "HursTe00",
                "position": "WR",
            }
        ]
    )
    draft = pd.DataFrame(
        [
            {
                "pfr_player_id": "HursTe00",
                "pfr_player_name": "Ted Hurst",
                "position": "WR",
            }
        ]
    )
    result = attach_exact_identities(draft, players).iloc[0]
    assert result["player_id"] == "00-1"
    assert result["identity_method"] == "EXACT_PFR_ID_BRIDGE"
    assert not bool(result["identity_conflict"])


def test_temporal_backtest_uses_only_prior_classes_and_component_medians() -> None:
    predictions, summaries = temporal_backtest(_history(), seasons=[2016])
    prediction = predictions.iloc[0]
    assert prediction["training_max_season"] == 2015
    assert prediction["cohort_scope"] == "POSITION_ROUND"
    assert prediction["cohort_rows"] == 8
    # Historical medians: 550 rushing yards and 4.5 touchdowns = 82 half-PPR points.
    assert prediction["predicted_points"] == 82.0
    assert summaries.iloc[-1]["season"] == 2016


def test_current_position_conflict_blocks_instead_of_coercing_projection() -> None:
    draft = pd.DataFrame(
        [
            {
                "season": 2026,
                "round": 5,
                "pick": 159,
                "team": "MIN",
                "gsis_id": None,
                "pfr_player_id": "BredMa00",
                "pfr_player_name": "Max Bredeson",
                "position": "TE",
                "college": "Michigan",
                "age": 23,
            }
        ]
    )
    players = pd.DataFrame(
        [
            {
                "gsis_id": "00-5",
                "display_name": "Max Bredeson",
                "pfr_id": "BredMa00",
                "position": "RB",
                "latest_team": "MIN",
                "status": "ACT",
                "rookie_season": 2026,
                "last_season": 2026,
            }
        ]
    )
    history = _history()
    result = build_current_rookie_candidate(
        draft,
        players,
        history,
        season=2026,
        source_as_of="2026-07-30",
        uncertainty_by_position={"TE": 20.0},
    )
    assert result.projections.empty
    assert len(result.blocked) == 1
    assert "position conflicts" in result.blocked.iloc[0]["block_reason"]


def test_currently_rostered_statuses_admit_exe_but_exclude_dev_and_preserve_status() -> None:
    """NWR next-draft rookie/insufficient-history closure (2026-09-08): the
    true-rookie pipeline gets the same real, owner-approved status widening
    as the veteran pipeline (PLAYER UNIVERSE ELIGIBILITY is separate from
    FANTASY AVAILABILITY/RISK). A real rookie on EXE/RSR/PUP is admitted;
    DEV (practice squad) stays excluded. The exact real status is preserved
    in `provenance`, never silently discarded, and never expressed as a
    fabricated projection-value or availability_probability discount."""
    draft = pd.DataFrame(
        [
            {
                "season": 2026, "round": 1, "pick": 1, "team": "MIN",
                "gsis_id": None, "pfr_player_id": "ExeRo00", "pfr_player_name": "Exe Rookie",
                "position": "RB", "college": "State", "age": 21,
            },
            {
                "season": 2026, "round": 3, "pick": 80, "team": "MIN",
                "gsis_id": None, "pfr_player_id": "DevRo00", "pfr_player_name": "Dev Rookie",
                "position": "RB", "college": "State", "age": 21,
            },
        ]
    )
    players = pd.DataFrame(
        [
            {
                "gsis_id": "00-exe-rookie", "display_name": "Exe Rookie", "pfr_id": "ExeRo00",
                "position": "RB", "latest_team": "MIN", "status": "EXE",
                "rookie_season": 2026, "last_season": 2026,
            },
            {
                "gsis_id": "00-dev-rookie", "display_name": "Dev Rookie", "pfr_id": "DevRo00",
                "position": "RB", "latest_team": "MIN", "status": "DEV",
                "rookie_season": 2026, "last_season": 2026,
            },
        ]
    )
    result = build_current_rookie_candidate(
        draft, players, _history(), season=2026, source_as_of="2026-09-08",
        uncertainty_by_position={"RB": 20.0},
    )
    admitted = set(result.projections["player_id"])
    assert admitted == {"00-exe-rookie"}
    provenance = result.projections.iloc[0]["provenance"]
    assert "current NFL roster status: EXE" in provenance
    assert result.blocked.iloc[0]["player_id"] == "00-dev-rookie"
    assert result.blocked.iloc[0]["block_reason"] == "current factual roster status is not a currently-rostered status"


def test_uncertainty_and_aggregate_are_position_specific() -> None:
    predictions, _ = temporal_backtest(_history(), seasons=[2016])
    uncertainty = uncertainty_from_predictions(predictions)
    aggregate = aggregate_backtest(predictions)
    assert set(uncertainty) == {"RB"}
    assert uncertainty["RB"] >= 0
    assert aggregate.iloc[0]["position"] == "RB"


def test_committed_rookie_packet_manifest_matches_exact_bytes() -> None:
    packet = Path(
        "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
    )
    manifest = pd.read_csv(packet / "MANIFEST.csv")
    observed = {
        row.file: hashlib.sha256((packet / row.file).read_bytes()).hexdigest()
        for row in manifest.itertuples()
    }
    expected = dict(zip(manifest["file"], manifest["sha256"], strict=True))
    assert observed == expected


def test_public_rookie_sources_pin_admitted_license_and_snapshot_receipts() -> None:
    packet = Path(
        "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
    )
    sources = pd.read_csv(packet / "SOURCE_EVIDENCE.csv").fillna("")
    public = sources[sources["source_status"].eq("PUBLIC_LOCAL_SNAPSHOT")]
    assert public["snapshot_id"].ne("").all()
    assert public["retrieved_at_utc"].eq("2026-07-30T07:24:07Z").all()
    assert public["completion_manifest_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
    assert public["license_spdx"].eq("CC-BY-4.0").all()
    assert public["license_review_result"].eq(
        "TERMS_ACCEPTED_FOR_RESEARCH_WITH_ATTRIBUTION"
    ).all()
    assert public["license_receipt_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()


def test_committed_rookie_scores_are_nonnegative_and_inside_bounds() -> None:
    packet = Path(
        "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
    )
    candidates = pd.read_csv(packet / "ROOKIE_PROJECTION_CANDIDATE.csv")
    central = candidates.apply(score_half_ppr, axis=1)
    assert central.ge(0).all()
    assert candidates["projection_low"].le(central).all()
    assert candidates["projection_high"].ge(central).all()


def _blocked_row(
    player_id: str,
    name: str,
    position: str,
    *,
    reason: str,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": name,
        "position": position,
        "team": "NEW",
        "rookie": False,
        "reason": reason,
    }


def test_insufficient_history_fallback_admits_a_brooks_class_player_with_draft_capital() -> None:
    """A current, active player (blocked by the veteran model for having no usable own
    prior-season stat line) with a real 1st-round draft record must be admitted here via
    the real, already-validated position+round rookie-year cohort median -- the Brooks-
    class gap this fallback exists to fix."""
    blocked = pd.DataFrame(
        [
            _blocked_row(
                "2024-injured",
                "Injured Sophomore",
                "RB",
                reason="no prior-season NFL stat line; persistence forecast blocked",
            )
        ]
    )
    draft = pd.DataFrame(
        [{"season": 2024, "round": 1, "pick": 1, "gsis_id": "2024-injured", "position": "RB"}]
    )
    result = build_insufficient_history_fallback_candidate(
        blocked,
        draft,
        _history(),
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"RB": 50.0},
    )
    assert result.projections["player_id"].tolist() == ["2024-injured"]
    assert result.projections.iloc[0]["source_id"] == INSUFFICIENT_HISTORY_FALLBACK_MODEL_ID
    # Real historical round-1 RB rookie-year cohort median from _history() (9 rows: 8 from
    # 2012-2015 plus the 2016 target row): 600 rushing yards, 5 TDs = 90.0 half-PPR points
    # -- the same real cohort a true rookie at the same slot would receive, never a
    # fabricated stat line for this specific player.
    assert score_half_ppr(result.projections.iloc[0]) == 90.0


def test_insufficient_history_fallback_ignores_true_rookie_blocked_rows() -> None:
    """A row blocked for being an ungoverned 2026 rookie (a different, dedicated lane)
    must never be picked up here -- only the two real 'no usable own history' reasons."""
    blocked = pd.DataFrame(
        [
            _blocked_row(
                "rookie-id",
                "True Rookie",
                "RB",
                reason="2026 rookie workload is not governed; no NFL-history projection generated",
            )
        ]
    )
    draft = pd.DataFrame(
        [{"season": 2026, "round": 1, "pick": 1, "gsis_id": "rookie-id", "position": "RB"}]
    )
    result = build_insufficient_history_fallback_candidate(
        blocked,
        draft,
        _history(),
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"RB": 50.0},
    )
    assert result.projections.empty
    assert result.blocked.empty
    assert result.identity.empty


def test_insufficient_history_fallback_leaves_undrafted_players_genuinely_unprojectable() -> None:
    """No real NFL draft-capital record means no fabricated stat line -- the player stays
    blocked with an honest reason instead of being silently dropped or guessed at."""
    blocked = pd.DataFrame(
        [
            _blocked_row(
                "undrafted-id",
                "Undrafted Player",
                "WR",
                reason="prior-season games are zero; persistence forecast blocked",
            )
        ]
    )
    draft = pd.DataFrame(
        [{"season": 2024, "round": 1, "pick": 1, "gsis_id": "some-other-id", "position": "WR"}]
    )
    result = build_insufficient_history_fallback_candidate(
        blocked,
        draft,
        _history(),
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"WR": 50.0},
    )
    assert result.projections.empty
    assert result.blocked.iloc[0]["player_id"] == "undrafted-id"
    assert "no real NFL draft-capital record" in result.blocked.iloc[0]["block_reason"]


def test_insufficient_history_fallback_blocks_a_real_position_conflict() -> None:
    blocked = pd.DataFrame(
        [
            _blocked_row(
                "conflict-id",
                "Position Conflict",
                "TE",
                reason="no prior-season NFL stat line; persistence forecast blocked",
            )
        ]
    )
    draft = pd.DataFrame(
        [{"season": 2024, "round": 3, "pick": 70, "gsis_id": "conflict-id", "position": "WR"}]
    )
    result = build_insufficient_history_fallback_candidate(
        blocked,
        draft,
        _history(),
        season=2026,
        source_as_of="2026-08-08",
        uncertainty_by_position={"TE": 50.0},
    )
    assert result.projections.empty
    assert "position conflicts" in result.blocked.iloc[0]["block_reason"]
