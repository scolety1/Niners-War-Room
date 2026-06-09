from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/model_v4/FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _packet_text() -> str:
    return PACKET.read_text(encoding="utf-8")


def test_formula_candidate_packet_is_proposal_only() -> None:
    text = _packet_text()

    required_phrases = [
        "This packet is proposal-only.",
        "Do not patch formulas from this packet.",
        "Do not implement these candidates in this packet.",
        "Do not tune formulas from this packet.",
        "not an instruction to change",
        "Require human approval before any app-facing promotion.",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_formula_candidate_packet_lists_expected_candidates() -> None:
    text = _packet_text()

    required_candidates = [
        "FC01",
        "No-premium TE ceiling clarity",
        "FC02",
        "1QB spread and cap clarity",
        "FC03",
        "RB/WR cross-position balance",
        "FC04",
        "Veteran age/status confidence shape",
        "FC05",
        "Young-player evidence sensitivity",
        "FC06",
        "Rookie source-limited prior handling",
        "FC07",
        "Pick-neighborhood explanation and comparison shape",
    ]

    for candidate in required_candidates:
        assert candidate in text


def test_formula_candidate_packet_names_evidence_and_sentinels() -> None:
    text = _packet_text()

    required_items = [
        "TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md",
        "QB_1QB_DISCIPLINE_REPORT_20260605.md",
        "RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md",
        "VETERAN_AGE_WINDOW_AUDIT_20260605.md",
        "YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md",
        "ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md",
        "PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md",
        "DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md",
        "Keenan Allen",
        "82.4",
        "Darius Slayton",
        "78.88",
        "Jeremiyah Love",
        "Carnell Tate",
        "Jordyn Tyson",
        "Fernando Mendoza",
        "Kenyon Sadiq",
        "2026 5.04",
    ]

    for item in required_items:
        assert item in text


def test_formula_candidate_packet_preserves_forbidden_scope() -> None:
    text = _packet_text()

    forbidden_scope_guardrails = [
        "does not implement experiments",
        "change model weights",
        "change veteran age curves",
        "change rookie weights",
        "change pick baselines",
        "change VORP",
        "change replacement formulas",
        "change market-gap thresholds",
        "change confidence cap magnitudes",
        "change startup-slot conversion",
        "Do not add ADP",
        "Do not convert review labels into final trade",
    ]

    for guardrail in forbidden_scope_guardrails:
        assert guardrail in text


def test_refinement_queue_marks_r25_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r25_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R25 |")
    ]
    assert len(r25_lines) == 1
    r25 = r25_lines[0]

    assert "| Done |" in r25
    assert "FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md" in r25
    assert "proposal-only candidate areas" in r25
    assert "no implementation" in r25
