from src.trading_lab import (
    FUTURE_PHASE_ALLOW_RESEARCH_ONLY,
    FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL,
    FUTURE_PHASE_REJECT_PROHIBITED,
    PaperJournalEntry,
    ResearchSourceMetadata,
    WatchlistNote,
    classify_future_phase_request,
    validate_lifecycle_transition,
    validate_manual_artifact_payload,
    validate_manual_review_packet,
    validate_paper_journal_entry,
    validate_source_metadata,
    validate_watchlist_note,
)


def codes(issues):
    return {issue.code for issue in issues}


def test_valid_source_inventory_fake_example_is_accepted() -> None:
    source = ResearchSourceMetadata(
        source_id="SRC-EXMPL-001",
        name="SEC EDGAR public filings",
        category="public_company_filings",
        intended_use="education_research",
        access_method="manual public website review",
        attribution="SEC EDGAR",
        reviewed_on="2026-06-18",
    )

    assert validate_source_metadata(source) == ()


def test_invalid_source_inventory_fake_example_is_rejected() -> None:
    source = ResearchSourceMetadata(
        source_id="SRC-PAPER-001",
        name="Broker credential vault",
        category="broker_credentials",
        intended_use="education_research",
        access_method="manual note",
        attribution="not applicable",
    )

    assert "prohibited_source_category" in codes(validate_source_metadata(source))


def test_research_intake_fake_examples_accept_and_reject() -> None:
    valid = {
        "intake_id": "INTAKE-SIM-001",
        "date": "2026-06-18",
        "research_question": "What public evidence would change the SIM paper thesis?",
        "paper_only_intent": "manual research only",
        "status": "draft",
    }
    invalid = valid | {"research_question": "Use broker token before reviewing SIM."}

    assert validate_manual_artifact_payload("research_intake", valid) == ()
    assert "prohibited_broker_credential_language" in codes(
        validate_manual_artifact_payload("research_intake", invalid)
    )


def test_manual_lifecycle_fake_examples_accept_and_reject() -> None:
    assert validate_lifecycle_transition("IDEA", "SOURCE_REVIEW", "manual review") == ()
    assert "invalid_lifecycle_transition" in codes(
        validate_lifecycle_transition("draft", "executed", "execution state is invalid")
    )


def test_watchlist_fake_examples_accept_and_reject() -> None:
    valid = WatchlistNote(
        symbol="REVIEW",
        research_theme="manual source review",
        hypothesis="REVIEW may need more public evidence before any paper note.",
        public_sources=("Public exchange reference page",),
        risk_notes="Evidence may be incomplete.",
        paper_only=True,
        review_date="2026-06-18",
    )
    invalid = WatchlistNote(
        symbol="REVIEW",
        research_theme="buy now",
        hypothesis="Buy now based on this note.",
        public_sources=("Public exchange reference page",),
        risk_notes="none",
        paper_only=True,
        review_date="2026-06-18",
    )

    assert validate_watchlist_note(valid) == ()
    assert "prohibited_advice_language" in codes(validate_watchlist_note(invalid))


def test_strategy_and_risk_fake_examples_accept_and_reject() -> None:
    strategy_valid = {
        "strategy_note_id": "STRAT-FAKE-001",
        "title": "FAKE manual research hypothesis",
        "research_question": "What evidence would invalidate FAKE?",
        "hypothesis": "Paper-only hypothesis for review.",
        "evidence_sources": "Public manual source notes",
        "risks": "Evidence concentration",
        "invalidation_conditions": "Public evidence no longer supports thesis.",
        "status": "draft",
    }
    strategy_invalid = strategy_valid | {"hypothesis": "Auto-execute FAKE order."}
    risk_valid = {
        "risk_id": "RISK-FAKE-001",
        "risk_category": "evidence_quality",
        "risk_description": "One public source may be stale.",
        "severity": "medium",
        "probability": "possible",
        "mitigation_note": "Manual review cadence.",
        "status": "open",
    }
    risk_invalid = risk_valid | {"risk_description": "Based on private account balance."}

    assert validate_manual_artifact_payload("strategy_note", strategy_valid) == ()
    assert "prohibited_execution_language" in codes(
        validate_manual_artifact_payload("strategy_note", strategy_invalid)
    )
    assert validate_manual_artifact_payload("risk_journal", risk_valid) == ()
    assert "prohibited_private_account_language" in codes(
        validate_manual_artifact_payload("risk_journal", risk_invalid)
    )


def test_paper_journal_fake_examples_accept_and_reject() -> None:
    valid = PaperJournalEntry(
        journal_id="PJ-PAPER-001",
        date="2026-06-18",
        symbol_or_topic="PAPER",
        asset_type="fake_equity",
        research_question="What would this paper thesis need to prove?",
        paper_action_type="hypothetical_watch",
        hypothetical_entry_reference="manual paper reference",
        hypothetical_exit_reference="manual invalidation reference",
        position_sizing_hypothesis="hypothetical paper sizing only",
        risk_hypothesis="evidence risk",
        invalidation_condition="public source contradiction",
        outcome_review_date="2026-07-18",
        lessons_learned="pending manual review",
        status="draft",
        notes="paper-only",
    )
    invalid = PaperJournalEntry(**(valid.__dict__ | {"notes": "real-money order history"}))

    assert validate_paper_journal_entry(valid) == ()
    assert "prohibited_private_account_language" in codes(
        validate_paper_journal_entry(invalid)
    )


def test_manual_review_packet_fake_examples_accept_and_hold() -> None:
    valid = {
        "packet_id": "PACKET-REVIEW-001",
        "intake_section": "manual intake complete",
        "source_review_section": "public sources reviewed",
        "watchlist_section": "paper-only note",
        "risk_review_section": "risk reviewed",
        "paper_journal_section": "paper journal drafted",
        "closeout_section": "manual closeout pending",
    }
    missing = valid | {"source_review_section": ""}

    assert validate_manual_review_packet(valid) == ()
    assert "hold_missing_packet_section" in codes(validate_manual_review_packet(missing))


def test_blocked_work_gate_fake_examples_accept_hold_and_reject() -> None:
    assert (
        classify_future_phase_request("Draft docs-only source review checklist.")
        == FUTURE_PHASE_ALLOW_RESEARCH_ONLY
    )
    assert (
        classify_future_phase_request("Discuss future data ingestion proposal.")
        == FUTURE_PHASE_HOLD_NEEDS_EXPLICIT_APPROVAL
    )
    assert (
        classify_future_phase_request("Add broker/API order routing.")
        == FUTURE_PHASE_REJECT_PROHIBITED
    )
