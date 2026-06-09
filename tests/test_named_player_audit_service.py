from __future__ import annotations

from types import SimpleNamespace

import src.services.named_player_audit_service as service
from src.services.named_player_audit_service import build_named_player_audit


def test_named_player_audit_renders_requested_pairs(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda _path: SimpleNamespace(
            has_errors=False,
            rows_by_table={"model_outputs": _model_output_rows()},
        ),
    )
    monkeypatch.setattr(
        service,
        "build_war_board",
        lambda _path: SimpleNamespace(rows=_model_output_rows()),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            rows=_receipt_rows(),
            issues=[],
        ),
    )

    report = build_named_player_audit("pack")
    pairs = {str(row["pair"]): row for row in report.pair_rows}

    assert pairs["BTJ vs Luther Burden"]["status"] == "ready"
    assert pairs["BTJ vs Luther Burden"]["player_a"] == "Brian Thomas"
    assert pairs["Luther Burden vs Chase Brown"]["status"] == "ready"
    assert pairs["JSN vs Tee Higgins"]["status"] == "ready"
    assert pairs["Kaleb Johnson vs older fragile RB"]["status"] == "ready"
    assert pairs["Kaleb Johnson vs older fragile RB"]["player_b"] == "Derrick Henry"
    assert pairs["Kyren vs Bijan"]["status"] == "ready"
    assert pairs["Kyren vs Gibbs"]["status"] == "ready"
    assert pairs["Kyren vs Jeanty"]["status"] == "ready"
    assert any(row["pair"] == "Kyren vs Jeanty" for row in report.pair_detail_rows)


def test_named_player_audit_shows_top_receipt_contributions(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda _path: SimpleNamespace(
            has_errors=False,
            rows_by_table={"model_outputs": _model_output_rows()},
        ),
    )
    monkeypatch.setattr(
        service,
        "build_war_board",
        lambda _path: SimpleNamespace(rows=_model_output_rows()),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            rows=_receipt_rows(),
            issues=[],
        ),
    )

    report = build_named_player_audit("pack")
    jsn = [row for row in report.player_rows if row["player"] == "Jaxon Smith-Njigba"][0]
    receipt = [
        row
        for row in report.receipt_rows
        if row["pair"] == "JSN vs Tee Higgins" and row["player"] == "Jaxon Smith-Njigba"
    ][0]

    assert "target earning" in str(jsn["top_receipt_contributions"])
    assert receipt["feature"] == "target_earning_stability"
    assert receipt["imputed"] is False


def test_named_player_audit_matches_suffix_receipts_before_wrapper_rows(
    monkeypatch,
) -> None:
    rows = [_output("12519", "Luther Burden", "WR", 34, 18, 84, 86, -2)]
    receipts = [
        _receipt_with_component(
            "00-0040735",
            "Luther Burden III",
            "private_lve_value",
            "dynasty_hold_value",
            18.4,
        ),
        _receipt_with_component(
            "00-0040735",
            "Luther Burden III",
            "dynasty_hold_value",
            "target_earning_stability",
            0.0,
        ),
        _receipt_with_component(
            "00-0040735",
            "Luther Burden III",
            "dynasty_hold_value",
            "lve_structural_formula_adjustment",
            -14.0,
        ),
    ]
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda _path: SimpleNamespace(has_errors=False, rows_by_table={"model_outputs": rows}),
    )
    monkeypatch.setattr(
        service,
        "build_war_board",
        lambda _path: SimpleNamespace(rows=rows),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(rows=receipts, issues=[]),
    )

    report = build_named_player_audit("pack")
    luther = [row for row in report.player_rows if row["player"] == "Luther Burden"][0]

    assert "LVE structural adjustment -14.00" in str(luther["top_receipt_contributions"])
    assert "dynasty_hold_value" not in str(luther["top_receipt_contributions"])


def test_named_player_audit_matches_receipts_when_visible_id_differs_from_receipt_id(
    monkeypatch,
) -> None:
    rows = [_output("sleeper_jsn", "Jaxon Smith-Njigba", "WR", 8, 5, 93, 96, -3)]
    receipts = [_receipt("gsis_jsn", "Jaxon Smith-Njigba", "target_earning_stability", 11.5)]
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda _path: SimpleNamespace(has_errors=False, rows_by_table={"model_outputs": rows}),
    )
    monkeypatch.setattr(
        service,
        "build_war_board",
        lambda _path: SimpleNamespace(rows=rows),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            rows=receipts,
            issues=[],
        ),
    )

    report = build_named_player_audit("pack")
    jsn = [row for row in report.player_rows if row["player"] == "Jaxon Smith-Njigba"][0]

    assert "target earning" in str(jsn["top_receipt_contributions"])


def test_named_player_audit_marks_missing_pair_players(monkeypatch) -> None:
    rows = [
        row
        for row in _model_output_rows()
        if row["player_name"] not in {"Chase Brown", "Kaleb Johnson"}
    ]
    monkeypatch.setattr(
        service,
        "validate_data_pack",
        lambda _path: SimpleNamespace(has_errors=False, rows_by_table={"model_outputs": rows}),
    )
    monkeypatch.setattr(
        service,
        "build_war_board",
        lambda _path: SimpleNamespace(rows=rows),
    )
    monkeypatch.setattr(
        service,
        "build_player_feature_receipts",
        lambda *_args, **_kwargs: SimpleNamespace(
            rows=_receipt_rows(),
            issues=[],
        ),
    )

    report = build_named_player_audit("pack")
    pairs = {str(row["pair"]): row for row in report.pair_rows}

    assert pairs["Luther Burden vs Chase Brown"]["status"] == "missing_player"
    assert "right player" in str(pairs["Luther Burden vs Chase Brown"]["next_action"])
    assert pairs["Kaleb Johnson vs older fragile RB"]["status"] == "missing_player"


def _model_output_rows() -> list[dict[str, str]]:
    return [
        _output("btj", "Brian Thomas", "WR", 12, 7, 91, 89, 2),
        _output("luther", "Luther Burden", "WR", 34, 18, 84, 86, -2),
        _output("chase_brown", "Chase Brown", "RB", 30, 11, 82, 78, 4),
        _output("kaleb", "Kaleb Johnson", "RB", 41, 16, 78, 69, 9),
        _output("jsn", "Jaxon Smith-Njigba", "WR", 8, 5, 93, 96, -3),
        _output("tee", "Tee Higgins", "WR", 20, 11, 88, 85, 3),
        _output("kyren", "Kyren Williams", "RB", 5, 1, 94, 90, 4),
        _output("bijan", "Bijan Robinson", "RB", 3, 2, 96, 95, 1),
        _output("gibbs", "Jahmyr Gibbs", "RB", 4, 3, 95, 94, 1),
        _output("jeanty", "Ashton Jeanty", "RB", 6, 4, 92, 89, 3),
        _output("henry", "Derrick Henry", "RB", 33, 12, 80, 70, 10),
    ]


def _output(
    player_id: str,
    player: str,
    position: str,
    overall_rank: int,
    position_rank: int,
    private_score: float,
    market_score: float,
    market_edge: float,
) -> dict[str, str]:
    return {
        "player_id": player_id,
        "player_name": player,
        "position": position,
        "team": "TST",
        "asset_lifecycle": "young_nfl_bridge",
        "asset_lifecycle_label": "Young NFL Bridge",
        "overall_rank": str(overall_rank),
        "position_rank": str(position_rank),
        "position_rank_label": f"{position}{position_rank}",
        "private_score": str(private_score),
        "market_score": str(market_score),
        "market_edge_score": str(market_edge),
        "confidence_score": "84",
        "warning_status": "review_needed",
        "warning_reasons": "missing_projection",
        "model_version": "test_stats_first",
    }


def _receipt_rows() -> list[dict[str, object]]:
    return [
        _receipt("btj", "Brian Thomas", "target_earning_stability", 10.5),
        _receipt("luther", "Luther Burden", "draft_capital_prior_score", 9.5),
        _receipt("chase_brown", "Chase Brown", "workload_earning", 8.5),
        _receipt("kaleb", "Kaleb Johnson", "draft_capital_prior_score", 7.5),
        _receipt("jsn", "Jaxon Smith-Njigba", "target_earning_stability", 11.5),
        _receipt("tee", "Tee Higgins", "route_role", 8.0),
        _receipt("kyren", "Kyren Williams", "role_security", 12.0),
        _receipt("bijan", "Bijan Robinson", "age_curve", 10.0),
        _receipt("gibbs", "Jahmyr Gibbs", "first_down_td_fit", 10.0),
        _receipt("jeanty", "Ashton Jeanty", "draft_capital_prior_score", 10.0),
        _receipt("henry", "Derrick Henry", "age_curve", -6.0),
    ]


def _receipt(
    player_id: str,
    player: str,
    feature: str,
    contribution: float,
) -> dict[str, object]:
    return _receipt_with_component(player_id, player, "private_lve_value", feature, contribution)


def _receipt_with_component(
    player_id: str,
    player: str,
    component: str,
    feature: str,
    contribution: float,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player": player,
        "position": "WR",
        "component": component,
        "receipt_section_label": "NFL Production",
        "formula_feature_name": feature,
        "raw_feature_value": "80",
        "normalized_score": "80",
        "feature_weight": "10",
        "contribution": contribution,
        "source_file": "fixture.csv",
        "warning_reason": "",
        "imputed_flag": False,
    }
