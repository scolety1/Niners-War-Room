from __future__ import annotations

from src.services.model_recalibration_service import model_v4_rebuild_freeze_active

LEGACY_ACTION_LABELS = {
    "core hold": "Review-only legacy core hold",
    "core holds": "Review-only legacy core holds",
    "bubble": "Review-only legacy bubble",
    "bubble players": "Review-only legacy bubble players",
    "shop": "Review-only legacy shop",
    "shop candidates": "Review-only legacy shop candidates",
    "shop/release": "Review-only legacy shop/release",
    "release": "Review-only legacy release",
    "release/drop": "Review-only legacy release/drop",
    "drop": "Review-only legacy drop",
}
READINESS_LABELS = {
    "decision ready": "Review Only",
    "roster decisions ready": "Roster Decisions Review Only",
    "draft ready": "Draft Review Only",
}


def legacy_label_quarantine_active() -> bool:
    return model_v4_rebuild_freeze_active()


def quarantine_legacy_label(
    label: object,
    *,
    active: bool | None = None,
) -> str:
    text = str(label or "").strip()
    if not text:
        return ""
    quarantine_active = legacy_label_quarantine_active() if active is None else active
    if not quarantine_active:
        return text
    normalized = _normalize_label(text)
    if normalized in READINESS_LABELS:
        return READINESS_LABELS[normalized]
    if normalized in LEGACY_ACTION_LABELS:
        return LEGACY_ACTION_LABELS[normalized]
    return text


def legacy_label_is_trusted_decision(
    label: object,
    *,
    active: bool | None = None,
) -> bool:
    text = str(label or "").strip()
    if not text:
        return False
    quarantine_active = legacy_label_quarantine_active() if active is None else active
    if not quarantine_active:
        return True
    return _normalize_label(text) not in _QUARANTINED_LABELS


def label_quarantine_notice() -> str:
    return (
        "Model v4 rebuild freeze is active. Legacy Core Hold, Bubble, Shop, "
        "Release, Decision Ready, Roster Decisions Ready, and Draft Ready labels "
        "are review-only until v4 thresholds and receipts are rebuilt."
    )


def _normalize_label(label: str) -> str:
    return " ".join(label.replace("_", " ").strip().lower().split())


_QUARANTINED_LABELS = set(LEGACY_ACTION_LABELS).union(READINESS_LABELS)
