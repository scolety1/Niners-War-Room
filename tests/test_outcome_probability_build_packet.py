from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/outcome_probability/BUILD_PROCESS_PACKET.md"


def test_build_process_packet_exists_and_stays_sprint_1_scoped() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "Build Sprint 1 - Historical Scoring and Outcome Labels" in text
    assert "Do not create player probabilities" in text
    assert "Point-in-time training rows" in text
    assert "v0 historical base-rate engine" in text
    assert "v1 calibrated probability model" in text


def test_build_process_packet_documents_core_scoring_and_replacement_contracts() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json" in text
    assert "src/services/nwr_outcome_scoring_service.py" in text
    assert "compute_weekly_replacement_lines" in text
    assert "Use score thresholds for ties" in text


def test_build_process_packet_documents_forbidden_inputs() -> None:
    text = PACKET.read_text(encoding="utf-8")

    for phrase in (
        "ADP",
        "market rank",
        "league rank",
        "RotoWire projections/rankings/outlooks/values",
        "legacy NWR `private_score`",
        "prior NWR model outputs",
    ):
        assert phrase in text
