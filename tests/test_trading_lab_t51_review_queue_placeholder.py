from src.trading_lab.trade_lab_component import (
    REVIEW_QUEUE_PLACEHOLDER_LABELS,
)
from src.trading_lab.trade_review_queue import (
    REVIEW_QUEUE_STATUS,
    review_queue_placeholder_labels,
    review_queue_status_message,
)


def test_review_queue_placeholder_exists() -> None:
    labels = review_queue_placeholder_labels()

    assert "Add to review queue (placeholder)" in labels
    assert REVIEW_QUEUE_PLACEHOLDER_LABELS == labels


def test_placeholder_says_not_saved_and_not_wired() -> None:
    message = review_queue_status_message()

    assert "not wired" in message
    assert "not saved" in message
    assert REVIEW_QUEUE_STATUS == "non-persistent placeholder"


def test_no_persistence_helper_exists() -> None:
    import src.trading_lab.trade_review_queue as review_queue

    for blocked in ("save", "write", "persist", "export"):
        assert not hasattr(review_queue, blocked)


def test_no_file_output_wording_appears() -> None:
    text = " ".join((*review_queue_placeholder_labels(), review_queue_status_message())).lower()

    for blocked in ("write file", "save file", "export csv", "generated output path"):
        assert blocked not in text


def test_manual_copy_note_exists() -> None:
    assert "copy package details" in review_queue_status_message()
