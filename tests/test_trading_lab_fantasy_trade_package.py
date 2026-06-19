from src.trading_lab import (
    FantasyTradePackage,
    validate_artifact_text_fields,
    validate_trade_package,
    validate_trade_package_payload,
)


def valid_package() -> FantasyTradePackage:
    return FantasyTradePackage(
        trade_mode="trade_for",
        target_player="Brandon Aiyuk",
        outgoing_player="Depth RB",
        give_assets=("Depth RB", "2027 rookie 2nd"),
        get_assets=("Brandon Aiyuk",),
        picks_included=("2027 rookie 2nd",),
        nwr_value_delta=14.5,
        public_market_fairness="public fantasy market value says this is fair",
        opponent_fit_score=7.5,
        roster_impact_score=8.0,
        keeper_impact="Improves keeper ceiling without crowding keeper slots.",
        drop_pressure_impact="Reduces drop pressure by consolidating bench value.",
        rookie_pick_context="Rookie pick cost is acceptable versus current Mock Draft tier.",
        negotiation_ladder={
            "opening_offer": "Depth RB",
            "fair_offer": "Depth RB plus 2027 rookie 3rd",
            "max_offer": "Depth RB plus 2027 rookie 2nd",
            "walk_away": "Any first-round rookie pick",
        },
        risk_flags=("injury context", "bye-week depth"),
        verdict="ready for manual fantasy trade review",
        review_status="ready_for_manual_review",
    )


def test_fantasy_trade_package_language_is_allowed() -> None:
    package = valid_package()

    assert validate_trade_package(package) == ()


def test_trade_for_trade_away_and_package_builder_modes_are_allowed() -> None:
    for mode in ("trade_for", "trade_away", "package_builder"):
        package = valid_package()
        package = FantasyTradePackage(**(package.__dict__ | {"trade_mode": mode}))

        assert validate_trade_package(package) == ()


def test_primary_fantasy_trade_questions_are_allowed() -> None:
    text = (
        "Trade for player, trade away player, dynasty trade value, rookie pick, "
        "keeper impact, drop pressure, opponent fit, roster aftermath, "
        "NWR value delta, and public fantasy market value."
    )

    assert validate_artifact_text_fields("trade_lab_prompt", {"text": text}) == ()


def test_trade_package_rejects_missing_required_fields() -> None:
    payload = valid_package().__dict__ | {"target_player": ""}

    issues = validate_trade_package_payload(payload)

    assert {issue.code for issue in issues} == {"required"}


def test_trade_package_rejects_automated_decisioning() -> None:
    payload = valid_package().__dict__ | {
        "verdict": "Auto-accept and submit trade if the other roster matches."
    }

    issues = validate_trade_package_payload(payload)

    assert "prohibited_automated_decisioning" in {issue.code for issue in issues}
