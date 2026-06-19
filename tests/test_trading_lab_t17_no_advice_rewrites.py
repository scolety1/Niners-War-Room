from src.trading_lab import validate_artifact_text_fields


def codes_for(text: str) -> set[str]:
    return {issue.code for issue in validate_artifact_text_fields("rewrite_note", {"text": text})}


def test_unsafe_buy_sell_and_place_order_examples_are_rejected() -> None:
    assert "prohibited_advice_language" in codes_for("Buy now after reviewing EXMPL.")
    assert "prohibited_advice_language" in codes_for("Sell now before manual review.")
    assert "prohibited_execution_language" in codes_for("Place order for PAPER.")


def test_safe_research_rewrites_are_accepted() -> None:
    safe_examples = (
        "Research whether the public evidence still supports the paper thesis.",
        "Review downside evidence and invalidation notes.",
        "Add a paper-only hypothetical note for manual review.",
        "Use hypothetical paper sizing assumptions without private data.",
        "Use a manual review trigger for a hypothetical paper scenario.",
        "Frame uncertainty, risks, and invalidation conditions.",
    )

    for example in safe_examples:
        assert validate_artifact_text_fields("rewrite_note", {"text": example}) == ()


def test_broker_secret_and_private_account_examples_are_rejected() -> None:
    assert "prohibited_broker_credential_language" in codes_for("Use broker token.")
    assert "prohibited_broker_credential_language" in codes_for("Use API key.")
    assert "prohibited_private_account_language" in codes_for(
        "Based on my private brokerage account balance."
    )


def test_guaranteed_return_language_is_rejected() -> None:
    assert "prohibited_advice_language" in codes_for("This has guaranteed return.")


def test_auto_execute_language_is_rejected() -> None:
    assert "prohibited_execution_language" in codes_for(
        "Auto execute if PAPER crosses a fake threshold."
    )
