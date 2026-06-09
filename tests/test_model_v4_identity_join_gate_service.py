from __future__ import annotations

from src.services.model_v4_identity_join_gate_service import (
    build_identity_join_lookup,
    identity_join_gate,
    identity_join_key,
    normalize_identity_name,
)


def test_identity_join_key_normalizes_suffixes_and_position() -> None:
    key = identity_join_key({"player_name": "Brian Thomas Jr.", "position": "wr"})

    assert key == ("brianthomas", "WR")
    assert normalize_identity_name("Brian Thomas Jr.") == "brianthomas"


def test_duplicate_identity_join_key_forces_manual_decision() -> None:
    lookup = build_identity_join_lookup(
        [
            {"player_name": "Keenan Allen", "position": "WR", "score": "41"},
            {"player_name": "Keenan Allen", "position": "WR", "score": "42"},
        ],
        source_name="current_player_value_review_rows.csv",
    )

    gate = identity_join_gate(("keenanallen", "WR"), lookup)

    assert ("keenanallen", "WR") in lookup.duplicate_keys
    assert ("keenanallen", "WR") not in lookup.rows_by_key
    assert gate.identity_uncertain is True
    assert gate.manual_decision_required is True
    assert "duplicate_identity_join_key" in gate.warning_flags


def test_unmatched_identity_join_key_forces_manual_decision() -> None:
    lookup = build_identity_join_lookup(
        [{"player_name": "Keenan Allen", "position": "WR"}],
        source_name="current_player_value_review_rows.csv",
    )

    gate = identity_join_gate(("dariusslayton", "WR"), lookup)

    assert gate.identity_uncertain is True
    assert gate.manual_decision_required is True
    assert "unmatched_identity_join_key" in gate.warning_flags


def test_clean_identity_join_key_passes_without_manual_gate() -> None:
    lookup = build_identity_join_lookup(
        [{"player_name": "Keenan Allen", "position": "WR"}],
        source_name="current_player_value_review_rows.csv",
    )

    gate = identity_join_gate(("keenanallen", "WR"), lookup)

    assert gate.identity_uncertain is False
    assert gate.manual_decision_required is False
    assert gate.warning_flags == ()
