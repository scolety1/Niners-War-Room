from src.trading_lab import validate_artifact_text_fields


def codes_for(text: str) -> set[str]:
    return {
        issue.code
        for issue in validate_artifact_text_fields("cleanup_check", {"text": text})
    }


def test_wall_street_terms_are_rejected() -> None:
    terms = (
        "stock",
        "equity",
        "crypto",
        "forex",
        "broker API",
        "market-data API",
        "SEC EDGAR",
        "FRED",
        "order execution",
        "real-money trading",
        "investment advice",
    )

    for term in terms:
        assert "prohibited_wall_street_language" in codes_for(term)


def test_fantasy_trade_terms_are_not_rejected_as_wall_street_terms() -> None:
    text = (
        "Trade away a wide receiver for a rookie pick and evaluate opponent fit, "
        "keeper impact, drop pressure, roster aftermath, NWR value delta, and "
        "public fantasy market value."
    )

    assert validate_artifact_text_fields("fantasy_terms", {"text": text}) == ()
