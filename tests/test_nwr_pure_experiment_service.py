from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.services.nwr_pure_experiment_service import (
    DecisionReceipt,
    ExperimentFreezeReceipt,
    NwrPureExperimentError,
    ReceiptCorrectionRecord,
    append_correction_record,
    append_decision_receipt,
    build_freeze_receipt_from_repo_state,
    build_git_provenance,
    build_league_profile_hash,
    freeze_experiment,
    hash_player_universe,
    load_freeze_receipt,
    read_correction_records,
    read_decision_receipts,
    run_pre_draft_check,
)
from src.services.redraft_engine_v1_service import (
    DraftContext,
    LeagueProfile,
    RankingResult,
    RosterSettings,
    ScoringSettings,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _freeze_receipt(experiment_id: str = "nwr-pure-001") -> ExperimentFreezeReceipt:
    return ExperimentFreezeReceipt(
        experiment_id=experiment_id,
        frozen_at_utc="2026-09-05T18:00:00+00:00",
        app_branch="work/nwr-draft-upgrade-hq-v1-20260903",
        app_head="06adaa304c8093e659f12c942184bbc41731f5fe",
        app_tree="422451c907b0bf3a6e47561fad71b4482df4fe9e",
        model_sha="fixture",
        player_universe_sha="e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25",
        player_universe_row_count=608,
        player_universe_valid_until="2026-09-06",
        league_profile_hash=build_league_profile_hash({"team_count": 16, "qb": 1}),
        market_snapshot_sha="",
        identity_registry_sha="NOT_YET_IMPLEMENTED",
        algorithm_version="R2_FLEX_AWARE_REPLACEMENT",
        authority_label="REDRAFT V1 - REVIEW",
        team_score_version="shadow-team-score-v1",
        championship_equity_version="shadow-championship-equity-v1",
        pick_score_version="shadow-pick-score-v1",
        source_as_of="2026-08-08",
    )


def _decision_receipt(
    pick_number: int = 1, *, experiment_id: str = "nwr-pure-001"
) -> DecisionReceipt:
    return DecisionReceipt(
        experiment_id=experiment_id,
        timestamp_utc="2026-09-05T19:00:00+00:00",
        pick_number=pick_number,
        round=1,
        owner_slot=9,
        available_player_universe_hash=hash_player_universe(["RB-0", "WR-0", "QB-0"]),
        roster_before=(),
        production_nwr_recommendation="RB-0",
        optimizer_recommendation="RB-0",
        candidate_set=("RB-0", "WR-0", "QB-0"),
        player_score_by_candidate={"RB-0": 399.0, "WR-0": 350.0, "QB-0": 399.0},
        team_score_before=None,
        team_score_after_by_candidate={"RB-0": 80.0, "WR-0": 60.0, "QB-0": 55.0},
        championship_equity_before=None,
        championship_equity_after_by_candidate={"RB-0": 0.15, "WR-0": 0.10, "QB-0": 0.08},
        equity_gain_by_candidate={"RB-0": 0.07, "WR-0": 0.02, "QB-0": 0.0},
        cost_of_waiting_by_candidate={"RB-0": 20.0, "WR-0": 0.0, "QB-0": 0.0},
        pick_score_by_candidate={"RB-0": 100.0, "WR-0": 40.0, "QB-0": 0.0},
        simulation_assumptions={"regular_season_weeks": 14},
        simulation_count=200,
        uncertainty={"championship_equity_standard_error": 0.03},
        selected_player="RB-0",
        decision_policy="OPTIMIZER",
        fallback_reason=None,
        owner_override=False,
        override_reason=None,
        factual_alerts=(),
        external_comparators={},
    )


def test_freeze_experiment_writes_once_and_refuses_a_second_freeze(tmp_path: Path) -> None:
    receipt = _freeze_receipt()
    path = freeze_experiment(tmp_path, receipt)
    assert path.is_file()
    with pytest.raises(NwrPureExperimentError, match="already frozen"):
        freeze_experiment(tmp_path, receipt)


def test_freeze_receipt_round_trips(tmp_path: Path) -> None:
    receipt = _freeze_receipt()
    freeze_experiment(tmp_path, receipt)
    reloaded = load_freeze_receipt(tmp_path, "nwr-pure-001")
    assert reloaded == receipt


def test_load_freeze_receipt_returns_none_when_not_frozen(tmp_path: Path) -> None:
    assert load_freeze_receipt(tmp_path, "does-not-exist") is None


def test_hash_player_universe_is_order_independent_and_deterministic() -> None:
    a = hash_player_universe(["RB-0", "WR-0", "QB-0"])
    b = hash_player_universe(["QB-0", "RB-0", "WR-0"])
    assert a == b
    assert a == hash_player_universe(["RB-0", "WR-0", "QB-0"])  # deterministic


def test_league_profile_hash_changes_when_profile_changes() -> None:
    a = build_league_profile_hash({"team_count": 10})
    b = build_league_profile_hash({"team_count": 16})
    assert a != b


def test_append_decision_receipt_and_read_back(tmp_path: Path) -> None:
    append_decision_receipt(tmp_path, _decision_receipt(1))
    append_decision_receipt(tmp_path, _decision_receipt(2))
    receipts = read_decision_receipts(tmp_path, "nwr-pure-001")
    assert [r["pick_number"] for r in receipts] == [1, 2]
    assert receipts[0]["selected_player"] == "RB-0"


def test_append_decision_receipt_refuses_a_duplicate_pick_number(tmp_path: Path) -> None:
    append_decision_receipt(tmp_path, _decision_receipt(5))
    with pytest.raises(NwrPureExperimentError, match="already has a decision receipt"):
        append_decision_receipt(tmp_path, _decision_receipt(5))


def test_append_decision_receipt_validates_fallback_reason(tmp_path: Path) -> None:
    bad = _decision_receipt(1)
    bad = DecisionReceipt(
        **{
            **bad.__dict__,
            "decision_policy": "PRODUCTION_FALLBACK",
            "fallback_reason": "MADE_UP_REASON",
        }
    )
    with pytest.raises(NwrPureExperimentError, match="PRODUCTION_FALLBACK requires"):
        append_decision_receipt(tmp_path, bad)


def test_append_decision_receipt_requires_override_reason_when_overridden(tmp_path: Path) -> None:
    bad = _decision_receipt(1)
    bad = DecisionReceipt(**{**bad.__dict__, "owner_override": True, "override_reason": None})
    with pytest.raises(NwrPureExperimentError, match="requires a non-empty override_reason"):
        append_decision_receipt(tmp_path, bad)


def test_append_decision_receipt_accepts_a_valid_fallback(tmp_path: Path) -> None:
    fallback = _decision_receipt(1)
    fallback = DecisionReceipt(
        **{
            **fallback.__dict__,
            "decision_policy": "PRODUCTION_FALLBACK",
            "fallback_reason": "NO_VALID_CANDIDATE",
        }
    )
    append_decision_receipt(tmp_path, fallback)
    receipts = read_decision_receipts(tmp_path, "nwr-pure-001")
    assert receipts[0]["fallback_reason"] == "NO_VALID_CANDIDATE"


def test_correction_record_never_touches_the_original_decision_receipt(tmp_path: Path) -> None:
    append_decision_receipt(tmp_path, _decision_receipt(3))
    original = read_decision_receipts(tmp_path, "nwr-pure-001")[0]
    record = ReceiptCorrectionRecord(
        experiment_id="nwr-pure-001",
        timestamp_utc="2026-09-05T20:00:00+00:00",
        original_pick_number=3,
        reason="Operator mis-typed the player during rapid capture.",
        correction_type="REPLACE_PICK",
        detail={"from_player_id": "RB-0", "to_player_id": "RB-1"},
    )
    append_correction_record(tmp_path, record)
    unchanged = read_decision_receipts(tmp_path, "nwr-pure-001")[0]
    assert unchanged == original  # the original receipt is byte-for-byte untouched
    corrections = read_correction_records(tmp_path, "nwr-pure-001")
    assert len(corrections) == 1
    assert corrections[0]["original_pick_number"] == 3
    assert corrections[0]["correction_type"] == "REPLACE_PICK"


def test_read_decision_receipts_empty_when_never_written(tmp_path: Path) -> None:
    assert read_decision_receipts(tmp_path, "never-existed") == []
    assert read_correction_records(tmp_path, "never-existed") == []


def test_pre_draft_check_ready_when_everything_passes() -> None:
    result = run_pre_draft_check(
        player_universe_current=True,
        projection_authority_valid=True,
        league_profile_valid=True,
        roster_rules_valid=True,
        market_snapshot_available=True,
        identity_registry_healthy=True,
        kdst_available=True,
        checkpoint_path_valid=True,
        decision_logger_writable=True,
        draft_state_writable=True,
        sync_ready_or_manual_fallback_ready=True,
    )
    assert result.ready is True
    assert result.verdict == "READY_FOR_NWR_PURE"
    assert result.reasons == {}


def test_pre_draft_check_blocked_reports_exact_failing_reasons() -> None:
    result = run_pre_draft_check(
        player_universe_current=False,
        player_universe_reason="current.manifest.json valid_until 2026-09-03 has passed.",
        projection_authority_valid=True,
        league_profile_valid=True,
        roster_rules_valid=True,
        market_snapshot_available=True,
        identity_registry_healthy=True,
        kdst_available=True,
        checkpoint_path_valid=True,
        decision_logger_writable=True,
        draft_state_writable=True,
        sync_ready_or_manual_fallback_ready=True,
    )
    assert result.ready is False
    assert result.verdict == "BLOCKED"
    assert set(result.reasons.keys()) == {"PLAYER_UNIVERSE_CURRENT"}
    assert "valid_until" in result.reasons["PLAYER_UNIVERSE_CURRENT"]


# --- Real repo-state freeze receipt builder (section 27) -------------------


def _init_git_repo(path: Path) -> None:
    env_args = ["-c", "user.email=test@example.com", "-c", "user.name=Test"]
    subprocess.run(["git", *env_args, "init", "-q"], cwd=path, check=True)
    (path / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", *env_args, "add", "seed.txt"], cwd=path, check=True)
    subprocess.run(
        ["git", *env_args, "commit", "-q", "-m", "seed commit"], cwd=path, check=True
    )


def test_build_git_provenance_against_the_real_worktree_returns_real_values() -> None:
    provenance = build_git_provenance(REPO_ROOT)
    assert provenance["app_branch"] != "UNKNOWN"
    assert len(provenance["app_head"]) == 40
    assert all(c in "0123456789abcdef" for c in provenance["app_head"])
    # app_tree always starts with the real 40-hex-char tree object sha,
    # optionally followed by the dirty-state marker -- both are valid
    # depending on whether this exact test run has uncommitted changes.
    tree_sha = provenance["app_tree"].split("+UNCOMMITTED_CHANGES:")[0]
    assert len(tree_sha) == 40
    assert all(c in "0123456789abcdef" for c in tree_sha)


def test_build_git_provenance_on_a_clean_repo_has_no_dirty_marker(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    provenance = build_git_provenance(tmp_path)
    assert "+UNCOMMITTED_CHANGES:" not in provenance["app_tree"]
    assert len(provenance["app_tree"]) == 40


def test_build_git_provenance_on_a_dirty_repo_carries_the_dirty_marker(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "seed.txt").write_text("changed\n", encoding="utf-8")
    provenance = build_git_provenance(tmp_path)
    assert "+UNCOMMITTED_CHANGES:" in provenance["app_tree"]
    tree_sha, _, dirty_hash = provenance["app_tree"].partition("+UNCOMMITTED_CHANGES:")
    assert len(tree_sha) == 40
    assert len(dirty_hash) == 64  # sha256 hex digest


def test_build_git_provenance_on_a_non_repo_directory_is_unknown(tmp_path: Path) -> None:
    provenance = build_git_provenance(tmp_path / "not-a-git-repo-at-all")
    assert provenance == {"app_branch": "UNKNOWN", "app_head": "UNKNOWN", "app_tree": "UNKNOWN"}


def _synthetic_ranking() -> RankingResult:
    profile = LeagueProfile(
        "fixture-league", "Fixture League", 2026, 10,
        RosterSettings(k=1, dst=1, bench_size=6), ScoringSettings(reception=1),
        DraftContext(rounds=15, draft_slot=1),
    )
    return RankingResult(profile, (), (), (), "2026-08-17T00:00:00+00:00", "fixture-sha-abc123")


def test_build_freeze_receipt_from_repo_state_assembles_a_real_receipt(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    ranking = _synthetic_ranking()
    profile_document = {"team_count": 10, "qb": 1}
    receipt = build_freeze_receipt_from_repo_state(
        tmp_path,
        experiment_id="nwr-pure-001",
        frozen_at_utc="2026-09-05T18:00:00+00:00",
        ranking=ranking,
        profile_document=profile_document,
        player_universe_sha="e483caae" * 8,
        player_universe_row_count=608,
        player_universe_valid_until="2026-09-06",
    )
    assert receipt.experiment_id == "nwr-pure-001"
    assert receipt.model_sha == "fixture-sha-abc123"
    assert receipt.source_as_of == "2026-08-17T00:00:00+00:00"
    assert receipt.league_profile_hash == build_league_profile_hash(profile_document)
    assert receipt.algorithm_version == "R2_FLEX_AWARE_REPLACEMENT"
    assert receipt.authority_label == "REDRAFT V1 - REVIEW"
    assert receipt.team_score_version == "shadow-team-score-v1"
    assert receipt.championship_equity_version == "shadow-championship-equity-v1"
    assert receipt.pick_score_version == "shadow-pick-score-v1"
    assert receipt.identity_registry_sha == "NOT_YET_IMPLEMENTED"
    assert len(receipt.app_head) == 40
    assert "+UNCOMMITTED_CHANGES:" not in receipt.app_tree  # freshly committed, clean repo

    # The assembled receipt is itself a real, freezable ExperimentFreezeReceipt.
    path = freeze_experiment(tmp_path / "store", receipt)
    assert path.is_file()
    assert load_freeze_receipt(tmp_path / "store", "nwr-pure-001") == receipt
