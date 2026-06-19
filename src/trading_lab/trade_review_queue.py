from __future__ import annotations

REVIEW_QUEUE_LABELS = (
    "Add to review queue (placeholder)",
    "Review queue not wired",
    "Not saved",
    "No generated artifacts",
    "Manual note: copy package details if needed.",
)

REVIEW_QUEUE_STATUS = "non-persistent placeholder"


def review_queue_placeholder_labels() -> tuple[str, ...]:
    return REVIEW_QUEUE_LABELS


def review_queue_status_message() -> str:
    return (
        "Review queue is not wired and not saved. "
        "No files are written; copy package details manually if needed."
    )
