from src.trading_lab import (
    FUTURE_PHASE_ALLOW_RESEARCH_ONLY,
    FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL,
    FUTURE_PHASE_REJECT_PROHIBITED,
    classify_future_phase_request,
    validate_future_phase_request,
)


def test_future_phase_gate_allows_manual_research_only_request() -> None:
    request = (
        "Create a paper-only checklist for manual source review using fake examples, "
        "research questions, risk notes, and lessons learned."
    )

    assert classify_future_phase_request(request) == FUTURE_PHASE_ALLOW_RESEARCH_ONLY
    assert validate_future_phase_request(request) == ()


def test_future_phase_gate_holds_data_ingestion_before_approval() -> None:
    request = "Propose data ingestion for public market data after a later review gate."

    issues = validate_future_phase_request(request)

    assert classify_future_phase_request(request) == FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL
    assert issues[0].code == "hold_needs_explicit_approval"


def test_future_phase_gate_holds_backtesting_implementation_before_approval() -> None:
    request = "Build backtesting implementation and simulation tooling for fake examples."

    issues = validate_future_phase_request(request)

    assert classify_future_phase_request(request) == FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL
    assert issues[0].code == "hold_needs_explicit_approval"


def test_future_phase_gate_rejects_broker_api_and_orders() -> None:
    request = "Add broker API support so the operator can place orders."

    issues = validate_future_phase_request(request)

    assert classify_future_phase_request(request) == FUTURE_PHASE_REJECT_PROHIBITED
    assert issues[0].code == "reject_prohibited_work"


def test_future_phase_gate_rejects_credentials_and_private_account_data() -> None:
    request = "Use an API key, broker token, and private brokerage account balance."

    issues = validate_future_phase_request(request)

    assert classify_future_phase_request(request) == FUTURE_PHASE_REJECT_PROHIBITED
    assert issues[0].code == "reject_prohibited_work"


def test_future_phase_gate_rejects_fantasy_lane_changes() -> None:
    request = "Update Outcome and Mock Draft behavior from Trading Lab notes."

    issues = validate_future_phase_request(request)

    assert classify_future_phase_request(request) == FUTURE_PHASE_REJECT_PROHIBITED
    assert issues[0].code == "reject_prohibited_work"

