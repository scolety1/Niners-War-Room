import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/model_v4/USER_JUDGMENT_WORKSHEET_20260605.md"
CSV_PATH = ROOT / "docs/model_v4/USER_JUDGMENT_WORKSHEET_20260605.csv"
QUEUE = ROOT / "docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md"


def _doc_text() -> str:
    return DOC.read_text(encoding="utf-8")


def _rows() -> list[dict[str, str]]:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_user_judgment_worksheet_doc_has_manual_use_guardrails() -> None:
    text = _doc_text()

    required_phrases = [
        "manual review artifact",
        "not a final ranking",
        "not a formula tuning packet",
        "Do not tune formulas from this worksheet.",
        "Do not treat any row as a final recommendation.",
        "display-only",
        "human_prior_before_model",
        "final_human_decision",
        "USER_JUDGMENT_WORKSHEET_20260605.csv",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_user_judgment_worksheet_csv_has_expected_columns_and_blank_human_fields() -> None:
    rows = _rows()
    assert len(rows) >= 30

    expected_columns = [
        "worksheet_id",
        "review_group",
        "subject_type",
        "subject",
        "position",
        "surface",
        "model_says",
        "source_report",
        "warning_context",
        "money_action_risk",
        "human_prior_before_model",
        "agreement_with_model",
        "disagreement_reason",
        "final_human_decision",
        "follow_up_notes",
    ]

    assert list(rows[0]) == expected_columns
    for row in rows:
        for column in [
            "human_prior_before_model",
            "agreement_with_model",
            "disagreement_reason",
            "final_human_decision",
            "follow_up_notes",
        ]:
            assert row[column] == ""


def test_user_judgment_worksheet_includes_required_review_groups_and_sentinels() -> None:
    rows = _rows()
    text = CSV_PATH.read_text(encoding="utf-8")

    required_groups = {
        "source_safety_sentinel",
        "blank_primary_score",
        "manual_pick_sentinel",
        "qb_1qb_context",
        "te_no_premium_context",
        "rb_wr_balance",
        "young_player_evidence",
        "veteran_status",
        "rookie_top_cluster",
        "rookie_watchlist",
        "pick_neighborhood",
        "external_asset_context",
        "decision_board_context",
    }
    assert required_groups <= {row["review_group"] for row in rows}

    required_subjects = [
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
        "Trey McBride",
        "Josh Allen",
        "Joe Burrow",
        "Daniel Sobkowicz",
        "2026 2.08",
    ]

    for subject in required_subjects:
        assert subject in text


def test_user_judgment_worksheet_csv_does_not_encode_recommendations() -> None:
    text = CSV_PATH.read_text(encoding="utf-8").lower()

    banned_recommendation_phrases = [
        "you should trade",
        "you should cut",
        "you should keep",
        "you should draft",
        "must buy",
        "must sell",
        "final recommendation",
    ]

    for phrase in banned_recommendation_phrases:
        assert phrase not in text


def test_refinement_queue_marks_r27_done_with_audit_note() -> None:
    queue_text = QUEUE.read_text(encoding="utf-8")

    r27_lines = [
        line for line in queue_text.splitlines() if line.startswith("| R27 |")
    ]
    assert len(r27_lines) == 1
    r27 = r27_lines[0]

    assert "| Done |" in r27
    assert "USER_JUDGMENT_WORKSHEET_20260605.md" in r27
    assert "USER_JUDGMENT_WORKSHEET_20260605.csv" in r27
    assert "blank human-prior" in r27
