from pathlib import Path


ROSTER_PATH = Path("docs/model_v4/NAMED_PLAYER_AUDIT_ROSTER_20260605.md")


def test_named_player_audit_roster_has_balanced_subject_count_and_categories() -> None:
    text = ROSTER_PATH.read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if line.startswith("| A")]

    assert len(rows) == 80
    for required in (
        "elite_young_wr",
        "elite_young_rb",
        "aging_wr",
        "aging_rb",
        "legacy_leak_sentinel",
        "low_evidence",
        "one_qb_qb",
        "no_premium_te",
        "rookie_top_cluster",
        "rookie_low_evidence",
        "pick_ladder",
        "manual_only_pick",
    ):
        assert required in text


def test_named_player_audit_roster_preserves_review_only_guardrails() -> None:
    text = ROSTER_PATH.read_text(encoding="utf-8")

    for required in (
        "does not change formulas",
        "does not change active rankings",
        "Do not tune formulas",
        "Do not use this roster as rankings",
        "legacy score must remain comparison-only",
        "2026 1.03",
        "2026 5.04",
        "Keenan Allen",
        "Christian McCaffrey",
        "Trey McBride",
        "Jake Ferguson",
        "Jeremiyah Love",
    ):
        assert required in text
