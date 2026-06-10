from __future__ import annotations

from pathlib import Path

from src.services.model_v4_wr_qb_v2_candidate_service import (
    DEFAULT_FULL_PLAYER_BOARD_ROWS,
    MODEL_VERSION,
    build_wr_qb_v2_candidate,
    write_wr_qb_v2_candidate_exports,
)
from src.services.player_detail_card_service import build_player_detail_card_payload


def test_candidate_build_is_explicit_and_shadowed_from_latest() -> None:
    result = build_wr_qb_v2_candidate()

    assert result.production_hash_before == result.production_hash_after
    assert result.candidate_hash != result.production_hash_before
    assert all(row["candidate_model_version"] == MODEL_VERSION for row in result.rows)
    assert _summary_value(result, "active_production_changed") == "false"


def test_candidate_writes_to_candidate_folder_without_mutating_latest(tmp_path: Path) -> None:
    before = DEFAULT_FULL_PLAYER_BOARD_ROWS.read_bytes()
    result = build_wr_qb_v2_candidate()

    paths = write_wr_qb_v2_candidate_exports(output_root=tmp_path, result=result)

    assert paths.full_candidate_board == tmp_path / "full_player_board_value_review_rows.csv"
    assert paths.top_40_diff.exists()
    assert paths.guardrail_report.exists()
    assert DEFAULT_FULL_PLAYER_BOARD_ROWS.read_bytes() == before


def test_candidate_guardrails_and_coverage_pass() -> None:
    result = build_wr_qb_v2_candidate()
    gates = {row["gate"]: row for row in result.guardrails}

    for gate in (
        "banned_scoring_input_count",
        "team_roster_tags_used_as_inputs",
        "legacy_active_pack_primary_score_used",
        "active_rows",
        "scored_qb_rb_wr_te",
        "unscored_kickers",
        "stale_71_player_cache",
        "players_moved_more_than_12",
        "players_moved_more_than_24",
        "non_elite_qb_suspicious_lifts",
        "aging_wr_generic_boosts",
        "te_score_changes",
        "rb_score_changes",
        "historical_top24_hit_rate",
        "historical_top24_bust_rate",
        "qb_v1_false_positive_fixed",
    ):
        assert gates[gate]["status"] == "pass"

    assert _summary_value(result, "candidate_rows") == 240
    assert _summary_value(result, "guardrail_failures") == 0


def test_candidate_uses_no_banned_input_receipts() -> None:
    result = build_wr_qb_v2_candidate()
    blocked = (
        "market_rank",
        "league_rank",
        "adp",
        "legacy_active_pack_score",
        "private_score",
        "projection",
        "rotowire_rank",
        "prior_draft",
        "is_my_team",
        "roster_status",
    )

    for row in result.rows:
        receipts = "|".join(
            str(row.get(column, ""))
            for column in (
                "candidate_evidence_fields_used",
                "candidate_source_policy",
            )
        )
        evidence_fields = str(row.get("candidate_evidence_fields_used", ""))
        assert not any(fragment in evidence_fields for fragment in blocked)
        assert "legacy_blocked" in receipts


def test_candidate_wr_qb_v2_behavior_is_narrow() -> None:
    result = build_wr_qb_v2_candidate()

    assert _candidate_adjustment(result, "CeeDee Lamb") > 0
    assert _candidate_adjustment(result, "Justin Jefferson") > 0
    assert _candidate_adjustment(result, "DeVonta Smith") > 0
    assert _candidate_adjustment(result, "Jameson Williams") == 0
    assert _candidate_adjustment(result, "Stefon Diggs") == 0
    assert _candidate_adjustment(result, "Davante Adams") == 0
    assert _candidate_adjustment(result, "Patrick Mahomes") > 0
    assert _candidate_adjustment(result, "Jalen Hurts") > 0
    assert _candidate_adjustment(result, "Jared Goff") == 0
    assert _candidate_adjustment(result, "Baker Mayfield") == 0
    assert _candidate_adjustment(result, "Jaxson Dart") == 0


def test_candidate_does_not_change_rb_or_te_scores() -> None:
    result = build_wr_qb_v2_candidate()

    for row in result.watch_row_diff:
        if row["position"] in {"RB", "TE"}:
            assert float(row["score_delta"]) == 0.0


def test_player_detail_card_shows_candidate_reasons_only_for_candidate_rows() -> None:
    result = build_wr_qb_v2_candidate()
    candidate = _row(result.rows, "CeeDee Lamb")
    payload = build_player_detail_card_payload(candidate, context="rankings")
    metrics = {metric.label: metric for metric in payload.private_model_metrics}

    assert "Candidate Model" in metrics
    assert metrics["Candidate Model"].value == MODEL_VERSION
    assert metrics["WR/QB v2 Reason Codes"].value
    assert metrics["WR/QB v2 Adjustment"].note == "candidate-only"

    production_payload = build_player_detail_card_payload(
        {
            "player": "CeeDee Lamb",
            "position": "WR",
            "nwr_dynasty_score": "48.5992",
            "nwr_rank": "23",
        },
        context="rankings",
    )
    assert all(
        metric.label != "Candidate Model"
        for metric in production_payload.private_model_metrics
    )


def _row(rows: tuple[dict[str, object], ...], player: str) -> dict[str, object]:
    return next(row for row in rows if row["player_name"] == player)


def _candidate_adjustment(result: object, player: str) -> float:
    return float(_row(result.rows, player)["candidate_adjustment"] or 0.0)


def _summary_value(result: object, metric: str) -> object:
    return next(row["value"] for row in result.summary_rows if row["metric"] == metric)
